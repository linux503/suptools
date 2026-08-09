"""SupTools — accurate macOS metrics collection."""

from __future__ import annotations

import os
import platform
import re
import socket
import subprocess
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional, Tuple

import psutil

HISTORY = 60
_VM_STAT_TTL = 4.0
_PARTITIONS_TTL = 8.0
_PROCESS_LIMIT = 40
_PROCESS_MIN_CPU = 0.1
_PROCESS_MIN_RSS = 12 * 1024 * 1024

# Virtual / tunnel interfaces that inflate totals if included with physical NICs.
_SKIP_IFACE_PREFIXES = (
    "lo", "awdl", "llw", "utun", "gif", "stf", "bridge", "ap", "vmnet", "vmenet", "anpi", "sipa",
)


@dataclass
class Snapshot:
    cpu_percent: float = 0.0
    cpu_per_core: List[float] = field(default_factory=list)
    cpu_times: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # user, system, idle
    load_avg: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    mem_total: int = 0
    mem_used: int = 0          # App-used style ≈ total - available (matches Memory Pressure %)
    mem_available: int = 0
    mem_percent: float = 0.0
    mem_wired: int = 0
    mem_active: int = 0
    mem_compressed: int = 0
    mem_cached: int = 0        # file-backed / inactive cache-ish
    mem_pressure: str = "normal"  # normal | warn | critical
    mem_pressure_score: float = 0.0
    swap_total: int = 0
    swap_used: int = 0
    swap_percent: float = 0.0

    disk_partitions: List[dict] = field(default_factory=list)
    disk_read_bps: float = 0.0
    disk_write_bps: float = 0.0
    primary_disk_percent: float = 0.0
    primary_disk_used: int = 0
    primary_disk_total: int = 0
    primary_disk_label: str = ""
    primary_disk_free: int = 0

    net_down_bps: float = 0.0
    net_up_bps: float = 0.0
    net_interfaces: List[dict] = field(default_factory=list)

    processes: List[dict] = field(default_factory=list)
    top_process_name: str = ""
    top_process_cpu: float = 0.0

    has_battery: bool = False
    battery_percent: float = 0.0
    battery_plugged: bool = False
    battery_secs_left: int = -1  # -1 unknown / unlimited when plugged

    hostname: str = ""
    platform: str = ""
    chip: str = ""
    boot_time: float = 0.0
    uptime: float = 0.0
    logical_cores: int = 0
    physical_cores: int = 0
    timestamp: float = 0.0


class MetricsCollector:
    def __init__(self) -> None:
        self.cpu_history: Deque[float] = deque(maxlen=HISTORY)
        self.mem_history: Deque[float] = deque(maxlen=HISTORY)
        self.net_down_history: Deque[float] = deque(maxlen=HISTORY)
        self.net_up_history: Deque[float] = deque(maxlen=HISTORY)
        self.disk_read_history: Deque[float] = deque(maxlen=HISTORY)
        self.disk_write_history: Deque[float] = deque(maxlen=HISTORY)

        self._prev_net = self._physical_net_counters()
        self._prev_disk = psutil.disk_io_counters()
        self._prev_iface: Dict[str, Tuple[int, int]] = {
            name: (c.bytes_recv, c.bytes_sent)
            for name, c in (psutil.net_io_counters(pernic=True) or {}).items()
            if self._is_physical_iface(name)
        }
        self._prev_time = time.time()
        self._hostname = socket.gethostname().replace(".lan", "").replace(".local", "")
        self._boot = psutil.boot_time()
        self._chip = self._detect_chip()
        self._cores = max(1, psutil.cpu_count(logical=True) or os.cpu_count() or 1)
        self._physical_cores = max(1, psutil.cpu_count(logical=False) or self._cores)
        self._platform = f"macOS {platform.mac_ver()[0]}"
        self._last_processes: List[dict] = []
        self._last_interfaces: List[dict] = []
        self._page_size = self._detect_page_size()
        self._vm_stat_cache: Dict[str, int] = {}
        self._vm_stat_at = 0.0
        self._partitions_cache: List[dict] = []
        self._partitions_at = 0.0
        self._primary_cache: Optional[dict] = None
        self._battery_cache: Optional[dict] = None
        self._battery_at = 0.0
        self._has_battery: Optional[bool] = None

        # EMA smoothing for bursty rates
        self._ema_down = 0.0
        self._ema_up = 0.0
        self._ema_read = 0.0
        self._ema_write = 0.0
        self._ema_alpha = 0.45

        # Prime counters so first real sample is meaningful (avoid full process walk)
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(interval=None, percpu=True)
        psutil.cpu_times_percent(interval=None)

    @staticmethod
    def _detect_page_size() -> int:
        try:
            return int(subprocess.check_output(["pagesize"], text=True).strip())
        except Exception:
            return 16384

    def _detect_chip(self) -> str:
        try:
            out = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            if out:
                return out
        except Exception:
            pass
        return "Apple Silicon" if platform.machine() == "arm64" else (platform.processor() or platform.machine())

    @staticmethod
    def _is_physical_iface(name: str) -> bool:
        return not name.startswith(_SKIP_IFACE_PREFIXES)

    def _physical_net_counters(self) -> Tuple[int, int]:
        """Sum only physical NICs to avoid double-counting utun/VPN/lo."""
        total_recv = total_sent = 0
        pernic = psutil.net_io_counters(pernic=True) or {}
        for name, c in pernic.items():
            if not self._is_physical_iface(name):
                continue
            total_recv += int(c.bytes_recv)
            total_sent += int(c.bytes_sent)
        return total_recv, total_sent

    def _ema(self, prev: float, value: float) -> float:
        a = self._ema_alpha
        return a * value + (1.0 - a) * prev

    def sample(self, *, include_processes: bool = True, include_interfaces: bool = True) -> Snapshot:
        now = time.time()
        dt = max(now - self._prev_time, 0.001)

        # CPU: derive overall from times so user/system/idle always add up
        times = psutil.cpu_times_percent(interval=None)
        user = float(getattr(times, "user", 0.0) + getattr(times, "nice", 0.0))
        system = float(getattr(times, "system", 0.0))
        idle = float(getattr(times, "idle", 0.0))
        # Keep leftover (iowait etc. rarely present on macOS) in system-ish residual
        cpu = max(0.0, min(100.0, 100.0 - idle))
        if user + system > 0 and abs((user + system) - cpu) > 1.5:
            cpu = min(100.0, user + system)
        per_core = [float(x) for x in psutil.cpu_percent(interval=None, percpu=True)]

        try:
            load_avg = tuple(float(x) for x in os.getloadavg())  # type: ignore[assignment]
        except OSError:
            load_avg = (0.0, 0.0, 0.0)

        mem = self._memory_stats()
        swap = psutil.swap_memory()

        partitions = self._collect_partitions(force=False)
        primary = self._primary_disk(partitions) if partitions else self._primary_cache
        if primary:
            self._primary_cache = primary

        # Disk IO rates
        disk_now = psutil.disk_io_counters()
        read_bps = write_bps = 0.0
        if disk_now and self._prev_disk:
            read_raw = max(0.0, (disk_now.read_bytes - self._prev_disk.read_bytes) / dt)
            write_raw = max(0.0, (disk_now.write_bytes - self._prev_disk.write_bytes) / dt)
            self._ema_read = self._ema(self._ema_read, read_raw)
            self._ema_write = self._ema(self._ema_write, write_raw)
            read_bps, write_bps = self._ema_read, self._ema_write
            self._prev_disk = disk_now

        # Network rates from physical NICs only
        net_recv, net_sent = self._physical_net_counters()
        down_bps = up_bps = 0.0
        if self._prev_net:
            down_raw = max(0.0, (net_recv - self._prev_net[0]) / dt)
            up_raw = max(0.0, (net_sent - self._prev_net[1]) / dt)
            self._ema_down = self._ema(self._ema_down, down_raw)
            self._ema_up = self._ema(self._ema_up, up_raw)
            down_bps, up_bps = self._ema_down, self._ema_up
        self._prev_net = (net_recv, net_sent)

        if include_interfaces:
            self._last_interfaces = self._collect_interfaces(dt)

        if include_processes:
            self._last_processes = self._collect_processes(
                limit=_PROCESS_LIMIT,
                include_cmd=True,
            )

        primary_pct = float(primary["percent"]) if primary else 0.0
        primary_used = int(primary["used"]) if primary else 0
        primary_total = int(primary["total"]) if primary else 0
        primary_label = str(primary.get("label", "")) if primary else ""
        primary_free = max(0, primary_total - primary_used) if primary_total else 0

        pressure_level, pressure_score = self._memory_pressure(mem, swap)
        batt = self._battery_stats()
        top_name = ""
        top_cpu = 0.0
        if self._last_processes:
            top = self._last_processes[0]
            top_name = str(top.get("name") or "")
            top_cpu = float(top.get("cpu") or 0.0)

        swap_total = int(swap.total)
        swap_used = int(swap.used)
        swap_pct = (swap_used / swap_total * 100.0) if swap_total else 0.0

        snap = Snapshot(
            cpu_percent=round(cpu, 1),
            cpu_per_core=per_core,
            cpu_times=(round(user, 1), round(system, 1), round(idle, 1)),
            load_avg=load_avg,  # type: ignore[arg-type]
            mem_total=mem["total"],
            mem_used=mem["used"],
            mem_available=mem["available"],
            mem_percent=mem["percent"],
            mem_wired=mem["wired"],
            mem_active=mem["active"],
            mem_compressed=mem["compressed"],
            mem_cached=mem["cached"],
            mem_pressure=pressure_level,
            mem_pressure_score=pressure_score,
            swap_total=swap_total,
            swap_used=swap_used,
            swap_percent=round(swap_pct, 1),
            disk_partitions=partitions,
            disk_read_bps=read_bps,
            disk_write_bps=write_bps,
            primary_disk_percent=primary_pct,
            primary_disk_used=primary_used,
            primary_disk_total=primary_total,
            primary_disk_label=primary_label,
            primary_disk_free=primary_free,
            net_down_bps=down_bps,
            net_up_bps=up_bps,
            # Keep last known lists so UI does not flash empty between sparse refreshes
            net_interfaces=list(self._last_interfaces),
            processes=list(self._last_processes),
            top_process_name=top_name,
            top_process_cpu=top_cpu,
            has_battery=bool(batt.get("has")),
            battery_percent=float(batt.get("percent") or 0.0),
            battery_plugged=bool(batt.get("plugged")),
            battery_secs_left=int(batt.get("secs_left") if batt.get("secs_left") is not None else -1),
            hostname=self._hostname,
            platform=self._platform,
            chip=self._chip,
            boot_time=self._boot,
            uptime=now - self._boot,
            logical_cores=self._cores,
            physical_cores=self._physical_cores,
            timestamp=now,
        )

        self.cpu_history.append(snap.cpu_percent)
        self.mem_history.append(snap.mem_percent)
        self.net_down_history.append(down_bps)
        self.net_up_history.append(up_bps)
        self.disk_read_history.append(read_bps)
        self.disk_write_history.append(write_bps)
        self._prev_time = now
        return snap

    def sample_light(self) -> Snapshot:
        return self.sample(include_processes=False, include_interfaces=False)

    def _memory_stats(self) -> dict:
        """
        Align with Activity Monitor / memory pressure:
        - percent ≈ (total - available) / total
        - used     = total - available
        - breakdown from vm_stat when possible
        """
        vm = psutil.virtual_memory()
        total = int(vm.total)
        available = int(vm.available)
        used = max(0, total - available)
        percent = (used / total * 100.0) if total else 0.0

        wired = int(getattr(vm, "wired", 0) or 0)
        active = int(getattr(vm, "active", 0) or 0)
        inactive = int(getattr(vm, "inactive", 0) or 0)
        compressed = 0
        cached = inactive

        # Refine with cached vm_stat pages (subprocess is relatively expensive)
        try:
            pages = self._parse_vm_stat()
            ps = self._page_size
            if pages:
                wired = pages.get("wired", wired // ps) * ps if "wired" in pages else wired
                active = pages.get("active", active // ps) * ps if "active" in pages else active
                inactive = pages.get("inactive", inactive // ps) * ps if "inactive" in pages else inactive
                compressed = pages.get("compressed", 0) * ps
                file_backed = pages.get("file_backed", 0) * ps
                cached = max(file_backed, inactive)
                am_used = min(total, active + wired + compressed)
                if am_used > 0 and total:
                    used = max(used, am_used) if abs(used - am_used) / total < 0.15 else used
        except Exception:
            pass

        return {
            "total": total,
            "available": available,
            "used": used,
            "percent": round(percent, 1),
            "wired": wired,
            "active": active,
            "compressed": compressed,
            "cached": cached,
        }

    @staticmethod
    def _memory_pressure(mem: dict, swap) -> Tuple[str, float]:
        """Approximate Activity Monitor memory pressure (normal/warn/critical)."""
        total = max(int(mem.get("total") or 0), 1)
        available = max(0, int(mem.get("available") or 0))
        compressed = max(0, int(mem.get("compressed") or 0))
        avail_ratio = available / total
        # Score 0..100 (higher = more pressure)
        score = max(0.0, min(100.0, (1.0 - avail_ratio) * 100.0))
        try:
            swap_used = int(getattr(swap, "used", 0) or 0)
        except Exception:
            swap_used = 0
        if swap_used > 256 * 1024 * 1024:
            score = min(100.0, score + 8.0)
        if compressed > total * 0.25:
            score = min(100.0, score + 6.0)
        if avail_ratio >= 0.28 and score < 70:
            level = "normal"
        elif avail_ratio >= 0.14 and score < 88:
            level = "warn"
        else:
            level = "critical"
        return level, round(score, 1)

    def _battery_stats(self) -> dict:
        """Cached battery readout (MacBook); desktops return has=False."""
        now = time.time()
        if self._battery_cache is not None and (now - self._battery_at) < 12.0:
            return self._battery_cache
        out = {
            "has": False,
            "percent": 0.0,
            "plugged": False,
            "secs_left": -1,
        }
        try:
            if self._has_battery is False:
                self._battery_cache = out
                self._battery_at = now
                return out
            batt = psutil.sensors_battery()
            if batt is None:
                self._has_battery = False
                self._battery_cache = out
                self._battery_at = now
                return out
            self._has_battery = True
            secs = getattr(batt, "secsleft", None)
            if secs is None or secs in (
                getattr(psutil, "POWER_TIME_UNLIMITED", -2),
                getattr(psutil, "POWER_TIME_UNKNOWN", -1),
            ):
                secs_left = -1
            else:
                try:
                    secs_left = int(secs)
                except Exception:
                    secs_left = -1
            out = {
                "has": True,
                "percent": round(float(batt.percent or 0.0), 1),
                "plugged": bool(batt.power_plugged),
                "secs_left": secs_left,
            }
        except Exception:
            pass
        self._battery_cache = out
        self._battery_at = now
        return out

    def _parse_vm_stat(self) -> Dict[str, int]:
        now = time.time()
        if self._vm_stat_cache and (now - self._vm_stat_at) < _VM_STAT_TTL:
            return self._vm_stat_cache
        out = subprocess.check_output(["vm_stat"], text=True, stderr=subprocess.DEVNULL)
        mapping = {
            "Pages free": "free",
            "Pages active": "active",
            "Pages inactive": "inactive",
            "Pages speculative": "speculative",
            "Pages wired down": "wired",
            "Pages purgeable": "purgeable",
            "Pages stored in compressor": "compressed",
            "File-backed pages": "file_backed",
            "Anonymous pages": "anonymous",
        }
        result: Dict[str, int] = {}
        for line in out.splitlines():
            if ":" not in line:
                continue
            key, raw = line.split(":", 1)
            key = key.strip()
            if key not in mapping:
                continue
            digits = re.sub(r"[^\d]", "", raw)
            if digits:
                result[mapping[key]] = int(digits)
        self._vm_stat_cache = result
        self._vm_stat_at = now
        return result

    def _collect_partitions(self, force: bool = False) -> List[dict]:
        now = time.time()
        if (
            not force
            and self._partitions_cache
            and (now - self._partitions_at) < _PARTITIONS_TTL
        ):
            return self._partitions_cache
        partitions: List[dict] = []
        seen = set()
        for part in psutil.disk_partitions(all=False):
            if part.fstype in ("", "devfs", "autofs"):
                continue
            mount = part.mountpoint
            if mount.startswith("/System/Volumes/") and mount != "/System/Volumes/Data":
                continue
            if mount in seen:
                continue
            try:
                usage = psutil.disk_usage(mount)
            except (PermissionError, OSError):
                continue
            seen.add(mount)
            # Capacity style percent like Finder/df: used / (used + free)
            denom = usage.used + usage.free
            percent = (usage.used / denom * 100.0) if denom else float(usage.percent)
            if mount == "/":
                label = "系统卷"
            elif mount == "/System/Volumes/Data":
                label = "数据卷"
            else:
                label = os.path.basename(mount.rstrip("/")) or mount
            partitions.append(
                {
                    "device": part.device,
                    "mount": mount,
                    "label": label,
                    "fstype": part.fstype or "?",
                    "total": int(usage.total),
                    "used": int(usage.used),
                    "free": int(usage.free),
                    "percent": round(percent, 1),
                    "is_root": mount == "/",
                    "is_data": mount == "/System/Volumes/Data",
                }
            )

        if not any(p["is_root"] for p in partitions):
            try:
                usage = psutil.disk_usage("/")
                denom = usage.used + usage.free
                percent = (usage.used / denom * 100.0) if denom else float(usage.percent)
                partitions.insert(
                    0,
                    {
                        "device": "/",
                        "mount": "/",
                        "label": "系统卷",
                        "fstype": "apfs",
                        "total": int(usage.total),
                        "used": int(usage.used),
                        "free": int(usage.free),
                        "percent": round(percent, 1),
                        "is_root": True,
                        "is_data": False,
                    },
                )
            except OSError:
                pass

        # Synthetic Macintosh HD container row (system + data on same APFS size)
        root = next((p for p in partitions if p["is_root"]), None)
        data = next((p for p in partitions if p.get("is_data")), None)
        if root and data and root["total"] == data["total"]:
            used = root["used"] + data["used"]
            free = data["free"]  # shared free space
            total = data["total"]
            denom = used + free
            percent = (used / denom * 100.0) if denom else 0.0
            partitions.insert(
                0,
                {
                    "device": data["device"],
                    "mount": "/",
                    "label": "Macintosh HD",
                    "fstype": "apfs",
                    "total": total,
                    "used": used,
                    "free": free,
                    "percent": round(min(100.0, percent), 1),
                    "is_root": False,
                    "is_data": False,
                    "is_container": True,
                },
            )

        partitions.sort(
            key=lambda p: (
                not p.get("is_container", False),
                not p.get("is_data", False),
                not p.get("is_root", False),
                p["mount"],
            )
        )
        self._partitions_cache = partitions
        self._partitions_at = now
        return partitions

    @staticmethod
    def _primary_disk(partitions: List[dict]) -> Optional[dict]:
        container = next((p for p in partitions if p.get("is_container")), None)
        if container:
            return container
        data = next((p for p in partitions if p.get("is_data")), None)
        if data:
            return data
        return next((p for p in partitions if p.get("is_root")), partitions[0] if partitions else None)

    def _collect_interfaces(self, dt: float) -> List[dict]:
        interfaces: List[dict] = []
        pernic = psutil.net_io_counters(pernic=True) or {}
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        next_prev: Dict[str, Tuple[int, int]] = {}

        for name, counters in pernic.items():
            if not self._is_physical_iface(name):
                continue
            st = stats.get(name)
            ip = ""
            for addr in addrs.get(name, []):
                family = addr.family
                family_name = getattr(family, "name", str(family))
                try:
                    is_v4 = family_name in ("AF_INET", "2") or int(family) == 2
                except Exception:
                    is_v4 = False
                if is_v4 and not str(addr.address).startswith("127."):
                    ip = addr.address
                    break
            isup = bool(st.isup) if st else False
            recv = int(counters.bytes_recv)
            sent = int(counters.bytes_sent)
            next_prev[name] = (recv, sent)
            down = up = 0.0
            if name in self._prev_iface and dt > 0:
                prev_r, prev_s = self._prev_iface[name]
                down = max(0.0, (recv - prev_r) / dt)
                up = max(0.0, (sent - prev_s) / dt)
            if not isup and recv == 0 and sent == 0:
                continue
            friendly = "Wi‑Fi/以太网" if name.startswith("en") else name
            interfaces.append(
                {
                    "name": name,
                    "display": f"{friendly} ({name})",
                    "ip": ip,
                    "isup": isup,
                    "speed": getattr(st, "speed", 0) if st else 0,
                    "bytes_recv": recv,
                    "bytes_sent": sent,
                    "down_bps": down,
                    "up_bps": up,
                    "packets_recv": int(counters.packets_recv),
                    "packets_sent": int(counters.packets_sent),
                }
            )

        self._prev_iface = next_prev
        interfaces.sort(key=lambda i: (not i["isup"], -(i["down_bps"] + i["up_bps"]), -(i["bytes_recv"] + i["bytes_sent"])))
        return interfaces

    def _collect_processes(self, limit: int = _PROCESS_LIMIT, include_cmd: bool = False) -> List[dict]:
        items: List[dict] = []
        now = time.time()
        attrs = [
            "pid",
            "name",
            "cpu_percent",
            "memory_info",
            "num_threads",
            "status",
            "username",
            "create_time",
        ]
        if include_cmd:
            attrs.append("cmdline")
        for proc in psutil.process_iter(attrs=attrs):
            try:
                info = proc.info
                mem = info.get("memory_info")
                rss = int(mem.rss) if mem else 0
                cpu = float(info.get("cpu_percent") or 0.0)
                if cpu < _PROCESS_MIN_CPU and rss < _PROCESS_MIN_RSS:
                    continue
                created = float(info.get("create_time") or 0.0)
                runtime = max(0.0, now - created) if created else 0.0
                cmd = ""
                if include_cmd:
                    raw_cmd = info.get("cmdline") or []
                    if isinstance(raw_cmd, (list, tuple)) and raw_cmd:
                        cmd = " ".join(str(x) for x in raw_cmd[:3])
                        if len(cmd) > 64:
                            cmd = cmd[:61] + "…"
                items.append(
                    {
                        "pid": info["pid"],
                        "name": info.get("name") or "?",
                        "cpu": round(cpu, 1),
                        "memory": rss,
                        "threads": int(info.get("num_threads") or 0),
                        "status": info.get("status") or "",
                        "user": info.get("username") or "",
                        "runtime": runtime,
                        "cmd": cmd,
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        items.sort(key=lambda p: (p["cpu"], p["memory"]), reverse=True)
        return items[:limit]


def format_bytes(n: float) -> str:
    n = float(max(0, n))
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while n >= 1024 and i < len(units) - 1:
        n /= 1024.0
        i += 1
    if i == 0:
        return f"{int(n)} {units[i]}"
    if abs(n - round(n)) < 0.05:
        return f"{int(round(n))} {units[i]}"
    return f"{n:.1f} {units[i]}"


def format_bps(n: float) -> str:
    return f"{format_bytes(n)}/s"


def format_bps_short(n: float) -> str:
    n = float(max(0, n))
    units = ["B", "K", "M", "G"]
    i = 0
    while n >= 1024 and i < len(units) - 1:
        n /= 1024.0
        i += 1
    if i == 0:
        return f"{int(n)}{units[i]}"
    return f"{n:.1f}{units[i]}"


def format_uptime(seconds: float) -> str:
    total = int(seconds)
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    if days:
        return f"{days}天{hours}时{minutes}分"
    if hours:
        return f"{hours}时{minutes}分"
    return f"{minutes}分"


def format_runtime(seconds: float) -> str:
    total = int(max(0, seconds))
    if total < 60:
        return f"{total}s"
    if total < 3600:
        return f"{total // 60}m"
    if total < 86400:
        return f"{total // 3600}h{(total % 3600) // 60:02d}m"
    return f"{total // 86400}d{(total % 86400) // 3600}h"
