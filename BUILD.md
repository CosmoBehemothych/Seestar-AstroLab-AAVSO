# Building Seestar AstroLab AAVSO from Source

This guide explains how to reproduce the official Windows installer (`Seestar_AstroLab_Setup_v1.3.2.exe`) directly from the source code in this repository — matching the exact pipeline executed by [`.github/workflows/build.yml`](.github/workflows/build.yml).

## Prerequisites (Windows 10 / 11, 64-bit)

- **Python 3.11** (64-bit) with `pip`
- **Inno Setup 6** (`ISCC.exe`, default install path `C:\Program Files (x86)\Inno Setup 6\`)
- **Microsoft Edge WebView2 Runtime** (pre-installed on Windows 10/11)

## 1. Clone the Repository & Install Dependencies

```powershell
git clone https://github.com/CosmoBehemothych/Seestar-AstroLab-AAVSO.git
cd Seestar-AstroLab-AAVSO
python -m pip install --upgrade pip
pip install pyinstaller pywebview pythonnet clr-loader pillow certifi
```

## 2. Run Mandatory Pre-Build Autotests

Verify all 8 UI localizations, coordinate reconciliation thresholds, and startup update checker logic before compiling:

```powershell
python tests/run_localization_autotest.py
python tests/run_coord_reconciliation_autotest.py
python tests/run_update_checker_autotest.py
```

All three scripts must exit with code `0` (`PASS`).

## 3. Compile the Application Binary (PyInstaller)

```powershell
cd Source_and_Build
pyinstaller --noconfirm --clean --onefile --console --noupx `
  --name "Seestar AstroLab" `
  --version-file version_info.txt `
  --collect-all webview `
  --collect-all pythonnet `
  --collect-all clr_loader `
  --collect-all certifi `
  --hidden-import webview.platforms.edgechromium `
  --add-data "pwa_mobile_and_electron;pwa_mobile_and_electron" `
  --add-data "backend;backend" `
  --add-data "desktop_pc;desktop_pc" `
  --add-data "Converted_Photometry_Storage;Converted_Photometry_Storage" `
  --icon "assets/Seestar_AstroLab.ico" `
  desktop_launcher.py
```

The standalone binary is produced at `Source_and_Build\dist\Seestar AstroLab.exe`.

## 4. Build the Windows Installer (Inno Setup 6)

```powershell
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" ".\Seestar_AstroLab_Installer.iss"
```

The final installer is written to:

```text
Source_and_Build\dist_installer\Seestar_AstroLab_Setup_v1.3.2.exe
```

## 5. Generate & Compare SHA-256 Checksum

```powershell
Get-FileHash .\dist_installer\Seestar_AstroLab_Setup_v1.3.2.exe -Algorithm SHA256
```

You can inspect the official CI build log and published `SHA256SUMS.txt` on the [GitHub Actions](https://github.com/CosmoBehemothych/Seestar-AstroLab-AAVSO/actions) and [Releases](https://github.com/CosmoBehemothych/Seestar-AstroLab-AAVSO/releases) pages.
