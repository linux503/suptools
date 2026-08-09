"""Finder right-click / Services: create a new empty .txt file."""

from __future__ import annotations

import os
import plistlib
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .brand import APP_NAME, SUPPORT_DIRNAME

HELPER_DIR = Path.home() / "Library" / "Application Support" / SUPPORT_DIRNAME / "FinderService"
HELPER_SCRIPT = HELPER_DIR / "new_text_file.sh"
SERVICE_APP = HELPER_DIR / f"{APP_NAME}NewText.app"
# Optional Automator-style alias name shown in some menus after copy
SERVICE_WORKFLOW = Path.home() / "Library" / "Services" / f"{APP_NAME}新建文本文档.workflow"

DEFAULT_BASENAME = "新建文本文档"
LSREGISTER = (
    "/System/Library/Frameworks/CoreServices.framework/"
    "Frameworks/LaunchServices.framework/Support/lsregister"
)


def _run(cmd: List[str], timeout: float = 30.0) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def front_finder_folder() -> Path:
    """Return the folder shown by the front Finder window (Desktop fallback)."""
    script = """
tell application "Finder"
  try
    if (count of Finder windows) is 0 then
      return POSIX path of (path to desktop folder)
    end if
    set t to target of front Finder window
    try
      return POSIX path of (t as alias)
    on error
      try
        return POSIX path of (t as text as alias)
      on error
        return POSIX path of (path to desktop folder)
      end try
    end try
  on error
    return POSIX path of (path to desktop folder)
  end try
end tell
"""
    try:
        proc = _run(["osascript", "-e", script])
        text = (proc.stdout or "").strip()
        if text:
            p = Path(text).expanduser()
            if p.is_dir():
                return p.resolve()
    except Exception:
        pass
    return (Path.home() / "Desktop").resolve()


def resolve_target_folder(paths: Optional[List[str]] = None) -> Path:
    for raw in paths or []:
        try:
            p = Path(str(raw)).expanduser()
            if p.is_dir():
                return p.resolve()
            if p.is_file():
                return p.parent.resolve()
        except Exception:
            continue
    return front_finder_folder()


def unique_txt_path(folder: Path, basename: str = DEFAULT_BASENAME) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    candidate = folder / f"{basename}.txt"
    if not candidate.exists():
        return candidate
    for i in range(2, 10000):
        candidate = folder / f"{basename} {i}.txt"
        if not candidate.exists():
            return candidate
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return folder / f"{basename}-{stamp}.txt"


def create_new_text_file(
    *,
    paths: Optional[List[str]] = None,
    folder: Optional[Path] = None,
    open_file: bool = True,
    reveal: bool = True,
    basename: str = DEFAULT_BASENAME,
) -> Dict[str, Any]:
    try:
        target = Path(folder).expanduser().resolve() if folder else resolve_target_folder(paths)
        if not target.is_dir():
            return {"ok": False, "error": "目标不是文件夹", "path": ""}
        out = unique_txt_path(target, basename=basename)
        out.write_text("", encoding="utf-8")
        try:
            os.utime(out, None)
        except Exception:
            pass
        if reveal:
            try:
                _run(["open", "-R", str(out)])
            except Exception:
                pass
        if open_file:
            try:
                _run(["open", "-t", str(out)])
            except Exception:
                try:
                    _run(["open", str(out)])
                except Exception:
                    pass
        return {
            "ok": True,
            "path": str(out),
            "folder": str(target),
            "message": f"已创建 {out.name}",
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "path": ""}


def _helper_script_text() -> str:
    return r"""#!/bin/bash
set -euo pipefail
PATHS=("$@")
DIR=""
if [[ ${#PATHS[@]} -gt 0 ]]; then
  for p in "${PATHS[@]}"; do
    if [[ -d "$p" ]]; then DIR="$p"; break; fi
    if [[ -f "$p" ]]; then DIR="$(dirname "$p")"; break; fi
  done
fi
if [[ -z "${DIR}" ]]; then
  DIR="$(osascript <<'APPLESCRIPT'
tell application "Finder"
  try
    if (count of Finder windows) is 0 then
      return POSIX path of (path to desktop folder)
    end if
    set t to target of front Finder window
    try
      return POSIX path of (t as alias)
    on error
      return POSIX path of (path to desktop folder)
    end try
  on error
    return POSIX path of (path to desktop folder)
  end try
end tell
APPLESCRIPT
)"
fi
DIR="${DIR%/}"
BASE="新建文本文档"
FILE="${DIR}/${BASE}.txt"
if [[ -e "$FILE" ]]; then
  i=2
  while [[ -e "${DIR}/${BASE} ${i}.txt" ]]; do
    i=$((i + 1))
  done
  FILE="${DIR}/${BASE} ${i}.txt"
fi
umask 022
: > "$FILE"
open -R "$FILE" >/dev/null 2>&1 || true
open -t "$FILE" >/dev/null 2>&1 || open "$FILE" >/dev/null 2>&1 || true
"""


def _service_menu_entries() -> List[dict]:
    return [
        {
            "NSMenuItem": {"default": "新建文本文档"},
            "NSMessage": "createNewTextFile",
            "NSPortName": APP_NAME,
            "NSSendTypes": [
                "public.file-url",
                "NSFilenamesPboardType",
                "public.utf8-plain-text",
            ],
            "NSSendFileTypes": ["public.item", "public.folder", "public.data"],
            "NSRequiredContext": {
                "NSApplicationIdentifier": "com.apple.finder",
            },
        },
        {
            "NSMenuItem": {"default": "在此新建文本文档"},
            "NSMessage": "createNewTextFileHere",
            "NSPortName": APP_NAME,
            "NSRequiredContext": {
                "NSApplicationIdentifier": "com.apple.finder",
            },
        },
    ]


def flush_services() -> None:
    if Path(LSREGISTER).exists():
        try:
            if SERVICE_APP.exists():
                _run([LSREGISTER, "-f", str(SERVICE_APP)])
        except Exception:
            pass
    for cmd in (
        ["/System/Library/CoreServices/pbs", "-flush"],
        ["/usr/bin/killall", "-u", os.environ.get("USER", ""), "pbs"],
    ):
        try:
            subprocess.run([c for c in cmd if c], capture_output=True, timeout=5)
        except Exception:
            pass
    try:
        from AppKit import NSUpdateDynamicServices  # type: ignore

        NSUpdateDynamicServices()
    except Exception:
        pass


def is_service_installed() -> bool:
    return HELPER_SCRIPT.is_file() and SERVICE_APP.is_dir()


def _write_helper_script() -> None:
    HELPER_DIR.mkdir(parents=True, exist_ok=True)
    HELPER_SCRIPT.write_text(_helper_script_text(), encoding="utf-8")
    HELPER_SCRIPT.chmod(0o755)


def _build_service_app() -> bool:
    """Compile a tiny AppleScript applet that runs the shell helper + declares Services."""
    _write_helper_script()
    if SERVICE_APP.exists():
        shutil.rmtree(SERVICE_APP, ignore_errors=True)

    # AppleScript: run helper with dropped/selected files, or Finder folder
    asa = f'''
on run
  do shell script quoted form of "{HELPER_SCRIPT}"
end run

on open fileList
  set argText to ""
  repeat with f in fileList
    set argText to argText & " " & quoted form of POSIX path of f
  end repeat
  do shell script quoted form of "{HELPER_SCRIPT}" & argText
end open
'''
    try:
        proc = _run(["osacompile", "-o", str(SERVICE_APP), "-e", asa])
        if proc.returncode != 0 or not SERVICE_APP.exists():
            return False
    except Exception:
        return False

    info_path = SERVICE_APP / "Contents" / "Info.plist"
    try:
        info = plistlib.loads(info_path.read_bytes())
    except Exception:
        info = {}
    info["CFBundleName"] = "新建文本文档"
    info["CFBundleDisplayName"] = "新建文本文档"
    info["CFBundleIdentifier"] = "com.suptools.service.newtxt"
    info["LSUIElement"] = True
    info["NSServices"] = [
        {
            "NSMenuItem": {"default": "新建文本文档"},
            "NSMessage": "run",
            "NSPortName": "SupToolsNewText",
            "NSSendFileTypes": ["public.item", "public.folder", "public.data"],
            "NSRequiredContext": {"NSApplicationIdentifier": "com.apple.finder"},
        }
    ]
    try:
        info_path.write_bytes(plistlib.dumps(info))
    except Exception:
        return False

    # Convenience copy into Services as a double-clickable alias workflow wrapper:
    # a shell workflow that simply executes the helper (Finder Quick Actions pick this up more often)
    try:
        if SERVICE_WORKFLOW.exists():
            shutil.rmtree(SERVICE_WORKFLOW, ignore_errors=True)
        contents = SERVICE_WORKFLOW / "Contents"
        contents.mkdir(parents=True, exist_ok=True)
        wf_info = {
            "CFBundleIdentifier": "com.suptools.service.newtxt.workflow",
            "CFBundleName": "新建文本文档",
            "NSServices": [
                {
                    "NSMenuItem": {"default": "新建文本文档"},
                    "NSMessage": "runWorkflowAsService",
                    "NSRequiredContext": {"NSApplicationIdentifier": "com.apple.finder"},
                    "NSSendFileTypes": ["public.item", "public.folder", "public.data"],
                },
                {
                    "NSMenuItem": {"default": "在此新建文本文档"},
                    "NSMessage": "runWorkflowAsService",
                    "NSRequiredContext": {"NSApplicationIdentifier": "com.apple.finder"},
                },
            ],
        }
        (contents / "Info.plist").write_bytes(plistlib.dumps(wf_info))
        # Tiny executable document: Automator-compatible shell action as plain script runner
        # macOS also accepts a "quick action" with a relative run script via document.wflow
        doc = {
            "AMDocumentVersion": "2",
            "actions": [
                {
                    "action": {
                        "ActionBundlePath": "/System/Library/Automator/Run Shell Script.action",
                        "ActionName": "Run Shell Script",
                        "BundleIdentifier": "com.apple.RunShellScript",
                        "ActionParameters": {
                            "COMMAND_STRING": f"\"{HELPER_SCRIPT}\" \"$@\"",
                            "INPUT_METHOD": 1,
                            "Shell": "/bin/bash",
                            "source": f"\"{HELPER_SCRIPT}\" \"$@\"",
                            "CheckedForUserDefaultShell": True,
                        },
                        "Class Name": "RunShellScriptAction",
                    }
                }
            ],
            "workflowMetaData": {
                "serviceApplicationBundleID": "com.apple.finder",
                "serviceApplicationPath": "/System/Library/CoreServices/Finder.app",
                "serviceInputTypeIdentifier": "com.apple.Automator.fileSystemObject",
                "serviceOutputTypeIdentifier": "com.apple.Automator.nothing",
                "serviceProcessesInput": 0,
                "workflowTypeIdentifier": "com.apple.Automator.services.quickaction",
                "presentationMode": 15,
            },
            "workflowType": "NCWorkflowTypeService",
        }
        (contents / "document.wflow").write_bytes(plistlib.dumps(doc))
    except Exception:
        # App service alone is still useful
        pass

    flush_services()
    return is_service_installed()


def install_service() -> bool:
    try:
        return _build_service_app()
    except Exception:
        return False


def uninstall_service() -> bool:
    try:
        if SERVICE_APP.exists():
            shutil.rmtree(SERVICE_APP, ignore_errors=True)
        if SERVICE_WORKFLOW.exists():
            shutil.rmtree(SERVICE_WORKFLOW, ignore_errors=True)
        flush_services()
        return not SERVICE_APP.exists()
    except Exception:
        return False


def set_service_enabled(enabled: bool) -> bool:
    return install_service() if enabled else uninstall_service()


def service_status() -> Dict[str, Any]:
    installed = is_service_installed()
    return {
        "installed": installed,
        "workflow_installed": SERVICE_WORKFLOW.is_dir(),
        "path": str(SERVICE_WORKFLOW),
        "app_path": str(SERVICE_APP),
        "helper": str(HELPER_SCRIPT),
        "menu_hint": "Finder 右键 → 快速操作 / 服务 → 新建文本文档",
    }


def paths_from_pasteboard(pboard) -> List[str]:
    """Extract filesystem paths from an NSPasteboard service invocation."""
    paths: List[str] = []
    if pboard is None:
        return paths
    try:
        from AppKit import NSFilenamesPboardType, NSPasteboardTypeFileURL  # type: ignore
    except Exception:
        NSFilenamesPboardType = "NSFilenamesPboardType"
        NSPasteboardTypeFileURL = "public.file-url"

    try:
        names = pboard.propertyListForType_(NSFilenamesPboardType)
        if names:
            paths.extend([str(x) for x in list(names)])
    except Exception:
        pass
    if paths:
        return paths
    try:
        # Newer file URL type
        urls = pboard.readObjectsForClasses_options_(
            [__import__("Foundation", fromlist=["NSURL"]).NSURL],
            None,
        )
        if urls:
            for u in list(urls):
                try:
                    p = u.path()
                    if p:
                        paths.append(str(p))
                except Exception:
                    pass
    except Exception:
        pass
    if paths:
        return paths
    try:
        raw = pboard.stringForType_("public.file-url") or pboard.stringForType_(NSPasteboardTypeFileURL)
        if raw:
            from Foundation import NSURL  # type: ignore

            u = NSURL.URLWithString_(str(raw).strip())
            if u is not None and u.path():
                paths.append(str(u.path()))
    except Exception:
        pass
    return paths
