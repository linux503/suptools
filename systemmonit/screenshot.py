"""macOS screenshot helper via /usr/sbin/screencapture + annotate draft flow."""

from __future__ import annotations

import base64
import re
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .brand import SCREENSHOT_DIRNAME, support_dir
from . import permissions as perm_mod

CAPTURE = "/usr/sbin/screencapture"
DEFAULT_DIR = Path.home() / "Pictures" / SCREENSHOT_DIRNAME
DRAFT_DIR = support_dir() / "ScreenshotDrafts"


def ensure_dir(path: Optional[Path] = None) -> Path:
    root = Path(path) if path else DEFAULT_DIR
    root.mkdir(parents=True, exist_ok=True)
    return root


def ensure_draft_dir() -> Path:
    DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    return DRAFT_DIR


def _stamp_name(prefix: str = "Screenshot") -> str:
    return f"{prefix}-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}.png"


def default_save_path(directory: Optional[Path] = None) -> Path:
    return ensure_dir(directory) / _stamp_name()


def draft_path() -> Path:
    return ensure_draft_dir() / f"draft-{uuid.uuid4().hex}.png"


def _run(cmd: List[str], timeout: float = 180.0) -> Dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "ok": proc.returncode == 0,
            "code": int(proc.returncode),
            "stderr": (proc.stderr or "").strip(),
            "stdout": (proc.stdout or "").strip(),
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "code": -1, "stderr": "截图超时或已取消", "stdout": ""}
    except Exception as exc:
        return {"ok": False, "code": -1, "stderr": str(exc), "stdout": ""}


def capture(
    *,
    mode: str = "selection",
    to_clipboard: bool = False,
    include_cursor: bool = False,
    delay: float = 0.0,
    hide_shadow: bool = True,
    save_dir: Optional[Path] = None,
    path: Optional[Path] = None,
    draft: bool = True,
) -> Dict[str, Any]:
    """
    mode:
      - selection: interactive region / window (-i)
      - full: entire main display
      - window: interactive window pick (-i, user can press Space)

    When draft=True (default), always writes a temp PNG for the annotate editor.
    to_clipboard only mirrors into clipboard during capture when draft=False.
    """
    mode = mode if mode in ("selection", "full", "window") else "selection"
    out_path: Optional[Path]
    if path is not None:
        out_path = Path(path)
    elif draft:
        out_path = draft_path()
    elif to_clipboard:
        out_path = None
    else:
        out_path = default_save_path(save_dir)

    if delay and delay > 0:
        time.sleep(float(delay))

    cmd = [CAPTURE, "-x"]  # mute shutter
    if include_cursor and mode == "full":
        cmd.append("-C")
    if mode in ("selection", "window"):
        cmd.append("-i")
    if hide_shadow:
        cmd.append("-o")
    if to_clipboard and not draft:
        cmd.append("-c")
        if out_path is not None:
            cmd.append(str(out_path))
    else:
        assert out_path is not None
        cmd.append(str(out_path))

    result = _run(cmd, timeout=300.0 if mode != "full" else 60.0)
    if not result["ok"]:
        if out_path and out_path.exists() and out_path.stat().st_size == 0:
            try:
                out_path.unlink()
            except Exception:
                pass
        msg = result.get("stderr") or "截图取消或失败"
        need_perm = perm_mod.looks_like_screen_permission_error(msg, code=result.get("code"))
        granted = perm_mod.screen_capture_granted()
        if need_perm or granted is False:
            msg = perm_mod.screen_permission_message()

            need_perm = True
        return {
            "ok": False,
            "error": msg,
            "path": str(out_path) if out_path else "",
            "mode": mode,
            "clipboard": to_clipboard,
            "draft": bool(draft),
            "permission": "screen" if need_perm else "",
        }

    if out_path and (not out_path.exists() or out_path.stat().st_size == 0):
        if out_path.exists():
            try:
                out_path.unlink()
            except Exception:
                pass
        return {
            "ok": False,
            "error": "已取消截图",
            "path": "",
            "mode": mode,
            "clipboard": to_clipboard,
            "draft": bool(draft),
        }

    info = file_info(out_path) if out_path and out_path.exists() else None
    return {
        "ok": True,
        "path": str(out_path) if out_path else "",
        "mode": mode,
        "clipboard": to_clipboard,
        "draft": bool(draft and out_path is not None),
        "file": info,
        "message": "请标注后保存" if draft else (
            "已复制到剪贴板" if to_clipboard and not out_path else "截图已保存"
        ),
    }


def file_info(path: Path) -> Dict[str, Any]:
    st = path.stat()
    return {
        "name": path.name,
        "path": str(path),
        "bytes": int(st.st_size),
        "size_text": _fmt_bytes(st.st_size),
        "mtime": float(st.st_mtime),
        "mtime_text": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
    }


def list_recent(limit: int = 24, directory: Optional[Path] = None) -> List[Dict[str, Any]]:
    root = ensure_dir(directory)
    files = sorted(
        [p for p in root.glob("*.png") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    out = []
    for p in files[: max(1, limit)]:
        try:
            out.append(file_info(p))
        except Exception:
            continue
    return out


def reveal(path: str) -> bool:
    p = Path(path)
    if not p.exists():
        return False
    try:
        subprocess.Popen(["open", "-R", str(p)])
        return True
    except Exception:
        return False


def open_file(path: str) -> bool:
    p = Path(path)
    if not p.exists():
        return False
    try:
        subprocess.Popen(["open", str(p)])
        return True
    except Exception:
        return False


def open_folder(directory: Optional[Path] = None) -> bool:
    root = ensure_dir(directory)
    try:
        subprocess.Popen(["open", str(root)])
        return True
    except Exception:
        return False


def _allowed_delete(path: Path) -> bool:
    try:
        resolved = path.resolve()
        resolved.relative_to(DEFAULT_DIR.resolve())
        return True
    except Exception:
        pass
    try:
        resolved = path.resolve()
        resolved.relative_to(DRAFT_DIR.resolve())
        return True
    except Exception:
        return False


def delete_file(path: str) -> bool:
    p = Path(path)
    if not p.exists() or p.suffix.lower() != ".png":
        return False
    if not _allowed_delete(p):
        return False
    try:
        p.unlink()
        return True
    except Exception:
        return False


def discard_draft(path: str) -> bool:
    return delete_file(path)


def copy_to_clipboard(path: str) -> bool:
    p = Path(path)
    if not p.exists():
        return False
    script = f'''
    set theFile to POSIX file "{p}"
    set theImage to (read theFile as «class PNGf»)
    set the clipboard to theImage
    '''
    try:
        r = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=20,
        )
        return r.returncode == 0
    except Exception:
        return False


def copy_png_bytes(data: bytes) -> bool:
    if not data:
        return False
    tmp = draft_path()
    try:
        tmp.write_bytes(data)
        ok = copy_to_clipboard(str(tmp))
        return ok
    except Exception:
        return False
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass


def _decode_data_url(data_url: str) -> Optional[bytes]:
    if not data_url:
        return None
    m = re.match(
        r"^data:image/(?:png|jpeg|jpg);base64,(.+)$",
        data_url.strip(),
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not m:
        # raw base64 fallback
        try:
            return base64.b64decode(data_url)
        except Exception:
            return None
    try:
        return base64.b64decode(m.group(1))
    except Exception:
        return None


def save_annotated(
    data_url: str,
    *,
    draft_path_str: str = "",
    copy: bool = False,
) -> Dict[str, Any]:
    """Commit annotated PNG from editor data URL into Pictures/SupTools."""
    raw = _decode_data_url(data_url)
    if not raw:
        return {"ok": False, "error": "无效的图片数据"}
    out = default_save_path()
    try:
        out.write_bytes(raw)
    except Exception as exc:
        return {"ok": False, "error": f"保存失败：{exc}"}

    if draft_path_str:
        discard_draft(draft_path_str)

    copied = False
    if copy:
        copied = copy_to_clipboard(str(out))

    info = file_info(out)
    return {
        "ok": True,
        "path": str(out),
        "file": info,
        "copied": copied,
        "message": "已保存并复制" if copied else "截图已保存",
        "preview": read_preview_base64(str(out)),
    }


def read_preview_base64(path: str, max_bytes: int = 12_000_000) -> Optional[str]:
    """PNG as data URL for in-app preview / annotate editor."""
    p = Path(path)
    if not p.exists() or p.stat().st_size > max_bytes:
        return None
    try:
        raw = p.read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception:
        return None


def _fmt_bytes(n: int) -> str:
    v = float(max(0, n))
    for unit in ("B", "KB", "MB", "GB"):
        if v < 1024 or unit == "GB":
            if unit == "B":
                return f"{int(v)} {unit}"
            return f"{v:.1f} {unit}"
        v /= 1024.0
    return f"{n} B"


def folder_payload() -> Dict[str, Any]:
    root = ensure_dir()
    items = list_recent(24)
    return {
        "folder": str(root),
        "count": len(items),
        "items": items,
    }
