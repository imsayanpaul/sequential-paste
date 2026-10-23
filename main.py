"""
Sequential Paste Clipboard Utility
Main entry point for the application
"""
import sys
import ctypes
import logging
import threading

# Import error logger first to capture any startup errors
import error_logger

from clipboard_manager import ClipboardManager
from hotkey_handler import HotkeyHandler
from tray_icon import TrayIcon
from app_window import AppWindow
from config import APP_NAME, APP_VERSION
from settings_manager import get_settings
import notification


# Single instance mutex handle (kept open for the lifetime of the process)
_instance_mutex = None
ERROR_ALREADY_EXISTS = 183


def is_already_running() -> bool:
    """Check if another instance is already running using a named mutex"""
    global _instance_mutex

    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    _instance_mutex = kernel32.CreateMutexW(None, False, "Local\\SequentialPaste_SingleInstance")
    return kernel32.GetLastError() == ERROR_ALREADY_EXISTS


def show_message(text: str) -> None:
    """Show a message box (the windowed exe has no console for print)"""
    MB_ICONINFORMATION = 0x40
    ctypes.windll.user32.MessageBoxW(None, text, APP_NAME, MB_ICONINFORMATION)


def main():
    """Main application entry point"""
    
    # Check for existing instance
    if is_already_running():
        print("Sequential Paste is already running!")
        show_message(f"{APP_NAME} is already running. Click its icon in the system tray to open it.")
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
    tray_icon = TrayIcon(clipboard_manager, hotkey_handler)
    window = AppWindow(clipboard_manager, hotkey_handler)
    
    # Keep the tray and the window in sync with each other and the sequence
    def refresh_all():
        tray_icon.update()
        window.push_state()
    
    hotkey_handler.set_state_callback(refresh_all)
    tray_icon.set_change_callback(refresh_all)
    window.set_change_callback(tray_icon.update)
    
    def on_exit():
        print("Shutting down...")
        hotkey_handler.stop()
        window.quit()
    
    tray_icon.set_exit_callback(on_exit)
    
    # Start hotkey listener
    hotkey_handler.start()
    print("Hotkey listener started")
    print("  - Ctrl+Shift+V: Paste next item")
    print("  - Ctrl+Shift+N: Skip item")
    print("  - Ctrl+Shift+B: Go back")
    print("  - Ctrl+Shift+R: Start over")
    print("  - Copy a list to load a sequence")
    
    def on_ready():
        notification.show_toast("Running in the system tray. Copy a list to start.")
    
    # The tray runs on its own thread; the window needs the main thread
    tray_thread = threading.Thread(target=tray_icon.run, args=(on_ready,), daemon=True)
    
    try:
        window.create()
    except Exception:
        logging.exception("App window unavailable, running in the tray only")
        tray_icon.run(on_ready)
        print(f"{APP_NAME} has stopped.")
        return
    
    tray_icon.set_window_opener(window.show)
    tray_thread.start()
    
    def on_window_started():
        # Show the window once on first run, so new users see what the app does
        if not settings.get('welcome_shown', False):
            settings.set('welcome_shown', True)
            window.show()
    
    try:
        window.run(on_window_started)
    except Exception:
        # e.g. the WebView2 runtime is missing: keep running in the tray
        logging.exception("App window failed, running in the tray only")
        tray_icon.set_window_opener(None)
        tray_icon.update()
        tray_thread.join()
    except KeyboardInterrupt:
        on_exit()
    
    print(f"{APP_NAME} has stopped.")


if __name__ == "__main__":
    main()
