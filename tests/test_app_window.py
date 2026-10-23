"""
Tests for the window's backend (the methods the page calls). The window
itself isn't created, so pywebview and WebView2 aren't needed.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fakes  # noqa: E402,F401  (must come before the app modules)

import app_window  # noqa: E402
import notification  # noqa: E402
import settings_manager  # noqa: E402
from clipboard_manager import ClipboardManager  # noqa: E402
from config import DelimiterType  # noqa: E402
from hotkey_handler import HotkeyHandler  # noqa: E402


class AppWindowApiTest(unittest.TestCase):
    def setUp(self):
        self._appdata = tempfile.TemporaryDirectory()
        os.environ['APPDATA'] = self._appdata.name
        settings_manager._settings = None

        # Keep the real Start with Windows registry entry untouched
        self.startup = False
        self._saved = {
            'is_startup_enabled': app_window.is_startup_enabled,
            'set_startup_with_windows': app_window.set_startup_with_windows,
            'show_toast': notification.show_toast,
        }
        app_window.is_startup_enabled = lambda: self.startup
        app_window.set_startup_with_windows = lambda on: setattr(self, 'startup', on) or True
        notification.show_toast = lambda *a, **k: None

        self.manager = ClipboardManager()
        self.handler = HotkeyHandler(self.manager)
        self.window = app_window.AppWindow(self.manager, self.handler)
        self.changes = 0
        self.window.set_change_callback(lambda: setattr(self, 'changes', self.changes + 1))
        self.api = app_window._Api(self.window)

    def tearDown(self):
        app_window.is_startup_enabled = self._saved['is_startup_enabled']
        app_window.set_startup_with_windows = self._saved['set_startup_with_windows']
        notification.show_toast = self._saved['show_toast']
        settings_manager._settings = None
        self._appdata.cleanup()

    def test_state_without_a_list(self):
        state = self.api.get_state()
        self.assertFalse(state['active'])
        self.assertEqual((state['current'], state['total']), (0, 0))
        self.assertEqual((state['split'], state['insert'], state['after']), ('line', 'paste', 'none'))

    def test_state_with_a_list(self):
        self.manager.load_text('a\nb\nc')
        self.manager.get_next_segment()
        state = self.api.get_state()
        self.assertTrue(state['active'])
        self.assertEqual(state['items'], ['a', 'b', 'c'])
        self.assertEqual((state['current'], state['total']), (1, 3))

    def test_long_items_are_shortened(self):
        self.manager.load_text('x' * 500 + '\ny')
        self.assertEqual(len(self.api.get_state()['items'][0]), app_window.MAX_ITEM_LENGTH)

    def test_split_option_resplits_and_is_saved(self):
        self.manager.load_text('a, b\nc')
        state = self.api.set_option('split', 'comma')
        self.assertEqual(state['items'], ['a', 'b\nc'])
        self.assertEqual(settings_manager.get_settings().get_delimiter(), DelimiterType.COMMA)
        self.assertEqual(self.changes, 1)

    def test_insert_and_after_options_are_saved(self):
        self.api.set_option('insert', 'type')
        state = self.api.set_option('after', 'tab')
        self.assertEqual((state['insert'], state['after']), ('type', 'tab'))
        settings = settings_manager.get_settings()
        self.assertEqual((settings.get('paste_mode'), settings.get('after_each')), ('type', 'tab'))

    def test_unknown_values_are_ignored(self):
        state = self.api.set_option('after', 'explode')
        self.assertEqual(state['after'], 'none')

    def test_toggles(self):
        state = self.api.set_toggle('notifications', True)
        self.assertTrue(state['notifications'])
        state = self.api.set_toggle('sounds', False)
        self.assertFalse(state['sounds'])
        state = self.api.set_toggle('startup', True)
        self.assertTrue(state['startup'])

    def test_pause(self):
        self.assertTrue(self.api.set_paused(True)['paused'])
        self.assertTrue(self.handler.paused)
        self.assertFalse(self.api.set_paused(False)['paused'])

    def test_navigation_actions(self):
        self.manager.load_text('a\nb\nc')
        self.assertEqual(self.api.action('skip')['current'], 1)
        self.assertEqual(self.api.action('skip')['current'], 2)
        self.assertEqual(self.api.action('back')['current'], 1)
        self.assertEqual(self.api.action('reset')['current'], 0)


if __name__ == '__main__':
    unittest.main()
