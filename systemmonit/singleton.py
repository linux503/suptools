"""Ensure only one SupTools instance owns the menu bar."""

from __future__ import annotations

import fcntl
import os
import sys
from pathlib import Path
from typing import Optional

from .brand import ACTIVATE_NOTIFICATION, BUNDLE_ID, migrate_support_dir

SHOW_NOTIFICATION = ACTIVATE_NOTIFICATION
LOCK_PATH = migrate_support_dir() / "instance.lock"

_lock_fh: Optional[object] = None
_acquired = False


def _notify_existing() -> None:
    """Ask the running instance to show its window, then activate the app."""
    try:
        from Foundation import NSDistributedNotificationCenter  # type: ignore

        NSDistributedNotificationCenter.defaultCenter().postNotificationName_object_userInfo_deliverImmediately_(
            SHOW_NOTIFICATION,
            None,
            None,
            True,
        )
    except Exception:
        pass
    try:
        from AppKit import NSApplicationActivateIgnoringOtherApps, NSRunningApplication  # type: ignore

        apps = NSRunningApplication.runningApplicationsWithBundleIdentifier_(BUNDLE_ID)
        if not apps:
            for legacy_id in ("com.syspulse.app", "com.systemmonit.app"):
                apps = NSRunningApplication.runningApplicationsWithBundleIdentifier_(legacy_id)
                if apps:
                    break
        for app in apps:
            try:
                app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
            except Exception:
                pass
    except Exception:
        pass


def acquire_singleton() -> bool:
    """Return True if this process is the primary instance.

    Safe to call more than once in the same process (idempotent).
    Secondary launches notify the primary and should exit immediately.
    """
    global _lock_fh, _acquired
    if _acquired and _lock_fh is not None:
        return True

    fh = None
    try:
        LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        fh = open(LOCK_PATH, "a+", encoding="utf-8")
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        fh.seek(0)
        fh.truncate()
        fh.write(f"{os.getpid()}\n")
        fh.flush()
        _lock_fh = fh
        _acquired = True
        return True
    except BlockingIOError:
        if fh is not None:
            try:
                fh.close()
            except Exception:
                pass
        _notify_existing()
        return False
    except Exception:
        if fh is not None:
            try:
                fh.close()
            except Exception:
                pass
        # If locking fails unexpectedly, allow start rather than brick the app.
        return True


def release_singleton() -> None:
    global _lock_fh, _acquired
    fh = _lock_fh
    _lock_fh = None
    _acquired = False
    if fh is None:
        return
    try:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    except Exception:
        pass
    try:
        fh.close()
    except Exception:
        pass


def exit_if_already_running() -> None:
    if not acquire_singleton():
        try:
            import time

            time.sleep(0.15)
        except Exception:
            pass
        sys.exit(0)
