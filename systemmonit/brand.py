"""Product brand — user-facing name and identifiers."""

from pathlib import Path

# Display
APP_NAME = "SupTools"
APP_TAGLINE = "超级工具箱"
APP_NAME_CN = "超级工具箱"

# Bundle / paths
BUNDLE_ID = "com.suptools.app"
ACTIVATE_NOTIFICATION = "com.suptools.activate"
APP_FILENAME = "SupTools.app"
EXECUTABLE = "SupTools"

# Support locations
SUPPORT_DIRNAME = "SupTools"
LEGACY_SUPPORT_DIRNAMES = ("SysPulse", "SystemMonit")
LEGACY_SUPPORT_DIRNAME = "SysPulse"  # primary migration source
SCREENSHOT_DIRNAME = "SupTools"

# Env / bridge
BUNDLE_ENV = "SUPTOOLS_APP_BUNDLE"
LEGACY_BUNDLE_ENVS = ("SYSPULSE_APP_BUNDLE", "SYSTEMMONIT_APP_BUNDLE")
LEGACY_BUNDLE_ENV = "SYSPULSE_APP_BUNDLE"
BRIDGE_NAME = "suptools"

DEFAULT_APP_PATH = f"/Applications/{APP_FILENAME}"


def support_dir() -> Path:
    return Path.home() / "Library" / "Application Support" / SUPPORT_DIRNAME


def legacy_support_dir() -> Path:
    return Path.home() / "Library" / "Application Support" / LEGACY_SUPPORT_DIRNAME


def migrate_support_dir() -> Path:
    """Prefer new support dir; copy prefs from legacy once if needed."""
    new = support_dir()
    new.mkdir(parents=True, exist_ok=True)
    for legacy_name in LEGACY_SUPPORT_DIRNAMES:
        old = Path.home() / "Library" / "Application Support" / legacy_name
        if not old.is_dir():
            continue
        try:
            if old.resolve() == new.resolve():
                continue
        except OSError:
            continue
        for name in ("settings.json", "prefs.json", "config.json"):
            src = old / name
            dst = new / name
            if src.is_file() and not dst.exists():
                try:
                    dst.write_bytes(src.read_bytes())
                except OSError:
                    pass
    return new
