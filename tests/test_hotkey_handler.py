"""
HotkeyHandler tests with fake keyboard and clipboard modules, so nothing is
typed, pasted or hooked on the machine running the tests.
"""
import os
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class FakeKeyboard(types.ModuleType):
    def __init__(self):
        super().__init__('keyboard')
        self.events = []
        self.esc_pressed = False

    def release(self, key):
        self.events.append(('release', key))

    def send(self, key):
        self.events.append(('send', key))

    def write(self, text, delay=0, restore_state_after=True):
        # Re-pressing held modifiers after typing left Ctrl/Shift stuck
        assert restore_state_after is False
        self.events.append(('write', text))

    def is_pressed(self, key):
        return key == 'esc' and self.esc_pressed

    def add_hotkey(self, *args, **kwargs):
        pass

    def unhook_all_hotkeys(self):
        pass

    def sent(self):
        return [e[1] for e in self.events if e[0] == 'send']

    def typed(self):
        return ''.join(e[1] for e in self.events if e[0] == 'write')


class FakeClipboard(types.ModuleType):
    def __init__(self):
        super().__init__('pyperclip')
        self.text = ''
        self.seq = 1
        self.pasted = []  # clipboard contents at each Ctrl+V

    def paste(self):
        return self.text

    def copy(self, text):
        self.text = text
        self.seq += 1

    def user_copies(self, text):
        self.copy(text)


fake_keyboard = FakeKeyboard()
fake_clipboard = FakeClipboard()
sys.modules['keyboard'] = fake_keyboard
sys.modules['pyperclip'] = fake_clipboard

import hotkey_handler  # noqa: E402
import notification  # noqa: E402
import settings_manager  # noqa: E402
from clipboard_manager import ClipboardManager  # noqa: E402
from config import DelimiterType  # noqa: E402


class HotkeyHandlerTest(unittest.TestCase):
    def setUp(self):
        self._appdata = tempfile.TemporaryDirectory()
        os.environ['APPDATA'] = self._appdata.name
        settings_manager._settings = None

        fake_keyboard.events.clear()
        fake_keyboard.esc_pressed = False
        fake_clipboard.text = ''
        fake_clipboard.seq = 1

        # Record what Ctrl+V would have pasted
        original_send = FakeKeyboard.send
        def send(kb, key):
            if key == 'ctrl+v':
                fake_clipboard.pasted.append(fake_clipboard.text)
            original_send(kb, key)
        fake_keyboard.send = types.MethodType(send, fake_keyboard)
        fake_clipboard.pasted = []

        self.notices = []
        self._patches = {
            (hotkey_handler, '_clipboard_seq_num'): lambda: fake_clipboard.seq,
            (hotkey_handler, 'CLIPBOARD_RESTORE_DELAY'): 0,
            (notification, 'show_toast'): lambda msg, force=False: self.notices.append(msg),
            (notification, 'play_completion_sound'): lambda: self.notices.append('beep'),
        }
        self._saved = {}
        for (module, name), value in self._patches.items():
            self._saved[(module, name)] = getattr(module, name)
            setattr(module, name, value)

        self.manager = ClipboardManager()
        self.handler = hotkey_handler.HotkeyHandler(self.manager)

    def tearDown(self):
        for (module, name), value in self._saved.items():
            setattr(module, name, value)
        settings_manager._settings = None
        self._appdata.cleanup()

    def press(self, action, hotkey='ctrl+shift+x'):
        """
        Simulate the keyboard hook firing, then run the worker.
        Returns True if the shortcut was passed on to the focused app.
        """
        callback = self.handler._hotkey_callback(action, hotkey)
        # The hook must always suppress; pass-through is done by replaying
        self.assertIsNone(callback())
        while not self.handler._actions.empty():
            queued = self.handler._actions.get()
            self.handler._sync_clipboard()
            queued()
        return hotkey in fake_keyboard.sent()

    def paste(self):
        return self.press(self.handler._on_sequential_paste)

    # Smart pass-through

    def test_passes_through_without_a_list(self):
        fake_clipboard.user_copies('just one word')
        self.handler._sync_clipboard()
        self.assertTrue(self.paste())
        self.assertTrue(self.press(self.handler._on_skip))
        self.assertEqual(fake_clipboard.pasted, [])

    def test_captures_a_list(self):
        fake_clipboard.user_copies('one\ntwo')
        self.handler._sync_clipboard()
        self.assertFalse(self.paste())
        self.assertEqual(fake_clipboard.pasted, ['one'])

    def test_captures_a_copy_the_monitor_has_not_seen_yet(self):
        fake_clipboard.user_copies('one\ntwo')
        # No _sync_clipboard: the user pressed Ctrl+Shift+V straight after Ctrl+C
        self.assertFalse(self.paste())
        self.assertEqual(fake_clipboard.pasted, ['one'])

    def test_pause_passes_everything_through(self):
        fake_clipboard.user_copies('one\ntwo')
        self.handler._sync_clipboard()
        self.handler.set_paused(True)
        self.assertTrue(self.paste())
        self.handler.set_paused(False)
        fake_keyboard.events.clear()
        self.assertFalse(self.paste())

    def test_finished_list_still_captures(self):
        fake_clipboard.user_copies('one\ntwo')
        for _ in range(3):
            self.assertFalse(self.paste())
        self.assertEqual(fake_clipboard.pasted, ['one', 'two'])
        self.assertIn('beep', self.notices)

    # Paste mode

    def test_restores_the_users_clipboard(self):
        fake_clipboard.user_copies('one\ntwo')
        self.paste()
        self.assertEqual(fake_clipboard.text, 'one\ntwo')
        # ...and the restore is not mistaken for a new copy
        self.assertFalse(self.handler._sync_clipboard())
        self.assertEqual(self.manager.get_position(), (1, 2))

    def test_releases_modifiers_before_pasting(self):
        fake_clipboard.user_copies('one\ntwo')
        self.paste()
        releases = [e[1] for e in fake_keyboard.events if e[0] == 'release']
        self.assertIn('shift', releases)
        self.assertIn('ctrl', releases)

    def test_after_each_tab(self):
        settings_manager.get_settings().set('after_each', 'tab')
        fake_clipboard.user_copies('one\ntwo')
        self.paste()
        self.assertEqual(fake_keyboard.sent(), ['ctrl+v', 'tab'])

    def test_empty_cell_still_presses_tab(self):
        settings_manager.get_settings().set('after_each', 'tab')
        self.manager.set_delimiter(DelimiterType.TAB)
        fake_clipboard.user_copies('a\t\tc')
        self.paste()
        self.paste()
        self.assertEqual(fake_keyboard.sent(), ['ctrl+v', 'tab', 'tab'])
        self.assertEqual(fake_clipboard.pasted, ['a'])

    # Type mode

    def test_type_mode(self):
        settings_manager.get_settings().set('paste_mode', 'type')
        settings_manager.get_settings().set('after_each', 'enter')
        fake_clipboard.user_copies('hello\nworld')
        self.paste()
        self.assertEqual(fake_keyboard.typed(), 'hello')
        self.assertEqual(fake_keyboard.sent(), ['enter'])
        self.assertEqual(fake_clipboard.pasted, [])

    def test_esc_cancels_typing_and_keeps_the_item(self):
        settings_manager.get_settings().set('paste_mode', 'type')
        fake_clipboard.user_copies('hello\nworld')
        fake_keyboard.esc_pressed = True
        self.paste()
        self.assertEqual(fake_keyboard.typed(), '')
        self.assertEqual(self.manager.peek_next_segment(), 'hello')

    def test_presses_while_typing_are_ignored(self):
        fake_clipboard.user_copies('one\ntwo')
        self.handler._sync_clipboard()
        self.handler._typing.set()
        self.handler._hotkey_callback(self.handler._on_sequential_paste, 'ctrl+shift+v')()
        self.assertTrue(self.handler._actions.empty())
        self.handler._typing.clear()


if __name__ == '__main__':
    unittest.main()
