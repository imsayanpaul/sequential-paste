"""
Configuration settings for Sequential Paste Clipboard Utility
"""
import re
from enum import Enum

class DelimiterType(Enum):
    SENTENCE = "sentence"
    LINE = "line"
    PARAGRAPH = "paragraph"
    COMMA = "comma"

# Common abbreviations that should NOT trigger sentence breaks
ABBREVIATIONS = [
    'Mr', 'Mrs', 'Ms', 'Dr', 'Prof', 'Sr', 'Jr', 'vs', 'etc', 'i.e', 'e.g',
    'Inc', 'Ltd', 'Co', 'Corp', 'St', 'Ave', 'Blvd', 'Rd',
    'Jan', 'Feb', 'Mar', 'Apr', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
    'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun',
    'No', 'Vol', 'Rev', 'Ed', 'Fig', 'Ch', 'Sec', 'pp',
]

# Delimiter patterns for splitting text
# Note: SENTENCE uses a function-based approach for abbreviation handling
DELIMITER_PATTERNS = {
    DelimiterType.SENTENCE: None,  # Handled specially in clipboard_manager
    DelimiterType.LINE: r'\n',                   # Split on newlines
    DelimiterType.PARAGRAPH: r'\n\s*\n',         # Split on blank lines
    DelimiterType.COMMA: r',',                   # Split on commas
}

# Hotkey configurations
HOTKEYS = {
    'sequential_paste': 'ctrl+shift+v',
    'reset_sequence': 'ctrl+shift+r',
    'skip_segment': 'ctrl+shift+n',
    'go_back': 'ctrl+shift+b',
}

# Notification settings
NOTIFICATIONS = {
    'sound_enabled': True,
    'toast_enabled': True,
    'show_position': True,  # Show "Pasted 2/3" in notification
}

# Application settings
APP_NAME = "Sequential Paste"
APP_VERSION = "1.0.0"
DEFAULT_DELIMITER = DelimiterType.LINE

# Sound frequency for completion beep (Hz)
COMPLETION_SOUND_FREQ = 800
COMPLETION_SOUND_DURATION = 150  # milliseconds
