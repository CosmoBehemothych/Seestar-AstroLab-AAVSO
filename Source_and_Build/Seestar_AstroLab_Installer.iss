; =============================================================================
; [RU] Скрипт сборки автономного установщика Seestar AstroLab AAVSO (Inno Setup 6)
; [EN] Standalone installer build script for Seestar AstroLab AAVSO (Inno Setup 6)
; =============================================================================
#define MyAppName "Seestar AstroLab AAVSO"
#define MyAppFullTitle "Seestar AstroLab AAVSO — Радар целей и фотометрия"
#define MyAppVersion "1.1.1 beta"
#define MyAppPublisher "CosmoBehemothych AstroLab"
#define MyAppURL "https://boosty.to/cosmobehemothych"
#define MyAppRepoURL "https://github.com/CosmoBehemothych/Seestar-AstroLab-AAVSO"
#define MyAppExeName "Seestar AstroLab.exe"
#define MyAppIconRelPath "assets\Seestar_AstroLab.ico"
#define MyAppHeaderBmpRelPath "assets\installer_header_fullwidth.bmp"
#define MyAppId "SeestarAstroLab_is1"
#define MySourceDir RemoveBackslashUnlessRoot(SourcePath)

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={cm:AppFullTitle}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppRepoURL}
AppUpdatesURL={#MyAppRepoURL}

; [RU] Привязка рабочей директории компилятора к папке самого .iss скрипта (Source_and_Build)
; [EN] Anchor compiler base directory to the folder containing this .iss script (Source_and_Build)
SourceDir={#MySourceDir}

PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={localappdata}\Programs\Seestar_AstroLab
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=no

ShowLanguageDialog=yes
UsePreviousLanguage=no
UsePreviousAppDir=yes
UsePreviousGroup=yes
CloseApplications=force
RestartApplications=no

WizardStyle=modern
#if FileExists(AddBackslash(SourcePath) + MyAppHeaderBmpRelPath)
WizardSmallImageFile={#MyAppHeaderBmpRelPath}
WizardImageStretch=no
WizardImageAlphaFormat=defined
#endif
#if FileExists(AddBackslash(SourcePath) + MyAppIconRelPath)
SetupIconFile={#MyAppIconRelPath}
UninstallDisplayIcon={app}\{#MyAppIconRelPath}
#else
UninstallDisplayIcon={app}\{#MyAppExeName}
#endif
UninstallDisplayName={cm:AppFullTitle}

Compression=lzma2/fast
SolidCompression=no
OutputDir=dist_installer
OutputBaseFilename=Seestar_AstroLab_Setup

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "german";  MessagesFile: "compiler:Languages\German.isl"
Name: "french";  MessagesFile: "compiler:Languages\French.isl"
Name: "chinese"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
russian.AppFullTitle=Seestar AstroLab AAVSO — Радар целей и фотометрия
russian.LaunchProgram=Запустить Seestar AstroLab AAVSO после завершения установки
russian.OpenBoosty=Поддержать проект на Boosty (CosmoBehemothych)
russian.CreateDesktopIcon=Создать ярлык на Рабочем столе
russian.CleanOldInstall=Обнаружена предыдущая версия программы. Выполняется чистая установка с сохранением пользовательских данных...

english.AppFullTitle=Seestar AstroLab AAVSO — Target Radar & Photometry
english.LaunchProgram=Launch Seestar AstroLab AAVSO after installation finishes
english.OpenBoosty=Support the project on Boosty (CosmoBehemothych)
english.CreateDesktopIcon=Create a Desktop shortcut
english.CleanOldInstall=Previous version detected. Performing clean upgrade while preserving user data...

spanish.AppFullTitle=Seestar AstroLab AAVSO — Radar de Objetivos y Fotometría
spanish.LaunchProgram=Iniciar Seestar AstroLab AAVSO al finalizar la instalación
spanish.OpenBoosty=Apoyar el proyecto en Boosty (CosmoBehemothych)
spanish.CreateDesktopIcon=Crear un acceso directo en el Escritorio
spanish.CleanOldInstall=Versión anterior detectada. Actualizando limpiamente conservando sus datos...

german.AppFullTitle=Seestar AstroLab AAVSO — Ziel-Radar & Photometrie
german.LaunchProgram=Seestar AstroLab AAVSO nach der Installation starten
german.OpenBoosty=Projekt auf Boosty unterstützen (CosmoBehemothych)
german.CreateDesktopIcon=Desktop-Verknüpfung erstellen
german.CleanOldInstall=Vorherige Version erkannt. Sauberes Update unter Beibehaltung der Benutzerdaten...

french.AppFullTitle=Seestar AstroLab AAVSO — Radar de Cibles & Photométrie
french.LaunchProgram=Lancer Seestar AstroLab AAVSO après l'installation
french.OpenBoosty=Soutenir le projet sur Boosty (CosmoBehemothych)
french.CreateDesktopIcon=Créer un raccourci sur le Bureau
french.CleanOldInstall=Version précédente détectée. Mise à jour propre avec conservation des données...

chinese.AppFullTitle=Seestar AstroLab AAVSO — 变星目标雷达与测光工作站
chinese.LaunchProgram=安装完成后立即启动 Seestar AstroLab AAVSO
chinese.OpenBoosty=在 Boosty 上支持开发者 (CosmoBehemothych)
chinese.CreateDesktopIcon=创建桌面快捷方式
chinese.CleanOldInstall=检测到旧版本，正在保留用户数据并执行全新升级...

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}\pwa_mobile_and_electron"
Type: filesandordirs; Name: "{app}\backend"
Type: filesandordirs; Name: "{app}\desktop_pc"
Type: files; Name: "{app}\{#MyAppExeName}"
Type: files; Name: "{app}\desktop_launcher.py"

[Dirs]
Name: "{app}\Converted_Photometry_Storage"

[Files]
Source: "dist\Seestar AstroLab\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
#if FileExists(AddBackslash(SourcePath) + MyAppIconRelPath)
Source: "{#MyAppIconRelPath}"; DestDir: "{app}\assets"; Flags: ignoreversion
#endif
#if FileExists(AddBackslash(SourcePath) + "pwa_mobile_and_electron\index.html")
Source: "pwa_mobile_and_electron\*"; DestDir: "{app}\pwa_mobile_and_electron"; Flags: ignoreversion recursesubdirs createallsubdirs
#endif
#if FileExists(AddBackslash(SourcePath) + "backend\astrolab_backend_core.py")
Source: "backend\*"; DestDir: "{app}\backend"; Flags: ignoreversion recursesubdirs createallsubdirs
#endif
#if FileExists(AddBackslash(SourcePath) + "desktop_pc\seestar_aavso_desktop_pc.py")
Source: "desktop_pc\*"; DestDir: "{app}\desktop_pc"; Flags: ignoreversion recursesubdirs createallsubdirs
#endif
#if FileExists(AddBackslash(SourcePath) + "..\Converted_Photometry_Storage\README_STORAGE.txt")
Source: "..\Converted_Photometry_Storage\README_STORAGE.txt"; DestDir: "{app}\Converted_Photometry_Storage"; Flags: ignoreversion
#endif
#if FileExists(AddBackslash(SourcePath) + "..\Converted_Photometry_Storage\user_converted_photometry_db.json")
Source: "..\Converted_Photometry_Storage\user_converted_photometry_db.json"; DestDir: "{app}\Converted_Photometry_Storage"; Flags: onlyifdoesntexist uninsneveruninstall
#endif

[Icons]
#if FileExists(AddBackslash(SourcePath) + MyAppIconRelPath)
Name: "{group}\{cm:AppFullTitle}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppIconRelPath}"
Name: "{autodesktop}\{cm:AppFullTitle}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppIconRelPath}"; Tasks: desktopicon
#else
Name: "{group}\{cm:AppFullTitle}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{cm:AppFullTitle}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon
#endif
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent
Filename: "{#MyAppURL}"; Description: "{cm:OpenBoosty}"; Flags: shellexec runasoriginaluser postinstall skipifsilent unchecked

[UninstallDelete]
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}\pwa_mobile_and_electron"
Type: filesandordirs; Name: "{app}\backend"
Type: filesandordirs; Name: "{app}\desktop_pc"

[Code]
procedure InitializeWizard();
begin
  WizardForm.Color := $0020120B;
  WizardForm.MainPanel.Color := $0020120B;
  WizardForm.PageNameLabel.Font.Color := $00F8FAFC;
  WizardForm.PageNameLabel.Font.Style := [fsBold];
  WizardForm.PageDescriptionLabel.Font.Color := $00CBD5E1;
  WizardForm.WizardSmallBitmapImage.Left := 0;
  WizardForm.WizardSmallBitmapImage.Top := 0;
  WizardForm.WizardSmallBitmapImage.Width := WizardForm.MainPanel.Width;
  WizardForm.WizardSmallBitmapImage.Height := WizardForm.MainPanel.Height;
  WizardForm.PageNameLabel.Width := WizardForm.MainPanel.Width - ScaleX(180);
  WizardForm.PageDescriptionLabel.Width := WizardForm.MainPanel.Width - ScaleX(180);
end;
; Build-Timestamp: 2026-11-17 12:35:58 UTC
