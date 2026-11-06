#define MyAppName "Seestar AstroLab AAVSO"
#define MyAppFullTitle "Seestar AstroLab AAVSO — Радар целей и фотометрия"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "CosmoBehemothych AstroLab"
#define MyAppURL "https://boosty.to/cosmobehemothych"
#define MyAppExeName "Seestar AstroLab.exe"
#define MyAppIconRelPath "assets\Seestar_AstroLab.ico"
#define MyAppId "SeestarAstroLab_is1"

[Setup]
AppId={#MyAppId}
AppName={#MyAppFullTitle}
AppVersion={#MyAppVersion}
AppVerName={#MyAppFullTitle} v{#MyAppVersion} (Первая версия)
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={userpf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=no

UsePreviousAppDir=yes
UsePreviousGroup=yes
CloseApplications=force
RestartApplications=no

WizardStyle=modern
WizardSmallImageFile=assets\installer_header_fullwidth.bmp
WizardImageStretch=no
WizardImageAlphaFormat=defined
SetupIconFile={#MyAppIconRelPath}
UninstallDisplayIcon={app}\{#MyAppIconRelPath}
UninstallDisplayName={#MyAppFullTitle} v{#MyAppVersion} (Первая версия)

Compression=lzma2/fast
SolidCompression=no
OutputDir=dist_installer
OutputBaseFilename=Seestar_AstroLab_Setup

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[InstallDelete]
Type: files; Name: "{userprograms}\{#MyAppName}\desktop.ini"
Type: files; Name: "{userprograms}\{#MyAppName}\Документация Seestar AstroLab.lnk"
Type: files; Name: "{userprograms}\{#MyAppName}\Seestar AstroLab Documentation.lnk"

[Files]
Source: "dist\Seestar AstroLab\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\Seestar_AstroLab.ico"; DestDir: "{app}\assets"; Flags: ignoreversion
Source: "pwa_mobile_and_electron\*"; DestDir: "{app}\pwa_mobile_and_electron"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "desktop_pc\*"; DestDir: "{app}\desktop_pc"; Flags: ignoreversion recursesubdirs createallsubdirs

[INI]
Filename: "{userprograms}\{#MyAppName}\desktop.ini"; Section: ".ShellClassInfo"; Key: "IconResource"; String: "{app}\{#MyAppIconRelPath},0"
Filename: "{userprograms}\{#MyAppName}\desktop.ini"; Section: ".ShellClassInfo"; Key: "IconFile"; String: "{app}\{#MyAppIconRelPath}"
Filename: "{userprograms}\{#MyAppName}\desktop.ini"; Section: ".ShellClassInfo"; Key: "IconIndex"; String: "0"
Filename: "{userprograms}\{#MyAppName}\desktop.ini"; Section: ".ShellClassInfo"; Key: "InfoTip"; String: "{#MyAppFullTitle} (v{#MyAppVersion} — Первая версия)"

[Icons]
; Пункт 1: Все 3 ярлыка в папке меню «Пуск» (включая ярлык удаления приложения!)
Name: "{userprograms}\{#MyAppName}\Seestar AstroLab AAVSO"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppIconRelPath}"; AppUserModelID: "CosmoBehemothych.SeestarAstroLab.Desktop.1.0"; Comment: "{#MyAppFullTitle} v{#MyAppVersion} (Первая версия)"
Name: "{userprograms}\{#MyAppName}\Seestar AstroLab AAVSO Web"; Filename: "{app}\pwa_mobile_and_electron\index.html"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppIconRelPath}"; Comment: "Seestar AstroLab Web UI"
Name: "{userprograms}\{#MyAppName}\Удалить Seestar AstroLab AAVSO"; Filename: "{uninstallexe}"; Parameters: "--uninstall"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppIconRelPath}"; Comment: "Удалить {#MyAppName}"
Name: "{userdesktop}\Seestar AstroLab AAVSO"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppIconRelPath}"; AppUserModelID: "CosmoBehemothych.SeestarAstroLab.Desktop.1.0"; Tasks: desktopicon; Comment: "{#MyAppFullTitle} v{#MyAppVersion} (Первая версия)"

[Code]
procedure InitializeWizard();
begin
  WizardForm.MainPanel.Height := 160;
  WizardForm.WizardSmallBitmapImage.Left := 0;
  WizardForm.WizardSmallBitmapImage.Top := 0;
  WizardForm.WizardSmallBitmapImage.Width := WizardForm.MainPanel.Width;
  WizardForm.WizardSmallBitmapImage.Height := WizardForm.MainPanel.Height;
  WizardForm.WizardSmallBitmapImage.Stretch := True;
  WizardForm.PageNameLabel.Visible := False;
  WizardForm.PageDescriptionLabel.Visible := False;
end;

[Run]
Filename: "attrib.exe"; Parameters: "+s ""{userprograms}\{#MyAppName}"""; Flags: runhidden nowait
Filename: "attrib.exe"; Parameters: "+h +s ""{userprograms}\{#MyAppName}\desktop.ini"""; Flags: runhidden nowait
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
