"""Entry for SupTools.app — native WebKit dashboard + menu bar (no Tk)."""
from systemmonit.bootstrap import ensure_deps
from systemmonit.native_app import run
from systemmonit.singleton import exit_if_already_running

if __name__ == "__main__":
    # Must run before creating a second menu-bar item.
    exit_if_already_running()
    ensure_deps()
    run()
