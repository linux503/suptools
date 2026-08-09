"""Ensure runtime dependencies for SupTools.app (first launch)."""

from __future__ import annotations

import importlib
import subprocess
import sys
from typing import List, Tuple


# (import_name, pip_package)
_DEPS: List[Tuple[str, str]] = [
    ("psutil", "psutil"),
    ("AppKit", "pyobjc-framework-Cocoa"),
    ("WebKit", "pyobjc-framework-WebKit"),
]


def ensure_deps() -> None:
    missing = []
    for mod, pkg in _DEPS:
        try:
            importlib.import_module(mod)
        except Exception:
            missing.append(pkg)
    if not missing:
        return

    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--user",
        "--disable-pip-version-check",
        "--only-binary=:all:",
        *missing,
    ]
    try:
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        # Fallback without only-binary for environments that need source wheels
        cmd2 = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--user",
            "--disable-pip-version-check",
            *missing,
        ]
        subprocess.check_call(cmd2)

    # Verify
    for mod, _pkg in _DEPS:
        importlib.import_module(mod)
