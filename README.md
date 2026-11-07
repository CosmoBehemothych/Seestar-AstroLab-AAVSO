# 🔭 Seestar AstroLab AAVSO (v1.0.0 — Initial Release)

🌟 **Seestar AstroLab AAVSO** is a specialized desktop application for owners of **ZWO Seestar smart telescopes (`S30`, `S30PRO`, `S50`, `S50PRO`)** and variable star observers affiliated with the [AAVSO (American Association of Variable Star Observers)](https://www.aavso.org).

The program bridges the technical gap between the built-in photometry tool of [ZWO Seestar](https://www.seestar.com) telescopes and the scientific [AAVSO WebObs](https://www.aavso.org/webobs) database: it automatically converts raw Seestar photometric CSV files into the international **AAVSO Extended** standard, verifies star coordinates and identifiers via [CDS SIMBAD](https://simbad.cds.unistra.fr/simbad/) and [AAVSO VSP (Variable Star Plotter)](https://app.aavso.org/vsp/), automatically selects the optimal check star (`Check Star`: `KNAME` / `KMAG`) within the field of view of each Seestar model, plots the light curve, and includes an interactive **AAVSO Urgent Target Radar (`Alert Notices`)** and a personal progress tracker **"My Observations"**.

---

## 📑 Table of Contents

- [📖 About the Project](#-about-the-project)
- [📸 Screenshots](#-screenshots)
- [✨ Key Features](#-key-features)
- [🔭 Supported Seestar Models](#-supported-seestar-models)
- [🧭 Step-by-Step Guide](#-step-by-step-guide)
  - [⚙️ Step 1: Installation & First Launch](#️-step-1-installation--first-launch)
  - [👤 Step 2: Observer Profile Setup (One-Time)](#-step-2-observer-profile-setup-one-time)
  - [⭐ Step 3: Target Selection & Check Star Auto-Selection](#-step-3-target-selection--check-star-auto-selection)
  - [📊 Step 4: CSV Conversion & Submission to AAVSO WebObs](#-step-4-csv-conversion--submission-to-aavso-webobs)
- [🔎 Search Keywords](#-search-keywords)
- [👨‍💻 Authorship & Support](#-authorship--support)
- [🇷🇺 Русская версия (Russian Version)](#-русская-версия-russian-version)

---

## 📖 About the Project

**Seestar AstroLab AAVSO** is an open desktop photometry suite for **ZWO Seestar (`S50`, `S50PRO`, `S30`, `S30PRO`)** smart telescopes that bridges the gap between Seestar's built-in photometry output and official [AAVSO WebObs](https://www.aavso.org/webobs) scientific submissions.

---

## 📸 Screenshots

### 1. Main dashboard, Seestar → AAVSO Extended photometry converter, and light curve (Dark theme)
![Seestar AstroLab AAVSO main dashboard, target radar, and light curve](https://raw.githubusercontent.com/CosmoBehemothych/Seestar-AstroLab-AAVSO/main/screenshots/01_main_dashboard_and_urgent_radar_dark.png)

### 2. Interactive AAVSO Urgent Target Radar (`Alert Notices` & Priority Targets)
![AAVSO urgent target radar in Seestar AstroLab AAVSO](https://raw.githubusercontent.com/CosmoBehemothych/Seestar-AstroLab-AAVSO/main/screenshots/02_photometry_converter_and_light_curve.png)

### 3. "My Observations" section (auto-logging of sessions and smoothed HiDPI progress chart)
![My Observations section and photometry progress chart](https://raw.githubusercontent.com/CosmoBehemothych/Seestar-AstroLab-AAVSO/main/screenshots/03_my_observations_analytics.png)

### 4. Light theme and multilingual interface (Light Theme)
![Seestar AstroLab AAVSO light theme](https://raw.githubusercontent.com/CosmoBehemothych/Seestar-AstroLab-AAVSO/main/screenshots/04_light_theme_and_multilang.png)

### 5. Installer menu localized into 6 languages (`RU | EN | ES | DE | FR | ZH`)
![Seestar AstroLab AAVSO installer window in 6 languages](https://raw.githubusercontent.com/CosmoBehemothych/Seestar-AstroLab-AAVSO/main/screenshots/05_installer_6_languages_ui.png)

---

## ✨ Key Features

- 🔄 **Direct ZWO Seestar CSV → AAVSO Extended conversion**: automatically calculates mid-exposure Julian Date (`JD_Mid = (JD_Start + JD_End) / 2`), filters target measurements (`Non-reference star`), rounds instrumental `MAG` and uncertainty `MERR` in the `TG` band to 4 decimal places, and generates a valid `#TYPE=EXTENDED` header with your `#OBSCODE`.
- 🔭 **Adapted for all 4 ZWO Seestar models**:
  - **Seestar S30** — FOV `1.28°×0.72°`, photometry limit up to `13.5 mag`
  - **Seestar S30PRO** — FOV `2.10°×1.18°`, 4K sensor, up to `14.2 mag`
  - **Seestar S50** — FOV `0.78°×1.05°`, up to `14.5 mag`
  - **Seestar S50PRO** — FOV `1.15°×0.65°`, 4K sensor, up to `15.2 mag`
- 🛰️ **Parallel synchronization with CDS SIMBAD, VizieR, and AAVSO VSP catalogs**: automatic reduction of Latin constellation names according to IAU standards (IAU 88 constellations, e.g., `SZ Lyncis` → `SZ Lyn`), retrieval of the official chart identifier (`CHART ID`), and automatic selection of a non-variable check star (`KNAME`, `KMAG`) within the field of view of the selected telescope (with an autonomous offline fallback for field work without internet).
- 🚨 **AAVSO Urgent Target Radar (`Urgent` flag)**: built-in catalog of priority AAVSO targets (recurrent novae `T CrB`, `RS Oph`, cataclysmic and symbiotic variables `SS Cyg`, `CH Cyg`, `U Gem`, short-period pulsating stars `SZ Lyn`, etc.) with filtering based on the limiting magnitude of your Seestar model.
- 💾 **Persistent storage of `OBSCODE` and "My Observations" database**: a native Windows storage bridge (`AstroLabDiskBridge`) atomically saves your observatory code `OBSCODE`, conversion history, selected language, and theme to `%APPDATA%\Seestar_AstroLab\user_persistent_store.json`. Data is reliably preserved after closing the program and when installing updates over the existing version.
- 🌍 **Full localization of the application and installer into 6 languages**: Russian (`ru-RU`), English (`en-US`), Spanish (`es-ES`), German (`de-DE`), French (`fr-FR`), and Chinese (`zh-CN`).

---

## 🔭 Supported Seestar Models

| 🔭 Model | 📐 Field of View (FOV) | 🌟 Photometry Limit |
| :--- | :--- | :--- |
| Seestar S30 | 1.28° × 0.72° | up to 13.5 mag |
| Seestar S30PRO | 2.10° × 1.18° | up to 14.2 mag |
| Seestar S50 | 0.78° × 1.05° | up to 14.5 mag |
| Seestar S50PRO | 1.15° × 0.65° | up to 15.2 mag |

---

## 🧭 Step-by-Step Guide (From Seestar Imaging to AAVSO WebObs Submission)

### ⚙️ Step 1: Installation & First Launch (Windows 10 / 11)

1. ⬇️ Download the installer **`Seestar_AstroLab_Setup.exe`** from the [Releases](https://github.com/CosmoBehemothych/Seestar-AstroLab-AAVSO/releases) section (or unzip the release archive).
2. 🚀 Run `Seestar_AstroLab_Setup.exe`, select your preferred installer language (`RU Русский`, `EN English`, `ES Español`, `DE Deutsch`, `FR Français`, `ZH 中文`), and click **"Install / Update"**.
   - 🛡️ *Security and path note*: The installer operates in user mode (`PrivilegesRequired=lowest`, without requesting UAC administrator rights) and installs the application to `%LOCALAPPDATA%\Programs\Seestar_AstroLab`, creating a **Seestar AstroLab AAVSO** shortcut on the Desktop and a folder with 3 shortcuts in the Start menu (`Seestar AstroLab AAVSO`, `Seestar AstroLab AAVSO Web`, `Uninstall Seestar AstroLab AAVSO`).
3. 💼 A portable build `Portable/Seestar_AstroLab_Portable.exe` (no installation required) and a standalone web interface `Source_and_Build/pwa_mobile_and_electron/index.html` are also available.

### 👤 Step 2: Observer Profile Setup (One-Time)

1. 🔭 In the top panel, select your telescope model (`S30`, `S30PRO`, `S50`, or `S50PRO`).
2. 🪪 In the **"Observer and Star"** block, enter your official AAVSO observer code in the **`OBSCODE`** field (e.g., `CBH01`). The field is saved to disk instantly upon entry and remains populated on all subsequent launches of the program.

### ⭐ Step 3: Target Selection & Check Star Auto-Selection

1. 🎯 Select a priority star in the left panel **"AAVSO Target Radar"** (by clicking the **"Select"** button on the object card) or manually enter the star name in the **`STARID`** field (e.g., `SZ Lyn`, `T CrB`, or `SS Cyg`).
2. 🛰️ The program automatically normalizes the name according to IAU standards, queries [CDS SIMBAD](https://simbad.cds.unistra.fr/simbad/) and the [AAVSO VSP API](https://app.aavso.org/vsp/) in parallel, verifies the `RA/DEC (J2000)` coordinates, and automatically fills in the following fields:
   - 📄 **`CHART ID`** — the identifier of the official AAVSO photometric chart;
   - ✅ **`KNAME`** and **`KMAG`** — the optimal non-variable check star (`Check Star`) within the field of view of your Seestar sensor.

### 📊 Step 4: CSV Conversion & Submission to AAVSO WebObs

1. 📂 Drag and drop (or use the **"Select Seestar CSV File"** button to choose) the raw photometry file exported from the ZWO Seestar app.
2. 📈 Review the automatically plotted **light curve** (`JD Mid` vs `MAG ± MERR`) and the preview table on the right.
3. 🔄 Click the **"Convert and Download AAVSO Extended File"** button:
   - 💾 The ready `.csv` report in the `#TYPE=EXTENDED` standard will be saved to your computer;
   - 📝 The session will be automatically logged in the **"My Observations"** section and will update your personal progress chart.
4. 🌐 Go to the [AAVSO WebObs — Upload File](https://www.aavso.org/webobs) portal (the page will open automatically after file conversion) and upload the generated `.csv` file.

---

## 🔎 Search Keywords

`seestar` `aavso` `zwo-seestar` `seestar-s50` `seestar-s30` `seestar-s50pro` `seestar-s30pro` `aavso-extended` `photometry` `variable-stars` `simbad` `aavso-vsp` `light-curve` `astronomy` `astrophotography` `citizen-science` `фотометрия` `переменные-звезды` `телескоп-seestar`

---

## 👨‍💻 Authorship & Support

- 🧑‍🚀 **Developer**: **CosmoBehemothych** ([https://github.com/CosmoBehemothych](https://github.com/CosmoBehemothych))
- 🛡️ **Anti-Plagiarism Fingerprint**: `CBH-ASTROLAB-AAVSO-2026-9F8E4A21-7C3D-B601` (detailed verification documentation is available in the [`AUTHORSHIP_AND_COPYRIGHT_PROOF.md`](Source_and_Build/docs/AUTHORSHIP_AND_COPYRIGHT_PROOF.md) file)
- ☕ **Support the project on Boosty**: [https://boosty.to/cosmobehemothych](https://boosty.to/cosmobehemothych)

---

## 🇷🇺 Русская версия (Russian Version)

> 📸 Скриншоты интерфейса — см. выше в разделе [📸 Screenshots](#-screenshots) (изображения не зависят от языка).

🌟 **Seestar AstroLab AAVSO** — специализированное десктопное приложение для владельцев умных телескопов **ZWO Seestar (`S30`, `S30PRO`, `S50`, `S50PRO`)** и наблюдателей переменных звёзд [AAVSO (American Association of Variable Star Observers)](https://www.aavso.org).

Программа устраняет технический барьер между встроенным инструментом фотометрии телескопов [ZWO Seestar](https://www.seestar.com) и научной базой данных [AAVSO WebObs](https://www.aavso.org/webobs): она автоматически переводит сырые фотометрические CSV-файлы Seestar в международный научный стандарт **AAVSO Extended**, сверяет координаты и идентификаторы звёзд через [CDS SIMBAD](https://simbad.cds.unistra.fr/simbad/) и [AAVSO VSP (Variable Star Plotter)](https://app.aavso.org/vsp/), автоматически подбирает оптимальную контрольную звезду (`Check Star`: `KNAME` / `KMAG`) в поле зрения конкретной модели Seestar, строит кривую блеска и включает интерактивный **Радар срочных целей AAVSO (`Alert Notices`)** и личный трекер прогресса **«Мои наблюдения»**.

### 🔍 Ключевые возможности

* 🔄 **Прямая конвертация ZWO Seestar CSV → AAVSO Extended**: автоматический пересчёт середины экспозиции в юлианскую дату (`JD_Mid = (JD_Start + JD_End) / 2`), фильтрация целевых измерений (`Non-reference star`), округление инструментального блеска `MAG` и погрешности `MERR` в полосе `TG` до 4 знаков после запятой и формирование валидного заголовка `#TYPE=EXTENDED` с вашим кодом `#OBSCODE`.
* 🔭 **Адаптация под все 4 модели телескопов ZWO Seestar**:
  * **Seestar S30** — FOV `1.28°×0.72°`, рабочий предел фотометрии до `13.5 mag`
  * **Seestar S30PRO** — FOV `2.10°×1.18°`, 4K сенсор, до `14.2 mag`
  * **Seestar S50** — FOV `0.78°×1.05°`, до `14.5 mag`
  * **Seestar S50PRO** — FOV `1.15°×0.65°`, 4K сенсор, до `15.2 mag`
* 🛰️ **Параллельная синхронизация с каталогами CDS SIMBAD, VizieR и AAVSO VSP**: автоматическая редукция латинских названий созвездий по стандарту МАС (IAU 88 constellations, например `SZ Lyncis` → `SZ Lyn`), загрузка официального идентификатора карты (`CHART ID`) и автоматический подбор непеременной контрольной звезды (`KNAME`, `KMAG`) в поле зрения выбранного телескопа (с автономным офлайн-резервом при работе в поле без интернета).
* 🚨 **Радар срочных запросов AAVSO (`Звёзды с пометкой «Срочно»`)**: встроенный каталог приоритетных целей AAVSO (повторные новые `T CrB`, `RS Oph`, катаклизмические и симбиотические переменные `SS Cyg`, `CH Cyg`, `U Gem`, короткопериодические пульсирующие звёзды `SZ Lyn` и др.) с фильтрацией под проницающую способность вашей модели Seestar.
* 💾 **Постоянное сохранение `OBSCODE` и базы «Мои наблюдения»**: нативный мост хранения Windows (`AstroLabDiskBridge`) атомарно сохраняет ваш код обсерватории `OBSCODE`, историю сконвертированных файлов, выбранный язык и тему в `%APPDATA%\Seestar_AstroLab\user_persistent_store.json`. Данные гарантированно сохраняются после закрытия программы и при установке обновлений поверх.
* 🌍 **Полная локализация программы и установщика на 6 языков**: Русский (`ru-RU`), English (`en-US`), Español (`es-ES`), Deutsch (`de-DE`), Français (`fr-FR`) и 中文 (`zh-CN`).

### 📋 Пошаговая инструкция пользователя (От съёмки на Seestar до отправки в AAVSO WebObs)

#### ⚙️ Шаг 1. Установка и первый запуск (Windows 10 / 11)

1. ⬇️ Скачайте установщик **`Seestar_AstroLab_Setup.exe`** из раздела [Releases](https://github.com/CosmoBehemothych/Seestar-AstroLab-AAVSO/releases) (или распакуйте архив релиза).
2. 🚀 Запустите `Seestar_AstroLab_Setup.exe`, выберите удобный язык установщика (`RU Русский`, `EN English`, `ES Español`, `DE Deutsch`, `FR Français`, `ZH 中文`) и нажмите **«Установить / Обновить»**.
   * 🛡️ *Примечание по безопасности и путям*: Установщик работает в пользовательском контуре (`PrivilegesRequired=lowest`, без запроса прав администратора UAC) и устанавливает приложение в `%LOCALAPPDATA%\Programs\Seestar_AstroLab`, создавая ярлык **Seestar AstroLab AAVSO** на Рабочем столе и папку с 3 ярлыками в меню «Пуск» (`Seestar AstroLab AAVSO`, `Seestar AstroLab AAVSO Web`, `Удалить Seestar AstroLab AAVSO`).
3. 💼 Также доступна портативная сборка `Portable/Seestar_AstroLab_Portable.exe` (не требует установки) и автономный веб-интерфейс `Source_and_Build/pwa_mobile_and_electron/index.html`.

#### 👤 Шаг 2. Настройка профиля наблюдателя (1 раз)

1. 🔭 В верхней панели выберите модель вашего телескопа (`S30`, `S30PRO`, `S50` или `S50PRO`).
2. 🪪 В блоке **«Наблюдатель и звезда»** введите ваш официальный код наблюдателя AAVSO в поле **`OBSCODE`** (например, `CBH01`). Поле сохраняется на жёсткий диск мгновенно при вводе и остаётся заполненным при всех последующих запусках программы.

#### ⭐ Шаг 3. Выбор цели и автоподбор контрольной звезды (`Check Star`)

1. 🎯 Выберите приоритетную звезду в левой панели **«Радар целей AAVSO»** (нажав кнопку **«Выбрать»** на карточке объекта) или введите название звезды вручную в поле **`STARID`** (например, `SZ Lyn`, `T CrB` или `SS Cyg`).
2. 🛰️ Программа автоматически нормализует название по стандарту МАС, параллельно опросит зеркала [CDS SIMBAD](https://simbad.cds.unistra.fr/simbad/) и [AAVSO VSP API](https://app.aavso.org/vsp/), проверит координаты `RA/DEC (J2000)` и автоматически заполнит поля:
   * 📄 **`CHART ID`** — идентификатор официальной фотометрической карты AAVSO;
   * ✅ **`KNAME`** и **`KMAG`** — оптимальная непеременная контрольная звезда (`Check Star`) в поле зрения вашей матрицы Seestar.

#### 📊 Шаг 4. Конвертация CSV-файла Seestar и отправка в AAVSO WebObs

1. 📂 Перетащите (Drag-and-Drop) или выберите через кнопку **«Выбрать CSV-файл Seestar»** сырой файл фотометрии, выгруженный из приложения ZWO Seestar.
2. 📈 Проверьте автоматически построенную **кривую блеска** (`JD Mid` vs `MAG ± MERR`) и таблицу предпросмотра справа.
3. 🔄 Нажмите кнопку **«Конвертировать и скачать файл AAVSO Extended»**:
   * 💾 Готовый отчёт `.csv` в стандарте `#TYPE=EXTENDED` сохранится на ваш компьютер;
   * 📝 Сессия автоматически запишется в раздел **«Мои наблюдения»** и обновит график вашего личного прогресса.
4. 🌐 Перейдите на портал [AAVSO WebObs — Upload File](https://www.aavso.org/webobs) (страница откроется автоматически, после конвертации файла) и загрузите созданный `.csv`-файл.

### 🏷️ Ключевые слова для поиска

`seestar` `aavso` `zwo-seestar` `seestar-s50` `seestar-s30` `seestar-s50pro` `seestar-s30pro` `aavso-extended` `photometry` `variable-stars` `simbad` `aavso-vsp` `light-curve` `astronomy` `astrophotography` `citizen-science` `фотометрия` `переменные-звезды` `телескоп-seestar`

### ❤️ Авторство и поддержка проекта

* 🧑‍🚀 **Разработчик**: **CosmoBehemothych** ([https://github.com/CosmoBehemothych](https://github.com/CosmoBehemothych))
* 🛡️ **Цифровой отпечаток авторства (Anti-Plagiarism Fingerprint)**: `CBH-ASTROLAB-AAVSO-2026-9F8E4A21-7C3D-B601` (подробная документация по верификации подлинности — в файле [`AUTHORSHIP_AND_COPYRIGHT_PROOF.md`](Source_and_Build/docs/AUTHORSHIP_AND_COPYRIGHT_PROOF.md))
* ☕ **Поддержать развитие проекта на Boosty**: [https://boosty.to/cosmobehemothych](https://boosty.to/cosmobehemothych)
