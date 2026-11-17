@echo off
setlocal EnableExtensions EnableDelayedExpansion

:: ==============================================================================
:: Seestar AstroLab by CosmoBehemothych (v1.1.2 beta)
:: Вспомогательный скрипт установки без предупреждений Windows SmartScreen
:: Кодировка: UTF-8 (без BOM)
:: ==============================================================================

:: 1. Переключаем кодовую страницу консоли в UTF-8 для корректного вывода русского текста
chcp 65001 >nul 2>&1
title Seestar AstroLab v1.1.2 beta — Помощник установки (CosmoBehemothych)

:: Определяем рабочую папку скрипта (без жёстко прописанных путей)
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"

echo ============================================================================
echo   Seestar AstroLab AAVSO v1.1.2 beta — Подготовка и запуск установщика
echo   Разработчик: CosmoBehemothych
echo   Репозиторий: https://github.com/CosmoBehemothych/Seestar-AstroLab-AAVSO
echo ============================================================================
echo.

:: 2. Проверка прав администратора (требуется для импорта сертификата и снятия блокировок)
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ИНФО] Для добавления сертификата в доверенные и снятия метки SmartScreen
    echo        требуются права администратора. Запрашиваем повышение прав ^(UAC^)...
    echo.
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "try { Start-Process -FilePath '%~f0' -WorkingDirectory '%SCRIPT_DIR%' -Verb RunAs } catch { Write-Host '[ОШИБКА] Повышение прав было отклонено пользователем.' -ForegroundColor Red; exit 1 }"
    if %errorlevel% neq 0 (
        echo.
        echo [ОШИБКА] Не удалось получить права администратора.
        echo Пожалуйста, нажмите правой кнопкой мыши по файлу и выберите
        echo "Запуск от имени администратора".
        pause
        exit /b 1
    )
    exit /b 0
)

echo [ШАГ 1/4] Права администратора подтверждены.
echo.

:: 3. Снятие метки Zone.Identifier (Mark-of-the-Web) через PowerShell Unblock-File
::    и обработка сертификата издателя + запуск установщика
echo [ШАГ 2/4] Снятие блокировки SmartScreen ^(Zone.Identifier^) с файлов установщика...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ErrorActionPreference = 'Continue'; " ^
    "$scriptDir = $env:SCRIPT_DIR; " ^
    "$downloadsDir = Join-Path $env:USERPROFILE 'Downloads'; " ^
    "try { " ^
    "    $shell = New-Object -ComObject Shell.Application; " ^
    "    $dlShell = $shell.NameSpace('shell:Downloads'); " ^
    "    if ($dlShell -and $dlShell.Self -and $dlShell.Self.Path) { $downloadsDir = $dlShell.Self.Path } " ^
    "} catch {} " ^
    "$targetDirs = @($scriptDir, $downloadsDir) | Select-Object -Unique; " ^
    "$unblockedCount = 0; " ^
    "foreach ($dir in $targetDirs) { " ^
    "    if (Test-Path -LiteralPath $dir) { " ^
    "        $files = Get-ChildItem -LiteralPath $dir -Filter 'Seestar_AstroLab_Setup*.exe' -File -ErrorAction SilentlyContinue; " ^
    "        foreach ($f in $files) { " ^
    "            try { " ^
    "                Unblock-File -LiteralPath $f.FullName -ErrorAction Stop; " ^
    "                Write-Host ('  [OK] Снята метка Mark-of-the-Web: ' + $f.FullName) -ForegroundColor Green; " ^
    "                $unblockedCount++; " ^
    "            } catch { " ^
    "                Write-Host ('  [ПРЕДУПРЕЖДЕНИЕ] Не удалось разблокировать ' + $f.Name + ': ' + $_.Exception.Message) -ForegroundColor Yellow; " ^
    "            } " ^
    "        } " ^
    "    } " ^
    "} " ^
    "if ($unblockedCount -eq 0) { " ^
    "    Write-Host '  [ИНФО] Файлы Seestar_AstroLab_Setup*.exe для разблокировки в текущей папке и Downloads не обнаружены или уже разблокированы.' -ForegroundColor Gray; " ^
    "}"

echo.
echo [ШАГ 3/4] Проверка цифровой подписи и добавление сертификата издателя ^(CosmoBehemothych^)...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ErrorActionPreference = 'Continue'; " ^
    "$scriptDir = $env:SCRIPT_DIR; " ^
    "$preferredName = 'Seestar_AstroLab_Setup_v1.1.2-beta.exe'; " ^
    "$installer = $null; " ^
    "$preferredPath = Join-Path $scriptDir $preferredName; " ^
    "if (Test-Path -LiteralPath $preferredPath) { " ^
    "    $installer = Get-Item -LiteralPath $preferredPath; " ^
    "} else { " ^
    "    $installer = Get-ChildItem -LiteralPath $scriptDir -Filter 'Seestar_AstroLab_Setup*.exe' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1; " ^
    "} " ^
    "if (-not $installer) { " ^
    "    Write-Host '[ОШИБКА] Файл установщика Seestar_AstroLab_Setup_v1.1.2-beta.exe (или Seestar_AstroLab_Setup*.exe) не найден в папке со скриптом!' -ForegroundColor Red; " ^
    "    Write-Host ('Текущая папка: ' + $scriptDir) -ForegroundColor Yellow; " ^
    "    exit 404; " ^
    "} " ^
    "Write-Host ('  Найден установщик: ' + $installer.FullName) -ForegroundColor Cyan; " ^
    "try { " ^
    "    $sig = Get-AuthenticodeSignature -LiteralPath $installer.FullName -ErrorAction Stop; " ^
    "    if ($sig -and $sig.SignerCertificate) { " ^
    "        $cert = $sig.SignerCertificate; " ^
    "        Write-Host ('  Обнаружен сертификат издателя: ' + $cert.Subject) -ForegroundColor Cyan; " ^
    "        $stores = @( " ^
    "            'Cert:\LocalMachine\Root', " ^
    "            'Cert:\LocalMachine\TrustedPublisher', " ^
    "            'Cert:\CurrentUser\Root', " ^
    "            'Cert:\CurrentUser\TrustedPublisher' " ^
    "        ); " ^
    "        foreach ($storePath in $stores) { " ^
    "            try { " ^
    "                $store = Get-Item -LiteralPath $storePath -ErrorAction Stop; " ^
    "                $store.Open('ReadWrite'); " ^
    "                $existing = $store.Certificates | Where-Object { $_.Thumbprint -eq $cert.Thumbprint }; " ^
    "                if (-not $existing) { " ^
    "                    $store.Add($cert); " ^
    "                    Write-Host ('  [OK] Сертификат добавлен в хранилище: ' + $storePath) -ForegroundColor Green; " ^
    "                } else { " ^
    "                    Write-Host ('  [OK] Сертификат уже присутствует в хранилище: ' + $storePath) -ForegroundColor Green; " ^
    "                } " ^
    "                $store.Close(); " ^
    "            } catch { " ^
    "                Write-Host ('  [ПРЕДУПРЕЖДЕНИЕ] Не удалось записать в ' + $storePath + ': ' + $_.Exception.Message) -ForegroundColor Yellow; " ^
    "            } " ^
    "        } " ^
    "    } else { " ^
    "        Write-Host '  [ИНФО] Цифровая подпись в файле установщика отсутствует (сборка GitHub Actions без сертификата). Метка SmartScreen (Zone.Identifier) успешно снята на предыдущем шаге.' -ForegroundColor Yellow; " ^
    "    } " ^
    "} catch { " ^
    "    Write-Host ('  [ОШИБКА СЕРТИФИКАТА] Не удалось обработать подпись файла: ' + $_.Exception.Message) -ForegroundColor Red; " ^
    "}"

if %errorlevel% equ 404 (
    echo.
    echo [КРИТИЧЕСКАЯ ОШИБКА] Пожалуйста, поместите этот BAT-файл в одну папку
    echo с файлом Seestar_AstroLab_Setup_v1.1.2-beta.exe и запустите снова.
    echo.
    pause
    exit /b 404
)

echo.
echo [ШАГ 4/4] Запуск установщика Seestar AstroLab от имени текущего пользователя...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$scriptDir = $env:SCRIPT_DIR; " ^
    "$preferredPath = Join-Path $scriptDir 'Seestar_AstroLab_Setup_v1.1.2-beta.exe'; " ^
    "if (Test-Path -LiteralPath $preferredPath) { " ^
    "    $targetExe = $preferredPath; " ^
    "} else { " ^
    "    $item = Get-ChildItem -LiteralPath $scriptDir -Filter 'Seestar_AstroLab_Setup*.exe' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1; " ^
    "    if ($item) { $targetExe = $item.FullName } else { $targetExe = $null } " ^
    "} " ^
    "if (-not $targetExe) { " ^
    "    Write-Host '[ОШИБКА] Не удалось найти исполняемый файл установщика для запуска.' -ForegroundColor Red; " ^
    "    exit 1; " ^
    "} " ^
    "try { " ^
    "    Write-Host ('  Запускаем через оболочку текущего пользователя: ' + $targetExe) -ForegroundColor Green; " ^
    "    Start-Process -FilePath 'explorer.exe' -ArgumentList ('\"' + $targetExe + '\"'); " ^
    "} catch { " ^
    "    Write-Host '[ПРЕДУПРЕЖДЕНИЕ] Откат на прямой запуск Start-Process...' -ForegroundColor Yellow; " ^
    "    Start-Process -FilePath $targetExe -WorkingDirectory $scriptDir; " ^
    "}"

if %errorlevel% neq 0 (
    echo.
    echo [ОШИБКА] Возникла проблема при запуске установщика.
    pause
    exit /b 1
)

echo.
echo [ГОТОВО] Мастер установки Seestar AstroLab v1.1.2 beta успешно запущен!
echo Окно закроется автоматически через 5 секунд...
timeout /t 5 >nul 2>&1
exit /b 0
