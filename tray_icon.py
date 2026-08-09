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
    
    def _toggle_notifications(self, icon, item):
        """Toggle toast notifications on/off"""
        current = self.settings.get('toast_enabled', False)
        self.settings.set('toast_enabled', not current)
        self.update_menu()

    def _toggle_startup(self, icon, item):
        """Toggle startup with Windows"""
        current = is_startup_enabled()
        if set_startup_with_windows(not current):
            self.settings.set('startup_with_windows', not current)
        self.update_menu()

    def _set_paste_mode(self, mode: str):
        """Change paste mode (paste or type)"""
        def action(icon, item):
            self.settings.set('paste_mode', mode)
            self.update_menu()
        return action
    
    def _exit_app(self, icon, item):
        """Exit the application"""
        if self._on_exit:
            self._on_exit()
        icon.stop()
    
    def _get_icon_image(self) -> Image.Image:
        """Get application icon from assets or fallback to generated icon"""
        import os
        for filename in ['icon.ico', 'icon.png']:
            icon_path = os.path.join(os.path.dirname(__file__), 'assets', filename)
            if os.path.exists(icon_path):
                try:
                    return Image.open(icon_path)
                except Exception:
                    pass
        return self._create_icon_image()

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
            pystray.MenuItem(
                "🔄 Reset Sequence",
                self._reset_sequence,
                enabled=self.clipboard_manager.has_content
            ),
            pystray.Menu.SEPARATOR,
            # Delimiter options - Direct single-click selection with inline examples
            pystray.MenuItem(
                "📄 Line  (Line1 ↵ Line2)",
                self._set_delimiter(DelimiterType.LINE),
                checked=lambda item: current_delimiter == DelimiterType.LINE,
                radio=True
            ),
            pystray.MenuItem(
                "🔤 Comma  (apple, banana)",
                self._set_delimiter(DelimiterType.COMMA),
                checked=lambda item: current_delimiter == DelimiterType.COMMA,
                radio=True
            ),
            pystray.MenuItem(
                "📝 Sentence  (Hello. World!)",
                self._set_delimiter(DelimiterType.SENTENCE),
                checked=lambda item: current_delimiter == DelimiterType.SENTENCE,
                radio=True
            ),
            pystray.MenuItem(
                "📃 Paragraph  (Para1 ↵↵ Para2)",
                self._set_delimiter(DelimiterType.PARAGRAPH),
                checked=lambda item: current_delimiter == DelimiterType.PARAGRAPH,
                radio=True
            ),
            pystray.Menu.SEPARATOR,
            # Paste mode options - Direct single-click selection
            pystray.MenuItem(
                "📋 Paste Mode  (Fast • Ctrl+V)",
                self._set_paste_mode('paste'),
                checked=lambda item: self.settings.get('paste_mode', 'paste') == 'paste',
                radio=True
            ),
            pystray.MenuItem(
                "⌨️ Type Mode  (Simulate keys)",
                self._set_paste_mode('type'),
                checked=lambda item: self.settings.get('paste_mode', 'paste') == 'type',
                radio=True
            ),
            pystray.Menu.SEPARATOR,
            # Hover side panel for detailed explanations
            pystray.MenuItem(
                "💡 Mode Details & Examples",
                pystray.Menu(
                    pystray.MenuItem("📄 Line Mode:", None, enabled=False),
                    pystray.MenuItem("   Splits text by newlines", None, enabled=False),
                    pystray.MenuItem("   Line 1↵Line 2 ➜ 'Line 1', 'Line 2'", None, enabled=False),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("🔤 Comma Mode:", None, enabled=False),
                    pystray.MenuItem("   Splits text at commas", None, enabled=False),
                    pystray.MenuItem("   apple, banana ➜ 'apple', 'banana'", None, enabled=False),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("📝 Sentence Mode:", None, enabled=False),
                    pystray.MenuItem("   Splits at . ! ? । 。 ؟", None, enabled=False),
                    pystray.MenuItem("   Handles Mr., Dr., URLs, decimals", None, enabled=False),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("📃 Paragraph Mode:", None, enabled=False),
                    pystray.MenuItem("   Splits at blank lines", None, enabled=False),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("📋 Paste Mode: Fast Ctrl+V paste", None, enabled=False),
                    pystray.MenuItem("⌨️ Type Mode: Works on blocked fields", None, enabled=False),
                )
            ),
            pystray.MenuItem(
                "🔔 Toast Notifications",
                self._toggle_notifications,
                checked=lambda item: self.settings.get('toast_enabled', False)
            ),
            pystray.MenuItem(
                "🚀 Start with Windows",
                self._toggle_startup,
                checked=lambda item: startup_enabled
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "⌨️ Shortcuts Guide",
                pystray.Menu(
                    pystray.MenuItem("Ctrl+Shift+V  ➜  Paste next segment", None, enabled=False),
                    pystray.MenuItem("Ctrl+Shift+N  ➜  Skip current segment", None, enabled=False),
                    pystray.MenuItem("Ctrl+Shift+B  ➜  Go back to previous", None, enabled=False),
                    pystray.MenuItem("Ctrl+Shift+R  ➜  Reset to start", None, enabled=False),
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
            self._get_icon_image(),
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

