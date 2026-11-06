# 🔭 Seestar AstroLab AAVSO (v1.0.0 — Первая версия)

**Seestar AstroLab AAVSO** — десктопное приложение для владельцев умных телескопов **ZWO Seestar (S30, S30PRO, S50, S50PRO)** и наблюдателей переменных звёзд **AAVSO** (American Association of Variable Star Observers). Программа автоматизирует конвертацию сырых фотометрических CSV-файлов Seestar в международный научный формат **AAVSO Extended**, выполняет сверку координат и идентификаторов звёзд через **CDS SIMBAD** и **AAVSO VSP (Variable Star Plotter)**, автоматически подбирает оптимальную контрольную звезду (`Check Star`: `KNAME` / `KMAG`), строит кривую блеска и включает интерактивный **Радар приоритетных и срочных целей AAVSO (Alert Notices)**.

---

## 🔍 Ключевые возможности (RU)

* **Прямая связь ZWO Seestar → AAVSO Extended**: автоматический пересчёт середины экспозиции в юлианскую дату (`JD Mid`), фильтрация целевых измерений (`Non-reference star`), округление `MAG` и `MERR` до 4 знаков и формирование валидного заголовка `#TYPE=EXTENDED` с вашим кодом наблюдателя `#OBSCODE`.
* **Поддержка всей линейки телескопов ZWO Seestar**:
  * **Seestar S30** (`FOV 1.28°×0.72°`, до `13.5 mag`)
  * **Seestar S30PRO** (`FOV 2.10°×1.18°`, 4K, до `14.2 mag`)
  * **Seestar S50** (`FOV 0.78°×1.05°`, до `14.5 mag`)
  * **Seestar S50PRO** (`FOV 1.15°×0.65°`, 4K, до `15.2 mag`)
* **Параллельная синхронизация с каталогами SIMBAD, VizieR и AAVSO VSP**: автоматическая нормализация названий созвездий по стандарту МАС (IAU 88 constellations, например `SZ Lyncis` → `SZ Lyn`), загрузка карт окрестностей (`CHART ID`) и подбор непеременной контрольной звезды (`KNAME`, `KMAG`) в поле зрения вашей модели Seestar.
* **Радар срочных целей AAVSO (`Звёзды с пометкой «Срочно»`)**: встроенный каталог приоритетных целей AAVSO (повторные новые, катаклизмические переменные, симбиотические звёзды, мириды, затменные двойные) с сортировкой по дате публикации запроса, названию и приоритету.
* **Раздел «Мои наблюдения»**: автоматическое логирование ваших научных сессий по факту конвертации CSV-файлов, построение сглаженного HiDPI-графика активности и фильтрация по дате, звезде (`STARID`) и телескопу с постоянным сохранением прогресса между сессиями.
* **6 языков интерфейса**: Русский (`ru-RU`), English (`en-US`), Español (`es-ES`), Deutsch (`de-DE`), Français (`fr-FR`), 中文 (`zh-CN`), а также переключатель **Стандартной тёмной** и **Светлой** темы.

---

## 🌐 Overview & Features (English — SEO Summary)

**Seestar AstroLab AAVSO** is a dedicated desktop photometry suite for **ZWO Seestar S50, S50PRO, S30, and S30PRO** smart telescopes designed to convert raw Seestar photometry CSV logs into official **AAVSO Extended Format** reports ready for submission to **AAVSO WebObs**.

* **Seestar CSV to AAVSO Extended Converter**: Computes mid-exposure Julian Date (`JD Mid`), extracts instrumental `TG` (Tri-color Green) magnitudes and uncertainties (`MAG`, `MERR`), and populates `#OBSCODE`, `#STARID`, `#CHART`, `KNAME`, and `KMAG`.
* **SIMBAD & AAVSO VSP Auto-Calibration**: Queries global CDS SIMBAD mirrors and the AAVSO Variable Star Plotter (VSP) API in parallel to verify `RA/DEC (J2000)` coordinates, resolve canonical VSX star identifiers, and automatically pick an optimal Check Star within your Seestar sensor field of view.
* **AAVSO Urgent Target Radar**: Track high-priority AAVSO Alert Notices and campaigns (such as `T CrB`, `SS Cyg`, `SZ Lyn`, `CH Cyg`, `RS Oph`, `U Gem`) filtered for your Seestar telescope's limiting magnitude.
* **Personal Observation Progress Tracker ("My Observations")**: Automatically records your converted photometry runs and visualizes your observation history with a high-DPI cubic-Bézier spline chart.

---

## 🚀 Быстрая установка (Windows 10 / 11)

1. Скачайте установщик **`Seestar_AstroLab_Setup.exe`** из раздела **Releases** (или распакуйте архив `Seestar_AstroLab_Desktop_Release_2026.zip`).
2. Запустите `Seestar_AstroLab_Setup.exe` — программа устанавливается в профиль пользователя без запроса прав администратора (UAC) и создаёт ярлык **Seestar AstroLab AAVSO** на Рабочем столе и в меню «Пуск».
3. Также доступна портативная версия в папке `Portable/Seestar_AstroLab_Portable.exe` и веб-версия `Source_and_Build/pwa_mobile_and_electron/index.html`.

---

## 🏷️ Ключевые слова для поиска (Search Keywords / Tags)

`seestar` `aavso` `zwo-seestar` `seestar-s50` `seestar-s30` `seestar-s50pro` `seestar-s30pro` `aavso-extended` `photometry` `variable-stars` `simbad` `aavso-vsp` `light-curve` `astronomy` `astrophotography` `smart-telescope` `фотометрия` `переменные-звезды` `телескоп-seestar`

---

## ❤️ Поддержать автора проекта

Проект разрабатывается и поддерживается **CosmoBehemothych** для сообщества наблюдателей переменных звёзд и владельцев телескопов Seestar:
* **Boosty**: [https://boosty.to/cosmobehemothych](https://boosty.to/cosmobehemothych)
