; Inno Setup Script for Sequential Paste
; Download Inno Setup from: https://jrsoftware.org/isdl.php
; Then compile this script to create Setup.exe

#define MyAppName "Sequential Paste"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Sayan Paul"
#define MyAppExeName "SequentialPaste.exe"

[Setup]
; Basic info
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

; Installation paths
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output settings
OutputDir=installer
OutputBaseFilename=SequentialPaste_Setup_v{#MyAppVersion}
SetupIconFile=assets\icon.ico
Compression=lzma
SolidCompression=yes

; Privileges (don't require admin for per-user install)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Modern look
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Start with Windows"; GroupDescription: "Startup:"

[Files]
; Main executable
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Icon file (optional)
Source: "assets\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

; README
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

; Desktop (optional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Startup with Windows (optional task)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: startupicon

[Run]
; Launch after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    MsgBox('Sequential Paste is now running in your system tray!' + #13#10 + #13#10 +
           'Look for the clipboard icon near the clock (bottom-right of your screen).' + #13#10 + #13#10 +
           'Shortcuts:' + #13#10 +
           '  Ctrl+Shift+V - Paste next segment' + #13#10 +
           '  Ctrl+Shift+N - Skip segment' + #13#10 +
           '  Ctrl+Shift+B - Go back' + #13#10 +
           '  Ctrl+Shift+R - Reset sequence',
           mbInformation, MB_OK);
  end;
end;
