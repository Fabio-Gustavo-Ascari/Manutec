#define AppName "Manutec"
#define AppVersion "0.1.0"
#define AppPublisher "Manutec"
#define AppExeName "Manutec.exe"

[Setup]
AppId={{B4C7DAB6-1F10-4D1A-9FD9-4C4E6AB55B20}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Manutec
DefaultGroupName=Manutec
OutputDir=..\dist\installer
OutputBaseFilename=Manutec-{#AppVersion}-setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
UninstallDisplayName=Manutec
WizardStyle=modern

[Files]
Source: "..\dist\Manutec\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{localappdata}\Manutec\data"
Name: "{localappdata}\Manutec\logs"
Name: "{localappdata}\Manutec\backups"

[Icons]
Name: "{autodesktop}\Manutec"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Manutec"; Filename: "{app}\{#AppExeName}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Executar Manutec"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
