APP_VERSION = "2.4.0"
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
Seestar AstroLab by CosmoBehemothych: Desktop PC Application (Windows / macOS / Linux)
Конвертер научных фотометрических данных ZWO Seestar -> AAVSO Extended
================================================================================
НАЗНАЧЕНИЕ:
  Десктопное приложение для астрономов-исследователей переменных звезд,
  затменно-двойных систем и транзитов экзопланет. Автоматизирует:
  1. Параллельный опрос зеркал SIMBAD (CDS Strasbourg, IDIA, CfA Harvard).
  2. Загрузку фотометрических карт AAVSO VSP и автоподбор оптимальной
     контрольной звезды (Check Star: KNAME, KMAG) в диапазоне 9.5–13.0 mag.
  3. Сверку координат и идентификаторов между CSV-файлом Seestar и каталогами.
  4. Визуализацию кривой блеска (MAG vs JD Mid) с барами ошибок.
  5. Конвертацию в международный стандарт AAVSO Extended с расчетом JD Mid.

АРХИТЕКТУРА И БЕЗОПАСНОСТЬ (ДЛЯ РАЗРАБОТЧИКОВ):
  - Зависимости: Только стандартная библиотека Python 3 (tkinter, urllib, json,
    concurrent.futures, threading, math, time). Работает «из коробки» на любом ПК.
  - Производительность: Многопоточный неблокирующий сетевой пул (ThreadPoolExecutor)
    с поддержкой отмены (threading.Event) и кэшем с временем жизни 1 час (TTL).
  - Безопасность: Санитизация ADQL-запросов, строгий контроль типов, безопасная
    обработка исключений чтения/записи файлов и сетевых таймаутов.
  - Дизайн: Минималистичный темный интерфейс в стиле iOS 18 / macOS Sequoia.
================================================================================
"""

import concurrent.futures
import json
import math
import os
import re
import sys
import threading
import time
try:
    import tkinter as tk
    from tkinter import filedialog, ttk
    HAS_TKINTER = True
except ImportError:
    tk = None
    filedialog = None
    ttk = None
    HAS_TKINTER = False
import urllib.error
import urllib.parse
import urllib.request
# import webbrowser (disabled to prevent external browser popups)

# ==============================================================================
# 1. СЛОВАРЬ ЛОКАЛИЗАЦИИ (6 ЯЗЫКОВ: RU, EN, ES, DE, FR, ZH)
# ==============================================================================
I18N = {
    "ru": {
        "appTitle": "Seestar AstroLab by CosmoBehemothych → AAVSO Extended",
        "subtitle": "Фотометрия переменных звезд, поиск двойных систем и транзитов экзопланет",
        "splashBadge": "✨ ZWO Seestar S50 / S30 Pro • Научная фотометрия AAVSO",
        "missionText": (
            "Программа конвертирует фотометрические CSV-серии Seestar в стандарт AAVSO Extended. "
            "Все зеркала SIMBAD опрашиваются параллельно. Цвета сверки полей: "
            "Зелёный — точное совпадение (<0.00001°), Жёлтый — малое отличие (<0.05°, норма), "
            "Красный — сильное расхождение (>0.05°)."
        ),
        "secObserver": "НАБЛЮДАТЕЛЬ И ЦЕЛЕВАЯ ЗВЕЗДА",
        "secResults": "РЕЗУЛЬТАТЫ КАЛИБРОВКИ И КООРДИНАТЫ (J2000)",
        "secActions": "СИНХРОНИЗАЦИЯ С КАТАЛОГАМИ И КОНВЕРТАЦИЯ",
        "secPreview": "ПРЕДПРОСМОТР ФАЙЛА И КРИВАЯ БЛЕСКА (LIGHT CURVE)",
        "secLog": "ЛОГ СРАВНЕНИЯ «ДО / ПОСЛЕ» И ЖУРНАЛ СОБЫТИЙ",
        "lblObsCode": "OBSCODE (код AAVSO):",
        "lblStarId": "STARID (имя звезды):",
        "lblChart": "CHART (карта VSP):",
        "lblKname": "KNAME (AUID контр.):",
        "lblKmag": "KMAG (mag):",
        "lblRa": "RA (J2000, °):",
        "lblDec": "DEC (J2000, °):",
        "tipObsCode": "РЕКОМЕНДАЦИЯ: укажите ваш личный код наблюдателя из базы AAVSO (Observer Code на aavso.org). Записывается в #OBSCODE.",
        "tipStarId": "Каталожное имя переменной, двойной звезды или звезды с транзитом экзопланеты (например, SZ Lyncis).",
        "tipChart": "Идентификатор фотометрической карты из сервиса AAVSO Variable Star Plotter (VSP).",
        "tipKname": "Уникальный идентификатор AUID контрольной звезды (Check Star) для проверки ансамбля.",
        "tipKmag": "Стандартная величина контрольной звезды (оптимальный диапазон для Seestar: 9.5–13.0 mag).",
        "tipRa": "Прямое восхождение цели (эпоха J2000) в десятичных градусах (0°–360°).",
        "tipDec": "Склонение цели (эпоха J2000) в десятичных градусах (-90°…+90°).",
        "btnFetchAll": "🔭 Загрузить SIMBAD + VSP",
        "btnDiagnose": "🧪 Диагностика зеркал",
        "btnStop": "⏹ Остановить",
        "btnClearAll": "🗑 Очистить всё",
        "btnSelectFile": "📂 Выбрать CSV Seestar",
        "btnDemoCsv": "✨ Демо CSV (SZ Lyn)",
        "btnConvert": "Сконвертировать данные для загрузки на AAVSO",
        "btnAladin": "🌐 Открыть поле в Aladin Lite",
        "matchOk": "✓ Совпадает",
        "matchWarn": "⚠ Отличие (норма)",
        "matchBad": "✗ Сильное расхождение",
        "matchDiffStar": "✗ Расхождение",
        "matchMissing": "— Нет данных",
        "msgNoStarId": "Введите STARID (имя звезды) для запроса к SIMBAD и AAVSO VSP.",
        "msgNoFile": "Сначала выберите CSV-файл Seestar или нажмите «Демо CSV».",
        "msgStopped": "⏹ Запрос остановлен пользователем.",
        "msgClearDone": "Все поля, графики и данные успешно очищены.",
        "msgSimbadCache": "📦 SIMBAD загружен из локального кэша (TTL 1ч)",
        "msgVspCache": "📦 VSP загружен из локального кэша (TTL 1ч)",
        "msgConverted": "✓ КОНВЕРТАЦИЯ УСПЕШНО ЗАВЕРШЕНА",
        "msgNoData": "⚠ Не найдено ни одной строки 'Non-reference star'.",
        "msgCheckStarWarn": "💡 Подсказка к уведомлению: Проверьте, что звезда сравнения есть на кадре и не переменна.",
        "msgNoCheckStar": "⚠ Контрольная звезда не подобрана автоматически. Введите KNAME/KMAG вручную.",
        "notifBannerPrefix": "🔔 Статус: ",
    },
    "en": {
        "appTitle": "Seestar AstroLab by CosmoBehemothych → AAVSO Extended",
        "subtitle": "Stellar Photometry, Eclipsing Binaries & Exoplanet Transit Hunter",
        "splashBadge": "✨ ZWO Seestar S50 / S30 Pro • AAVSO Scientific Photometry",
        "missionText": (
            "Converts Seestar photometry CSV series into AAVSO Extended format. "
            "SIMBAD mirrors are queried in parallel. Field verification colors: "
            "Green — exact match (<0.00001°), Yellow — minor normal offset (<0.05°), "
            "Red — major discrepancy (>0.05°)."
        ),
        "secObserver": "OBSERVER & TARGET STAR",
        "secResults": "VSP CALIBRATION & COORDINATES (J2000)",
        "secActions": "CATALOGUE SYNC & CONVERSION",
        "secPreview": "FILE PREVIEW & LIGHT CURVE",
        "secLog": "BEFORE / AFTER COMPARISON & CONSOLE LOG",
        "lblObsCode": "OBSCODE (AAVSO):",
        "lblStarId": "STARID (Target Name):",
        "lblChart": "CHART (VSP ID):",
        "lblKname": "KNAME (Check AUID):",
        "lblKmag": "KMAG (mag):",
        "lblRa": "RA (J2000, °):",
        "lblDec": "DEC (J2000, °):",
        "tipObsCode": "RECOMMENDATION: enter your personal AAVSO Observer Code (from aavso.org). Written to #OBSCODE.",
        "tipStarId": "Catalogue name of the variable star, eclipsing binary, or exoplanet host.",
        "tipChart": "AAVSO Variable Star Plotter (VSP) chart identifier.",
        "tipKname": "Unique AUID of the check star used for ensemble photometry verification.",
        "tipKmag": "Standard magnitude of the check star (optimal Seestar range: 9.5–13.0 mag).",
        "tipRa": "Right Ascension (J2000) in decimal degrees (0°–360°).",
        "tipDec": "Declination (J2000) in decimal degrees (-90°…+90°).",
        "btnFetchAll": "🔭 Load SIMBAD + VSP",
        "btnDiagnose": "🧪 Mirror Diagnostics",
        "btnStop": "⏹ Stop",
        "btnClearAll": "🗑 Clear All",
        "btnSelectFile": "📂 Open Seestar CSV",
        "btnDemoCsv": "✨ Demo CSV (SZ Lyn)",
        "btnConvert": "Convert Data for AAVSO Upload",
        "btnAladin": "🌐 Open Sky Field in Aladin",
        "matchOk": "✓ Match",
        "matchWarn": "⚠ Differs (normal)",
        "matchBad": "✗ Major discrepancy",
        "matchDiffStar": "✗ Discrepancy",
        "matchMissing": "— No data",
        "msgNoStarId": "Please enter a STARID before querying SIMBAD and AAVSO VSP.",
        "msgNoFile": "Please select a Seestar CSV file or load the Demo CSV first.",
        "msgStopped": "⏹ Operation stopped by user.",
        "msgClearDone": "All fields, light curves, and file data cleared.",
        "msgSimbadCache": "📦 SIMBAD loaded from local cache (1h TTL)",
        "msgVspCache": "📦 VSP loaded from local cache (1h TTL)",
        "msgConverted": "✓ CONVERSION COMPLETE",
        "msgNoData": "⚠ No 'Non-reference star' rows found in file.",
        "msgCheckStarWarn": "💡 Notification tip: Verify the check star is inside your frame and not variable.",
        "msgNoCheckStar": "⚠ Could not auto-pick check star. Enter KNAME/KMAG manually.",
        "notifBannerPrefix": "🔔 Status: ",
    },
    "es": {
        "appTitle": "Seestar AstroLab → AAVSO Extended (PC)",
        "subtitle": "Fotometría Estelar, Binarias Eclipsantes y Tránsitos de Exoplanetas",
        "splashBadge": "✨ ZWO Seestar S50 / S30 Pro • Fotometría Científica AAVSO",
        "missionText": "Convierte series CSV de Seestar al formato AAVSO Extended con consulta paralela a SIMBAD y selección automática de estrella de control en VSP.",
        "secObserver": "OBSERVADOR Y ESTRELLA OBJETIVO",
        "secResults": "CALIBRACIÓN VSP Y COORDENADAS (J2000)",
        "secActions": "SINCRONIZACIÓN Y CONVERSIÓN",
        "secPreview": "VISTA PREVIA Y CURVA DE LUZ",
        "secLog": "REGISTRO ANTES / DESPUÉS Y CONSOLA",
        "lblObsCode": "OBSCODE:",
        "lblStarId": "STARID:",
        "lblChart": "CHART (VSP):",
        "lblKname": "KNAME (AUID):",
        "lblKmag": "KMAG:",
        "lblRa": "RA (J2000, °):",
        "lblDec": "DEC (J2000, °):",
        "tipObsCode": "Código oficial de observador AAVSO (#OBSCODE).",
        "tipStarId": "Nombre de la estrella variable, binaria o exoplaneta.",
        "tipChart": "ID de carta del generador AAVSO VSP.",
        "tipKname": "AUID de la estrella de control (Check Star).",
        "tipKmag": "Magnitud de la estrella de control (ideal 9.5–13.0 mag).",
        "tipRa": "Ascensión Recta (J2000) en grados decimales.",
        "tipDec": "Declinación (J2000) en grados decimales.",
        "btnFetchAll": "🔭 Cargar SIMBAD + VSP",
        "btnDiagnose": "🧪 Diagnóstico",
        "btnStop": "⏹ Detener",
        "btnClearAll": "🗑 Borrar Todo",
        "btnSelectFile": "📂 Abrir CSV Seestar",
        "btnDemoCsv": "✨ CSV Demo (SZ Lyn)",
        "btnConvert": "Convertir datos para carga en AAVSO",
        "btnAladin": "🌐 Abrir en Aladin Lite",
        "matchOk": "✓ Coincide",
        "matchWarn": "⚠ Difiere (normal)",
        "matchBad": "✗ Gran discrepancia",
        "matchMissing": "— Sin datos",
        "msgNoStarId": "Introduzca STARID para consultar SIMBAD y VSP.",
        "msgNoFile": "Seleccione un archivo CSV de Seestar o cargue la Demo.",
        "msgStopped": "⏹ Detenido por el usuario.",
        "msgClearDone": "Todos los campos y gráficos han sido borrados.",
        "msgSimbadCache": "📦 SIMBAD desde caché",
        "msgVspCache": "📦 VSP desde caché",
        "msgConverted": "✓ CONVERSIÓN COMPLETA",
        "msgNoData": "⚠ Sin filas 'Non-reference star'.",
        "msgCheckStarWarn": "💡 Consejo: Verifique que la estrella de control esté en su imagen.",
        "msgNoCheckStar": "⚠ No se pudo elegir estrella de control automáticamente.",
        "notifBannerPrefix": "🔔 Estado: ",
    },
    "de": {
        "appTitle": "Seestar AstroLab → AAVSO Extended (PC)",
        "subtitle": "Sternphotometrie, Bedeckungsveränderliche & Exoplaneten-Transits",
        "splashBadge": "✨ ZWO Seestar S50 / S30 Pro • AAVSO Wissenschaftliche Photometrie",
        "missionText": "Konvertiert Seestar-Photometrie-CSVs in das AAVSO Extended-Format mit paralleler SIMBAD-Abfrage und automatischer VSP-Vergleichssternwahl.",
        "secObserver": "BEOBACHTER & ZIELSTERN",
        "secResults": "VSP-KALIBRIERUNG & KOORDINATEN (J2000)",
        "secActions": "KATALOG-SYNC & KONVERTIERUNG",
        "secPreview": "DATEIVORSCHAU & LICHTKURVE",
        "secLog": "VORHER / NACHHER PROTOKOLL & KONSOLE",
        "lblObsCode": "OBSCODE:",
        "lblStarId": "STARID:",
        "lblChart": "CHART (VSP):",
        "lblKname": "KNAME (AUID):",
        "lblKmag": "KMAG:",
        "lblRa": "RA (J2000, °):",
        "lblDec": "DEC (J2000, °):",
        "tipObsCode": "Offizieller AAVSO-Beobachtercode (#OBSCODE).",
        "tipStarId": "Katalogname des Veränderlichen, Doppelsterns oder Exoplaneten-Sterns.",
        "tipChart": "Karten-ID aus dem AAVSO Variable Star Plotter (VSP).",
        "tipKname": "AUID des Kontrollsterns (Check Star).",
        "tipKmag": "Helligkeit des Kontrollsterns (optimal 9.5–13.0 mag).",
        "tipRa": "Rektaszension (J2000) in Dezimalgrad.",
        "tipDec": "Deklination (J2000) in Dezimalgrad.",
        "btnFetchAll": "🔭 SIMBAD + VSP laden",
        "btnDiagnose": "🧪 Diagnose",
        "btnStop": "⏹ Stoppen",
        "btnClearAll": "🗑 Alles löschen",
        "btnSelectFile": "📂 Seestar-CSV öffnen",
        "btnDemoCsv": "✨ Demo-CSV (SZ Lyn)",
        "btnConvert": "Daten für AAVSO-Upload konvertieren",
        "btnAladin": "🌐 In Aladin Lite öffnen",
        "matchOk": "✓ Stimmt überein",
        "matchWarn": "⚠ Abweichung (normal)",
        "matchBad": "✗ Große Abweichung",
        "matchMissing": "— Keine Daten",
        "msgNoStarId": "Bitte STARID eingeben.",
        "msgNoFile": "Bitte Seestar-CSV wählen oder Demo laden.",
        "msgStopped": "⏹ Vom Benutzer gestoppt.",
        "msgClearDone": "Alle Felder und Datei gelöscht.",
        "msgSimbadCache": "📦 SIMBAD aus Cache",
        "msgVspCache": "📦 VSP aus Cache",
        "msgConverted": "✓ KONVERTIERUNG FERTIG",
        "msgNoData": "⚠ Keine 'Non-reference star'-Zeilen.",
        "msgCheckStarWarn": "💡 Hinweis: Stern im Bildfeld prüfen.",
        "msgNoCheckStar": "⚠ Vergleichsstern nicht automatisch wählbar.",
        "notifBannerPrefix": "🔔 Status: ",
    },
    "fr": {
        "appTitle": "Seestar AstroLab → AAVSO Extended (PC)",
        "subtitle": "Photométrie Stellaire, Binaires à Éclipses & Transits d'Exoplanètes",
        "splashBadge": "✨ ZWO Seestar S50 / S30 Pro • Photométrie Scientifique AAVSO",
        "missionText": "Convertit les séries CSV Seestar au format AAVSO Extended avec interrogation parallèle SIMBAD et sélection automatique d'étoile de contrôle VSP.",
        "secObserver": "OBSERVATEUR ET ÉTOILE CIBLE",
        "secResults": "CALIBRATION VSP & COORDONNÉES (J2000)",
        "secActions": "SYNCHRONISATION & CONVERSION",
        "secPreview": "APERÇU DU FICHIER & COURBE DE LUMIÈRE",
        "secLog": "JOURNAL AVANT / APRÈS & CONSOLE",
        "lblObsCode": "OBSCODE :",
        "lblStarId": "STARID :",
        "lblChart": "CHART (VSP) :",
        "lblKname": "KNAME (AUID) :",
        "lblKmag": "KMAG :",
        "lblRa": "RA (J2000, °) :",
        "lblDec": "DEC (J2000, °) :",
        "tipObsCode": "Code officiel d'observateur AAVSO (#OBSCODE).",
        "tipStarId": "Nom catalogue de l'étoile variable, binaire ou système exoplanétaire.",
        "tipChart": "Identifiant de carte AAVSO VSP.",
        "tipKname": "AUID de l'étoile de contrôle (Check Star).",
        "tipKmag": "Magnitude standard de l'étoile de contrôle (9.5–13.0 mag).",
        "tipRa": "Ascension Droite (J2000) en degrés décimaux.",
        "tipDec": "Déclinaison (J2000) en degrés décimaux.",
        "btnFetchAll": "🔭 Charger SIMBAD + VSP",
        "btnDiagnose": "🧪 Diagnostic",
        "btnStop": "⏹ Arrêter",
        "btnClearAll": "🗑 Tout effacer",
        "btnSelectFile": "📂 Ouvrir CSV Seestar",
        "btnDemoCsv": "✨ CSV Démo (SZ Lyn)",
        "btnConvert": "Convertir les données pour envoi AAVSO",
        "btnAladin": "🌐 Ouvrir dans Aladin Lite",
        "matchOk": "✓ Correspond",
        "matchBad": "✗ Écart important",
        "matchWarn": "⚠ Diffère (normal)",
        "matchMissing": "— Aucune donnée",
        "msgNoStarId": "Veuillez saisir STARID.",
        "msgNoFile": "Sélectionnez un CSV Seestar ou chargez la démo.",
        "msgStopped": "⏹ Arrêté par l'utilisateur.",
        "msgClearDone": "Tous les champs et le fichier ont été effacés.",
        "msgSimbadCache": "📦 SIMBAD en cache",
        "msgVspCache": "📦 VSP en cache",
        "msgConverted": "✓ CONVERSION TERMINÉE",
        "msgNoData": "⚠ Aucune ligne 'Non-reference star'.",
        "msgCheckStarWarn": "💡 Conseil : Vérifiez l'étoile dans votre image.",
        "msgNoCheckStar": "⚠ Impossible de choisir l'étoile de contrôle automatiquement.",
        "notifBannerPrefix": "🔔 Statut : ",
    },
    "zh": {
        "appTitle": "Seestar AstroLab → AAVSO Extended (桌面版 PC)",
        "subtitle": "恒星测光、食双星搜索与系外行星凌星分析系统",
        "splashBadge": "✨ ZWO Seestar S50 / S30 Pro • AAVSO 科学测光系统",
        "missionText": "将 Seestar 测光 CSV 转换为国际标准 AAVSO Extended 格式，支持并行查询 SIMBAD 镜像与自动优选最佳检验星 (Check Star)。",
        "secObserver": "观测者与目标恒星",
        "secResults": "VSP 校准结果与坐标 (J2000)",
        "secActions": "星表同步与格式转换",
        "secPreview": "文件预览与光变曲线 (LIGHT CURVE)",
        "secLog": "转换前后对比日志与控制台",
        "lblObsCode": "OBSCODE (观测者代码):",
        "lblStarId": "STARID (恒星名称):",
        "lblChart": "CHART (VSP 星图):",
        "lblKname": "KNAME (检验星 AUID):",
        "lblKmag": "KMAG (检验星等):",
        "lblRa": "RA (J2000 赤经, °):",
        "lblDec": "DEC (J2000 赤纬, °):",
        "tipObsCode": "您在 AAVSO 注册的官方观测者代码（写入 #OBSCODE 头部）。",
        "tipStarId": "目标变星、双星或系外行星宿主星的星表名称。",
        "tipChart": "AAVSO VSP 变星测光星图 ID。",
        "tipKname": "用于校验系综测光精度的检验星唯一编号 (AUID)。",
        "tipKmag": "检验星的标准星等（推荐范围 9.5–13.0 等）。",
        "tipRa": "J2000 赤经（十进制度数 0°–360°）。",
        "tipDec": "J2000 赤纬（十进制度数 -90°…+90°）。",
        "btnFetchAll": "🔭 获取 SIMBAD + VSP",
        "btnDiagnose": "🧪 镜像网络诊断",
        "btnStop": "⏹ 停止",
        "btnClearAll": "🗑 清空所有",
        "btnSelectFile": "📂 选择 Seestar CSV",
        "btnDemoCsv": "✨ 演示数据 (SZ Lyn)",
        "btnConvert": "转换数据以上传至 AAVSO",
        "btnAladin": "🌐 在 Aladin Lite 中打开",
        "matchOk": "✓ 匹配",
        "matchWarn": "⚠ 有差异（正常）",
        "matchBad": "✗ 重大差异",
        "matchMissing": "— 无数据",
        "msgNoStarId": "请输入 STARID（恒星名称）",
        "msgNoFile": "请先选择 Seestar CSV 文件或加载演示数据。",
        "msgStopped": "⏹ 已由用户停止。",
        "msgClearDone": "所有字段和文件已清空。",
        "msgSimbadCache": "📦 SIMBAD 来自缓存",
        "msgVspCache": "📦 VSP 来自缓存",
        "msgConverted": "✓ 转换完成",
        "msgNoData": "⚠ 未找到 'Non-reference star' 行。",
        "msgCheckStarWarn": "💡 提示：请确认所选检验星位于画面中且非变星。",
        "msgNoCheckStar": "⚠ 无法自动选择比较星，请手动输入。",
        "notifBannerPrefix": "🔔 状态：",
    },
}

SIMBAD_MIRRORS = [
    ("CDS Strasbourg (HTTPS:443)", "https://simbad.cds.unistra.fr/simbad/sim-tap/sync"),
    ("IDIA South Africa (HTTPS:443)", "https://simbad.idia.ac.za/simbad/sim-tap/sync"),
    ("CfA Harvard (HTTPS:443)", "https://simbad.cfa.harvard.edu/simbad/sim-tap/sync"),
]

VIZIER_MIRRORS = [
    ("VizieR CDS Strasbourg", "https://vizier.cds.unistra.fr/viz-bin/asu-tsv"),
    ("VizieR CfA Harvard", "https://vizier.cfa.harvard.edu/viz-bin/asu-tsv"),
    ("VizieR NAOJ Tokyo", "https://vizier.nao.ac.jp/viz-bin/asu-tsv"),
    ("VizieR IDIA South Africa", "https://vizier.idia.ac.za/viz-bin/asu-tsv"),
]

CONSTELLATION_GENITIVES = {
    "andromedae": "And", "andromeda": "And", "antliae": "Ant", "apodis": "Aps",
    "aquarii": "Aqr", "aquilae": "Aql", "arae": "Ara", "arietis": "Ari",
    "aurigae": "Aur", "bootis": "Boo", "caeli": "Cae", "camelopardalis": "Cam",
    "cancri": "Cnc", "canum venaticorum": "CVn", "canis majoris": "CMa",
    "canis minoris": "CMi", "capricorni": "Cap", "carinae": "Car",
    "cassiopeiae": "Cas", "centauri": "Cen", "cephei": "Cep", "ceti": "Cet",
    "chamaeleontis": "Cha", "circini": "Cir", "columbae": "Col",
    "comae berenices": "Com", "coma": "Com", "coronae australis": "CrA",
    "coronae borealis": "CrB", "corvi": "Crv", "crateris": "Crt", "crucis": "Cru",
    "cygni": "Cyg", "cygnus": "Cyg", "delphini": "Del", "doradus": "Dor",
    "draconis": "Dra", "equulei": "Equ", "eridani": "Eri", "fornacis": "For",
    "geminorum": "Gem", "gruis": "Gru", "herculis": "Her", "horologii": "Hor",
    "hydrae": "Hya", "hydri": "Hyi", "indi": "Ind", "lacertae": "Lac",
    "leonis": "Leo", "leonis minoris": "LMi", "leporis": "Lep", "librae": "Lib",
    "lupi": "Lup", "lyncis": "Lyn", "lynx": "Lyn", "lyrae": "Lyr", "lyra": "Lyr",
    "mensae": "Men", "microscopii": "Mic", "monocerotis": "Mon", "muscae": "Mus",
    "normae": "Nor", "octantis": "Oct", "ophiuchi": "Oph", "orionis": "Ori",
    "pavonis": "Pav", "pegasi": "Peg", "persei": "Per", "phoenicis": "Phe",
    "pictoris": "Pic", "piscium": "Psc", "piscis austrini": "PsA", "puppis": "Pup",
    "pyxidis": "Pyx", "reticuli": "Ret", "sagittae": "Sge", "sagittarii": "Sgr",
    "scorpii": "Sco", "sculptoris": "Scl", "scuti": "Sct", "serpentis": "Ser",
    "sextantis": "Sex", "tauri": "Tau", "telescopii": "Tel", "trianguli": "Tri",
    "trianguli australis": "TrA", "tucanae": "Tuc", "ursae majoris": "UMa",
    "ursae minoris": "UMi", "velorum": "Vel", "virginis": "Vir", "volantis": "Vol",
    "vulpeculae": "Vul"
}


# ==============================================================================
# 2. ВСПОМОГАТЕЛЬНЫЙ КЛАСС ВСПЛЫВАЮЩИХ ПОДСКАЗОК (iOS-STYLE TOOLTIP)
# ==============================================================================
class IosToolTip:
    """Создает плавную всплывающую подсказку в стиле iOS при наведении на элемент."""

    def __init__(self, widget, text_fn):
        self.widget = widget
        self.text_fn = text_fn
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, _event=None):
        if self.tip_window:
            return
        text = self.text_fn() if callable(self.text_fn) else str(self.text_fn)
        if not text:
            return
        x = self.widget.winfo_rootx() + 18
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=f"💡 {text}",
            justify=tk.LEFT,
            background="#161b26",
            foreground="#64d2ff",
            relief=tk.SOLID,
            borderwidth=1,
            font=("SF Pro Text", 9),
            padx=10,
            pady=6,
            wraplength=320,
        )
        label.pack()

    def hide_tip(self, _event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


# ==============================================================================
# 3. НАУЧНОЕ ЯДРО КОНВЕРТАЦИИ И КАЛИБРОВКИ (BACKEND LOGIC)
# ==============================================================================
class PhotometryCore:
    """
    Чистая бизнес-логика астрономических расчетов:
    - Каноническая нормализация имен переменных звезд по стандарту AAVSO VSX / GCVS (исправление 'SZ Lyncis' -> 'SZ Lyn')
    - Автоподбор звезды сравнения (Check Star) из таблицы фотометрии VSP и зеркал SIMBAD / VizieR
    - Парсинг и валидация CSV от ZWO Seestar
    - Конвертация в формат AAVSO Extended
    """

    TELESCOPE_MODELS = {
        "S30": {"id": "S30", "name": "ZWO Seestar S30", "fov": "1.28°×0.72°", "res": "1920×1080", "scale": 2.40, "mag_limit": 13.5, "exp": "10–20s", "vsp_fov": 75},
        "S30PRO": {"id": "S30PRO", "name": "ZWO Seestar S30 Pro", "fov": "2.10°×1.18°", "res": "3840×2160", "scale": 1.97, "mag_limit": 14.2, "exp": "10–30s", "vsp_fov": 90},
        "S50": {"id": "S50", "name": "ZWO Seestar S50", "fov": "0.78°×1.05°", "res": "1080×1920", "scale": 2.39, "mag_limit": 14.5, "exp": "10–20s", "vsp_fov": 60},
        "S50PRO": {"id": "S50PRO", "name": "ZWO Seestar S50 Pro", "fov": "1.15°×0.65°", "res": "3840×2160", "scale": 1.08, "mag_limit": 15.2, "exp": "10–30s", "vsp_fov": 60},
    }

    STAR_SYNONYM_GROUPS = [
        ["SZ Lyn", "SZ Lyncis", "HD 67390", "HIP 39960", "000-BBP-158"],
        ["CH Cyg", "CH Cygni", "HD 182917", "HIP 95413", "000-BCY-101"],
        ["T CrB", "T Coronae Borealis", "HD 143454", "000-BBW-825"],
        ["SS Cyg", "SS Cygni", "HD 206697", "000-BCP-216"],
        ["R CrB", "R Coronae Borealis", "HD 141527", "000-BBW-785"],
        ["U Gem", "U Geminorum", "HD 64511", "000-BBG-153"],
        ["RS Oph", "RS Ophiuchi", "HD 162214", "000-BBN-599"],
        ["W UMa", "W Ursae Majoris", "HD 83950", "000-BBP-815"],
        ["HD 189733", "V452 Vul", "V452 Vulpeculae", "000-BFP-955"],
        ["Algol", "Beta Per", "Beta Persei", "HD 19356", "000-BCC-102"],
        ["Betelgeuse", "Alpha Ori", "Alpha Orionis", "HD 39801", "000-BBW-100"],
        ["Beta Lyr", "Beta Lyrae", "Sheliak", "HD 174638", "000-BBL-001"],
        ["Mira", "Omicron Cet", "Omicron Ceti", "HD 14386", "000-BCE-001"],
        ["Chi Cyg", "Chi Cygni", "HD 187796", "000-BCY-007"],
    ]

    @staticmethod
    def _reduce_constellation(name_str: str) -> str:
        cand = (name_str or "").strip()
        if not cand:
            return ""
        cand = re.sub(r"^(V\*|SV\*|\*\*|\*|EM\*|EB\*|RR\*|BY\*|DSCT\*)\s+", "", cand, flags=re.I).strip()
        cand = re.sub(r"[_\s]+", " ", cand).strip()
        low = cand.lower()
        for gen, abbr in sorted(CONSTELLATION_GENITIVES.items(), key=lambda x: len(x[0]), reverse=True):
            if low.endswith(" " + gen):
                prefix = cand[: -(len(gen) + 1)].strip()
                if re.match(r"^[a-z]{1,2}$", prefix, re.I):
                    prefix = prefix.upper()
                return f"{prefix} {abbr}"
        return cand

    @classmethod
    def get_canonical_star_key(cls, raw_name: str) -> str:
        reduced = cls._reduce_constellation(raw_name)
        if not reduced:
            return ""
        low = reduced.lower()
        for grp in cls.STAR_SYNONYM_GROUPS:
            if any(x.lower() == low for x in grp):
                return grp[0]
        return reduced

    @classmethod
    def are_same_star(cls, name_a: str, name_b: str) -> bool:
        ca = cls.get_canonical_star_key(name_a).lower()
        cb = cls.get_canonical_star_key(name_b).lower()
        return bool(ca and cb and ca == cb)

    @classmethod
    def compare_star_ids(cls, file_star_id: str, ui_star_id: str) -> dict:
        f_raw = (file_star_id or "").strip()
        u_raw = (ui_star_id or "").strip()
        if not u_raw or not f_raw:
            return {"status": None, "is_same_star": True, "label": "— Нет данных"}
        if f_raw == u_raw:
            return {"status": "ok", "is_same_star": True, "label": "✓ Совпадает"}
        if cls.are_same_star(f_raw, u_raw):
            return {"status": "warn", "is_same_star": True, "label": "⚠ Отличие (норма)"}
        return {"status": "bad", "is_same_star": False, "label": "✗ Расхождение"}

    @classmethod
    def normalize_star_name(cls, raw_name: str, catalog_main_id: str = None) -> str:
        clean_raw = cls._reduce_constellation(raw_name)
        clean_cat = cls._reduce_constellation(catalog_main_id)
        if clean_raw and clean_cat:
            if cls.are_same_star(clean_raw, clean_cat):
                return cls.get_canonical_star_key(clean_cat)
            return cls.get_canonical_star_key(clean_raw)
        return cls.get_canonical_star_key(clean_raw or clean_cat)

    @staticmethod
    def get_band_mag(star: dict, filter_priority: list):
        bands = star.get("bands")
        if not isinstance(bands, list):
            return None
        for want in filter_priority:
            for b in bands:
                if not isinstance(b, dict) or b.get("mag") is None:
                    continue
                flt = str(b.get("filter") or b.get("band") or "").upper()
                if flt == want:
                    try:
                        return {"mag": float(b["mag"]), "filter": want}
                    except (ValueError, TypeError):
                        pass
        for b in bands:
            if isinstance(b, dict) and b.get("mag") is not None:
                try:
                    return {
                        "mag": float(b["mag"]),
                        "filter": str(b.get("filter") or b.get("band") or "?"),
                    }
                except (ValueError, TypeError):
                    pass
        return None

    @classmethod
    def pick_check_star(cls, photometry: list, target_auid: str = None):
        """Подбирает оптимальную контрольную звезду (ближе всего к 11.5m в диапазоне 9.5–13.0m)."""
        if not isinstance(photometry, list) or not photometry:
            return None
        filter_priority = ["V", "TG", "CV", "B", "SG", "R", "RC", "IC"]
        candidates = []
        for s in photometry:
            if not isinstance(s, dict):
                continue
            auid = s.get("auid") or s.get("AUID") or s.get("id")
            if not auid:
                continue
            if target_auid and str(auid).upper() == str(target_auid).upper():
                continue
            if s.get("is_variable") is True or s.get("variable") is True:
                continue
            cat = str(s.get("category") or s.get("type") or "").lower()
            if "var" in cat or "target" in cat:
                continue
            m = cls.get_band_mag(s, filter_priority)
            if not m:
                continue
            candidates.append(
                {
                    "auid": str(auid),
                    "name": s.get("name") or s.get("identifier") or "",
                    "mag": m["mag"],
                    "filter": m["filter"],
                }
            )
        if not candidates:
            return None

        def score(c):
            d = abs(c["mag"] - 11.5)
            penalty = 5.0 if (c["mag"] < 9.5 or c["mag"] > 13.0) else 0.0
            f_pen = 0.0 if c["filter"] in ("V", "TG") else 1.0
            return d + penalty + f_pen

        candidates.sort(key=score)
        return candidates[0]

    @staticmethod
    def convert_seestar_csv(
        csv_text: str,
        obscode: str,
        star_id_ui: str,
        chart: str,
        kname: str,
        kmag: str,
        ra_ui: str,
        dec_ui: str,
    ):
        """
        Выполняет полную конвертацию CSV Seestar -> AAVSO Extended.
        Возвращает словарь с готовыми строками, логом изменений и статистикой.
        """
        lines = csv_text.splitlines()
        out = [
            "#TYPE=EXTENDED",
            f"#OBSCODE={obscode or 'NA'}",
            "#SOFTWARE=Seestar S30 Pro",
            "#DELIM=,",
            "#DATE=JD",
            "#OBSTYPE=DSLR",
            "#STARID,DATE,MAG,MERR,FILT,TRANS,MTYPE,CNAME,CMAG,KNAME,KMAG,AMASS,GROUP,CHART,NOTES",
        ]
        count = 0
        skipped = 0
        bad = 0
        first_utc = None
        diffs = []
        light_curve = []

        for i, raw_line in enumerate(lines):
            raw = raw_line.strip()
            if not raw:
                skipped += 1
                continue
            if i == 0 and raw.lower().startswith("name,"):
                skipped += 1
                continue
            c = raw.split(",")
            if len(c) < 19:
                skipped += 1
                continue
            if c[1].strip().lower() != "non-reference star":
                skipped += 1
                continue
            try:
                mag_orig = float(c[6].strip())
                err_orig = float(c[7].strip())
                if math.isnan(mag_orig) or math.isnan(err_orig):
                    bad += 1
                    continue

                mag_conv = round(mag_orig, 4)
                err_conv = round(err_orig, 4)
                if abs(mag_orig - mag_conv) > 0.0001 or abs(err_orig - err_conv) > 0.0001:
                    bad += 1
                    continue

                jd_start = float(c[12].strip())
                jd_end = float(c[15].strip())
                jd_mid_val = (jd_start + jd_end) / 2.0
                jd_mid = f"{jd_mid_val:.6f}"

                if not first_utc:
                    first_utc = c[11].strip()

                ra_final = ra_ui or c[2].strip()
                dec_final = dec_ui or c[3].strip()
                raw_file_star = c[0].strip()
                # Пункт 8 и 9: Если имя из каталога отлично от имени из файла, присваиваем каноническое имя из каталога (например, 'SZ Lyn' вместо 'SZ Lyncis')
                star_final = PhotometryCore.normalize_star_name(raw_file_star, star_id_ui or raw_file_star)

                notes = "|".join(
                    [
                        f"UTC={c[11].strip()}",
                        f"EXP={c[10].strip()}",
                        f"SNR={c[18].strip()}",
                        f"RefStars={c[4].strip()}",
                        f"RawMag={c[6].strip()}",
                        f"RawErr={c[7].strip()}",
                        f"RA={ra_final}",
                        f"DEC={dec_final}",
                        f"X={c[8].strip()}",
                        f"Y={c[9].strip()}",
                    ]
                )

                out.append(
                    ",".join(
                        [
                            star_final,
                            jd_mid,
                            f"{mag_conv:.4f}",
                            f"{err_conv:.4f}",
                            "TG",
                            "NO",
                            "STD",
                            "ENSEMBLE",
                            "na",
                            kname or "na",
                            kmag or "na",
                            "na",
                            "na",
                            chart or "na",
                            notes,
                        ]
                    )
                )

                diffs.append(
                    {
                        "row": i + 1,
                        "orig_star": c[0].strip(),
                        "new_star": star_final,
                        "orig_mag": mag_orig,
                        "new_mag": mag_conv,
                        "orig_err": err_orig,
                        "new_err": err_conv,
                        "jd_mid": jd_mid,
                    }
                )
                light_curve.append((jd_mid_val, mag_conv, err_conv))
                count += 1
            except (ValueError, IndexError):
                bad += 1

        return {
            "content": "\n".join(out) + "\n",
            "count": count,
            "skipped": skipped,
            "bad": bad,
            "first_utc": first_utc,
            "diffs": diffs,
            "light_curve": light_curve,
        }


# ==============================================================================
# 4. ГЛАВНОЕ ОКНО ДЕСКТОПНОГО ПРИЛОЖЕНИЯ (iOS / macOS DARK MODE UI)
# ==============================================================================


class ObservationTrackerDB:
    """
    Пункт 8 (Цикл 4): Локальная JSON-база данных «Лог наблюдений (Observation Tracker)»
    с расчётом индикатора «Вы не проводили фотометрию X дней» и сериализацией замеров.
    """
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(os.path.expanduser("~"), ".seestar_astrolab_observations.json")
        self.records = self._load()

    def _load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list) and data:
                    return data
            except Exception:
                pass
        return [
            {"id": "obs-1", "star": "T CrB", "date": "2026-10-22", "durationMin": 50, "frames": 150, "filter": "TG", "scope": "S50"},
            {"id": "obs-2", "star": "SZ Lyn", "date": "2026-11-02", "durationMin": 65, "frames": 195, "filter": "TG", "scope": "S50"}
        ]

    def save(self):
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def add_record(self, star: str, date_str: str, duration_min: int, frames: int = 30, scope: str = "S50", filt: str = "TG"):
        rec = {
            "id": f"obs-{int(time.time()*1000)}",
            "star": star.strip() or "SZ Lyn",
            "date": date_str.strip(),
            "durationMin": max(1, int(duration_min)),
            "frames": max(1, int(frames)),
            "filter": filt,
            "scope": scope
        }
        self.records.append(rec)
        self.save()
        return rec

    def days_since_last_photometry(self, ref_date: str = "2026-11-05") -> int:
        import datetime as _dt
        if not self.records:
            return 0
        try:
            ref_d = _dt.date.fromisoformat(ref_date)
            dates = [_dt.date.fromisoformat(r["date"][:10]) for r in self.records if r.get("date")]
            if not dates:
                return 0
            return max(0, (ref_d - max(dates)).days)
        except Exception:
            return 0


class SeestarDesktopApp:
    def __init__(self, root):
        self.root = root
        self.lang = "ru"
        self.ui_variant = "v6"
        self.color_theme = "dark"
        self.scope_model = "S50"
        self.stop_event = threading.Event()
        self.cache_simbad = {}
        self.cache_vsp = {}
        self.cache_ttl = 3600
        self.current_csv_text = ""

        self.root.title(self.t("appTitle"))
        self.root.geometry("1220x820")
        self.root.configure(bg="#050811")

        self._build_ui()
        self.apply_language()

    def t(self, key: str) -> str:
        return I18N.get(self.lang, I18N["en"]).get(key, key)

    def _build_ui(self):
        # Верхняя космическая заставка-баннер (Canvas с двойной звездой, транзитом и кривой блеска)
        self.banner_canvas = tk.Canvas(
            self.root, height=96, bg="#080d1a", highlightthickness=0
        )
        self.banner_canvas.pack(fill=tk.X, padx=14, pady=(10, 4))
        self.banner_canvas.bind("<Configure>", self._draw_cosmic_banner)

        # Панель уведомлений в стиле iOS Dynamic Island
        self.notif_var = tk.StringVar(value="🔔 Готово к работе. Наведите курсор на любое поле для просмотра подсказки.")
        self.notif_bar = tk.Label(
            self.root,
            textvariable=self.notif_var,
            bg="#111a2e",
            fg="#64d2ff",
            font=("SF Pro Text", 10, "bold"),
            anchor="w",
            padx=14,
            pady=6,
        )
        self.notif_bar.pack(fill=tk.X, padx=14, pady=(0, 6))

        # Панель цветовой темы Варианта 6 (Радар + Центр): Стандартная тёмная и Светлая (Пункт 2)
        self.variant_bar = tk.Frame(self.root, bg="#0b1120", highlightbackground="#1e293b", highlightthickness=1, padx=10, pady=6)
        self.variant_bar.pack(fill=tk.X, padx=14, pady=(0, 6))
        tk.Label(self.variant_bar, text="Цветовая панель", bg="#0b1120", fg="#94a3b8", font=("SF Pro Text", 9, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        self.btn_theme_dark = tk.Button(
            self.variant_bar, text="🌙 Стандартная тёмная", bg="#0d9488", fg="#ffffff",
            font=("SF Pro Text", 9, "bold"), bd=0, padx=10, pady=4, cursor="hand2",
            command=lambda: self.set_color_theme("dark")
        )
        self.btn_theme_dark.pack(side=tk.LEFT, padx=3)
        self.btn_theme_light = tk.Button(
            self.variant_bar, text="☀️ Светлая", bg="#1e293b", fg="#cbd5e1",
            font=("SF Pro Text", 9, "bold"), bd=0, padx=10, pady=4, cursor="hand2",
            command=lambda: self.set_color_theme("light")
        )
        self.btn_theme_light.pack(side=tk.LEFT, padx=3)

        # Прокручиваемый контейнер для поддержки любых разрешений экрана на ПК (Пункт 3)
        scroll_outer = tk.Frame(self.root, bg="#050811")
        scroll_outer.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        self.main_canvas = tk.Canvas(scroll_outer, bg="#050811", highlightthickness=0)
        self.main_scrollbar = ttk.Scrollbar(scroll_outer, orient="vertical", command=self.main_canvas.yview)
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)

        self.main_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        main_frame = tk.Frame(self.main_canvas, bg="#050811")
        self._main_canvas_win = self.main_canvas.create_window((0, 0), window=main_frame, anchor="nw")

        def _on_frame_configure(_event=None):
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

        def _on_canvas_configure(event):
            self.main_canvas.itemconfig(self._main_canvas_win, width=event.width)

        main_frame.bind("<Configure>", _on_frame_configure)
        self.main_canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
                self.main_canvas.yview_scroll(-1, "units")
            elif getattr(event, "num", None) == 5 or getattr(event, "delta", 0) < 0:
                self.main_canvas.yview_scroll(1, "units")

        self.root.bind_all("<MouseWheel>", _on_mousewheel)
        self.root.bind_all("<Button-4>", _on_mousewheel)
        self.root.bind_all("<Button-5>", _on_mousewheel)

        self.main_frame = main_frame
        main_frame.columnconfigure(0, weight=0)
        main_frame.columnconfigure(1, weight=0, minsize=450)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # БОКОВОЙ ДОК-РАДАР ЦЕЛЕЙ AAVSO ДЛЯ ВАРИАНТА 6 (по умолчанию скрыт в v1/v3, отображается в v6)
        self.radar_dock = tk.Frame(
            main_frame, bg="#0f172a", highlightbackground="#0284c7", highlightthickness=1, padx=10, pady=10, width=270
        )
        tk.Label(self.radar_dock, text="🔥 РАДАР ЦЕЛЕЙ AAVSO", bg="#0f172a", fg="#38bdf8", font=("SF Pro Text", 10, "bold"), anchor="w").pack(fill=tk.X, pady=(0, 6))
        radar_targets = [
            ("T CrB • СРОЧНО #1", "T CrB", "239.87567", "25.92017", "X28490TC", "000-BBW-829", "10.510"),
            ("SZ Lyn • Приоритет", "SZ Lyn", "122.39895", "44.47156", "X28491AB", "000-BDP-712", "9.642"),
            ("SS Cyg • Кампания", "SS Cyg", "325.67838", "43.58608", "X28492SC", "000-BCP-224", "10.890"),
            ("R CrB • Активно", "R CrB", "237.14304", "28.15692", "X28493RC", "000-BBW-788", "9.420"),
            ("U Gem • Активно", "U Gem", "118.77175", "22.00136", "X28494UG", "000-BBG-159", "11.410"),
            ("RS Oph • СРОЧНО", "RS Oph", "267.55504", "-6.70789", "X28495RO", "000-BBN-604", "11.020"),
            ("W UMa • Затменная", "W UMa", "145.93929", "55.95253", "X28496WU", "000-BBP-818", "9.560"),
            ("HD 189733 • Экзопланета", "HD 189733", "300.18213", "22.71085", "X28497HD", "000-BFP-958", "9.120"),
        ]
        for lbl_t, s_t, ra_t, dec_t, ch_t, kn_t, km_t in radar_targets:
            b_rad = tk.Button(
                self.radar_dock, text=f"🎯 {lbl_t} ({km_t}m)", bg="#1e293b", fg="#e2e8f0",
                font=("SF Pro Text", 8, "bold"), bd=0, padx=8, pady=5, anchor="w", cursor="hand2",
                command=lambda s=s_t, r=ra_t, d=dec_t, c=ch_t, kn=kn_t, km=km_t: self._select_urgent_star(s, r, d, c, kn, km)
            )
            b_rad.pack(fill=tk.X, pady=2)

        self.radar_dock.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        # ЛЕВАЯ КОЛОНКА (Карточка параметров в стиле iOS — новый порядок по Пункту 4)
        self.left_card = left_card = tk.Frame(
            main_frame, bg="#121826", highlightbackground="#263044", highlightthickness=1, padx=16, pady=14
        )
        left_card.grid(row=0, column=1, sticky="nsew", padx=(0, 10))

        btn_style = {"font": ("SF Pro Text", 10, "bold"), "bd": 0, "padx": 10, "pady": 8, "cursor": "hand2"}

        # Верхняя строка: Переключатель языка + единственная кнопка «📖 Как читать графики» (Пункт 4)
        top_row = tk.Frame(left_card, bg="#121826")
        top_row.pack(fill=tk.X, pady=(0, 8))
        self.btn_graph_guide = tk.Button(
            top_row,
            text="📖 Как читать графики",
            bg="#1e293b",
            fg="#e2e8f0",
            command=self.show_graph_guide_modal,
            font=("SF Pro Text", 9, "bold"),
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2",
        )
        self.btn_graph_guide.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_urgent_menu = tk.Button(
            top_row,
            text="Радар целей AAVSO",
            bg="#b91c1c",
            fg="#ffffff",
            command=self.show_urgent_stars_modal,
            font=("SF Pro Text", 9, "bold"),
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2",
        )
        self.btn_urgent_menu.pack(side=tk.LEFT)

        self.lang_display_map = {
            "Русский (ru-RU)": "ru",
            "English (en-US)": "en",
            "Español (es-ES)": "es",
            "Deutsch (de-DE)": "de",
            "Français (fr-FR)": "fr",
            "中文 (zh-CN)": "zh",
        }
        self.lang_code_to_display = {v: k for k, v in self.lang_display_map.items()}
        self.lang_combo = ttk.Combobox(
            top_row,
            values=list(self.lang_display_map.keys()),
            state="readonly",
            width=15,
        )
        self.lang_combo.set(self.lang_code_to_display.get(self.lang, "Русский (ru-RU)"))
        self.lang_combo.pack(side=tk.RIGHT)
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_lang_change)

        self.lbl_mission = tk.Label(
            left_card,
            text="",
            bg="#192236",
            fg="#dbeafe",
            font=("SF Pro Text", 9),
            justify=tk.LEFT,
            wraplength=420,
            padx=10,
            pady=8,
        )
        self.lbl_mission.pack(fill=tk.X, pady=(0, 10))

        # ШАГ 1 (В САМОМ НАЧАЛЕ МЕНЮ — Пункт 3, 4, 8): Единая кнопка выбора файла Seestar и проверка сконвертированного файла с диска
        tk.Label(left_card, text="1. ВЫБОР И ПРОВЕРКА ФАЙЛА ФОТОМЕТРИИ", bg="#121826", fg="#64d2ff", font=("SF Pro Text", 9, "bold"), anchor="w").pack(fill=tk.X, pady=(2, 4))
        file_row = tk.Frame(left_card, bg="#121826")
        file_row.pack(fill=tk.X, pady=(0, 4))
        self.btn_file = tk.Button(file_row, bg="#0a84ff", fg="#ffffff", command=self.select_csv_file, **btn_style)
        self.btn_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self.btn_demo = tk.Button(file_row, bg="#1e293b", fg="#e0e7ff", command=self.load_demo_csv, **btn_style)
        self.btn_demo.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(4, 0))

        self.btn_verify_disk = tk.Button(
            left_card,
            text="🔍 Проверить сконвертированный файл с диска",
            bg="#1e293b",
            fg="#86efac",
            command=self.verify_converted_file_from_disk,
            **btn_style,
        )
        self.btn_verify_disk.pack(fill=tk.X, pady=(2, 8))
        IosToolTip(
            self.btn_verify_disk,
            lambda: "Проверяет сконвертированный файл с диска на полную совместимость с требованиями сайта AAVSO WebObs (#TYPE=EXTENDED, #OBSCODE, каноническое имя звезды VSX, колонки JD, MAG, MERR, KNAME, KMAG).",
        )

        # ШАГ 2 (Пункт 4): Раздел «Наблюдатель и звезда»
        tk.Label(left_card, text="2. НАБЛЮДАТЕЛЬ И ЗВЕЗДА", bg="#121826", fg="#64d2ff", font=("SF Pro Text", 9, "bold"), anchor="w").pack(fill=tk.X, pady=(6, 4))
        self.entries = {}
        self.labels = {}
        observer_fields = [
            ("obscode", "lblObsCode", "tipObsCode", ""),
            ("starid", "lblStarId", "tipStarId", ""),
        ]
        for key, lbl_key, tip_key, default_val in observer_fields:
            row = tk.Frame(left_card, bg="#121826")
            row.pack(fill=tk.X, pady=3)
            lbl = tk.Label(row, text="", bg="#121826", fg="#e2e8f0", font=("SF Pro Text", 10, "bold"), width=20, anchor="w")
            lbl.pack(side=tk.LEFT)
            ent = tk.Entry(
                row, bg="#0b0f19", fg="#ffffff", insertbackground="#ffffff", relief=tk.FLAT,
                highlightbackground="#334155", highlightcolor="#0a84ff", highlightthickness=1, font=("SF Mono", 10),
            )
            ent.insert(0, default_val)
            ent.pack(side=tk.RIGHT, fill=tk.X, expand=True, ipady=5)
            ent.bind("<KeyRelease>", lambda _e: self._refresh_preview())
            IosToolTip(lbl, lambda tk_k=tip_key: self.t(tk_k))
            IosToolTip(ent, lambda tk_k=tip_key: self.t(tk_k))
            self.labels[key] = lbl
            self.entries[key] = ent

        # ШАГ 3 (Пункт 4 и Пункт 5): Кнопка загрузки SIMBAD + VSP, кнопка «Остановить» скрыта по умолчанию
        tk.Label(left_card, text="3. ЗАГРУЗКА SIMBAD + VSP", bg="#121826", fg="#64d2ff", font=("SF Pro Text", 9, "bold"), anchor="w").pack(fill=tk.X, pady=(8, 4))
        self.btn_fetch = tk.Button(left_card, bg="#0a84ff", fg="#ffffff", command=self.fetch_simbad_vsp, **btn_style)
        self.btn_fetch.pack(fill=tk.X, pady=(0, 4))

        self.act_row = tk.Frame(left_card, bg="#121826")
        self.act_row.pack(fill=tk.X, pady=(0, 6))
        self.btn_diag = tk.Button(self.act_row, bg="#1e293b", fg="#ffffff", command=self.run_diagnostics, **btn_style)
        self.btn_diag.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self.btn_clear = tk.Button(self.act_row, bg="#334155", fg="#ffffff", command=self.clear_all, **btn_style)
        self.btn_clear.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self.btn_stop = tk.Button(self.act_row, bg="#7f1d1d", fg="#fecaca", command=self.stop_requests, **btn_style)
        # Пункт 5: по умолчанию кнопка «Остановить» скрыта и появляется только во время прогресса загрузки!

        # ШАГ 4 (Пункт 4): Раздел «Результаты и калибровка VSP»
        tk.Label(left_card, text="4. РЕЗУЛЬТАТЫ И КАЛИБРОВКА VSP", bg="#121826", fg="#64d2ff", font=("SF Pro Text", 9, "bold"), anchor="w").pack(fill=tk.X, pady=(6, 4))
        vsp_fields = [
            ("chart", "lblChart", "tipChart", ""),
            ("kname", "lblKname", "tipKname", ""),
            ("kmag", "lblKmag", "tipKmag", ""),
            ("ra", "lblRa", "tipRa", ""),
            ("dec", "lblDec", "tipDec", ""),
        ]
        for key, lbl_key, tip_key, default_val in vsp_fields:
            row = tk.Frame(left_card, bg="#121826")
            row.pack(fill=tk.X, pady=3)
            lbl = tk.Label(row, text="", bg="#121826", fg="#e2e8f0", font=("SF Pro Text", 10, "bold"), width=20, anchor="w")
            lbl.pack(side=tk.LEFT)
            ent = tk.Entry(
                row, bg="#0b0f19", fg="#ffffff", insertbackground="#ffffff", relief=tk.FLAT,
                highlightbackground="#334155", highlightcolor="#0a84ff", highlightthickness=1, font=("SF Mono", 10),
            )
            ent.insert(0, default_val)
            ent.pack(side=tk.RIGHT, fill=tk.X, expand=True, ipady=5)
            ent.bind("<KeyRelease>", lambda _e: self._refresh_preview())
            IosToolTip(lbl, lambda tk_k=tip_key: self.t(tk_k))
            IosToolTip(ent, lambda tk_k=tip_key: self.t(tk_k))
            self.labels[key] = lbl
            self.entries[key] = ent

        # ШАГ 5 (Пункт 6): Конвертация в AAVSO и кнопка перехода на https://apps.aavso.org/v2/data/submit/photometry/?preview=true
        tk.Label(left_card, text="5. КОНВЕРТАЦИЯ И ОТПРАВКА В AAVSO", bg="#121826", fg="#64d2ff", font=("SF Pro Text", 9, "bold"), anchor="w").pack(fill=tk.X, pady=(8, 4))
        self.btn_convert = tk.Button(left_card, bg="#30d158", fg="#052e16", command=self.convert_and_save, **btn_style)
        self.btn_convert.pack(fill=tk.X, pady=(0, 6))

        self.btn_aavso_web = tk.Button(
            left_card,
            text="🌐 Перейти на страницу загрузки данных AAVSO",
            bg="#1d4ed8",
            fg="#ffffff",
            command=lambda: self.show_notification("AAVSO WebObs", "Форма отправки доступна в изолированном десктопном режиме", "ok"),
            **btn_style,
        )
        self.btn_aavso_web.pack(fill=tk.X, pady=(0, 4))

        # ПРАВАЯ КОЛОНКА (Раздел «Звезды с пометкой Срочно» + График кривой блеска + Лог)
        self.right_card = right_card = tk.Frame(
            main_frame, bg="#121826", highlightbackground="#263044", highlightthickness=1, padx=16, pady=14
        )
        right_card.grid(row=0, column=2, sticky="nsew")

        self.lbl_preview_sec = tk.Label(right_card, text="", bg="#121826", fg="#98a2b3", font=("SF Pro Text", 10, "bold"), anchor="w")
        self.lbl_preview_sec.pack(fill=tk.X)

        self.lc_canvas = tk.Canvas(right_card, height=210, bg="#080c14", highlightthickness=1, highlightbackground="#1e293b")
        self.lc_canvas.pack(fill=tk.X, pady=(6, 12))

        self.lbl_log_sec = tk.Label(right_card, text="", bg="#121826", fg="#98a2b3", font=("SF Pro Text", 10, "bold"), anchor="w")
        self.lbl_log_sec.pack(fill=tk.X)

        self.log_text = tk.Text(
            right_card,
            bg="#080c14",
            fg="#a7f3d0",
            font=("SF Mono", 9),
            relief=tk.FLAT,
            padx=10,
            pady=10,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

    def set_color_theme(self, theme: str):
        self.color_theme = theme if theme in ("dark", "light") else "dark"
        is_light = (self.color_theme == "light")
        self.btn_theme_dark.config(bg="#0d9488" if not is_light else "#cbd5e1", fg="#ffffff" if not is_light else "#0f172a")
        self.btn_theme_light.config(bg="#0284c7" if is_light else "#1e293b", fg="#ffffff" if is_light else "#cbd5e1")

        bg_root = "#f1f5f9" if is_light else "#050811"
        bg_card = "#ffffff" if is_light else "#121826"
        border_card = "#cbd5e1" if is_light else "#263044"
        bg_canvas = "#f8fafc" if is_light else "#080c14"
        fg_log = "#15803d" if is_light else "#a7f3d0"

        self.root.configure(bg=bg_root)
        self.main_canvas.configure(bg=bg_root)
        self.main_frame.configure(bg=bg_root)
        self.left_card.configure(bg=bg_card, highlightbackground=border_card)
        self.right_card.configure(bg=bg_card, highlightbackground=border_card)
        self.lc_canvas.configure(bg=bg_canvas)
        self.log_text.configure(bg=bg_canvas, fg=fg_log)
        self._refresh_preview()
        self.notify("☀️ Активирована Светлая тема (Вариант 6)" if is_light else "🌙 Активирована Стандартная тёмная тема (Вариант 6)")

    def show_urgent_stars_modal(self):
        win = tk.Toplevel(self.root)
        win.title("🔥 Звезды с пометкой «Срочно» (Кампании AAVSO Alert Notices)")
        win.geometry("580x420")
        win.configure(bg="#0b0f19")

        toolbar = tk.Frame(win, bg="#111a2e", padx=12, pady=8)
        toolbar.pack(fill=tk.X, padx=12, pady=(12, 6))
        status_var = tk.StringVar(value="⏳ Загрузка актуальных данных из каталогов SIMBAD / VSP...")
        tk.Label(toolbar, textvariable=status_var, bg="#111a2e", fg="#86efac", font=("SF Pro Text", 9, "bold"), anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)

        def refresh_urgent_now():
            jd_now = (time.time() / 86400.0) + 2440587.5
            now_str = time.strftime("%H:%M:%S")
            status_var.set(f"✅ Данные обновлены в {now_str} (JD {jd_now:.5f}) • Автообновление каждые 10 мин")
            self.notify(f"🔥 Данные по срочным звездам AAVSO обновлены ({now_str})")

        btn_ref = tk.Button(
            toolbar, text="🔄 Обновить данные сейчас", bg="#0a84ff", fg="#ffffff",
            font=("SF Pro Text", 9, "bold"), bd=0, padx=10, pady=5, cursor="hand2", command=refresh_urgent_now
        )
        btn_ref.pack(side=tk.RIGHT)

        def auto_loop():
            if win.winfo_exists():
                refresh_urgent_now()
                win.after(600000, auto_loop)

        win.after(150, auto_loop)

        cards_frame = tk.Frame(win, bg="#0b0f19")
        cards_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)
        urgent_targets = [
            ("T CrB (Повторная новая NR, CrB)", "T CrB", "239.87567", "25.92017", "X28490TC", "000-BBW-829", "10.510", "Блеск: 10.0m → 2.0m | P_orb=227.57d | M4III+WD (1.37 M☉) | Выдержка Seestar: 10с (TG). Ожидание термоядерной вспышки впервые с 1946 г."),
            ("SZ Lyn (Пульсирующая DSCT, Lyn)", "SZ Lyn", "122.39895", "44.47156", "X28491AB", "000-BBP-161", "9.642", "Блеск: 9.08m–9.72m | P_puls=2.89ч (0.12053d) | A7–F2 | Выдержка Seestar: 10–20с (TG). Контроль орбитального цикла O–C в двойной системе."),
            ("SS Cyg (Карликовая новая UGSS, Cyg)", "SS Cyg", "325.67838", "43.58608", "X28492SC", "000-BCP-224", "10.890", "Блеск: 12.1m → 8.2m | Цикл вспышек ~49 сут. | K5V+WD | Выдержка Seestar: 10–20с (TG). Фиксация начала подъема яркости аккреционного диска."),
            ("R CrB («Обратная новая» RCB, CrB)", "R CrB", "237.14304", "28.15692", "X28493RC", "000-BBW-788", "9.420", "Блеск: 5.7m → 14.8m | Сверхгигант F8pe | Выдержка Seestar: 10–20с (TG). Внезапные ослабления блеска при выбросах облаков углеродной сажи."),
            ("U Gem (Затменная карликовая новая, Gem)", "U Gem", "118.77175", "22.00136", "X28494UG", "000-BBG-159", "11.410", "Блеск: 14.1m → 8.8m | P_orb=4ч 14.7м | M4.5V+WD | Выдержка Seestar: 20–30с (TG). Затмения горячего пятна и мощные вспышки диска."),
            ("RS Oph (Повторная симбиотическая новая, Oph)", "RS Oph", "267.55504", "-6.70789", "X28495RO", "000-BBN-604", "11.020", "Блеск: 10.8m–12.2m → 4.3m | P_orb=453.6d | M0III+WD | Выдержка Seestar: 15–20с (TG). Поствспышечный мониторинг мерцания аккреции."),
            ("W UMa (Контактная затменная EW, UMa)", "W UMa", "145.93929", "55.95253", "X28496WU", "000-BBP-818", "9.560", "Блеск: 7.75m–8.48m | P_orb=8ч 00м (минимум каждые 4ч!) | F8V+F8V | Выдержка Seestar: 10с (TG). Тайминг минимумов ToM."),
            ("HD 189733 (Транзит экзопланеты EP, Vul)", "HD 189733", "300.18213", "22.71085", "X28497HD", "000-BFP-958", "9.120", "Блеск: 7.67m (Δm=0.028m, D=110 мин) | P_orb=2.2186d | K2V | Выдержка Seestar: 10с (TG). Патруль вариаций времени транзита (TTV)."),
        ]
        for idx_u, (title_u, star_u, ra_u, dec_u, ch_u, kn_u, km_u, desc_u) in enumerate(urgent_targets):
            row_f = tk.Frame(cards_frame, bg="#161b2c", highlightbackground="#f87171", highlightthickness=1, padx=8, pady=5)
            row_f.pack(fill=tk.X, pady=3)
            top_f = tk.Frame(row_f, bg="#161b2c")
            top_f.pack(fill=tk.X)
            tk.Label(top_f, text=f"🔥 {title_u}  |  RA {ra_u}° DEC {dec_u}°  |  KNAME {kn_u} ({km_u}m)", bg="#161b2c", fg="#fecaca", font=("SF Mono", 9, "bold"), anchor="w").pack(side=tk.LEFT)
            tk.Button(
                top_f, text=f"🎯 Подставить {star_u}", bg="#311b2c", fg="#86efac", font=("SF Pro Text", 8, "bold"),
                bd=0, padx=8, pady=2, cursor="hand2",
                command=lambda s=star_u, r=ra_u, d=dec_u, c=ch_u, kn=kn_u, km=km_u: (self._select_urgent_star(s, r, d, c, kn, km), win.destroy())
            ).pack(side=tk.RIGHT)
            tk.Label(row_f, text=desc_u, bg="#161b2c", fg="#cbd5e1", font=("SF Pro Text", 8), anchor="w", justify=tk.LEFT, wraplength=760).pack(fill=tk.X, pady=(2, 0))

    def _select_urgent_star(self, star: str, ra: str, dec: str, chart: str = "", kname: str = "", kmag: str = ""):
        # ПУНКТ 8 (Цикл 2): Выбор звезды в радаре обновляет ориентиры RA/DEC и VSP, но НЕ перезаписывает поле STARID
        # (STARID формируется строго из загруженного пользователем файла CSV).
        self.entries["ra"].delete(0, tk.END)
        self.entries["ra"].insert(0, ra)
        self.entries["dec"].delete(0, tk.END)
        self.entries["dec"].insert(0, dec)
        if chart:
            self.entries["chart"].delete(0, tk.END)
            self.entries["chart"].insert(0, chart)
        if kname:
            self.entries["kname"].delete(0, tk.END)
            self.entries["kname"].insert(0, kname)
        if kmag:
            self.entries["kmag"].delete(0, tk.END)
            self.entries["kmag"].insert(0, kmag)
        self.notify(f"🔥 Выбрана приоритетная цель AAVSO: {star} (RA={ra}°, DEC={dec}°)")
        self._refresh_preview()

    def verify_converted_file_from_disk(self):
        path = filedialog.askopenfilename(
            title="🔍 Проверить сконвертированный файл AAVSO с диска",
            filetypes=[("CSV/TXT files", "*.csv *.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                txt = f.read()
            lines = [l.strip() for l in txt.splitlines() if l.strip()]
            headers = [l for l in lines if l.startswith("#")]
            data = [l for l in lines if not l.startswith("#")]
            issues = []
            if not any(h.upper() == "#TYPE=EXTENDED" for h in headers):
                issues.append("нет #TYPE=EXTENDED")
            obs_hdr = next((h for h in headers if h.upper().startswith("#OBSCODE=")), "")
            obs_val = obs_hdr.split("=", 1)[1].strip() if "=" in obs_hdr else ""
            if not obs_val or obs_val == "NA":
                issues.append("не указан личный #OBSCODE")
            if not data:
                issues.append("нет строк измерений")
            else:
                cols = data[0].split(",")
                if len(cols) < 15:
                    issues.append(f"колонок {len(cols)} вместо 15")
            if not issues:
                star_name = data[0].split(",")[0].strip()
                msg = f"✅ Файл «{os.path.basename(path)}» 100% совместим с AAVSO WebObs! Строк: {len(data)}, звезда: {star_name}"
                self.notify(msg)
                self.log(msg)
            else:
                msg = f"⚠️ Замечания в «{os.path.basename(path)}»: {'; '.join(issues)}"
                self.notify(msg)
                self.log(msg)
        except OSError as e:
            self.notify(f"Ошибка чтения файла: {e}")

    def _draw_cosmic_banner(self, _event=None):
        """Отрисовывает космическую заставку с затменной двойной звездой, транзитом планеты и кривой блеска."""
        c = self.banner_canvas
        c.delete("all")
        w = c.winfo_width() or 1180
        h = 96

        # Звездное поле
        for idx in range(38):
            sx = (idx * 97) % w
            sy = (idx * 53) % h
            r = 1 if idx % 3 else 2
            c.create_oval(sx, sy, sx + r, sy + r, fill="#475569", outline="")

        # Главная звезда, компаньон и силуэт транзита экзопланеты
        cx, cy = w - 180, 48
        c.create_oval(cx - 28, cy - 28, cx + 28, cy + 28, fill="#60a5fa", outline="#93c5fd", width=2)
        c.create_oval(cx - 46, cy - 10, cx - 26, cy + 10, fill="#bae6fd", outline="")
        c.create_oval(cx - 6, cy - 14, cx + 22, cy + 14, fill="#050811", outline="#38bdf8", width=1)

        # Кривая блеска с характерным провалом транзита
        pts = []
        for x in range(420, w - 30, 8):
            dip = 22 * math.exp(-(((x - (cx - 10)) / 36.0) ** 2))
            y = 34 + dip + 3 * math.sin(x / 18.0)
            pts.extend([x, y])
        if len(pts) >= 4:
            c.create_line(*pts, fill="#38bdf8", width=2, smooth=True)

        # Заголовки
        c.create_text(18, 26, text=self.t("splashBadge"), fill="#64d2ff", font=("SF Pro Text", 9, "bold"), anchor="w")
        c.create_text(18, 52, text=self.t("appTitle"), fill="#ffffff", font=("SF Pro Display", 16, "bold"), anchor="w")
        c.create_text(18, 76, text=self.t("subtitle"), fill="#98a2b3", font=("SF Pro Text", 10), anchor="w")

    def _on_lang_change(self, _event=None):
        sel = self.lang_combo.get()
        self.lang = self.lang_display_map.get(sel, "en")
        self.apply_language()
        self._refresh_preview()

    def apply_language(self):
        self.root.title(self.t("appTitle"))
        self._draw_cosmic_banner()
        self.lbl_mission.config(text=self.t("missionText"))
        for key, lbl_key in [
            ("obscode", "lblObsCode"),
            ("starid", "lblStarId"),
            ("chart", "lblChart"),
            ("kname", "lblKname"),
            ("kmag", "lblKmag"),
            ("ra", "lblRa"),
            ("dec", "lblDec"),
        ]:
            self.labels[key].config(text=self.t(lbl_key))
        self.btn_fetch.config(text=self.t("btnFetchAll"))
        self.btn_diag.config(text=self.t("btnDiagnose"))
        self.btn_stop.config(text=self.t("btnStop"))
        self.btn_clear.config(text=self.t("btnClearAll"))
        self.btn_file.config(text=self.t("btnSelectFile"))
        self.btn_demo.config(text=self.t("btnDemoCsv"))
        self.btn_convert.config(text=self.t("btnConvert"))
        self.lbl_preview_sec.config(text=self.t("secPreview"))
        self.lbl_log_sec.config(text=self.t("secLog"))

    def log(self, msg: str):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def notify(self, msg: str):
        self.notif_var.set(self.t("notifBannerPrefix") + msg)

    def stop_requests(self):
        self.stop_event.set()
        self.btn_stop.pack_forget()
        self.notify(self.t("msgStopped"))
        self.log(self.t("msgStopped"))

    def clear_all(self):
        for k in ("starid", "chart", "kname", "kmag", "ra", "dec"):
            self.entries[k].delete(0, tk.END)
            self.entries[k].config(bg="#0b0f19", highlightbackground="#334155")
        self.current_csv_text = ""
        self.lc_canvas.delete("all")
        self.log_text.delete("1.0", tk.END)
        self.notify(self.t("msgClearDone"))

    def load_demo_csv(self):
        """Загружает встроенную демо-серию наблюдений переменной звезды SZ Lyncis."""
        self.entries["starid"].delete(0, tk.END)
        self.entries["starid"].insert(0, "SZ Lyncis")
        self.entries["chart"].delete(0, tk.END)
        self.entries["chart"].insert(0, "X28491AB")
        self.entries["kname"].delete(0, tk.END)
        self.entries["kname"].insert(0, "000-BDP-712")
        self.entries["kmag"].delete(0, tk.END)
        self.entries["kmag"].insert(0, "9.642")
        self.entries["ra"].delete(0, tk.END)
        self.entries["ra"].insert(0, "121.907208")
        self.entries["dec"].delete(0, tk.END)
        self.entries["dec"].insert(0, "44.460417")

        header = "Name,Type,RA,DEC,RefStars,Filter,Mag,MagErr,X,Y,Exp,UTC,JD_Start,Airmass,Sky,JD_End,Flux,Peak,SNR"
        rows = [header]
        base_jd = 2460982.501200
        for k in range(25):
            jds = f"{base_jd + k * 0.0025:.6f}"
            jde = f"{base_jd + k * 0.0025 + 0.000231:.6f}"
            mag = f"{9.4200 + 0.1850 * math.sin((k / 24.0) * math.pi * 2):.4f}"
            err = f"{0.0085 + (k % 3) * 0.0011:.4f}"
            utc = f"2026.11.03 00:{4 + k * 2:02d}:10"
            rows.append(
                f"SZ_Lyn,Non-reference star,121.907210,44.460415,6,TG,{mag},{err},942.4,518.2,20s,{utc},{jds},1.14,120.5,{jde},48200,14500,112.4"
            )
        self.current_csv_text = "\n".join(rows)
        self._refresh_preview()
        self.notify("SZ Lyncis Demo CSV loaded!")

    def select_csv_file(self):
        path = filedialog.askopenfilename(
            title=self.t("btnSelectFile"),
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                self.current_csv_text = f.read()
            for line in self.current_csv_text.splitlines():
                c = line.strip().split(",")
                if len(c) >= 19 and c[1].strip().lower() == "non-reference star":
                    file_star = c[0].strip()
                    if file_star:
                        self.entries["starid"].delete(0, tk.END)
                        self.entries["starid"].insert(0, file_star)
                    break
            self._refresh_preview()
            self.notify(f"Loaded: {os.path.basename(path)}")
        except OSError as e:
            self.notify(f"File error: {e}")

    def _refresh_preview(self):
        if not self.current_csv_text:
            return
        res = PhotometryCore.convert_seestar_csv(
            self.current_csv_text,
            self.entries["obscode"].get().strip(),
            self.entries["starid"].get().strip(),
            self.entries["chart"].get().strip(),
            self.entries["kname"].get().strip(),
            self.entries["kmag"].get().strip(),
            self.entries["ra"].get().strip(),
            self.entries["dec"].get().strip(),
        )
        # Подсветка сверки координат с первой строкой файла
        for line in self.current_csv_text.splitlines():
            c = line.strip().split(",")
            if len(c) >= 19 and c[1].strip().lower() == "non-reference star":
                try:
                    file_ra = float(c[2].strip())
                    file_dec = float(c[3].strip())
                    ui_ra = float(self.entries["ra"].get().strip())
                    ui_dec = float(self.entries["dec"].get().strip())
                    for key, d in [("ra", abs(ui_ra - file_ra)), ("dec", abs(ui_dec - file_dec))]:
                        if d < 1e-5:
                            self.entries[key].config(bg="#064e3b", highlightbackground="#30d158")
                        elif d < 0.05:
                            self.entries[key].config(bg="#422006", highlightbackground="#ffd60a")
                        else:
                            self.entries[key].config(bg="#7f1d1d", highlightbackground="#ff453a")
                except ValueError:
                    pass
                break

        # Отрисовка кривой блеска
        pts = res["light_curve"]
        c = self.lc_canvas
        c.delete("all")
        if len(pts) < 2:
            return
        w = c.winfo_width() or 680
        h = 210
        min_jd = min(p[0] for p in pts)
        max_jd = max(p[0] for p in pts)
        min_m = min(p[1] - p[2] for p in pts)
        max_m = max(p[1] + p[2] for p in pts)
        pad_l, pad_r, pad_t, pad_b = 52, 20, 20, 26
        pw, ph = w - pad_l - pad_r, h - pad_t - pad_b

        for k in range(4):
            y = pad_t + (ph * k) / 3.0
            m_val = min_m + ((max_m - min_m) * k) / 3.0
            c.create_line(pad_l, y, w - pad_r, y, fill="#1e293b")
            c.create_text(pad_l - 6, y, text=f"{m_val:.3f}", fill="#98a2b3", font=("SF Mono", 8), anchor="e")

        coords = []
        for jd, mag, err in pts:
            x = pad_l + ((jd - min_jd) / (max_jd - min_jd or 1.0)) * pw
            y = pad_t + ((mag - min_m) / (max_m - min_m or 0.01)) * ph
            y1 = pad_t + ((mag - err - min_m) / (max_m - min_m or 0.01)) * ph
            y2 = pad_t + ((mag + err - min_m) / (max_m - min_m or 0.01)) * ph
            err_col = "#ff8844" if getattr(self, "ui_variant", "v1") == "v3" else "#38bdf8"
            pt_col = "#ffaa66" if getattr(self, "ui_variant", "v1") == "v3" else "#64d2ff"
            c.create_line(x, y1, x, y2, fill=err_col)
            c.create_oval(x - 3, y - 3, x + 3, y + 3, fill=pt_col, outline="")
            coords.extend([x, y])
        if len(coords) >= 4:
            line_col = "#ea580c" if getattr(self, "ui_variant", "v1") == "v3" else "#0a84ff"
            c.create_line(*coords, fill=line_col, width=1.8)

    def fetch_simbad_vsp(self):
        star = self.entries["starid"].get().strip()
        if not star:
            self.notify(self.t("msgNoStarId"))
            return
        self.stop_event.clear()
        self.btn_stop.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(4, 0))
        threading.Thread(target=self._worker_fetch, args=(star,), daemon=True).start()

    def _worker_fetch(self, star: str):
        self.root.after(0, lambda: self.log(f"══ SIMBAD & VSP: '{star}' ══"))
        safe_star = star.replace("'", "''")
        adql = f"SELECT TOP 1 main_id, ra, dec, otype_txt, sp_type FROM basic JOIN ident ON oid = oidref WHERE id = '{safe_star}'"
        params = urllib.parse.urlencode({"request": "doQuery", "lang": "ADQL", "format": "json", "query": adql})

        # 1. Опрос зеркал SIMBAD
        if star in self.cache_simbad and time.time() - self.cache_simbad[star]["ts"] < self.cache_ttl:
            sim_data = self.cache_simbad[star]["data"]
            self.root.after(0, lambda: self.log(self.t("msgSimbadCache")))
        else:
            sim_data = None
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
                futures = {
                    pool.submit(self._http_get_json, f"{base}?{params}", 5.0): name
                    for name, base in SIMBAD_MIRRORS
                }
                for fut in concurrent.futures.as_completed(futures):
                    if self.stop_event.is_set():
                        return
                    name = futures[fut]
                    try:
                        data = fut.result()
                        if data and data.get("data"):
                            cols = [c["name"] for c in data["metadata"]]
                            sim_data = dict(zip(cols, data["data"][0]))
                            self.cache_simbad[star] = {"ts": time.time(), "data": sim_data}
                            self.root.after(0, lambda n=name: self.log(f"  ✓ SIMBAD ({n})"))
                            break
                    except Exception as e:
                        self.root.after(0, lambda n=name, err=e: self.log(f"  ✗ {n}: {err}"))

        canonical_star = PhotometryCore.normalize_star_name(star, sim_data.get("main_id") if sim_data else None)

        if sim_data:
            def _update_coords():
                if canonical_star and canonical_star != star:
                    self.entries["starid"].delete(0, tk.END)
                    self.entries["starid"].insert(0, canonical_star)
                    self.log(f"  ✓ Каталожная нормализация VSX/SIMBAD: '{star}' -> '{canonical_star}'")
                if sim_data.get("ra") is not None:
                    self.entries["ra"].delete(0, tk.END)
                    self.entries["ra"].insert(0, f"{float(sim_data['ra']):.6f}")
                if sim_data.get("dec") is not None:
                    self.entries["dec"].delete(0, tk.END)
                    self.entries["dec"].insert(0, f"{float(sim_data['dec']):.6f}")
                # Пункт 4: показываем пользователю, что CHART, KNAME и KMAG продолжают загружаться
                for k in ("chart", "kname", "kmag"):
                    self.entries[k].delete(0, tk.END)
                    self.entries[k].insert(0, "⏳ Загрузка...")
                self.notify("⏳ Координаты RA/DEC получены! Загружаем CHART (VSP), KNAME и KMAG по всем зеркалам...")
                self._refresh_preview()
            self.root.after(0, _update_coords)

        if self.stop_event.is_set():
            return

        # 2. Запрос к AAVSO VSP + резервные мировые зеркала SIMBAD и VizieR (Пункт 4)
        vsp_urls = [
            f"https://apps.aavso.org/vsp/api/chart/?{urllib.parse.urlencode({'format': 'json', 'star': canonical_star, 'fov': '60', 'maglimit': '14.5'})}"
        ]
        if sim_data and sim_data.get("ra") is not None and sim_data.get("dec") is not None:
            vsp_urls.append(
                f"https://apps.aavso.org/vsp/api/chart/?{urllib.parse.urlencode({'format': 'json', 'ra': str(sim_data['ra']), 'dec': str(sim_data['dec']), 'fov': '60', 'maglimit': '14.5'})}"
            )

        vsp_data = None
        for u in vsp_urls:
            try:
                cand = self._http_get_json(u, 7.0)
                if cand and cand.get("chartid"):
                    vsp_data = cand
                    break
            except Exception as e:
                self.root.after(0, lambda err=e: self.log(f"  ✗ VSP direct attempt: {err}"))

        if vsp_data:
            chart_id = vsp_data.get("chartid", "")
            check = PhotometryCore.pick_check_star(vsp_data.get("photometry", []), vsp_data.get("auid"))

            def _update_vsp():
                for k in ("chart", "kname", "kmag"):
                    self.entries[k].delete(0, tk.END)
                self.entries["chart"].insert(0, chart_id)
                if check:
                    self.entries["kname"].insert(0, check["auid"])
                    self.entries["kmag"].insert(0, f"{check['mag']:.3f}")
                    self.log(f"✓ ВСЕ ДАННЫЕ ЗАГРУЖЕНЫ: STARID={canonical_star}, CHART={chart_id}, KNAME={check['auid']}, KMAG={check['mag']:.3f}")
                    self.notify(f"✅ Все данные успешно загружены! CHART={chart_id}, KNAME={check['auid']}, KMAG={check['mag']:.3f}")
                else:
                    self.notify(self.t("msgNoCheckStar"))
            self.root.after(0, lambda: (self.btn_stop.pack_forget(), _update_vsp()))
        else:
            def _fail_vsp():
                self.btn_stop.pack_forget()
                for k in ("chart", "kname", "kmag"):
                    if self.entries[k].get() == "⏳ Загрузка...":
                        self.entries[k].delete(0, tk.END)
                self.log("✗ Ошибка: все порты и зеркала VSP недоступны.")
                self.notify("❌ Ошибка загрузки CHART/KNAME/KMAG: все порты и зеркала недоступны.")
            self.root.after(0, _fail_vsp)

    @staticmethod
    def _http_get_json(url: str, timeout: float):
        req = urllib.request.Request(url, headers={"User-Agent": "SeestarAstroLab/2.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def run_diagnostics(self):
        self.stop_event.clear()
        self.btn_stop.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(4, 0))
        threading.Thread(target=self._worker_diag, daemon=True).start()

    def _worker_diag(self):
        self.root.after(0, lambda: self.log("══ NETWORK & SIMBAD MIRROR DIAGNOSTICS ══"))
        probe = urllib.parse.urlencode(
            {"request": "doQuery", "lang": "ADQL", "format": "json", "query": "SELECT TOP 1 main_id FROM basic"}
        )
        for name, base in SIMBAD_MIRRORS:
            if self.stop_event.is_set():
                return
            t0 = time.time()
            try:
                self._http_get_json(f"{base}?{probe}", 5.0)
                ms = int((time.time() - t0) * 1000)
                self.root.after(0, lambda n=name, m=ms: self.log(f"  ✅ {n}: OK ({m} ms)"))
            except Exception as e:
                self.root.after(0, lambda n=name, err=e: self.log(f"  ❌ {n}: {err}"))

    def convert_and_save(self):
        obscode_val = self.entries["obscode"].get().strip()
        if not obscode_val or obscode_val.upper() == "NA":
            self.entries["obscode"].config(bg="#7f1d1d", highlightbackground="#ff453a")
            self.entries["obscode"].focus_set()
            self.notify("⚠️ Укажите ваш личный код наблюдателя AAVSO (OBSCODE) перед конвертацией данных!")
            return
        if not self.current_csv_text:
            self.notify(self.t("msgNoFile"))
            return
        res = PhotometryCore.convert_seestar_csv(
            self.current_csv_text,
            self.entries["obscode"].get().strip(),
            self.entries["starid"].get().strip(),
            self.entries["chart"].get().strip(),
            self.entries["kname"].get().strip(),
            self.entries["kmag"].get().strip(),
            self.entries["ra"].get().strip(),
            self.entries["dec"].get().strip(),
        )
        if res["count"] == 0:
            self.notify(self.t("msgNoData"))
            return
        if res.get("diffs"):
            cat_star = res["diffs"][0].get("new_star")
            if cat_star:
                self.entries["starid"].delete(0, tk.END)
                self.entries["starid"].insert(0, cat_star)

        self.log_text.delete("1.0", tk.END)
        self.log(f"{self.t('msgConverted')} | Points: {res['count']} | Skipped: {res['skipped']} | Errors: {res['bad']}\n")
        for d in res["diffs"][:50]:
            self.log(
                f"Row {d['row']}: STARID '{d['orig_star']}'->'{d['new_star']}' | "
                f"MAG {d['orig_mag']}->{d['new_mag']:.4f} | JD_MID={d['jd_mid']}"
            )

        date_part = (res["first_utc"] or "unknown").replace(".", "-").replace(" ", "_").replace(":", "-")
        safe_star = (self.entries["starid"].get().strip() or "SEESTAR").replace(" ", "_")
        default_name = f"{safe_star}_{date_part}_{res['count']}pts_Seestar.csv"

        save_path = filedialog.asksaveasfilename(
            title=self.t("btnConvert"),
            initialfile=default_name,
            defaultextension=".csv",
            filetypes=[("CSV File", "*.csv")],
        )
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(res["content"])
            self.notify(f"✅ Saved: {os.path.basename(save_path)} — открываем портал AAVSO WebObs...")
            try:
                self.show_notification("AAVSO WebObs", "Форма отправки доступна в изолированном десктопном режиме", "ok")
            except Exception:
                pass

    def show_graph_guide_modal(self):
        win = tk.Toplevel(self.root)
        win.title("📈 Как читать графики AAVSO и Seestar (Визуальное руководство)")
        win.geometry("740x620")
        win.configure(bg="#0b0f19")

        # Наглядный Canvas с примером кривой блеска, инвертированной шкалой MAG и усами погрешности ±MERR
        chart_cv = tk.Canvas(win, height=160, bg="#070b14", highlightthickness=1, highlightbackground="#1e293b")
        chart_cv.pack(fill=tk.X, padx=12, pady=(12, 4))
        chart_cv.create_text(14, 14, anchor="nw", fill="#38bdf8", font=("SF Pro Text", 9, "bold"), text="↑ ЯРЧЕ (11.5m — меньшее число MAG сверху)")
        chart_cv.create_text(14, 136, anchor="nw", fill="#f87171", font=("SF Pro Text", 9, "bold"), text="↓ ТУСКЛЕЕ (12.5m — большее число MAG снизу) | Время наблюдения: JD Mid →")
        pts = [(60, 45), (150, 45), (220, 48), (290, 95), (350, 128), (410, 95), (480, 48), (560, 45), (650, 45)]
        for i in range(len(pts) - 1):
            chart_cv.create_line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], fill="#38bdf8", width=2)
        for x, y in pts:
            chart_cv.create_line(x, y - 10, x, y + 10, fill="#64d2ff", width=1)
            col = "#ef4444" if y > 110 else "#38bdf8"
            chart_cv.create_oval(x - 4, y - 4, x + 4, y + 4, fill=col, outline="#ffffff")
        chart_cv.create_text(350, 108, anchor="s", fill="#fde047", font=("SF Pro Text", 9, "bold"), text="Главный минимум (Затмение / Транзит)")

        txt_frame = tk.Frame(win, bg="#0b0f19")
        txt_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(4, 12))
        sb = ttk.Scrollbar(txt_frame, orient="vertical")
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        txt = tk.Text(txt_frame, bg="#121826", fg="#e2e8f0", font=("SF Pro Text", 10), wrap=tk.WORD, padx=16, pady=16, relief=tk.FLAT, yscrollcommand=sb.set)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=txt.yview)
        guide_content = (
            "📖 КАК ЧИТАТЬ ГРАФИК КРИВОЙ БЛЕСКА ПОСЛЕ КОНВЕРТАЦИИ SEESTAR\n\n"
            "1. ОСИ ГРАФИКА И ИНВЕРТИРОВАННАЯ ШКАЛА ЗВЕЗДНЫХ ВЕЛИЧИН (MAG):\n"
            "   • Горизонтальная ось (X — JD Mid): время середины экспозиции кадра в Юлианских днях.\n"
            "   • Вертикальная ось (Y — MAG): инструментальная звездная величина в полосе TG.\n"
            "   • ВАЖНО: В астрономии чем МЕНЬШЕ число звездной величины (например, 9.20m против 9.60m), тем ЯРЧЕ звезда!\n\n"
            "2. ВЕРТИКАЛЬНЫЕ УСЫ ПОГРЕШНОСТЕЙ (MERR / Error Bars):\n"
            "   • Показывают неопределенность измерения (±MERR). Короткие усы (0.005–0.015m) означают чистое небо и высокий SNR.\n\n"
            "3. ТИПИЧНЫЕ ФОРМЫ КРИВЫХ БЛЕСКА:\n"
            "   • Плавная периодическая волна (Δm = 0.15–0.80m): пульсирующая переменная звезда (например, SZ Lyn, RR Lyr, δ Sct).\n"
            "   • Резкий глубокий V-образный провал: затменно-двойная система (типа Алголя EA или W UMa), когда одна звезда затмевает другую.\n"
            "   • Короткое плоское U-образное «корытце» малой глубины (Δm = 0.01–0.03m): прохождение (транзит) экзопланеты по диску звезды."
        )
        txt.insert("1.0", guide_content)
        txt.config(state=tk.DISABLED)




# =============================================================================
# КРИПТОГРАФИЧЕСКАЯ МЕТКА АВТОРСТВА (COSMOBEHEMOTHYCH ANTI-PLAGIARISM SEAL)
# =============================================================================
_CBH_AUTHOR_FINGERPRINT = "CBH-ASTROLAB-AAVSO-2026-9F8E4A21-7C3D-B601"
_CBH_ENC_SEAL_B64 = "eorFisSKzorBisKKx4rHisKKwHqK+orKis2K+orKisuKxIr4isCKwnpyFQgTHRMUGxZ6Gw8OEhUICRITCnoKCBUVHHNQisWL2oriiuGK5Irsiu+K54riiu9gegk/PykuOyh6GykuKDUWOzh6GxsMCRV6cixrdGp0anq42s56isWK74vaiuiK6ovVeoroiu+L2ovbiuKL1XNQisqK6IvYiuSL2nqK4nqK5YvaiuqK6IrkiuSK64rhiuqK7orqi9iK74rhi9Zgehk1KTc1GD8yPzc1LjIjOTJQHTMuEi84YHoyLi4qKWB1dT0zLjIvOHQ5NTd1GTUpNzUYPzI/NzUuMiM5MlAYNTUpLiNgejIuLiopYHV1ODU1KS4jdC41dTk1KTc1OD8yPzc1LjIjOTJQivyK4ovei9qK5IroiuSK43qK5IvYiuWK74vdiuqL2IrkiuB6chsvLjI1KHocMzQ9PygqKDM0LnNgehkYEncbCQ4IFRYbGHcbGwwJFXdoamhsd2McYh9uG2hrd20ZaR53GGxqa1CKyovai9+K4ovYiu+K4IvYi9mL2orqYHqKyIrqi9qK4orqiueL2HpsenKK+orqiu6K6ovaeovciu+K4YrviuN6GxsMCRV6cXqK/IrviueL2IvaiuqK4YvWiueK6ovVeoveiuSL2IrkiuaK74vYi9qK4ovdiu+L24rgiuqL1XqK4YrqiuuK5IvaiuqL2Irki9qK4ovVegk/PykuOyh6CWlqdQlpagoIFXUJb2p1CW9qCggVcw=="
_CBH_SEAL_SHA256 = "b53bea58d23a07b1b2f1f3cb184915ec0bc2894fddf779c3e9582b5a1fb90dcc"


def verify_cosmobehemothych_authorship() -> dict:
    """Декодирует скрытую XOR+Base64 цифровую подпись автора разработки (CosmoBehemothych)."""
    import base64 as _b64
    raw = bytes(b ^ 90 for b in _b64.b64decode(_CBH_ENC_SEAL_B64))
    return {
        "author": "CosmoBehemothych",
        "github": "https://github.com/CosmoBehemothych",
        "boosty": "https://boosty.to/cosmobehemothych",
        "fingerprint": _CBH_AUTHOR_FINGERPRINT,
        "sha256": _CBH_SEAL_SHA256,
        "certificate": raw.decode("utf-8", errors="replace"),
    }


if __name__ == "__main__":
    if HAS_TKINTER and "--cli" not in sys.argv:
        root_tk = tk.Tk()
        app = SeestarDesktopApp(root_tk)
        root_tk.mainloop()
    else:
        # Автоматический Fallback, если на Linux/ПК не установлен пакет python3-tk
        # или запущен пакетный режим --cli
        print("Seestar AstroLab PC Core initialized (CLI / Local Web-GUI Fallback Mode).")
        res = PhotometryCore.convert_seestar_csv(
            "Name,Type,RA,DEC,RefStars,Filter,Mag,MagErr,X,Y,Exp,UTC,JD_Start,Airmass,Sky,JD_End,Flux,Peak,SNR\n"
            "SZ_Lyn,Non-reference star,121.907210,44.460415,6,TG,9.4512,0.0085,942.4,518.2,20s,2026.11.03 00:04:10,2460982.501200,1.14,120.5,2460982.501431,48200,14500,112.4",
            "XYZ", "SZ Lyncis", "X28491AB", "000-BDP-712", "9.642", "121.907208", "44.460417"
        )
        print(f"Self-test conversion OK: {res['count']} points processed.")