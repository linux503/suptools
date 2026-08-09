"""Resolve and invoke the native SupTools binary (com.suptools.app TCC identity)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import List, Optional


def app_bundle_path() -> Optional[Path]:
    env = (
        os.environ.get("SUPTOOLS_APP_BUNDLE")
        or os.environ.get("SYSPULSE_APP_BUNDLE")
        or os.environ.get("SYSTEMMONIT_APP_BUNDLE")
        or ""
    )
    if env:
        p = Path(env)
        if p.is_dir():
            return p
    # Dev / fallback: Applications install
    for cand in (
        Path("/Applications/SupTools.app"),
        Path(__file__).resolve().parents[1] / "dist" / "arm64" / "SupTools.app",
        Path(__file__).resolve().parents[1] / "dist" / "SupTools.app",
    ):
        if cand.is_dir():
            return cand
    return None


def native_helper_path() -> Optional[Path]:
    bundle = app_bundle_path()
    if not bundle:
        return None
    helper = bundle / "Contents" / "MacOS" / "SupTools"
    return helper if helper.is_file() and os.access(helper, os.X_OK) else None


def run_helper(helper_args: List[str], *, timeout: Optional[float] = 30.0) -> subprocess.CompletedProcess:
    helper = native_helper_path()
    if helper is None:
        raise FileNotFoundError("SupTools native helper not found")
    return subprocess.run(
        [str(helper), *helper_args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def screencapture_command(capture_args: List[str]) -> List[str]:
    """Prefer native helper so Screen Recording attaches to SupTools.app."""
    helper = native_helper_path()
    if helper is not None:
        return [str(helper), "--screencapture", *capture_args]
    return ["/usr/sbin/screencapture", *capture_args]
