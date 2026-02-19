"""
Sequential Paste Clipboard Utility
Main entry point for the application
"""
import sys
import os
import threading
import time
import tempfile
import msvcrt

# Import error logger first to capture any startup errors
import error_logger

from clipboard_manager import ClipboardManager
from hotkey_handler import HotkeyHandler, set_handler
from tray_icon import TrayIcon
from config import APP_NAME, APP_VERSION
from settings_manager import get_settings
import notification


# Single instance lock file
_lock_file = None


def is_already_running() -> bool:
    """Check if another instance is already running using a lock file"""
    global _lock_file
    
    lock_path = os.path.join(tempfile.gettempdir(), 'sequential_paste.lock')
    
    try:
        # Try to open and lock the file
        _lock_file = open(lock_path, 'w')
        msvcrt.locking(_lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        return False  # Lock acquired, we're the only instance
    except (IOError, OSError):
        return True  # Lock failed, another instance is running


def main():
    """Main application entry point"""
    
    # Check for existing instance
    if is_already_running():
        print("Sequential Paste is already running!")
        notification.show_toast(
            APP_NAME,
            "Already running in system tray",
            timeout=2
        )
        sys.exit(0)
    
    print(f"Starting {APP_NAME} v{APP_VERSION}...")
    
    # Load settings
    settings = get_settings()
    
    # Initialize components
    clipboard_manager = ClipboardManager()
    
    # Apply saved delimiter setting
    saved_delimiter = settings.get_delimiter()
    clipboard_manager.set_delimiter(saved_delimiter)
    
    hotkey_handler = HotkeyHandler(clipboard_manager)
    tray_icon = TrayIcon(clipboard_manager)
    
    # Set up callbacks for UI updates
    def update_tray():
        tray_icon.update_menu()
    
    hotkey_handler.set_callbacks(
        on_position_change=update_tray
    )
    
    # Store global reference
    set_handler(hotkey_handler)
    
    # Set up exit callback
    running = threading.Event()
    running.set()
    
    def on_exit():
        print("Shutting down...")
        hotkey_handler.stop()
        running.clear()
    
    tray_icon.set_exit_callback(on_exit)
    
    # Start hotkey listener
    hotkey_handler.start()
    print("Hotkey listener started")
    print(f"  - Ctrl+Shift+V: Paste next segment")
    print(f"  - Ctrl+Shift+N: Skip segment")
    print(f"  - Ctrl+Shift+B: Go back")
    print(f"  - Ctrl+Shift+R: Reset sequence")
    print(f"  - Copy any text to load sequence")
    
    # Show startup notification
    notification.show_toast(
        APP_NAME,
        "Running in system tray. Copy text to start.",
        timeout=3
    )
    
    # Run tray icon (this blocks until exit)
    try:
        tray_icon.run()
    except KeyboardInterrupt:
        on_exit()
    
    print(f"{APP_NAME} has stopped.")


if __name__ == "__main__":
    main()
