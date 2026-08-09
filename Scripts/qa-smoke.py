#!/usr/bin/env python3
"""Non-destructive smoke tests for SupTools feature backends."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import traceback
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

results: list[tuple[str, str, str]] = []


def ok(name: str, detail: str = "") -> None:
    results.append(("PASS", name, detail))
    print(f"PASS  {name}" + (f" — {detail}" if detail else ""), flush=True)


def fail(name: str, detail: str = "") -> None:
    results.append(("FAIL", name, detail))
    print(f"FAIL  {name} — {detail}", flush=True)


def warn(name: str, detail: str = "") -> None:
    results.append(("WARN", name, detail))
    print(f"WARN  {name} — {detail}", flush=True)


def main() -> int:
    # Imports
    for m in (
        "collector",
        "cleaner",
        "uninstaller",
        "startup",
        "screenshot",
        "recording",
        "permissions",
        "prefs",
        "connectivity",
        "native_helper",
        "notify",
        "finder_newtxt",
        "singleton",
        "brand",
        "hotkeys",
    ):
        try:
            __import__(f"systemmonit.{m}")
            ok(f"import.{m}")
        except Exception as e:
            fail(f"import.{m}", f"{type(e).__name__}: {e}")

    # Collector + payload (function lives in native_app)
    try:
        from systemmonit.collector import MetricsCollector
        from systemmonit.native_app import snapshot_to_payload

        c = MetricsCollector()
        snap = c.sample(include_processes=True, include_interfaces=True)
        payload = snapshot_to_payload(c, snap)
        need = ("cpu", "memory", "disk", "network", "processes")
        missing = [k for k in need if k not in payload]
        if missing:
            fail("collector.payload", f"missing {missing}; keys={sorted(payload)[:40]}")
        else:
            cpu = payload.get("cpu")
            cpu_pct = cpu.get("percent") if isinstance(cpu, dict) else cpu
            ok(
                "collector.sample",
                f"cpu={cpu_pct} procs={len(payload.get('processes') or [])}",
            )
    except Exception:
        fail("collector", traceback.format_exc()[-700:])

    # Prefs
    try:
        from systemmonit import prefs

        sp = prefs.settings_payload()
        ok("prefs.settings", f"ver={sp.get('version')} menubar={sp.get('menubar_mode')}")
    except Exception as e:
        fail("prefs", str(e))

    # Cleaner targets + trash-only scan
    try:
        from systemmonit import cleaner

        targets = cleaner.targets()
        keys = [t.key for t in targets]
        ok("cleaner.targets", f"n={len(targets)} has_trash={'trash' in keys}")
        t0 = time.time()
        scanned = cleaner.scan_detailed(["trash"])
        items = scanned.get("items") if isinstance(scanned, dict) else None
        ok(
            "cleaner.scan_trash",
            f"elapsed={time.time()-t0:.1f}s items={len(items) if items is not None else '?'} "
            f"keys={sorted(scanned)[:10] if isinstance(scanned, dict) else type(scanned)}",
        )
    except Exception:
        fail("cleaner", traceback.format_exc()[-700:])

    # Uninstaller list without icons (faster)
    try:
        from systemmonit import uninstaller

        t0 = time.time()
        listed = uninstaller.list_apps(include_icons=False)
        apps = listed.get("apps") or []
        ok(
            "uninstaller.list",
            f"elapsed={time.time()-t0:.1f}s n={listed.get('app_count')} removable={listed.get('removable_count')} "
            f"first={(apps[0].get('name') if apps else None)}",
        )
    except Exception:
        fail("uninstaller", traceback.format_exc()[-700:])

    # Startup
    try:
        from systemmonit import startup

        listed = startup.list_startup()
        items = listed.get("items") if isinstance(listed, dict) else listed
        ok("startup.list", f"n={len(items) if items is not None else listed}")
    except Exception:
        fail("startup", traceback.format_exc()[-700:])

    # Permissions
    try:
        from systemmonit import permissions

        st = permissions.permissions_status()
        items = st.get("items") if isinstance(st, dict) else None
        summary = {}
        if isinstance(items, list):
            for it in items:
                summary[it.get("id") or it.get("key") or it.get("kind")] = it.get("granted")
        elif isinstance(st, dict):
            for k, v in st.items():
                if isinstance(v, dict) and "granted" in v:
                    summary[k] = v.get("granted")
        ok("permissions.status", json.dumps(summary, ensure_ascii=False)[:500])
        guide = permissions.permission_guide_payload("screen")
        ok("permissions.guide", f"keys={sorted(guide)[:8]}")
    except Exception:
        fail("permissions", traceback.format_exc()[-700:])

    # Screenshot folder + helper + non-interactive capture
    try:
        from systemmonit import screenshot
        from systemmonit import native_helper as nh

        fp = screenshot.folder_payload()
        ok("screenshot.folder", str(fp)[:200])
        cmd = nh.screencapture_command(["-x", "/tmp/__qa.png"])
        ok("helper.cmd", " ".join(map(str, cmd))[:220])
        if hasattr(nh, "runtime_tcc_identity"):
            ok("helper.tcc", str(nh.runtime_tcc_identity())[:200])

        out = Path(tempfile.gettempdir()) / f"suptools-qa-{int(time.time())}.png"
        # Full screen silent capture via helper identity
        cmd = nh.screencapture_command(["-x", str(out)])
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode == 0 and out.is_file() and out.stat().st_size > 1000:
            ok("screenshot.fullscreen", f"bytes={out.stat().st_size} path={out}")
            try:
                out.unlink()
            except OSError:
                pass
        else:
            fail(
                "screenshot.fullscreen",
                f"rc={proc.returncode} exists={out.exists()} "
                f"stderr={proc.stderr[-300:]!r} stdout={proc.stdout[-200:]!r}",
            )
        recent = screenshot.list_recent(limit=5)
        ok("screenshot.recent", f"n={len(recent)}")
    except Exception:
        fail("screenshot", traceback.format_exc()[-700:])

    # Recording list / folder
    try:
        from systemmonit import recording

        ok("recording.recent", f"n={len(recording.list_recent(limit=5))}")
        ok("recording.folder", str(recording.folder_payload())[:200])
    except Exception:
        fail("recording", traceback.format_exc()[-700:])

    # Connectivity
    try:
        from systemmonit import connectivity
        import threading

        box: dict = {}

        def run() -> None:
            try:
                box["r"] = connectivity.run_connectivity_test()
            except Exception as e:  # noqa: BLE001
                box["e"] = e

        th = threading.Thread(target=run, daemon=True)
        th.start()
        th.join(15)
        if th.is_alive():
            warn("connectivity", "still running after 15s")
        elif "e" in box:
            fail("connectivity", str(box["e"]))
        else:
            r = box["r"]
            ok(
                "connectivity",
                f"type={type(r).__name__} keys={list(r)[:8] if isinstance(r, dict) else '?'}",
            )
    except Exception as e:
        fail("connectivity", str(e))

    # Dashboard + bridge coverage
    try:
        html = (ROOT / "systemmonit" / "dashboard_html.py").read_text()
        for needle in (
            "page-overview",
            "page-clean",
            "page-uninstall",
            "page-startup",
            "page-shot",
            "page-rec",
            "page-perms",
            "page-settings",
            "page-processes",
            "page-conn",
            "function showPage",
            "__navigate",
        ):
            (ok if needle in html else fail)(f"html.{needle}", "" if needle in html else "missing")

        src = (ROOT / "systemmonit" / "native_app.py").read_text()
        for typ in (
            "clean_scan",
            "clean_run",
            "clean_cancel",
            "uninstall_list",
            "uninstall_scan",
            "uninstall_run",
            "startup_list",
            "startup_set",
            "screenshot_capture",
            "recording_start",
            "recording_stop",
            "permissions_status",
            "permission_request",
            "connectivity_run",
            "proc_action",
            "settings_get",
            "settings_set",
            "hotkey_record",
        ):
            token = f'typ == "{typ}"'
            alt = f"typ == '{typ}'"
            found = token in src or alt in src
            (ok if found else warn)(f"bridge.{typ}", "ok" if found else "handler missing")
    except Exception as e:
        fail("html/bridge", str(e))

    # Packaged app sanity
    app = Path("/Applications/SupTools.app")
    if app.is_dir():
        helper = app / "Contents" / "MacOS" / "SupTools"
        ok("app.installed", str(helper))
        try:
            rc = subprocess.run([str(helper), "--preflight-screen"], timeout=10)
            (ok if rc.returncode == 0 else warn)(
                "app.preflight_screen", f"rc={rc.returncode}"
            )
        except Exception as e:
            fail("app.preflight_screen", str(e))
        src_icon = ROOT / "assets" / "SupToolsIcon.png"
        app_icon = app / "Contents" / "Resources" / "SupToolsIcon.png"
        if src_icon.is_file() and app_icon.is_file():
            if src_icon.read_bytes() != app_icon.read_bytes():
                warn("app.icon", "installed icon differs from source (needs reinstall)")
            else:
                ok("app.icon", "matches source")
    else:
        warn("app.installed", "not found")

    print("\n==== SUMMARY ====", flush=True)
    print(dict(Counter(s for s, _, _ in results)), flush=True)
    for status in ("FAIL", "WARN"):
        xs = [r for r in results if r[0] == status]
        if not xs:
            continue
        print(f"{status}S:", flush=True)
        for _, name, detail in xs:
            print(f" - {name}: {detail[:300]}", flush=True)

    return 1 if any(s == "FAIL" for s, _, _ in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
