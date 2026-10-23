import ctypes
import logging
import queue
import keyboard
import pyperclip
import threading
import time
from typing import Callable, Optional
from clipboard_manager import ClipboardManager
from config import HOTKEYS
from settings_manager import get_settings
import notification


# Modifiers the user is still physically holding when a hotkey fires.
# They must be released before we send Ctrl+V or type text, otherwise the
# target app sees Ctrl+Shift+V / Ctrl+Shift+<char> instead.
_MODIFIERS = ['ctrl', 'shift', 'left ctrl', 'right ctrl', 'left shift', 'right shift']


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
        self._clipboard_monitor_thread: Optional[threading.Thread] = None
        self._worker_thread: Optional[threading.Thread] = None
        self._actions: "queue.Queue[Optional[Callable]]" = queue.Queue()
        self._on_delimiter_change: Optional[Callable] = None
        self._on_position_change: Optional[Callable] = None
        self._last_clipboard_content: str = ""
        self._last_clip_seq_num: int = 0
        # Serializes clipboard checks between the monitor and the worker
        self._clipboard_lock = threading.Lock()
        # Set while Type Mode is typing a segment
        self._typing = threading.Event()

    def set_callbacks(self,
                      on_delimiter_change: Optional[Callable] = None,
                      on_position_change: Optional[Callable] = None):
        """Set callback functions for UI updates"""
        self._on_delimiter_change = on_delimiter_change
        self._on_position_change = on_position_change

    def _update_position(self):
        """Trigger position change callback"""
        if self._on_position_change:
            try:
                self._on_position_change()
            except Exception:
                logging.exception("Position change callback failed")

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
        if count > 0:
            logging.debug("New copy detected (seq #%s), loaded %d segments", seq_num, count)
            notification.notify_sequence_loaded(count)
            self._update_position()
        return True

    def _clipboard_monitor_loop(self):
        """Background thread that picks up copies made by any method"""
        while self.running:
            try:
                self._sync_clipboard()
            except Exception:
                logging.exception("Clipboard monitor error")

            # Poll every 500ms
            time.sleep(0.5)

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

    def _enqueue(self, action: Callable) -> Callable:
        """
        Wrap an action for keyboard.add_hotkey.
        With suppress=True the keyboard library calls the callback inside the
        Windows low-level keyboard hook; slow work there (typing a long
        segment) makes Windows drop the hook and every hotkey stops working.
        The callback must also return a falsy value so the keys stay suppressed.
        """
        def callback():
            # Ignore Ctrl+Shift+V while a segment is still being typed, so
            # impatient repeated presses don't queue up a burst of typing
            if self._typing.is_set() and action == self._on_sequential_paste:
                return
            self._actions.put(action)
        return callback

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

    def _release_modifiers(self):
        for key in _MODIFIERS:
            try:
                keyboard.release(key)
            except Exception:
                pass
        time.sleep(0.05)

    def _on_sequential_paste(self):
        """Handle Ctrl+Shift+V - Paste next segment"""
        # Nothing loaded yet (e.g. text was copied before the app started):
        # load whatever is on the clipboard now
        if not self.clipboard_manager.has_content:
            with self._clipboard_lock:
                current = pyperclip.paste()
                if current and current.strip():
                    self.clipboard_manager.load_text(current)
                    self._last_clipboard_content = current
                    self._last_clip_seq_num = _clipboard_seq_num()
            count = self.clipboard_manager.total_segments
            if count > 0:
                notification.notify_sequence_loaded(count)
                self._update_position()

        if not self.clipboard_manager.has_content:
            notification.notify_no_content()
            return

        # Check if sequence is exhausted - if so, stop cleanly (DO NOT auto-loop old text!)
        segment = self.clipboard_manager.get_next_segment()
        if segment is None:
            notification.notify_sequence_complete(self.clipboard_manager.total_segments)
            return

        # Check paste mode from settings
        settings = get_settings()
        paste_mode = settings.get('paste_mode', 'paste')

        self._release_modifiers()

        if paste_mode == 'type':
            # Type mode: simulate keystrokes (works on paste-blocked fields)
            if not self._type_text(segment):
                # Step back so the cancelled segment can be typed again
                self.clipboard_manager.go_back()
                notification.show_toast(notification.APP_NAME, "Typing cancelled", timeout=1)
                self._update_position()
                return
        else:
            # Paste mode: use clipboard (faster)
            with self._clipboard_lock:
                pyperclip.copy(segment)
                # Track segment & update sequence number to prevent monitor re-triggering
                self._last_clipboard_content = segment
                self._last_clip_seq_num = _clipboard_seq_num()
            keyboard.send('ctrl+v')

        # Small delay to let action complete
        time.sleep(0.1)

        # Show position notification (respects toast_enabled setting)
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
                notification.show_toast(
                    notification.APP_NAME,
                    "Skipped to end. Sequence complete.",
                    timeout=2
                )
            else:
                notification.show_toast(
                    notification.APP_NAME,
                    f"Skipped. Now at {current + 1}/{total}",
                    timeout=1
                )
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
            notification.show_toast(
                notification.APP_NAME,
                f"Back to {current + 1}/{total}",
                timeout=1
            )
            self._update_position()
        else:
            notification.show_toast(
                notification.APP_NAME,
                "Already at start",
                timeout=1
            )

    def start(self):
        """Start listening for hotkeys and clipboard changes"""
        if self.running:
            return

        self.running = True

        # Text already on the clipboard at startup is not auto-loaded; the
        # first Ctrl+Shift+V picks it up via _sync_clipboard instead
        try:
            self._last_clipboard_content = pyperclip.paste() or ""
        except Exception:
            self._last_clipboard_content = ""

        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

        # Start clipboard monitor thread (detects ALL copy methods)
        self._clipboard_monitor_thread = threading.Thread(
            target=self._clipboard_monitor_loop,
            daemon=True
        )
        self._clipboard_monitor_thread.start()

        # Register hotkeys
        keyboard.add_hotkey(
            HOTKEYS['sequential_paste'],
            self._enqueue(self._on_sequential_paste),
            suppress=True
        )

        keyboard.add_hotkey(
            HOTKEYS['reset_sequence'],
            self._enqueue(self._on_reset),
            suppress=True
        )

        keyboard.add_hotkey(
            HOTKEYS['skip_segment'],
            self._enqueue(self._on_skip),
            suppress=True
        )

        keyboard.add_hotkey(
            HOTKEYS['go_back'],
            self._enqueue(self._on_go_back),
            suppress=True
        )

    def stop(self):
        """Stop listening for hotkeys and clipboard monitor"""
        self.running = False
        keyboard.unhook_all_hotkeys()
        self._actions.put(None)


# Global instance for easy access
_handler_instance: Optional[HotkeyHandler] = None


def get_handler() -> Optional[HotkeyHandler]:
    """Get the global hotkey handler instance"""
    return _handler_instance


def set_handler(handler: HotkeyHandler):
    """Set the global hotkey handler instance"""
    global _handler_instance
    _handler_instance = handler
