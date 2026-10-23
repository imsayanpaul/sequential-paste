<p align="center">
  <img src="assets/icon.ico" alt="Sequential Paste" width="96" height="96">
</p>

<h1 align="center">Sequential Paste</h1>

<p align="center">
  Copy a list once, then paste it one item at a time.<br>
  A small Windows tray utility for filling in forms, spreadsheets and anything else that wants one value per field.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-blue" alt="Platform">
  <img src="https://img.shields.io/badge/license-MIT-lightgrey" alt="License">
</p>

---

## How it works

1. Copy a list: lines of text, comma-separated values, or cells from Excel or Google Sheets.
2. Click into the first field and press `Ctrl+Shift+V`. The first item is pasted.
3. Press `Ctrl+Shift+V` again for the second item, and so on.

Set **After each item** to **Press Tab** and you can fill a whole form by pressing `Ctrl+Shift+V` repeatedly, since each paste moves on to the next field.

<p align="center">
  <img src="assets/image.png" alt="The Sequential Paste tray menu" width="312">
</p>

## Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+V` | Paste the next item |
| `Ctrl+Shift+N` | Skip the next item |
| `Ctrl+Shift+B` | Go back one item |
| `Ctrl+Shift+R` | Start over from the first item |
| Hold `Esc` | Stop typing (when inserting by typing it out) |

These shortcuts only act while a list is loaded. When the clipboard holds a single item, or the shortcuts are paused, they reach the app you're using as normal, so `Ctrl+Shift+V` still pastes plain text in your browser and `Ctrl+Shift+N` still opens a private window.

Click the tray icon to pause or resume the shortcuts. The icon turns grey while paused, and shows a check mark once every item has been pasted.

## Settings

Everything is in the tray menu (right-click the icon).

**Split copied text into**

| Option | Input | Items |
|--------|-------|-------|
| Lines | `Line 1` ↵ `Line 2` | `Line 1`, `Line 2` |
| Commas | `apple, banana` | `apple`, `banana` |
| Spreadsheet cells | A copied range of cells | Each cell, row by row. Empty cells are kept so fields stay lined up. |
| Sentences | `Hello. How are you?` | `Hello.`, `How are you?` |
| Paragraphs | Text separated by blank lines | One item per paragraph |

Sentence splitting understands abbreviations (Mr., Dr., e.g.), decimals, URLs, email addresses and ellipses, and also splits on Hindi (।), Chinese and Japanese (。！？) and Arabic (؟) sentence endings.

**Insert items by**

- **Pasting**: fast, and works almost everywhere. Your clipboard is put back after each paste.
- **Typing it out**: types the text character by character. Use this for fields that block pasting.

**After each item**: do nothing, press Tab (jump to the next form field), or press Enter.

**Show notifications**, **Beep when a list is finished** and **Start with Windows** can be switched on and off. Notifications are off by default.

**How to use…** in the menu shows a short guide.

## Install

- **Installer**: download `SequentialPaste_Setup_v1.0.0.exe` from [Releases](../../releases).
- **Portable**: download `SequentialPaste.exe` from [Releases](../../releases) and run it.
- **From source** (Python 3.10+):

  ```bash
  git clone https://github.com/imsayanpaul/sequential-paste.git
  cd sequential-paste
  pip install -r requirements.txt
  python main.py
  ```

Settings are stored in `%APPDATA%\Sequential Paste\settings.json`, and errors are logged to `error.log` in the same folder.

## Development

```bash
python -m unittest discover -s tests   # run the tests
python build.py                        # build dist/SequentialPaste.exe
```

The installer is built from `installer.iss` with [Inno Setup](https://jrsoftware.org/isinfo.php).

| File | Purpose |
|------|---------|
| `main.py` | Entry point and single-instance check |
| `clipboard_manager.py` | Splitting text into items and tracking the position |
| `hotkey_handler.py` | Global shortcuts, clipboard monitoring, pasting and typing |
| `tray_icon.py` | Tray icon and menu |
| `notification.py` | Notifications and sounds |
| `settings_manager.py` | Settings file and the Start with Windows entry |
| `error_logger.py` | Error log |
| `config.py` | Constants |

## License

MIT. See [LICENSE](LICENSE).
