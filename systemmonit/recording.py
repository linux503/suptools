"""macOS screen recording via /usr/sbin/screencapture -v."""

from __future__ import annotations

import base64
import signal
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .brand import SCREENSHOT_DIRNAME, support_dir
from . import permissions as perm_mod
from .native_helper import screencapture_command

CAPTURE = "/usr/sbin/screencapture"
DEFAULT_DIR = Path.home() / "Movies" / SCREENSHOT_DIRNAME
DRAFT_DIR = support_dir() / "RecordingDrafts"


def ensure_dir(path: Optional[Path] = None) -> Path:
    root = Path(path) if path else DEFAULT_DIR
    root.mkdir(parents=True, exist_ok=True)
    return root


def ensure_draft_dir() -> Path:
    DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    return DRAFT_DIR


def _stamp_name(prefix: str = "Recording") -> str:
    return f"{prefix}-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}.mov"


def default_save_path(directory: Optional[Path] = None) -> Path:
    return ensure_dir(directory) / _stamp_name()


def draft_path() -> Path:
    return ensure_draft_dir() / f"draft-{uuid.uuid4().hex}.mov"


def _fmt_bytes(n: int) -> str:
    v = float(max(0, n))
    for unit in ("B", "KB", "MB", "GB"):
        if v < 1024 or unit == "GB":
            if unit == "B":
                return f"{int(v)} {unit}"
            return f"{v:.1f} {unit}"
        v /= 1024.0
    return f"{n} B"


def _fmt_duration(seconds: Optional[float]) -> str:
    if seconds is None:
        return "—"
    s = max(0, int(round(float(seconds))))
    m, sec = divmod(s, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


def file_info(path: Path) -> Dict[str, Any]:
    st = path.stat()
    meta = media_meta(str(path))
    return {
        "name": path.name,
        "path": str(path),
        "bytes": int(st.st_size),
        "size_text": _fmt_bytes(st.st_size),
        "mtime": float(st.st_mtime),
        "mtime_text": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "duration": meta.get("duration"),
        "duration_text": meta.get("duration_text") or "—",
        "width": meta.get("width"),
        "height": meta.get("height"),
    }


def media_meta(path: str) -> Dict[str, Any]:
    """Best-effort duration / size via mdls (no AVFoundation dependency)."""
    out: Dict[str, Any] = {
        "duration": None,
        "duration_text": "—",
        "width": None,
        "height": None,
    }
    p = Path(path)
    if not p.exists():
        return out

    def _mdls(key: str) -> Optional[str]:
        try:
            r = subprocess.run(
                ["mdls", "-raw", "-name", key, str(p)],
                capture_output=True,
                text=True,
                timeout=8,
            )
            text = (r.stdout or "").strip()
            if not text or text == "(null)":
                return None
            return text
        except Exception:
            return None

    dur_raw = _mdls("kMDItemDurationSeconds")
    if dur_raw:
        try:
            dur = float(dur_raw)
            out["duration"] = round(dur, 2)
            out["duration_text"] = _fmt_duration(dur)
        except Exception:
            pass
    w = _mdls("kMDItemPixelWidth")
    h = _mdls("kMDItemPixelHeight")
    try:
        if w:
            out["width"] = int(float(w))
        if h:
            out["height"] = int(float(h))
    except Exception:
        pass
    return out


def make_poster(path: str, max_edge: int = 720) -> Optional[str]:
    """Generate a JPEG poster via qlmanage; return data URL."""
    p = Path(path)
    if not p.exists():
        return None
    out_dir = ensure_draft_dir() / "posters"
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["qlmanage", "-t", "-s", str(int(max_edge)), "-o", str(out_dir), str(p)],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except Exception:
        return None
    # qlmanage names output as "<name>.png" or "<name>.mov.png"
    candidates = list(out_dir.glob(p.name + "*"))
    if not candidates:
        candidates = sorted(out_dir.glob("*.png"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not candidates:
        return None
    poster = candidates[0]
    try:
        raw = poster.read_bytes()
        if len(raw) > 4_000_000:
            return None
        b64 = base64.b64encode(raw).decode("ascii")
        mime = "image/png" if poster.suffix.lower() == ".png" else "image/jpeg"
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None
    finally:
        try:
            poster.unlink()
        except Exception:
            pass


def build_command(
    *,
    out_path: Path,
    mode: str = "selection",
    mic: bool = False,
    system_audio: bool = False,
    show_clicks: bool = True,
    max_seconds: float = 0.0,
    show_toolbar: bool = True,
) -> List[str]:
    mode = mode if mode in ("selection", "full") else "selection"
    flags = ["-x", "-v"]
    if mode == "selection":
        flags.append("-i")
        if show_toolbar:
            flags.append("-U")
    else:
        # Full display (main)
        flags.extend(["-D1"])
    if mic:
        flags.append("-g")
    if system_audio:
        flags.append("-A")
    if show_clicks:
        flags.append("-k")
    if max_seconds and max_seconds > 0:
        flags.append(f"-V{max(1, int(round(float(max_seconds))))}")
    flags.append(str(out_path))
    return screencapture_command(flags)


def start_process(
    *,
    mode: str = "selection",
    mic: bool = False,
    system_audio: bool = False,
    show_clicks: bool = True,
    max_seconds: float = 0.0,
    delay: float = 0.0,
    path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Spawn screencapture -v; returns session dict with pid + path."""
    out_path = Path(path) if path else draft_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if delay and delay > 0:
        time.sleep(float(delay))
    cmd = build_command(
        out_path=out_path,
        mode=mode,
        mic=mic,
        system_audio=system_audio,
        show_clicks=show_clicks,
        max_seconds=max_seconds,
    )
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception as exc:
        need_perm = perm_mod.screen_capture_granted() is False
        return {
            "ok": False,
                "error": (
                    perm_mod.screen_permission_message()
                    if need_perm else str(exc)
            ),
            "path": str(out_path),
            "permission": "screen" if need_perm else "",
        }
    return {
        "ok": True,
        "pid": int(proc.pid),
        "path": str(out_path),
        "mode": mode,
        "started_at": time.time(),
        "_proc": proc,
        "cmd": cmd,
    }


def stop_process(proc: Any, *, timeout: float = 20.0) -> Dict[str, Any]:
    """Stop an active screencapture process (SIGINT → finalize .mov)."""
    if proc is None:
        return {"ok": False, "error": "没有进行中的录制"}
    try:
        if proc.poll() is not None:
            # Already exited
            code = proc.returncode
            err = ""
            try:
                err = (proc.stderr.read() if proc.stderr else "") or ""
            except Exception:
                pass
            return {"ok": code == 0, "code": code, "stderr": str(err).strip()}
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                proc.wait(timeout=5)
            except Exception:
                pass
            return {"ok": False, "error": "停止超时，已强制结束"}
        err = ""
        try:
            err = (proc.stderr.read() if proc.stderr else "") or ""
        except Exception:
            pass
        return {"ok": True, "code": int(proc.returncode or 0), "stderr": str(err).strip()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def wait_process(proc: Any, *, timeout: Optional[float] = None) -> Dict[str, Any]:
    if proc is None:
        return {"ok": False, "error": "没有进行中的录制"}
    try:
        code = proc.wait(timeout=timeout)
        err = ""
        try:
            err = (proc.stderr.read() if proc.stderr else "") or ""
        except Exception:
            pass
        return {"ok": code == 0, "code": int(code), "stderr": str(err).strip()}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout", "timed_out": True}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def finalize_draft(path: str, *, started_at: float = 0.0) -> Dict[str, Any]:
    """Validate draft movie after stop; enrich with meta/poster."""
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass
        return {"ok": False, "error": "已取消录制或未生成文件", "path": ""}
    # Give Spotlight a moment for mdls
    time.sleep(0.15)
    info = file_info(p)
    if not info.get("duration") and started_at:
        info["duration"] = round(max(0.0, time.time() - float(started_at)), 1)
        info["duration_text"] = _fmt_duration(info["duration"])
    poster = make_poster(str(p))
    return {
        "ok": True,
        "path": str(p),
        "draft": True,
        "file": info,
        "poster": poster,
        "message": "录制完成，请预览后保存",
    }


def save_recording(draft_path_str: str, *, open_after: bool = False) -> Dict[str, Any]:
    src = Path(draft_path_str)
    if not src.exists() or src.suffix.lower() not in (".mov", ".mp4", ".m4v"):
        return {"ok": False, "error": "草稿不存在"}
    dest = default_save_path()
    try:
        src.replace(dest)
    except Exception:
        try:
            dest.write_bytes(src.read_bytes())
            src.unlink()
        except Exception as exc:
            return {"ok": False, "error": f"保存失败：{exc}"}
    info = file_info(dest)
    poster = make_poster(str(dest))
    if open_after:
        open_file(str(dest))
    return {
        "ok": True,
        "path": str(dest),
        "file": info,
        "poster": poster,
        "message": "录屏已保存",
    }


def discard_draft(path: str) -> bool:
    return delete_file(path, allow_draft=True)


def _allowed_delete(path: Path, *, allow_draft: bool = True) -> bool:
    try:
        path.resolve().relative_to(DEFAULT_DIR.resolve())
        return True
    except Exception:
        pass
    if allow_draft:
        try:
            path.resolve().relative_to(DRAFT_DIR.resolve())
            return True
        except Exception:
            return False
    return False


def delete_file(path: str, *, allow_draft: bool = False) -> bool:
    p = Path(path)
    if not p.exists() or p.suffix.lower() not in (".mov", ".mp4", ".m4v"):
        return False
    if not _allowed_delete(p, allow_draft=allow_draft or "draft-" in p.name):
        return False
    try:
        p.unlink()
        return True
    except Exception:
        return False


def list_recent(limit: int = 24, directory: Optional[Path] = None) -> List[Dict[str, Any]]:
    root = ensure_dir(directory)
    files = []
    for pat in ("*.mov", "*.mp4", "*.m4v"):
        files.extend([p for p in root.glob(pat) if p.is_file()])
    files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)
    out = []
    for p in files[: max(1, limit)]:
        try:
            out.append(file_info(p))
        except Exception:
            continue
    return out


def folder_payload() -> Dict[str, Any]:
    root = ensure_dir()
    items = list_recent(24)
    return {"folder": str(root), "count": len(items), "items": items}


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


def copy_file_to_clipboard(path: str) -> bool:
    """Put the movie file on the clipboard (Finder-style file copy)."""
    p = Path(path)
    if not p.exists():
        return False
    script = f'''
    set theFile to POSIX file "{p}"
    set the clipboard to (theFile as alias)
    '''
    try:
        r = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return r.returncode == 0
    except Exception:
        return False
