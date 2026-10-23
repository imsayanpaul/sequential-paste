"""
Notification system - Audio and visual feedback

Notifications are shown through the app's own tray icon (pystray), so they
carry the app's name and icon and don't create extra tray icons.
"""
import logging
import threading
import winsound
from config import (
    COMPLETION_SOUND_FREQ,
    COMPLETION_SOUND_DURATION,
    APP_NAME
)

# The running pystray.Icon, set by the tray once it is visible
_icon = None


def set_icon(icon) -> None:
    """Register the tray icon used to show notifications"""
    global _icon
    _icon = icon


def _setting(key: str, default):
    try:
        from settings_manager import get_settings
        return get_settings().get(key, default)
    except Exception:
        return default


def play_completion_sound():
    """Play a beep sound when sequence is exhausted"""
    if not _setting('sounds', True):
        return

    def _play():
        try:
            winsound.Beep(COMPLETION_SOUND_FREQ, COMPLETION_SOUND_DURATION)
        except Exception:
            pass

    # Play in background thread to avoid blocking
    threading.Thread(target=_play, daemon=True).start()


def show_toast(message: str, force: bool = False):
    """
    Show a Windows notification if notifications are enabled.
    force=True shows it regardless (for direct responses to a menu click).
    """
    if not (force or _setting('toast_enabled', False)):
        return
    if _icon is None:
        return
    try:
        _icon.notify(message, APP_NAME)
    except Exception:
        logging.exception("Failed to show notification")


def notify_sequence_loaded(count: int):
    """Notify user that a new sequence has been loaded"""
    show_toast(f"{count} item{'s' if count != 1 else ''} ready to paste")


def notify_paste_position(current: int, total: int):
    """Notify user of current paste position"""
    show_toast(f"Pasted {current} of {total}")


def notify_sequence_complete(total: int):
    """Notify user that sequence is exhausted"""
    play_completion_sound()
    show_toast(f"All {total} items pasted. Press Ctrl+Shift+R to start over.")


def notify_sequence_reset():
    """Notify user that sequence was reset"""
    show_toast("Back to the first item")


def notify_no_content():
    """Notify user there's no content to paste"""
    play_completion_sound()
    show_toast("Nothing to paste yet. Copy some text first.")


def notify_paused(paused: bool):
    """Confirm a pause toggle - always shown, since it changes what the shortcuts do"""
    if paused:
        show_toast("Shortcuts paused. Ctrl+Shift+V and the others work as usual in other apps.", force=True)
    else:
        show_toast("Shortcuts resumed", force=True)
