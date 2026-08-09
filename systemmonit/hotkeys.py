"""Global / local keyboard shortcuts for SupTools (screenshot etc.)."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Set, Tuple

# Stored format: "ctrl+alt+cmd+shift+4" (order fixed). Empty = disabled.
DEFAULT_HOTKEYS = {
    "hotkey_shot_selection": "ctrl+cmd+4",
    "hotkey_shot_window": "ctrl+cmd+5",
    "hotkey_shot_full": "ctrl+cmd+3",
    "hotkey_rec_selection": "ctrl+cmd+6",
    "hotkey_rec_full": "ctrl+cmd+7",
    "hotkey_rec_stop": "ctrl+cmd+8",
}

_MOD_ORDER = ("ctrl", "alt", "shift", "cmd")
_MOD_LABEL = {"ctrl": "⌃", "alt": "⌥", "shift": "⇧", "cmd": "⌘"}

# Characters that need shift on a US-ish layout — we store the unshifted char
# and rely on charactersIgnoringModifiers from NSEvent.


def normalize_hotkey(spec: Any) -> str:
    """Normalize a hotkey string; return '' if invalid / empty."""
    if spec is None:
        return ""
    text = str(spec).strip().lower()
    if not text or text in ("none", "off", "disabled", "-"):
        return ""
    parts = [p for p in text.replace(" ", "").split("+") if p]
    if not parts:
        return ""
    mods: Set[str] = set()
    key = ""
    alias = {
        "control": "ctrl",
        "ctl": "ctrl",
        "option": "alt",
        "opt": "alt",
        "command": "cmd",
        "cmd": "cmd",
        "meta": "cmd",
        "⌘": "cmd",
        "⌃": "ctrl",
        "⌥": "alt",
        "⇧": "shift",
    }
    for p in parts:
        token = alias.get(p, p)
        if token in _MOD_ORDER:
            mods.add(token)
        else:
            key = token
    if not key:
        return ""
    # Require at least one modifier for safety (avoid eating plain letters globally)
    if not mods:
        return ""
    ordered = [m for m in _MOD_ORDER if m in mods]
    return "+".join(ordered + [key])


def format_hotkey(spec: Any) -> str:
    """Human-readable macOS-style shortcut, or '未设置'."""
    norm = normalize_hotkey(spec)
    if not norm:
        return "未设置"
    parts = norm.split("+")
    key = parts[-1]
    mods = parts[:-1]
    label_key = key.upper() if len(key) == 1 else key
    special = {
        "space": "空格",
        "return": "↩",
        "enter": "↩",
        "escape": "⎋",
        "esc": "⎋",
        "tab": "⇥",
        "delete": "⌫",
        "backspace": "⌫",
        "up": "↑",
        "down": "↓",
        "left": "←",
        "right": "→",
    }
    label_key = special.get(key, label_key)
    return "".join(_MOD_LABEL.get(m, m) for m in mods) + label_key


def event_to_hotkey(event) -> str:
    """Convert an NSEvent keyDown into a normalized hotkey string."""
    try:
        from AppKit import (  # type: ignore
            NSAlternateKeyMask,
            NSCommandKeyMask,
            NSControlKeyMask,
            NSShiftKeyMask,
        )
    except Exception:
        return ""

    try:
        flags = int(event.modifierFlags())
    except Exception:
        return ""

    mods = []
    if flags & NSControlKeyMask:
        mods.append("ctrl")
    if flags & NSAlternateKeyMask:
        mods.append("alt")
    if flags & NSShiftKeyMask:
        mods.append("shift")
    if flags & NSCommandKeyMask:
        mods.append("cmd")
    if not mods:
        return ""

    key = ""
    try:
        chars = event.charactersIgnoringModifiers() or ""
        if chars:
            ch = chars[0]
            code = ord(ch)
            if 32 < code < 127:
                key = ch.lower()
            elif ch == " ":
                key = "space"
            elif code == 13:
                key = "return"
            elif code == 9:
                key = "tab"
            elif code == 27:
                key = "escape"
            elif code == 127:
                key = "delete"
    except Exception:
        key = ""

    if not key:
        # Function / arrow keys via keyCode fallback
        try:
            kc = int(event.keyCode())
        except Exception:
            return ""
        keymap = {
            36: "return",
            48: "tab",
            49: "space",
            51: "delete",
            53: "escape",
            123: "left",
            124: "right",
            125: "down",
            126: "up",
            122: "f1",
            120: "f2",
            99: "f3",
            118: "f4",
            96: "f5",
            97: "f6",
            98: "f7",
            100: "f8",
            101: "f9",
            109: "f10",
            103: "f11",
            111: "f12",
        }
        key = keymap.get(kc, "")
    if not key:
        return ""
    return normalize_hotkey("+".join(mods + [key]))


def match_event(event, spec: str) -> bool:
    want = normalize_hotkey(spec)
    if not want:
        return False
    got = event_to_hotkey(event)
    return bool(got) and got == want


class HotkeyCenter:
    """Local + global NSEvent monitors for configurable app hotkeys."""

    def __init__(self) -> None:
        self._bindings: Dict[str, Tuple[str, Callable[[], None]]] = {}
        self._local = None
        self._global = None
        self._recording: Optional[str] = None  # binding id being recorded
        self._on_recorded: Optional[Callable[[str, str], None]] = None
        self._on_record_cancel: Optional[Callable[[], None]] = None
        self._enabled = True
        self._global_ok = False

    @property
    def global_ok(self) -> bool:
        return self._global_ok

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)

    def set_bindings(self, bindings: Dict[str, Tuple[str, Callable[[], None]]]) -> None:
        """bindings: id -> (hotkey_spec, callback)."""
        cleaned: Dict[str, Tuple[str, Callable[[], None]]] = {}
        for key, (spec, cb) in (bindings or {}).items():
            cleaned[str(key)] = (normalize_hotkey(spec), cb)
        self._bindings = cleaned

    def start_record(
        self,
        binding_id: str,
        *,
        on_recorded: Callable[[str, str], None],
        on_cancel: Optional[Callable[[], None]] = None,
    ) -> None:
        self._recording = str(binding_id)
        self._on_recorded = on_recorded
        self._on_record_cancel = on_cancel

    def cancel_record(self) -> None:
        was = self._recording
        self._recording = None
        self._on_recorded = None
        cb = self._on_record_cancel
        self._on_record_cancel = None
        if was and cb:
            try:
                cb()
            except Exception:
                pass

    def _handle(self, event, *, consume: bool) -> Any:
        if event is None:
            return event

        # Recording mode
        if self._recording:
            try:
                from AppKit import NSControlKeyMask, NSAlternateKeyMask, NSCommandKeyMask, NSShiftKeyMask  # type: ignore

                flags = int(event.modifierFlags())
                kc = int(event.keyCode())
            except Exception:
                return event if consume else None

            # Esc cancels
            if kc == 53:
                bid = self._recording
                self.cancel_record()
                return None if consume else None
            # Delete / Backspace clears
            if kc == 51:
                bid = self._recording
                on_rec = self._on_recorded
                self._recording = None
                self._on_recorded = None
                self._on_record_cancel = None
                if on_rec and bid:
                    try:
                        on_rec(bid, "")
                    except Exception:
                        pass
                return None if consume else None

            # Ignore bare modifier key presses
            if kc in (54, 55, 56, 57, 58, 59, 60, 61, 62, 63):
                return event if consume else None

            mods_present = bool(
                flags
                & (NSControlKeyMask | NSAlternateKeyMask | NSCommandKeyMask | NSShiftKeyMask)
            )
            if not mods_present:
                return event if consume else None

            spec = event_to_hotkey(event)
            if not spec:
                return event if consume else None
            bid = self._recording
            on_rec = self._on_recorded
            self._recording = None
            self._on_recorded = None
            self._on_record_cancel = None
            if on_rec and bid:
                try:
                    on_rec(bid, spec)
                except Exception:
                    pass
            return None if consume else None

        if not self._enabled:
            return event if consume else None

        for _bid, (spec, cb) in list(self._bindings.items()):
            if not spec:
                continue
            if match_event(event, spec):
                try:
                    cb()
                except Exception:
                    pass
                return None if consume else None
        return event if consume else None

    def install(self) -> None:
        self.uninstall()
        try:
            from AppKit import NSEvent, NSKeyDownMask  # type: ignore
        except Exception:
            return

        def local_handler(event):
            return self._handle(event, consume=True)

        def global_handler(event):
            self._handle(event, consume=False)

        try:
            self._local = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
                NSKeyDownMask, local_handler
            )
        except Exception:
            self._local = None

        try:
            self._global = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                NSKeyDownMask, global_handler
            )
            self._global_ok = self._global is not None
        except Exception:
            self._global = None
            self._global_ok = False

    def uninstall(self) -> None:
        try:
            from AppKit import NSEvent  # type: ignore

            if self._local is not None:
                NSEvent.removeMonitor_(self._local)
            if self._global is not None:
                NSEvent.removeMonitor_(self._global)
        except Exception:
            pass
        self._local = None
        self._global = None
        self._global_ok = False


def hotkey_payload(cfg: Dict[str, Any], *, global_ok: bool = True) -> Dict[str, Any]:
    out: Dict[str, Any] = {"global_ok": bool(global_ok)}
    for key in DEFAULT_HOTKEYS:
        spec = normalize_hotkey(cfg.get(key, DEFAULT_HOTKEYS[key]))
        out[key] = spec
        out[key + "_label"] = format_hotkey(spec)
    return out
