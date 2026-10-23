"""
Build script for creating standalone executable
Run this script to create SequentialPaste.exe
"""
import PyInstaller.__main__
import os
import shutil

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
    
    # Add data files if assets folder exists
    if os.path.exists('assets'):
        args.extend(['--add-data', 'assets;assets'])
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)
    
    print("\n" + "="*50)
    print(f"BUILD COMPLETE!")
    print(f"Executable: dist/{APP_NAME}.exe")
    print("="*50)


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
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'clean':
        clean()
    else:
        build()
