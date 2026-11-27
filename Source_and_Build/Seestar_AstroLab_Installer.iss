; ============================================================================
; [RU] Скрипт сборки автономного установщика Seestar AstroLab AAVSO (Inno Setup 6)
; [EN] Standalone installer build script for Seestar AstroLab AAVSO (Inno Setup 6)
; ============================================================================
#define MyAppName "Seestar AstroLab AAVSO"
#define MyAppFullTitle "Seestar AstroLab AAVSO — Радар целей и фотометрия"
#define MyAppVersion "1.5.0"
#define MyAppNumericVersion "1.5.0.0"
#define MyAppPublisher "CosmoBehemothych AstroLab"
#define MyAppCopyright "Copyright (C) 2026 CosmoBehemothych. MIT License."
#define MyAppRepoURL "https://github.com/CosmoBehemothych/Seestar-AstroLab-AAVSO"
#define MyAppExeName "Seestar AstroLab.exe"
#define MyAppIconRelPath "assets\Seestar_AstroLab.ico"
#define MyAppHeaderBmpRelPath "assets\installer_header_fullwidth.bmp"
#define MyAppId "SeestarAstroLab_is1"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={cm:AppFullTitle}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppRepoURL}
AppSupportURL={#MyAppRepoURL}
AppUpdatesURL={#MyAppRepoURL}
AppCopyright={#MyAppCopyright}

VersionInfoVersion={#MyAppNumericVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Standalone Windows Installer (AAVSO Photometry & Target Radar)
VersionInfoTextVersion={#MyAppVersion}
VersionInfoCopyright={#MyAppCopyright}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppNumericVersion}
VersionInfoProductTextVersion={#MyAppVersion}
VersionInfoOriginalFilename=Seestar_AstroLab_Setup.exe

LicenseFile=..\LICENSE

PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={localappdata}\Programs\Seestar_AstroLab
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=no

ShowLanguageDialog=yes

LanguageDetectionMethod=none
UsePreviousLanguage=no
UsePreviousAppDir=yes
UsePreviousGroup=yes
CloseApplications=force
RestartApplications=no

WizardStyle=modern
#if FileExists(AddBackslash(SourcePath) + MyAppHeaderBmpRelPath)
WizardSmallImageFile={#MyAppHeaderBmpRelPath}
WizardImageStretch=yes
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
OutputBaseFilename=Seestar_AstroLab_Setup_v{#MyAppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "german";  MessagesFile: "compiler:Languages\German.isl"
Name: "french";  MessagesFile: "compiler:Languages\French.isl"
Name: "chinese"; MessagesFile: "compiler:Default.isl"
Name: "czech";   MessagesFile: "compiler:Languages\Czech.isl"

[LangOptions]
; [FIX ПУНКТ 1] Уникальные LanguageName и LanguageID для каждого из 6 языков,
; чтобы chinese (использующий базовый Default.isl) НЕ перезаписывал English ($0409)!
english.LanguageName=English
english.LanguageID=$0409
russian.LanguageName=Русский
russian.LanguageID=$0419
spanish.LanguageName=Español
spanish.LanguageID=$0C0A
german.LanguageName=Deutsch
german.LanguageID=$0407
french.LanguageName=Français
french.LanguageID=$040C
chinese.LanguageName=<7B80><4F53><4E2D><6587> (Chinese Simplified)
chinese.LanguageID=$0804
czech.LanguageName=Čeština
czech.LanguageID=$0405

[Messages]
; Явная локализация системных заголовков задач и кнопок для всех 6 языков
english.AdditionalIcons=Additional shortcuts:
english.CreateDesktopIcon=Create a &desktop shortcut
russian.AdditionalIcons=Дополнительные ярлыки:
russian.CreateDesktopIcon=Создать ярлык на &Рабочем столе
czech.AdditionalIcons=Další zástupci:
czech.CreateDesktopIcon=Vytvořit zástupce na &ploše
spanish.AdditionalIcons=Iconos adicionales:
spanish.CreateDesktopIcon=Crear un icono en el &Escritorio
german.AdditionalIcons=Zusätzliche Symbole:
german.CreateDesktopIcon=&Desktop-Symbol erstellen
french.AdditionalIcons=Icônes supplémentaires :
french.CreateDesktopIcon=Créer une icône sur le &Bureau
chinese.AdditionalIcons=附加快捷方式：
chinese.CreateDesktopIcon=创建桌面快捷方式(&D)
chinese.SelectTasksDesc=您想要执行哪些附加任务？
chinese.SelectTasksLabel2=选择安装 [%1] 时想要执行的附加任务，然后点击“下一步”。
chinese.FinishedHeadingLabel=[name] 安装完成
chinese.FinishedLabelNoIcons=已在您的电脑上完成安装 [name]。
chinese.FinishedLabel=已在您的电脑上完成安装 [name]。可以通过选择安装的图标来运行应用程序。
chinese.ClickFinish=点击“完成”退出安装程序。

[CustomMessages]
english.AppFullTitle=Seestar AstroLab AAVSO — Target Radar & Photometry
english.LaunchProgram=Launch Seestar AstroLab AAVSO after installation finishes
english.CreateDesktopIcon=Create a Desktop shortcut
english.AdditionalIconsGroup=Additional shortcuts:
english.CleanOldInstall=Previous version detected. Performing clean upgrade while preserving user data...

russian.AppFullTitle=Seestar AstroLab AAVSO — Радар целей и фотометрия
russian.LaunchProgram=Запустить Seestar AstroLab AAVSO после завершения установки
russian.CreateDesktopIcon=Создать ярлык на Рабочем столе
russian.AdditionalIconsGroup=Дополнительные ярлыки:
russian.CleanOldInstall=Обнаружена предыдущая версия программы. Выполняется чистая установка с сохранением пользовательских данных...

spanish.AppFullTitle=Seestar AstroLab AAVSO — Radar de Objetivos y Fotometría
spanish.LaunchProgram=Iniciar Seestar AstroLab AAVSO al finalizar la instalación
spanish.CreateDesktopIcon=Crear un acceso directo en el Escritorio
spanish.AdditionalIconsGroup=Iconos adicionales:
spanish.CleanOldInstall=Versión anterior detectada. Actualizando limpiamente conservando sus datos...

german.AppFullTitle=Seestar AstroLab AAVSO — Ziel-Radar & Photometrie
german.LaunchProgram=Seestar AstroLab AAVSO nach der Installation starten
german.CreateDesktopIcon=Desktop-Verknüpfung erstellen
german.AdditionalIconsGroup=Zusätzliche Symbole:
german.CleanOldInstall=Vorherige Version erkannt. Sauberes Update unter Beibehaltung der Benutzerdaten...

french.AppFullTitle=Seestar AstroLab AAVSO — Radar de Cibles & Photométrie
french.LaunchProgram=Lancer Seestar AstroLab AAVSO après l'installation
french.CreateDesktopIcon=Créer un raccourci sur le Bureau
french.AdditionalIconsGroup=Icônes supplémentaires :
french.CleanOldInstall=Version précédente détectée. Mise à jour propre avec conservation des données...

chinese.AppFullTitle=Seestar AstroLab AAVSO — 变星目标雷达与测光工作站
chinese.LaunchProgram=安装完成后立即启动 Seestar AstroLab AAVSO
chinese.CreateDesktopIcon=创建桌面快捷方式
chinese.AdditionalIconsGroup=附加快捷方式：
chinese.CleanOldInstall=检测到旧版本，正在保留用户数据并执行全新升级...

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIconsGroup}"

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
Source: "dist\Seestar AstroLab.exe"; DestDir: "{app}"; Flags: ignoreversion
#if FileExists(AddBackslash(SourcePath) + MyAppIconRelPath)
Source: "{#MyAppIconRelPath}"; DestDir: "{app}\assets"; Flags: ignoreversion
#endif
#if FileExists(AddBackslash(SourcePath) + "pwa_mobile_and_electron\index.html")
Source: "pwa_mobile_and_electron\*"; DestDir: "{app}\pwa_mobile_and_electron"; Flags: ignoreversion recursesubdirs createallsubdirs
#endif
#if FileExists(AddBackslash(SourcePath) + "backend\astrolab_backend_core.py")
Source: "backend\*"; DestDir: "{app}\backend"; Flags: ignoreversion recursesubdirs createallsubdirs
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

[UninstallDelete]
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}\pwa_mobile_and_electron"
Type: filesandordirs; Name: "{app}\backend"
Type: filesandordirs; Name: "{app}\desktop_pc"

[Code]
procedure HideBannerOverlayLabels();
begin
  { [FIX ПУНКТ 2] Полностью скрываем системные текстовые плашки поверх верхнего баннера
    на всех шагах мастера установки и на всех 6 языках локализации }
  WizardForm.PageNameLabel.Visible := False;
  WizardForm.PageDescriptionLabel.Visible := False;
  WizardForm.PageNameLabel.Caption := '';
  WizardForm.PageDescriptionLabel.Caption := '';
  WizardForm.PageNameLabel.Width := 0;
  WizardForm.PageDescriptionLabel.Width := 0;
  WizardForm.PageNameLabel.Top := -5000;
  WizardForm.PageDescriptionLabel.Top := -5000;
end;

procedure InitializeWizard();
begin
  WizardForm.Color := $0020120B;
  WizardForm.MainPanel.Color := $0020120B;
  WizardForm.WizardSmallBitmapImage.Left := 0;
  WizardForm.WizardSmallBitmapImage.Top := 0;
  WizardForm.WizardSmallBitmapImage.Width := WizardForm.MainPanel.Width;
  WizardForm.WizardSmallBitmapImage.Height := WizardForm.MainPanel.Height;
  HideBannerOverlayLabels();
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  HideBannerOverlayLabels();
end;

function GetAppLangCodeFromSetup(): String;
var
  L: String;
begin
  L := Lowercase(ActiveLanguage);
  if L = 'russian' then Result := 'ru'
  else if L = 'spanish' then Result := 'es'
  else if L = 'german' then Result := 'de'
  else if L = 'french' then Result := 'fr'
  else if L = 'chinese' then Result := 'zh'
  else if L = 'czech' then Result := 'cs'
  else Result := 'en';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  LangCode, JsonContent, JsContent, AppDataDir, StorePath: String;
begin
  if CurStep = ssPostInstall then
  begin
    { Язык, выбранный пользователем на этапе установки, применяется при первом запуске приложения }
    LangCode := GetAppLangCodeFromSetup();
    AppDataDir := ExpandConstant('{userappdata}\Seestar_AstroLab');
    ForceDirectories(AppDataDir);
    StorePath := AppDataDir + '\user_persistent_store.json';

    if not FileExists(StorePath) then
    begin
      JsonContent := '{"lang": "' + LangCode + '", "seestar_lang": "' + LangCode + '", "installer_lang": "' + LangCode + '"}';
      SaveStringToFile(ExpandConstant('{app}\user_settings.json'), JsonContent, False);
      SaveStringToFile(AppDataDir + '\installer_lang.txt', LangCode, False);
      SaveStringToFile(AppDataDir + '\user_settings.json', JsonContent, False);

      if DirExists(ExpandConstant('{app}\pwa_mobile_and_electron')) then
      begin
        JsContent := 'window.__SEESTAR_DISK_STORE__ = {"lang": "' + LangCode + '", "seestar_lang": "' + LangCode + '", "installer_lang": "' + LangCode + '"};' + #13#10;
        SaveStringToFile(ExpandConstant('{app}\pwa_mobile_and_electron\user_persistent_store.js'), JsContent, False);
      end;
    end;
  end;
end;
