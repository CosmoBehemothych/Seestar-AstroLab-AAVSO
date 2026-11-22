@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>nul
title Seestar AstroLab AAVSO — Снятие блокировки SmartScreen и доверие издателю

echo ===============================================================================
echo   Seestar AstroLab AAVSO — Устранение предупреждения Windows SmartScreen
echo ===============================================================================
echo.
echo [1/3] Удаление метки интернета (Zone.Identifier / Mark-of-the-Web) со всех .exe...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$paths = @('%~dp0', "$env:USERPROFILE\Downloads", "$env:LOCALAPPDATA\Programs\Seestar_AstroLab"); " ^
  "foreach ($p in $paths) { if (Test-Path $p) { Get-ChildItem -Path $p -Filter '*Seestar*' -Recurse -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue } }"
echo   [OK] Поток Zone.Identifier удалён (SmartScreen больше не блокирует запуск).
echo.

echo [2/3] Извлечение и установка сертификата издателя CosmoBehemothych AstroLab...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$exe = Get-ChildItem -Path @('%~dp0', "$env:USERPROFILE\Downloads") -Filter 'Seestar_AstroLab_Setup*.exe' -ErrorAction SilentlyContinue | Select-Object -First 1; " ^
  "if ($exe) { " ^
  "  $sig = Get-AuthenticodeSignature -FilePath $exe.FullName; " ^
  "  if ($sig -and $sig.SignerCertificate) { " ^
  "    $cer = Join-Path $env:TEMP 'CosmoBehemothych_AstroLab.cer'; " ^
  "    [IO.File]::WriteAllBytes($cer, $sig.SignerCertificate.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert)); " ^
  "    certutil -user -addstore Root $cer | Out-Null; " ^
  "    certutil -user -addstore TrustedPublisher $cer | Out-Null; " ^
  "    Write-Host '  [OK] Сертификат издателя добавлен в Доверенные корневые центры и Доверенные издатели (CurrentUser).' -ForegroundColor Green " ^
  "  } else { Write-Host '  [i] Файл установщика разблокирован от метки Mark-of-the-Web (Unblock-File).' -ForegroundColor Cyan } " ^
  "}"
echo.

echo [3/3] Запуск установщика Seestar_AstroLab_Setup.exe (если находится в этой папке)...
if exist "%~dp0Seestar_AstroLab_Setup.exe" (
    start "" "%~dp0Seestar_AstroLab_Setup.exe"
) else if exist "%~dp0Seestar_AstroLab_Setup_v1.1.1-beta.exe" (
    start "" "%~dp0Seestar_AstroLab_Setup_v1.1.1-beta.exe"
) else (
    echo   Готово! Теперь вы можете запускать Seestar_AstroLab_Setup.exe без окна SmartScreen.
    pause
)
exit /b 0
