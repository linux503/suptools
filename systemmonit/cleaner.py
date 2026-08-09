"""Professional junk cleaner — itemized scan, progress, selective delete."""

from __future__ import annotations

import os
import shutil
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


HOME = Path.home()
ProgressCb = Callable[[Dict[str, Any]], None]

# Never touch these under Caches (system-critical or owned by other categories)
_CACHE_DENY = {
    "CloudKit",
    "com.apple.Safari",
    "com.apple.appleseed.FeedbackAssistant",
    "FamilyCircle",
    "com.apple.HomeKit",
    "com.apple.keychainaccessd",
    "com.apple.Safari.SafeBrowsing",
    "Google",
    "com.apple.storekitagent",
    # Owned by dedicated categories — avoid double counting
    "pip",
    "Homebrew",
    "com.spotify.client",
    "com.apple.Safari",
    # Owned by chat / media categories
    "com.tinyspeck.slackmacgap",
    "com.hnc.Discord",
    "ru.keepcoder.Telegram",
    "us.zoom.xos",
    "net.whatsapp.WhatsApp",
}

# Names under Library/Caches that belong to browser category
_BROWSER_CACHE_NAMES = {
    "Google/Chrome",  # nested handled separately
    "com.google.Chrome",
    "com.google.Chrome.Canary",
    "com.microsoft.edgemac",
    "org.mozilla.firefox",
    "company.thebrowser.Browser",  # Arc
    "com.brave.Browser",
}


class CancelToken:
    """Cooperative cancellation for long scan/clean jobs."""

    def __init__(self) -> None:
        self._ev = threading.Event()

    def cancel(self) -> None:
        self._ev.set()

    @property
    def cancelled(self) -> bool:
        return self._ev.is_set()

    def raise_if_cancelled(self) -> None:
        if self._ev.is_set():
            raise InterruptedError("cancelled")


@dataclass
class CleanTarget:
    key: str
    title: str
    detail: str
    paths: List[Path]
    risk: str = "safe"  # safe | caution
    icon: str = "folder"


@dataclass
class CleanResult:
    freed_bytes: int = 0
    removed_items: int = 0
    errors: List[str] = field(default_factory=list)
    details: List[Dict] = field(default_factory=list)
    moved_to_trash: bool = False
    cancelled: bool = False


def targets() -> List[CleanTarget]:
    brew_paths = [HOME / "Library" / "Caches" / "Homebrew"]
    for p in (
        Path("/opt/homebrew/var/cache"),
        Path("/usr/local/var/homebrew/cache"),
        HOME / ".cache" / "Homebrew",
    ):
        if p.exists() or p.parent.exists():
            brew_paths.append(p)

    browser_paths = [
        HOME / "Library" / "Caches" / "Google" / "Chrome",
        HOME / "Library" / "Caches" / "com.microsoft.edgemac",
        HOME / "Library" / "Caches" / "org.mozilla.firefox",
        HOME / "Library" / "Caches" / "company.thebrowser.Browser",
        HOME / "Library" / "Caches" / "com.brave.Browser",
        HOME / "Library" / "Caches" / "Chromium",
    ]
    # Prefer com.google.Chrome only when Google/Chrome tree is absent (avoid double-count)
    chrome_bundle = HOME / "Library" / "Caches" / "com.google.Chrome"
    chrome_tree = HOME / "Library" / "Caches" / "Google" / "Chrome"
    if chrome_bundle.exists() and not chrome_tree.exists():
        browser_paths.insert(1, chrome_bundle)

    return [
        CleanTarget(
            key="user_caches",
            title="用户缓存",
            detail="应用程序缓存（已排除系统关键与浏览器/开发缓存）",
            paths=[HOME / "Library" / "Caches"],
            risk="safe",
            icon="cache",
        ),
        CleanTarget(
            key="browser",
            title="浏览器缓存",
            detail="Chrome / Edge / Firefox / Arc / Brave 缓存",
            paths=browser_paths,
            risk="safe",
            icon="browser",
        ),
        CleanTarget(
            key="app_support_cache",
            title="应用支持缓存",
            detail="Application Support 下常见 Cache / Logs 子目录",
            paths=[HOME / "Library" / "Application Support"],
            risk="safe",
            icon="app",
        ),
        CleanTarget(
            key="logs",
            title="旧日志",
            detail="~/Library/Logs 中超过 7 天的日志",
            paths=[HOME / "Library" / "Logs"],
            risk="safe",
            icon="log",
        ),
        CleanTarget(
            key="tmp",
            title="临时文件",
            detail="/tmp 中超过 2 天的文件",
            paths=[Path("/tmp")],
            risk="safe",
            icon="tmp",
        ),
        CleanTarget(
            key="xcode",
            title="Xcode 缓存",
            detail="DerivedData / iOS DeviceSupport（Archives 单独标为谨慎）",
            paths=[
                HOME / "Library" / "Developer" / "Xcode" / "DerivedData",
                HOME / "Library" / "Developer" / "Xcode" / "iOS DeviceSupport",
            ],
            risk="safe",
            icon="dev",
        ),
        CleanTarget(
            key="xcode_archives",
            title="Xcode Archives",
            detail="归档包，删除后无法再上传同版本（谨慎）",
            paths=[HOME / "Library" / "Developer" / "Xcode" / "Archives"],
            risk="caution",
            icon="archive",
        ),
        CleanTarget(
            key="pip",
            title="Python / pip 缓存",
            detail="pip 下载与 wheel 缓存",
            paths=[
                HOME / "Library" / "Caches" / "pip",
                HOME / ".cache" / "pip",
            ],
            risk="safe",
            icon="code",
        ),
        CleanTarget(
            key="npm",
            title="Node 缓存",
            detail="npm / yarn / pnpm 缓存目录",
            paths=[
                HOME / ".npm",
                HOME / "Library" / "Caches" / "Yarn",
                HOME / "Library" / "Caches" / "pnpm",
                HOME / ".cache" / "yarn",
            ],
            risk="safe",
            icon="node",
        ),
        CleanTarget(
            key="pnpm_store",
            title="pnpm Store",
            detail="全局包仓库，清理后需重新下载依赖（谨慎）",
            paths=[HOME / ".local" / "share" / "pnpm" / "store"],
            risk="caution",
            icon="node",
        ),
        CleanTarget(
            key="homebrew",
            title="Homebrew 缓存",
            detail="Homebrew 下载包与旧版本缓存",
            paths=brew_paths,
            risk="safe",
            icon="brew",
        ),
        CleanTarget(
            key="safari",
            title="Safari 缓存",
            detail="Safari 网页缓存（不含书签与历史）",
            paths=[
                HOME / "Library" / "Caches" / "com.apple.Safari",
                HOME / "Library" / "Caches" / "CloudKit" / "com.apple.Safari",
            ],
            risk="safe",
            icon="browser",
        ),
        CleanTarget(
            key="mail",
            title="邮件下载",
            detail="Mail 附件下载缓存",
            paths=[
                HOME / "Library" / "Containers" / "com.apple.mail" / "Data" / "Library" / "Mail Downloads",
                HOME / "Library" / "Mail Downloads",
            ],
            risk="safe",
            icon="mail",
        ),
        CleanTarget(
            key="xcode_simulators",
            title="Xcode 模拟器",
            detail="CoreSimulator 设备数据，体积可能很大（谨慎）",
            paths=[HOME / "Library" / "Developer" / "CoreSimulator" / "Devices"],
            risk="caution",
            icon="dev",
        ),
        CleanTarget(
            key="docker",
            title="Docker 数据",
            detail="Docker 镜像与虚拟磁盘（谨慎，可能极大）",
            paths=[
                HOME / "Library" / "Containers" / "com.docker.docker" / "Data",
                HOME / ".docker",
            ],
            risk="caution",
            icon="docker",
        ),
        CleanTarget(
            key="spotify",
            title="Spotify 缓存",
            detail="Spotify 本地缓存与数据",
            paths=[HOME / "Library" / "Caches" / "com.spotify.client"],
            risk="safe",
            icon="app",
        ),
        CleanTarget(
            key="chat",
            title="聊天应用缓存",
            detail="Slack / Discord / Telegram / Zoom / WhatsApp 缓存",
            paths=[
                HOME / "Library" / "Caches" / "com.tinyspeck.slackmacgap",
                HOME / "Library" / "Caches" / "com.hnc.Discord",
                HOME / "Library" / "Application Support" / "discord" / "Cache",
                HOME / "Library" / "Application Support" / "discord" / "Code Cache",
                HOME / "Library" / "Caches" / "ru.keepcoder.Telegram",
                HOME / "Library" / "Caches" / "us.zoom.xos",
                HOME / "Library" / "Caches" / "us.zoom.ZoomPresence",
                HOME / "Library" / "Caches" / "net.whatsapp.WhatsApp",
                HOME / "Library" / "Group Containers" / "group.com.facebook.family" / "Library" / "Caches",
            ],
            risk="safe",
            icon="app",
        ),
        CleanTarget(
            key="dev_stores",
            title="开发依赖缓存",
            detail="CocoaPods / Gradle / Cargo / Go module 缓存",
            paths=[
                HOME / "Library" / "Caches" / "CocoaPods",
                HOME / ".gradle" / "caches",
                HOME / ".cargo" / "registry" / "cache",
                HOME / "Library" / "Caches" / "go-build",
                HOME / "go" / "pkg" / "mod" / "cache",
            ],
            risk="safe",
            icon="code",
        ),
        CleanTarget(
            key="installers",
            title="下载的安装包",
            detail="下载文件夹中的 .dmg / .pkg / .zip（谨慎）",
            paths=[HOME / "Downloads"],
            risk="caution",
            icon="archive",
        ),
        CleanTarget(
            key="large_files",
            title="大文件发现",
            detail="桌面 / 文稿 / 下载中超过 100 MB 的文件（谨慎）",
            paths=[
                HOME / "Desktop",
                HOME / "Documents",
                HOME / "Downloads",
                HOME / "Movies",
            ],
            risk="caution",
            icon="large",
        ),
        CleanTarget(
            key="ios_backups",
            title="iOS 备份",
            detail="本地设备备份，体积通常很大（谨慎）",
            paths=[HOME / "Library" / "Application Support" / "MobileSync" / "Backup"],
            risk="caution",
            icon="phone",
        ),
        CleanTarget(
            key="trash",
            title="废纸篓",
            detail="清空废纸篓（不可恢复）",
            paths=[HOME / ".Trash"],
            risk="caution",
            icon="trash",
        ),
    ]


def format_size(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    v = float(max(0, int(n)))
    for u in units:
        if v < 1024 or u == units[-1]:
            if u == "B":
                return f"{int(v)} {u}"
            return f"{v:.1f} {u}"
        v /= 1024.0
    return f"{n} B"


def _fmt(n: int) -> str:
    return format_size(n)


def _dir_stats(path: Path, cancel: Optional[CancelToken] = None) -> Tuple[int, int]:
    """Single walk: (total_bytes, file_count)."""
    total = 0
    files_n = 0
    try:
        if path.is_file() or path.is_symlink():
            return int(path.lstat().st_size), 1
        for root, _dirs, files in os.walk(path, followlinks=False):
            if cancel and cancel.cancelled:
                break
            files_n += len(files)
            for name in files:
                try:
                    total += int((Path(root) / name).lstat().st_size)
                except OSError:
                    continue
    except OSError:
        return 0, 0
    return total, files_n


def _dir_size(path: Path, cancel: Optional[CancelToken] = None) -> int:
    return _dir_stats(path, cancel=cancel)[0]


def _count_files(path: Path, cancel: Optional[CancelToken] = None) -> int:
    return _dir_stats(path, cancel=cancel)[1]


def _rel_display(path: Path) -> str:
    try:
        return str(path).replace(str(HOME), "~")
    except Exception:
        return str(path)


def _emit(progress: Optional[ProgressCb], **kwargs) -> None:
    if progress:
        try:
            progress(kwargs)
        except Exception:
            pass


def _item(
    *,
    category: str,
    category_title: str,
    name: str,
    path: Path,
    risk: str,
    selected: bool = True,
    cancel: Optional[CancelToken] = None,
) -> Dict[str, Any]:
    size, files = _dir_stats(path, cancel=cancel)
    return {
        "id": f"{category}:{uuid.uuid4().hex[:10]}",
        "category": category,
        "category_title": category_title,
        "name": name,
        "path": str(path),
        "path_display": _rel_display(path),
        "bytes": size,
        "size_text": _fmt(size),
        "files": files,
        "risk": risk,
        "selected": bool(selected and size > 0),
    }


def scan_detailed(
    selected_categories: Optional[List[str]] = None,
    progress: Optional[ProgressCb] = None,
    cancel: Optional[CancelToken] = None,
) -> Dict[str, Any]:
    """Scan junk and return categories + selectable items with live progress."""
    cats = targets()
    if selected_categories:
        want = set(selected_categories)
        cats = [t for t in cats if t.key in want]

    items: List[Dict[str, Any]] = []
    total_cats = max(1, len(cats))
    started = time.time()
    cancelled = False

    def check_cancel() -> bool:
        nonlocal cancelled
        if cancel and cancel.cancelled:
            cancelled = True
            return True
        return False

    browser_top = {
        "Google",
        "com.google.Chrome",
        "com.google.Chrome.Canary",
        "com.microsoft.edgemac",
        "org.mozilla.firefox",
        "company.thebrowser.Browser",
        "com.brave.Browser",
        "Chromium",
        "Yarn",
        "pnpm",
    }

    for idx, t in enumerate(cats):
        if check_cancel():
            break
        base_pct = int(idx * 100 / total_cats)
        _emit(
            progress,
            phase="scan",
            percent=base_pct,
            category=t.title,
            category_key=t.key,
            current=f"正在扫描「{t.title}」…",
            found_items=len(items),
            scanned_bytes=sum(i["bytes"] for i in items),
        )

        found_here: List[Dict[str, Any]] = []

        if t.key == "user_caches":
            root = HOME / "Library" / "Caches"
            if root.is_dir():
                try:
                    children = sorted(root.iterdir(), key=lambda p: p.name.lower())
                except OSError:
                    children = []
                for i, child in enumerate(children):
                    if check_cancel():
                        break
                    if child.name in _CACHE_DENY or child.name.startswith("."):
                        continue
                    if child.name in browser_top:
                        continue
                    if "SupTools" in child.name or "SysPulse" in child.name or "SystemMonit" in child.name:
                        continue
                    if i % 3 == 0 or i == len(children) - 1:
                        _emit(
                            progress,
                            phase="scan",
                            percent=base_pct + int((i + 1) / max(1, len(children)) * (100 / total_cats) * 0.9),
                            category=t.title,
                            category_key=t.key,
                            current=_rel_display(child),
                            found_items=len(items) + len(found_here),
                            scanned_bytes=sum(x["bytes"] for x in items) + sum(x["bytes"] for x in found_here),
                        )
                    it = _item(
                        category=t.key,
                        category_title=t.title,
                        name=child.name,
                        path=child,
                        risk=t.risk,
                        selected=True,
                        cancel=cancel,
                    )
                    if it["bytes"] > 0:
                        found_here.append(it)

        elif t.key == "app_support_cache":
            root = HOME / "Library" / "Application Support"
            if root.is_dir():
                try:
                    apps = sorted([p for p in root.iterdir() if p.is_dir()], key=lambda p: p.name.lower())
                except OSError:
                    apps = []
                for i, app in enumerate(apps):
                    if check_cancel():
                        break
                    if app.name in ("MobileSync", "CloudDocs", "SyncServices", "AddressBook", "CallHistoryDB"):
                        continue
                    if i % 4 == 0:
                        _emit(
                            progress,
                            phase="scan",
                            percent=base_pct + int((i + 1) / max(1, len(apps)) * (100 / total_cats) * 0.9),
                            category=t.title,
                            category_key=t.key,
                            current=_rel_display(app),
                            found_items=len(items) + len(found_here),
                            scanned_bytes=sum(x["bytes"] for x in items) + sum(x["bytes"] for x in found_here),
                        )
                    for sub in ("Cache", "Caches", "Logs", "log", "tmp", "Temp"):
                        cand = app / sub
                        if cand.exists():
                            it = _item(
                                category=t.key,
                                category_title=t.title,
                                name=f"{app.name}/{sub}",
                                path=cand,
                                risk=t.risk,
                                selected=True,
                                cancel=cancel,
                            )
                            if it["bytes"] > 4096:
                                found_here.append(it)

        elif t.key == "logs":
            root = HOME / "Library" / "Logs"
            cutoff = time.time() - 7 * 86400
            if root.is_dir():
                try:
                    children = sorted(root.iterdir(), key=lambda p: p.name.lower())
                except OSError:
                    children = []
                for i, child in enumerate(children):
                    if check_cancel():
                        break
                    if "SupTools" in child.name or "SysPulse" in child.name or "SystemMonit" in child.name:
                        continue
                    if i % 2 == 0:
                        _emit(
                            progress,
                            phase="scan",
                            percent=min(99, base_pct + int((i + 1) / max(1, len(children)) * (100 / total_cats) * 0.9)),
                            category=t.title,
                            category_key=t.key,
                            current=_rel_display(child),
                            found_items=len(items) + len(found_here),
                            scanned_bytes=sum(x["bytes"] for x in items) + sum(x["bytes"] for x in found_here),
                        )
                    size = 0
                    files = 0
                    try:
                        if child.is_file():
                            st = child.stat()
                            if st.st_mtime < cutoff:
                                size = st.st_size
                                files = 1
                        else:
                            for path in child.rglob("*"):
                                if check_cancel():
                                    break
                                try:
                                    if path.is_file() and path.stat().st_mtime < cutoff:
                                        size += path.stat().st_size
                                        files += 1
                                except OSError:
                                    continue
                    except OSError:
                        continue
                    if size > 0:
                        found_here.append({
                            "id": f"{t.key}:{uuid.uuid4().hex[:10]}",
                            "category": t.key,
                            "category_title": t.title,
                            "name": child.name,
                            "path": str(child),
                            "path_display": _rel_display(child),
                            "bytes": size,
                            "size_text": _fmt(size),
                            "files": files,
                            "risk": t.risk,
                            "selected": True,
                            "mode": "old_logs",
                            "cutoff_days": 7,
                        })

        elif t.key == "tmp":
            root = Path("/tmp")
            cutoff = time.time() - 2 * 86400
            if root.is_dir():
                try:
                    children = list(root.iterdir())
                except OSError:
                    children = []
                for i, child in enumerate(children):
                    if check_cancel():
                        break
                    try:
                        st = child.lstat()
                        if st.st_mtime >= cutoff:
                            continue
                    except OSError:
                        continue
                    if i % 8 == 0:
                        _emit(
                            progress,
                            phase="scan",
                            percent=base_pct + int((i + 1) / max(1, len(children)) * (100 / total_cats) * 0.9),
                            category=t.title,
                            category_key=t.key,
                            current=_rel_display(child),
                            found_items=len(items) + len(found_here),
                            scanned_bytes=sum(x["bytes"] for x in items) + sum(x["bytes"] for x in found_here),
                        )
                    it = _item(
                        category=t.key,
                        category_title=t.title,
                        name=child.name,
                        path=child,
                        risk=t.risk,
                        selected=True,
                        cancel=cancel,
                    )
                    if it["bytes"] > 0:
                        found_here.append(it)

        elif t.key == "trash":
            root = HOME / ".Trash"
            if root.is_dir():
                try:
                    children = list(root.iterdir())
                except OSError:
                    children = []
                for i, child in enumerate(children):
                    if check_cancel():
                        break
                    if i % 5 == 0:
                        _emit(
                            progress,
                            phase="scan",
                            percent=base_pct + int((i + 1) / max(1, len(children)) * (100 / total_cats) * 0.9),
                            category=t.title,
                            category_key=t.key,
                            current=_rel_display(child),
                            found_items=len(items) + len(found_here),
                            scanned_bytes=sum(x["bytes"] for x in items) + sum(x["bytes"] for x in found_here),
                        )
                    it = _item(
                        category=t.key,
                        category_title=t.title,
                        name=child.name,
                        path=child,
                        risk="caution",
                        selected=False,
                        cancel=cancel,
                    )
                    if it["bytes"] > 0 or child.exists():
                        it["selected"] = False
                        found_here.append(it)

        elif t.key == "installers":
            root = HOME / "Downloads"
            exts = {".dmg", ".pkg", ".zip", ".iso", ".app.zip"}
            max_hits = 60
            hits: List[Tuple[int, Path]] = []
            if root.is_dir():
                _emit(
                    progress,
                    phase="scan",
                    percent=min(99, base_pct + 5),
                    category=t.title,
                    category_key=t.key,
                    current=_rel_display(root),
                    found_items=len(items) + len(found_here),
                    scanned_bytes=sum(x["bytes"] for x in items) + sum(x["bytes"] for x in found_here),
                )
                try:
                    for child in root.iterdir():
                        if check_cancel() or len(hits) >= max_hits:
                            break
                        if child.name.startswith("."):
                            continue
                        name_l = child.name.lower()
                        if not any(name_l.endswith(ext) for ext in exts):
                            continue
                        try:
                            st = child.lstat()
                            if st.st_size < 5 * 1024 * 1024:
                                continue
                            hits.append((int(st.st_size), child))
                        except OSError:
                            continue
                except OSError:
                    pass
            hits.sort(key=lambda x: -x[0])
            for size, fp in hits[:max_hits]:
                if check_cancel():
                    break
                found_here.append({
                    "id": f"{t.key}:{uuid.uuid4().hex[:10]}",
                    "category": t.key,
                    "category_title": t.title,
                    "name": fp.name,
                    "path": str(fp),
                    "path_display": _rel_display(fp),
                    "bytes": size,
                    "size_text": _fmt(size),
                    "files": 1,
                    "risk": "caution",
                    "selected": False,
                    "hint": "安装包 · 确认不再需要后再删",
                })

        elif t.key == "large_files":
            min_bytes = 100 * 1024 * 1024  # 100 MB
            max_hits = 48
            hits: List[Tuple[int, Path]] = []
            installer_exts = (".dmg", ".pkg", ".zip", ".iso")
            for root in t.paths:
                if check_cancel() or len(hits) >= max_hits * 2:
                    break
                if not root.is_dir():
                    continue
                _emit(
                    progress,
                    phase="scan",
                    percent=min(99, base_pct + 5),
                    category=t.title,
                    category_key=t.key,
                    current=_rel_display(root),
                    found_items=len(items) + len(found_here),
                    scanned_bytes=sum(x["bytes"] for x in items) + sum(x["bytes"] for x in found_here),
                )
                try:
                    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
                        if check_cancel():
                            break
                        # Skip hidden / package-ish dirs for speed
                        dirnames[:] = [
                            d for d in dirnames
                            if not d.startswith(".") and not d.endswith(".app") and d not in ("node_modules", ".git", "Library")
                        ]
                        depth = Path(dirpath).relative_to(root).parts if Path(dirpath) != root else ()
                        if len(depth) > 4:
                            dirnames[:] = []
                            continue
                        for name in filenames:
                            if name.startswith("."):
                                continue
                            # Avoid double-counting Downloads installers category
                            if root == HOME / "Downloads" and name.lower().endswith(installer_exts):
                                continue
                            fp = Path(dirpath) / name
                            try:
                                st = fp.lstat()
                                if st.st_size >= min_bytes:
                                    hits.append((int(st.st_size), fp))
                            except OSError:
                                continue
                        if len(hits) >= max_hits * 3:
                            break
                except OSError:
                    continue
            hits.sort(key=lambda x: -x[0])
            for size, fp in hits[:max_hits]:
                if check_cancel():
                    break
                found_here.append({
                    "id": f"{t.key}:{uuid.uuid4().hex[:10]}",
                    "category": t.key,
                    "category_title": t.title,
                    "name": fp.name,
                    "path": str(fp),
                    "path_display": _rel_display(fp),
                    "bytes": size,
                    "size_text": _fmt(size),
                    "files": 1,
                    "risk": "caution",
                    "selected": False,
                    "hint": "大文件 · 请确认后再删",
                })

        else:
            # Generic path targets (browser / xcode / pip / npm / homebrew / ios / docker / …)
            seen: Set[str] = set()
            for p in t.paths:
                if check_cancel():
                    break
                if not p.exists():
                    continue
                keyp = str(p.resolve()) if p.exists() else str(p)
                if keyp in seen:
                    continue
                seen.add(keyp)
                _emit(
                    progress,
                    phase="scan",
                    percent=min(99, base_pct + 10),
                    category=t.title,
                    category_key=t.key,
                    current=_rel_display(p),
                    found_items=len(items) + len(found_here),
                    scanned_bytes=sum(x["bytes"] for x in items) + sum(x["bytes"] for x in found_here),
                )
                default_selected = t.risk != "caution"
                # Docker.raw and huge single files: list as one item
                if p.is_file() or p.is_symlink():
                    it = _item(
                        category=t.key,
                        category_title=t.title,
                        name=p.name,
                        path=p,
                        risk=t.risk,
                        selected=default_selected,
                        cancel=cancel,
                    )
                    if it["bytes"] > 0:
                        found_here.append(it)
                    continue
                if p.is_dir():
                    try:
                        children = list(p.iterdir())
                    except OSError:
                        children = []
                    # For browser / large roots, list top-level; for small caches list children
                    collapse_keys = (
                        "browser", "npm", "pip", "homebrew", "ios_backups",
                        "safari", "mail", "spotify", "pnpm_store", "docker",
                        "xcode_simulators", "chat", "dev_stores",
                    )
                    if t.key in collapse_keys and not children:
                        it = _item(
                            category=t.key,
                            category_title=t.title,
                            name=p.name,
                            path=p,
                            risk=t.risk,
                            selected=default_selected,
                            cancel=cancel,
                        )
                        if it["bytes"] > 0:
                            found_here.append(it)
                    elif t.key in (
                        "browser", "pip", "homebrew", "npm", "safari", "spotify",
                        "mail", "pnpm_store", "chat", "dev_stores",
                    ) or len(children) <= 1:
                        it = _item(
                            category=t.key,
                            category_title=t.title,
                            name=p.name if p.name else _rel_display(p),
                            path=p,
                            risk=t.risk,
                            selected=default_selected,
                            cancel=cancel,
                        )
                        if it["bytes"] > 0:
                            found_here.append(it)
                    elif t.key in ("docker", "xcode_simulators", "ios_backups"):
                        # Show top-level children so user can pick subsets
                        for child in children:
                            if check_cancel():
                                break
                            if child.name.startswith("."):
                                continue
                            it = _item(
                                category=t.key,
                                category_title=t.title,
                                name=child.name,
                                path=child,
                                risk=t.risk,
                                selected=False if t.key == "docker" else default_selected,
                                cancel=cancel,
                            )
                            if it["bytes"] > 0:
                                found_here.append(it)
                    else:
                        for child in children:
                            if check_cancel():
                                break
                            it = _item(
                                category=t.key,
                                category_title=t.title,
                                name=child.name,
                                path=child,
                                risk=t.risk,
                                selected=default_selected,
                                cancel=cancel,
                            )
                            if it["bytes"] > 0:
                                found_here.append(it)

        items.extend(found_here)

    items.sort(key=lambda x: (-int(x.get("bytes") or 0), x.get("category", ""), x.get("name", "")))

    categories: List[Dict[str, Any]] = []
    by_cat: Dict[str, List[Dict[str, Any]]] = {}
    for it in items:
        by_cat.setdefault(it["category"], []).append(it)

    meta = {t.key: t for t in targets()}
    for key, group in by_cat.items():
        t = meta.get(key)
        total = sum(int(i["bytes"]) for i in group)
        categories.append({
            "key": key,
            "title": t.title if t else key,
            "detail": t.detail if t else "",
            "risk": t.risk if t else "safe",
            "icon": t.icon if t else "folder",
            "bytes": total,
            "size_text": _fmt(total),
            "count": len(group),
            "selected_count": sum(1 for i in group if i.get("selected")),
        })
    categories.sort(key=lambda c: -c["bytes"])

    total_bytes = sum(int(i["bytes"]) for i in items)
    selected_bytes = sum(int(i["bytes"]) for i in items if i.get("selected"))
    safe_bytes = sum(int(i["bytes"]) for i in items if i.get("risk") != "caution")
    caution_bytes = sum(int(i["bytes"]) for i in items if i.get("risk") == "caution")
    trash_bytes = sum(int(i["bytes"]) for i in items if i.get("category") == "trash")

    # Smart recommend: selected safe items + oversized safe caches ≥ 20MB
    recommend_ids = [
        str(i["id"]) for i in items
        if i.get("risk") != "caution" and (
            i.get("selected") or int(i.get("bytes") or 0) >= 20 * 1024 * 1024
        )
    ]
    recommend_bytes = sum(
        int(i["bytes"]) for i in items if str(i.get("id")) in set(recommend_ids)
    )

    insights = [
        {
            "key": "safe",
            "label": "建议清理",
            "value": _fmt(recommend_bytes or safe_bytes),
            "detail": f"{len(recommend_ids)} 项安全可清",
            "tone": "good",
        },
        {
            "key": "caution",
            "label": "谨慎项",
            "value": _fmt(caution_bytes),
            "detail": "需手动确认",
            "tone": "warn",
        },
        {
            "key": "top",
            "label": "最大分类",
            "value": (categories[0]["title"] if categories else "—"),
            "detail": (categories[0]["size_text"] if categories else ""),
            "tone": "info",
        },
        {
            "key": "trash",
            "label": "废纸篓",
            "value": _fmt(trash_bytes),
            "detail": "可一键清空",
            "tone": "warn" if trash_bytes else "info",
        },
    ]

    _emit(
        progress,
        phase="scan_done" if not cancelled else "scan_cancelled",
        percent=100 if not cancelled else int(len(items) and 99 or 0),
        category="完成" if not cancelled else "已取消",
        current="扫描完成" if not cancelled else "扫描已取消",
        found_items=len(items),
        scanned_bytes=total_bytes,
        elapsed=round(time.time() - started, 2),
    )

    return {
        "items": items,
        "categories": categories,
        "insights": insights,
        "recommend_ids": recommend_ids,
        "recommend_bytes": recommend_bytes,
        "recommend_text": _fmt(recommend_bytes),
        "total_bytes": total_bytes,
        "total_text": _fmt(total_bytes),
        "selected_bytes": selected_bytes,
        "selected_text": _fmt(selected_bytes),
        "safe_bytes": safe_bytes,
        "safe_text": _fmt(safe_bytes),
        "caution_bytes": caution_bytes,
        "caution_text": _fmt(caution_bytes),
        "trash_bytes": trash_bytes,
        "trash_text": _fmt(trash_bytes),
        "item_count": len(items),
        "elapsed": round(time.time() - started, 2),
        "cancelled": cancelled,
    }


def empty_trash(
    progress: Optional[ProgressCb] = None,
    cancel: Optional[CancelToken] = None,
) -> CleanResult:
    """Hard-delete everything in ~/.Trash."""
    root = HOME / ".Trash"
    items: List[Dict[str, Any]] = []
    if root.is_dir():
        try:
            for child in root.iterdir():
                items.append({
                    "id": f"trash:{uuid.uuid4().hex[:8]}",
                    "category": "trash",
                    "category_title": "废纸篓",
                    "name": child.name,
                    "path": str(child),
                    "path_display": _rel_display(child),
                    "risk": "caution",
                })
        except OSError:
            pass
    return clean_items(items, progress=progress, move_to_trash=False, cancel=cancel)


def _trash_path(path: Path) -> bool:
    """Move path to Trash via NSFileManager. Returns True on success."""
    try:
        from Foundation import NSFileManager, NSURL  # type: ignore

        fm = NSFileManager.defaultManager()
        url = NSURL.fileURLWithPath_(str(path))
        result = fm.trashItemAtURL_resultingItemURL_error_(url, None, None)
        if isinstance(result, tuple):
            return bool(result[0])
        return bool(result)
    except Exception:
        try:
            trash = HOME / ".Trash"
            trash.mkdir(parents=True, exist_ok=True)
            dest = trash / path.name
            if dest.exists():
                dest = trash / f"{path.stem}-{uuid.uuid4().hex[:6]}{path.suffix}"
            shutil.move(str(path), str(dest))
            return True
        except Exception:
            return False


def _rm_path(
    path: Path,
    result: CleanResult,
    mode: str = "all",
    cutoff_days: int = 7,
    move_to_trash: bool = False,
) -> None:
    try:
        if mode == "old_logs":
            cutoff = time.time() - cutoff_days * 86400
            if path.is_file():
                st = path.stat()
                if st.st_mtime < cutoff:
                    size = st.st_size
                    if move_to_trash and _trash_path(path):
                        result.freed_bytes += size
                        result.removed_items += 1
                    else:
                        path.unlink(missing_ok=True)
                        result.freed_bytes += size
                        result.removed_items += 1
                return
            if path.is_dir():
                for fp in list(path.rglob("*")):
                    try:
                        if fp.is_file() and fp.stat().st_mtime < cutoff:
                            size = fp.stat().st_size
                            if move_to_trash and _trash_path(fp):
                                result.freed_bytes += size
                                result.removed_items += 1
                            else:
                                fp.unlink(missing_ok=True)
                                result.freed_bytes += size
                                result.removed_items += 1
                    except OSError as exc:
                        result.errors.append(f"{fp}: {exc}")
                return

        if not path.exists() and not path.is_symlink():
            return

        if move_to_trash:
            size = path.lstat().st_size if path.is_file() or path.is_symlink() else _dir_size(path)
            if _trash_path(path):
                result.freed_bytes += size
                result.removed_items += 1
                return
            # fall through to hard delete if trash fails

        if path.is_symlink() or path.is_file():
            size = path.lstat().st_size
            path.unlink(missing_ok=True)
            result.freed_bytes += size
            result.removed_items += 1
            return

        if path.is_dir():
            size_before = _dir_size(path)
            try:
                shutil.rmtree(path, ignore_errors=False)
            except Exception:
                # Partial / locked trees: delete what we can
                freed = 0
                for root, dirs, files in os.walk(path, topdown=False):
                    for name in files:
                        fp = Path(root) / name
                        try:
                            sz = fp.lstat().st_size
                            fp.unlink()
                            freed += sz
                        except OSError as exc:
                            result.errors.append(f"{fp}: {exc}")
                    for name in dirs:
                        dp = Path(root) / name
                        try:
                            dp.rmdir()
                        except OSError:
                            try:
                                shutil.rmtree(dp, ignore_errors=True)
                            except Exception:
                                pass
                try:
                    path.rmdir()
                except OSError:
                    shutil.rmtree(path, ignore_errors=True)
                if path.exists():
                    result.errors.append(f"{path}: 部分文件无法删除（可能被占用）")
                result.freed_bytes += freed if freed else max(0, size_before - _dir_size(path))
                if freed or not path.exists():
                    result.removed_items += 1
                return
            result.freed_bytes += size_before
            result.removed_items += 1
    except Exception as exc:  # noqa: BLE001
        result.errors.append(f"{path}: {exc}")


def clean_items(
    items: List[Dict[str, Any]],
    progress: Optional[ProgressCb] = None,
    move_to_trash: bool = False,
    cancel: Optional[CancelToken] = None,
) -> CleanResult:
    """Delete specifically selected scan items."""
    result = CleanResult(moved_to_trash=bool(move_to_trash))
    total = max(1, len(items))
    for i, it in enumerate(items):
        if cancel and cancel.cancelled:
            result.cancelled = True
            break
        path = Path(it.get("path") or "")
        name = it.get("name") or path.name
        # Never "trash-to-trash" for items already in Trash — always hard delete
        use_trash = move_to_trash and it.get("category") != "trash"
        _emit(
            progress,
            phase="clean",
            percent=int(i * 100 / total),
            category=it.get("category_title") or it.get("category") or "",
            current=it.get("path_display") or str(path),
            cleaned_items=result.removed_items,
            freed_bytes=result.freed_bytes,
            index=i + 1,
            total=total,
        )
        if not path.exists():
            continue
        before = result.freed_bytes
        _rm_path(
            path,
            result,
            mode=str(it.get("mode") or "all"),
            cutoff_days=int(it.get("cutoff_days") or 7),
            move_to_trash=use_trash,
        )
        freed = result.freed_bytes - before
        result.details.append({
            "id": it.get("id"),
            "name": name,
            "category": it.get("category"),
            "freed": freed,
            "freed_text": _fmt(freed),
            "ok": freed > 0 or not path.exists(),
        })

    _emit(
        progress,
        phase="clean_done" if not result.cancelled else "clean_cancelled",
        percent=100,
        category="完成" if not result.cancelled else "已取消",
        current="清理完成" if not result.cancelled else "清理已取消",
        cleaned_items=result.removed_items,
        freed_bytes=result.freed_bytes,
    )
    return result


# Backward-compatible wrappers used by older UI paths
def scan(selected: Optional[List[str]] = None) -> List[Dict]:
    data = scan_detailed(selected_categories=selected)
    out = []
    for c in data["categories"]:
        out.append({
            "key": c["key"],
            "title": c["title"],
            "detail": c["detail"],
            "risk": c["risk"],
            "bytes": c["bytes"],
            "exists": c["count"] > 0,
            "size_text": c["size_text"],
        })
    return out


def clean(selected: Optional[List[str]] = None, progress: Optional[Callable[[str], None]] = None) -> CleanResult:
    data = scan_detailed(selected_categories=selected)
    items = [i for i in data["items"] if i.get("selected") or (selected and i["category"] in set(selected or []))]
    if selected:
        keys = set(selected)
        items = [i for i in data["items"] if i["category"] in keys]
        # respect caution defaults: if trash explicitly selected, include
        for i in items:
            i["selected"] = True

    def _p(info: Dict[str, Any]) -> None:
        if progress:
            progress(str(info.get("current") or info.get("category") or ""))

    return clean_items(items, progress=_p if progress else None)
