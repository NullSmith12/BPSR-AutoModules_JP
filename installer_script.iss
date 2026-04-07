[Setup]
AppName=BPSR Module Optimizer
AppVersion=1.0
AppPublisher=MrSnake
DefaultDirName={autopf}\BPSR Module Optimizer
DefaultGroupName=BPSR Module Optimizer
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=Output
OutputBaseFilename=BPSR Module Optimizer Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SourceDir=.
UninstallDisplayIcon={app}\BPSR-AutoModules_JP.exe
PrivilegesRequired=admin
DisableProgramGroupPage=yes

[Files]
Source: "dist\gui_app\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "npcap-1.83.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall skipifsourcedoesntexist

[Icons]
Name: "{autoprograms}\BPSR Module Optimizer"; Filename: "{app}\BPSR-AutoModules_JP.exe"; IconFilename: "{app}\icon.ico"
Name: "{autodesktop}\BPSR Module Optimizer"; Filename: "{app}\BPSR-AutoModules_JP.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Run]
Filename: "{tmp}\npcap-1.83.exe"; Parameters: ""; StatusMsg: "Npcap をインストールします。画面の案内に従って進めてください (パケット取得に必須です)..."; Flags: waituntilterminated; Check: NpcapInstallerExists

[Code]
function NpcapInstallerExists: Boolean;
begin
  Result := FileExists(ExpandConstant('{tmp}\npcap-1.83.exe'));
end;
