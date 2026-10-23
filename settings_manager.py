"""
Settings Manager - Persistent settings storage
"""
import json
import logging
import os
import sys
import winreg
from typing import Any, Optional
from config import DelimiterType, APP_NAME

# Settings file location
def get_settings_path() -> str:
    """Get path to settings file in user's AppData"""
    appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
    settings_dir = os.path.join(appdata, APP_NAME)
    os.makedirs(settings_dir, exist_ok=True)
    return os.path.join(settings_dir, 'settings.json')

# Default settings
DEFAULT_SETTINGS = {
    'delimiter': 'line',
    'paste_mode': 'paste',  # 'paste' = Ctrl+V, 'type' = simulate keystrokes
    'after_each': 'none',   # key pressed after each item: 'none', 'tab' or 'enter'
    'toast_enabled': False,  # Silent by default (no popup notifications on copy/paste)
    'sounds': True,          # Beep when the sequence is finished or empty
}


class SettingsManager:
    """Manages persistent application settings"""
    
    def __init__(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.load()
    
    def load(self) -> None:
        """Load settings from file"""
        try:
            path = get_settings_path()
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                if isinstance(saved, dict):
                    self.settings.update(saved)
        except Exception:
            logging.exception("Failed to load settings, using defaults")
    
    def save(self) -> None:
        """Save settings to file"""
        try:
            path = get_settings_path()
            # Write to a temp file and swap it in, so a crash mid-write
            # can't leave a truncated settings.json behind
            tmp_path = path + '.tmp'
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            os.replace(tmp_path, path)
        except Exception:
            logging.exception("Failed to save settings")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a setting value and save"""
        self.settings[key] = value
        self.save()
    
    def get_delimiter(self) -> DelimiterType:
        """Get the saved delimiter type"""
        delimiter_str = self.get('delimiter', 'line')
        try:
            return DelimiterType(delimiter_str)
        except ValueError:
            return DelimiterType.LINE
    
    def set_delimiter(self, delimiter: DelimiterType) -> None:
        """Set and save delimiter type"""
        self.set('delimiter', delimiter.value)


def get_exe_path() -> str:
    """Get the quoted startup command for the current executable"""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe. Quoted, because the default install dir
        # ("C:\Program Files\Sequential Paste") contains spaces.
        return f'"{sys.executable}"'
    else:
        # Running as script - prefer pythonw.exe so no console window opens
        python = sys.executable
        pythonw = os.path.join(os.path.dirname(python), 'pythonw.exe')
        if os.path.exists(pythonw):
            python = pythonw
        return f'"{python}" "{os.path.abspath(sys.argv[0])}"'


def set_startup_with_windows(enable: bool) -> bool:
    """
    Enable or disable startup with Windows.
    Returns True if successful.
    """
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        
        if enable:
            exe_path = get_exe_path()
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def is_startup_enabled() -> bool:
    """Check if startup with Windows is enabled"""
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False


# Global settings instance
_settings: Optional[SettingsManager] = None


def get_settings() -> SettingsManager:
    """Get the global settings manager"""
    global _settings
    if _settings is None:
        _settings = SettingsManager()
    return _settings
