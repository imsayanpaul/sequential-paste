"""
Fake keyboard and clipboard modules, installed before the app modules are
imported, so tests never type, paste or hook anything on the real machine.
"""
import sys
import types


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
