"""
Notification system - Audio and visual feedback
"""
import winsound
import threading
from config import (
    NOTIFICATIONS, 
    COMPLETION_SOUND_FREQ, 
    COMPLETION_SOUND_DURATION,
    APP_NAME
)

# Try to import plyer for toast notifications
try:
    from plyer import notification as plyer_notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False


def play_completion_sound():
    """Play a beep sound when sequence is exhausted"""
    if not NOTIFICATIONS.get('sound_enabled', True):
        return
    
    def _play():
        try:
            winsound.Beep(COMPLETION_SOUND_FREQ, COMPLETION_SOUND_DURATION)
        except Exception:
            pass
    
    # Play in background thread to avoid blocking
    threading.Thread(target=_play, daemon=True).start()


def play_success_sound():
    """Play a subtle click sound for successful paste"""
    def _play():
        try:
            # Higher frequency, shorter duration for success
            winsound.Beep(1200, 50)
        except Exception:
            pass
    
    threading.Thread(target=_play, daemon=True).start()


def is_toast_enabled() -> bool:
    """Check if toast notifications are enabled in settings"""
    try:
        from settings_manager import get_settings
        return get_settings().get('toast_enabled', False)
    except Exception:
        return False


def show_toast(title: str, message: str, timeout: int = 3):
    """Show a Windows toast notification if enabled"""
    if not is_toast_enabled():
        return
    
    if not PLYER_AVAILABLE:
        return
    
    def _show():
        try:
            plyer_notification.notify(
                title=title,
                message=message,
                app_name=APP_NAME,
                timeout=timeout
            )
        except Exception:
            pass
    
    # Show in background thread to avoid blocking
    threading.Thread(target=_show, daemon=True).start()


def notify_sequence_loaded(count: int):
    """Notify user that a new sequence has been loaded"""
    show_toast(
        APP_NAME,
        f"Sequence loaded: {count} item{'s' if count != 1 else ''} ready",
        timeout=2
    )


def notify_paste_position(current: int, total: int):
    """Notify user of current paste position"""
    if NOTIFICATIONS.get('show_position', True):
        show_toast(
            APP_NAME,
            f"Pasted {current}/{total}",
            timeout=1
        )


def notify_sequence_complete(total: int):
    """Notify user that sequence is exhausted"""
    play_completion_sound()
    show_toast(
        APP_NAME,
        f"Sequence complete! All {total} items pasted.",
        timeout=3
    )


def notify_sequence_reset():
    """Notify user that sequence was reset"""
    show_toast(
        APP_NAME,
        "Sequence reset to start",
        timeout=2
    )


def notify_no_content():
    """Notify user there's no content to paste"""
    play_completion_sound()
    show_toast(
        APP_NAME,
        "No content loaded. Copy text first with Ctrl+C",
        timeout=3
    )
