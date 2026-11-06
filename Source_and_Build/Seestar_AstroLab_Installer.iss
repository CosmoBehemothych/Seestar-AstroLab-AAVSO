#define MyAppName "Seestar AstroLab AAVSO"
#define MyAppFullTitle "Seestar AstroLab AAVSO — Радар целей и фотометрия"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "CosmoBehemothych AstroLab"
#define MyAppURL "https://boosty.to/cosmobehemothych"
#define MyAppRepoURL "https://github.com/CosmoBehemothych/Seestar-AstroLab-AAVSO"
#define MyAppExeName "Seestar AstroLab.exe"
#define MyAppIconRelPath "assets\Seestar_AstroLab.ico"
#define MyAppId "SeestarAstroLab_is1"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={cm:AppFullTitle}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppRepoURL}
AppUpdatesURL={#MyAppRepoURL}

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
WizardSmallImageFile=assets\installer_header_fullwidth.bmp
WizardImageStretch=no
WizardImageAlphaFormat=defined
SetupIconFile={#MyAppIconRelPath}
UninstallDisplayIcon={app}\{#MyAppIconRelPath}
UninstallDisplayName={cm:AppFullTitle}

Compression=lzma2/fast
SolidCompression=no
OutputDir=dist_installer
OutputBaseFilename=Seestar_AstroLab_Setup

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[CustomMessages]
; 1. Русский (ru-RU)
russian.AppFullTitle=Seestar AstroLab AAVSO — Радар целей и фотометрия v{#MyAppVersion} (Первая версия)
russian.AppSubtitle=Радар срочных целей AAVSO и конвертер фотометрии Seestar S30 / S30PRO / S50 / S50PRO
russian.CreateStartMenuFolder=Создать папку с фирменной иконкой в меню «Пуск» (Seestar AstroLab AAVSO)
russian.WebUIShortcutComment=Открыть веб-интерфейс Seestar AstroLab AAVSO
russian.UninstallShortcutName=Удалить Seestar AstroLab AAVSO
russian.UninstallShortcutComment=Удалить Seestar AstroLab AAVSO с компьютера

; 2. English (en-US)
english.AppFullTitle=Seestar AstroLab AAVSO — Target Radar & Photometry v{#MyAppVersion} (First Release)
english.AppSubtitle=AAVSO Urgent Target Radar & Seestar S30 / S30PRO / S50 / S50PRO Photometry Converter
english.CreateStartMenuFolder=Create Start Menu folder with custom icon (Seestar AstroLab AAVSO)
english.WebUIShortcutComment=Open Seestar AstroLab AAVSO Web Interface
english.UninstallShortcutName=Uninstall Seestar AstroLab AAVSO
english.UninstallShortcutComment=Uninstall Seestar AstroLab AAVSO from your computer

; 3. Español (es-ES)
spanish.AppFullTitle=Seestar AstroLab AAVSO — Radar de Objetivos y Fotometría v{#MyAppVersion} (Primera versión)
spanish.AppSubtitle=Radar de alertas AAVSO y convertidor fotométrico Seestar S30 / S30PRO / S50 / S50PRO
spanish.CreateStartMenuFolder=Crear carpeta con icono en el Menú Inicio (Seestar AstroLab AAVSO)
spanish.WebUIShortcutComment=Abrir interfaz web de Seestar AstroLab AAVSO
spanish.UninstallShortcutName=Desinstalar Seestar AstroLab AAVSO
spanish.UninstallShortcutComment=Desinstalar Seestar AstroLab AAVSO del equipo

; 4. Deutsch (de-DE)
german.AppFullTitle=Seestar AstroLab AAVSO — Zielradar & Photometrie v{#MyAppVersion} (Erste Version)
german.AppSubtitle=AAVSO-Zielradar & Seestar S30 / S30PRO / S50 / S50PRO Photometrie-Konverter
german.CreateStartMenuFolder=Startmenü-Ordner mit App-Symbol erstellen (Seestar AstroLab AAVSO)
german.WebUIShortcutComment=Seestar AstroLab AAVSO Web-Oberfläche öffnen
german.UninstallShortcutName=Seestar AstroLab AAVSO deinstallieren
german.UninstallShortcutComment=Seestar AstroLab AAVSO vollständig vom Computer entfernen

; 5. Français (fr-FR)
french.AppFullTitle=Seestar AstroLab AAVSO — Radar de Cibles & Photométrie v{#MyAppVersion} (Première version)
french.AppSubtitle=Radar d'alertes AAVSO et convertisseur photométrique Seestar S30 / S30PRO / S50 / S50PRO
french.CreateStartMenuFolder=Créer un dossier avec icône dans le menu Démarrer (Seestar AstroLab AAVSO)
french.WebUIShortcutComment=Ouvrir l'interface Web Seestar AstroLab AAVSO
french.UninstallShortcutName=Désinstaller Seestar AstroLab AAVSO
french.UninstallShortcutComment=Désinstaller complètement Seestar AstroLab AAVSO de l'ordinateur

; 6. 中文 (zh-CN)
chinesesimplified.AppFullTitle=Seestar AstroLab AAVSO — 变星目标雷达与测光套件 v{#MyAppVersion} (第一版)
chinesesimplified.AppSubtitle=AAVSO 紧急目标雷达与 Seestar S30 / S30PRO / S50 / S50PRO 测光转换器
chinesesimplified.CreateStartMenuFolder=在「开始」菜单创建带应用图标的文件夹 (Seestar AstroLab AAVSO)
chinesesimplified.WebUIShortcutComment=打开 Seestar AstroLab AAVSO 网页界面
chinesesimplified.UninstallShortcutName=卸载 Seestar AstroLab AAVSO
chinesesimplified.UninstallShortcutComment=从计算机完全卸载 Seestar AstroLab AAVSO

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startmenuicon"; Description: "{cm:CreateStartMenuFolder}"; GroupDescription: "{cm:AdditionalIcons}"

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
Filename: "{userprograms}\{#MyAppName}\desktop.ini"; Section: ".ShellClassInfo"; Key: "InfoTip"; String: "{cm:AppFullTitle}"

[Icons]
Name: "{userprograms}\{#MyAppName}\Seestar AstroLab AAVSO"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppIconRelPath}"; AppUserModelID: "CosmoBehemothych.SeestarAstroLab.Desktop.1.0"; Comment: "{cm:AppFullTitle}"
Name: "{userprograms}\{#MyAppName}\Seestar AstroLab AAVSO Web"; Filename: "{app}\pwa_mobile_and_electron\index.html"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppIconRelPath}"; Comment: "{cm:WebUIShortcutComment}"
Name: "{userprograms}\{#MyAppName}\{cm:UninstallShortcutName}"; Filename: "{uninstallexe}"; Parameters: "--uninstall"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppIconRelPath}"; Comment: "{cm:UninstallShortcutComment}"
Name: "{userdesktop}\Seestar AstroLab AAVSO"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppIconRelPath}"; AppUserModelID: "CosmoBehemothych.SeestarAstroLab.Desktop.1.0"; Tasks: desktopicon; Comment: "{cm:AppFullTitle}"

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
