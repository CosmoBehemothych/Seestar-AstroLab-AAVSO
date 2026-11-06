# 🔭 Seestar AstroLab AAVSO

> Desktop photometry suite for **ZWO Seestar** smart telescopes → official **AAVSO Extended** submissions.  
> Превращает сырые CSV-логи Seestar в готовые научные отчёты AAVSO за один клик.

[![Version](https://img.shields.io/badge/version-1.0.0-blue)]()
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-lightgrey)]()
[![AAVSO](https://img.shields.io/badge/format-AAVSO%20Extended-success)]()
[![Languages](https://img.shields.io/badge/UI-6%20languages-orange)]()
[![License](https://img.shields.io/badge/license-see%20LICENSE-informational)]()

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Supported Telescopes](#-supported-telescopes)
- [Installation](#-installation-windows-10--11)
- [Quick Start](#-quick-start)
- [Screenshots](#-screenshots)
- [Roadmap & Status](#-roadmap--status)
- [FAQ](#-faq)
- [Support the Author](#-support-the-author)
- [Search Keywords](#-search-keywords--tags)
- [Русская версия](#-русская-версия)

---

## 🌐 Overview

**Seestar AstroLab AAVSO** is a dedicated desktop photometry suite for **ZWO Seestar S50, S50PRO, S30, and S30PRO** smart telescopes. It converts raw Seestar photometry CSV logs into the official **AAVSO Extended Format** ready for submission to **AAVSO WebObs**, verifies coordinates and star identifiers against **CDS SIMBAD** and the **AAVSO Variable Star Plotter (VSP)**, automatically picks an optimal **Check Star** (`KNAME` / `KMAG`), renders the light curve, and includes an interactive **AAVSO Alert Notice radar** for high-priority targets.

Built and maintained by **CosmoBehemothych** for the variable-star observer community and Seestar owners worldwide.

---

## ✨ Key Features

### 🔁 Seestar CSV → AAVSO Extended
- Computes mid-exposure Julian Date (`JD Mid`) automatically.
- Filters target measurements (`Non-reference star` only).
- Rounds `MAG` and `MERR` to 4 decimal places.
- Emits a valid AAVSO Extended header: `#TYPE=EXTENDED`, `#OBSCODE`, `#STARID`, `#CHART`, `KNAME`, `KMAG`.

### 🔭 Full ZWO Seestar Lineup Support
| Model | FOV | Limiting mag (approx.) | Notes |
|---|---|---|---|
| **Seestar S30** | 1.28° × 0.72° | ~13.5 mag | Standard |
| **Seestar S30PRO** | 2.10° × 1.18° | ~14.2 mag | 4K sensor |
| **Seestar S50** | 0.78° × 1.05° | ~14.5 mag | Standard |
| **Seestar S50PRO** | 1.15° × 0.65° | ~15.2 mag | 4K sensor |

### 🛰️ Parallel Catalog Synchronization
- Queries **CDS SIMBAD** mirrors, **VizieR**, and **AAVSO VSP** in parallel.
- Normalizes constellation names per **IAU 88 constellations** (e.g. `SZ Lyncis` → `SZ Lyn`).
- Downloads `CHART ID` for the target neighborhood.
- Automatically selects a non-variable **Check Star** (`KNAME`, `KMAG`) within your Seestar's field of view.

### 🚨 AAVSO Urgent Target Radar
- Built-in catalog of priority AAVSO Alert Notices: recurrent novae, cataclysmic variables, symbiotic stars, Miras, eclipsing binaries.
- Sortable by publication date, target name, and priority.
- Filters targets to those observable within your telescope's limiting magnitude.

### 📊 "My Observations" Tracker
- Automatically logs every scientific session when a CSV is converted.
- High-DPI smoothed (cubic-Bézier) activity chart.
- Filter by date, star (`STARID`), and telescope model.
- Persistent state across app restarts.

### 🌍 Localization & Theming
- **6 UI languages**: Русский (`ru-RU`), English (`en-US`), Español (`es-ES`), Deutsch (`de-DE`), Français (`fr-FR`), 中文 (`zh-CN`).
- **Standard Dark** and **Light** themes with instant switching.

---

## 🖥️ Supported Telescopes

Optimized and tested for the entire **ZWO Seestar** family:

- ✅ **Seestar S30**
- ✅ **Seestar S30 PRO**
- ✅ **Seestar S50**
- ✅ **Seestar S50 PRO**

> ⚠️ Other smart telescopes may work if their CSV format matches Seestar's — but this is not officially supported.

---

## 🚀 Installation (Windows 10 / 11)

1. Download **`Seestar_AstroLab_Setup.exe`** from the [Releases](../../releases) section (or unpack `Seestar_AstroLab_Desktop_Release_2026.zip`).
2. Run `Seestar_AstroLab_Setup.exe` — the app installs into the user profile **without UAC elevation** and creates the **Seestar AstroLab AAVSO** shortcut on your Desktop and in the Start menu.
3. Alternatives:
   - **Portable:** `Portable/Seestar_AstroLab_Portable.exe`
   - **Web / PWA / Electron build:** `Source_and_Build/pwa_mobile_and_electron/index.html`

**System requirements:** Windows 10 or 11 (64-bit), 4 GB RAM, 200 MB free disk space, active internet connection (for SIMBAD / VSP queries).

---

## ⚡ Quick Start

1. **Set your observer code** in *Settings* — your official **AAVSO `OBSCODE`** (required for valid submissions).
2. **Pick your Seestar model** — this sets the FOV used for check-star search.
3. **Load your Seestar CSV** — drag-and-drop or *File → Open*.
4. **Review the auto-filled header** — `STARID`, `RA/DEC (J2000)`, `CHART`, `KNAME`, `KMAG` are pre-populated.
5. **Export AAVSO Extended file** — ready to upload to **AAVSO WebObs**.
6. (Optional) Open the **Urgent Targets Radar** to plan tonight's session.

---

## 🖼️ Screenshots

> _Add screenshots here once a stable UI is available: `docs/screenshot-main.png`, `docs/screenshot-radar.png`, `docs/screenshot-lightcurve.png`._

---

## 🗺️ Roadmap & Status

| Status | Item |
|---|---|
| ✅ | Seestar CSV → AAVSO Extended conversion |
| ✅ | SIMBAD / VizieR / VSP auto-lookup |
| ✅ | Auto check-star selection |
| ✅ | Urgent-target radar |
| ✅ | "My Observations" tracker |
| ✅ | 6-language UI + dark/light themes |
| 🔜 | Native macOS / Linux builds |
| 🔜 | Direct upload to AAVSO WebObs (experimental) |
| 🔜 | Variable-star light-curve overlay from AAVSO LCG |

---

## ❓ FAQ

**Q: Is my data uploaded anywhere?**  
A: No. All conversions happen locally. Only catalog queries (SIMBAD, VizieR, VSP) go out over HTTPS.

**Q: Which AAVSO chart is used?**  
A: The one returned by VSP for the target — automatically inserted as `CHART ID`.

**Q: Does it work with S30 without PRO?**  
A: Yes — the smaller FOV is accounted for during check-star selection.

**Q: Can I submit raw Seestar CSV to AAVSO?**  
A: No. WebObs requires a specific format — that's exactly what this app produces.

---

## ❤️ Support the Author

The project is developed and maintained by **CosmoBehemothych** for the variable-star observer community and Seestar owners.

- **Boosty:** [https://boosty.to/cosmobehemothych](https://boosty.to/cosmobehemothych)

Your support covers: SIMBAD/VSP API stability, test hardware, and ongoing localization work.

---

## 🏷️ Search Keywords / Tags

`seestar` `aavso` `zwo-seestar` `seestar-s50` `seestar-s30` `seestar-s50pro` `seestar-s30pro` `aavso-extended` `photometry` `variable-stars` `simbad` `aavso-vsp` `light-curve` `astronomy` `astrophotography` `smart-telescope` `фотометрия` `переменные-звезды` `телескоп-seestar` `ZWO` `WebObs` `CCD photometry`

---

<br>

# 🇷🇺 Русская версия

**Seestar AstroLab AAVSO** — десктопное приложение для владельцев умных телескопов **ZWO Seestar (S30, S30PRO, S50, S50PRO)** и наблюдателей переменных звёзд **AAVSO** (American Association of Variable Star Observers). Программа автоматизирует конвертацию сырых фотометрических CSV-файлов Seestar в международный научный формат **AAVSO Extended**, выполняет сверку координат и идентификаторов звёзд через **CDS SIMBAD** и **AAVSO VSP (Variable Star Plotter)**, автоматически подбирает оптимальную контрольную звезду (`Check Star`: `KNAME` / `KMAG`), строит кривую блеска и включает интерактивный **Радар приоритетных и срочных целей AAVSO (Alert Notices)**.

## 🔍 Ключевые возможности

### 🔁 Прямая связь ZWO Seestar → AAVSO Extended
Автоматический пересчёт середины экспозиции в юлианскую дату (`JD Mid`), фильтрация целевых измерений (`Non-reference star`), округление `MAG` и `MERR` до 4 знаков и формирование валидного заголовка `#TYPE=EXTENDED` с вашим кодом наблюдателя `#OBSCODE`.

### 🔭 Поддержка всей линейки ZWO Seestar
- **Seestar S30** — `FOV 1.28°×0.72°`, до `13.5 mag`
- **Seestar S30PRO** — `FOV 2.10°×1.18°`, 4K, до `14.2 mag`
- **Seestar S50** — `FOV 0.78°×1.05°`, до `14.5 mag`
- **Seestar S50PRO** — `FOV 1.15°×0.65°`, 4K, до `15.2 mag`

### 🛰️ Параллельная синхронизация с каталогами
SIMBAD, VizieR и AAVSO VSP — параллельно. Автоматическая нормализация названий созвездий по стандарту МАС (IAU 88 constellations, например `SZ Lyncis` → `SZ Lyn`), загрузка карт окрестностей (`CHART ID`) и подбор непеременной контрольной звезды (`KNAME`, `KMAG`) в поле зрения вашей модели Seestar.

### 🚨 Радар срочных целей AAVSO
Встроенный каталог приоритетных целей AAVSO (повторные новые, катаклизмические переменные, симбиотические звёзды, мириды, затменные двойные) с сортировкой по дате публикации запроса, названию и приоритету.

### 📊 Раздел «Мои наблюдения»
Автоматическое логирование ваших научных сессий по факту конвертации CSV-файлов, построение сглаженного HiDPI-графика активности и фильтрация по дате, звезде (`STARID`) и телескопу с постоянным сохранением прогресса между сессиями.

### 🌍 Локализация и темы
**6 языков интерфейса**: Русский (`ru-RU`), English (`en-US`), Español (`es-ES`), Deutsch (`de-DE`), Français (`fr-FR`), 中文 (`zh-CN`), а также переключатель **Стандартной тёмной** и **Светлой** темы.

## 🚀 Быстрая установка (Windows 10 / 11)

1. Скачайте установщик **`Seestar_AstroLab_Setup.exe`** из раздела **Releases** (или распакуйте архив `Seestar_AstroLab_Desktop_Release_2026.zip`).
2. Запустите `Seestar_AstroLab_Setup.exe` — программа устанавливается в профиль пользователя без запроса прав администратора (UAC) и создаёт ярлык **Seestar AstroLab AAVSO** на Рабочем столе и в меню «Пуск».
3. Альтернативы:
   - **Портативная версия** — `Portable/Seestar_AstroLab_Portable.exe`
   - **Веб/PWA/Electron-сборка** — `Source_and_Build/pwa_mobile_and_electron/index.html`

## ❤️ Поддержать автора проекта

Проект разрабатывается и поддерживается **CosmoBehemothych** для сообщества наблюдателей переменных звёзд и владельцев телескопов Seestar:

- **Boosty:** [https://boosty.to/cosmobehemothych](https://boosty.to/cosmobehemothych)

---

## 📄 License

See the `LICENSE` file in the repository root for details.  
Подробности — в файле `LICENSE` в корне репозитория.
