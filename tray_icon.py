"""
System Tray Icon - Background application interface
"""
import pystray
from PIL import Image, ImageDraw
import threading
from typing import Callable, Optional
from config import APP_NAME, APP_VERSION, DelimiterType
from clipboard_manager import ClipboardManager
from settings_manager import get_settings, set_startup_with_windows, is_startup_enabled
import notification


class TrayIcon:
    """System tray icon with menu for settings and status"""
    
    def __init__(self, clipboard_manager: ClipboardManager):
        self.clipboard_manager = clipboard_manager
        self.icon: Optional[pystray.Icon] = None
        self._on_exit: Optional[Callable] = None
        self.settings = get_settings()
    
    def set_exit_callback(self, callback: Callable):
        """Set callback for when user clicks Exit"""
        self._on_exit = callback
    
    def _create_icon_image(self, color: str = "#4CAF50") -> Image.Image:
        """Create a simple icon image"""
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw clipboard background
        draw.rounded_rectangle(
            [8, 4, 56, 60],
            radius=6,
            fill=color
        )
        
        # Draw clipboard clip at top
        draw.rectangle([24, 0, 40, 10], fill="#333333")
        draw.rectangle([20, 6, 44, 14], fill="#666666")
        
        # Draw lines representing text
        line_color = "#FFFFFF"
        draw.rectangle([14, 22, 50, 26], fill=line_color)
        draw.rectangle([14, 32, 45, 36], fill=line_color)
        draw.rectangle([14, 42, 48, 46], fill=line_color)
        
        return image
    
    def _get_status_text(self) -> str:
        """Get current status for tooltip"""
        if not self.clipboard_manager.has_content:
            return f"{APP_NAME} - No content"
        
        current, total = self.clipboard_manager.get_position()
        remaining = self.clipboard_manager.get_remaining_count()
        
        if remaining == 0:
            return f"{APP_NAME} - Complete ({total} items)"
        else:
            return f"{APP_NAME} - {remaining}/{total} remaining"
    
    def _get_preview_text(self) -> str:
        """Get preview of next segment"""
        next_seg = self.clipboard_manager.peek_next_segment()
        if next_seg:
            # Truncate if too long
            if len(next_seg) > 50:
                return f"Next: {next_seg[:47]}..."
            return f"Next: {next_seg}"
        return "No content"
    
    def _set_delimiter(self, delimiter: DelimiterType):
        """Change delimiter and update menu"""
        def action(icon, item):
            self.clipboard_manager.set_delimiter(delimiter)
            self.settings.set_delimiter(delimiter)
            self.update_menu()
        return action
    
    def _reset_sequence(self, icon, item):
        """Reset sequence to start"""
        self.clipboard_manager.reset()
        notification.notify_sequence_reset()
        self.update_menu()
    
    def _toggle_startup(self, icon, item):
        """Toggle startup with Windows"""
        current = is_startup_enabled()
        if set_startup_with_windows(not current):
            self.settings.set('startup_with_windows', not current)
            status = "enabled" if not current else "disabled"
            notification.show_toast(APP_NAME, f"Startup with Windows {status}")
        else:
            notification.show_toast(APP_NAME, "Failed to change startup setting")
        self.update_menu()
    
    def _set_paste_mode(self, mode: str):
        """Change paste mode (paste or type)"""
        def action(icon, item):
            self.settings.set('paste_mode', mode)
            mode_name = "Paste (Ctrl+V)" if mode == 'paste' else "Type (simulate keys)"
            notification.show_toast(APP_NAME, f"Mode: {mode_name}")
            self.update_menu()
        return action
    
    def _exit_app(self, icon, item):
        """Exit the application"""
        if self._on_exit:
            self._on_exit()
        icon.stop()
    
    def _create_menu(self) -> pystray.Menu:
        """Create the right-click menu"""
        current_delimiter = self.clipboard_manager.delimiter
        startup_enabled = is_startup_enabled()
        
        # Status and preview
        if self.clipboard_manager.has_content:
            current, total = self.clipboard_manager.get_position()
            remaining = self.clipboard_manager.get_remaining_count()
            status_text = f"Position: {current}/{total} ({remaining} remaining)"
            preview_text = self._get_preview_text()
        else:
            status_text = "No content loaded"
            preview_text = "Copy text to start"
        
        return pystray.Menu(
            pystray.MenuItem(
                f"📋 {status_text}",
                None,
                enabled=False
            ),
            pystray.MenuItem(
                f"👁️ {preview_text}",
                None,
                enabled=False
            ),
            pystray.Menu.SEPARATOR,
            # Delimiter options directly in main menu
            pystray.MenuItem(
                "📝 Sentence (. ! ?)",
                pystray.Menu(
                    pystray.MenuItem(
                        "✓ Use this delimiter",
                        self._set_delimiter(DelimiterType.SENTENCE)
                    ),
                    pystray.MenuItem(
                        "ℹ️ 'Hello. World!' → 'Hello.' then 'World!'",
                        None,
                        enabled=False
                    ),
                ),
                checked=lambda item: current_delimiter == DelimiterType.SENTENCE
            ),
            pystray.MenuItem(
                "📄 Line (newline)",
                pystray.Menu(
                    pystray.MenuItem(
                        "✓ Use this delimiter",
                        self._set_delimiter(DelimiterType.LINE)
                    ),
                    pystray.MenuItem(
                        "ℹ️ Line1↵Line2 → 'Line1' then 'Line2'",
                        None,
                        enabled=False
                    ),
                ),
                checked=lambda item: current_delimiter == DelimiterType.LINE
            ),
            pystray.MenuItem(
                "📃 Paragraph (blank line)",
                pystray.Menu(
                    pystray.MenuItem(
                        "✓ Use this delimiter",
                        self._set_delimiter(DelimiterType.PARAGRAPH)
                    ),
                    pystray.MenuItem(
                        "ℹ️ Para1↵↵Para2 → 'Para1' then 'Para2'",
                        None,
                        enabled=False
                    ),
                ),
                checked=lambda item: current_delimiter == DelimiterType.PARAGRAPH
            ),
            pystray.Menu.SEPARATOR,
            # Paste mode options
            pystray.MenuItem(
                "📋 Paste Mode (Ctrl+V)",
                pystray.Menu(
                    pystray.MenuItem(
                        "✓ Use this mode",
                        self._set_paste_mode('paste')
                    ),
                    pystray.MenuItem(
                        "ℹ️ Fast, uses clipboard. Default.",
                        None,
                        enabled=False
                    ),
                ),
                checked=lambda item: self.settings.get('paste_mode', 'paste') == 'paste'
            ),
            pystray.MenuItem(
                "⌨️ Type Mode (simulate keys)",
                pystray.Menu(
                    pystray.MenuItem(
                        "✓ Use this mode",
                        self._set_paste_mode('type')
                    ),
                    pystray.MenuItem(
                        "ℹ️ Slower, but works on paste-blocked fields.",
                        None,
                        enabled=False
                    ),
                ),
                checked=lambda item: self.settings.get('paste_mode', 'paste') == 'type'
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "🚀 Start with Windows",
                self._toggle_startup,
                checked=lambda item: startup_enabled
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Shortcuts",
                pystray.Menu(
                    pystray.MenuItem("Ctrl+Shift+V: Paste next", None, enabled=False),
                    pystray.MenuItem("Ctrl+Shift+N: Skip", None, enabled=False),
                    pystray.MenuItem("Ctrl+Shift+B: Go back", None, enabled=False),
                    pystray.MenuItem("Ctrl+Shift+R: Reset", None, enabled=False),
                )
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                f"ℹ️ {APP_NAME} v{APP_VERSION}",
                None,
                enabled=False
            ),
            pystray.MenuItem(
                "❌ Exit",
                self._exit_app
            )
        )
    
    def update_menu(self):
        """Update the menu to reflect current state"""
        if self.icon:
            self.icon.menu = self._create_menu()
            self.icon.title = self._get_status_text()
    
    def run(self):
        """Start the tray icon (blocking)"""
        self.icon = pystray.Icon(
            APP_NAME,
            self._create_icon_image(),
            self._get_status_text(),
            self._create_menu()
        )
        self.icon.run()
    
    def run_detached(self):
        """Start the tray icon in a background thread"""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        return thread
    
    def stop(self):
        """Stop the tray icon"""
        if self.icon:
            self.icon.stop()

