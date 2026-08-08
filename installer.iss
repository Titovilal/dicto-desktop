#define MyAppName "Dicto"
; No edites MyAppVersion a mano: la fuente de verdad es pyproject.toml y
; `scripts/sync-installer-version.py` la reescribe aqui (lo llaman tanto
; `make installer` como el CI). Se habia quedado clavada en 2.5.1 con el
; proyecto en 2.8.4, y un build local escupia Dicto-2.5.1-setup.exe que el
; updater aceptaba como valido.
#define MyAppVersion "2.8.6"
#define MyAppPublisher "Titovilal"
#define MyAppURL "https://github.com/Titovilal/dicto-desktop"
#define MyAppExeName "Dicto.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=Dicto-{#MyAppVersion}-setup
SetupIconFile=assets\icons\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
; Let the in-app updater run this installer over a running Dicto: close the
; running instance before replacing files, and don't try to restart it itself
; (the [Run] section relaunches it once the upgrade finishes).
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startupicon"; Description: "Start Dicto when Windows starts"; GroupDescription: "Startup"

[Files]
Source: "dist\Dicto\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Dicto\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: startupicon

[Run]
; Interactive install: offer the usual "launch now" checkbox at the end.
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
; Silent install (in-app updater): relaunch Dicto automatically as the original,
; non-elevated user once the upgrade finishes.
Filename: "{app}\{#MyAppExeName}"; Flags: nowait runasoriginaluser skipifnotsilent
