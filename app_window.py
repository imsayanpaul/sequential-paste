"""
App Window - the main window with the current list, settings and
animated previews of what each option does.

Built on pywebview (Microsoft Edge WebView2). The window is created hidden at
startup and shown from the tray; closing it only hides it again.
"""
import json
import logging
import os
import sys
from typing import Callable, Optional

from clipboard_manager import ClipboardManager
from config import APP_NAME, DelimiterType
from hotkey_handler import HotkeyHandler
from settings_manager import get_settings, is_startup_enabled, set_startup_with_windows

# Long lists are cut down for display; the window only needs to show context
MAX_ITEMS_SHOWN = 500
MAX_ITEM_LENGTH = 120


def _ui_path() -> str:
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, 'ui', 'index.html')


class _Api:
    """Methods the page calls as window.pywebview.api.*; each returns the new state"""

    def __init__(self, window: 'AppWindow'):
        self._w = window

    def get_state(self):
        return self._w.state()

    def set_option(self, kind, value):
        w = self._w
        settings = get_settings()
        if kind == 'split':
            delimiter = DelimiterType(value)
            w.clipboard_manager.set_delimiter(delimiter)
            settings.set_delimiter(delimiter)
        elif kind == 'insert' and value in ('paste', 'type'):
            settings.set('paste_mode', value)
        elif kind == 'after' and value in ('none', 'tab', 'enter'):
            settings.set('after_each', value)
        w.changed(from_window=True)
        return w.state()

    def set_toggle(self, key, on):
        settings = get_settings()
        if key == 'notifications':
            settings.set('toast_enabled', bool(on))
        elif key == 'sounds':
            settings.set('sounds', bool(on))
        elif key == 'startup':
            set_startup_with_windows(bool(on))
        self._w.changed(from_window=True)
        return self._w.state()

    def set_paused(self, on):
        # set_paused triggers the state callback, which refreshes everything
        self._w.hotkey_handler.set_paused(bool(on))
        return self._w.state()

    def action(self, name):
        handler = self._w.hotkey_handler
        manager = self._w.clipboard_manager
        # Run directly rather than through the hotkey queue so the returned
        # state already includes the change
        if name == 'skip':
            manager.skip_segment()
        elif name == 'back':
            manager.go_back()
        elif name == 'reset':
            manager.reset()
        self._w.changed(from_window=True)
        return self._w.state()


class AppWindow:
    def __init__(self, clipboard_manager: ClipboardManager, hotkey_handler: HotkeyHandler):
        self.clipboard_manager = clipboard_manager
        self.hotkey_handler = hotkey_handler
        self._window = None
        self._ready = False
        self._quitting = False
        self._on_change: Optional[Callable] = None

    def set_change_callback(self, callback: Callable):
        """Called when the user changes something in the window (to refresh the tray)"""
        self._on_change = callback

    def state(self) -> dict:
        manager = self.clipboard_manager
        settings = get_settings()
        current, total = manager.get_position()
        items = [s[:MAX_ITEM_LENGTH] for s in manager.segments[:MAX_ITEMS_SHOWN]]
        return {
            'paused': self.hotkey_handler.paused,
            'active': self.hotkey_handler.has_active_sequence,
            'current': current,
            'total': total,
            'items': items,
            'split': manager.delimiter.value,
            'insert': settings.get('paste_mode', 'paste'),
            'after': settings.get('after_each', 'none'),
            'notifications': bool(settings.get('toast_enabled', False)),
            'sounds': bool(settings.get('sounds', True)),
            'startup': is_startup_enabled(),
        }

    def changed(self, from_window: bool = False):
        if from_window and self._on_change:
            self._on_change()

    def push_state(self):
        """Send the current state to the page (any thread)"""
        if not (self._window and self._ready):
            return
        try:
            self._window.evaluate_js(f"window.app && window.app.render({json.dumps(self.state())})")
        except Exception:
            logging.exception("Failed to update the window")

    def create(self) -> None:
        """Create the (hidden) window. Must be called before run()."""
        import webview

        # Load the page as a string: no file paths or local server involved.
        # data-app tells the page to wait for this backend instead of using
        # its built-in demo data.
        with open(_ui_path(), encoding='utf-8') as f:
            html = f.read().replace('<html lang="en">', '<html lang="en" data-app>', 1)
        self._window = webview.create_window(
            APP_NAME, html=html, js_api=_Api(self), hidden=True,
            width=1000, height=720, min_size=(760, 520),
            background_color='#202020' if _dark_mode() else '#f3f3f3',
        )

        def on_loaded():
            self._ready = True

        def on_closing():
            # Closing the window keeps the app running in the tray
            if self._quitting:
                return True
            self._window.hide()
            return False

        self._window.events.loaded += on_loaded
        self._window.events.closing += on_closing

    def show(self):
        if not self._window:
            return
        self.push_state()
        self._window.show()
        self._window.restore()

    def run(self, on_started: Optional[Callable] = None):
        """Run the window event loop on the main thread (blocks until quit)"""
        import webview
        webview.start(on_started, private_mode=False, storage_path=_storage_path())

    def quit(self):
        self._quitting = True
        if self._window:
            self._window.destroy()


def _storage_path() -> str:
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    return os.path.join(appdata, APP_NAME, 'webview')


def _dark_mode() -> bool:
    """Whether Windows apps use the dark theme (avoids a white flash on open)"""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
        winreg.CloseKey(key)
        return value == 0
    except Exception:
        return False
