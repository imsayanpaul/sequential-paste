import ctypes
import logging
import queue
import keyboard
import pyperclip
import threading
import time
from typing import Callable, Optional
from clipboard_manager import ClipboardManager
from config import HOTKEYS, AFTER_EACH_KEYS
from settings_manager import get_settings
import notification


# Modifiers the user is still physically holding when a hotkey fires.
# They must be released before we send Ctrl+V or type text, otherwise the
# target app sees Ctrl+Shift+V / Ctrl+Shift+<char> instead.
_MODIFIERS = ['ctrl', 'shift', 'left ctrl', 'right ctrl', 'left shift', 'right shift']

# How long apps get to read the clipboard after Ctrl+V before we put the
# user's own clipboard back. Some apps read it asynchronously.
CLIPBOARD_RESTORE_DELAY = 0.3


def _clipboard_seq_num() -> int:
    """Windows clipboard sequence number (changes on every clipboard write)"""
    try:
        return ctypes.windll.user32.GetClipboardSequenceNumber()
    except Exception:
        return 0


class HotkeyHandler:
    """Manages global hotkeys for sequential paste functionality"""

    def __init__(self, clipboard_manager: ClipboardManager):
        self.clipboard_manager = clipboard_manager
        self.running = False
        self.paused = False
        self._clipboard_monitor_thread: Optional[threading.Thread] = None
        self._worker_thread: Optional[threading.Thread] = None
        self._actions: "queue.Queue[Optional[Callable]]" = queue.Queue()
        self._on_state_change: Optional[Callable] = None
        self._last_clipboard_content: str = ""
        self._last_clip_seq_num: int = 0
        # Serializes clipboard checks between the monitor and the worker
        self._clipboard_lock = threading.Lock()
        # Set while Type Mode is typing a segment
        self._typing = threading.Event()

    def set_state_callback(self, callback: Optional[Callable]):
        """Called (from any thread) whenever position, content or pause state changes"""
        self._on_state_change = callback

    def _update_position(self):
        """Trigger state change callback"""
        if self._on_state_change:
            try:
                self._on_state_change()
            except Exception:
                logging.exception("State change callback failed")

    # ------------------------------------------------------------------
    # Clipboard tracking
    # ------------------------------------------------------------------

    def _sync_clipboard(self) -> bool:
        """
        Load the clipboard into the sequence if the user copied something new.
        Uses Windows GetClipboardSequenceNumber to detect genuine copy actions.
        Returns True if a new sequence was loaded.
        """
        with self._clipboard_lock:
            seq_num = _clipboard_seq_num()

            # If system sequence number hasn't changed, user has NOT performed a new copy
            if seq_num > 0 and seq_num == self._last_clip_seq_num:
                return False

            current_clipboard = pyperclip.paste()
            # Remember this sequence number so we don't re-read the clipboard
            # every poll for content we've already decided to ignore
            self._last_clip_seq_num = seq_num

            if not current_clipboard or not current_clipboard.strip():
                return False

            # Skip if clipboard matches the single segment we JUST copied in Paste Mode
            if (current_clipboard == self._last_clipboard_content and
                current_clipboard != self.clipboard_manager.current_content):
                return False

            # Genuine new copy operation detected!
            self._last_clipboard_content = current_clipboard
            self.clipboard_manager.load_text(current_clipboard)

        count = self.clipboard_manager.total_segments
        logging.debug("New copy detected (seq #%s), loaded %d segments", seq_num, count)
        if count > 1:
            notification.notify_sequence_loaded(count)
        self._update_position()
        return True

    def _set_clipboard(self, text: str):
        """Write to the clipboard without the monitor mistaking it for a user copy"""
        with self._clipboard_lock:
            pyperclip.copy(text)
            self._last_clipboard_content = text
            self._last_clip_seq_num = _clipboard_seq_num()

    def _clipboard_monitor_loop(self):
        """Background thread that picks up copies made by any method"""
        while self.running:
            try:
                self._sync_clipboard()
            except Exception:
                logging.exception("Clipboard monitor error")

            # Poll every 500ms
            time.sleep(0.5)

    # ------------------------------------------------------------------
    # Hotkey dispatch
    # ------------------------------------------------------------------

    @property
    def has_active_sequence(self) -> bool:
        """True when a copy split into more than one item"""
        return self.clipboard_manager.total_segments > 1

    def _should_capture(self) -> bool:
        """
        Whether our shortcuts should act, or pass through to the focused app
        (Ctrl+Shift+V is paste-as-plain-text in browsers, Ctrl+Shift+N is a
        new incognito window, and so on).
        Runs inside the keyboard hook, so it must be instant: no locks, no I/O.
        """
        if self.paused:
            return False
        if self.has_active_sequence:
            return True
        # A copy the monitor hasn't loaded yet may be a multi-item sequence;
        # capture and let the worker decide
        return _clipboard_seq_num() != self._last_clip_seq_num

    def _hotkey_callback(self, action: Callable, hotkey: str) -> Callable:
        """
        Wrap an action for keyboard.add_hotkey.
        With suppress=True the keyboard library calls the callback inside the
        Windows low-level keyboard hook; slow work there (typing a long
        segment) makes Windows drop the hook and every hotkey stops working.
        The callback must return a falsy value so the keys stay suppressed.
        """
        def callback():
            if not self._should_capture():
                # Hand the shortcut to the focused app. Returning True from
                # here isn't enough: the library has already swallowed Ctrl
                # and Shift, so the app would only get a bare "v". Replay the
                # whole combination instead - outside the hook, since sending
                # keys from inside it stalls all keyboard input.
                self._actions.put(lambda: self._replay(hotkey))
                return None
            # Ignore Ctrl+Shift+V while a segment is still being typed, so
            # impatient repeated presses don't queue up a burst of typing
            if self._typing.is_set() and action == self._on_sequential_paste:
                return None
            self._actions.put(action)
            return None
        return callback

    def _replay(self, hotkey: str):
        """Send a shortcut on to the focused app (the hook ignores keys we send)"""
        keyboard.send(hotkey)

    def _submit(self, action: Callable):
        """Queue an action from outside the keyboard hook (e.g. the tray menu)"""
        self._actions.put(action)

    def _worker_loop(self):
        """Runs hotkey actions one at a time, outside the keyboard hook"""
        while True:
            action = self._actions.get()
            if action is None:
                return
            try:
                # Pick up a copy the monitor hasn't polled yet, so a quick
                # Ctrl+C then Ctrl+Shift+V pastes the NEW text, not the old one
                self._sync_clipboard()
                action()
            except Exception:
                logging.exception("Hotkey action failed")

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def _type_text(self, text: str) -> bool:
        """
        Type text as keystrokes. Holding Esc cancels.
        Returns False if cancelled.
        """
        self._typing.set()
        try:
            for char in text:
                if keyboard.is_pressed('esc'):
                    return False
                # restore_state_after=False: by default keyboard.write presses
                # the modifiers that were held when typing started (Ctrl+Shift
                # from the hotkey) back down afterwards. The user has released
                # them by then, so they stayed stuck down system-wide and every
                # key and click became Ctrl+Shift+<key>.
                keyboard.write(char, restore_state_after=False)
                time.sleep(0.01)
            return True
        finally:
            self._typing.clear()

    def _paste_text(self, text: str):
        """Paste via the clipboard, then put the user's clipboard back"""
        if not text:
            # Empty spreadsheet cell: nothing to paste
            return
        try:
            original = pyperclip.paste()
        except Exception:
            original = ""

        self._set_clipboard(text)
        keyboard.send('ctrl+v')

        # Only text can be restored; if the clipboard held an image or files,
        # it keeps the pasted item instead
        if original and original != text:
            time.sleep(CLIPBOARD_RESTORE_DELAY)
            self._set_clipboard(original)

    def _release_modifiers(self):
        for key in _MODIFIERS:
            try:
                keyboard.release(key)
            except Exception:
                pass
        time.sleep(0.05)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _on_sequential_paste(self):
        """Handle Ctrl+Shift+V - Paste next segment"""
        if not self.clipboard_manager.has_content:
            notification.notify_no_content()
            return

        # Check if sequence is exhausted - if so, stop cleanly (DO NOT auto-loop old text!)
        segment = self.clipboard_manager.get_next_segment()
        if segment is None:
            notification.notify_sequence_complete(self.clipboard_manager.total_segments)
            self._update_position()
            return

        settings = get_settings()
        self._release_modifiers()

        if settings.get('paste_mode', 'paste') == 'type':
            # Type mode: simulate keystrokes (works on paste-blocked fields)
            if not self._type_text(segment):
                # Step back so the cancelled segment can be typed again
                self.clipboard_manager.go_back()
                notification.show_toast("Typing cancelled")
                self._update_position()
                return
        else:
            self._paste_text(segment)

        after_key = AFTER_EACH_KEYS.get(settings.get('after_each', 'none'))
        if after_key:
            # Give the app a moment to take the paste before moving on
            time.sleep(0.05)
            keyboard.send(after_key)

        current, total = self.clipboard_manager.get_position()
        notification.notify_paste_position(current, total)

        self._update_position()

    def _on_reset(self):
        """Handle Ctrl+Shift+R - Reset sequence"""
        self.clipboard_manager.reset()
        notification.notify_sequence_reset()
        self._update_position()

    def _on_skip(self):
        """Handle Ctrl+Shift+N - Skip current segment"""
        if not self.clipboard_manager.has_content:
            notification.notify_no_content()
            return

        if self.clipboard_manager.skip_segment():
            current, total = self.clipboard_manager.get_position()
            if current >= total:
                notification.show_toast("Skipped the last item. Sequence finished.")
            else:
                notification.show_toast(f"Skipped. Next is {current + 1} of {total}")
            self._update_position()
        else:
            notification.notify_sequence_complete(self.clipboard_manager.total_segments)

    def _on_go_back(self):
        """Handle Ctrl+Shift+B - Go back to previous segment"""
        if not self.clipboard_manager.has_content:
            notification.notify_no_content()
            return

        if self.clipboard_manager.go_back():
            current, total = self.clipboard_manager.get_position()
            notification.show_toast(f"Next is {current + 1} of {total}")
            self._update_position()
        else:
            notification.show_toast("Already at the first item")

    # Tray menu entry points

    def skip(self):
        self._submit(self._on_skip)

    def go_back(self):
        self._submit(self._on_go_back)

    def reset(self):
        self._submit(self._on_reset)

    def set_paused(self, paused: bool):
        """Pause or resume the shortcuts; while paused they reach other apps as usual"""
        self.paused = paused
        notification.notify_paused(paused)
        self._update_position()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        """Start listening for hotkeys and clipboard changes"""
        if self.running:
            return

        self.running = True

        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

        # Start clipboard monitor thread (detects ALL copy methods). Its first
        # poll also loads whatever was copied before the app started.
        self._clipboard_monitor_thread = threading.Thread(
            target=self._clipboard_monitor_loop,
            daemon=True
        )
        self._clipboard_monitor_thread.start()

        actions = {
            'sequential_paste': self._on_sequential_paste,
            'reset_sequence': self._on_reset,
            'skip_segment': self._on_skip,
            'go_back': self._on_go_back,
        }
        for name, action in actions.items():
            keyboard.add_hotkey(HOTKEYS[name], self._hotkey_callback(action, HOTKEYS[name]),
                                suppress=True)

    def stop(self):
        """Stop listening for hotkeys and clipboard monitor"""
        self.running = False
        keyboard.unhook_all_hotkeys()
        self._actions.put(None)
