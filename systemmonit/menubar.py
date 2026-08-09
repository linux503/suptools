"""macOS menu bar — live metrics + quick actions."""

from __future__ import annotations

from typing import Callable, Optional

from .collector import Snapshot, format_bytes
from .icons import (
    MENUBAR_MODES,
    app_icon_path,
    format_net_compact,
    format_net_m,
    menubar_title,
    menubar_tooltip,
    status_icon_path,
)
from . import prefs


class MenuBarController:
    def __init__(
        self,
        on_show: Callable[[], None],
        on_hide: Callable[[], None],
        on_toggle_pause: Callable[[], None],
        on_quit: Callable[[], None],
        is_paused: Callable[[], bool],
        on_open_clean: Optional[Callable[[], None]] = None,
        on_open_uninstall: Optional[Callable[[], None]] = None,
        on_open_startup: Optional[Callable[[], None]] = None,
        on_open_perms: Optional[Callable[[], None]] = None,
        on_open_settings: Optional[Callable[[], None]] = None,
        on_open_processes: Optional[Callable[[], None]] = None,
        on_open_shot: Optional[Callable[[], None]] = None,
        on_open_recording: Optional[Callable[[], None]] = None,
        on_stop_recording: Optional[Callable[[], None]] = None,
        on_mode_changed: Optional[Callable[[str], None]] = None,
        on_theme_toggle: Optional[Callable[[], None]] = None,
        on_new_txt: Optional[Callable[[], None]] = None,
        on_open_connectivity: Optional[Callable[[], None]] = None,
    ) -> None:
        self._on_show = on_show
        self._on_hide = on_hide
        self._on_toggle_pause = on_toggle_pause
        self._on_quit = on_quit
        self._is_paused = is_paused
        self._on_open_clean = on_open_clean
        self._on_open_uninstall = on_open_uninstall
        self._on_open_startup = on_open_startup
        self._on_open_perms = on_open_perms
        self._on_open_settings = on_open_settings
        self._on_open_processes = on_open_processes
        self._on_open_shot = on_open_shot
        self._on_open_recording = on_open_recording
        self._on_stop_recording = on_stop_recording
        self._on_mode_changed = on_mode_changed
        self._on_theme_toggle = on_theme_toggle
        self._on_new_txt = on_new_txt
        self._on_open_connectivity = on_open_connectivity
        self._available = False
        self._status_item = None
        self._items = {}
        self._mode_items = {}
        self._mode = str(prefs.get("menubar_mode", "net"))
        self._last_snap: Optional[Snapshot] = None
        self._last_title: Optional[str] = None
        self._title_font = None
        self._cpu_history = []
        self._setup()
        self._apply_dock_icon()

    @property
    def available(self) -> bool:
        return self._available

    @property
    def mode(self) -> str:
        return self._mode

    def set_mode(self, mode: str, persist: bool = True) -> None:
        if mode not in {m for m, _ in MENUBAR_MODES}:
            return
        self._mode = mode
        if persist:
            prefs.set_pref("menubar_mode", mode)
        self._sync_mode_checks()
        if self._last_snap is not None:
            self.update(self._last_snap)
        if self._on_mode_changed and persist:
            try:
                self._on_mode_changed(mode)
            except Exception:
                pass

    def apply_icon_pref(self) -> None:
        """Show/hide template glyph per settings."""
        try:
            button = self._status_item.button() if self._status_item else None
            if button is None:
                return
            if prefs.get("menubar_show_icon", True):
                icon = status_icon_path()
                if icon:
                    from AppKit import NSImage  # type: ignore

                    image = NSImage.alloc().initWithContentsOfFile_(icon)
                    if image is not None:
                        image.setSize_((16, 16))
                        image.setTemplate_(True)
                        button.setImage_(image)
                        button.setImagePosition_(2)
                        return
            button.setImage_(None)
        except Exception:
            pass

    def _apply_dock_icon(self) -> None:
        path = app_icon_path()
        if not path:
            return
        try:
            from AppKit import NSApp, NSApplication, NSImage  # type: ignore

            NSApplication.sharedApplication()
            image = NSImage.alloc().initWithContentsOfFile_(path)
            if image is not None:
                NSApp.setApplicationIconImage_(image)
        except Exception:
            pass

    def _sync_mode_checks(self) -> None:
        for key, item in self._mode_items.items():
            try:
                item.setState_(1 if key == self._mode else 0)
            except Exception:
                pass

    def _setup(self) -> None:
        try:
            from AppKit import (  # type: ignore
                NSImage,
                NSMenu,
                NSMenuItem,
                NSPasteboard,
                NSStatusBar,
                NSStringPboardType,
                NSVariableStatusItemLength,
            )
            from Foundation import NSObject  # type: ignore
            import objc  # type: ignore
        except Exception:
            return

        controller = self
        OnShow, OnHide = self._on_show, self._on_hide
        OnPause, OnQuit = self._on_toggle_pause, self._on_quit
        OnClean = self._on_open_clean
        OnUninstall = self._on_open_uninstall
        OnStartup = self._on_open_startup
        OnPerms = self._on_open_perms
        OnSettings = self._on_open_settings
        OnProcs = self._on_open_processes
        OnShot = self._on_open_shot
        OnRec = self._on_open_recording
        OnStopRec = self._on_stop_recording
        OnTheme = self._on_theme_toggle
        OnNewTxt = self._on_new_txt
        OnConn = self._on_open_connectivity

        class _Target(NSObject):
            def showWindow_(self, _sender):  # noqa: N802
                OnShow()

            def hideWindow_(self, _sender):  # noqa: N802
                OnHide()

            def togglePause_(self, _sender):  # noqa: N802
                OnPause()

            def quitApp_(self, _sender):  # noqa: N802
                OnQuit()

            def openClean_(self, _sender):  # noqa: N802
                if OnClean:
                    OnClean()
                else:
                    OnShow()

            def openUninstall_(self, _sender):  # noqa: N802
                if OnUninstall:
                    OnUninstall()
                else:
                    OnShow()

            def openStartup_(self, _sender):  # noqa: N802
                if OnStartup:
                    OnStartup()
                else:
                    OnShow()

            def openPerms_(self, _sender):  # noqa: N802
                if OnPerms:
                    OnPerms()
                else:
                    OnShow()

            def openSettings_(self, _sender):  # noqa: N802
                if OnSettings:
                    OnSettings()
                else:
                    OnShow()

            def openProcesses_(self, _sender):  # noqa: N802
                if OnProcs:
                    OnProcs()
                else:
                    OnShow()

            def openShot_(self, _sender):  # noqa: N802
                if OnShot:
                    OnShot()
                else:
                    OnShow()

            def openRecording_(self, _sender):  # noqa: N802
                if OnRec:
                    OnRec()
                else:
                    OnShow()

            def stopRecording_(self, _sender):  # noqa: N802
                if OnStopRec:
                    OnStopRec()

            def openConnectivity_(self, _sender):  # noqa: N802
                if OnConn:
                    OnConn()
                else:
                    OnShow()

            def newTextFile_(self, _sender):  # noqa: N802
                if OnNewTxt:
                    OnNewTxt()

            def toggleTheme_(self, _sender):  # noqa: N802
                if OnTheme:
                    OnTheme()

            def copyNet_(self, _sender):  # noqa: N802
                snap = controller._last_snap
                if snap is None:
                    return
                text = (
                    f"↓{format_net_compact(snap.net_down_bps)}/s  "
                    f"↑{format_net_compact(snap.net_up_bps)}/s"
                )
                controller._copy_text(text)

            def copyAll_(self, _sender):  # noqa: N802
                snap = controller._last_snap
                if snap is None:
                    return
                text = (
                    f"SupTools\n"
                    f"CPU {snap.cpu_percent:.1f}%\n"
                    f"内存 {snap.mem_percent:.1f}% ({format_bytes(snap.mem_used)})\n"
                    f"↓{format_net_compact(snap.net_down_bps)}/s "
                    f"↑{format_net_compact(snap.net_up_bps)}/s\n"
                    f"磁盘 {snap.primary_disk_percent:.0f}%\n"
                    f"负载 {snap.load_avg[0]:.2f} {snap.load_avg[1]:.2f} {snap.load_avg[2]:.2f}"
                )
                controller._copy_text(text)

            def cycleMode_(self, _sender):  # noqa: N802
                keys = [m for m, _ in MENUBAR_MODES]
                try:
                    idx = keys.index(controller._mode)
                except ValueError:
                    idx = 0
                controller.set_mode(keys[(idx + 1) % len(keys)])

            def setModeNet_(self, _sender):  # noqa: N802
                controller.set_mode("net")

            def setModeNetM_(self, _sender):  # noqa: N802
                controller.set_mode("net_m")

            def setModeCpuNet_(self, _sender):  # noqa: N802
                controller.set_mode("cpu_net")

            def setModeCpu_(self, _sender):  # noqa: N802
                controller.set_mode("cpu")

            def setModeMemory_(self, _sender):  # noqa: N802
                controller.set_mode("memory")

            def setModeCompact_(self, _sender):  # noqa: N802
                controller.set_mode("compact")

            def setModeDisk_(self, _sender):  # noqa: N802
                controller.set_mode("disk")

            def setModeBattery_(self, _sender):  # noqa: N802
                controller.set_mode("battery")

            def setModeSpark_(self, _sender):  # noqa: N802
                controller.set_mode("spark")

        self._target = _Target.alloc().init()
        self._status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
        button = self._status_item.button()
        if button is not None:
            button.setTitle_("↓0↑0")
            button.setToolTip_("SupTools — 点击查看详情")
            try:
                from AppKit import NSFont  # type: ignore

                self._title_font = NSFont.monospacedDigitSystemFontOfSize_weight_(11.0, 0.23)
            except Exception:
                self._title_font = None
            self.apply_icon_pref()

        menu = NSMenu.alloc().init()
        menu.setAutoenablesItems_(False)

        def add_disabled(title: str, key: str):
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, None, "")
            item.setEnabled_(False)
            menu.addItem_(item)
            self._items[key] = item

        def add_action(title: str, action: str, key: str = ""):
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                title, objc.selector(getattr(self._target, action), signature=b"v@:@"), ""
            )
            item.setTarget_(self._target)
            menu.addItem_(item)
            if key:
                self._items[key] = item
            return item

        add_disabled("SupTools", "header")
        add_disabled("状态良好", "alert")
        menu.addItem_(NSMenuItem.separatorItem())
        add_disabled("▣  CPU      —", "cpu")
        add_disabled("▦  内存     —", "mem")
        add_disabled("◌  压力     —", "pressure")
        add_disabled("↘  负载     —", "load")
        add_disabled("↓  下行     0B/s", "net_down")
        add_disabled("↑  上行     0B/s", "net_up")
        add_disabled("⇄  接口     —", "iface")
        add_disabled("▤  磁盘     —", "disk")
        add_disabled("⚡  电池     —", "battery")
        add_disabled("▲  TOP      —", "top")
        menu.addItem_(NSMenuItem.separatorItem())

        # Display mode submenu
        mode_menu = NSMenu.alloc().init()
        mode_map = {
            "net": "setModeNet_",
            "net_m": "setModeNetM_",
            "cpu_net": "setModeCpuNet_",
            "cpu": "setModeCpu_",
            "memory": "setModeMemory_",
            "compact": "setModeCompact_",
            "disk": "setModeDisk_",
            "battery": "setModeBattery_",
            "spark": "setModeSpark_",
        }
        mode_root = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("显示模式", None, "")
        for mode_key, label in MENUBAR_MODES:
            short = label.replace("显示：", "")
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                short, objc.selector(getattr(self._target, mode_map[mode_key]), signature=b"v@:@"), ""
            )
            item.setTarget_(self._target)
            mode_menu.addItem_(item)
            self._mode_items[mode_key] = item
        mode_root.setSubmenu_(mode_menu)
        menu.addItem_(mode_root)
        add_action("⟳  切换下一显示模式", "cycleMode_", "cycle")
        menu.addItem_(NSMenuItem.separatorItem())

        add_action("◈  显示监控面板", "showWindow_", "show")
        add_action("◌  隐藏监控面板", "hideWindow_", "hide")
        menu.addItem_(NSMenuItem.separatorItem())

        add_action("☰  打开进程管理", "openProcesses_", "procs")
        menu.addItem_(NSMenuItem.separatorItem())

        add_action("♻  打开垃圾清理", "openClean_", "clean")
        add_action("⌫  打开软件卸载", "openUninstall_", "uninstall")
        add_action("⏻  打开启动项管理", "openStartup_", "startup")
        add_action("🔐  打开权限引导", "openPerms_", "perms")
        add_action("✂  打开截图工具", "openShot_", "shot")
        add_action("⏺  打开录屏工具", "openRecording_", "rec")
        stop_item = add_action("⏹  停止录屏", "stopRecording_", "rec_stop")
        try:
            stop_item.setEnabled_(False)
        except Exception:
            pass
        add_action("◎  网络连通性测试", "openConnectivity_", "conn")
        add_action("📄  新建文本文档", "newTextFile_", "newtxt")
        menu.addItem_(NSMenuItem.separatorItem())

        add_action("⚙  打开设置中心", "openSettings_", "settings")
        menu.addItem_(NSMenuItem.separatorItem())

        add_action("⎘  复制当前网速", "copyNet_", "copy")
        add_action("⎘  复制全部指标", "copyAll_", "copy_all")
        add_action("◐  切换外观主题", "toggleTheme_", "theme")
        add_action("❚  暂停刷新", "togglePause_", "pause")
        menu.addItem_(NSMenuItem.separatorItem())
        add_action("✕  退出 SupTools", "quitApp_", "quit")

        self._status_item.setMenu_(menu)
        self._sync_mode_checks()
        self._available = True

    def _copy_text(self, text: str) -> None:
        try:
            from AppKit import NSPasteboard, NSPasteboardTypeString, NSStringPboardType  # type: ignore

            pb = NSPasteboard.generalPasteboard()
            pb.clearContents()
            try:
                pb.setString_forType_(text, NSPasteboardTypeString)
            except Exception:
                pb.setString_forType_(text, NSStringPboardType)
        except Exception:
            pass

    def _apply_title(self, button, text: str) -> None:
        """Set menubar title with monospaced digits; skip no-op updates."""
        if text == self._last_title:
            return
        self._last_title = text
        # No leading space — keeps the status item tighter
        title = text
        if self._title_font is not None:
            try:
                from AppKit import NSAttributedString, NSFontAttributeName  # type: ignore

                attrs = {NSFontAttributeName: self._title_font}
                attr = NSAttributedString.alloc().initWithString_attributes_(title, attrs)
                button.setAttributedTitle_(attr)
                return
            except Exception:
                pass
        button.setTitle_(title)

    def update(self, snap: Optional[Snapshot], history=None) -> None:
        if not self._available or snap is None:
            return
        self._last_snap = snap
        if history is not None:
            self._cpu_history = list(history)
        try:
            paused = bool(self._is_paused())
            button = self._status_item.button()
            if button is not None:
                self._apply_title(
                    button,
                    menubar_title(
                        snap,
                        paused=paused,
                        mode=self._mode,
                        history=self._cpu_history,
                    ),
                )
                button.setToolTip_(menubar_tooltip(snap))

            disk_text = f"▤  磁盘     {snap.primary_disk_percent:.0f}%"
            if snap.primary_disk_total:
                free = getattr(snap, "primary_disk_free", 0) or max(
                    0, snap.primary_disk_total - snap.primary_disk_used
                )
                disk_text = (
                    f"▤  磁盘     {snap.primary_disk_percent:.0f}%  "
                    f"可用 {format_bytes(free)}"
                )

            iface = "—"
            for i in snap.net_interfaces or []:
                if i.get("isup") and (i.get("ip") or i.get("down_bps", 0) > 0):
                    iface = i.get("display") or i.get("name") or "—"
                    break

            pressure_map = {"normal": "正常", "warn": "警告", "critical": "严重"}
            pressure = pressure_map.get(getattr(snap, "mem_pressure", "normal"), "正常")

            alerts = []
            alert_cpu = int(prefs.get("alert_cpu", 85))
            alert_mem = int(prefs.get("alert_mem", 85))
            alert_disk = int(prefs.get("alert_disk", 90))
            if snap.cpu_percent >= alert_cpu:
                alerts.append(f"CPU {snap.cpu_percent:.0f}%")
            if snap.mem_percent >= alert_mem or getattr(snap, "mem_pressure", "") == "critical":
                alerts.append(f"内存 {snap.mem_percent:.0f}%")
            if snap.primary_disk_percent >= alert_disk:
                alerts.append(f"磁盘 {snap.primary_disk_percent:.0f}%")
            if prefs.get("show_alerts", True) and alerts:
                alert_text = "⚠  注意  " + " · ".join(alerts)
            else:
                alert_text = "✓  状态良好"

            if getattr(snap, "has_battery", False):
                plug = "充电" if snap.battery_plugged else "电池"
                batt_text = f"⚡  电池     {snap.battery_percent:.0f}%  ·  {plug}"
            else:
                batt_text = "⚡  电池     台式机 / 外接供电"

            if getattr(snap, "top_process_name", ""):
                top_text = f"▲  TOP      {snap.top_process_name}  {snap.top_process_cpu:.0f}%"
            else:
                top_text = "▲  TOP      —"

            mapping = {
                "header": "SupTools" + ("  ·  已暂停" if paused else ""),
                "alert": alert_text,
                "cpu": f"▣  CPU      {snap.cpu_percent:.1f}%",
                "mem": f"▦  内存     {snap.mem_percent:.1f}%  ({format_bytes(snap.mem_used)})",
                "pressure": f"◌  压力     {pressure}",
                "load": f"↘  负载     {snap.load_avg[0]:.2f}  {snap.load_avg[1]:.2f}  {snap.load_avg[2]:.2f}",
                "net_down": f"↓  下行     {format_net_compact(snap.net_down_bps)}/s  ({format_net_m(snap.net_down_bps)})",
                "net_up": f"↑  上行     {format_net_compact(snap.net_up_bps)}/s  ({format_net_m(snap.net_up_bps)})",
                "iface": f"⇄  接口     {iface}",
                "disk": disk_text,
                "battery": batt_text,
                "top": top_text,
                "pause": "▶  继续刷新" if paused else "❚  暂停刷新",
            }
            for key, text in mapping.items():
                item = self._items.get(key)
                if item is not None:
                    item.setTitle_(text)
            self._sync_mode_checks()
        except Exception:
            pass
