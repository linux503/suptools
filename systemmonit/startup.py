"""Startup / login item manager — list and disable user LaunchAgents & login items."""

from __future__ import annotations

import os
import plistlib
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

HOME = Path.home()
ProgressCb = Callable[[Dict[str, Any]], None]

_PROTECTED_LABELS = {
    "com.suptools.app",
    "com.apple.",  # prefix check separately
}

_USER_AGENTS = HOME / "Library" / "LaunchAgents"
_SYSTEM_AGENTS = Path("/Library/LaunchAgents")
_DISABLED_DIR = HOME / "Library" / "Application Support" / "SupTools" / "DisabledLaunchAgents"


def _emit(progress: Optional[ProgressCb], **kwargs) -> None:
    if progress:
        try:
            progress(kwargs)
        except Exception:
            pass


def _uid() -> int:
    try:
        return int(os.getuid())
    except Exception:
        return 501


def _rel(path: Path) -> str:
    try:
        return str(path).replace(str(HOME), "~")
    except Exception:
        return str(path)


def _read_plist(path: Path) -> Dict[str, Any]:
    try:
        with path.open("rb") as fh:
            data = plistlib.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _run(args: List[str], timeout: float = 8.0) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return int(proc.returncode), proc.stdout or "", proc.stderr or ""
    except Exception as exc:
        return 1, "", str(exc)


def _disabled_labels() -> Set[str]:
    """Parse `launchctl print-disabled gui/$UID` output."""
    code, out, _ = _run(["/bin/launchctl", "print-disabled", f"gui/{_uid()}"])
    disabled: Set[str] = set()
    if code != 0:
        return disabled
    for line in out.splitlines():
        line = line.strip().rstrip(",")
        # "com.example.foo" => enabled
        # or "\t\"com.example.foo\" => disabled
        if "=>" not in line:
            continue
        left, right = [x.strip() for x in line.split("=>", 1)]
        label = left.strip().strip('"').strip("'")
        state = right.strip().lower()
        if not label:
            continue
        if state in ("disabled", "true"):
            # print-disabled shows: "label" => true  means DISABLED
            disabled.add(label)
        elif "disabled" in state:
            disabled.add(label)
    return disabled


def _loaded_labels() -> Set[str]:
    code, out, _ = _run(["/bin/launchctl", "list"])
    loaded: Set[str] = set()
    if code != 0:
        return loaded
    for i, line in enumerate(out.splitlines()):
        if i == 0 and line.lower().startswith("pid"):
            continue
        parts = line.split()
        if len(parts) >= 3:
            loaded.add(parts[-1])
    return loaded


def _is_protected(label: str, path: Optional[Path] = None) -> bool:
    lab = (label or "").lower()
    if not lab:
        return True
    if lab.startswith("com.apple."):
        return True
    if "suptools" in lab or "syspulse" in lab or "systemmonit" in lab:
        return True
    if path and ("SupTools" in str(path) or "SysPulse" in str(path)):
        return True
    return False


def _program_from_plist(info: Dict[str, Any]) -> str:
    prog = info.get("Program")
    if isinstance(prog, str) and prog.strip():
        return prog
    args = info.get("ProgramArguments")
    if isinstance(args, (list, tuple)) and args:
        return str(args[0])
    return ""


def _display_name(label: str, program: str, path: Path) -> str:
    if program:
        name = Path(program).name
        if name and name not in ("open", "bash", "sh", "zsh", "python", "python3"):
            return name
    # last component of label
    if "." in label:
        return label.split(".")[-1]
    return path.stem or label


def _scan_agents(
    root: Path,
    *,
    scope: str,
    risk: str,
    disabled: Set[str],
    loaded: Set[str],
    cancel_check: Optional[Callable[[], bool]] = None,
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    if not root.is_dir():
        return items
    try:
        children = sorted(root.glob("*.plist"))
    except OSError:
        return items
    for plist_path in children:
        if cancel_check and cancel_check():
            break
        info = _read_plist(plist_path)
        label = str(info.get("Label") or plist_path.stem)
        program = _program_from_plist(info)
        protected = _is_protected(label, plist_path)
        is_disabled = label in disabled
        is_loaded = label in loaded
        run_at_load = bool(info.get("RunAtLoad"))
        keep_alive = bool(info.get("KeepAlive")) if not isinstance(info.get("KeepAlive"), dict) else True
        items.append({
            "id": f"agent:{uuid.uuid4().hex[:10]}",
            "kind": "launch_agent",
            "scope": scope,
            "label": label,
            "name": _display_name(label, program, plist_path),
            "path": str(plist_path),
            "path_display": _rel(plist_path),
            "program": program,
            "program_display": _rel(Path(program)) if program else "",
            "enabled": (not is_disabled) and not protected,
            "disabled": is_disabled,
            "loaded": is_loaded,
            "run_at_load": run_at_load,
            "keep_alive": keep_alive,
            "protected": protected,
            "risk": "safe" if scope == "user" else risk,
            "detail": (
                ("已禁用" if is_disabled else ("运行中" if is_loaded else "已加载配置"))
                + (" · 登录启动" if run_at_load else "")
            ),
        })
    return items


def _scan_login_items(cancel_check: Optional[Callable[[], bool]] = None) -> List[Dict[str, Any]]:
    """Legacy 'Open at Login' apps via System Events."""
    items: List[Dict[str, Any]] = []
    script = """
    tell application "System Events"
      set out to {}
      repeat with itm in login items
        set n to name of itm
        try
          set p to path of itm
        on error
          set p to ""
        end try
        try
          set h to hidden of itm
        on error
          set h to false
        end try
        set end of out to n & tab & p & tab & h
      end repeat
      set AppleScript's text item delimiters to linefeed
      return out as text
    end tell
    """
    code, out, err = _run(["/usr/bin/osascript", "-e", script], timeout=12.0)
    if code != 0:
        return items
    for line in out.splitlines():
        if cancel_check and cancel_check():
            break
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        name = (parts[0] if parts else "").strip()
        path = (parts[1] if len(parts) > 1 else "").strip()
        hidden = (parts[2] if len(parts) > 2 else "").strip().lower() in ("true", "yes", "1")
        if not name:
            continue
        protected = _is_protected(name, Path(path) if path else None)
        items.append({
            "id": f"login:{uuid.uuid4().hex[:10]}",
            "kind": "login_item",
            "scope": "user",
            "label": name,
            "name": name,
            "path": path,
            "path_display": _rel(Path(path)) if path else name,
            "program": path,
            "program_display": _rel(Path(path)) if path else "",
            "enabled": not protected,
            "disabled": False,
            "loaded": True,
            "run_at_load": True,
            "keep_alive": False,
            "protected": protected,
            "risk": "safe",
            "hidden": hidden,
            "detail": "登录时打开" + (" · 隐藏" if hidden else ""),
        })
    return items


def list_startup(
    progress: Optional[ProgressCb] = None,
    cancel: Any = None,
) -> Dict[str, Any]:
    started = time.time()
    cancelled = False

    def cancelled_now() -> bool:
        nonlocal cancelled
        if cancel is not None and getattr(cancel, "cancelled", False):
            cancelled = True
            return True
        return False

    _emit(progress, phase="list", percent=5, current="读取 launchd 状态…")
    disabled = _disabled_labels()
    loaded = _loaded_labels()

    items: List[Dict[str, Any]] = []

    _emit(progress, phase="list", percent=20, current="扫描用户 LaunchAgents…")
    items.extend(_scan_agents(
        _USER_AGENTS, scope="user", risk="safe",
        disabled=disabled, loaded=loaded, cancel_check=cancelled_now,
    ))

    _emit(progress, phase="list", percent=45, current="扫描登录项…")
    items.extend(_scan_login_items(cancel_check=cancelled_now))

    _emit(progress, phase="list", percent=70, current="扫描系统 LaunchAgents…")
    items.extend(_scan_agents(
        _SYSTEM_AGENTS, scope="system", risk="caution",
        disabled=disabled, loaded=loaded, cancel_check=cancelled_now,
    ))

    # Sort: enabled user first, then by name
    items.sort(key=lambda it: (
        0 if it.get("scope") == "user" else 1,
        1 if it.get("disabled") else 0,
        1 if it.get("protected") else 0,
        str(it.get("name") or "").lower(),
    ))

    enabled_n = sum(1 for it in items if it.get("enabled") and not it.get("disabled") and not it.get("protected"))
    disabled_n = sum(1 for it in items if it.get("disabled"))
    login_n = sum(1 for it in items if it.get("kind") == "login_item")
    agent_n = sum(1 for it in items if it.get("kind") == "launch_agent")

    _emit(progress, phase="list_done", percent=100, current="扫描完成", found=len(items))
    return {
        "items": items,
        "item_count": len(items),
        "enabled_count": enabled_n,
        "disabled_count": disabled_n,
        "login_count": login_n,
        "agent_count": agent_n,
        "elapsed": round(time.time() - started, 2),
        "cancelled": cancelled,
        "settings_hint": "部分「允许在后台」项目需在系统设置 → 通用 → 登录项中管理",
    }


def _disable_launch_agent(path: Path, label: str) -> Tuple[bool, str]:
    domain = f"gui/{_uid()}"
    target = f"{domain}/{label}"
    # Unload if running
    _run(["/bin/launchctl", "bootout", target], timeout=6.0)
    _run(["/bin/launchctl", "unload", "-w", str(path)], timeout=6.0)
    code, _, err = _run(["/bin/launchctl", "disable", target], timeout=6.0)
    # Also move user agent aside so it won't be re-loaded casually
    if path.is_file() and str(path).startswith(str(_USER_AGENTS)):
        try:
            _DISABLED_DIR.mkdir(parents=True, exist_ok=True)
            dest = _DISABLED_DIR / path.name
            if dest.exists():
                dest = _DISABLED_DIR / f"{path.stem}-{uuid.uuid4().hex[:6]}.plist"
            path.replace(dest)
            return True, f"已禁用并移至 {_rel(dest)}"
        except Exception as exc:
            if code == 0:
                return True, "已禁用（文件保留）"
            return False, str(exc) or err or "禁用失败"
    if code == 0:
        return True, "已禁用"
    # System agents may fail without privileges
    return False, err.strip() or "禁用失败（可能需要管理员权限）"


def _enable_launch_agent(path: Path, label: str) -> Tuple[bool, str]:
    domain = f"gui/{_uid()}"
    target = f"{domain}/{label}"
    # Restore from disabled folder if needed
    src = path
    if not src.is_file():
        cand = _DISABLED_DIR / Path(path).name
        if cand.is_file():
            try:
                _USER_AGENTS.mkdir(parents=True, exist_ok=True)
                dest = _USER_AGENTS / cand.name
                cand.replace(dest)
                src = dest
            except Exception as exc:
                return False, f"无法恢复配置文件: {exc}"
    if not src.is_file():
        return False, "找不到 LaunchAgent 配置文件"
    _run(["/bin/launchctl", "enable", target], timeout=6.0)
    code, _, err = _run(["/bin/launchctl", "bootstrap", domain, str(src)], timeout=8.0)
    if code != 0:
        # fallback older load
        code2, _, err2 = _run(["/bin/launchctl", "load", "-w", str(src)], timeout=8.0)
        if code2 != 0:
            return False, (err or err2 or "启用失败").strip()
    return True, "已启用"


def _remove_login_item(name: str) -> Tuple[bool, str]:
    # Escape quotes in name for AppleScript
    safe = name.replace("\\", "\\\\").replace('"', '\\"')
    script = f'tell application "System Events" to delete login item "{safe}"'
    code, _, err = _run(["/usr/bin/osascript", "-e", script], timeout=10.0)
    if code == 0:
        return True, "已从登录项移除"
    return False, (err or "移除登录项失败").strip()


def set_item_enabled(
    item: Dict[str, Any],
    enabled: bool,
) -> Dict[str, Any]:
    """Enable or disable one startup item. Returns result payload."""
    kind = str(item.get("kind") or "")
    label = str(item.get("label") or "")
    path = Path(str(item.get("path") or ""))
    name = str(item.get("name") or label)

    if item.get("protected") or _is_protected(label, path if path.as_posix() != "." else None):
        return {"ok": False, "error": "受保护项目，无法修改", "label": label, "name": name}

    if kind == "login_item":
        if enabled:
            return {
                "ok": False,
                "error": "登录项需在「系统设置 → 通用 → 登录项」中重新添加",
                "label": label,
                "name": name,
                "open_settings": True,
            }
        ok, msg = _remove_login_item(name)
        return {"ok": ok, "message": msg, "error": "" if ok else msg, "label": label, "name": name, "enabled": False}

    if kind == "launch_agent":
        if path.as_posix() == "." or not label:
            return {"ok": False, "error": "无效的服务项", "label": label, "name": name}
        if str(path).startswith("/Library/") and not enabled:
            # Try disable without moving file
            domain = f"gui/{_uid()}"
            target = f"{domain}/{label}"
            _run(["/bin/launchctl", "bootout", target], timeout=6.0)
            code, _, err = _run(["/bin/launchctl", "disable", target], timeout=6.0)
            if code != 0:
                return {
                    "ok": False,
                    "error": (err or "系统级服务禁用失败，可能需要管理员权限").strip(),
                    "label": label,
                    "name": name,
                }
            return {"ok": True, "message": "已禁用系统 LaunchAgent", "label": label, "name": name, "enabled": False}
        if enabled:
            ok, msg = _enable_launch_agent(path, label)
        else:
            ok, msg = _disable_launch_agent(path, label)
        return {
            "ok": ok,
            "message": msg if ok else "",
            "error": "" if ok else msg,
            "label": label,
            "name": name,
            "enabled": bool(enabled) if ok else (not enabled),
        }

    return {"ok": False, "error": f"未知类型: {kind}", "label": label, "name": name}


def open_login_items_settings() -> bool:
    """Open System Settings → Login Items (best-effort)."""
    urls = [
        "x-apple.systempreferences:com.apple.LoginItems-Settings.extension",
        "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?LoginItems",
        "/System/Library/PreferencePanes/Accounts.prefPane",
    ]
    for u in urls:
        code, _, _ = _run(["/usr/bin/open", u], timeout=5.0)
        if code == 0:
            return True
    code, _, _ = _run(["/usr/bin/open", "-b", "com.apple.systempreferences"], timeout=5.0)
    return code == 0
