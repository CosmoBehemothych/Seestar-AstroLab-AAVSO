@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul 2>nul
color 0B
title Seestar AstroLab AAVSO v1.5.0-alpha - Local PC Installer (No Git Required)

echo ===============================================================================
echo   Seestar AstroLab AAVSO v1.5.0-alpha - Local PC Installer (No Git Required)
echo ===============================================================================
echo.

set "SCRIPT_DIR=%~dp0"

if not exist "!SCRIPT_DIR!Source_and_Build\desktop_launcher.py" (
    echo [ERROR] Source_and_Build folder not found next to this .bat file!
    echo         Please extract the entire Seestar_AstroLab_v1.5.0-alpha.zip archive first.
    echo         (Папка Source_and_Build не найдена. Сначала полностью распакуйте ZIP-архив!)
    pause
    exit /b 1
)

set "PYTHONUTF8=1"
set "PY_EXE="
set "PY_ARGS=-X utf8"

if exist "%SystemRoot%\py.exe" (
    "%SystemRoot%\py.exe" -3 -c "import sys; assert sys.version_info >= (3, 9)" >nul 2>nul
    if !ERRORLEVEL! EQU 0 (
        set "PY_EXE=%SystemRoot%\py.exe"
        set "PY_ARGS=-3 -X utf8"
    )
)

if not defined PY_EXE (
    for /f "delims=" %%P in ('where python 2^>nul') do (
        if not defined PY_EXE (
            echo "%%~P" | find /i "WindowsApps" >nul
            if !ERRORLEVEL! NEQ 0 (
                if exist "%%~P" (
                    "%%~P" -c "import sys; assert sys.version_info >= (3, 9)" >nul 2>nul
                    if !ERRORLEVEL! EQU 0 set "PY_EXE=%%~P"
                )
            )
        )
    )
)

if not defined PY_EXE (
    for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*" "%ProgramFiles%\Python3*") do (
        if not defined PY_EXE (
            if exist "%%~D\python.exe" (
                "%%~D\python.exe" -c "import sys; assert sys.version_info >= (3, 9)" >nul 2>nul
                if !ERRORLEVEL! EQU 0 set "PY_EXE=%%~D\python.exe"
            )
        )
    )
)

if not defined PY_EXE (
    echo [ERROR] Python 3.9+ not found! Install Python from https://www.python.org/downloads/
    echo         Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [1/4] Python found: "!PY_EXE!"
echo [2/4] Checking dependencies (pywebview, pillow, certifi)...

"!PY_EXE!" !PY_ARGS! -c "import webview, PIL, certifi" >nul 2>nul
if !ERRORLEVEL! NEQ 0 (
    echo       Installing missing Python packages...
    "!PY_EXE!" !PY_ARGS! -m pip install --upgrade pywebview pillow certifi
    if !ERRORLEVEL! NEQ 0 (
        echo       Retrying with --user...
        "!PY_EXE!" !PY_ARGS! -m pip install --user --upgrade pywebview pillow certifi
    )
    "!PY_EXE!" !PY_ARGS! -c "import webview, PIL, certifi" >nul 2>nul
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Failed to import pywebview / pillow / certifi.
        echo         Check your internet connection or Python installation and try again.
        pause
        exit /b 1
    )
)

set "APP_DIR=%LOCALAPPDATA%\Programs\Seestar AstroLab v1.5.0-alpha"
echo [3/4] Copying files to "!APP_DIR!"...
if not exist "!APP_DIR!" mkdir "!APP_DIR!"
xcopy /E /I /Y /Q "!SCRIPT_DIR!Source_and_Build" "!APP_DIR!\Source_and_Build" >nul
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Failed to copy Source_and_Build to "!APP_DIR!".
    pause
    exit /b 1
)

if exist "!SCRIPT_DIR!Converted_Photometry_Storage" (
    if not exist "!APP_DIR!\Converted_Photometry_Storage" (
        xcopy /E /I /Y /Q "!SCRIPT_DIR!Converted_Photometry_Storage" "!APP_DIR!\Converted_Photometry_Storage" >nul
    )
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Test-Path -LiteralPath $env:APP_DIR) { Get-ChildItem -LiteralPath $env:APP_DIR -Recurse -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue }" >nul 2>nul

if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    echo [OPT] Inno Setup 6 detected.
    set "BUILD_EXE_CHOICE="
    set /p "BUILD_EXE_CHOICE=Build Setup .exe via PyInstaller + Inno Setup? [y/N]: "
    if /i "!BUILD_EXE_CHOICE!"=="y" (
        "!PY_EXE!" !PY_ARGS! -m pip install --quiet pyinstaller
        pushd "!APP_DIR!\Source_and_Build"
        "!PY_EXE!" !PY_ARGS! -m PyInstaller --noconfirm --clean --onefile --console --noupx --name "Seestar AstroLab" --version-file version_info.txt --collect-all webview --collect-all pythonnet --collect-all clr_loader --collect-all certifi --hidden-import webview.platforms.edgechromium --add-data "pwa_mobile_and_electron;pwa_mobile_and_electron" --add-data "backend;backend" --add-data "Converted_Photometry_Storage;Converted_Photometry_Storage" --icon "assets/Seestar_AstroLab.ico" desktop_launcher.py
        "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" ".\Seestar_AstroLab_Installer.iss"
        popd
        if exist "!APP_DIR!\Source_and_Build\dist_installer\Seestar_AstroLab_Setup_v1.5.0-alpha.exe" (
            echo [OK] Launching Seestar_AstroLab_Setup_v1.5.0-alpha.exe...
            start "" "!APP_DIR!\Source_and_Build\dist_installer\Seestar_AstroLab_Setup_v1.5.0-alpha.exe"
            exit /b 0
        )
    )
)

set "GUI_PY_EXE=!PY_EXE!"
set "GUI_PY_ARGS=!PY_ARGS!"
if /i "!PY_EXE!"=="%SystemRoot%\py.exe" (
    if exist "%SystemRoot%\pyw.exe" (
        set "GUI_PY_EXE=%SystemRoot%\pyw.exe"
    )
) else (
    for %%F in ("!PY_EXE!") do (
        if exist "%%~dpFpythonw.exe" (
            set "GUI_PY_EXE=%%~dpFpythonw.exe"
        )
    )
)

echo [4/4] Creating Desktop shortcut and launching v1.5.0-alpha...
set "SL_LNK_NAME=Seestar AstroLab v1.5.0-alpha.lnk"
set "SL_TARGET=!GUI_PY_EXE!"
set "SL_ARGS=!GUI_PY_ARGS! ""!APP_DIR!\Source_and_Build\desktop_launcher.py"""
set "SL_WORKDIR=!APP_DIR!\Source_and_Build"
set "SL_ICON=!APP_DIR!\Source_and_Build\assets\Seestar_AstroLab.ico"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $lnk = Join-Path ([Environment]::GetFolderPath('Desktop')) $env:SL_LNK_NAME; $s = $ws.CreateShortcut($lnk); $s.TargetPath = $env:SL_TARGET; $s.Arguments = $env:SL_ARGS; $s.WorkingDirectory = $env:SL_WORKDIR; if (Test-Path -LiteralPath $env:SL_ICON) { $s.IconLocation = $env:SL_ICON }; $s.Save()"
if !ERRORLEVEL! NEQ 0 (
    echo [WARN] Could not create Desktop shortcut automatically, continuing launch...
)

echo.
echo [OK] Seestar AstroLab v1.5.0-alpha installed! Launching application...
start "Seestar AstroLab v1.5.0-alpha" "!GUI_PY_EXE!" !GUI_PY_ARGS! "!APP_DIR!\Source_and_Build\desktop_launcher.py"
exit /b 0
