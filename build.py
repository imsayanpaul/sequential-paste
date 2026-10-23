"""
Build script for creating standalone executable
Run this script to create SequentialPaste.exe
"""
import PyInstaller.__main__
import os
import shutil
import sys

# Configuration
APP_NAME = "SequentialPaste"
MAIN_SCRIPT = "main.py"
ICON_PATH = "assets/icon.ico"  # Will use default if not exists

def build():
    """Build the executable"""
    print("Building Sequential Paste executable...")
    
    # Base PyInstaller arguments
    args = [
        MAIN_SCRIPT,
        '--name', APP_NAME,
        '--onefile',           # Single executable
        '--windowed',          # No console window
        '--clean',             # Clean build
        '--noconfirm',         # Overwrite without asking
    ]
    
    # Add icon if exists
    if os.path.exists(ICON_PATH):
        args.extend(['--icon', ICON_PATH])
    
    # Hidden imports that PyInstaller might miss
    hidden_imports = [
        'pystray._win32',
        'PIL._tkinter_finder',
    ]
    
    for imp in hidden_imports:
        args.extend(['--hidden-import', imp])
    
    # Data files: tray icon assets and the app window's page
    for folder in ('assets', 'ui'):
        if os.path.exists(folder):
            args.extend(['--add-data', f'{folder};{folder}'])
    
    # pywebview loads its Windows backend and .NET bridge dynamically
    for module in ('webview.platforms.winforms', 'webview.platforms.edgechromium', 'clr'):
        args.extend(['--hidden-import', module])
    
    work_around_python_3_10_0_dis_bug()
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)
    
    print("\n" + "="*50)
    print(f"BUILD COMPLETE!")
    print(f"Executable: dist/{APP_NAME}.exe")
    print("="*50)


def work_around_python_3_10_0_dis_bug():
    """
    Python 3.10.0's dis module crashes on some bytecode (fixed in 3.10.1),
    which aborts PyInstaller's import scan. It's triggered by bottle.py, which
    pywebview imports. Skip the scan of any code object that hits the bug.
    That can miss the skipped code's imports; for bottle they are standard
    library modules the app bundles anyway. Better: use Python 3.10.1+.
    """
    if sys.version_info[:3] != (3, 10, 0):
        return
    import PyInstaller.lib.modulegraph.modulegraph as modulegraph
    original = modulegraph.util.iterate_instructions
    
    def iterate_instructions(code):
        try:
            return list(original(code))
        except IndexError:
            print(f"Skipping bytecode scan of {code.co_filename} (Python 3.10.0 dis bug)")
            return []
    
    modulegraph.util.iterate_instructions = iterate_instructions


def clean():
    """Clean build artifacts"""
    dirs_to_remove = ['build', '__pycache__', f'{APP_NAME}.spec']
    
    for d in dirs_to_remove:
        if os.path.exists(d):
            if os.path.isdir(d):
                shutil.rmtree(d)
            else:
                os.remove(d)
            print(f"Removed: {d}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'clean':
        clean()
    else:
        build()
