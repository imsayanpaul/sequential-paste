import ctypes
import keyboard
import pyperclip
import threading
import time
from typing import Callable, Optional
from clipboard_manager import ClipboardManager
from config import HOTKEYS
from settings_manager import get_settings
import notification


class HotkeyHandler:
    """Manages global hotkeys for sequential paste functionality"""
    
    def __init__(self, clipboard_manager: ClipboardManager):
        self.clipboard_manager = clipboard_manager
        self.running = False
        self._clipboard_monitor_thread: Optional[threading.Thread] = None
        self._on_delimiter_change: Optional[Callable] = None
        self._on_position_change: Optional[Callable] = None
        self._last_clipboard_content: str = ""
        self._last_clip_seq_num: int = 0
        self._is_pasting: bool = False  # Guard to prevent monitor interference
    
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
                pass
    
    def _clipboard_monitor_loop(self):
        """
        Background thread that monitors clipboard for ANY changes using
        Windows GetClipboardSequenceNumber to detect genuine user copy actions.
        """
        while self.running:
            try:
                # Skip monitoring while we're pasting (to avoid false detections)
                if self._is_pasting:
                    time.sleep(0.5)
                    continue
                
                try:
                    seq_num = ctypes.windll.user32.GetClipboardSequenceNumber()
                except Exception:
                    seq_num = 0
                
                # If system sequence number hasn't changed, user has NOT performed a new copy
                if seq_num > 0 and seq_num == self._last_clip_seq_num:
                    time.sleep(0.5)
                    continue
                
                current_clipboard = pyperclip.paste()
                if not current_clipboard or not current_clipboard.strip():
                    time.sleep(0.5)
                    continue
                
                # Skip if clipboard matches the single segment we JUST copied in Paste Mode
                if (current_clipboard == self._last_clipboard_content and 
                    current_clipboard != self.clipboard_manager.current_content):
                    time.sleep(0.5)
                    continue
                
                # Genuine new copy operation detected!
                self._last_clip_seq_num = seq_num
                self._last_clipboard_content = current_clipboard
                self.clipboard_manager.load_text(current_clipboard)
                count = self.clipboard_manager.total_segments
                if count > 0:
                    print(f"[DEBUG] New copy detected (seq #{seq_num})! Loaded {count} segments.")
                    notification.notify_sequence_loaded(count)
                    self._update_position()
            except Exception:
                pass
            
            # Poll every 500ms
            time.sleep(0.5)
    
    def _on_sequential_paste(self):
        """Handle Ctrl+Shift+V - Paste next segment"""
        # Check if we have content - if not, try loading from clipboard directly
        if not self.clipboard_manager.has_content:
            try:
                current = pyperclip.paste()
                if current and current.strip():
                    self.clipboard_manager.load_text(current)
                    self._last_clipboard_content = current
                    try:
                        self._last_clip_seq_num = ctypes.windll.user32.GetClipboardSequenceNumber()
                    except Exception:
                        pass
                    count = self.clipboard_manager.total_segments
                    if count > 0:
                        print(f"[DEBUG] Fallback load: {count} segments")
                        notification.notify_sequence_loaded(count)
                        self._update_position()
            except Exception:
                pass
        
        if not self.clipboard_manager.has_content:
            notification.notify_no_content()
            return
        
        # Check if sequence is exhausted - if so, stop cleanly (DO NOT auto-loop old text!)
        if self.clipboard_manager.is_exhausted():
            notification.notify_sequence_complete(self.clipboard_manager.total_segments)
            return
        
        # Get next segment
        segment = self.clipboard_manager.get_next_segment()
        if segment:
            # Set pasting flag to prevent monitor from interfering
            self._is_pasting = True
            
            try:
                # Check paste mode from settings
                settings = get_settings()
                paste_mode = settings.get('paste_mode', 'paste')
                
                if paste_mode == 'type':
                    # Release Ctrl and Shift modifiers so typed characters aren't treated as Ctrl+Shift shortcuts
                    keyboard.release('ctrl')
                    keyboard.release('shift')
                    keyboard.release('left ctrl')
                    keyboard.release('right ctrl')
                    keyboard.release('left shift')
                    keyboard.release('right shift')
                    time.sleep(0.05)
                    
                    # Type mode: simulate keystrokes (works on paste-blocked fields)
                    keyboard.write(segment, delay=0.01)
                else:
                    # Paste mode: use clipboard (faster)
                    pyperclip.copy(segment)
                    keyboard.send('ctrl+v')
                    # Track segment & update sequence number to prevent monitor re-triggering
                    self._last_clipboard_content = segment
                    try:
                        self._last_clip_seq_num = ctypes.windll.user32.GetClipboardSequenceNumber()
                    except Exception:
                        pass
                
                # Small delay to let action complete
                time.sleep(0.1)
            finally:
                self._is_pasting = False
            
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
            if self.clipboard_manager.is_exhausted():
                notification.show_toast(
                    notification.APP_NAME,
                    f"Skipped to end. Sequence complete.",
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
        
        # Initialize clipboard content tracking
        try:
            self._last_clipboard_content = pyperclip.paste() or ""
        except Exception:
            self._last_clipboard_content = ""
        
        # Start clipboard monitor thread (detects ALL copy methods)
        self._clipboard_monitor_thread = threading.Thread(
            target=self._clipboard_monitor_loop,
            daemon=True
        )
        self._clipboard_monitor_thread.start()
        
        # Register hotkeys
        keyboard.add_hotkey(
            HOTKEYS['sequential_paste'], 
            self._on_sequential_paste,
            suppress=True
        )
        
        keyboard.add_hotkey(
            HOTKEYS['reset_sequence'], 
            self._on_reset,
            suppress=True
        )
        
        keyboard.add_hotkey(
            HOTKEYS['skip_segment'], 
            self._on_skip,
            suppress=True
        )
        
        keyboard.add_hotkey(
            HOTKEYS['go_back'], 
            self._on_go_back,
            suppress=True
        )
    
    def stop(self):
        """Stop listening for hotkeys and clipboard monitor"""
        self.running = False
        keyboard.unhook_all_hotkeys()


# Global instance for easy access
_handler_instance: Optional[HotkeyHandler] = None


def get_handler() -> Optional[HotkeyHandler]:
    """Get the global hotkey handler instance"""
    return _handler_instance


def set_handler(handler: HotkeyHandler):
    """Set the global hotkey handler instance"""
    global _handler_instance
    _handler_instance = handler
