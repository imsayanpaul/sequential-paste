"""
System Tray Icon - Background application interface
"""
import ctypes
import os
import threading
import pystray
from PIL import Image, ImageDraw, ImageOps
from typing import Callable, Optional
from config import APP_NAME, DelimiterType
from clipboard_manager import ClipboardManager
from hotkey_handler import HotkeyHandler
from settings_manager import get_settings, set_startup_with_windows, is_startup_enabled
import notification


Item = pystray.MenuItem
SEPARATOR = pystray.Menu.SEPARATOR

# (value, label, what it does) - the description is shown beside each choice
DELIMITER_CHOICES = [
    (DelimiterType.LINE, "Lines", "each line is one item"),
    (DelimiterType.COMMA, "Commas", "red, green, blue  →  3 items"),
    (DelimiterType.TAB, "Spreadsheet cells", "each cell, row by row"),
    (DelimiterType.SENTENCE, "Sentences", "each sentence is one item"),
    (DelimiterType.PARAGRAPH, "Paragraphs", "split at blank lines"),
]

PASTE_MODE_CHOICES = [
    ('paste', "Pasting", "fast, works in most apps"),
    ('type', "Typing it out", "for fields that block pasting"),
]

AFTER_EACH_CHOICES = [
    ('none', "Do nothing", "stay in the same field"),
    ('tab', "Press Tab", "jump to the next form field"),
    ('enter', "Press Enter", "new line, or submit"),
]

HELP_TEXT = (
    "1. Copy a list: several lines, comma-separated values, "
    "or cells from a spreadsheet.\n"
    "2. Click where the first item should go.\n"
    "3. Press Ctrl+Shift+V. Each press inserts the next item.\n"
    "\n"
    "Ctrl+Shift+N skips an item, Ctrl+Shift+B goes back one, "
    "Ctrl+Shift+R starts over.\n"
    "\n"
    "Filling in a form? Set \"After each item\" to \"Press Tab\" and keep "
    "pressing Ctrl+Shift+V to fill one field after another.\n"
    "\n"
    "When no list is loaded, or the shortcuts are paused, the shortcuts "
    "work as normal in other apps. Click the tray icon to pause."
)

PREVIEW_LENGTH = 32


def _escape(text: str) -> str:
    """Make arbitrary text safe for a Windows menu label"""
    # '&' marks a keyboard accelerator in Win32 menus, and tabs/newlines
    # would break the layout
    text = ' '.join(text.split())
    return text.replace('&', '&&')


def _current_label(choices, value) -> str:
    """Current choice shown next to a submenu, e.g. 'Split copied text into    Lines'"""
    for key, label, _ in choices:
        if key == value:
            return label
    return ''


class TrayIcon:
    """System tray icon with menu for settings and status"""

    def __init__(self, clipboard_manager: ClipboardManager, hotkey_handler: HotkeyHandler):
        self.clipboard_manager = clipboard_manager
        self.hotkey_handler = hotkey_handler
        self.icon: Optional[pystray.Icon] = None
        self._on_exit: Optional[Callable] = None
        self.settings = get_settings()
        self._images = self._build_images()
        self._update_lock = threading.Lock()

    def set_exit_callback(self, callback: Callable):
        """Set callback for when user clicks Quit"""
        self._on_exit = callback

    # ------------------------------------------------------------------
    # Icon images
    # ------------------------------------------------------------------

    def _load_base_image(self) -> Image.Image:
        """Get application icon from assets or fallback to generated icon"""
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'icon.ico')
        try:
            image = Image.open(icon_path)
            image.load()
            return image.convert('RGBA').resize((64, 64), Image.LANCZOS)
        except Exception:
            return self._create_icon_image()

    def _create_icon_image(self) -> Image.Image:
        """Simple clipboard icon, used if the asset is missing"""
        image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle([8, 4, 56, 60], radius=6, fill="#3FA34D")
        draw.rectangle([20, 0, 44, 12], fill="#2D7A38")
        for top, right in ((22, 50), (32, 45), (42, 48)):
            draw.rectangle([14, top, right, top + 4], fill="#FFFFFF")
        return image

    def _build_images(self) -> dict:
        base = self._load_base_image()

        # Paused: greyscale, slightly faded
        alpha = base.getchannel('A').point(lambda a: int(a * 0.6))
        paused = ImageOps.grayscale(base).convert('RGBA')
        paused.putalpha(alpha)

        # Finished: small check badge in the corner
        done = base.copy()
        draw = ImageDraw.Draw(done)
        draw.ellipse([30, 30, 63, 63], fill="#1F6FEB", outline="#FFFFFF", width=3)
        draw.line([(38, 47), (44, 53), (55, 39)], fill="#FFFFFF", width=5)

        return {'active': base, 'paused': paused, 'done': done}

    def _current_image(self) -> Image.Image:
        if self.hotkey_handler.paused:
            return self._images['paused']
        if self.hotkey_handler.has_active_sequence and self.clipboard_manager.is_exhausted():
            return self._images['done']
        return self._images['active']

    # ------------------------------------------------------------------
    # Status text
    # ------------------------------------------------------------------

    def _status_text(self) -> str:
        if self.hotkey_handler.paused:
            return "Shortcuts paused"
        if not self.hotkey_handler.has_active_sequence:
            return "No list loaded"
        current, total = self.clipboard_manager.get_position()
        if current >= total:
            return f"All {total} items pasted"
        return f"{current} of {total} pasted"

    def _next_text(self) -> Optional[str]:
        if not self.hotkey_handler.has_active_sequence:
            return None
        next_seg = self.clipboard_manager.peek_next_segment()
        if next_seg is None:
            return None
        if not next_seg:
            preview = "(empty cell)"
        else:
            preview = ' '.join(next_seg.split())
            if len(preview) > PREVIEW_LENGTH:
                preview = preview[:PREVIEW_LENGTH - 1].rstrip() + "…"
            preview = f"“{preview}”"
        return _escape(f"Paste next: {preview}") + "\tCtrl+Shift+V"

    def _tooltip(self) -> str:
        # Windows truncates tray tooltips at 127 characters
        return f"{APP_NAME}: {self._status_text()}"[:127]

    # ------------------------------------------------------------------
    # Menu actions
    # ------------------------------------------------------------------

    def _set_delimiter(self, delimiter: DelimiterType):
        def action(icon, item):
            self.clipboard_manager.set_delimiter(delimiter)
            self.settings.set_delimiter(delimiter)
            self.update()
        return action

    def _set_setting(self, key: str, value):
        def action(icon, item):
            self.settings.set(key, value)
            self.update()
        return action

    def _toggle_setting(self, key: str, default: bool):
        def action(icon, item):
            self.settings.set(key, not self.settings.get(key, default))
            self.update()
        return action

    def _toggle_startup(self, icon, item):
        set_startup_with_windows(not is_startup_enabled())
        self.update()

    def _toggle_pause(self, icon, item):
        self.hotkey_handler.set_paused(not self.hotkey_handler.paused)

    def _show_help(self, icon, item):
        # A message box blocks, so keep it off the tray's message loop
        def show():
            MB_ICONINFORMATION = 0x40
            ctypes.windll.user32.MessageBoxW(None, HELP_TEXT, f"How to use {APP_NAME}",
                                             MB_ICONINFORMATION)
        threading.Thread(target=show, daemon=True).start()

    def _quit(self, icon, item):
        if self._on_exit:
            self._on_exit()
        icon.stop()

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _choice_menu(self, choices, current, make_action) -> pystray.Menu:
        return pystray.Menu(*[
            Item(f"{label}\t{hint}", make_action(value),
                 checked=lambda item, v=value: v == current, radio=True)
            for value, label, hint in choices
        ])

    def _create_menu(self) -> pystray.Menu:
        """Create the right-click menu"""
        handler = self.hotkey_handler
        active = handler.has_active_sequence
        current, total = self.clipboard_manager.get_position()
        next_text = self._next_text()

        delimiter = self.clipboard_manager.delimiter
        paste_mode = self.settings.get('paste_mode', 'paste')
        after_each = self.settings.get('after_each', 'none')
        toasts = self.settings.get('toast_enabled', False)
        sounds = self.settings.get('sounds', True)
        startup = is_startup_enabled()
        paused = handler.paused

        return pystray.Menu(
            Item(self._status_text(), None, enabled=False),
            Item(next_text or "Copy two or more lines, then press Ctrl+Shift+V",
                 None, enabled=False, visible=next_text is not None or not active),
            SEPARATOR,
            Item("Skip next item\tCtrl+Shift+N", lambda icon, item: handler.skip(),
                 enabled=active and current < total),
            Item("Previous item\tCtrl+Shift+B", lambda icon, item: handler.go_back(),
                 enabled=active and current > 0),
            Item("Start over\tCtrl+Shift+R", lambda icon, item: handler.reset(),
                 enabled=active and current > 0),
            SEPARATOR,
            Item(f"Split copied text into\t{_current_label(DELIMITER_CHOICES, delimiter)}",
                 self._choice_menu(DELIMITER_CHOICES, delimiter, self._set_delimiter)),
            Item(f"Insert items by\t{_current_label(PASTE_MODE_CHOICES, paste_mode)}",
                 self._choice_menu(PASTE_MODE_CHOICES, paste_mode,
                                   lambda v: self._set_setting('paste_mode', v))),
            Item(f"After each item\t{_current_label(AFTER_EACH_CHOICES, after_each)}",
                 self._choice_menu(AFTER_EACH_CHOICES, after_each,
                                   lambda v: self._set_setting('after_each', v))),
            SEPARATOR,
            Item("Show notifications", self._toggle_setting('toast_enabled', False),
                 checked=lambda item: toasts),
            Item("Beep when a list is finished", self._toggle_setting('sounds', True),
                 checked=lambda item: sounds),
            Item("Start with Windows", self._toggle_startup,
                 checked=lambda item: startup),
            SEPARATOR,
            # Default item: drawn bold, and runs when the tray icon is clicked
            Item("Pause shortcuts", self._toggle_pause,
                 checked=lambda item: paused, default=True),
            Item("How to use…", self._show_help),
            Item(f"Quit {APP_NAME}", self._quit),
        )

    def update(self):
        """Refresh menu, tooltip and icon to reflect current state (any thread)"""
        if not self.icon:
            return
        with self._update_lock:
            self.icon.menu = self._create_menu()
            self.icon.title = self._tooltip()
            image = self._current_image()
            if self.icon.icon is not image:
                self.icon.icon = image

    def run(self, on_ready: Optional[Callable] = None):
        """Start the tray icon (blocking)"""
        self.icon = pystray.Icon(
            APP_NAME,
            self._current_image(),
            self._tooltip(),
            self._create_menu()
        )

        def setup(icon):
            icon.visible = True
            notification.set_icon(icon)
            if on_ready:
                on_ready()

        self.icon.run(setup=setup)
