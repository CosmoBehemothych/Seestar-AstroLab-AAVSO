@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul 2>nul
title Seestar AstroLab AAVSO - SmartScreen Unblock and Publisher Trust

echo ===============================================================================
echo   Seestar AstroLab AAVSO - Устранение предупреждения Windows SmartScreen
echo ===============================================================================
echo.

set "SCRIPT_DIR=%~dp0"

echo [1/3] Удаление метки интернета (Zone.Identifier / Mark-of-the-Web) со всех .exe и .bat...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$paths = @($env:SCRIPT_DIR, (Join-Path $env:USERPROFILE 'Downloads'), (Join-Path $env:LOCALAPPDATA 'Programs\Seestar_AstroLab'), (Join-Path $env:LOCALAPPDATA 'Programs\Seestar AstroLab v1.5.0-alpha')); foreach ($p in $paths) { if ($p -and (Test-Path -LiteralPath $p)) { Get-ChildItem -LiteralPath $p -Filter '*Seestar*' -Recurse -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue } }"
if !ERRORLEVEL! EQU 0 (
    echo   [OK] Поток Zone.Identifier удалён (SmartScreen больше не блокирует запуск).
) else (
    echo   [WARN] Не удалось полностью обработать часть файлов, продолжаем...
)
echo.

echo [2/3] Извлечение и установка сертификата издателя CosmoBehemothych AstroLab...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$dirs = @($env:SCRIPT_DIR, (Join-Path $env:USERPROFILE 'Downloads')); $exe = $null; foreach ($d in $dirs) { if ($d -and (Test-Path -LiteralPath $d)) { $exe = Get-ChildItem -LiteralPath $d -Filter 'Seestar_AstroLab_Setup*.exe' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1; if ($exe) { break } } }; if ($exe) { $sig = Get-AuthenticodeSignature -LiteralPath $exe.FullName; if ($sig -and $sig.SignerCertificate) { $cer = Join-Path $env:TEMP 'CosmoBehemothych_AstroLab.cer'; [IO.File]::WriteAllBytes($cer, $sig.SignerCertificate.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert)); certutil -user -addstore Root $cer | Out-Null; certutil -user -addstore TrustedPublisher $cer | Out-Null; Write-Host '  [OK] Сертификат издателя добавлен в Доверенные корневые центры и Доверенные издатели (CurrentUser).' -ForegroundColor Green } else { Write-Host '  [i] Файл установщика разблокирован от метки Mark-of-the-Web (Unblock-File).' -ForegroundColor Cyan } } else { Write-Host '  [i] Файл Seestar_AstroLab_Setup*.exe не найден в текущей папке или Загрузках.' -ForegroundColor Yellow }"
echo.

echo [3/3] Поиск и запуск установщика Seestar_AstroLab_Setup*.exe в текущей папке...
set "FOUND_SETUP="
for %%F in ("!SCRIPT_DIR!Seestar_AstroLab_Setup*.exe") do (
    if not defined FOUND_SETUP set "FOUND_SETUP=%%~fF"
)

if defined FOUND_SETUP (
    echo   [OK] Запускаю "!FOUND_SETUP!"...
    start "" "!FOUND_SETUP!"
) else (
    echo   Готово! Файлы разблокированы от SmartScreen.
    echo   Для локальной установки v1.5.0-alpha без Git запустите Install_Local_v1.5.0-alpha_1Click.bat.
    pause
)
exit /b 0
