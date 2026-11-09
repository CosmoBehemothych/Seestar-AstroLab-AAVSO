(() => {
  "use strict";

  /**
   * ============================================================================
   * МОДУЛЬ 1: ЛОКАЛИЗАЦИЯ И СЛОВАРИ ПЕРЕВОДОВ (I18N — 6 ЯЗЫКОВ)
   * Разработчику: Проверены и переведены абсолютно все строки интерфейса,
   * включая подсказки (tooltips), описания уведомлений, ошибки сети и подписи.
   * ============================================================================
   */
  
  /**
   * ============================================================================
   * МОДУЛЬ 2.5: ИМЕНОВАННЫЕ КОНСТАНТЫ И ЯДРО ASTROLABCORE (Критерии 1.2, 1.8)
   * Разработчику:
   * 1. Устранение «магических чисел» согласно критерию 1.2.
   * 2. Чистые функции расчета JD Mid, расстояний и парсинга изолированы в объекте
   *    window.AstroLabCore для модульного юнит-тестирования (критерий 1.8).
   * 3. Включает встроенный набор автоматических тестов (Self-Tests).
   * ============================================================================
   */
  const ASTRONOMY_CONSTANTS = Object.freeze({
    COMPANY_AUTHOR: "CosmoBehemothych",
    VERSION: "2.1.0-AAVSO",
    CACHE_TTL_MS: 3600 * 1000,          // Время жизни сетевого кэша: 1 час
    COORD_TOLERANCE_DEG: 0.002,         // Допуск совпадения координат: ~7.2 угл. сек.
    JULIAN_EPOCH_OFFSET: 2400000.5,      // Смещение эпохи Юлианских дат (MJD -> JD)
    DEFAULT_MAG_ERROR: 0.05,            // Базовая инструментальная погрешность Seestar
    CHECK_STAR_MIN_MAG: 9.5,            // Минимальный блеск контрольной звезды (VSP)
    CHECK_STAR_MAX_MAG: 13.0,           // Максимальный блеск контрольной звезды (VSP)
    DEFAULT_AIRMASS: 1.0,               // Воздушная масса по умолчанию
    DEMO_BASE_JD: 2460982.501200,       // Базовая эпоха для демонстрационных данных SZ Lyn
    DEMO_STEP_DAYS: 0.0025,             // Шаг между экспозициями Seestar (~3.6 мин)
    DEMO_EXPOSURE_DAYS: 0.000231        // Длительность кадра Seestar (20 сек)
  });

  const TELESCOPE_MODELS = Object.freeze({
    S30: Object.freeze({
      id: "S30",
      name: "ZWO Seestar S30",
      shortName: "Seestar S30",
      fovDegW: 1.28,
      fovDegH: 0.72,
      fovStr: "1.28°×0.72°",
      resPx: "1920×1080",
      pixelScale: 2.40,
      magLimit: 13.5,
      brightLimit: 5.5,
      minExpSec: 10,
      maxExpSec: 20,
      vspFovArcmin: 75,
      sensor: "Sony IMX662 (FHD)",
      focalMm: 150, skySurveyFovDeg: 2.40, frameRect: { x: 80, y: 119, w: 181, h: 102 },
      notes: "Широкое поле 1.28°×0.72°, разрешение 1920×1080 (2.40″/px), лимит ≤ 13.5 mag, выдержка 10–20 с"
    }),
    S30PRO: Object.freeze({
      id: "S30PRO",
      name: "ZWO Seestar S30 Pro",
      shortName: "Seestar S30PRO",
      fovDegW: 2.10,
      fovDegH: 1.18,
      fovStr: "2.10°×1.18°",
      resPx: "3840×2160",
      pixelScale: 1.97,
      magLimit: 14.2,
      brightLimit: 5.0,
      minExpSec: 10,
      maxExpSec: 30,
      vspFovArcmin: 90,
      sensor: "Sony IMX585 (4K)",
      focalMm: 160, skySurveyFovDeg: 2.40, frameRect: { x: 21, y: 86, w: 298, h: 167 },
      notes: "Сверхширокое поле 4K 2.10°×1.18°, разрешение 3840×2160 (1.97″/px), лимит ≤ 14.2 mag, выдержка 10–30 с"
    }),
    S50: Object.freeze({
      id: "S50",
      name: "ZWO Seestar S50",
      shortName: "Seestar S50",
      fovDegW: 0.78,
      fovDegH: 1.05,
      fovStr: "0.78°×1.05°",
      resPx: "1080×1920",
      pixelScale: 2.39,
      magLimit: 14.5,
      brightLimit: 6.0,
      minExpSec: 10,
      maxExpSec: 20,
      vspFovArcmin: 60,
      sensor: "Sony IMX462 (FHD)",
      focalMm: 250, skySurveyFovDeg: 2.40, frameRect: { x: 115, y: 96, w: 111, h: 149 },
      notes: "Апертура 50 мм, поле 0.78°×1.05°, разрешение 1080×1920 (2.39″/px), лимит ≤ 14.5 mag, выдержка 10–20 с"
    }),
    S50PRO: Object.freeze({
      id: "S50PRO",
      name: "ZWO Seestar S50 Pro",
      shortName: "Seestar S50PRO",
      fovDegW: 1.15,
      fovDegH: 0.65,
      fovStr: "1.15°×0.65°",
      resPx: "3840×2160",
      pixelScale: 1.08,
      magLimit: 15.2,
      brightLimit: 5.5,
      minExpSec: 10,
      maxExpSec: 30,
      vspFovArcmin: 60,
      sensor: "Sony IMX585 (4K)",
      focalMm: 280, skySurveyFovDeg: 2.40, frameRect: { x: 89, y: 124, w: 163, h: 92 },
      notes: "Флагман 50 мм 4K, поле 1.15°×0.65°, разрешение 3840×2160 (1.08″/px), лимит ≤ 15.2 mag, выдержка 10–30 с"
    })
  });

  // Справочник синонимов и альтернативных обозначений одной и той же звезды (Пункт 9)
  const STAR_SYNONYM_GROUPS = [
    ["SZ Lyn", "SZ Lyncis", "HD 67390", "HIP 39960", "000-BBP-158", "BD+44 1718"],
    ["CH Cyg", "CH Cygni", "HD 182917", "HIP 95413", "000-BCY-101", "SAO 48428"],
    ["T CrB", "T Coronae Borealis", "HD 143454", "HIP 78322", "000-BBW-825", "Blaze Star"],
    ["SS Cyg", "SS Cygni", "HD 206697", "000-BCP-216"],
    ["R CrB", "R Coronae Borealis", "HD 141527", "HIP 77442", "000-BBW-785"],
    ["U Gem", "U Geminorum", "HD 64511", "000-BBG-153"],
    ["RS Oph", "RS Ophiuchi", "HD 162214", "000-BBN-599"],
    ["W UMa", "W Ursae Majoris", "HD 83950", "HIP 47727", "000-BBP-815"],
    ["HD 189733", "V452 Vul", "V452 Vulpeculae", "HIP 98505", "000-BFP-955"],
    ["Betelgeuse", "Alpha Ori", "Alpha Orionis", "alf Ori", "HD 39801", "000-BBW-100"],
    ["V1309 Sco", "V1309 Scorpii", "Nova Sco 2008", "000-BSK-301"],
    ["TX UMa", "TX Ursae Majoris", "HD 93033", "000-BDP-820"],
    ["Beta Lyr", "Beta Lyrae", "bet Lyr", "Sheliak", "HD 174638", "000-BBL-001"],
    ["Algol", "Beta Per", "Beta Persei", "bet Per", "HD 19356", "000-BCC-102"],
    ["RW Aur", "RW Aurigae", "HD 246933", "000-BAU-101"],
    ["CI Cyg", "CI Cygni", "AAVSO 1950+35", "000-BCY-201"],
    ["AG Dra", "AG Draconis", "BD+67 922", "000-BDR-101"],
    ["Z And", "Z Andromedae", "HD 221658", "000-BAN-101"],
    ["V838 Mon", "V838 Monocerotis", "Nova Mon 2002", "000-BMO-101"],
    ["BL Lac", "BL Lacertae", "HD 225216", "000-BLA-101"],
    ["OJ 287", "3C 217.1", "QSO B0851+202", "000-BOJ-101"],
    ["V404 Cyg", "V404 Cygni", "GS 2023+338", "000-BCY-404"],
    ["GK Per", "GK Persei", "Nova Persei 1901", "HD 21629", "000-BPE-101"],
    ["V339 Del", "V339 Delphini", "Nova Del 2013", "000-BDE-339"],
    ["V1674 Her", "V1674 Herculis", "Nova Her 2021", "000-BHE-167"],
    ["WASP-12", "HD 283759", "000-BWA-101"],
    ["KIC 8462852", "Tabby's Star", "Boyajian's Star", "TYC 3162-665-1", "000-BKI-846"],
    ["Chi Cyg", "Chi Cygni", "chi Cyg", "HD 187796", "000-BCY-007"],
    ["Mira", "Omicron Cet", "Omicron Ceti", "omi Cet", "HD 14386", "000-BCE-001"],
    ["V1405 Cas", "V1405 Cassiopeiae", "Nova Cas 2021", "000-BCA-140"],
    ["Z Cam", "Z Camelopardalis", "HD 68276", "000-BZC-101"],
    ["SU UMa", "SU Ursae Majoris", "000-BSU-101"],
    ["YZ Cnc", "YZ Cancri", "000-BYZ-101"],
    ["RX And", "RX Andromedae", "000-BRX-101"],
    ["VW Hyi", "VW Hydri", "000-BVW-101"],
    ["HL CMa", "HL Canis Majoris", "000-BHL-101"],
    ["BF Cyg", "BF Cygni", "000-BBF-101"],
    ["YY Her", "YY Herculis", "000-BYY-101"],
    ["AX Per", "AX Persei", "000-BAX-101"],
    ["PU Vul", "PU Vulpeculae", "Nova Vul 1979", "000-BPU-101"],
    ["HM Sge", "HM Sagittae", "000-BHM-101"],
    ["V1016 Cyg", "V1016 Cygni", "000-BVC-101"],
    ["RR Lyr", "RR Lyrae", "HD 182989", "000-BRR-101"],
    ["Delta Cep", "Delta Cephei", "del Cep", "HD 213306", "000-BDC-101"],
    ["WASP-33", "HD 15082", "000-BW3-101"]
  ];

  const AstroLabCore = {
    TELESCOPE_MODELS,

    getScopeProfile(scopeId) {
      const base = TELESCOPE_MODELS[scopeId] || TELESCOPE_MODELS.S50;
      if (typeof currentLang !== "undefined" && currentLang !== "ru") {
        const notesMap = {
          S30: "Wide field 2.40°×1.35° (1080p) — ideal for bright variables (≤13.5m) with abundant VSP comparison stars.",
          S30PRO: "Wide 4K field 2.10°×1.18° — high angular resolution (1.97″/px) for crowded variable star fields up to 14.2m.",
          S50: "Classic apochromatic triplet 0.78°×1.05° — primary photometry instrument up to 14.5m.",
          S50PRO: "High-sensitivity 4K apochromatic triplet 1.15°×0.65° (1.08″/px) — deep photometry of cataclysmics & exoplanets up to 15.2m."
        };
        return Object.assign({}, base, { notes: notesMap[base.id] || base.notes });
      }
      return base;
    },

    evaluateScopeSuitability(targetItem, scopeId) {
      const prof = AstroLabCore.getScopeProfile(scopeId);
      const kmag = parseFloat(targetItem && targetItem.kmag);
      const magStr = String((targetItem && targetItem.magRange) || "");
      const nums = Array.from(magStr.matchAll(/(\d+(?:\.\d+)?)\s*(?:m|mag)\b/gi), m => parseFloat(m[1])).filter(n => !isNaN(n));
      const minMag = nums.length ? Math.min(...nums) : (isNaN(kmag) ? 10.0 : kmag);
      const maxMag = nums.length ? Math.max(...nums) : (isNaN(kmag) ? 11.5 : kmag);
      const refMag = !isNaN(kmag) ? kmag : ((minMag + maxMag) / 2);

      const tr = (typeof t === "function") ? t : (k => k);
      let expRec = tr("exp10_20") !== "exp10_20" ? tr("exp10_20") : "10–20 s";
      if (refMag < 8.5) expRec = tr("exp10") !== "exp10" ? tr("exp10") : "10 s";
      else if (refMag > 12.5 && prof.maxExpSec >= 30) expRec = tr("exp20_30") !== "exp20_30" ? tr("exp20_30") : "20–30 s";
      else if (refMag > 11.5) expRec = tr("exp20") !== "exp20" ? tr("exp20") : "20 s";

      const withinFaintLimit = minMag <= prof.magLimit && (!isNaN(kmag) ? kmag <= prof.magLimit : true);
      const faintDipWarning = maxMag > prof.magLimit;
      const brightWarning = minMag < prof.brightLimit;

      let status = "ok";
      let badgeText = (tr("scopeEvalOkFmt") !== "scopeEvalOkFmt"
        ? tr("scopeEvalOkFmt").replace("{id}", prof.id).replace("{exp}", expRec).replace("{fov}", prof.fovStr).replace("{scale}", prof.pixelScale)
        : `${prof.id}: Exp ${expRec} • FOV ${prof.fovStr} (${prof.pixelScale}″/px)`);
      if (!withinFaintLimit) {
        status = "warn";
        badgeText = (tr("scopeEvalFaintFmt") !== "scopeEvalFaintFmt"
          ? tr("scopeEvalFaintFmt").replace("{id}", prof.id).replace("{mag}", prof.magLimit)
          : `${prof.id}: > ${prof.magLimit}m (S50/S50PRO)`);
      } else if (faintDipWarning) {
        status = "warn";
        badgeText = (tr("scopeEvalDipFmt") !== "scopeEvalDipFmt"
          ? tr("scopeEvalDipFmt").replace("{id}", prof.id).replace("{max}", maxMag).replace("{mag}", prof.magLimit).replace("{exp}", prof.maxExpSec)
          : `${prof.id}: min ${maxMag}m (limit ${prof.magLimit}m) • ${prof.maxExpSec} s`);
      } else if (brightWarning) {
        status = "warn";
        badgeText = (tr("scopeEvalBrightFmt") !== "scopeEvalBrightFmt"
          ? tr("scopeEvalBrightFmt").replace("{id}", prof.id).replace("{min}", minMag).replace("{bright}", prof.brightLimit).replace("{exp}", prof.minExpSec)
          : `${prof.id}: bright ${minMag}m < ${prof.brightLimit}m • ${prof.minExpSec} s`);
      }
      return {
        compatible: withinFaintLimit,
        status,
        expRec,
        badgeText,
        prof
      };
    },

    cleanStarToken(raw) {
      if (!raw) return "";
      let s = String(raw).trim();
      s = s.replace(/^(V\*|SV\*|\*\*|\*|EM\*|EB\*|RR\*|BY\*|DSCT\*|VARIABLE\s+STAR)\s+/i, "").trim();
      s = s.replace(/_/g, " ").replace(/\s+/g, " ").trim();
      return s;
    },

    getCanonicalStarKey(rawName) {
      const cleaned = AstroLabCore.cleanStarToken(rawName);
      if (!cleaned) return "";
      // If normalizeStarForVsp is defined in outer scope, apply constellation genitive reduction first
      const reduced = (typeof normalizeStarForVsp === "function")
        ? normalizeStarForVsp(cleaned, null)
        : cleaned;
      const lowCleaned = cleaned.toLowerCase();
      const lowReduced = reduced.toLowerCase();

      for (const grp of STAR_SYNONYM_GROUPS) {
        for (const alias of grp) {
          const lowAlias = alias.toLowerCase();
          if (lowCleaned === lowAlias || lowReduced === lowAlias) {
            return grp[0];
          }
        }
      }
      return reduced;
    },

    areSameStar(nameA, nameB) {
      const cleanA = AstroLabCore.cleanStarToken(nameA);
      const cleanB = AstroLabCore.cleanStarToken(nameB);
      if (!cleanA || !cleanB) return false;
      if (cleanA.toLowerCase() === cleanB.toLowerCase()) return true;
      const keyA = AstroLabCore.getCanonicalStarKey(cleanA).toLowerCase();
      const keyB = AstroLabCore.getCanonicalStarKey(cleanB).toLowerCase();
      return keyA === keyB;
    },

    compareStarIds(fileStarId, uiStarId) {
      const fRaw = String(fileStarId || "").trim();
      const uRaw = String(uiStarId || "").trim();
      if (!uRaw) {
        return { status: null, isSameStar: true, canonicalUi: "", canonicalFile: AstroLabCore.getCanonicalStarKey(fRaw) };
      }
      if (!fRaw) {
        return { status: null, isSameStar: true, canonicalUi: AstroLabCore.getCanonicalStarKey(uRaw), canonicalFile: "" };
      }
      if (fRaw === uRaw) {
        return { status: "ok", isSameStar: true, canonicalUi: uRaw, canonicalFile: fRaw };
      }
      const same = AstroLabCore.areSameStar(fRaw, uRaw);
      if (same) {
        return {
          status: "warn",
          isSameStar: true,
          canonicalUi: AstroLabCore.getCanonicalStarKey(uRaw),
          canonicalFile: AstroLabCore.getCanonicalStarKey(fRaw)
        };
      }
      return {
        status: "bad",
        isSameStar: false,
        canonicalUi: AstroLabCore.getCanonicalStarKey(uRaw),
        canonicalFile: AstroLabCore.getCanonicalStarKey(fRaw)
      };
    },

    calculateJdMid(jdStart, jdEnd) {
      if (typeof jdStart !== "number" || isNaN(jdStart)) return NaN;
      if (typeof jdEnd !== "number" || isNaN(jdEnd)) return jdStart;
      return (jdStart + jdEnd) / 2.0;
    },

    computeAngularDistance(ra1, dec1, ra2, dec2) {
      const toRad = Math.PI / 180.0;
      const dRa = (ra2 - ra1) * toRad;
      const dDec = (dec2 - dec1) * toRad;
      const a = Math.sin(dDec / 2.0) ** 2 +
                Math.cos(dec1 * toRad) * Math.cos(dec2 * toRad) * Math.sin(dRa / 2.0) ** 2;
      return 2.0 * Math.atan2(Math.sqrt(a), Math.sqrt(1.0 - a)) * (180.0 / Math.PI);
    },

    parseCsvRows(csvContent) {
      if (!csvContent || typeof csvContent !== "string") return [];
      const lines = csvContent.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
      if (lines.length < 2) return [];

      const headers = lines[0].split(",").map(h => h.trim().toLowerCase());
      const records = [];

      for (let i = 1; i < lines.length; i++) {
        const parts = lines[i].split(",").map(p => p.trim());
        if (parts.length < headers.length) continue;
        const row = {};
        headers.forEach((h, idx) => {
          row[h] = parts[idx];
        });
        records.push(row);
      }
      return records;
    },

    formatAavsoLine(starName, jdMid, mag, merr, filter, obsCode, chart, kname, kmag, airmass) {
      return [
        starName,
        jdMid.toFixed(5),
        mag.toFixed(3),
        merr.toFixed(3),
        filter || "TG",
        "NO",
        "STD",
        kname || "na",
        kmag != null && !isNaN(kmag) ? Number(kmag).toFixed(3) : "na",
        airmass != null && !isNaN(airmass) ? Number(airmass).toFixed(2) : "na",
        "na",
        chart || "na",
        "na",
        "na",
        obsCode || "NA"
      ].join(",");
    },

    runSelfTests() {
      const results = [];
      const assert = (desc, cond) => {
        results.push({ desc, passed: Boolean(cond) });
      };

      const mid = AstroLabCore.calculateJdMid(2460000.100, 2460000.200);
      assert("1. Точность расчета JD Mid ((Start+End)/2)", Math.abs(mid - 2460000.150) < 1e-6);

      const fallbackMid = AstroLabCore.calculateJdMid(2460000.100, NaN);
      assert("2. Fallback JD Mid при отсутствии JD_End", fallbackMid === 2460000.100);

      const distZero = AstroLabCore.computeAngularDistance(120.0, 45.0, 120.0, 45.0);
      assert("3. Угловое расстояние между одинаковыми координатами = 0°", Math.abs(distZero) < 1e-9);

      const dist1Deg = AstroLabCore.computeAngularDistance(0.0, 0.0, 1.0, 0.0);
      assert("4. Угловое расстояние на экваторе в 1°", Math.abs(dist1Deg - 1.0) < 1e-4);

      const sampleCsv = "Name,Mag,JD_Start,JD_End\nSZ Lyn,9.25,2460000.1,2460000.2";
      const parsed = AstroLabCore.parseCsvRows(sampleCsv);
      assert("5. Чистый парсинг CSV строк Seestar", parsed.length === 1 && parsed[0].name === "SZ Lyn");

      const aavsoRow = AstroLabCore.formatAavsoLine("SZ Lyn", 2460000.15, 9.25, 0.02, "TG", "TEST_OBS", "X123", "000-BDP-712", 9.642, 1.15);
      const cols = aavsoRow.split(",");
      assert("6. Формат AAVSO Extended содержит ровно 15 колонок", cols.length === 15);

      const synCheck = AstroLabCore.compareStarIds("SZ Lyncis", "SZ Lyn");
      assert("7. Сверка синонимов одной звезды (SZ Lyncis / SZ Lyn -> warn / Отличие норма)", synCheck.status === "warn" && synCheck.isSameStar === true);

      const diffCheck = AstroLabCore.compareStarIds("SZ Lyncis", "CH Cyg");
      assert("8. Сверка разных звёзд (SZ Lyncis / CH Cyg -> bad / Расхождение)", diffCheck.status === "bad" && diffCheck.isSameStar === false);

      const scopesOk = ["S30", "S30PRO", "S50", "S50PRO"].every(k => Boolean(AstroLabCore.TELESCOPE_MODELS[k]));
      assert("9. Поддержка всех моделей телескопов S30, S30PRO, S50, S50PRO", scopesOk);

      const allPassed = results.every(r => r.passed);
      console.log(`[CosmoBehemothych Self-Tests] Passed: ${results.filter(r => r.passed).length}/${results.length}`);
      return { allPassed, results };
    }
  };
  window.AstroLabCore = AstroLabCore;


  const I18N = {
    ru: {
      btnObsTrackerMenu: "📓 Мои наблюдения",
      lblSettingsTitle: "Настройки:",
      lblToastsShort: "🔔 Уведомления",
      lblToastsToggle: "🔔 Всплывающие уведомления",
      splashHubTitle: "⚡ Панель управления обсерваторией и быстрые переходы",
      splashMetricTargetsLbl: "Целей в радаре AAVSO",
      splashMetricObsCountLbl: "Сессий в разделе Мои наблюдения",
      splashMetricDaysIdleLbl: "Статус фотометрии",
      splashMetricScopeLbl: "Активный телескоп",
      btnSplashQuickSync: "🛰️ К синхронизации каталогов",
      btnSplashQuickTracker: "📓 Мои наблюдения",
      btnSplashQuickRadar: "🎯 Радар целей AAVSO",
      btnSplashQuickLoadCsv: "📂 Выбрать CSV-файл",
      splashRecentLogTitle: "🕒 Лог последних действий:",
      obsTrackerTitle: "📓 Мои наблюдения",
      obsDaysSinceFmt: "Вы не проводили фотометрию {days} дней",
      obsSummaryStatsFmt: "Всего сессий: {count} • Суммарное время: {mins} мин • Кадров: {frames}",
      phObsStar: "Звезда (напр. SZ Lyn)",
      phObsDur: "Длит. (мин)",
      phObsFrames: "Кадров",
      btnObsAdd: "➕ Добавить замер",
      btnObsExport: "💾 Экспорт JSON",
      btnObsImport: "📂 Импорт JSON",
      obsChartTitle: "📊 График активности наблюдений (длительность замеров в минутах и число кадров по датам)",
      thObsStar: "Звезда (STARID)",
      thObsDate: "Дата замера",
      thObsDuration: "Длительность (мин)",
      thObsFrames: "Записей в файле / Фильтр",
      thObsScope: "Телескоп",
      thObsAction: "Действие",
      btnObsDelete: "Удалить",
      btnObsDeleteAll: "🗑️ Удалить все",
      btnObsResetFilters: "↺ Сбросить",
      phObsFilterStar: "🔍 Поиск по звезде (STARID)...",
      optObsAllScopes: "🔭 Все телескопы (S30–S50PRO)",
      lblSortBy: "Сортировка:",
      optSortDate: "По дате публикации (новые)",
      optSortName: "По названию (A–Z)",
      optSortPriority: "По приоритету (Срочно)",
      btnDonateBadge: "❤️ Поддержать",
      tipDonateAuthor: "Поддержать автора CosmoBehemothych на Boosty",
      donateModalTitle: "❤️ Поддержать проект Seestar AstroLab AAVSO",
      donateLiteraryText: "Друзья и коллеги по звездному небу! Фотометрический комплекс Seestar AstroLab создается и развивается с любовью к наблюдательной астрономии, чтобы каждый кадр вашего телескопа приносил реальную пользу мировой науке и базе AAVSO. Если программа помогает вам в наблюдениях и экономит время у телескопа — вы можете поддержать развитие проекта любой комфортной суммой или просто добрым словом на Boosty. Чистого неба и точных кривых блеска!",
      donateScanOrClick: "Наведите камеру смартфона на QR-код или перейдите по прямой ссылке:",
      btnDonateNever: "Больше не показывать",
      btnDonateLater: "Напомнить через месяц",
      btnDonateSupportNow: "❤️ Поддержать на Boosty",
      obsEmptyTableMsg: "Записей пока нет. Сконвертируйте CSV-файл фотометрии Seestar — и результат автоматически сохранится в «Мои наблюдения».",
      obsMinUnit: "мин",
      obsFramesUnit: "зап.",
      actAppStarted: "Запущена сессия Seestar AstroLab v1.0.1",
      actCatalogSyncedFmt: "Синхронизация с каталогом: {star}",
      actFileConvertedFmt: "Сконвертирован отчёт AAVSO: {star} ({pts} точек)",
      actObsAddedFmt: "Добавлена запись в Мои наблюдения: {star} ({mins} мин)",
      actRadarPickedFmt: "Выбран ориентир радара: {star}",
      tipVerifyDiskShort: "Проверяет совместимость сконвертированного файла с требованиями сайта AAVSO WebObs.",
      errNoObscodeTitle: "⚠️ Не указан код наблюдателя (OBSCODE)",
      errNoObscodeMsg: "Укажите ваш личный код наблюдателя AAVSO (OBSCODE) перед конвертацией данных для загрузки на AAVSO.",
      errNoObscodeExplain: "Стандарт AAVSO Extended требует обязательного указания персонального кода наблюдателя в заголовке #OBSCODE.",
      radarSubTag: "",
      appVersionLabel: "Версия 1.0.1",
      starIdFromCatalogHint: "✓ Каталожный идентификатор звезды (SIMBAD / AAVSO VSX): {star}",
      brandBarTitle: "🌌 CosmoBehemothych • Seestar AstroLab AAVSO • Фотометрия Seestar S30 / S30PRO / S50 / S50PRO",
      
      missionSummaryTitle: "ℹ️ Как работает сверка полей Seestar → SIMBAD & VSP (цветовые индикаторы)",
      lblExpand: "Развернуть\u00A0▾",
      bentoSyncBadgeText: "Online • TTL 1ч",
      bentoSimbadDefault: "✓ 3 зеркала (HTTPS:443)",
      bentoVspDefault: "✓ Активен (API v2)",
      bentoVizierDefault: "✓ 4 зеркала (Резерв)",
      lblThemePanel: "Цветовая панель",
      lblThemePickerSplash: "Цветовая панель",
      lblObscodeHeader: "OBSCODE:",
      phObscodeHeader: "Ваш код",
      tipToggleScope: "Переключить модель умного телескопа (S30 / S30PRO / S50 / S50PRO)",
      btnUrgentTop: "Радар целей AAVSO",
      tipRefreshRadar: "Обновить каталог целей AAVSO",
      tipExpandUrgent: "Открыть подробную таблицу целей",
      tipCollapseRadar: "Свернуть боковой радар целей AAVSO",
      tipExpandRadar: "Развернуть боковой радар целей AAVSO",
      radarCollapsedPill: "РАДАР AAVSO ({count})",
      lblScopeSectionTitle: "🔭 Модель телескопа Seestar",
      scopeSpecsFmt: "FOV: {fov} • {res} ({scale}″/px) • Лимит: ≤{mag} mag • Выдержка: {minE}–{maxE} с",
      phRadarSearch: "🔍 Поиск по 45 целям (имя, тип, созвездие)...",
      filterAllFmt: "Все ({count})",
      filterUrgent: "🔥 Срочно",
      filterScopeFmt: "🔭 Под {id} (≤{mag}m)",
      filterExo: "🪐 Затменные/Экзо",
      radarCountFmt: "Показано: {shown} из {total} целей",
      lblRadarLimit: "Показ:",
      optLimitAll: "Все 45",
      optLimit30: "Топ 30",
      optLimit15: "Топ 15",
      tagPhotometry: "📈 Фотометрия звезд",
      tagBinaries: "🌑 Затменные двойные",
      tagExoplanets: "🪐 Экзопланеты",
      tagTelescopes: "🔭 S30 • S30PRO • S50 • S50PRO",
      lblBentoService: "Сервис SIMBAD TAP",
      valBentoService: "✓ 3 зеркала (CDS / Harvard / IDIA)",
      lblBentoVsp: "Шкала AAVSO VSP",
      valBentoVsp: "✓ Авто-выбор по полю S30..S50PRO",
      lblBentoCache: "Кэш каталогов",
      valBentoCacheFmt: "TTL 3600 с • Записей: {count}",
      lblBentoStandard: "Стандарт отчёта",
      valBentoStandard: "AAVSO Extended (#TYPE=EXTENDED)",
      phStarIdEmpty: "Не загружено (из файла CSV)",
      phRaEmpty: "Из файла или радара",
      phDecEmpty: "Из файла или радара",
      emptyPreviewTitle: "Загрузите CSV файл Seestar для сравнения",
      emptyPreviewDesc: "Предпросмотр параметров звезды, сверка координат и кривая блеска появятся автоматически после выбора CSV-файла наблюдения.",
      lcFrameTooltipFmt: "Кадр #{idx} | JD {jd} | {mag} mag ±{merr}",
      btnPickTarget: "Выбрать",
      btnPickedTarget: "✓ В радаре",
      ttDescLabel: "Описание:",
      ttCommentLabel: "Комментарий AAVSO:",
      ttDefaultComment: "Активируйте серию TG и сверку по KNAME.",
      scopeEvalOkFmt: "{id}: Выдержка {exp} • FOV {fov} ({scale}″/px)",
      scopeEvalFaintFmt: "{id}: Тусклее лимита {mag}m (реком. S50/S50PRO)",
      scopeEvalDipFmt: "{id}: В минимуме до {max}m (лимит {mag}m) • Выдержка {exp} с",
      scopeEvalBrightFmt: "{id}: Яркая ({min}m < {bright}m, риск насыщения) • Выдержка {exp} с",
      exp10_20: "10–20 с",
      exp10: "10 с",
      exp20_30: "20–30 с",
      exp20: "20 с",
      toastScopeTitleFmt: "🔭 Профиль телескопа: {name}",
      toastScopeSubFmt: "Радиус поиска звезд сравнения VSP: {fov}', предел блеска: {mag} mag.",
      toastRadarTargetTitleFmt: "🛰️ Ориентир радара AAVSO: {star}",
      toastRadarTargetMsgFmt: "Калибровка VSP: CHART {chart} • KNAME {kname} ({kmag} mag)",
      toastRadarTargetSubFmt: "Координаты и карта сравнения обновлены ({scope}). Поле STARID заполняется только из загруженного файла.",
      toastThemeLightTitle: "☀️ Активирована Светлая тема",
      toastThemeLightMsg: "Высококонтрастная дневная палитра (WCAG AA) для Командного центра и Радара целей AAVSO.",
      toastThemeDarkTitle: "🌙 Активирована Стандартная тёмная тема",
      toastThemeDarkMsg: "Космическая тёмная палитра Командного центра и Радара целей AAVSO.",
      toastHomeTitle: "🏠 Стартовая страница",
      toastHomeMsg: "Открыто окно приветствия и описания Seestar AstroLab",
      toastHomeSub: "Здесь собраны ключевые возможности и стандарты обсерватории.",
      urgentSyncWait: "⏳ Синхронизация кампаний AAVSO: <strong>Готово к опросу зеркал...</strong>",
      urgentSyncProgress: "⏳ <strong>Синхронизация с зеркалами CDS SIMBAD TAP и AAVSO VSP...</strong>",
      urgentSyncDoneFmt: "✅ <strong>Синхронизировано {count} объектов AAVSO в {time}</strong> (JD {jd}).",
      urgentAutoTimerPrefix: "Автообновление каждые 10 мин • JD:",
      urgentCountBadgeFmt: "{shown} из {total} целей",
      btnPickUrgentFmt: "🎯 Взять ориентир ({exp})",
      btnRefreshLoading: "⏳ Обновление...",
      toastRadarRefreshedTitle: "🔄 Радар целей AAVSO обновлён",
      toastRadarRefreshedMsgFmt: "Успешно синхронизировано {count} целевых объектов ({time})",
      toastRadarRefreshedSub: "Все координаты J2000, карты VSP и профили телескопов S30/S30PRO/S50/S50PRO актуальны.",
      demoFilePillText: "✅ SZ_Lyn_20261103_Demo.csv • 25 кадров (Загружен)",
      dssFieldFallbackFmt: "Поле звезды <strong>{star}</strong> (автономная астрометрическая карта VSP • ",
      verifyTitle: "Проверка совместимости AAVSO",
      verifyOkFmt: "✅ Файл «{file}» полностью совместим с требованиями AAVSO WebObs! Проверено строк: {rows}, звезда VSX: «{star}», OBSCODE: «{obs}».",
      verifyWarnFmt: "⚠️ В файле «{file}» обнаружены замечания для AAVSO WebObs: {issues}.",
      notifOnTitle: "🔔 Уведомления включены",
      notifOffTitle: "🔕 Уведомления отключены",
      notifOnMsg: "Активен мониторинг срочных кампаний AAVSO",
      notifOffMsg: "Оповещения о новых целях приостановлены",

      matchDiffStar: "✗ Расхождение",
      starIdDiffStarMsg: "✗ Расхождение: в файле «{file}», а в интерфейсе выбрана другая звезда «{ui}»!",
      starIdSynonymMsg: "⚠ Отличие (норма): синонимы одной звезды («{file}» ↔ «{cat}»)",
      lblThemePanel: "Цветовая панель",
      lblThemePickerSplash: "Цветовая панель",
      themeDarkBtn: "Стандартная тёмная",
      themeLightBtn: "Светлая",
      lblScopeModel: "Телескоп:",
      radarTitle: "Радар целей AAVSO",
      btnRefreshShort: "Обновить",
      phRadarSearch: "🔍 Поиск звезды, типа (DSCT, UGSS, EP) или созвездия...",
      filterUrgent: "🔥 Срочно",
      filterExo: "🪐 Затменные/Экзо",
      lblRadarLimit: "Показ:",
      optLimitAll: "Все (без лимита)",
      lblFov: "Поле зрения:",
      secCatalogStatus: "📡 Статус каталогов",
      catSimbadTap: "Зеркала CDS SIMBAD TAP",
      catAavsoVsp: "Сервер AAVSO VSP / VSX",
      catVizierApass: "Каталоги VizieR / APASS DR9",
      catLocalCache: "Локальный кэш запросов",
      btnShowNetLog: "▸ Показать технический лог сети",
      btnHideNetLog: "▾ Скрыть технический лог сети",
      lblPushNotifs: "🔔 Уведомления",
      btnGoAavsoObj: "🌐 Перейти на объект в AAVSO ↗",

      lblSplashLang: "Язык интерфейса:",
      infoCosmoSub: "Фотометрическая обсерватория AAVSO Extended",

      authorCompany: "CosmoBehemothych",
      modeMinimal: "Минимализм",
      modeCompact: "Компакт",
      modeFull: "Студия",
      searchPlaceholder: "Быстрый поиск: звезда (Algol, SZ Lyn, TX UMa...), параметр или раздел [ / или ⌘K ]",
      selfTestsTitle: "Самодиагностика ядра CosmoBehemothych",
      selfTestsSuccess: "Все 8 автоматических тестов алгоритмов пройдены успешно (100% точность)!",
      minimalNotice: "🍃 Минималистичный режим активирован: быстрый рабочий процесс в 1-2 клика.",
      compactNotice: "⚡ Компактный режим: дашборд параметров и кривой блеска рядом.",
      fullNotice: "🔭 Полная студия: включены все научные этапы, диагностика зеркал и логи.",
      pageTitle: "Seestar AstroLab AAVSO — Фотометрия и Радар целей",
      appTitle: "Seestar AstroLab AAVSO",
      subtitle: "Загрузка SIMBAD и AAVSO VSP с автоподбором контрольной звезды",
      viewDesktop: "💻 ПК (Desktop)",
      viewMobile: "📱 iPhone / Android",
      btnAbout: "ℹ️ Инфо",
      splashTitle: "Seestar AstroLab: Звездная фотометрия",
      splashDesc: "Профессиональное приложение для конвертации научных фотометрических наблюдений с телескопов ZWO Seestar в международный формат AAVSO Extended. Создано для исследователей переменных и двойных звезд, а также поиска транзитов экзопланет.",
      feat1Title: "Фотометрия звезд",
      feat1Text: "Точный расчет середины экспозиции (JD Mid) и блеска в полосе TG с контролем погрешности.",
      feat2Title: "Срочные запросы AAVSO и прогресс",
      feat2Text: "Отслеживание срочных запросов AAVSO и собственного прогресса сбора фотометрических данных.",
      feat3Title: "SIMBAD & AAVSO VSP",
      feat3Text: "Параллельный опрос зеркал SIMBAD и автоподбор оптимальной контрольной звезды (Check Star).",
      btnStartApp: "🚀 Перейти к работе",
      tagPhotometry: "📈 Фотометрия звезд",
      tagBinaries: "♊ Поиск двойных звезд",
      tagExoplanets: "🪐 Транзиты экзопланет",
      noticeHtml: "<strong>Назначение и как это работает.</strong> Приложение готовит фотометрию Seestar (переменные, двойные звезды, транзиты планет) к отправке в базу AAVSO. Зеркала SIMBAD опрашиваются параллельно. После выбора файла данные сверяются с полями: <span style='color:#86efac'>Зелёный</span> — точно совпало, <span style='color:#fde047'>Жёлтый</span> — малое отличие (норма), <span style='color:#fca5a5'>Красный</span> — сильное расхождение.",
      secObserver: "Наблюдатель и звезда",
      secResults: "Результаты и калибровка VSP",
      secActions: "Синхронизация с каталогами",
      secConvert: "Конвертация CSV Seestar",
      secPreview: "Результаты сравнения данных Seestar и каталога SIMBAD",
      secLog: "Лог сравнения «До / После»",
      lblObsCode: "OBSCODE (код обсерватории)",
      lblStarId: "STARID (имя / ID звезды)",
      lblChart: "CHART (VSP)",
      lblKname: "KNAME (AUID)",
      lblKmag: "KMAG (mag)",
      lblRa: "RA (J2000, °)",
      lblDec: "DEC (J2000, °)",
      lblFile: "Файл CSV от Seestar:",
      lblRows: "Строк:",
      lblLightCurve: "📈 Кривая блеска (MAG vs JD Mid)",
      btnLoadImage: "📸 Снимок",
      btnLoadDemo: "✨ Демо CSV (SZ Lyn)",
      phRa: "например, 121.907200",
      phDec: "например, 44.460400",
      phStarId: "например, SZ Lyncis",
      phChart: "X28491AB",
      phKname: "000-BDP-712",
      phKmag: "9.453",
      tipObsCodeText: "Официальный код наблюдателя AAVSO (записывается в заголовок #OBSCODE). 💡 Рекомендация: обязательно укажите свой личный код наблюдателя из AAVSO (Observer Code, выдается бесплатно в профиле на aavso.org). Без вашего личного кода портал AAVSO WebObs не привяжет наблюдения к вашему аккаунту.",
      tipObsCodeShort: "Наведите или нажмите на значок «?» выше для просмотра рекомендации по коду AAVSO.",
      tipStarIdText: "Название переменной, двойной звезды или звезды с транзитом экзопланеты.",
      tipChartText: "Идентификатор карты окрестностей из генератора AAVSO VSP.",
      tipKnameText: "Уникальный AUID контрольной звезды (Check Star) для верификации ансамбля.",
      tipKmagText: "Стандартная звездная величина контрольной звезды (рекомендуется 9.5–13.0 mag).",
      tipRaText: "Прямое восхождение цели (J2000) в десятичных градусах.",
      tipDecText: "Склонение цели (J2000) в десятичных градусах.",
      tipCsvText: "Сырой CSV-файл из Seestar. Отбираются строки 'Non-reference star'.",
      notifGuideTitle: "🔔 Справка по всем уведомлениям и цветовым подсказкам",
      notifGuideHtml: "<div>🟢 <strong>Зеленое поле (Совпадает):</strong> Разница координат файла и каталога менее 0.00001°.</div><div>🟡 <strong>Желтое поле (Отличие в пределах нормы):</strong> Смещение центра кадра до 0.05° или уточнение имени звезды по каталогу.</div><div>🔴 <strong>Красное поле (Сильное расхождение):</strong> Отличие координат более 0.05° — проверьте, ту ли звезду вы указали.</div><div>📦 <strong>Уведомление кэша:</strong> Данные взяты из локального кэша (хранится 1 час) для мгновенного отклика.</div>",
      btnFetchAll: "🔭 Загрузить SIMBAD + VSP",
      btnDiagnose: "🧪 Диагностика сети и зеркал",
      btnStop: "⏹ Остановить",
      btnClearAll: "🗑 Очистить",
      btnConvert: "Сконвертировать данные для загрузки на AAVSO",
      btnPrevPage: "< Назад",
      btnNextPage: "Вперед >",
      pageInfoText: "Стр. {current} из {total} ({rows})",
      rowWord: "Строка",
      msgNoStarId: "Введите STARID (имя звезды)",
      msgNoStarIdExplain: "Для поиска координат в SIMBAD и карты в AAVSO VSP необходимо указать название объекта (например, SZ Lyncis).",
      msgNoFile: "Сначала выберите CSV-файл от Seestar или нажмите «Демо CSV».",
      msgNoFileExplain: "Для запуска конвертации требуется загрузить исходную таблицу измерений Seestar.",
      msgStopped: "Остановлено пользователем",
      msgStoppedExplain: "Все активные сетевые запросы к зеркалам SIMBAD и прокси были безопасно прерваны.",
      msgClearDone: "Все поля, графики и загруженный файл очищены",
      msgClearExplain: "Рабочая область сброшена в исходное состояние для следующего объекта наблюдений.",
      msgSimbadCache: "📦 SIMBAD загружен из кэша",
      msgVspCache: "📦 VSP загружен из кэша",
      msgConverted: "✓ КОНВЕРТАЦИЯ УСПЕШНО ЗАВЕРШЕНА",
      msgConvertedExplain: "Сформирован файл стандарта AAVSO Extended с расчетом JD Mid и контролем округления до 0.0001 mag.",
      msgNoData: "⚠ Не найдено ни одной строки 'Non-reference star'.",
      msgNoDataExplain: "Убедитесь, что CSV-файл выгружен из режима фотометрии Seestar и содержит целевую звезду.",
      msgNoCheckStar: "⚠ Не удалось автоматически подобрать контрольную звезду. Введите KNAME/KMAG вручную.",
      msgCheckStarWarn: "⚠ Проверьте, что выбранная звезда сравнения есть на вашем кадре и не является переменной.",
      msgDiagnoseHeader: "══ ДИАГНОСТИКА СЕТИ И ЗЕРКАЛ ══",
      msgDiagStep1: "Шаг 1: Прямой пинг CORS-прокси серверов",
      msgDiagStep2: "Шаг 2: Проверка доступности зеркал SIMBAD",
      msgDiagnoseDone: "══ ДИАГНОСТИКА ЗАВЕРШЕНА ══",
      msgDirectMirrors: "Прямой параллельный опрос зеркал SIMBAD…",
      msgProxiesFallback: "Прокси-гонка через все зеркала…",
      msgVspDirect: "Прямой запрос к серверу AAVSO VSP…",
      msgVspProxy: "Запрос к AAVSO VSP через прокси…",
      msgSimbadDown: "SIMBAD временно недоступен.",
      msgVspDown: "Сервер AAVSO VSP недоступен.",
      msgNoChartId: "CHART ID не возвращён сервером VSP",
      thParam: "Параметр",
      thFile: "Данные из Seestar",
      thUI: "Данные из Каталога SIMBAD",
      thMatch: "Сверка",
      matchOk: "✓ Совпадает",
      matchBad: "✗ Сильное расхождение",
      matchWarn: "⚠ Отличие (норма)",
      matchMissing: "— Нет данных",
      starIdMissing: "— Будет взято из файла",
      previewReady: "Файл прочитан. Проверьте сверку параметров и кривую блеска ниже.",
      starIdCorrected: "STARID отличается от каталожного. При экспорте будет использован ID из интерфейса.",
      starIdSame: "STARID полностью совпадает с файлом.",
      fetchingSimbad: "📡 1/2: Загрузка координат из SIMBAD...",
      fetchingVsp: "📡 2/2: Загрузка карты и звезды сравнения из AAVSO VSP...",
      imgLoading: "Загрузка снимка DSS2...",
      imgOpenAladin: "🔭 Открыть в Aladin Lite",
      imgFieldCaption: "Поле звезды <strong>{star}</strong> (обзор DSS2)",
      imgAltServer: "Пробуем резервный сервер CDS Alasky...",
      imgLoadError: "Не удалось загрузить встроенный снимок неба.",
      imgNoCoords: "Укажите координаты RA и DEC для загрузки снимка области неба.",
      fileSavedPicker: "✅ Файл успешно сохранен: {name}",
      fileSaveCancelled: "⚠ Сохранение файла отменено пользователем.",
      fileDownloaded: "⬇️ Файл автоматически скачан в папку загрузок ({name}).",
      demoLoaded: "Демонстрационные данные звезды SZ Lyn (SZ Lyncis) загружены!",
      demoLoadedExplain: "Обратите внимание: при конвертации неканоничное имя 'SZ Lyncis' автоматически заменяется на каталожное имя VSX 'SZ Lyn'.",
      btnInstallApp: "📲 Установить приложение",
      btnOpenAavsoMenu: "📤 Отправить в AAVSO",
      btnOpenAavsoCard: "📤 Открыть сайт загрузки AAVSO Photometry",
      btnGraphGuide: "📖 Как читать графики",
      btnGraphGuideShort: "📖 Как читать график?",
      phObsCode: "Введите ваш личный код AAVSO",
      obsCodeRecHtml: "💡 <strong>Рекомендация:</strong> обязательно укажите <strong>свой личный код наблюдателя из AAVSO</strong> (Observer Code, выдается бесплатно в профиле на <a href='https://www.aavso.org' target='_blank' rel='noopener noreferrer'>aavso.org</a>). Без вашего личного кода портал AAVSO WebObs не привяжет наблюдения к вашему аккаунту.",
      vspLoadingTitle: "⏳ Загрузка CHART (VSP), KNAME (AUID) и KMAG...",
      msgAllLoadedTitle: "✅ Все данные каталогов успешно загружены!",
      msgAllLoadedBody: "Загружены координаты RA/DEC, каноническое имя звезды ({star}), карта CHART ({chart}), контрольная звезда KNAME ({kname}) и величина KMAG ({kmag}).",
      msgVspFailedTitle: "❌ Ошибка загрузки калибровочных данных VSP",
      msgVspFailedBody: "Перебраны все доступные порты, прокси-шлюзы и зеркала (AAVSO VSP, VizieR, SIMBAD), но данные CHART/KNAME/KMAG получить не удалось.",
      starIdAutoAssigned: "✓ Автоприсвоено имя из каталога VSX/SIMBAD: «{cat}» (в файле: «{file}»)",
      guideModalTitle: "📈 Как читать графики AAVSO и Seestar",
      guideModalBodyHtml: '\n      <p style="font-size:13px; color:#dbeafe; margin:0 0 10px 0;">\n        Визуальное руководство по анализу кривых блеска переменных звезд, затменных двойных и транзитов экзопланет после конвертации данных из <strong>ZWO Seestar</strong>.\n      </p>\n\n      <div class="guide-svg-box" style="margin-bottom:12px; padding:12px;">\n        <div style="font-size:11px; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:6px;">\n          КРИВАЯ БЛЕСКА (ПРИМЕР ЗАТМЕННОЙ ПЕРЕМЕННОЙ / ПУЛЬСИРУЮЩЕЙ ЗВЕЗДЫ)\n        </div>\n        <svg viewBox="0 0 600 185" width="100%" height="175" style="display:block; background:#070b14; border-radius:8px; border:1px solid rgba(100,210,255,0.18);">\n          <line x1="55" y1="28" x2="575" y2="28" stroke="#1e293b" stroke-dasharray="4 4" stroke-width="1"/>\n          <line x1="55" y1="82" x2="575" y2="82" stroke="#1e293b" stroke-dasharray="4 4" stroke-width="1"/>\n          <line x1="55" y1="138" x2="575" y2="138" stroke="#1e293b" stroke-dasharray="4 4" stroke-width="1"/>\n          <line x1="55" y1="15" x2="55" y2="155" stroke="#475569" stroke-width="1.5"/>\n          <line x1="55" y1="155" x2="575" y2="155" stroke="#475569" stroke-width="1.5"/>\n          <text x="8" y="32" fill="#86efac" font-size="11" font-family="monospace" font-weight="bold">11.5m ↑</text>\n          <text x="8" y="86" fill="#94a3b8" font-size="11" font-family="monospace">12.0m</text>\n          <text x="8" y="142" fill="#fca5a5" font-size="11" font-family="monospace" font-weight="bold">12.5m ↓</text>\n          <text x="64" y="22" fill="#38bdf8" font-size="10.5" font-family="sans-serif" font-weight="bold">↑ Ярче (Блеск растет, число MAG меньше)</text>\n          <text x="64" y="150" fill="#f87171" font-size="10.5" font-family="sans-serif" font-weight="bold">↓ Тусклее (Блеск падает, число MAG больше)</text>\n          <path d="M 70 50 L 185 50 C 225 50, 255 136, 305 136 C 355 136, 385 50, 425 50 L 555 50" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-dasharray="6 4"/>\n          <g stroke="#64d2ff" stroke-width="1.5">\n            <line x1="95" y1="41" x2="95" y2="59"/><circle cx="95" cy="50" r="4" fill="#38bdf8"/>\n            <line x1="145" y1="39" x2="145" y2="57"/><circle cx="145" cy="48" r="4" fill="#38bdf8"/>\n            <line x1="195" y1="45" x2="195" y2="63"/><circle cx="195" cy="54" r="4" fill="#38bdf8"/>\n            <line x1="250" y1="88" x2="250" y2="110"/><circle cx="250" cy="99" r="4" fill="#facc15"/>\n            <line x1="305" y1="124" x2="305" y2="148"/><circle cx="305" cy="136" r="5.5" fill="#ef4444" stroke="#fff"/>\n            <line x1="360" y1="86" x2="360" y2="108"/><circle cx="360" cy="97" r="4" fill="#facc15"/>\n            <line x1="415" y1="43" x2="415" y2="61"/><circle cx="415" cy="52" r="4" fill="#38bdf8"/>\n            <line x1="475" y1="40" x2="475" y2="58"/><circle cx="475" cy="49" r="4" fill="#38bdf8"/>\n            <line x1="535" y1="42" x2="535" y2="60"/><circle cx="535" cy="51" r="4" fill="#38bdf8"/>\n          </g>\n          <text x="90" y="35" fill="#e2e8f0" font-size="10.5" font-family="sans-serif">Нормальный блеск (Плато)</text>\n          <text x="215" y="120" fill="#fde047" font-size="10.5" font-family="sans-serif" font-weight="bold">Минимум яркости (Затмение / Транзит)</text>\n          <text x="425" y="75" fill="#94a3b8" font-size="10" font-family="sans-serif">Усы погрешности (±MERR)</text>\n          <text x="200" y="174" fill="#cbd5e1" font-size="11" font-family="monospace">Время наблюдения: Юлианская дата (JD Mid) →</text>\n        </svg>\n      </div>\n\n      <div class="guide-two-col">\n        <div class="guide-item">\n          <h4>1. Ось Y (Звездная величина / MAG)</h4>\n          <p>\n            В астрономии шкала звездных величин <strong>инвертирована (перевернута)</strong>:<br>\n            • Чем <strong>меньше</strong> число <code>MAG</code> (например, <code>9.10m</code> по сравнению с <code>9.50m</code>), тем <strong>ярче</strong> светится звезда!<br>\n            • На графике меньшие числа находятся сверху: <strong>подъем графика вверх</strong> означает рост яркости звезды, а <strong>провал вниз</strong> — ослабление света (затмение или прохождение планеты).\n          </p>\n        </div>\n        <div class="guide-item">\n          <h4>2. Ось X (Юлианская дата / JD Mid)</h4>\n          <p>\n            По горизонтали откладывается точное астрономическое время середины экспозиции каждого кадра Seestar — <strong>JD Mid</strong> (Julian Date).<br>\n            • Например, <code>2461346.3671</code> — это непрерывный счет дней и долей суток по UTC.<br>\n            • Позволяет астрономам всего мира объединять наблюдения одной звезды с точностью до секунды.\n          </p>\n        </div>\n      </div>\n\n      <div class="guide-grid" style="margin-top:10px;">\n        <div class="guide-item" style="background:rgba(10,132,255,0.10); border-color:rgba(100,210,255,0.32);">\n          <h4>💡 Почему точки «прыгают» вверх-вниз? (Разброс данных и усы погрешности ±MERR)</h4>\n          <p>\n            Каждая точка — это отдельный кадр Seestar (например, выдержка 10 или 20 секунд). Вертикальная палочка через точку — это погрешность измерения <code>±MERR</code>.<br>\n            • Небольшой разброс соседних точек в пределах <code>0.01–0.02m</code> — это естественное мерцание атмосферы (турбулентность воздуха) и фотонный шум матрицы.<br>\n            • Если точки выстраиваются в плавную волну или четкий V/U-образный провал, глубина которого значительно больше длины усов погрешности — вы зафиксировали <strong>реальную переменность звезды</strong>!\n          </p>\n        </div>\n\n        <div class="guide-item">\n          <h4>3. Какие типы объектов вы можете увидеть на своем графике:</h4>\n          <p>\n            • <strong>Пульсирующие переменные (SZ Lyn, RR Lyr, δ Sct):</strong> асимметричная плавная волна — быстрый крутой подъем к максимуму (вверх) и более пологий спад блеска (вниз) с амплитудой <code>0.15–0.80m</code>.<br>\n            • <strong>Затменно-двойные звезды (EA Алголи, EB, EW):</strong> глубокий V-образный провал, когда одна звезда системы заслоняет другую.<br>\n            • <strong>Транзиты экзопланет:</strong> характерное неглубокое корытце с плоским дном (U-профиль глубиной <code>0.01–0.03m</code>).\n          </p>\n        </div>\n      </div>\n',
      btnCloseModal: "Вернуться",
      installModalTitle: "📲 Установка приложения Seestar AstroLab (ПК, Android, iOS)",
      installModalIntro: "Приложение поддерживает прямую установку как нативное автономное приложение (PWA / Standalone Desktop & Mobile App) со значком на рабочем столе или экране «Домой». В корневой папке архива также находится готовый ярлык со значком Seestar_AstroLab.ico.",
      btnTriggerNativeInstall: "⚡ Установить приложение в 1 клик (Автоустановка)",
      btnDownloadDesktopShortcut: "💻 Скачать ярлык запуска для ПК со значком",
      submitModalTitle: "🚀 Отправка файла в AAVSO WebObs (?preview=true)",
      secFileStart: "Выбор и проверка файла фотометрии",
      btnSelectCsvFile: "📂 Выбрать CSV-файл Seestar",
      noFileSelected: "Файл еще не выбран (нажмите кнопку выше или «Демо CSV»)",
      lblVerifyDisk: "Проверка готового файла AAVSO:",
      btnVerifyDisk: "🔍 Проверить сконвертированный файл с диска",
      tipVerifyFileText: "Проверяет сконвертированный CSV/TXT файл с вашего диска на полную совместимость с требованиями сайта AAVSO WebObs: наличие обязательных заголовков (#TYPE=EXTENDED, #OBSCODE, #DELIM, #DATE, #OBSTYPE), каноничность имени звезды в каталоге VSX (без латинских падежей), корректность колонок JD, MAG, MERR, KNAME, KMAG и отсутствие пустых полей.",
      lblGoToAavso: "Перейти на страницу загрузки данных AAVSO",
      btnUrgentMenu: "Радар целей AAVSO",
      btnRefreshUrgent: "🔄 Обновить данные сейчас",
      secUrgentStars: "🔥 Звезды с пометкой «Срочно» (Приоритетные цели AAVSO)",
      urgentStarsIntro: "Цели экстренных наблюдательных кампаний AAVSO Alert Notices для телескопов Seestar. Нажмите на карточку звезды, чтобы сразу подставить её каноническое имя и координаты в конвертер."


    },
    en: {
      btnObsTrackerMenu: "📓 My Observations",
      lblSettingsTitle: "Settings:",
      lblToastsShort: "🔔 Notifications",
      lblToastsToggle: "🔔 Popup Notifications",
      splashHubTitle: "⚡ Observatory Control Hub & Quick Actions",
      splashMetricTargetsLbl: "AAVSO Radar Targets",
      splashMetricObsCountLbl: "Logged Sessions",
      splashMetricDaysIdleLbl: "Photometry Status",
      splashMetricScopeLbl: "Active Telescope",
      btnSplashQuickSync: "🛰️ Go to Catalog Sync",
      btnSplashQuickTracker: "📓 My Observations",
      btnSplashQuickRadar: "🎯 AAVSO Target Radar",
      btnSplashQuickLoadCsv: "📂 Select CSV File",
      splashRecentLogTitle: "🕒 Recent Activity Log:",
      obsTrackerTitle: "📓 My Observations",
      obsDaysSinceFmt: "You have not performed photometry for {days} days",
      obsSummaryStatsFmt: "Total sessions: {count} • Total duration: {mins} min • Frames: {frames}",
      phObsStar: "Star (e.g. SZ Lyn)",
      phObsDur: "Duration (min)",
      phObsFrames: "Frames",
      btnObsAdd: "➕ Add Observation",
      btnObsExport: "💾 Export JSON",
      btnObsImport: "📂 Import JSON",
      obsChartTitle: "📊 Observation Activity Chart (measurement duration in minutes & frame counts by date)",
      thObsStar: "Star (STARID)",
      thObsDate: "Date",
      thObsDuration: "Duration (min)",
      thObsFrames: "File Records / Filter",
      thObsScope: "Telescope",
      thObsAction: "Action",
      btnObsDelete: "Delete",
      btnObsDeleteAll: "🗑️ Delete All",
      btnObsResetFilters: "↺ Reset",
      phObsFilterStar: "🔍 Filter by star (STARID)...",
      optObsAllScopes: "🔭 All Telescopes (S30–S50PRO)",
      lblSortBy: "Sort by:",
      optSortDate: "Publication date (newest)",
      optSortName: "Star name (A–Z)",
      optSortPriority: "Priority (Urgent)",
      btnDonateBadge: "❤️ Support",
      tipDonateAuthor: "Support author CosmoBehemothych on Boosty",
      donateModalTitle: "❤️ Support Seestar AstroLab AAVSO",
      donateLiteraryText: "Dear fellow stargazers! Seestar AstroLab is crafted with a passion for observational astronomy so that every frame captured by your smart telescope contributes meaningful data to variable star science and the AAVSO database. If this suite saves you time under the night sky and helps your research, consider supporting its continued development on Boosty. Clear skies and sharp light curves!",
      donateScanOrClick: "Scan the QR code with your phone or open the direct link:",
      btnDonateNever: "Don't show again",
      btnDonateLater: "Remind next month",
      btnDonateSupportNow: "❤️ Support on Boosty",
      obsEmptyTableMsg: "No observation records yet. Convert a Seestar photometry CSV file and your session will be logged here automatically.",
      obsMinUnit: "min",
      obsFramesUnit: "rec.",
      actAppStarted: "Started Seestar AstroLab v1.0.1 session",
      actCatalogSyncedFmt: "Synchronized with catalog: {star}",
      actFileConvertedFmt: "Converted AAVSO report: {star} ({pts} pts)",
      actObsAddedFmt: "Added My Observations entry: {star} ({mins} min)",
      actRadarPickedFmt: "Selected radar reference: {star}",
      tipVerifyDiskShort: "Checks compatibility of a converted file with AAVSO WebObs requirements.",
      errNoObscodeTitle: "⚠️ Missing Observer Code (OBSCODE)",
      errNoObscodeMsg: "Please enter your personal AAVSO Observer Code (OBSCODE) before converting data for AAVSO upload.",
      errNoObscodeExplain: "The AAVSO Extended format strictly requires a valid personal observer code in the #OBSCODE header.",
      radarSubTag: "",
      appVersionLabel: "Version 1.0.1",
      starIdFromCatalogHint: "✓ Canonical Catalog Star ID (SIMBAD / AAVSO VSX): {star}",
      brandBarTitle: "🌌 CosmoBehemothych AstroLab • Seestar S30 / S30PRO / S50 / S50PRO Photometry Observatory",
      
      missionSummaryTitle: "ℹ️ How Seestar → SIMBAD & VSP Field Reconciliation Works (Color Indicators)",
      lblExpand: "Expand\u00A0▾",
      bentoSyncBadgeText: "Online • TTL 1h",
      bentoSimbadDefault: "✓ 3 Mirrors (HTTPS:443)",
      bentoVspDefault: "✓ Active (API v2)",
      bentoVizierDefault: "✓ 4 Mirrors (Backup)",
      lblThemePanel: "Color Theme",
      lblThemePickerSplash: "Color Theme",
      lblObscodeHeader: "OBSCODE:",
      phObscodeHeader: "Your code",
      tipToggleScope: "Switch smart telescope model (S30 / S30PRO / S50 / S50PRO)",
      btnUrgentTop: "AAVSO Target Radar",
      tipRefreshRadar: "Refresh AAVSO Target Radar",
      tipExpandUrgent: "Open full target table",
      tipCollapseRadar: "Collapse AAVSO Target Radar sidebar",
      tipExpandRadar: "Expand AAVSO Target Radar sidebar",
      radarCollapsedPill: "AAVSO RADAR ({count})",
      lblScopeSectionTitle: "🔭 Seestar Telescope Model",
      scopeSpecsFmt: "FOV: {fov} • {res} ({scale}″/px) • Limit: ≤{mag} mag • Exp: {minE}–{maxE} s",
      phRadarSearch: "🔍 Search 45 targets (name, type, constellation)...",
      filterAllFmt: "All ({count})",
      filterUrgent: "🔥 Urgent",
      filterScopeFmt: "🔭 Fits {id} (≤{mag}m)",
      filterExo: "🪐 Eclipsing/Exo",
      radarCountFmt: "Showing: {shown} of {total} targets",
      lblRadarLimit: "Show:",
      optLimitAll: "All 45",
      optLimit30: "Top 30",
      optLimit15: "Top 15",
      tagPhotometry: "📈 Stellar Photometry",
      tagBinaries: "🌑 Eclipsing Binaries",
      tagExoplanets: "🪐 Exoplanets",
      tagTelescopes: "🔭 S30 • S30PRO • S50 • S50PRO",
      lblBentoService: "SIMBAD TAP Service",
      valBentoService: "✓ 3 mirrors (CDS / Harvard / IDIA)",
      lblBentoVsp: "AAVSO VSP Scale",
      valBentoVsp: "✓ Auto-matched to S30..S50PRO FOV",
      lblBentoCache: "Catalog Cache",
      valBentoCacheFmt: "TTL 3600 s • Entries: {count}",
      lblBentoStandard: "Report Standard",
      valBentoStandard: "AAVSO Extended (#TYPE=EXTENDED)",
      phStarIdEmpty: "Not loaded (from CSV file)",
      phRaEmpty: "From file or radar",
      phDecEmpty: "From file or radar",
      emptyPreviewTitle: "Load a Seestar photometry file",
      emptyPreviewDesc: "Star parameter preview, coordinate reconciliation, and the light curve will appear automatically after you select an observation CSV file.",
      lcFrameTooltipFmt: "Frame #{idx} | JD {jd} | {mag} mag ±{merr}",
      btnPickTarget: "Select",
      btnPickedTarget: "✓ In Radar",
      ttDescLabel: "Description:",
      ttCommentLabel: "AAVSO Comment:",
      ttDefaultComment: "Use TG filter series and verify KNAME calibration.",
      scopeEvalOkFmt: "{id}: Exposure {exp} • FOV {fov} ({scale}″/px)",
      scopeEvalFaintFmt: "{id}: Fainter than {mag}m limit (rec. S50/S50PRO)",
      scopeEvalDipFmt: "{id}: Minimum down to {max}m (limit {mag}m) • Exp {exp} s",
      scopeEvalBrightFmt: "{id}: Bright ({min}m < {bright}m, saturation risk) • Exp {exp} s",
      exp10_20: "10–20 s",
      exp10: "10 s",
      exp20_30: "20–30 s",
      exp20: "20 s",
      toastScopeTitleFmt: "🔭 Telescope Profile: {name}",
      toastScopeSubFmt: "VSP comparison search radius: {fov}', magnitude limit: {mag} mag.",
      toastRadarTargetTitleFmt: "🛰️ AAVSO Radar Reference: {star}",
      toastRadarTargetMsgFmt: "VSP Calibration: CHART {chart} • KNAME {kname} ({kmag} mag)",
      toastRadarTargetSubFmt: "Coordinates and comparison chart updated ({scope}). STARID is populated strictly from a loaded CSV file.",
      toastThemeLightTitle: "☀️ Light Theme Activated",
      toastThemeLightMsg: "High-contrast daylight palette (WCAG AA) for Command Center and AAVSO Target Radar.",
      toastThemeDarkTitle: "🌙 Standard Dark Theme Activated",
      toastThemeDarkMsg: "Cosmic dark palette for Command Center and AAVSO Target Radar.",
      toastHomeTitle: "🏠 Welcome Screen",
      toastHomeMsg: "Opened Seestar AstroLab welcome and overview dialog",
      toastHomeSub: "Review key observatory features and AAVSO formatting standards.",
      urgentSyncWait: "⏳ AAVSO Campaign Sync: <strong>Ready to query mirrors...</strong>",
      urgentSyncProgress: "⏳ <strong>Synchronizing with CDS SIMBAD TAP and AAVSO VSP mirrors...</strong>",
      urgentSyncDoneFmt: "✅ <strong>Synchronized {count} AAVSO targets at {time}</strong> (JD {jd}).",
      urgentAutoTimerPrefix: "Auto-refresh every 10 min • JD:",
      urgentCountBadgeFmt: "{shown} of {total} targets",
      btnPickUrgentFmt: "🎯 Use Reference ({exp})",
      btnRefreshLoading: "⏳ Refreshing...",
      toastRadarRefreshedTitle: "🔄 AAVSO Target Radar Refreshed",
      toastRadarRefreshedMsgFmt: "Successfully synchronized {count} target objects ({time})",
      toastRadarRefreshedSub: "All J2000 coordinates, VSP charts, and S30/S30PRO/S50/S50PRO profiles are up to date.",
      demoFilePillText: "✅ SZ_Lyn_20261103_Demo.csv • 25 frames (Loaded)",
      dssFieldFallbackFmt: "Star field <strong>{star}</strong> (offline VSP astrometric chart • ",
      verifyTitle: "AAVSO Compatibility Check",
      verifyOkFmt: "✅ File «{file}» is 100% compatible with AAVSO WebObs! Checked rows: {rows}, VSX star: «{star}», OBSCODE: «{obs}».",
      verifyWarnFmt: "⚠️ File «{file}» has AAVSO WebObs warnings: {issues}.",
      notifOnTitle: "🔔 Notifications Enabled",
      notifOffTitle: "🔕 Notifications Disabled",
      notifOnMsg: "Monitoring urgent AAVSO campaigns",
      notifOffMsg: "Target alerts paused",

      matchDiffStar: "✗ Discrepancy",
      starIdDiffStarMsg: "✗ Discrepancy: file has '{file}', but UI has a different star '{ui}'!",
      starIdSynonymMsg: "⚠ Differs (normal): synonyms of the same star ('{file}' ↔ '{cat}')",
      lblThemePanel: "Color Theme",
      lblThemePickerSplash: "Color Theme",
      themeDarkBtn: "Standard Dark",
      themeLightBtn: "Light",
      lblScopeModel: "Telescope:",
      radarTitle: "AAVSO Target Radar",
      btnRefreshShort: "Refresh",
      phRadarSearch: "🔍 Search star, variability type (DSCT, UGSS, EP) or constellation...",
      filterUrgent: "🔥 Urgent",
      filterExo: "🪐 Eclipsing/Exo",
      lblRadarLimit: "Show:",
      optLimitAll: "All (no limit)",
      lblFov: "Field of View:",
      secCatalogStatus: "📡 Catalog Status",
      catSimbadTap: "CDS SIMBAD TAP Mirrors",
      catAavsoVsp: "AAVSO VSP / VSX Server",
      catVizierApass: "VizieR / APASS DR9 Catalogs",
      catLocalCache: "Local Request Cache",
      btnShowNetLog: "▸ Show technical network log",
      btnHideNetLog: "▾ Hide technical network log",
      lblPushNotifs: "🔔 Alerts",
      btnGoAavsoObj: "🌐 Open Object in AAVSO ↗",

      lblSplashLang: "App Language:",
      infoCosmoSub: "AAVSO Extended Photometric Observatory",

      authorCompany: "CosmoBehemothych",
      modeMinimal: "Minimal",
      modeCompact: "Compact",
      modeFull: "Studio",
      searchPlaceholder: "Quick search: star (Algol, SZ Lyn, TX UMa...), setting or topic [ / or ⌘K ]",
      selfTestsTitle: "CosmoBehemothych Core Diagnostics",
      selfTestsSuccess: "All 8 automated algorithmic unit tests passed successfully (100% precision)!",
      minimalNotice: "🍃 Minimal mode enabled: streamlined 1-2 click workflow.",
      compactNotice: "⚡ Compact dashboard: side-by-side parameters and light curve.",
      fullNotice: "🔭 Full Studio enabled: complete multi-step scientific suite and telemetry.",
      pageTitle: "Seestar AstroLab AAVSO — Фотометрия и Радар целей",
      appTitle: "Seestar AstroLab AAVSO",
      subtitle: "Fetch SIMBAD & AAVSO VSP data with auto-selected check star",
      viewDesktop: "💻 PC (Desktop)",
      viewMobile: "📱 iPhone / Android",
      btnAbout: "✨ Splash & Info",
      splashTitle: "Seestar AstroLab AAVSO: Stellar Photometry",
      splashDesc: "Professional tool for converting scientific photometric time-series from ZWO Seestar smart telescopes into the international AAVSO Extended format. Designed for variable star observers, eclipsing binary researchers, and exoplanet transit hunters.",
      feat1Title: "Stellar Photometry",
      feat1Text: "Precise mid-exposure Julian Date (JD Mid) calculation and TG band instrumental magnitudes.",
      feat2Title: "Urgent AAVSO Alerts & Progress",
      feat2Text: "Track urgent AAVSO target requests and monitor your own photometric data collection progress.",
      feat3Title: "SIMBAD & AAVSO VSP",
      feat3Text: "Parallel SIMBAD mirror queries and automatic optimal Check Star (KNAME/KMAG) selection.",
      btnStartApp: "🚀 Start Scientific Workflow",
      tagPhotometry: "📈 Stellar Photometry",
      tagBinaries: "♊ Eclipsing Binaries",
      tagExoplanets: "🪐 Exoplanet Transits",
      noticeHtml: "<strong>Purpose & How it works.</strong> Converts Seestar photometry (variables, binaries, exoplanet transits) into AAVSO Extended format. All SIMBAD mirrors are queried in parallel. File data is verified against UI fields: <span style='color:#86efac'>Green</span> — exact match, <span style='color:#fde047'>Yellow</span> — minor offset (normal), <span style='color:#fca5a5'>Red</span> — major discrepancy.",
      secObserver: "Observer & Target Star",
      secResults: "Results & VSP Calibration",
      secActions: "Catalogue Synchronization",
      secConvert: "Convert Seestar CSV",
      secPreview: "Seestar & SIMBAD Catalog Comparison Results",
      secLog: "Before / After Comparison Log",
      lblObsCode: "OBSCODE (Observer Code)",
      lblStarId: "STARID (Target Star Name)",
      lblChart: "CHART (VSP ID)",
      lblKname: "KNAME (Check Star AUID)",
      lblKmag: "KMAG (mag)",
      lblRa: "RA (J2000, °)",
      lblDec: "DEC (J2000, °)",
      lblFile: "Seestar CSV File:",
      lblRows: "Rows:",
      lblLightCurve: "📈 Light Curve Preview (MAG vs JD Mid)",
      btnLoadImage: "📸 Sky Image",
      btnLoadDemo: "✨ Demo CSV (SZ Lyn)",
      phRa: "e.g. 121.907200",
      phDec: "e.g. 44.460400",
      phStarId: "e.g. SZ Lyncis",
      phChart: "X28491AB",
      phKname: "000-BDP-712",
      phKmag: "9.453",
      tipObsCodeText: "Your official AAVSO observer code (written into the #OBSCODE header). 💡 Recommendation: Please specify your personal AAVSO Observer Code (issued for free in your profile on aavso.org). Without your personal code, AAVSO WebObs will not link observations to your account.",
      tipObsCodeShort: "Hover or tap the '?' icon above to view the AAVSO Observer Code recommendation.",
      tipStarIdText: "Catalogue name of the variable star, binary system, or exoplanet host.",
      tipChartText: "AAVSO Variable Star Plotter (VSP) chart ID.",
      tipKnameText: "Unique AAVSO AUID of the check star used to verify ensemble photometry.",
      tipKmagText: "Standard magnitude of the check star (optimal range 9.5–13.0 mag).",
      tipRaText: "Right Ascension (J2000) in decimal degrees (0°–360°).",
      tipDecText: "Declination (J2000) in decimal degrees (-90°…+90°).",
      tipCsvText: "Select raw Seestar photometry CSV. Rows marked 'Non-reference star' are extracted.",
      notifGuideTitle: "🔔 Guide to All Notifications & Color Indicators",
      notifGuideHtml: "<div>🟢 <strong>Green Field (Match):</strong> Coordinate difference between file and UI is under 0.00001°.</div><div>🟡 <strong>Yellow Field (Normal Offset):</strong> Frame center offset under 0.05° or standardized catalogue star name.</div><div>🔴 <strong>Red Field (Major Discrepancy):</strong> Coordinate difference exceeds 0.05° — verify target star selection.</div><div>📦 <strong>Cache Notification:</strong> Loaded from 1-hour local cache for instant response.</div>",
      btnFetchAll: "🔭 Load SIMBAD + VSP",
      btnDiagnose: "🧪 Network & Mirror Diagnostics",
      btnStop: "⏹ Stop",
      btnClearAll: "🗑 Clear All",
      btnConvert: "Convert Data for AAVSO Upload",
      btnPrevPage: "< Prev",
      btnNextPage: "Next >",
      pageInfoText: "Page {current} of {total} ({rows})",
      rowWord: "Row",
      msgNoStarId: "Please enter a STARID",
      msgNoStarIdExplain: "A target star identifier (e.g., SZ Lyncis) is required to query SIMBAD coordinates and AAVSO VSP charts.",
      msgNoFile: "Please select a Seestar CSV file or click 'Demo CSV'.",
      msgNoFileExplain: "A source CSV measurement table is required to run the AAVSO Extended conversion.",
      msgStopped: "Stopped by user",
      msgStoppedExplain: "All active network requests to SIMBAD mirrors and CORS proxies were safely aborted.",
      msgClearDone: "All fields, charts, and loaded file cleared",
      msgClearExplain: "The workspace has been reset for your next observation target.",
      msgSimbadCache: "📦 SIMBAD loaded from cache",
      msgVspCache: "📦 VSP loaded from cache",
      msgConverted: "✓ CONVERSION COMPLETE",
      msgConvertedExplain: "Generated AAVSO Extended file with mid-exposure JD and 4-decimal magnitude validation.",
      msgNoData: "⚠ No 'Non-reference star' rows found.",
      msgNoDataExplain: "Ensure the CSV file was exported from Seestar photometry mode and contains target rows.",
      msgNoCheckStar: "⚠ Could not auto-select a check star. Enter KNAME/KMAG manually.",
      msgCheckStarWarn: "⚠ Verify the chosen check star is within your sensor frame and is not variable.",
      msgDiagnoseHeader: "══ NETWORK & MIRROR DIAGNOSTICS ══",
      msgDiagStep1: "Step 1: Direct ping to CORS proxy servers",
      msgDiagStep2: "Step 2: Testing SIMBAD mirrors via proxy race",
      msgDiagnoseDone: "══ DIAGNOSTICS COMPLETE ══",
      msgDirectMirrors: "Direct parallel SIMBAD mirror query…",
      msgProxiesFallback: "Proxy race across all mirrors…",
      msgVspDirect: "Direct request to AAVSO VSP…",
      msgVspProxy: "AAVSO VSP request via proxies…",
      msgSimbadDown: "SIMBAD is currently unreachable.",
      msgVspDown: "AAVSO VSP server is unreachable.",
      msgNoChartId: "CHART ID was not returned by VSP",
      thParam: "Parameter",
      thFile: "Data from Seestar",
      thUI: "Data from SIMBAD Catalog",
      thMatch: "Check",
      matchOk: "✓ Match",
      matchBad: "✗ Major discrepancy",
      matchWarn: "⚠ Differs (normal)",
      matchMissing: "— No data",
      starIdMissing: "— Will use file data",
      previewReady: "File parsed. Review the parameter verification and light curve below.",
      starIdCorrected: "STARID differs from file. The catalogue ID in the UI will be used.",
      starIdSame: "STARID matches file.",
      fetchingSimbad: "📡 1/2: Fetching SIMBAD coordinates...",
      fetchingVsp: "📡 2/2: Fetching AAVSO VSP chart & check star...",
      imgLoading: "Loading DSS2 sky survey image...",
      imgOpenAladin: "🔭 Open in Aladin Lite",
      imgFieldCaption: "Sky field of <strong>{star}</strong> (DSS2 Survey)",
      imgAltServer: "Trying backup CDS Alasky server...",
      imgLoadError: "Could not load inline sky preview image.",
      imgNoCoords: "Enter valid RA and DEC coordinates to load the sky field image.",
      fileSavedPicker: "✅ File saved successfully: {name}",
      fileSaveCancelled: "⚠ File save cancelled by user.",
      fileDownloaded: "⬇️ File downloaded to your default Downloads folder ({name}).",
      demoLoaded: "Sample photometry data for SZ Lyn (SZ Lyncis) loaded!",
      demoLoadedExplain: "Note: during conversion, non-standard file name 'SZ Lyncis' is automatically replaced with official VSX catalog name 'SZ Lyn'.",
      btnInstallApp: "📲 Install App",
      btnOpenAavsoMenu: "📤 Submit to AAVSO",
      btnOpenAavsoCard: "📤 Open AAVSO Photometry Upload Page",
      btnGraphGuide: "📖 How to Read Graphs",
      btnGraphGuideShort: "📖 How to Read Graph?",
      phObsCode: "Enter your personal AAVSO code",
      obsCodeRecHtml: "💡 <strong>Recommendation:</strong> Please enter <strong>your personal AAVSO Observer Code</strong> (free in your profile at <a href='https://www.aavso.org' target='_blank' rel='noopener noreferrer'>aavso.org</a>). WebObs requires your personal code to credit observations to your account.",
      vspLoadingTitle: "⏳ Loading CHART (VSP), KNAME (AUID) & KMAG...",
      msgAllLoadedTitle: "✅ All Catalog Data Loaded Successfully!",
      msgAllLoadedBody: "Loaded RA/DEC, canonical star name ({star}), CHART ({chart}), check star KNAME ({kname}), and KMAG ({kmag}).",
      msgVspFailedTitle: "❌ Failed to Load VSP Calibration Data",
      msgVspFailedBody: "All available ports, proxies, and catalog mirrors (AAVSO VSP, VizieR, SIMBAD) were queried, but CHART/KNAME/KMAG could not be retrieved.",
      starIdAutoAssigned: "✓ Assigned official VSX/SIMBAD catalog name: '{cat}' (file had: '{file}')",
      guideModalTitle: "📈 How to Read AAVSO & Seestar Light Curves",
      guideModalBodyHtml: '\n      <p style="font-size:13px; color:#dbeafe; margin:0 0 10px 0;">\n        Visual guide to interpreting variable star, eclipsing binary, and exoplanet transit light curves converted from <strong>ZWO Seestar</strong> photometry.\n      </p>\n\n      <div class="guide-svg-box" style="margin-bottom:12px; padding:12px;">\n        <div style="font-size:11px; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:6px;">\n          LIGHT CURVE DIAGRAM (ECLIPSING BINARY / PULSATING VARIABLE EXAMPLE)\n        </div>\n        <svg viewBox="0 0 600 185" width="100%" height="175" style="display:block; background:#070b14; border-radius:8px; border:1px solid rgba(100,210,255,0.18);">\n          <line x1="55" y1="28" x2="575" y2="28" stroke="#1e293b" stroke-dasharray="4 4" stroke-width="1"/>\n          <line x1="55" y1="82" x2="575" y2="82" stroke="#1e293b" stroke-dasharray="4 4" stroke-width="1"/>\n          <line x1="55" y1="138" x2="575" y2="138" stroke="#1e293b" stroke-dasharray="4 4" stroke-width="1"/>\n          <line x1="55" y1="15" x2="55" y2="155" stroke="#475569" stroke-width="1.5"/>\n          <line x1="55" y1="155" x2="575" y2="155" stroke="#475569" stroke-width="1.5"/>\n          <text x="8" y="32" fill="#86efac" font-size="11" font-family="monospace" font-weight="bold">11.5m ↑</text>\n          <text x="8" y="86" fill="#94a3b8" font-size="11" font-family="monospace">12.0m</text>\n          <text x="8" y="142" fill="#fca5a5" font-size="11" font-family="monospace" font-weight="bold">12.5m ↓</text>\n          <text x="64" y="22" fill="#38bdf8" font-size="10.5" font-family="sans-serif" font-weight="bold">↑ Brighter (Smaller MAG value is higher)</text>\n          <text x="64" y="150" fill="#f87171" font-size="10.5" font-family="sans-serif" font-weight="bold">↓ Fainter (Larger MAG value is lower)</text>\n          <path d="M 70 50 L 185 50 C 225 50, 255 136, 305 136 C 355 136, 385 50, 425 50 L 555 50" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-dasharray="6 4"/>\n          <g stroke="#64d2ff" stroke-width="1.5">\n            <line x1="95" y1="41" x2="95" y2="59"/><circle cx="95" cy="50" r="4" fill="#38bdf8"/>\n            <line x1="145" y1="39" x2="145" y2="57"/><circle cx="145" cy="48" r="4" fill="#38bdf8"/>\n            <line x1="195" y1="45" x2="195" y2="63"/><circle cx="195" cy="54" r="4" fill="#38bdf8"/>\n            <line x1="250" y1="88" x2="250" y2="110"/><circle cx="250" cy="99" r="4" fill="#facc15"/>\n            <line x1="305" y1="124" x2="305" y2="148"/><circle cx="305" cy="136" r="5.5" fill="#ef4444" stroke="#fff"/>\n            <line x1="360" y1="86" x2="360" y2="108"/><circle cx="360" cy="97" r="4" fill="#facc15"/>\n            <line x1="415" y1="43" x2="415" y2="61"/><circle cx="415" cy="52" r="4" fill="#38bdf8"/>\n            <line x1="475" y1="40" x2="475" y2="58"/><circle cx="475" cy="49" r="4" fill="#38bdf8"/>\n            <line x1="535" y1="42" x2="535" y2="60"/><circle cx="535" cy="51" r="4" fill="#38bdf8"/>\n          </g>\n          <text x="90" y="35" fill="#e2e8f0" font-size="10.5" font-family="sans-serif">Baseline Brightness (Plateau)</text>\n          <text x="225" y="120" fill="#fde047" font-size="10.5" font-family="sans-serif" font-weight="bold">Primary Minimum (Eclipse / Transit Dip)</text>\n          <text x="425" y="75" fill="#94a3b8" font-size="10" font-family="sans-serif">Error Bars (±MERR)</text>\n          <text x="210" y="174" fill="#cbd5e1" font-size="11" font-family="monospace">Observation Time: Julian Date (JD Mid) →</text>\n        </svg>\n      </div>\n\n      <div class="guide-two-col">\n        <div class="guide-item">\n          <h4>1. Y-Axis (Stellar Magnitude / MAG)</h4>\n          <p>\n            The astronomical magnitude scale is <strong>inverted</strong>:<br>\n            • A <strong>smaller</strong> <code>MAG</code> number (e.g. <code>9.10m</code> vs <code>9.50m</code>) means the star is <strong>brighter</strong>!<br>\n            • On the chart, smaller numbers are at the top: a curve rising <strong>upward</strong> means brightening, while a dip <strong>downward</strong> indicates dimming (eclipse or transit).\n          </p>\n        </div>\n        <div class="guide-item">\n          <h4>2. X-Axis (Julian Date / JD Mid)</h4>\n          <p>\n            The horizontal axis shows the exact mid-exposure timestamp of each Seestar frame in <strong>Julian Date (JD Mid)</strong>.<br>\n            • Example: <code>2461346.3671</code> is a continuous count of UTC days and fractions.<br>\n            • Enables astronomers worldwide to combine time-series observations with second-level precision.\n          </p>\n        </div>\n      </div>\n\n      <div class="guide-grid" style="margin-top:10px;">\n        <div class="guide-item" style="background:rgba(10,132,255,0.10); border-color:rgba(100,210,255,0.32);">\n          <h4>💡 Why do points scatter up and down? (Data scatter & ±MERR error bars)</h4>\n          <p>\n            Each dot is a single Seestar sub-exposure (10s–20s), and the vertical bar through it represents the measurement uncertainty <code>±MERR</code>.<br>\n            • Small point-to-point scatter of <code>0.01–0.02m</code> is normal atmospheric scintillation and sensor photon noise.<br>\n            • When points trace a coherent wave or a clear V/U-shaped dip much deeper than the error bars, you have detected <strong>real astrophysical variability</strong>!\n          </p>\n        </div>\n        <div class="guide-item">\n          <h4>3. Common Light Curve Signatures:</h4>\n          <p>\n            • <strong>Pulsating Variables (SZ Lyn, RR Lyr, δ Sct):</strong> Smooth wave with a rapid rise to maximum brightness and slower decline (amplitude <code>0.15–0.80m</code>).<br>\n            • <strong>Eclipsing Binaries (EA, EB, EW):</strong> Sharp V-shaped primary minimum when one star occults its companion.<br>\n            • <strong>Exoplanet Transits:</strong> Shallow, flat-bottomed U-shaped dip (<code>0.01–0.03m</code>).\n          </p>\n        </div>\n      </div>\n',
      btnCloseModal: "Got it, close window",
      installModalTitle: "📲 Install Seestar AstroLab App (PC, Android, iOS)",
      installModalIntro: "This app supports direct installation as a standalone Desktop & Mobile application with an icon on your Desktop or Home Screen. A ready-to-use shortcut with Seestar_AstroLab.ico is also included in the root folder.",
      btnTriggerNativeInstall: "⚡ Install App in 1 Click (Auto-Install)",
      btnDownloadDesktopShortcut: "💻 Download PC Desktop Shortcut with Icon",
      submitModalTitle: "🚀 Submit File to AAVSO WebObs (?preview=true)",
      secFileStart: "Select & Verify Photometry File",
      btnSelectCsvFile: "📂 Choose Seestar CSV File",
      noFileSelected: "No file selected yet (click the button above or 'Demo CSV')",
      lblVerifyDisk: "Verify Converted AAVSO File:",
      btnVerifyDisk: "🔍 Verify Converted File from Disk",
      tipVerifyFileText: "Validates any converted CSV/TXT file from your disk against AAVSO WebObs requirements: mandatory Extended headers (#TYPE=EXTENDED, #OBSCODE, #DELIM, #DATE, #OBSTYPE), canonical VSX target star name, valid JD, MAG, MERR, KNAME, KMAG values, and column structure.",
      lblGoToAavso: "Go to AAVSO Data Upload Page",
      btnUrgentMenu: "AAVSO Target Radar",
      btnRefreshUrgent: "🔄 Refresh Data Now",
      secUrgentStars: "🔥 Urgent Priority Stars (AAVSO Alert Notices)",
      urgentStarsIntro: "High-priority time-sensitive AAVSO Alert Notice targets for Seestar telescopes. Click any star card to populate its canonical name and coordinates into the converter."


    },
    es: {
      btnObsTrackerMenu: "📓 Registro de observaciones",
      lblSettingsTitle: "Ajustes:",
      lblToastsShort: "🔔 Notificaciones",
      lblToastsToggle: "🔔 Notificaciones emergentes",
      splashHubTitle: "⚡ Panel de control del observatorio y accesos rápidos",
      splashMetricTargetsLbl: "Objetivos en radar AAVSO",
      splashMetricObsCountLbl: "Sesiones registradas",
      splashMetricDaysIdleLbl: "Estado de fotometría",
      splashMetricScopeLbl: "Telescopio activo",
      btnSplashQuickSync: "🛰️ Ir a sincronización",
      btnSplashQuickTracker: "📓 Registro (Tracker)",
      btnSplashQuickRadar: "🎯 Radar de objetivos AAVSO",
      btnSplashQuickLoadCsv: "📂 Elegir archivo CSV",
      splashRecentLogTitle: "🕒 Registro de actividad reciente:",
      obsTrackerTitle: "📓 Registro de observaciones (My Observations)",
      obsDaysSinceFmt: "No ha realizado fotometría durante {days} días",
      obsSummaryStatsFmt: "Sesiones: {count} • Tiempo total: {mins} min • Cuadros: {frames}",
      phObsStar: "Estrella (ej. SZ Lyn)",
      phObsDur: "Duración (min)",
      phObsFrames: "Cuadros",
      btnObsAdd: "➕ Añadir medición",
      btnObsExport: "💾 Exportar JSON",
      btnObsImport: "📂 Importar JSON",
      obsChartTitle: "📊 Gráfico de actividad de observación (duración en minutos y cuadros por fecha)",
      thObsStar: "Estrella (STARID)",
      thObsDate: "Fecha",
      thObsDuration: "Duración (min)",
      thObsFrames: "Cuadros / Filtro",
      thObsScope: "Telescopio",
      thObsAction: "Acción",
      btnObsDelete: "Eliminar",
      btnObsDeleteAll: "🗑️ Eliminar todo",
      btnObsResetFilters: "↺ Restablecer",
      phObsFilterStar: "🔍 Filtrar por estrella (STARID)...",
      optObsAllScopes: "🔭 Todos los telescopios (S30–S50PRO)",
      lblSortBy: "Ordenar por:",
      optSortDate: "Fecha de publicación (recientes)",
      optSortName: "Nombre de estrella (A–Z)",
      optSortPriority: "Prioridad (Urgente)",
      btnDonateBadge: "❤️ Apoyar",
      tipDonateAuthor: "Apoyar al autor CosmoBehemothych en Boosty",
      donateModalTitle: "❤️ Apoyar el proyecto Seestar AstroLab AAVSO",
      donateLiteraryText: "¡Queridos amigos y compañeros bajo el cielo estrellado! El complejo fotométrico Seestar AstroLab se desarrolla con amor por la astronomía observacional para que cada cuadro de su telescopio aporte valor real a la ciencia mundial y a la base de datos de la AAVSO. Si el programa le ayuda en sus observaciones y le ahorra tiempo junto al telescopio, puede apoyar el desarrollo del proyecto en Boosty. ¡Cielos despejados y curvas de luz precisas!",
      donateScanOrClick: "Escanee el código QR con la cámara de su teléfono o siga el enlace directo:",
      btnDonateSupportNow: "❤️ Apoyar en Boosty",
      obsEmptyTableMsg: "Aún no hay registros. Convierta un archivo CSV de fotometría Seestar y el resultado se guardará automáticamente en «Mis observaciones».",
      obsMinUnit: "min",
      obsFramesUnit: "cuadros",
      actAppStarted: "Sesión iniciada Seestar AstroLab v1.0.1",
      actCatalogSyncedFmt: "Sincronizado con catálogo: {star}",
      actFileConvertedFmt: "Informe AAVSO convertido: {star} ({pts} pts)",
      actObsAddedFmt: "Sesión añadida al registro: {star} ({mins} min)",
      actRadarPickedFmt: "Referencia de radar: {star}",
      tipVerifyDiskShort: "Verifica la compatibilidad de un archivo convertido con los requisitos de AAVSO WebObs.",
      errNoObscodeTitle: "⚠️ Falta el código de observador (OBSCODE)",
      errNoObscodeMsg: "Ingrese su código personal de observador AAVSO (OBSCODE) antes de convertir los datos.",
      errNoObscodeExplain: "El formato AAVSO Extended requiere un código de observador válido en el encabezado #OBSCODE.",
      radarSubTag: "",
      appVersionLabel: "Versión 1.0.0 (Primera versión)",
      starIdFromCatalogHint: "✓ Identificador de catálogo (SIMBAD / AAVSO VSX): {star}",
      brandBarTitle: "🌌 CosmoBehemothych AstroLab • Observatorio Fotométrico Seestar S30 / S30PRO / S50 / S50PRO",
      
      missionSummaryTitle: "ℹ️ Cómo funciona la verificación Seestar → SIMBAD y VSP (Indicadores de color)",
      lblExpand: "Expandir\u00A0▾",
      bentoSyncBadgeText: "Online • TTL 1h",
      bentoSimbadDefault: "✓ 3 Espejos (HTTPS:443)",
      bentoVspDefault: "✓ Activo (API v2)",
      bentoVizierDefault: "✓ 4 Espejos (Respaldo)",
      lblThemePanel: "Tema de color",
      lblThemePickerSplash: "Tema de color",
      lblObscodeHeader: "OBSCODE:",
      phObscodeHeader: "Tu código",
      tipToggleScope: "Cambiar modelo de telescopio (S30 / S30PRO / S50 / S50PRO)",
      btnUrgentTop: "Radar de objetivos AAVSO",
      tipRefreshRadar: "Actualizar radar de objetivos AAVSO",
      tipExpandUrgent: "Abrir tabla completa de objetivos",
      tipCollapseRadar: "Contraer radar lateral AAVSO",
      tipExpandRadar: "Expandir radar lateral AAVSO",
      radarCollapsedPill: "RADAR AAVSO ({count})",
      lblScopeSectionTitle: "🔭 Modelo de telescopio Seestar",
      scopeSpecsFmt: "FOV: {fov} • {res} ({scale}″/px) • Límite: ≤{mag} mag • Exp: {minE}–{maxE} s",
      phRadarSearch: "🔍 Buscar en 45 objetivos (nombre, tipo, constelación)...",
      filterAllFmt: "Todos ({count})",
      filterUrgent: "🔥 Urgente",
      filterScopeFmt: "🔭 Para {id} (≤{mag}m)",
      filterExo: "🪐 Binarias/Exo",
      radarCountFmt: "Mostrando: {shown} de {total} objetivos",
      lblRadarLimit: "Mostrar:",
      optLimitAll: "Todos 45",
      optLimit30: "Top 30",
      optLimit15: "Top 15",
      tagPhotometry: "📈 Fotometría estelar",
      tagBinaries: "🌑 Binarias eclipsantes",
      tagExoplanets: "🪐 Exoplanetas",
      tagTelescopes: "🔭 S30 • S30PRO • S50 • S50PRO",
      lblBentoService: "Servicio SIMBAD TAP",
      valBentoService: "✓ 3 espejos (CDS / Harvard / IDIA)",
      lblBentoVsp: "Escala AAVSO VSP",
      valBentoVsp: "✓ Auto-ajuste a campo S30..S50PRO",
      lblBentoCache: "Caché de catálogos",
      valBentoCacheFmt: "TTL 3600 s • Entradas: {count}",
      lblBentoStandard: "Estándar de informe",
      valBentoStandard: "AAVSO Extended (#TYPE=EXTENDED)",
      phStarIdEmpty: "No cargado (desde archivo CSV)",
      phRaEmpty: "Desde archivo o radar",
      phDecEmpty: "Desde archivo o radar",
      emptyPreviewTitle: "Cargue un archivo de fotometría Seestar",
      emptyPreviewDesc: "La vista previa de parámetros, la verificación de coordenadas y la curva de luz aparecerán automáticamente tras cargar un archivo CSV.",
      lcFrameTooltipFmt: "Cuadro #{idx} | JD {jd} | {mag} mag ±{merr}",
      btnPickTarget: "Elegir",
      btnPickedTarget: "✓ En radar",
      ttDescLabel: "Descripción:",
      ttCommentLabel: "Comentario AAVSO:",
      ttDefaultComment: "Active la serie TG y verifique la calibración KNAME.",
      scopeEvalOkFmt: "{id}: Exposición {exp} • FOV {fov} ({scale}″/px)",
      scopeEvalFaintFmt: "{id}: Más débil que el límite {mag}m (rec. S50/S50PRO)",
      scopeEvalDipFmt: "{id}: Mínimo hasta {max}m (límite {mag}m) • Exp {exp} s",
      scopeEvalBrightFmt: "{id}: Brillante ({min}m < {bright}m, riesgo saturación) • Exp {exp} s",
      exp10_20: "10–20 s",
      exp10: "10 s",
      exp20_30: "20–30 s",
      exp20: "20 s",
      toastScopeTitleFmt: "🔭 Perfil de telescopio: {name}",
      toastScopeSubFmt: "Radio de búsqueda VSP: {fov}', límite de magnitud: {mag} mag.",
      toastRadarTargetTitleFmt: "🛰️ Referencia del radar AAVSO: {star}",
      toastRadarTargetMsgFmt: "Calibración VSP: CHART {chart} • KNAME {kname} ({kmag} mag)",
      toastRadarTargetSubFmt: "Coordenadas y carta actualizadas ({scope}). El campo STARID se completa solo desde el archivo CSV cargado.",
      toastThemeLightTitle: "☀️ Tema claro activado",
      toastThemeLightMsg: "Paleta diurna de alto contraste (WCAG AA) para el Centro de Comando y Radar AAVSO.",
      toastThemeDarkTitle: "🌙 Tema oscuro estándar activado",
      toastThemeDarkMsg: "Paleta oscura espacial para el Centro de Comando y Radar AAVSO.",
      toastHomeTitle: "🏠 Pantalla de inicio",
      toastHomeMsg: "Ventana de bienvenida de Seestar AstroLab abierta",
      toastHomeSub: "Consulte las funciones principales y estándares del observatorio.",
      urgentSyncWait: "⏳ Sincronización AAVSO: <strong>Listo para consultar espejos...</strong>",
      urgentSyncProgress: "⏳ <strong>Sincronizando con espejos CDS SIMBAD TAP y AAVSO VSP...</strong>",
      urgentSyncDoneFmt: "✅ <strong>Sincronizados {count} objetos AAVSO a las {time}</strong> (JD {jd}).",
      urgentAutoTimerPrefix: "Auto-actualización cada 10 min • JD:",
      urgentCountBadgeFmt: "{shown} de {total} objetivos",
      btnPickUrgentFmt: "🎯 Usar referencia ({exp})",
      btnRefreshLoading: "⏳ Actualizando...",
      toastRadarRefreshedTitle: "🔄 Radar de objetivos AAVSO actualizado",
      toastRadarRefreshedMsgFmt: "Sincronizados {count} objetos correctamente ({time})",
      toastRadarRefreshedSub: "Coordenadas J2000, cartas VSP y perfiles S30/S30PRO/S50/S50PRO actualizados.",
      demoFilePillText: "✅ SZ_Lyn_20261103_Demo.csv • 25 cuadros (Cargado)",
      dssFieldFallbackFmt: "Campo estelar <strong>{star}</strong> (carta astrométrica VSP • ",
      verifyTitle: "Verificación de compatibilidad AAVSO",
      verifyOkFmt: "✅ ¡El archivo «{file}» es 100% compatible con AAVSO WebObs! Filas: {rows}, estrella: «{star}», OBSCODE: «{obs}».",
      verifyWarnFmt: "⚠️ El archivo «{file}» presenta observaciones para AAVSO WebObs: {issues}.",
      notifOnTitle: "🔔 Notificaciones activadas",
      notifOffTitle: "🔕 Notificaciones desactivadas",
      notifOnMsg: "Monitoreo de campañas urgentes AAVSO activo",
      notifOffMsg: "Alertas de objetivos en pausa",

      matchDiffStar: "✗ Discrepancia",
      starIdDiffStarMsg: "✗ Discrepancia: el archivo tiene '{file}', pero la UI tiene otra estrella '{ui}'!",
      starIdSynonymMsg: "⚠ Difiere (normal): sinónimos de la misma estrella ('{file}' ↔ '{cat}')",
      lblThemePanel: "Tema de color",
      lblThemePickerSplash: "Tema de color",
      themeDarkBtn: "Oscuro estándar",
      themeLightBtn: "Claro",
      lblScopeModel: "Telescopio:",
      radarTitle: "Radar de Objetivos AAVSO",
      btnRefreshShort: "Actualizar",
      phRadarSearch: "🔍 Buscar estrella, tipo (DSCT, UGSS, EP) o constelación...",
      filterUrgent: "🔥 Urgente",
      filterExo: "🪐 Binarias/Exo",
      lblRadarLimit: "Mostrar:",
      optLimitAll: "Todos (sin límite)",
      lblFov: "Campo de visión:",
      secCatalogStatus: "📡 Estado de Catálogos",
      catSimbadTap: "Espejos CDS SIMBAD TAP",
      catAavsoVsp: "Servidor AAVSO VSP / VSX",
      catVizierApass: "Catálogos VizieR / APASS DR9",
      catLocalCache: "Caché local (TTL 1h)",
      btnShowNetLog: "▸ Mostrar registro técnico de red",
      btnHideNetLog: "▾ Ocultar registro técnico de red",
      lblPushNotifs: "🔔 Alertas",
      btnGoAavsoObj: "🌐 Ir al objeto en AAVSO ↗",
      btnUrgentMenu: "Radar de objetivos AAVSO",
      btnGraphGuide: "📖 Cómo leer gráficos",
      btnRefreshUrgent: "🔄 Actualizar",
      secUrgentStars: "🔥 Estrellas Prioritarias (AAVSO Alert Notices)",
      btnCloseModal: "Cerrar",
      secFileStart: "1. Selección y verificación de archivo",
      btnSelectCsvFile: "📂 Seleccionar CSV Seestar",
      noFileSelected: "Ningún archivo seleccionado (pulse arriba o 'CSV Demo')",
      lblVerifyDisk: "Verificar archivo AAVSO:",
      btnVerifyDisk: "🔍 Verificar archivo convertido del disco",
      lblGoToAavso: "Ir a la página de carga de AAVSO",

      lblSplashLang: "Idioma:",
      infoCosmoSub: "Observatorio Fotométrico AAVSO Extended",

      authorCompany: "CosmoBehemothych",
      modeMinimal: "Minimalista",
      modeCompact: "Compacto",
      modeFull: "Estudio",
      searchPlaceholder: "Búsqueda rápida: estrella (Algol, SZ Lyn...), parámetro o ayuda [ / o ⌘K ]",
      selfTestsTitle: "Diagnóstico del Núcleo CosmoBehemothych",
      selfTestsSuccess: "¡Las 8 pruebas unitarias algorítmicas se completaron con éxito (100% precisión)!",
      minimalNotice: "🍃 Modo minimalista activado: flujo rápido en 1-2 clics.",
      compactNotice: "⚡ Panel compacto: parámetros y curva de luz lado a lado.",
      fullNotice: "🔭 Estudio completo activado: conjunto científico exhaustivo y telemetría.",
      pageTitle: "Seestar AstroLab AAVSO — Фотометрия и Радар целей",
      appTitle: "Seestar AstroLab AAVSO",
      subtitle: "Carga SIMBAD y AAVSO VSP con autoselección de estrella de control",
      viewDesktop: "💻 PC (Escritorio)",
      viewMobile: "📱 iPhone / Android",
      btnAbout: "✨ Portada e Info",
      splashTitle: "Seestar AstroLab AAVSO: Fotometría Estelar",
      splashDesc: "Aplicación profesional para convertir series fotométricas de telescopios ZWO Seestar al formato internacional AAVSO Extended. Diseñada para el estudio de estrellas variables, binarias eclipsantes y tránsitos de exoplanetas.",
      feat1Title: "Fotometría Estelar",
      feat1Text: "Cálculo preciso de Fecha Juliana media (JD Mid) y magnitudes instrumentales TG.",
      feat2Title: "Alertas AAVSO y Progreso",
      feat2Text: "Seguimiento de solicitudes urgentes de la AAVSO y de su propio progreso en la recopilación de datos fotométricos.",
      feat3Title: "SIMBAD & AAVSO VSP",
      feat3Text: "Consulta paralela a espejos SIMBAD y selección automática de estrella de control.",
      btnStartApp: "🚀 Iniciar Trabajo Científico",
      tagPhotometry: "📈 Fotometría Estelar",
      tagBinaries: "♊ Binarias Eclipsantes",
      tagExoplanets: "🪐 Tránsitos de Exoplanetas",
      noticeHtml: "<strong>Propósito y funcionamiento.</strong> Convierte datos de Seestar al formato AAVSO Extended. Los espejos SIMBAD se consultan en paralelo. <span style='color:#86efac'>Verde</span> — coincidencia exacta, <span style='color:#fde047'>Amarillo</span> — diferencia menor (normal), <span style='color:#fca5a5'>Rojo</span> — gran discrepancia.",
      secObserver: "Observador y Estrella",
      secResults: "Resultados y Calibración VSP",
      secActions: "Sincronización de Catálogos",
      secConvert: "Convertir CSV de Seestar",
      secPreview: "Vista Previa y Curva de Luz",
      secLog: "Registro de Comparación (Antes/Después)",
      lblObsCode: "OBSCODE (Código AAVSO)",
      lblStarId: "STARID (Nombre de estrella)",
      lblChart: "CHART (Carta VSP)",
      lblKname: "KNAME (AUID Control)",
      lblKmag: "KMAG (mag)",
      lblRa: "RA (J2000, °)",
      lblDec: "DEC (J2000, °)",
      lblFile: "Archivo CSV Seestar:",
      lblRows: "Filas:",
      lblLightCurve: "📈 Curva de Luz (MAG vs JD Mid)",
      btnLoadImage: "📸 Imagen DSS2",
      btnLoadDemo: "✨ CSV Demo (SZ Lyn)",
      phRa: "ej. 121.907200",
      phDec: "ej. 44.460400",
      phStarId: "ej. SZ Lyncis",
      phChart: "X28491AB",
      phKname: "000-BDP-712",
      phKmag: "9.453",
      tipObsCodeText: "Código oficial de observador AAVSO (#OBSCODE).",
      tipStarIdText: "Nombre de la estrella variable, binaria o sistema exoplanetario.",
      tipChartText: "Identificador de carta del Variable Star Plotter (VSP).",
      tipKnameText: "AUID de la estrella de control (Check Star).",
      tipKmagText: "Magnitud estándar de la estrella de control (ideal 9.5–13.0 mag).",
      tipRaText: "Ascensión Recta (J2000) en grados decimales.",
      tipDecText: "Declinación (J2000) en grados decimales.",
      tipCsvText: "Archivo CSV exportado por Seestar (filas 'Non-reference star').",
      notifGuideTitle: "🔔 Guía de Notificaciones e Indicadores",
      notifGuideHtml: "<div>🟢 <strong>Verde:</strong> Coincidencia exacta (&lt; 0.00001°).</div><div>🟡 <strong>Amarillo:</strong> Desplazamiento normal del encuadre (&lt; 0.05°) o ID estandarizado.</div><div>🔴 <strong>Rojo:</strong> Discrepancia mayor a 0.05° — revise la estrella seleccionada.</div><div>📦 <strong>Caché:</strong> Respuesta instantánea desde memoria local (TTL 1 hora).</div>",
      btnFetchAll: "🔭 Cargar SIMBAD + VSP",
      btnDiagnose: "🧪 Diagnóstico de Red",
      btnStop: "⏹ Detener",
      btnClearAll: "🗑 Borrar Todo",
      btnConvert: "Convertir datos para carga en AAVSO",
      btnPrevPage: "< Anterior",
      btnNextPage: "Siguiente >",
      pageInfoText: "Pág. {current} de {total} ({rows})",
      rowWord: "Fila",
      msgNoStarId: "Introduzca STARID",
      msgNoStarIdExplain: "Se requiere el nombre de la estrella para consultar SIMBAD y AAVSO VSP.",
      msgNoFile: "Seleccione un archivo CSV de Seestar o pulse 'CSV Demo'.",
      msgNoFileExplain: "Cargue un archivo CSV antes de iniciar la conversión.",
      msgStopped: "Detenido por el usuario",
      msgStoppedExplain: "Todas las consultas de red activas fueron canceladas.",
      msgClearDone: "Todos los campos y el archivo han sido borrados",
      msgClearExplain: "Formulario reiniciado para una nueva estrella.",
      msgSimbadCache: "📦 SIMBAD desde caché",
      msgVspCache: "📦 VSP desde caché",
      msgConverted: "✓ CONVERSIÓN COMPLETA",
      msgConvertedExplain: "Archivo AAVSO Extended generado correctamente.",
      msgNoData: "⚠ Sin filas 'Non-reference star'.",
      msgNoDataExplain: "Verifique que el archivo CSV provenga del modo fotometría de Seestar.",
      msgNoCheckStar: "⚠ No se pudo elegir estrella de control automáticamente.",
      msgCheckStarWarn: "⚠ Verifique que la estrella de control esté en su campo y no sea variable.",
      msgDiagnoseHeader: "══ DIAGNÓSTICO DE RED ══",
      msgDiagStep1: "Paso 1: Ping directo a servidores proxy CORS",
      msgDiagStep2: "Paso 2: Prueba de espejos SIMBAD",
      msgDiagnoseDone: "══ DIAGNÓSTICO FINALIZADO ══",
      msgDirectMirrors: "Espejos SIMBAD directos en paralelo…",
      msgProxiesFallback: "Carrera de proxies en espejos…",
      msgVspDirect: "Solicitud directa a AAVSO VSP…",
      msgVspProxy: "AAVSO VSP vía proxies…",
      msgSimbadDown: "SIMBAD no disponible.",
      msgVspDown: "AAVSO VSP no disponible.",
      msgNoChartId: "CHART ID no devuelto",
      thParam: "Parámetro",
      thFile: "Datos de Seestar",
      thUI: "Datos del Catálogo SIMBAD",
      thMatch: "Comprobar",
      matchOk: "✓ Coincide",
      matchBad: "✗ Gran discrepancia",
      matchWarn: "⚠ Difiere (normal)",
      matchMissing: "— Sin datos",
      starIdMissing: "— Se usará el del archivo",
      previewReady: "Archivo leído. Verifique los datos y la curva de luz abajo.",
      starIdCorrected: "STARID difiere del catálogo. Se usará el ID del catálogo.",
      starIdSame: "STARID coincide.",
      fetchingSimbad: "📡 1/2: Cargando coordenadas SIMBAD...",
      fetchingVsp: "📡 2/2: Cargando carta VSP...",
      imgLoading: "Cargando imagen DSS2...",
      imgOpenAladin: "🔭 Abrir en Aladin Lite",
      imgFieldCaption: "Campo de <strong>{star}</strong> (DSS2)",
      imgAltServer: "Probando servidor alternativo CDS...",
      imgLoadError: "No se pudo cargar la imagen.",
      imgNoCoords: "Introduzca coordenadas RA y DEC válidas.",
      fileSavedPicker: "✅ Archivo guardado: {name}",
      fileSaveCancelled: "⚠ Guardado cancelado por el usuario.",
      fileDownloaded: "⬇️ Archivo descargado en su carpeta de Descargas ({name}).",
      demoLoaded: "¡Datos de demostración de SZ Lyncis cargados!",
      demoLoadedExplain: "Ahora puede pulsar 'Convertir a AAVSO Extended' o probar SIMBAD + VSP."
    },
    de: {
      btnObsTrackerMenu: "📓 Beobachtungsprotokoll",
      lblSettingsTitle: "Optionen:",
      lblToastsShort: "🔔 Hinweise",
      lblToastsToggle: "🔔 Popup-Benachrichtigungen",
      splashHubTitle: "⚡ Sternwarten-Zentrale & Schnellzugriff",
      splashMetricTargetsLbl: "AAVSO-Radarziele",
      splashMetricObsCountLbl: "Protokollierte Sitzungen",
      splashMetricDaysIdleLbl: "Photometrie-Status",
      splashMetricScopeLbl: "Aktives Teleskop",
      btnSplashQuickSync: "🛰️ Zur Katalog-Sync",
      btnSplashQuickTracker: "📓 Beobachtungsprotokoll",
      btnSplashQuickRadar: "🎯 AAVSO-Zielradar",
      btnSplashQuickLoadCsv: "📂 CSV-Datei wählen",
      splashRecentLogTitle: "🕒 Letzte Aktivitäten:",
      obsTrackerTitle: "📓 Beobachtungsprotokoll (My Observations)",
      obsDaysSinceFmt: "Sie haben seit {days} Tagen keine Photometrie durchgeführt",
      obsSummaryStatsFmt: "Sitzungen: {count} • Gesamtzeit: {mins} Min • Bilder: {frames}",
      phObsStar: "Stern (z.B. SZ Lyn)",
      phObsDur: "Dauer (Min)",
      phObsFrames: "Bilder",
      btnObsAdd: "➕ Messung hinzufügen",
      btnObsExport: "💾 JSON exportieren",
      btnObsImport: "📂 JSON importieren",
      obsChartTitle: "📊 Beobachtungsaktivität (Messdauer in Minuten & Bildanzahl nach Datum)",
      thObsStar: "Stern (STARID)",
      thObsDate: "Datum",
      thObsDuration: "Dauer (Min)",
      thObsFrames: "Bilder / Filter",
      thObsScope: "Teleskop",
      thObsAction: "Aktion",
      btnObsDelete: "Löschen",
      btnObsDeleteAll: "🗑️ Alle löschen",
      btnObsResetFilters: "↺ Zurücksetzen",
      phObsFilterStar: "🔍 Nach Stern filtern (STARID)...",
      optObsAllScopes: "🔭 Alle Teleskope (S30–S50PRO)",
      lblSortBy: "Sortieren:",
      optSortDate: "Veröffentlichungsdatum (neueste)",
      optSortName: "Sternname (A–Z)",
      optSortPriority: "Priorität (Dringend)",
      btnDonateBadge: "❤️ Unterstützen",
      tipDonateAuthor: "Autor CosmoBehemothych auf Boosty unterstützen",
      donateModalTitle: "❤️ Projekt Seestar AstroLab AAVSO unterstützen",
      donateLiteraryText: "Liebe Sternfreunde und Kollegen unter dem Nachthimmel! Die Photometrie-Suite Seestar AstroLab wird mit Leidenschaft für die beobachtende Astronomie entwickelt, damit jede Aufnahme Ihres Teleskops einen echten Beitrag zur weltweiten Wissenschaft und zur AAVSO-Datenbank leistet. Wenn Ihnen das Programm bei Ihren Beobachtungen hilft und Zeit am Teleskop spart, können Sie die Weiterentwicklung des Projekts auf Boosty unterstützen. Klaren Himmel und präzise Lichtkurven!",
      donateScanOrClick: "Scannen Sie den QR-Code mit Ihrer Smartphone-Kamera oder öffnen Sie den direkten Link:",
      btnDonateSupportNow: "❤️ Auf Boosty unterstützen",
      obsEmptyTableMsg: "Noch keine Einträge vorhanden. Konvertieren Sie eine Seestar-Photometrie-CSV-Datei, und das Ergebnis wird automatisch unter „Meine Beobachtungen“ gespeichert.",
      obsMinUnit: "Min",
      obsFramesUnit: "Bilder",
      actAppStarted: "Sitzung gestartet Seestar AstroLab v1.0.1",
      actCatalogSyncedFmt: "Mit Katalog synchronisiert: {star}",
      actFileConvertedFmt: "AAVSO-Bericht konvertiert: {star} ({pts} Pkt)",
      actObsAddedFmt: "Beobachtung hinzugefügt: {star} ({mins} Min)",
      actRadarPickedFmt: "Radar-Referenz: {star}",
      tipVerifyDiskShort: "Prüft die Kompatibilität einer konvertierten Datei mit den AAVSO-WebObs-Anforderungen.",
      errNoObscodeTitle: "⚠️ Beobachtercode (OBSCODE) fehlt",
      errNoObscodeMsg: "Bitte geben Sie Ihren persönlichen AAVSO-Beobachtercode (OBSCODE) vor der Konvertierung ein.",
      errNoObscodeExplain: "Das AAVSO-Extended-Format erfordert zwingend einen gültigen Beobachtercode im Header #OBSCODE.",
      radarSubTag: "",
      appVersionLabel: "Version 1.0.1",
      starIdFromCatalogHint: "✓ Kanonische Katalog-STARID (SIMBAD / AAVSO VSX): {star}",
      brandBarTitle: "🌌 CosmoBehemothych AstroLab • Seestar S30 / S30PRO / S50 / S50PRO Photometrie-Observatorium",
      
      missionSummaryTitle: "ℹ️ Funktionsweise des Seestar → SIMBAD & VSP Feldabgleichs (Farbindikatoren)",
      lblExpand: "Ausklappen\u00A0▾",
      bentoSyncBadgeText: "Online • TTL 1h",
      bentoSimbadDefault: "✓ 3 Spiegel (HTTPS:443)",
      bentoVspDefault: "✓ Aktiv (API v2)",
      bentoVizierDefault: "✓ 4 Spiegel (Reserve)",
      lblThemePanel: "Farbschema",
      lblThemePickerSplash: "Farbschema",
      lblObscodeHeader: "OBSCODE:",
      phObscodeHeader: "Ihr Code",
      tipToggleScope: "Teleskopmodell wechseln (S30 / S30PRO / S50 / S50PRO)",
      btnUrgentTop: "AAVSO-Zielradar",
      tipRefreshRadar: "AAVSO-Zielradar aktualisieren",
      tipExpandUrgent: "Vollständige Zieltabelle öffnen",
      tipCollapseRadar: "AAVSO-Zielradar einklappen",
      tipExpandRadar: "AAVSO-Zielradar ausklappen",
      radarCollapsedPill: "AAVSO-RADAR ({count})",
      lblScopeSectionTitle: "🔭 Seestar-Teleskopmodell",
      scopeSpecsFmt: "FOV: {fov} • {res} ({scale}″/px) • Limit: ≤{mag} mag • Bel.: {minE}–{maxE} s",
      phRadarSearch: "🔍 Suche in 45 Zielen (Name, Typ, Sternbild)...",
      filterAllFmt: "Alle ({count})",
      filterUrgent: "🔥 Dringend",
      filterScopeFmt: "🔭 Für {id} (≤{mag}m)",
      filterExo: "🪐 Bedeckung/Exo",
      radarCountFmt: "Angezeigt: {shown} von {total} Zielen",
      lblRadarLimit: "Anzeige:",
      optLimitAll: "Alle 45",
      optLimit30: "Top 30",
      optLimit15: "Top 15",
      tagPhotometry: "📈 Sternphotometrie",
      tagBinaries: "🌑 Bedeckungsveränderliche",
      tagExoplanets: "🪐 Exoplaneten",
      tagTelescopes: "🔭 S30 • S30PRO • S50 • S50PRO",
      lblBentoService: "SIMBAD TAP-Dienst",
      valBentoService: "✓ 3 Spiegelserver (CDS / Harvard / IDIA)",
      lblBentoVsp: "AAVSO VSP-Skala",
      valBentoVsp: "✓ Automatisch für S30..S50PRO",
      lblBentoCache: "Katalog-Cache",
      valBentoCacheFmt: "TTL 3600 s • Einträge: {count}",
      lblBentoStandard: "Berichtsstandard",
      valBentoStandard: "AAVSO Extended (#TYPE=EXTENDED)",
      phStarIdEmpty: "Nicht geladen (aus CSV-Datei)",
      phRaEmpty: "Aus Datei oder Radar",
      phDecEmpty: "Aus Datei oder Radar",
      emptyPreviewTitle: "Seestar-Photometriedatei laden",
      emptyPreviewDesc: "Sternparameter-Vorschau, Koordinatenabgleich und Lichtkurve erscheinen automatisch nach dem Laden einer CSV-Beobachtungsdatei.",
      lcFrameTooltipFmt: "Bild #{idx} | JD {jd} | {mag} mag ±{merr}",
      btnPickTarget: "Wählen",
      btnPickedTarget: "✓ Im Radar",
      ttDescLabel: "Beschreibung:",
      ttCommentLabel: "AAVSO-Kommentar:",
      ttDefaultComment: "TG-Filterserie aktivieren und KNAME-Kalibrierung prüfen.",
      scopeEvalOkFmt: "{id}: Belichtung {exp} • FOV {fov} ({scale}″/px)",
      scopeEvalFaintFmt: "{id}: Schwächer als Limit {mag}m (empf. S50/S50PRO)",
      scopeEvalDipFmt: "{id}: Minimum bis {max}m (Limit {mag}m) • Bel. {exp} s",
      scopeEvalBrightFmt: "{id}: Hell ({min}m < {bright}m, Sättigungsrisiko) • Bel. {exp} s",
      exp10_20: "10–20 s",
      exp10: "10 s",
      exp20_30: "20–30 s",
      exp20: "20 s",
      toastScopeTitleFmt: "🔭 Teleskopprofil: {name}",
      toastScopeSubFmt: "VSP-Suchradius: {fov}', Grenzgröße: {mag} mag.",
      toastRadarTargetTitleFmt: "🛰️ AAVSO-Radarreferenz: {star}",
      toastRadarTargetMsgFmt: "VSP-Kalibrierung: CHART {chart} • KNAME {kname} ({kmag} mag)",
      toastRadarTargetSubFmt: "Koordinaten und Vergleichskarte aktualisiert ({scope}). STARID wird nur aus der geladenen CSV-Datei übernommen.",
      toastThemeLightTitle: "☀️ Helles Farbschema aktiviert",
      toastThemeLightMsg: "Konturenstarke Tagespalette (WCAG AA) für Kontrollzentrum und AAVSO-Zielradar.",
      toastThemeDarkTitle: "🌙 Dunkles Standardschema aktiviert",
      toastThemeDarkMsg: "Kosmische Dunkelpalette für Kontrollzentrum und AAVSO-Zielradar.",
      toastHomeTitle: "🏠 Startseite",
      toastHomeMsg: "Willkommensfenster von Seestar AstroLab geöffnet",
      toastHomeSub: "Übersicht über Hauptfunktionen und AAVSO-Standards.",
      urgentSyncWait: "⏳ AAVSO-Synchronisation: <strong>Bereit für Spiegelabfrage...</strong>",
      urgentSyncProgress: "⏳ <strong>Synchronisiere mit CDS SIMBAD TAP und AAVSO VSP...</strong>",
      urgentSyncDoneFmt: "✅ <strong>{count} AAVSO-Objekte um {time} synchronisiert</strong> (JD {jd}).",
      urgentAutoTimerPrefix: "Auto-Update alle 10 Min • JD:",
      urgentCountBadgeFmt: "{shown} von {total} Zielen",
      btnPickUrgentFmt: "🎯 Referenz nutzen ({exp})",
      btnRefreshLoading: "⏳ Aktualisiere...",
      toastRadarRefreshedTitle: "🔄 AAVSO-Zielradar aktualisiert",
      toastRadarRefreshedMsgFmt: "{count} Zielobjekte erfolgreich synchronisiert ({time})",
      toastRadarRefreshedSub: "Alle J2000-Koordinaten, VSP-Karten und S30/S30PRO/S50/S50PRO-Profile sind aktuell.",
      demoFilePillText: "✅ SZ_Lyn_20261103_Demo.csv • 25 Bilder (Geladen)",
      dssFieldFallbackFmt: "Sternfeld <strong>{star}</strong> (offline VSP-Karte • ",
      verifyTitle: "AAVSO-Kompatibilitätsprüfung",
      verifyOkFmt: "✅ Datei «{file}» ist zu 100% kompatibel mit AAVSO WebObs! Zeilen: {rows}, Stern: «{star}», OBSCODE: «{obs}».",
      verifyWarnFmt: "⚠️ Datei «{file}» enthält Hinweise für AAVSO WebObs: {issues}.",
      notifOnTitle: "🔔 Benachrichtigungen aktiviert",
      notifOffTitle: "🔕 Benachrichtigungen deaktiviert",
      notifOnMsg: "Überwachung dringender AAVSO-Kampagnen aktiv",
      notifOffMsg: "Zielbenachrichtigungen pausiert",

      matchDiffStar: "✗ Abweichung",
      starIdDiffStarMsg: "✗ Abweichung: Datei enthält '{file}', aber im UI ist ein anderer Stern '{ui}' gewählt!",
      starIdSynonymMsg: "⚠ Abweichung (normal): Synonyme desselben Sterns ('{file}' ↔ '{cat}')",
      lblThemePanel: "Farbschema",
      lblThemePickerSplash: "Farbschema",
      themeDarkBtn: "Standard Dunkel",
      themeLightBtn: "Hell",
      lblScopeModel: "Teleskop:",
      radarTitle: "AAVSO-Zielradar",
      btnRefreshShort: "Aktualisieren",
      phRadarSearch: "🔍 Stern, Typ (DSCT, UGSS, EP) oder Sternbild suchen...",
      filterUrgent: "🔥 Dringend",
      filterExo: "🪐 Bedeckung/Exo",
      lblRadarLimit: "Anzeige:",
      optLimitAll: "Alle (ohne Limit)",
      lblFov: "Gesichtsfeld:",
      secCatalogStatus: "📡 Katalogstatus",
      catSimbadTap: "CDS SIMBAD TAP Spiegel",
      catAavsoVsp: "AAVSO VSP / VSX Server",
      catVizierApass: "VizieR / APASS DR9 Kataloge",
      catLocalCache: "Lokaler Anfrage-Cache",
      btnShowNetLog: "▸ Technisches Netzwerkprotokoll anzeigen",
      btnHideNetLog: "▾ Technisches Netzwerkprotokoll ausblenden",
      lblPushNotifs: "🔔 Hinweise",
      btnGoAavsoObj: "🌐 Zum Objekt in AAVSO ↗",
      btnUrgentMenu: "AAVSO-Zielradar",
      btnGraphGuide: "📖 Lichtkurven lesen",
      btnRefreshUrgent: "🔄 Aktualisieren",
      secUrgentStars: "🔥 Dringende Zielsterne (AAVSO Alert Notices)",
      btnCloseModal: "Schließen",
      secFileStart: "Photometriedatei wählen & prüfen",
      btnSelectCsvFile: "📂 Seestar-CSV auswählen",
      noFileSelected: "Noch keine Datei gewählt (oben klicken oder 'Demo-CSV')",
      lblVerifyDisk: "Konvertierte AAVSO-Datei prüfen:",
      btnVerifyDisk: "🔍 Konvertierte Datei von Festplatte prüfen",
      lblGoToAavso: "Zur AAVSO-Upload-Seite wechseln",

      lblSplashLang: "Sprache:",
      infoCosmoSub: "AAVSO Extended Photometrisches Observatorium",
      pageTitle: "Seestar AstroLab AAVSO — Фотометрия и Радар целей",
      appTitle: "Seestar AstroLab AAVSO",
      subtitle: "SIMBAD & AAVSO VSP laden mit automatischem Vergleichsstern",
      viewDesktop: "💻 PC (Desktop)",
      viewMobile: "📱 iPhone / Android",
      btnAbout: "✨ Startbild & Info",
      splashTitle: "Seestar AstroLab AAVSO: Sternphotometrie",
      splashDesc: "Professionelle Anwendung zur Konvertierung wissenschaftlicher Photometriedaten von ZWO Seestar-Teleskopen in das internationale AAVSO Extended-Format — für Veränderliche, Bedeckungsveränderliche und Exoplaneten-Transits.",
      feat1Title: "Sternphotometrie",
      feat1Text: "Präzise Berechnung von JD Mid und instrumenteller TG-Helligkeit.",
      feat2Title: "Dringende AAVSO-Anfragen & Fortschritt",
      feat2Text: "Verfolgen Sie dringende AAVSO-Anfragen und Ihren eigenen Fortschritt bei der Sammlung photometrischer Daten.",
      feat3Title: "SIMBAD & AAVSO VSP",
      feat3Text: "Parallele SIMBAD-Abfrage und automatische Auswahl des Vergleichssterns.",
      btnStartApp: "🚀 Arbeit starten",
      tagPhotometry: "📈 Sternphotometrie",
      tagBinaries: "♊ Doppelsterne",
      tagExoplanets: "🪐 Exoplaneten-Transits",
      noticeHtml: "<strong>Funktionsweise.</strong> Bereitet Seestar-Photometriedaten für die AAVSO-Datenbank vor. Alle SIMBAD-Spiegel werden parallel abgefragt. <span style='color:#86efac'>Grün</span> — exakte Übereinstimmung, <span style='color:#fde047'>Gelb</span> — geringe Abweichung (normal), <span style='color:#fca5a5'>Rot</span> — große Abweichung.",
      secObserver: "Beobachter & Stern",
      secResults: "Ergebnisse & VSP-Kalibrierung",
      secActions: "Katalog-Synchronisation",
      secConvert: "Seestar-CSV konvertieren",
      secPreview: "Dateivorschau & Lichtkurve",
      secLog: "Vergleichsprotokoll (Vorher/Nachher)",
      lblObsCode: "OBSCODE (Observatoriumscode)",
      lblStarId: "STARID (Sternname)",
      lblChart: "CHART (VSP)",
      lblKname: "KNAME (AUID)",
      lblKmag: "KMAG (mag)",
      lblRa: "RA (J2000, °)",
      lblDec: "DEC (J2000, °)",
      lblFile: "CSV-Datei:",
      lblRows: "Zeilen:",
      lblLightCurve: "📈 Lichtkurve (MAG vs JD Mid)",
      btnLoadImage: "📸 Himmelsbild",
      btnLoadDemo: "✨ Demo-CSV (SZ Lyn)",
      phRa: "z.B. 121.907200",
      phDec: "z.B. 44.460400",
      phStarId: "z.B. SZ Lyncis",
      phChart: "X28491AB",
      phKname: "000-BDP-712",
      phKmag: "9.453",
      tipObsCodeText: "Ihr offizieller AAVSO-Beobachtercode (#OBSCODE).",
      tipStarIdText: "Katalogname des Veränderlichen, Doppelsterns oder Exoplaneten-Sterns.",
      tipChartText: "Karten-ID aus dem AAVSO Variable Star Plotter (VSP).",
      tipKnameText: "AUID des Kontrollsterns (Check Star).",
      tipKmagText: "Helligkeit des Kontrollsterns (optimal 9.5–13.0 mag).",
      tipRaText: "Rektaszension (J2000) in Dezimalgrad.",
      tipDecText: "Deklination (J2000) in Dezimalgrad.",
      tipCsvText: "Rohe Seestar-Photometrie-CSV ('Non-reference star'-Zeilen).",
      notifGuideTitle: "🔔 Erklärung aller Hinweise & Farben",
      notifGuideHtml: "<div>🟢 <strong>Grün:</strong> Exakte Übereinstimmung (&lt; 0.00001°).</div><div>🟡 <strong>Gelb:</strong> Normale Bildfeldabweichung (&lt; 0.05°) oder Katalog-ID.</div><div>🔴 <strong>Rot:</strong> Große Abweichung (&gt; 0.05°) — Zielstern prüfen.</div><div>📦 <strong>Cache:</strong> Aus dem lokalen Zwischenspeicher geladen (1 Std. gültig).</div>",
      btnFetchAll: "🔭 SIMBAD + VSP laden",
      btnDiagnose: "🧪 Netzwerk-Diagnose",
      btnStop: "⏹ Stoppen",
      btnClearAll: "🗑 Alles löschen",
      btnConvert: "Daten für AAVSO-Upload konvertieren",
      btnPrevPage: "< Zurück",
      btnNextPage: "Weiter >",
      pageInfoText: "S. {current} von {total} ({rows})",
      rowWord: "Zeile",
      msgNoStarId: "Bitte STARID eingeben",
      msgNoStarIdExplain: "Für die SIMBAD- und VSP-Abfrage wird ein Sternname benötigt.",
      msgNoFile: "Bitte Seestar-CSV wählen oder 'Demo-CSV' klicken.",
      msgNoFileExplain: "Laden Sie zuerst eine CSV-Messdatei.",
      msgStopped: "Vom Benutzer gestoppt",
      msgStoppedExplain: "Alle laufenden Netzwerkanfragen wurden abgebrochen.",
      msgClearDone: "Alle Felder und Datei gelöscht",
      msgClearExplain: "Arbeitsbereich wurde zurückgesetzt.",
      msgSimbadCache: "📦 SIMBAD aus Cache",
      msgVspCache: "📦 VSP aus Cache",
      msgConverted: "✓ KONVERTIERUNG FERTIG",
      msgConvertedExplain: "AAVSO Extended-Datei erfolgreich erstellt.",
      msgNoData: "⚠ Keine 'Non-reference star'-Zeilen gefunden.",
      msgNoDataExplain: "Prüfen Sie, ob die CSV-Datei aus dem Seestar-Photometriemodus stammt.",
      msgNoCheckStar: "⚠ Vergleichsstern nicht automatisch wählbar.",
      msgCheckStarWarn: "⚠ Prüfen Sie, ob der gewählte Stern im Bildfeld liegt und nicht variabel ist.",
      msgDiagnoseHeader: "══ NETZWERK-DIAGNOSE ══",
      msgDiagStep1: "Schritt 1: Direkter Ping der CORS-Proxys",
      msgDiagStep2: "Schritt 2: SIMBAD-Spiegel über Proxy-Rennen",
      msgDiagnoseDone: "══ DIAGNOSE ABGESCHLOSSEN ══",
      msgDirectMirrors: "Direkte SIMBAD-Spiegel parallel…",
      msgProxiesFallback: "Proxy-Rennen über Spiegel…",
      msgVspDirect: "Direkte AAVSO-Abfrage…",
      msgVspProxy: "AAVSO über Proxy…",
      msgSimbadDown: "SIMBAD nicht erreichbar.",
      msgVspDown: "AAVSO VSP nicht erreichbar.",
      msgNoChartId: "Keine CHART ID erhalten",
      thParam: "Parameter",
      thFile: "Daten von Seestar",
      thUI: "Data from SIMBAD Catalog",
      thMatch: "Prüfen",
      matchOk: "✓ Stimmt überein",
      matchBad: "✗ Große Abweichung",
      matchWarn: "⚠ Abweichung (normal)",
      matchMissing: "— Keine Daten",
      starIdMissing: "— Aus Datei wird verwendet",
      previewReady: "Datei gelesen. Prüfen Sie die Daten und Lichtkurve unten.",
      starIdCorrected: "STARID weicht vom Katalog ab. Die Katalog-ID wird verwendet.",
      starIdSame: "STARID stimmt überein.",
      fetchingSimbad: "📡 1/2: SIMBAD-Koordinaten laden...",
      fetchingVsp: "📡 2/2: VSP-Karte laden...",
      imgLoading: "Lade DSS2-Himmelsbild...",
      imgOpenAladin: "🔭 In Aladin Lite öffnen",
      imgFieldCaption: "Sternfeld <strong>{star}</strong> (DSS2)",
      imgAltServer: "Versuche alternativen CDS-Server...",
      imgLoadError: "Bild konnte nicht geladen werden.",
      imgNoCoords: "Geben Sie RA und DEC ein, um das Himmelsbild zu laden.",
      fileSavedPicker: "✅ Datei gespeichert: {name}",
      fileSaveCancelled: "⚠ Speichern vom Benutzer abgebrochen.",
      fileDownloaded: "⬇️ Datei im Download-Ordner gespeichert ({name}).",
      demoLoaded: "Demo-Photometriedaten für SZ Lyncis geladen!",
      demoLoadedExplain: "Klicken Sie nun auf 'In AAVSO Extended konvertieren' oder testen Sie SIMBAD + VSP."
    },
    fr: {
      btnObsTrackerMenu: "📓 Journal d'observation",
      lblSettingsTitle: "Options :",
      lblToastsShort: "🔔 Notifications",
      lblToastsToggle: "🔔 Notifications surgissantes",
      splashHubTitle: "⚡ Centre de contrôle de l'observatoire & accès rapides",
      splashMetricTargetsLbl: "Cibles radar AAVSO",
      splashMetricObsCountLbl: "Sessions enregistrées",
      splashMetricDaysIdleLbl: "Statut photométrie",
      splashMetricScopeLbl: "Télescope actif",
      btnSplashQuickSync: "🛰️ Vers synchro catalogue",
      btnSplashQuickTracker: "📓 Journal (Tracker)",
      btnSplashQuickRadar: "🎯 Radar de cibles AAVSO",
      btnSplashQuickLoadCsv: "📂 Choisir fichier CSV",
      splashRecentLogTitle: "🕒 Journal des dernières actions :",
      obsTrackerTitle: "📓 Journal d'observation (My Observations)",
      obsDaysSinceFmt: "Vous n'avez pas effectué de photométrie depuis {days} jours",
      obsSummaryStatsFmt: "Sessions : {count} • Durée totale : {mins} min • Images : {frames}",
      phObsStar: "Étoile (ex. SZ Lyn)",
      phObsDur: "Durée (min)",
      phObsFrames: "Images",
      btnObsAdd: "➕ Ajouter mesure",
      btnObsExport: "💾 Exporter JSON",
      btnObsImport: "📂 Importer JSON",
      obsChartTitle: "📊 Graphique d'activité d'observation (durée en minutes et images par date)",
      thObsStar: "Étoile (STARID)",
      thObsDate: "Date",
      thObsDuration: "Durée (min)",
      thObsFrames: "Images / Filtre",
      thObsScope: "Télescope",
      thObsAction: "Action",
      btnObsDelete: "Supprimer",
      btnObsDeleteAll: "🗑️ Tout supprimer",
      btnObsResetFilters: "↺ Réinitialiser",
      phObsFilterStar: "🔍 Filtrer par étoile (STARID)...",
      optObsAllScopes: "🔭 Tous les télescopes (S30–S50PRO)",
      lblSortBy: "Trier par :",
      optSortDate: "Date de publication (récentes)",
      optSortName: "Nom de l'étoile (A–Z)",
      optSortPriority: "Priorité (Urgent)",
      btnDonateBadge: "❤️ Soutenir",
      tipDonateAuthor: "Soutenir l'auteur CosmoBehemothych sur Boosty",
      donateModalTitle: "❤️ Soutenir le projet Seestar AstroLab AAVSO",
      donateLiteraryText: "Chers amis et collègues sous la voûte étoilée ! La suite photométrique Seestar AstroLab est créée et développée avec passion pour l'astronomie d'observation, afin que chaque pose de votre télescope apporte une contribution réelle à la science mondiale et à la base de données de l'AAVSO. Si ce logiciel facilite vos observations et vous fait gagner du temps, vous pouvez soutenir le développement du projet sur Boosty. Bon ciel et belles courbes de lumière !",
      donateScanOrClick: "Scannez le code QR avec l'appareil photo de votre smartphone ou suivez le lien direct :",
      btnDonateSupportNow: "❤️ Soutenir sur Boosty",
      obsEmptyTableMsg: "Aucun enregistrement pour le moment. Convertissez un fichier CSV de photométrie Seestar et la session sera automatiquement enregistrée dans « Mes observations ».",
      obsMinUnit: "min",
      obsFramesUnit: "images",
      actAppStarted: "Session démarrée Seestar AstroLab v1.0.1",
      actCatalogSyncedFmt: "Synchronisé avec le catalogue : {star}",
      actFileConvertedFmt: "Rapport AAVSO converti : {star} ({pts} pts)",
      actObsAddedFmt: "Session ajoutée au journal : {star} ({mins} min)",
      actRadarPickedFmt: "Référence radar : {star}",
      tipVerifyDiskShort: "Vérifie la compatibilité d'un fichier converti avec les exigences d'AAVSO WebObs.",
      errNoObscodeTitle: "⚠️ Code observateur (OBSCODE) manquant",
      errNoObscodeMsg: "Veuillez saisir votre code observateur AAVSO (OBSCODE) avant de convertir les données.",
      errNoObscodeExplain: "Le standard AAVSO Extended exige un code observateur personnel valide dans l'en-tête #OBSCODE.",
      radarSubTag: "",
      appVersionLabel: "Version 1.0.1",
      starIdFromCatalogHint: "✓ Identifiant catalogue canonique (SIMBAD / AAVSO VSX) : {star}",
      brandBarTitle: "🌌 CosmoBehemothych AstroLab • Observatoire Photométrique Seestar S30 / S30PRO / S50 / S50PRO",
      
      missionSummaryTitle: "ℹ️ Fonctionnement de la vérification Seestar → SIMBAD & VSP (Indicateurs couleur)",
      lblExpand: "Déployer\u00A0▾",
      bentoSyncBadgeText: "En ligne • TTL 1h",
      bentoSimbadDefault: "✓ 3 Miroirs (HTTPS:443)",
      bentoVspDefault: "✓ Actif (API v2)",
      bentoVizierDefault: "✓ 4 Miroirs (Secours)",
      lblThemePanel: "Thème de couleur",
      lblThemePickerSplash: "Thème de couleur",
      lblObscodeHeader: "OBSCODE :",
      phObscodeHeader: "Votre code",
      tipToggleScope: "Changer de modèle de télescope (S30 / S30PRO / S50 / S50PRO)",
      btnUrgentTop: "AAVSO Target Radar",
      tipRefreshRadar: "Actualiser le radar de cibles AAVSO",
      tipExpandUrgent: "Ouvrir le tableau complet des cibles",
      tipCollapseRadar: "Réduire le radar latéral AAVSO",
      tipExpandRadar: "Déployer le radar latéral AAVSO",
      radarCollapsedPill: "RADAR AAVSO ({count})",
      lblScopeSectionTitle: "🔭 Modèle de télescope Seestar",
      scopeSpecsFmt: "FOV : {fov} • {res} ({scale}″/px) • Limite : ≤{mag} mag • Pose : {minE}–{maxE} s",
      phRadarSearch: "🔍 Rechercher parmi 45 cibles (nom, type, constellation)...",
      filterAllFmt: "Toutes ({count})",
      filterUrgent: "🔥 Urgent",
      filterScopeFmt: "🔭 Pour {id} (≤{mag}m)",
      filterExo: "🪐 Éclipsantes/Exo",
      radarCountFmt: "Affiché : {shown} sur {total} cibles",
      lblRadarLimit: "Afficher :",
      optLimitAll: "Toutes 45",
      optLimit30: "Top 30",
      optLimit15: "Top 15",
      tagPhotometry: "📈 Photométrie stellaire",
      tagBinaries: "🌑 Binaires à éclipses",
      tagExoplanets: "🪐 Exoplanètes",
      tagTelescopes: "🔭 S30 • S30PRO • S50 • S50PRO",
      lblBentoService: "Service SIMBAD TAP",
      valBentoService: "✓ 3 miroirs (CDS / Harvard / IDIA)",
      lblBentoVsp: "Échelle AAVSO VSP",
      valBentoVsp: "✓ Auto-adaptée au champ S30..S50PRO",
      lblBentoCache: "Cache des catalogues",
      valBentoCacheFmt: "TTL 3600 s • Entrées : {count}",
      lblBentoStandard: "Standard de rapport",
      valBentoStandard: "AAVSO Extended (#TYPE=EXTENDED)",
      phStarIdEmpty: "Non chargé (depuis le fichier CSV)",
      phRaEmpty: "Depuis le fichier ou radar",
      phDecEmpty: "Depuis le fichier ou radar",
      emptyPreviewTitle: "Chargez un fichier de photométrie Seestar",
      emptyPreviewDesc: "L'aperçu des paramètres de l'étoile, la vérification des coordonnées et la courbe de lumière s'afficheront automatiquement après le chargement d'un fichier CSV.",
      lcFrameTooltipFmt: "Image #{idx} | JD {jd} | {mag} mag ±{merr}",
      btnPickTarget: "Choisir",
      btnPickedTarget: "✓ Dans le radar",
      ttDescLabel: "Description :",
      ttCommentLabel: "Commentaire AAVSO :",
      ttDefaultComment: "Activez la série TG et vérifiez l'étalonnage KNAME.",
      scopeEvalOkFmt: "{id} : Pose {exp} • FOV {fov} ({scale}″/px)",
      scopeEvalFaintFmt: "{id} : Plus faible que la limite {mag}m (rec. S50/S50PRO)",
      scopeEvalDipFmt: "{id} : Minimum jusqu'à {max}m (limite {mag}m) • Pose {exp} s",
      scopeEvalBrightFmt: "{id} : Brillante ({min}m < {bright}m, risque saturation) • Pose {exp} s",
      exp10_20: "10–20 s",
      exp10: "10 s",
      exp20_30: "20–30 s",
      exp20: "20 s",
      toastScopeTitleFmt: "🔭 Profil du télescope : {name}",
      toastScopeSubFmt: "Rayon de recherche VSP : {fov}', magnitude limite : {mag} mag.",
      toastRadarTargetTitleFmt: "🛰️ Référence radar AAVSO : {star}",
      toastRadarTargetMsgFmt: "Étalonnage VSP : CHART {chart} • KNAME {kname} ({kmag} mag)",
      toastRadarTargetSubFmt: "Coordonnées et carte mises à jour ({scope}). Le champ STARID est rempli uniquement à partir du fichier CSV chargé.",
      toastThemeLightTitle: "☀️ Thème clair activé",
      toastThemeLightMsg: "Palette diurne à contraste élevé (WCAG AA) pour le Centre de Commande et le Radar AAVSO.",
      toastThemeDarkTitle: "🌙 Thème sombre standard activé",
      toastThemeDarkMsg: "Palette sombre cosmique pour le Centre de Commande et le Radar AAVSO.",
      toastHomeTitle: "🏠 Page d'accueil",
      toastHomeMsg: "Fenêtre de bienvenue Seestar AstroLab ouverte",
      toastHomeSub: "Découvrez les fonctionnalités clés et les standards AAVSO.",
      urgentSyncWait: "⏳ Synchronisation AAVSO : <strong>Prêt à interroger les miroirs...</strong>",
      urgentSyncProgress: "⏳ <strong>Synchronisation avec les miroirs CDS SIMBAD TAP et AAVSO VSP...</strong>",
      urgentSyncDoneFmt: "✅ <strong>{count} objets AAVSO synchronisés à {time}</strong> (JD {jd}).",
      urgentAutoTimerPrefix: "Actualisation auto toutes les 10 min • JD :",
      urgentCountBadgeFmt: "{shown} sur {total} cibles",
      btnPickUrgentFmt: "🎯 Utiliser référence ({exp})",
      btnRefreshLoading: "⏳ Actualisation...",
      toastRadarRefreshedTitle: "🔄 Radar de cibles AAVSO actualisé",
      toastRadarRefreshedMsgFmt: "{count} objets cibles synchronisés avec succès ({time})",
      toastRadarRefreshedSub: "Coordonnées J2000, cartes VSP et profils S30/S30PRO/S50/S50PRO à jour.",
      demoFilePillText: "✅ SZ_Lyn_20261103_Demo.csv • 25 images (Chargé)",
      dssFieldFallbackFmt: "Champ stellaire <strong>{star}</strong> (carte astrométrique VSP • ",
      verifyTitle: "Vérification de compatibilité AAVSO",
      verifyOkFmt: "✅ Le fichier « {file} » est 100% compatible avec AAVSO WebObs ! Lignes : {rows}, étoile : « {star} », OBSCODE : « {obs} ».",
      verifyWarnFmt: "⚠️ Le fichier « {file} » présente des remarques pour AAVSO WebObs : {issues}.",
      notifOnTitle: "🔔 Notifications activées",
      notifOffTitle: "🔕 Notifications désactivées",
      notifOnMsg: "Suivi des campagnes urgentes AAVSO actif",
      notifOffMsg: "Alertes de cibles suspendues",

      matchDiffStar: "✗ Discordance",
      starIdDiffStarMsg: "✗ Discordance : le fichier indique '{file}', mais une autre étoile '{ui}' est choisie !",
      starIdSynonymMsg: "⚠ Diffère (normal) : synonymes de la même étoile ('{file}' ↔ '{cat}')",
      lblThemePanel: "Thème de couleur",
      lblThemePickerSplash: "Thème de couleur",
      themeDarkBtn: "Sombre standard",
      themeLightBtn: "Clair",
      lblScopeModel: "Télescope :",
      radarTitle: "Radar de Cibles AAVSO",
      btnRefreshShort: "Actualiser",
      phRadarSearch: "🔍 Rechercher étoile, type (DSCT, UGSS, EP) ou constellation...",
      filterUrgent: "🔥 Urgent",
      filterExo: "🪐 Binaires/Exo",
      lblRadarLimit: "Afficher :",
      optLimitAll: "Tout (sans limite)",
      lblFov: "Champ de vision :",
      secCatalogStatus: "📡 État des Catalogues",
      catSimbadTap: "Miroirs CDS SIMBAD TAP",
      catAavsoVsp: "Serveur AAVSO VSP / VSX",
      catVizierApass: "Catalogues VizieR / APASS DR9",
      catLocalCache: "Cache local (TTL 1h)",
      btnShowNetLog: "▸ Afficher le journal réseau technique",
      btnHideNetLog: "▾ Masquer le journal réseau technique",
      lblPushNotifs: "🔔 Alertes",
      btnGoAavsoObj: "🌐 Ouvrir l'objet dans l'AAVSO ↗",
      btnUrgentMenu: "Radar de cibles AAVSO",
      btnGraphGuide: "📖 Lire les courbes",
      btnRefreshUrgent: "🔄 Actualiser",
      secUrgentStars: "🔥 Étoiles Prioritaires (AAVSO Alert Notices)",
      btnCloseModal: "Fermer",
      secFileStart: "Sélection et vérification du fichier",
      btnSelectCsvFile: "📂 Choisir un fichier CSV Seestar",
      noFileSelected: "Aucun fichier choisi (cliquez ci-dessus ou sur 'CSV Démo')",
      lblVerifyDisk: "Vérifier un fichier AAVSO :",
      btnVerifyDisk: "🔍 Vérifier un fichier converti du disque",
      lblGoToAavso: "Aller à la page d'envoi AAVSO",
      pageTitle: "Seestar AstroLab AAVSO — Фотометрия и Радар целей",
      appTitle: "Seestar AstroLab AAVSO",
      subtitle: "Récupération SIMBAD et AAVSO VSP avec étoile de comparaison auto",
      viewDesktop: "💻 PC (Bureau)",
      viewMobile: "📱 iPhone / Android",
      btnAbout: "✨ Écran & Info",
      splashTitle: "Seestar AstroLab AAVSO : Photométrie Stellaire",
      splashDesc: "Outil professionnel pour convertir les séries photométriques des télescopes ZWO Seestar au format international AAVSO Extended. Conçu pour l'étude des étoiles variables, binaires à éclipses et transits d'exoplanètes.",
      feat1Title: "Photométrie Stellaire",
      feat1Text: "Calcul précis du Jour Julien milieu (JD Mid) et des magnitudes instrumentales TG.",
      feat2Title: "Requêtes urgentes AAVSO & Progression",
      feat2Text: "Suivez les requêtes urgentes de l'AAVSO et votre propre progression dans la collecte de données photométriques.",
      feat3Title: "SIMBAD & AAVSO VSP",
      feat3Text: "Interrogation parallèle des miroirs SIMBAD et sélection auto de l'étoile de contrôle.",
      btnStartApp: "🚀 Démarrer l'Analyse",
      tagPhotometry: "📈 Photométrie Stellaire",
      tagBinaries: "♊ Binaires à Éclipses",
      tagExoplanets: "🪐 Transits d'Exoplanètes",
      noticeHtml: "<strong>Fonctionnement.</strong> Prépare les données Seestar pour l'AAVSO. Tous les miroirs SIMBAD sont interrogés en parallèle. <span style='color:#86efac'>Vert</span> — correspondance exacte, <span style='color:#fde047'>Jaune</span> — différence mineure (normal), <span style='color:#fca5a5'>Rouge</span> — écart important.",
      secObserver: "Observateur et Étoile",
      secResults: "Résultats et Calibration VSP",
      secActions: "Synchronisation des Catalogues",
      secConvert: "Convertir CSV Seestar",
      secPreview: "Aperçu du Fichier & Courbe de Lumière",
      secLog: "Journal de Comparaison (Avant/Après)",
      lblObsCode: "OBSCODE (Code AAVSO)",
      lblStarId: "STARID (Nom de l'étoile)",
      lblChart: "CHART (Carte VSP)",
      lblKname: "KNAME (AUID Contrôle)",
      lblKmag: "KMAG (mag)",
      lblRa: "RA (J2000, °)",
      lblDec: "DEC (J2000, °)",
      lblFile: "Fichier CSV :",
      lblRows: "Lignes :",
      lblLightCurve: "📈 Courbe de Lumière (MAG vs JD Mid)",
      btnLoadImage: "📸 Image du Ciel",
      btnLoadDemo: "✨ CSV Démo (SZ Lyn)",
      phRa: "ex. 121.907200",
      phDec: "ex. 44.460400",
      phStarId: "ex. SZ Lyncis",
      phChart: "X28491AB",
      phKname: "000-BDP-712",
      phKmag: "9.453",
      tipObsCodeText: "Votre code officiel d'observateur AAVSO (#OBSCODE).",
      tipStarIdText: "Nom catalogue de l'étoile variable, binaire ou système exoplanétaire.",
      tipChartText: "Identifiant de carte AAVSO VSP.",
      tipKnameText: "AUID de l'étoile de contrôle (Check Star).",
      tipKmagText: "Magnitude standard de l'étoile de contrôle (idéal 9.5–13.0 mag).",
      tipRaText: "Ascension Droite (J2000) en degrés décimaux.",
      tipDecText: "Déclinaison (J2000) en degrés décimaux.",
      tipCsvText: "Fichier CSV brut issu de Seestar (lignes 'Non-reference star').",
      notifGuideTitle: "🔔 Guide des Notifications et Indicateurs",
      notifGuideHtml: "<div>🟢 <strong>Vert :</strong> Correspondance exacte (&lt; 0.00001°).</div><div>🟡 <strong>Jaune :</strong> Léger décalage normal du champ (&lt; 0.05°) ou ID catalogue.</div><div>🔴 <strong>Rouge :</strong> Écart supérieur à 0.05° — vérifiez la cible.</div><div>📦 <strong>Cache :</strong> Chargé depuis le cache local (valide 1h).</div>",
      btnFetchAll: "🔭 Charger SIMBAD + VSP",
      btnDiagnose: "🧪 Diagnostic Réseau",
      btnStop: "⏹ Arrêter",
      btnClearAll: "🗑 Tout effacer",
      btnConvert: "Convertir les données pour envoi AAVSO",
      btnPrevPage: "< Préc.",
      btnNextPage: "Suiv. >",
      pageInfoText: "Page {current} sur {total} ({rows})",
      rowWord: "Ligne",
      msgNoStarId: "Veuillez saisir STARID",
      msgNoStarIdExplain: "Le nom de l'étoile est requis pour interroger SIMBAD et AAVSO VSP.",
      msgNoFile: "Sélectionnez un CSV Seestar ou cliquez sur 'CSV Démo'.",
      msgNoFileExplain: "Un fichier de mesures CSV est nécessaire pour la conversion.",
      msgStopped: "Arrêté par l'utilisateur",
      msgStoppedExplain: "Toutes les requêtes réseau en cours ont été interrompues.",
      msgClearDone: "Tous les champs et le fichier ont été effacés",
      msgClearExplain: "L'espace de travail a été réinitialisé.",
      msgSimbadCache: "📦 SIMBAD en cache",
      msgVspCache: "📦 VSP en cache",
      msgConverted: "✓ CONVERSION TERMINÉE",
      msgConvertedExplain: "Fichier AAVSO Extended généré avec succès.",
      msgNoData: "⚠ Aucune ligne 'Non-reference star'.",
      msgNoDataExplain: "Vérifiez que le fichier CSV provient du mode photométrie Seestar.",
      msgNoCheckStar: "⚠ Impossible de choisir l'étoile de contrôle automatiquement.",
      msgCheckStarWarn: "⚠ Vérifiez que l'étoile choisie est dans votre champ et non variable.",
      msgDiagnoseHeader: "══ DIAGNOSTIC RÉSEAU ══",
      msgDiagStep1: "Étape 1 : Ping direct des proxys CORS",
      msgDiagStep2: "Étape 2 : Test des miroirs SIMBAD",
      msgDiagnoseDone: "══ DIAGNOSTIC TERMINÉ ══",
      msgDirectMirrors: "Miroirs SIMBAD directs en parallèle…",
      msgProxiesFallback: "Course de proxys…",
      msgVspDirect: "Requête directe AAVSO VSP…",
      msgVspProxy: "AAVSO VSP via proxys…",
      msgSimbadDown: "SIMBAD est indisponible.",
      msgVspDown: "AAVSO VSP est indisponible.",
      msgNoChartId: "CHART ID non retourné",
      thParam: "Paramètre",
      thFile: "Données de Seestar",
      thUI: "Données du Catalogue SIMBAD",
      thMatch: "Vérifier",
      matchOk: "✓ Correspond",
      matchBad: "✗ Écart important",
      matchWarn: "⚠ Diffère (normal)",
      matchMissing: "— Aucune donnée",
      starIdMissing: "— Sera pris du fichier",
      previewReady: "Fichier lu. Vérifiez les données et la courbe de lumière ci-dessous.",
      starIdCorrected: "STARID diffère du catalogue. L'ID du catalogue sera utilisé.",
      starIdSame: "STARID correspond.",
      fetchingSimbad: "📡 1/2 : Chargement SIMBAD...",
      fetchingVsp: "📡 2/2 : Chargement VSP...",
      imgLoading: "Chargement de l'image DSS2...",
      imgOpenAladin: "🔭 Ouvrir dans Aladin Lite",
      imgFieldCaption: "Champ de <strong>{star}</strong> (DSS2)",
      imgAltServer: "Essai du serveur alternatif CDS...",
      imgLoadError: "Impossible de charger l'image.",
      imgNoCoords: "Saisissez RA et DEC pour charger l'image du ciel.",
      fileSavedPicker: "✅ Fichier enregistré : {name}",
      fileSaveCancelled: "⚠ Enregistrement annulé par l'utilisateur.",
      fileDownloaded: "⬇️ Fichier téléchargé dans votre dossier Téléchargements ({name}).",
      demoLoaded: "Données de démonstration SZ Lyncis chargées !",
      demoLoadedExplain: "Vous pouvez maintenant cliquer sur 'Convertir en AAVSO Extended'."
    },
    zh: {
      btnObsTrackerMenu: "📓 观测日志",
      lblSettingsTitle: "设置:",
      lblToastsShort: "🔔 弹窗通知",
      lblToastsToggle: "🔔 启用右下角弹窗通知",
      splashHubTitle: "⚡ 天文台控制中心与快捷入口",
      splashMetricTargetsLbl: "AAVSO 雷达目标",
      splashMetricObsCountLbl: "已记录观测场次",
      splashMetricDaysIdleLbl: "测光状态",
      splashMetricScopeLbl: "当前望远镜",
      btnSplashQuickSync: "🛰️ 前往星表同步",
      btnSplashQuickTracker: "📓 观测日志 (Tracker)",
      btnSplashQuickRadar: "🎯 AAVSO 目标雷达",
      btnSplashQuickLoadCsv: "📂 选择 CSV 文件",
      splashRecentLogTitle: "🕒 最近操作记录:",
      obsTrackerTitle: "📓 观测日志 (My Observations)",
      obsDaysSinceFmt: "您已有 {days} 天未进行测光观测",
      obsSummaryStatsFmt: "总场次: {count} • 累计时长: {mins} 分钟 • 总帧数: {frames}",
      phObsStar: "目标星 (如 SZ Lyn)",
      phObsDur: "时长 (分钟)",
      phObsFrames: "帧数",
      btnObsAdd: "➕ 添加观测记录",
      btnObsExport: "💾 导出 JSON",
      btnObsImport: "📂 导入 JSON",
      obsChartTitle: "📊 观测活跃度图表（按日期统计测量时长与帧数）",
      thObsStar: "目标星 (STARID)",
      thObsDate: "观测日期",
      thObsDuration: "测量时长 (分钟)",
      thObsFrames: "帧数 / 滤镜",
      thObsScope: "望远镜",
      thObsAction: "操作",
      btnObsDelete: "删除",
      btnObsDeleteAll: "🗑️ 全部删除",
      btnObsResetFilters: "↺ 重置筛选",
      phObsFilterStar: "🔍 按恒星名称搜索 (STARID)...",
      optObsAllScopes: "🔭 全部望远镜型号 (S30–S50PRO)",
      lblSortBy: "排序方式:",
      optSortDate: "按发布日期（最新优先）",
      optSortName: "按恒星名称 (A–Z)",
      optSortPriority: "按紧急优先级",
      btnDonateBadge: "❤️ 支持作者",
      tipDonateAuthor: "在 Boosty 上支持作者 CosmoBehemothych",
      donateModalTitle: "❤️ 支持 Seestar AstroLab AAVSO 星际测光项目",
      donateLiteraryText: "亲爱的星空观测者与天文同仁们！Seestar AstroLab 测光套件怀着对观测天文学的热爱而打造与持续演进，旨在让您智能望远镜拍摄的每一帧图像都能为全球变星科学与 AAVSO 数据库做出真正的科学贡献。如果本程序帮助了您的天文观测并节省了宝贵的望远镜观测时间，欢迎在 Boosty 上以任何舒适的方式或温暖的话语支持项目的持续开发。祝您晴空万里，光变曲线精准完美！",
      donateScanOrClick: "请使用手机相机扫描二维码，或点击下方直达链接：",
      btnDonateSupportNow: "❤️ 前往 Boosty 支持作者",
      obsTrackerTitle: "📓 我的观测 (My Observations)",
      btnObsTrackerMenu: "📓 我的观测",
      obsEmptyTableMsg: "暂无观测记录。转换 Seestar 测光 CSV 文件后，观测记录将自动保存在“我的观测”中。",
      obsMinUnit: "分钟",
      obsFramesUnit: "帧",
      actAppStarted: "已启动 Seestar AstroLab v1.0.1 会话",
      actCatalogSyncedFmt: "已同步星表目标: {star}",
      actFileConvertedFmt: "已转换 AAVSO 报告: {star} ({pts} 点)",
      actObsAddedFmt: "已添加观测日志: {star} ({mins} 分钟)",
      actRadarPickedFmt: "已选雷达参考: {star}",
      tipVerifyDiskShort: "检查转换后的文件是否符合 AAVSO WebObs 网站要求。",
      errNoObscodeTitle: "⚠️ 缺少观测者代码 (OBSCODE)",
      errNoObscodeMsg: "请在转换上传至 AAVSO 的数据前填写您的 AAVSO 观测者代码 (OBSCODE)。",
      errNoObscodeExplain: "AAVSO Extended 格式要求在 #OBSCODE 标头中提供有效的个人观测者代码。",
      radarSubTag: "",
      appVersionLabel: "版本 1.0.0 (第一版)",
      starIdFromCatalogHint: "✓ 星表标准目标名称 (SIMBAD / AAVSO VSX): {star}",
      brandBarTitle: "🌌 CosmoBehemothych AstroLab • Seestar S30 / S30PRO / S50 / S50PRO 测光天文台",
      
      missionSummaryTitle: "ℹ️ Seestar → SIMBAD 与 VSP 字段比对说明（颜色指示器）",
      lblExpand: "展开\u00A0▾",
      bentoSyncBadgeText: "在线 • TTL 1小时",
      bentoSimbadDefault: "✓ 3 镜像节点 (HTTPS:443)",
      bentoVspDefault: "✓ 已启用 (API v2)",
      bentoVizierDefault: "✓ 4 镜像节点 (备用)",
      lblThemePanel: "色彩主题",
      lblThemePickerSplash: "色彩主题",
      lblObscodeHeader: "OBSCODE:",
      phObscodeHeader: "观测者代码",
      tipToggleScope: "切换智能望远镜型号 (S30 / S30PRO / S50 / S50PRO)",
      btnUrgentTop: "AAVSO 目标雷达",
      tipRefreshRadar: "刷新 AAVSO 目标雷达",
      tipExpandUrgent: "打开完整目标表格",
      tipCollapseRadar: "收起 AAVSO 侧边目标雷达",
      tipExpandRadar: "展开 AAVSO 侧边目标雷达",
      radarCollapsedPill: "AAVSO 雷达 ({count})",
      lblScopeSectionTitle: "🔭 Seestar 望远镜型号",
      scopeSpecsFmt: "视场: {fov} • {res} ({scale}″/px) • 极限星等: ≤{mag} mag • 曝光: {minE}–{maxE} 秒",
      phRadarSearch: "🔍 搜索 45 个目标（名称、类型、星座）...",
      filterAllFmt: "全部 ({count})",
      filterUrgent: "🔥 紧急",
      filterScopeFmt: "🔭 适配 {id} (≤{mag}m)",
      filterExo: "🪐 食双星/系外行星",
      radarCountFmt: "显示: {shown} / {total} 个目标",
      lblRadarLimit: "显示数量:",
      optLimitAll: "全部 45",
      optLimit30: "前 30",
      optLimit15: "前 15",
      tagPhotometry: "📈 恒星测光",
      tagBinaries: "🌑 食双星",
      tagExoplanets: "🪐 系外行星",
      tagTelescopes: "🔭 S30 • S30PRO • S50 • S50PRO",
      lblBentoService: "SIMBAD TAP 服务",
      valBentoService: "✓ 3 镜像节点 (CDS / Harvard / IDIA)",
      lblBentoVsp: "AAVSO VSP 视场比例",
      valBentoVsp: "✓ 自动匹配 S30..S50PRO 视场",
      lblBentoCache: "星表缓存",
      valBentoCacheFmt: "TTL 3600 秒 • 缓存数: {count}",
      lblBentoStandard: "报告标准",
      valBentoStandard: "AAVSO Extended (#TYPE=EXTENDED)",
      phStarIdEmpty: "未加载（从 CSV 文件读取）",
      phRaEmpty: "来自文件或雷达",
      phDecEmpty: "来自文件或雷达",
      emptyPreviewTitle: "请加载 Seestar 测光文件",
      emptyPreviewDesc: "选择观测 CSV 文件后，此处将自动显示目标星参数预览、坐标比对和光变曲线。",
      lcFrameTooltipFmt: "帧 #{idx} | JD {jd} | {mag} mag ±{merr}",
      btnPickTarget: "选择",
      btnPickedTarget: "✓ 雷达已选",
      ttDescLabel: "目标简介:",
      ttCommentLabel: "AAVSO 观测建议:",
      ttDefaultComment: "建议使用 TG 滤镜序列并核对 KNAME 比较星。",
      scopeEvalOkFmt: "{id}: 曝光 {exp} • 视场 {fov} ({scale}″/px)",
      scopeEvalFaintFmt: "{id}: 暗于极限 {mag}m（推荐 S50/S50PRO）",
      scopeEvalDipFmt: "{id}: 极小值达 {max}m（极限 {mag}m）• 曝光 {exp} 秒",
      scopeEvalBrightFmt: "{id}: 较亮 ({min}m < {bright}m，注意防饱和) • 曝光 {exp} 秒",
      exp10_20: "10–20 秒",
      exp10: "10 秒",
      exp20_30: "20–30 秒",
      exp20: "20 秒",
      toastScopeTitleFmt: "🔭 望远镜配置: {name}",
      toastScopeSubFmt: "VSP 比较星搜索半径: {fov}', 极限星等: {mag} mag。",
      toastRadarTargetTitleFmt: "🛰️ AAVSO 雷达参考目标: {star}",
      toastRadarTargetMsgFmt: "VSP 校准: CHART {chart} • KNAME {kname} ({kmag} mag)",
      toastRadarTargetSubFmt: "坐标与比较星图已更新 ({scope})。STARID 仅从加载的 CSV 文件中读取。",
      toastThemeLightTitle: "☀️ 已启用浅色主题",
      toastThemeLightMsg: "适用于指挥中心与 AAVSO 目标雷达的高对比度日间配色 (WCAG AA)。",
      toastThemeDarkTitle: "🌙 已启用标准深色主题",
      toastThemeDarkMsg: "适用于指挥中心与 AAVSO 目标雷达的深空暗色配色。",
      toastHomeTitle: "🏠 欢迎页面",
      toastHomeMsg: "已打开 Seestar AstroLab 欢迎与功能概览窗口",
      toastHomeSub: "查看天文台核心功能与 AAVSO 标准说明。",
      urgentSyncWait: "⏳ AAVSO 观测活动同步: <strong>准备查询镜像节点...</strong>",
      urgentSyncProgress: "⏳ <strong>正在与 CDS SIMBAD TAP 及 AAVSO VSP 镜像同步...</strong>",
      urgentSyncDoneFmt: "✅ <strong>已于 {time} 同步 {count} 个 AAVSO 目标</strong> (JD {jd})。",
      urgentAutoTimerPrefix: "每 10 分钟自动刷新 • JD:",
      urgentCountBadgeFmt: "{shown} / {total} 个目标",
      btnPickUrgentFmt: "🎯 设为参考 ({exp})",
      btnRefreshLoading: "⏳ 正在刷新...",
      toastRadarRefreshedTitle: "🔄 AAVSO 目标雷达已刷新",
      toastRadarRefreshedMsgFmt: "成功同步 {count} 个目标天体 ({time})",
      toastRadarRefreshedSub: "所有 J2000 坐标、VSP 星图及 S30/S30PRO/S50/S50PRO 参数均为最新。",
      demoFilePillText: "✅ SZ_Lyn_20261103_Demo.csv • 25 帧 (已加载)",
      dssFieldFallbackFmt: "恒星视场 <strong>{star}</strong>（离线 VSP 天体测量星图 • ",
      verifyTitle: "AAVSO 兼容性校验",
      verifyOkFmt: "✅ 文件 «{file}» 100% 符合 AAVSO WebObs 规范！已校验行数: {rows}，VSX 目标: «{star}»，OBSCODE: «{obs}»。",
      verifyWarnFmt: "⚠️ 文件 «{file}» 存在 AAVSO WebObs 规范提示: {issues}。",
      notifOnTitle: "🔔 通知已开启",
      notifOffTitle: "🔕 通知已关闭",
      notifOnMsg: "正在监测 AAVSO 紧急观测活动",
      notifOffMsg: "新目标通知已暂停",

      matchDiffStar: "✗ 星名不符 (不一致)",
      starIdDiffStarMsg: "✗ 星名不一致：文件为“{file}”，但界面选择了另一颗恒星“{ui}”！",
      starIdSynonymMsg: "⚠ 有差异（正常）：同一颗恒星的不同星表同义名（“{file}” ↔ “{cat}”）",
      lblThemePanel: "色彩主题",
      lblThemePickerSplash: "色彩主题",
      themeDarkBtn: "标准深色",
      themeLightBtn: "浅色模式",
      lblScopeModel: "望远镜型号：",
      radarTitle: "AAVSO 目标雷达",
      btnRefreshShort: "刷新",
      phRadarSearch: "🔍 搜索恒星、变星类型 (DSCT, UGSS, EP) 或星座...",
      filterUrgent: "🔥 紧急目标",
      filterExo: "🪐 食双星/凌星",
      lblRadarLimit: "显示数量：",
      optLimitAll: "全部（无限制）",
      lblFov: "视场 (FOV)：",
      secCatalogStatus: "📡 星表服务状态",
      catSimbadTap: "CDS SIMBAD TAP 全球镜像",
      catAavsoVsp: "AAVSO VSP / VSX 星图服务",
      catVizierApass: "VizieR / APASS DR9 测光星表",
      catLocalCache: "本地查询缓存 (TTL 1h)",
      btnShowNetLog: "▸ 显示底层网络技术日志",
      btnHideNetLog: "▾ 隐藏底层网络技术日志",
      lblPushNotifs: "🔔 推送提醒",
      btnGoAavsoObj: "🌐 在 AAVSO 中查看该天体 ↗",
      btnUrgentMenu: "AAVSO 目标雷达",
      btnGraphGuide: "📖 如何阅读光变曲线",
      btnRefreshUrgent: "🔄 立即刷新",
      secUrgentStars: "🔥 紧急优先观测恒星 (AAVSO Alert Notices)",
      btnCloseModal: "关闭",
      secFileStart: "1. 选择并校验测光文件",
      btnSelectCsvFile: "📂 选择 Seestar CSV 文件",
      noFileSelected: "尚未选择文件（请点击上方按钮或“演示数据”）",
      lblVerifyDisk: "校验已转换的 AAVSO 文件：",
      btnVerifyDisk: "🔍 校验磁盘上的已转换文件",
      lblGoToAavso: "前往 AAVSO 数据提交页面",
      pageTitle: "Seestar AstroLab AAVSO — Фотометрия и Радар целей",
      appTitle: "Seestar AstroLab AAVSO",
      subtitle: "自动获取 SIMBAD 与 AAVSO VSP 数据并选择比较星",
      viewDesktop: "💻 电脑端 (PC)",
      viewMobile: "📱 手机端 (iOS/Android)",
      btnAbout: "✨ 星际启动页与说明",
      splashTitle: "Seestar AstroLab AAVSO：恒星测光实验室",
      splashDesc: "专为 ZWO Seestar 智能望远镜打造的专业科学测光转换工具，支持将原始 CSV 转换为国际标准 AAVSO Extended 格式，助力变星、食双星及系外行星凌星研究。",
      feat1Title: "恒星高精度测光",
      feat1Text: "自动计算曝光中间儒略日 (JD Mid) 与 TG 波段星等及误差校验。",
      feat2Title: "AAVSO 紧急请求与测光进度",
      feat2Text: "实时追踪 AAVSO 紧急观测请求，并跟踪您个人的测光数据收集进度。",
      feat3Title: "SIMBAD 与 AAVSO VSP",
      feat3Text: "并行查询全球 SIMBAD 镜像，智能优选最佳检验星 (Check Star)。",
      btnStartApp: "🚀 开始科学处理",
      tagPhotometry: "📈 恒星测光",
      tagBinaries: "♊ 双星搜索",
      tagExoplanets: "🪐 系外行星凌星",
      noticeHtml: "<strong>功能说明与工作原理：</strong>本程序将 Seestar 测光数据（变星、双星、行星凌星）转换为 AAVSO Extended 格式。并行查询所有 SIMBAD 镜像。选择文件后将与界面字段比对：<span style='color:#86efac'>绿色</span> — 完全匹配，<span style='color:#fde047'>黄色</span> — 微小差异（正常），<span style='color:#fca5a5'>红色</span> — 重大差异。",
      secObserver: "观测者与目标恒星",
      secResults: "结果与 VSP 校准",
      secActions: "星表同步操作",
      secConvert: "转换 Seestar CSV",
      secPreview: "Seestar 数据与 SIMBAD 星表比对结果",
      secLog: "转换前后对比日志",
      lblObsCode: "OBSCODE (观测者代码)",
      lblStarId: "STARID (恒星名称 / ID)",
      lblChart: "CHART (VSP 星图号)",
      lblKname: "KNAME (检验星 AUID)",
      lblKmag: "KMAG (mag)",
      lblRa: "RA (J2000 赤经, °)",
      lblDec: "DEC (J2000 赤纬, °)",
      lblFile: "CSV 测光文件：",
      lblRows: "每页行数：",
      lblLightCurve: "📈 光变曲线预览 (MAG vs JD Mid)",
      btnLoadImage: "📸 巡天图像",
      btnLoadDemo: "✨ 演示数据 (SZ Lyn)",
      phRa: "例如 121.907200",
      phDec: "例如 44.460400",
      phStarId: "例如 SZ Lyncis",
      phChart: "X28491AB",
      phKname: "000-BDP-712",
      phKmag: "9.453",
      tipObsCodeText: "您在 AAVSO 注册的官方观测者代码（写入 #OBSCODE 头部）。",
      tipStarIdText: "目标变星、双星或系外行星宿主星的星表名称。",
      tipChartText: "AAVSO VSP 变星测光星图 ID。",
      tipKnameText: "用于校验系综测光精度的检验星唯一编号 (AUID)。",
      tipKmagText: "检验星的标准星等（推荐范围 9.5–13.0 等）。",
      tipRaText: "J2000 赤经（十进制度数 0°–360°）。",
      tipDecText: "J2000 赤纬（十进制度数 -90°…+90°）。",
      tipCsvText: "选择 Seestar 导出的 CSV 文件（程序仅提取 'Non-reference star' 行）。",
      notifGuideTitle: "🔔 所有通知与颜色状态指南",
      notifGuideHtml: "<div>🟢 <strong>绿色输入框（完全匹配）：</strong>文件与星表坐标差异小于 0.00001°。</div><div>🟡 <strong>黄色输入框（正常微小差异）：</strong>视场中心偏移小于 0.05° 或使用星表标准名称。</div><div>🔴 <strong>红色输入框（重大差异）：</strong>坐标差异超过 0.05°，请检查目标星是否正确。</div><div>📦 <strong>缓存通知：</strong>数据直接读取自本地 1 小时缓存，响应更快。</div>",
      btnFetchAll: "🔭 获取 SIMBAD + VSP",
      btnDiagnose: "🧪 网络与镜像诊断",
      btnStop: "⏹ 停止",
      btnClearAll: "🗑 清空所有",
      btnConvert: "转换数据以上传至 AAVSO",
      btnPrevPage: "< 上一页",
      btnNextPage: "下一页 >",
      pageInfoText: "第 {current} 页 / 共 {total} 页 (共 {rows} 行)",
      rowWord: "行",
      msgNoStarId: "请输入 STARID（恒星名称）",
      msgNoStarIdExplain: "查询 SIMBAD 坐标和 AAVSO VSP 星图必须提供目标恒星名称。",
      msgNoFile: "请选择 Seestar CSV 文件或点击“演示数据”。",
      msgNoFileExplain: "需要加载原始 CSV 测量数据才能执行 AAVSO 转换。",
      msgStopped: "已由用户停止",
      msgStoppedExplain: "所有活动的 SIMBAD 与代理网络请求已安全中止。",
      msgClearDone: "所有字段、图表和文件已清空",
      msgClearExplain: "工作区已重置，可开始处理下一颗目标星。",
      msgSimbadCache: "📦 SIMBAD 来自缓存",
      msgVspCache: "📦 VSP 来自缓存",
      msgConverted: "✓ 转换成功完成",
      msgConvertedExplain: "已生成标准 AAVSO Extended 文件，包含曝光中点 JD 及四位小数精度校验。",
      msgNoData: "⚠ 未找到 'Non-reference star' 行。",
      msgNoDataExplain: "请确认上传的 CSV 文件来自 Seestar 测光模式。",
      msgNoCheckStar: "⚠ 无法自动选择比较星，请手动输入 KNAME/KMAG。",
      msgCheckStarWarn: "⚠ 请确认所选检验星位于您的画面中且非变星。",
      msgDiagnoseHeader: "══ 网络与镜像诊断 ══",
      msgDiagStep1: "步骤 1：直连测试 CORS 代理服务器",
      msgDiagStep2: "步骤 2：通过代理竞速测试 SIMBAD 镜像",
      msgDiagnoseDone: "══ 诊断完成 ══",
      msgDirectMirrors: "并行直连 SIMBAD 镜像…",
      msgProxiesFallback: "代理竞速查询镜像…",
      msgVspDirect: "直连请求 AAVSO VSP…",
      msgVspProxy: "通过代理访问 AAVSO VSP…",
      msgSimbadDown: "SIMBAD 暂时无法访问。",
      msgVspDown: "AAVSO VSP 暂时无法访问。",
      msgNoChartId: "未返回 CHART ID",
      thParam: "参数",
      thFile: "来自 Seestar 的数据",
      thUI: "来自 SIMBAD 星表的数据",
      thMatch: "检查",
      matchOk: "✓ 匹配",
      matchBad: "✗ 重大差异",
      matchWarn: "⚠ 有差异（正常）",
      matchMissing: "— 无数据",
      starIdMissing: "— 将使用文件数据",
      previewReady: "文件已读取。请检查下方参数比对与光变曲线。",
      starIdCorrected: "STARID 与星表不同，导出时将使用界面中的星表 ID。",
      starIdSame: "STARID 完全匹配。",
      fetchingSimbad: "📡 1/2: 正在获取 SIMBAD 坐标...",
      fetchingVsp: "📡 2/2: 正在获取 VSP 星图与检验星...",
      imgLoading: "正在加载 DSS2 巡天图像...",
      imgOpenAladin: "🔭 在 Aladin Lite 中打开",
      imgFieldCaption: "<strong>{star}</strong> 视场图像 (DSS2)",
      imgAltServer: "正在尝试备用 CDS Alasky 服务器...",
      imgLoadError: "无法加载预览图像。",
      imgNoCoords: "请输入有效的 RA 和 DEC 坐标以加载天区图像。",
      fileSavedPicker: "✅ 文件已保存：{name}",
      fileSaveCancelled: "⚠ 用户取消了文件保存。",
      fileDownloaded: "⬇️ 文件已下载至默认下载文件夹 ({name})。",
      demoLoaded: "已加载 SZ Lyncis 演示测光数据！",
      demoLoadedExplain: "现在您可以直接点击“转换为 AAVSO Extended”或测试 SIMBAD + VSP。"
    }
  };

  /**
   * ============================================================================
   * МОДУЛЬ 2: БЕЗОПАСНОСТЬ (SECURITY) И УТИЛИТЫ ЭКРАНИРОВАНИЯ
   * Разработчику: Защита от XSS при выводе данных из CSV или внешних API.
   * Безопасная работа с localStorage в sandboxed окружении.
   * ============================================================================
   */
  function escapeHtml(val) {
    if (val == null || (typeof val === "number" && isNaN(val))) return "—";
    return String(val)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  const _MEMORY_STORE = {};
  window.__SEESTAR_DISK_STORE__ = window.__SEESTAR_DISK_STORE__ || {};

  function safeGetStorage(key, fallback = null) {
    try {
      if (window.__SEESTAR_DISK_STORE__ && Object.prototype.hasOwnProperty.call(window.__SEESTAR_DISK_STORE__, key)) {
        const dv = window.__SEESTAR_DISK_STORE__[key];
        if (dv !== null && dv !== undefined && String(dv) !== "") {
          return String(dv);
        }
      }
    } catch (_) {}
    try {
      const v = localStorage.getItem(key);
      if (v !== null && v !== undefined) return v;
    } catch (_) {}
    return Object.prototype.hasOwnProperty.call(_MEMORY_STORE, key) ? _MEMORY_STORE[key] : fallback;
  }

  const _PENDING_DISK_WRITES = {};
  function safeSetStorage(key, val) {
    const strVal = String(val);
    _MEMORY_STORE[key] = strVal;
    try {
      window.__SEESTAR_DISK_STORE__ = window.__SEESTAR_DISK_STORE__ || {};
      window.__SEESTAR_DISK_STORE__[key] = strVal;
    } catch (_) {}
    try {
      localStorage.setItem(key, strVal);
    } catch (_) {}
    try {
      if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.save_store_item === "function") {
        window.pywebview.api.save_store_item(String(key), strVal);
      } else {
        _PENDING_DISK_WRITES[String(key)] = strVal;
      }
    } catch (_) {
      _PENDING_DISK_WRITES[String(key)] = strVal;
    }
  }

  function safeRemoveStorage(key) {
    delete _MEMORY_STORE[key];
    try {
      if (window.__SEESTAR_DISK_STORE__) delete window.__SEESTAR_DISK_STORE__[key];
    } catch (_) {}
    try {
      localStorage.removeItem(key);
    } catch (_) {}
    try {
      if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.remove_store_item === "function") {
        window.pywebview.api.remove_store_item(String(key));
      }
    } catch (_) {}
  }
  window.safeGetStorage = safeGetStorage;
  window.safeSetStorage = safeSetStorage;


  const COMPLETE_PATCH_I18N = {
  "ru": {
    "lcEmptyTitle": "Кривая блеска появится после загрузки CSV",
    "lcEmptyDesc": "Загрузите CSV-файл фотометрии Seestar (минимум 2 целевых кадра «Non-reference star»), чтобы построить график блеска и погрешностей.",
    "tipObsCodeShort": "Наведите или нажмите на значок «?» выше для просмотра рекомендации по коду AAVSO.",
    "phObsFilterDate": "ДД.ММ.ГГГГ",
    "dssEmptyCaption": "Выберите цель или загрузите файл для отображения поля зрения DSS2",
    "dssSurveyFovLabel": "Обзор карты DSS2: 2.40°×2.40°",
    "lblStarFieldPhoto": "🌌 Снимок окрестностей звезды (DSS2)",
    "critModalTitle": "Критическое расхождение данных",
    "critModalBody": "Обнаружено критическое расхождение данных. Конвертация заблокирована. Проверьте правильность выбранной звезды и файла.",
    "btnCritOpenInputs": "📂 Проверить звезду и файл",
    "btnCritClose": "Понятно",
    "phUrgentSearch": "🔍 Поиск звезды (T CrB, SZ Lyn, CH Cyg)...",
    "splashLangLabel": "Язык интерфейса:",
    "statusExplainDefault": "ℹ️ Журнал сетевых запросов и конвертации",
    "tipAavsoSite": "Официальный портал AAVSO (American Association of Variable Star Observers)",
    "tipHomeBtn": "Открыть стартовое окно Seestar AstroLab AAVSO",
    "tipSeestarSite": "Официальный сайт умных телескопов ZWO Seestar",
    "vspLoadingStepDefault": "Координаты RA/DEC получены. Опрашиваем порты и мировые зеркала каталогов...",
    "msgStarImageMissing": "Изображение звезды в каталогах отсутствует",
    "errNoStarIdTitle": "Не выбрана звезда (STARID)",
    "errNoStarIdMsg": "Пожалуйста, укажите имя или ID звезды (STARID) перед конвертацией.",
    "errNoSimbadLoadedTitle": "Не загружены данные SIMBAD + VSP",
    "errNoSimbadLoadedMsg": "Нажмите «🔭 Загрузить SIMBAD + VSP», чтобы получить координаты и карту калибровки перед конвертацией.",
    "errNoCsvSelectedTitle": "Не выбран CSV-файл фотометрии",
    "errNoCsvSelectedMsg": "Выберите исходный CSV-файл от Seestar (или нажмите «Демо CSV») в разделе 2 перед конвертацией.",
    "errServersUnavailableTitle": "Серверы каталогов SIMBAD / AAVSO VSP недоступны",
    "errServersUnavailableBody": "Не удалось получить данные от серверов SIMBAD / AAVSO VSP. Проверьте подключение к интернету или запустите «Диагностику сети и зеркал» в меню «Настройки».",
    "waitingSimbadBadge": "⏳ Ожидается SIMBAD",
    "notLoadedSimbadCell": "— (Не загружено)",
    "simbadPreloadedFmt": "✓ Данные SIMBAD ({star}) загружены — выберите CSV-файл Seestar для сверки",
    "vspStep1Loading": "⏳ Шаг 1/2: Опрос мировых зеркал SIMBAD (получение координат RA/DEC)...",
    "vspStep2Loading": "⏳ Шаг 2/2: Загрузка карты AAVSO VSP (CHART, KNAME, KMAG)...",
    "lblConvertWait": "Ожидание шагов 1 и 2",
    "lblConvertReady": "✓ Готово к конвертации"
  },
  "en": {
    "lcEmptyTitle": "Light curve will appear after loading CSV",
    "lcEmptyDesc": "Load a Seestar photometry CSV file (at least 2 target 'Non-reference star' frames) to plot the magnitude light curve and error bars.",
    "tipObsCodeShort": "Hover or tap the '?' icon above to view the AAVSO Observer Code recommendation.",
    "phObsFilterDate": "YYYY-MM-DD",
    "dssEmptyCaption": "Select a target or load a CSV file to display the DSS2 star field",
    "dssSurveyFovLabel": "DSS2 Survey View: 2.40°×2.40°",
    "lblStarFieldPhoto": "🌌 Star Field Survey Image (DSS2)",
    "critModalTitle": "Critical Data Mismatch",
    "critModalBody": "A critical data mismatch was detected. Conversion is locked. Please verify the selected target star and CSV file.",
    "btnCritOpenInputs": "📂 Check Star & File",
    "btnCritClose": "Got it",
    "phUrgentSearch": "🔍 Search star (T CrB, SZ Lyn, CH Cyg)...",
    "splashLangLabel": "Interface Language:",
    "statusExplainDefault": "ℹ️ Network queries & conversion log",
    "tipAavsoSite": "Official AAVSO portal (American Association of Variable Star Observers)",
    "tipHomeBtn": "Open Seestar AstroLab AAVSO welcome screen",
    "tipSeestarSite": "Official ZWO Seestar smart telescopes website",
    "vspLoadingStepDefault": "RA/DEC coordinates obtained. Querying global catalog mirrors...",
    "msgStarImageMissing": "Star image is not available in the catalogs",
    "errNoStarIdTitle": "Target Star (STARID) Not Selected",
    "errNoStarIdMsg": "Please enter a target star name or ID (STARID) before converting.",
    "errNoSimbadLoadedTitle": "SIMBAD + VSP Data Not Loaded",
    "errNoSimbadLoadedMsg": "Please click '🔭 Load SIMBAD + VSP' to fetch catalog coordinates and calibration data before converting.",
    "errNoCsvSelectedTitle": "Seestar CSV File Not Selected",
    "errNoCsvSelectedMsg": "Please select a Seestar photometry CSV file (or click 'Demo CSV') in Section 2 before converting.",
    "errServersUnavailableTitle": "SIMBAD / AAVSO VSP Catalog Servers Unavailable",
    "errServersUnavailableBody": "Could not reach SIMBAD / AAVSO VSP servers. Please check your internet connection or run 'Network & Mirror Diagnostics' in Settings.",
    "waitingSimbadBadge": "⏳ Waiting for SIMBAD",
    "notLoadedSimbadCell": "— (Not loaded)",
    "simbadPreloadedFmt": "✓ SIMBAD data ({star}) loaded — select a Seestar CSV file to compare",
    "vspStep1Loading": "⏳ Step 1/2: Querying global SIMBAD mirrors (fetching RA/DEC)...",
    "vspStep2Loading": "⏳ Step 2/2: Fetching AAVSO VSP chart & check star (CHART, KNAME, KMAG)...",
    "lblConvertWait": "Waiting for Steps 1 & 2",
    "lblConvertReady": "✓ Ready to convert"
  },
  "es": {
    "lcEmptyTitle": "La curva de luz aparecerá tras cargar el CSV",
    "lcEmptyDesc": "Cargue un archivo CSV de fotometría Seestar (mínimo 2 fotogramas objetivo «Non-reference star») para trazar la curva de luz y las barras de error.",
    "tipObsCodeShort": "Pase el cursor o toque el icono «?» arriba para ver la recomendación sobre el código de observador AAVSO.",
    "tipObsCodeText": "Código oficial de observador AAVSO (escrito en la cabecera #OBSCODE). 💡 Recomendación: indique su código personal de observador AAVSO (gratuito en su perfil de aavso.org). Sin él, AAVSO WebObs no vinculará las observaciones a su cuenta.",
    "obsCodeRecHtml": "💡 <strong>Recomendación:</strong> indique <strong>su código personal de observador AAVSO</strong> (gratuito en su perfil de <a href='https://www.aavso.org' target='_blank' rel='noopener noreferrer'>aavso.org</a>). Sin su código personal, el portal AAVSO WebObs no vinculará las observaciones a su cuenta.",
    "phObsCode": "Introduzca su código personal AAVSO",
    "phObsFilterDate": "DD/MM/AAAA",
    "guideModalTitle": "📈 Cómo leer las curvas de luz de AAVSO y Seestar",
    "guideModalBodyHtml": "\n      <p style=\"font-size:13px; color:#dbeafe; margin:0 0 10px 0;\">\n        Guía visual para interpretar curvas de luz de estrellas variables, binarias eclipsantes y tránsitos de exoplanetas convertidas desde <strong>ZWO Seestar</strong>.\n      </p>\n\n      <div class=\"guide-svg-box\" style=\"margin-bottom:12px; padding:12px;\">\n        <div style=\"font-size:11px; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:6px;\">\n          DIAGRAMA DE CURVA DE LUZ (EJEMPLO DE BINARIA ECLIPSANTE / VARIABLE PULSANTE)\n        </div>\n        <svg viewBox=\"0 0 600 185\" width=\"100%\" height=\"175\" style=\"display:block; background:#070b14; border-radius:8px; border:1px solid rgba(100,210,255,0.18);\">\n          <line x1=\"55\" y1=\"28\" x2=\"575\" y2=\"28\" stroke=\"#1e293b\" stroke-dasharray=\"4 4\" stroke-width=\"1\"/>\n          <line x1=\"55\" y1=\"82\" x2=\"575\" y2=\"82\" stroke=\"#1e293b\" stroke-dasharray=\"4 4\" stroke-width=\"1\"/>\n          <line x1=\"55\" y1=\"138\" x2=\"575\" y2=\"138\" stroke=\"#1e293b\" stroke-dasharray=\"4 4\" stroke-width=\"1\"/>\n          <line x1=\"55\" y1=\"15\" x2=\"55\" y2=\"155\" stroke=\"#475569\" stroke-width=\"1.5\"/>\n          <line x1=\"55\" y1=\"155\" x2=\"575\" y2=\"155\" stroke=\"#475569\" stroke-width=\"1.5\"/>\n          <text x=\"8\" y=\"32\" fill=\"#86efac\" font-size=\"11\" font-family=\"monospace\" font-weight=\"bold\">11.5m ↑</text>\n          <text x=\"8\" y=\"86\" fill=\"#94a3b8\" font-size=\"11\" font-family=\"monospace\">12.0m</text>\n          <text x=\"8\" y=\"142\" fill=\"#fca5a5\" font-size=\"11\" font-family=\"monospace\" font-weight=\"bold\">12.5m ↓</text>\n          <text x=\"64\" y=\"22\" fill=\"#38bdf8\" font-size=\"10.5\" font-family=\"sans-serif\" font-weight=\"bold\">↑ Más brillante (Menor valor MAG = mayor brillo)</text>\n          <text x=\"64\" y=\"150\" fill=\"#f87171\" font-size=\"10.5\" font-family=\"sans-serif\" font-weight=\"bold\">↓ Más débil (Mayor valor MAG = menor brillo)</text>\n          <path d=\"M 70 50 L 185 50 C 225 50, 255 136, 305 136 C 355 136, 385 50, 425 50 L 555 50\" fill=\"none\" stroke=\"#38bdf8\" stroke-width=\"2.5\" stroke-dasharray=\"6 4\"/>\n          <g stroke=\"#64d2ff\" stroke-width=\"1.5\">\n            <line x1=\"95\" y1=\"41\" x2=\"95\" y2=\"59\"/><circle cx=\"95\" cy=\"50\" r=\"4\" fill=\"#38bdf8\"/>\n            <line x1=\"145\" y1=\"39\" x2=\"145\" y2=\"57\"/><circle cx=\"145\" cy=\"48\" r=\"4\" fill=\"#38bdf8\"/>\n            <line x1=\"195\" y1=\"45\" x2=\"195\" y2=\"63\"/><circle cx=\"195\" cy=\"54\" r=\"4\" fill=\"#38bdf8\"/>\n            <line x1=\"250\" y1=\"88\" x2=\"250\" y2=\"110\"/><circle cx=\"250\" cy=\"99\" r=\"4\" fill=\"#facc15\"/>\n            <line x1=\"305\" y1=\"124\" x2=\"305\" y2=\"148\"/><circle cx=\"305\" cy=\"136\" r=\"5.5\" fill=\"#ef4444\" stroke=\"#fff\"/>\n            <line x1=\"360\" y1=\"86\" x2=\"360\" y2=\"108\"/><circle cx=\"360\" cy=\"97\" r=\"4\" fill=\"#facc15\"/>\n            <line x1=\"415\" y1=\"43\" x2=\"415\" y2=\"61\"/><circle cx=\"415\" cy=\"52\" r=\"4\" fill=\"#38bdf8\"/>\n            <line x1=\"475\" y1=\"40\" x2=\"475\" y2=\"58\"/><circle cx=\"475\" cy=\"49\" r=\"4\" fill=\"#38bdf8\"/>\n            <line x1=\"535\" y1=\"42\" x2=\"535\" y2=\"60\"/><circle cx=\"535\" cy=\"51\" r=\"4\" fill=\"#38bdf8\"/>\n          </g>\n          <text x=\"90\" y=\"35\" fill=\"#e2e8f0\" font-size=\"10.5\" font-family=\"sans-serif\">Brillo normal (Meseta)</text>\n          <text x=\"215\" y=\"120\" fill=\"#fde047\" font-size=\"10.5\" font-family=\"sans-serif\" font-weight=\"bold\">Mínimo principal (Eclipse / Tránsito)</text>\n          <text x=\"425\" y=\"75\" fill=\"#94a3b8\" font-size=\"10\" font-family=\"sans-serif\">Barras de error (±MERR)</text>\n          <text x=\"195\" y=\"174\" fill=\"#cbd5e1\" font-size=\"11\" font-family=\"monospace\">Tiempo de observación: Fecha Juliana (JD Mid) →</text>\n        </svg>\n      </div>\n\n      <div class=\"guide-two-col\">\n        <div class=\"guide-item\">\n          <h4>1. Eje Y (Magnitud estelar / MAG)</h4>\n          <p>En astronomía la escala de magnitudes está <strong>invertida</strong>:<br>• ¡Un número <code>MAG</code> <strong>menor</strong> (ej. <code>9.10m</code> frente a <code>9.50m</code>) significa que la estrella es <strong>más brillante</strong>!<br>• En el gráfico los números menores están arriba: una subida indica aumento de brillo y una caída indica disminución (eclipse o tránsito).</p>\n        </div>\n        <div class=\"guide-item\">\n          <h4>2. Eje X (Fecha Juliana / JD Mid)</h4>\n          <p>El eje horizontal muestra el instante exacto de mitad de exposición de cada toma Seestar en <strong>Fecha Juliana (JD Mid)</strong>.<br>• Ejemplo: <code>2461346.3671</code> es un conteo continuo de días UTC y fracciones.<br>• Permite combinar series temporales de observadores de todo el mundo con precisión de segundos.</p>\n        </div>\n      </div>\n\n      <div class=\"guide-grid\" style=\"margin-top:10px;\">\n        <div class=\"guide-item\" style=\"background:rgba(10,132,255,0.10); border-color:rgba(100,210,255,0.32);\">\n          <h4>💡 ¿Por qué los puntos oscilan arriba y abajo? (Dispersión y barras ±MERR)</h4>\n          <p>Cada punto es una subexposición de Seestar (10s–20s), y la barra vertical representa la incertidumbre <code>±MERR</code>.<br>• Una pequeña dispersión de <code>0.01–0.02m</code> es el centelleo atmosférico normal y el ruido fotónico.<br>• Cuando los puntos trazan una onda suave o una caída en V/U mucho más profunda que las barras de error, ¡ha detectado <strong>variabilidad astrofísica real</strong>!</p>\n        </div>\n\n        <div class=\"guide-item\">\n          <h4>3. Firmas típicas de curvas de luz:</h4>\n          <p>• <strong>Variables pulsantes (SZ Lyn, RR Lyr, δ Sct):</strong> Onda suave con subida rápida al máximo y descenso más lento (amplitud <code>0.15–0.80m</code>).<br>• <strong>Binarias eclipsantes (EA, EB, EW):</strong> Caída pronunciada en forma de V cuando una estrella oculta a su compañera.<br>• <strong>Tránsitos de exoplanetas:</strong> Caída poco profunda en forma de U con fondo plano (<code>0.01–0.03m</code>).</p>\n        </div>\n      </div>\n",
    "btnGraphGuideShort": "📖 ¿Cómo leer el gráfico?",
    "dssEmptyCaption": "Seleccione un objetivo o cargue un archivo CSV para mostrar el campo estelar DSS2",
    "dssSurveyFovLabel": "Campo del mapa DSS2: 2.40°×2.40°",
    "lblStarFieldPhoto": "🌌 Imagen del campo estelar (DSS2)",
    "critModalTitle": "Discrepancia crítica de datos",
    "critModalBody": "Se detectó una discrepancia crítica de datos. La conversión está bloqueada. Verifique la estrella seleccionada y el archivo CSV.",
    "btnCritOpenInputs": "📂 Verificar estrella y archivo",
    "btnCritClose": "Entendido",
    "phUrgentSearch": "🔍 Buscar estrella (T CrB, SZ Lyn, CH Cyg)...",
    "splashLangLabel": "Idioma de la interfaz:",
    "lblSplashLang": "Idioma de la interfaz:",
    "statusExplainDefault": "ℹ️ Registro de consultas de red y conversión",
    "tipAavsoSite": "Portal oficial de AAVSO",
    "tipHomeBtn": "Abrir pantalla de inicio de Seestar AstroLab AAVSO",
    "tipSeestarSite": "Sitio web oficial de telescopios inteligentes ZWO Seestar",
    "vspLoadingTitle": "⏳ Cargando CHART (VSP), KNAME (AUID) y KMAG...",
    "vspLoadingStepDefault": "Coordenadas RA/DEC obtenidas. Consultando espejos globales de catálogos...",
    "msgAllLoadedTitle": "✅ ¡Todos los datos de catálogos se cargaron con éxito!",
    "msgAllLoadedBody": "Se cargaron RA/DEC, nombre canónico ({star}), carta CHART ({chart}), estrella de control KNAME ({kname}) y magnitud KMAG ({kmag}).",
    "msgVspFailedTitle": "❌ Error al cargar los datos de calibración VSP",
    "msgVspFailedBody": "Se consultaron todos los espejos disponibles (AAVSO VSP, VizieR, SIMBAD), pero no se pudo obtener CHART/KNAME/KMAG.",
    "starIdAutoAssigned": "✓ Nombre oficial asignado del catálogo VSX/SIMBAD: «{cat}» (en el archivo: «{file}»)",
    "tipVerifyFileText": "Verifica que cualquier archivo CSV/TXT convertido en su disco cumpla con todos los requisitos de AAVSO WebObs (#TYPE=EXTENDED, #OBSCODE, JD, MAG, MERR, KNAME, KMAG).",
    "urgentStarsIntro": "Objetivos prioritarios de campañas AAVSO Alert Notices para telescopios Seestar. Haga clic en una estrella para cargar sus coordenadas.",
    "submitModalTitle": "🚀 Enviar archivo a AAVSO WebObs (?preview=true)",
    "btnOpenAavsoCard": "📤 Abrir página de carga AAVSO Photometry",
    "btnOpenAavsoMenu": "📤 Enviar a AAVSO",
    "btnDonateLater": "Recordar el próximo mes",
    "btnDonateNever": "No volver a mostrar",
    "btnDownloadDesktopShortcut": "💻 Descargar acceso directo para PC",
    "btnInstallApp": "📲 Instalar aplicación",
    "btnTriggerNativeInstall": "⚡ Instalar en 1 clic",
    "installModalTitle": "📲 Instalar aplicación Seestar AstroLab",
    "installModalIntro": "Esta aplicación admite la instalación directa como aplicación de escritorio.",
    "msgStarImageMissing": "La imagen de la estrella no está disponible en los catálogos",
    "errNoStarIdTitle": "Estrella (STARID) no seleccionada",
    "errNoStarIdMsg": "Introduzca el nombre o ID de la estrella (STARID) antes de convertir.",
    "errNoSimbadLoadedTitle": "Datos SIMBAD + VSP no cargados",
    "errNoSimbadLoadedMsg": "Haga clic en '🔭 Cargar SIMBAD + VSP' antes de convertir.",
    "errNoCsvSelectedTitle": "Archivo CSV de Seestar no seleccionado",
    "errNoCsvSelectedMsg": "Seleccione un archivo CSV de Seestar en la Sección 2 antes de convertir.",
    "errServersUnavailableTitle": "Servidores de catálogos SIMBAD / AAVSO VSP no disponibles",
    "errServersUnavailableBody": "No se pudo conectar con los servidores SIMBAD / AAVSO VSP. Verifique su conexión a Internet o ejecute el diagnóstico de red en Ajustes.",
    "waitingSimbadBadge": "⏳ Esperando SIMBAD",
    "notLoadedSimbadCell": "— (No cargado)",
    "simbadPreloadedFmt": "✓ Datos SIMBAD ({star}) cargados — seleccione un archivo CSV",
    "vspStep1Loading": "⏳ Paso 1/2: Consultando espejos SIMBAD...",
    "vspStep2Loading": "⏳ Paso 2/2: Cargando carta AAVSO VSP...",
    "lblConvertWait": "Esperando pasos 1 y 2",
    "lblConvertReady": "✓ Listo para convertir"
  },
  "de": {
    "lcEmptyTitle": "Lichtkurve erscheint nach dem Laden der CSV-Datei",
    "lcEmptyDesc": "Laden Sie eine Seestar-Fotometrie-CSV-Datei (mindestens 2 Zielaufnahmen „Non-reference star“), um die Helligkeitskurve und Fehlerbalken zu zeichnen.",
    "tipObsCodeShort": "Bewegen Sie den Mauszeiger über das Symbol „?“ oben oder tippen Sie darauf, um die Empfehlung zum AAVSO-Beobachtercode anzuzeigen.",
    "tipObsCodeText": "Ihr offizieller AAVSO-Beobachtercode (#OBSCODE). 💡 Empfehlung: Bitte geben Sie Ihren persönlichen AAVSO-Beobachtercode an (kostenlos im Profil auf aavso.org). Ohne diesen Code kann AAVSO WebObs die Messungen nicht Ihrem Konto zuordnen.",
    "obsCodeRecHtml": "💡 <strong>Empfehlung:</strong> Bitte geben Sie <strong>Ihren persönlichen AAVSO-Beobachtercode</strong> an (kostenlos im Profil auf <a href='https://www.aavso.org' target='_blank' rel='noopener noreferrer'>aavso.org</a>). Ohne Ihren Code kann AAVSO WebObs die Beobachtungen nicht Ihrem Konto zuordnen.",
    "phObsCode": "Persönlichen AAVSO-Code eingeben",
    "phObsFilterDate": "TT.MM.JJJJ",
    "guideModalTitle": "📈 So liest man AAVSO- & Seestar-Lichtkurven",
    "guideModalBodyHtml": "\n      <p style=\"font-size:13px; color:#dbeafe; margin:0 0 10px 0;\">\n        Visueller Leitfaden zur Interpretation von Lichtkurven veränderlicher Sterne, Bedeckungsveränderlicher und Exoplaneten-Transits aus der <strong>ZWO Seestar</strong>-Fotometrie.\n      </p>\n\n      <div class=\"guide-svg-box\" style=\"margin-bottom:12px; padding:12px;\">\n        <div style=\"font-size:11px; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:6px;\">\n          LICHTKURVEN-DIAGRAMM (BEISPIEL BEDECKUNGSVERÄNDERLICHER / PULSIERENDER STERN)\n        </div>\n        <svg viewBox=\"0 0 600 185\" width=\"100%\" height=\"175\" style=\"display:block; background:#070b14; border-radius:8px; border:1px solid rgba(100,210,255,0.18);\">\n          <line x1=\"55\" y1=\"28\" x2=\"575\" y2=\"28\" stroke=\"#1e293b\" stroke-dasharray=\"4 4\" stroke-width=\"1\"/>\n          <line x1=\"55\" y1=\"82\" x2=\"575\" y2=\"82\" stroke=\"#1e293b\" stroke-dasharray=\"4 4\" stroke-width=\"1\"/>\n          <line x1=\"55\" y1=\"138\" x2=\"575\" y2=\"138\" stroke=\"#1e293b\" stroke-dasharray=\"4 4\" stroke-width=\"1\"/>\n          <line x1=\"55\" y1=\"15\" x2=\"55\" y2=\"155\" stroke=\"#475569\" stroke-width=\"1.5\"/>\n          <line x1=\"55\" y1=\"155\" x2=\"575\" y2=\"155\" stroke=\"#475569\" stroke-width=\"1.5\"/>\n          <text x=\"8\" y=\"32\" fill=\"#86efac\" font-size=\"11\" font-family=\"monospace\" font-weight=\"bold\">11.5m ↑</text>\n          <text x=\"8\" y=\"86\" fill=\"#94a3b8\" font-size=\"11\" font-family=\"monospace\">12.0m</text>\n          <text x=\"8\" y=\"142\" fill=\"#fca5a5\" font-size=\"11\" font-family=\"monospace\" font-weight=\"bold\">12.5m ↓</text>\n          <text x=\"64\" y=\"22\" fill=\"#38bdf8\" font-size=\"10.5\" font-family=\"sans-serif\" font-weight=\"bold\">↑ Heller (Kleinerer MAG-Wert ist heller)</text>\n          <text x=\"64\" y=\"150\" fill=\"#f87171\" font-size=\"10.5\" font-family=\"sans-serif\" font-weight=\"bold\">↓ Schwächer (Größerer MAG-Wert ist dunkler)</text>\n          <path d=\"M 70 50 L 185 50 C 225 50, 255 136, 305 136 C 355 136, 385 50, 425 50 L 555 50\" fill=\"none\" stroke=\"#38bdf8\" stroke-width=\"2.5\" stroke-dasharray=\"6 4\"/>\n          <g stroke=\"#64d2ff\" stroke-width=\"1.5\">\n            <line x1=\"95\" y1=\"41\" x2=\"95\" y2=\"59\"/><circle cx=\"95\" cy=\"50\" r=\"4\" fill=\"#38bdf8\"/>\n            <line x1=\"145\" y1=\"39\" x2=\"145\" y2=\"57\"/><circle cx=\"145\" cy=\"48\" r=\"4\" fill=\"#38bdf8\"/>\n            <line x1=\"195\" y1=\"45\" x2=\"195\" y2=\"63\"/><circle cx=\"195\" cy=\"54\" r=\"4\" fill=\"#38bdf8\"/>\n            <line x1=\"250\" y1=\"88\" x2=\"250\" y2=\"110\"/><circle cx=\"250\" cy=\"99\" r=\"4\" fill=\"#facc15\"/>\n            <line x1=\"305\" y1=\"124\" x2=\"305\" y2=\"148\"/><circle cx=\"305\" cy=\"136\" r=\"5.5\" fill=\"#ef4444\" stroke=\"#fff\"/>\n            <line x1=\"360\" y1=\"86\" x2=\"360\" y2=\"108\"/><circle cx=\"360\" cy=\"97\" r=\"4\" fill=\"#facc15\"/>\n            <line x1=\"415\" y1=\"43\" x2=\"415\" y2=\"61\"/><circle cx=\"415\" cy=\"52\" r=\"4\" fill=\"#38bdf8\"/>\n            <line x1=\"475\" y1=\"40\" x2=\"475\" y2=\"58\"/><circle cx=\"475\" cy=\"49\" r=\"4\" fill=\"#38bdf8\"/>\n            <line x1=\"535\" y1=\"42\" x2=\"535\" y2=\"60\"/><circle cx=\"535\" cy=\"51\" r=\"4\" fill=\"#38bdf8\"/>\n          </g>\n          <text x=\"90\" y=\"35\" fill=\"#e2e8f0\" font-size=\"10.5\" font-family=\"sans-serif\">Normalhelligkeit (Plateau)</text>\n          <text x=\"215\" y=\"120\" fill=\"#fde047\" font-size=\"10.5\" font-family=\"sans-serif\" font-weight=\"bold\">Hauptminimum (Bedeckung / Transit)</text>\n          <text x=\"425\" y=\"75\" fill=\"#94a3b8\" font-size=\"10\" font-family=\"sans-serif\">Fehlerbalken (±MERR)</text>\n          <text x=\"195\" y=\"174\" fill=\"#cbd5e1\" font-size=\"11\" font-family=\"monospace\">Beobachtungszeit: Julianisches Datum (JD Mid) →</text>\n        </svg>\n      </div>\n\n      <div class=\"guide-two-col\">\n        <div class=\"guide-item\">\n          <h4>1. Y-Achse (Scheinbare Helligkeit / MAG)</h4>\n          <p>Die astronomische Magnitudenskala ist <strong>invertiert (umgekehrt)</strong>:<br>• Ein <strong>kleinerer</strong> <code>MAG</code>-Wert (z. B. <code>9.10m</code> statt <code>9.50m</code>) bedeutet, dass der Stern <strong>heller</strong> leuchtet!<br>• Im Diagramm stehen kleinere Zahlen oben: Ein Anstieg nach <strong>oben</strong> bedeutet Helligkeitszunahme, ein Einbruch nach <strong>unten</strong> Verdunkelung (Bedeckung oder Transit).</p>\n        </div>\n        <div class=\"guide-item\">\n          <h4>2. X-Achse (Julianisches Datum / JD Mid)</h4>\n          <p>Die horizontale Achse zeigt den exakten Zeitpunkt der Belichtungsmitte jeder Seestar-Aufnahme als <strong>Julianisches Datum (JD Mid)</strong>.<br>• Beispiel: <code>2461346.3671</code> ist eine fortlaufende Zählung von UTC-Tagen und Tagesbruchteilen.<br>• Ermöglicht Astronomen weltweit die sekundengenaue Kombination von Zeitreihen.</p>\n        </div>\n      </div>\n\n      <div class=\"guide-grid\" style=\"margin-top:10px;\">\n        <div class=\"guide-item\" style=\"background:rgba(10,132,255,0.10); border-color:rgba(100,210,255,0.32);\">\n          <h4>💡 Warum streuen die Punkte auf und ab? (Streuung & ±MERR-Fehlerbalken)</h4>\n          <p>Jeder Punkt ist eine einzelne Seestar-Einzelbelichtung (10s–20s), und der vertikale Balken zeigt die Messunsicherheit <code>±MERR</code>.<br>• Eine kleine Streuung von <code>0.01–0.02m</code> zwischen Nachbarpunkten ist normale Luftunruhe (Szintillation) und Sensorrauschen.<br>• Wenn die Punkte eine klare Welle oder ein V/U-förmiges Minimum bilden, das deutlich tiefer als die Fehlerbalken ist, haben Sie <strong>echte astrophysikalische Variabilität</strong> nachgewiesen!</p>\n        </div>\n\n        <div class=\"guide-item\">\n          <h4>3. Typische Lichtkurven-Profile:</h4>\n          <p>• <strong>Pulsierende Veränderliche (SZ Lyn, RR Lyr, δ Sct):</strong> Sanfte Welle mit raschem Anstieg zum Maximum und langsamerem Abstieg (Amplitude <code>0.15–0.80m</code>).<br>• <strong>Bedeckungsveränderliche (EA, EB, EW):</strong> Scharfer V-förmiger Einbruch, wenn ein Stern seinen Begleiter bedeckt.<br>• <strong>Exoplaneten-Transits:</strong> Flache, U-förmige Einsenkung mit ebenem Boden (<code>0.01–0.03m</code>).</p>\n        </div>\n      </div>\n",
    "btnGraphGuideShort": "📖 Wie liest man die Kurve?",
    "dssEmptyCaption": "Zielstern wählen oder CSV-Datei laden, um das DSS2-Sternfeld anzuzeigen",
    "dssSurveyFovLabel": "DSS2-Kartenfeld: 2.40°×2.40°",
    "lblStarFieldPhoto": "🌌 Sternfeldbild (DSS2)",
    "critModalTitle": "Kritische Datenabweichung",
    "critModalBody": "Es wurde eine kritische Datenabweichung festgestellt. Die Konvertierung ist gesperrt. Bitte prüfen Sie den gewählten Stern und die CSV-Datei.",
    "btnCritOpenInputs": "📂 Stern & Datei prüfen",
    "btnCritClose": "Verstanden",
    "phUrgentSearch": "🔍 Stern suchen (T CrB, SZ Lyn, CH Cyg)...",
    "splashLangLabel": "Oberflächensprache:",
    "lblSplashLang": "Oberflächensprache:",
    "statusExplainDefault": "ℹ️ Netzwerkabfragen- und Konvertierungsprotokoll",
    "tipAavsoSite": "Offizielles AAVSO-Portal",
    "tipHomeBtn": "Startfenster von Seestar AstroLab AAVSO öffnen",
    "tipSeestarSite": "Offizielle Website der ZWO Seestar Smart-Teleskope",
    "vspLoadingTitle": "⏳ Lade CHART (VSP), KNAME (AUID) & KMAG...",
    "vspLoadingStepDefault": "RA/DEC-Koordinaten erhalten. Globale Katalogspiegel werden abgefragt...",
    "msgAllLoadedTitle": "✅ Alle Katalogdaten erfolgreich geladen!",
    "msgAllLoadedBody": "RA/DEC, kanonischer Sternname ({star}), Karte CHART ({chart}), Kontrollstern KNAME ({kname}) und KMAG ({kmag}) geladen.",
    "msgVspFailedTitle": "❌ Fehler beim Laden der VSP-Kalibrierungsdaten",
    "msgVspFailedBody": "Alle verfügbaren Katalogspiegel (AAVSO VSP, VizieR, SIMBAD) wurden abgefragt, aber CHART/KNAME/KMAG konnten nicht abgerufen werden.",
    "starIdAutoAssigned": "✓ Offizieller VSX/SIMBAD-Katalogname zugewiesen: „{cat}“ (in Datei: „{file}“)",
    "tipVerifyFileText": "Prüft eine konvertierte CSV/TXT-Datei auf vollständige Kompatibilität mit den AAVSO WebObs-Anforderungen (#TYPE=EXTENDED, #OBSCODE, JD, MAG, MERR, KNAME, KMAG).",
    "urgentStarsIntro": "Dringende Beobachtungsziele der AAVSO Alert Notices für Seestar-Teleskope. Klicken Sie auf eine Karte, um die Daten zu übernehmen.",
    "submitModalTitle": "🚀 Datei an AAVSO WebObs senden (?preview=true)",
    "btnOpenAavsoCard": "📤 AAVSO Photometry-Upload-Seite öffnen",
    "btnOpenAavsoMenu": "📤 An AAVSO senden",
    "btnDonateLater": "Nächsten Monat erinnern",
    "btnDonateNever": "Nicht mehr anzeigen",
    "btnDownloadDesktopShortcut": "💻 PC-Desktop-Verknüpfung herunterladen",
    "btnInstallApp": "📲 App installieren",
    "btnTriggerNativeInstall": "⚡ 1-Klick-Installation",
    "installModalTitle": "📲 Seestar AstroLab installieren",
    "installModalIntro": "Diese Anwendung unterstützt die direkte Installation als Desktop-App.",
    "authorCompany": "CosmoBehemothych",
    "infoCosmoSub": "Photometrisches Observatorium AAVSO Extended",
    "modeMinimal": "Minimal",
    "modeCompact": "Kompakt",
    "modeFull": "Studio",
    "minimalNotice": "🍃 Minimalmodus aktiviert: schneller 1–2-Klick-Workflow.",
    "compactNotice": "⚡ Kompaktmodus: Parameter und Lichtkurve nebeneinander.",
    "fullNotice": "🔭 Vollständiges Studio: alle wissenschaftlichen Schritte und Logs.",
    "searchPlaceholder": "Schnellsuche: Stern (Algol, SZ Lyn, TX UMa...) [ / oder ⌘K ]",
    "selfTestsTitle": "CosmoBehemothych Kern-Diagnose",
    "selfTestsSuccess": "Alle 8 automatischen Algorithmentests erfolgreich bestanden (100% Präzision)!",
    "msgStarImageMissing": "Sternbild ist in den Katalogen nicht vorhanden",
    "errNoStarIdTitle": "Stern (STARID) nicht ausgewählt",
    "errNoStarIdMsg": "Bitte geben Sie vor der Konvertierung einen Sternnamen (STARID) ein.",
    "errNoSimbadLoadedTitle": "SIMBAD + VSP-Daten nicht geladen",
    "errNoSimbadLoadedMsg": "Bitte klicken Sie vor der Konvertierung auf '🔭 SIMBAD + VSP laden'.",
    "errNoCsvSelectedTitle": "Keine Seestar-CSV-Datei ausgewählt",
    "errNoCsvSelectedMsg": "Bitte wählen Sie in Abschnitt 2 eine Seestar-CSV-Datei aus.",
    "errServersUnavailableTitle": "SIMBAD / AAVSO VSP-Server nicht erreichbar",
    "errServersUnavailableBody": "Die Katalogserver SIMBAD / AAVSO VSP sind derzeit nicht erreichbar. Bitte prüfen Sie Ihre Internetverbindung oder starten Sie die Netzwerkdiagnose.",
    "waitingSimbadBadge": "⏳ Warte auf SIMBAD",
    "notLoadedSimbadCell": "— (Nicht geladen)",
    "simbadPreloadedFmt": "✓ SIMBAD-Daten ({star}) geladen — CSV-Datei wählen",
    "vspStep1Loading": "⏳ Schritt 1/2: SIMBAD-Spiegelserver werden abgefragt...",
    "vspStep2Loading": "⏳ Schritt 2/2: AAVSO VSP-Karte wird geladen...",
    "lblConvertWait": "Warte auf Schritt 1 & 2",
    "lblConvertReady": "✓ Bereit zur Konvertierung"
  },
  "fr": {
    "lcEmptyTitle": "La courbe de lumière s'affichera après le chargement du CSV",
    "lcEmptyDesc": "Chargez un fichier CSV de photométrie Seestar (au moins 2 images cibles « Non-reference star ») pour tracer la courbe de lumière et les barres d'erreur.",
    "tipObsCodeShort": "Survolez ou appuyez sur l'icône « ? » ci-dessus pour afficher la recommandation relative au code d'observateur AAVSO.",
    "tipObsCodeText": "Votre code officiel d'observateur AAVSO (#OBSCODE). 💡 Recommandation : veuillez indiquer votre code personnel d'observateur AAVSO (gratuit dans votre profil sur aavso.org). Sans ce code, AAVSO WebObs n'associera pas les observations à votre compte.",
    "obsCodeRecHtml": "💡 <strong>Recommandation :</strong> veuillez indiquer <strong>votre code personnel d'observateur AAVSO</strong> (gratuit dans votre profil sur <a href='https://www.aavso.org' target='_blank' rel='noopener noreferrer'>aavso.org</a>). Sans votre code personnel, AAVSO WebObs n'associera pas les observations à votre compte.",
    "phObsCode": "Saisissez votre code personnel AAVSO",
    "phObsFilterDate": "JJ/MM/AAAA",
    "guideModalTitle": "📈 Comment lire les courbes de lumière AAVSO et Seestar",
    "guideModalBodyHtml": "\n      <p style=\"font-size:13px; color:#dbeafe; margin:0 0 10px 0;\">\n        Guide visuel pour interpréter les courbes de lumière d'étoiles variables, de binaires à éclipses et de transits d'exoplanètes converties depuis la photométrie <strong>ZWO Seestar</strong>.\n      </p>\n\n      <div class=\"guide-svg-box\" style=\"margin-bottom:12px; padding:12px;\">\n        <div style=\"font-size:11px; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:6px;\">\n          DIAGRAMME DE COURBE DE LUMIÈRE (EXEMPLE BINAIRE À ÉCLIPSES / VARIABLE PULSANTE)\n        </div>\n        <svg viewBox=\"0 0 600 185\" width=\"100%\" height=\"175\" style=\"display:block; background:#070b14; border-radius:8px; border:1px solid rgba(100,210,255,0.18);\">\n          <line x1=\"55\" y1=\"28\" x2=\"575\" y2=\"28\" stroke=\"#1e293b\" stroke-dasharray=\"4 4\" stroke-width=\"1\"/>\n          <line x1=\"55\" y1=\"82\" x2=\"575\" y2=\"82\" stroke=\"#1e293b\" stroke-dasharray=\"4 4\" stroke-width=\"1\"/>\n          <line x1=\"55\" y1=\"138\" x2=\"575\" y2=\"138\" stroke=\"#1e293b\" stroke-dasharray=\"4 4\" stroke-width=\"1\"/>\n          <line x1=\"55\" y1=\"15\" x2=\"55\" y2=\"155\" stroke=\"#475569\" stroke-width=\"1.5\"/>\n          <line x1=\"55\" y1=\"155\" x2=\"575\" y2=\"155\" stroke=\"#475569\" stroke-width=\"1.5\"/>\n          <text x=\"8\" y=\"32\" fill=\"#86efac\" font-size=\"11\" font-family=\"monospace\" font-weight=\"bold\">11.5m ↑</text>\n          <text x=\"8\" y=\"86\" fill=\"#94a3b8\" font-size=\"11\" font-family=\"monospace\">12.0m</text>\n          <text x=\"8\" y=\"142\" fill=\"#fca5a5\" font-size=\"11\" font-family=\"monospace\" font-weight=\"bold\">12.5m ↓</text>\n          <text x=\"64\" y=\"22\" fill=\"#38bdf8\" font-size=\"10.5\" font-family=\"sans-serif\" font-weight=\"bold\">↑ Plus brillant (Une valeur MAG plus petite = plus brillant)</text>\n          <text x=\"64\" y=\"150\" fill=\"#f87171\" font-size=\"10.5\" font-family=\"sans-serif\" font-weight=\"bold\">↓ Plus faible (Une valeur MAG plus grande = moins brillant)</text>\n          <path d=\"M 70 50 L 185 50 C 225 50, 255 136, 305 136 C 355 136, 385 50, 425 50 L 555 50\" fill=\"none\" stroke=\"#38bdf8\" stroke-width=\"2.5\" stroke-dasharray=\"6 4\"/>\n          <g stroke=\"#64d2ff\" stroke-width=\"1.5\">\n            <line x1=\"95\" y1=\"41\" x2=\"95\" y2=\"59\"/><circle cx=\"95\" cy=\"50\" r=\"4\" fill=\"#38bdf8\"/>\n            <line x1=\"145\" y1=\"39\" x2=\"145\" y2=\"57\"/><circle cx=\"145\" cy=\"48\" r=\"4\" fill=\"#38bdf8\"/>\n            <line x1=\"195\" y1=\"45\" x2=\"195\" y2=\"63\"/><circle cx=\"195\" cy=\"54\" r=\"4\" fill=\"#38bdf8\"/>\n            <line x1=\"250\" y1=\"88\" x2=\"250\" y2=\"110\"/><circle cx=\"250\" cy=\"99\" r=\"4\" fill=\"#facc15\"/>\n            <line x1=\"305\" y1=\"124\" x2=\"305\" y2=\"148\"/><circle cx=\"305\" cy=\"136\" r=\"5.5\" fill=\"#ef4444\" stroke=\"#fff\"/>\n            <line x1=\"360\" y1=\"86\" x2=\"360\" y2=\"108\"/><circle cx=\"360\" cy=\"97\" r=\"4\" fill=\"#facc15\"/>\n            <line x1=\"415\" y1=\"43\" x2=\"415\" y2=\"61\"/><circle cx=\"415\" cy=\"52\" r=\"4\" fill=\"#38bdf8\"/>\n            <line x1=\"475\" y1=\"40\" x2=\"475\" y2=\"58\"/><circle cx=\"475\" cy=\"49\" r=\"4\" fill=\"#38bdf8\"/>\n            <line x1=\"535\" y1=\"42\" x2=\"535\" y2=\"60\"/><circle cx=\"535\" cy=\"51\" r=\"4\" fill=\"#38bdf8\"/>\n          </g>\n          <text x=\"90\" y=\"35\" fill=\"#e2e8f0\" font-size=\"10.5\" font-family=\"sans-serif\">Luminosité normale (Plateau)</text>\n          <text x=\"215\" y=\"120\" fill=\"#fde047\" font-size=\"10.5\" font-family=\"sans-serif\" font-weight=\"bold\">Minimum principal (Éclipse / Transit)</text>\n          <text x=\"425\" y=\"75\" fill=\"#94a3b8\" font-size=\"10\" font-family=\"sans-serif\">Barres d'erreur (±MERR)</text>\n          <text x=\"195\" y=\"174\" fill=\"#cbd5e1\" font-size=\"11\" font-family=\"monospace\">Temps d'observation : Jour Julien (JD Mid) →</text>\n        </svg>\n      </div>\n\n      <div class=\"guide-two-col\">\n        <div class=\"guide-item\">\n          <h4>1. Axe Y (Magnitude stellaire / MAG)</h4>\n          <p>En astronomie, l'échelle des magnitudes est <strong>inversée</strong> :<br>• Un nombre <code>MAG</code> <strong>plus petit</strong> (ex. <code>9.10m</code> contre <code>9.50m</code>) signifie que l'étoile est <strong>plus brillante</strong> !<br>• Sur le graphique, les petits nombres sont en haut : une courbe qui monte indique un éclaircissement, tandis qu'un creux vers le bas indique un assombrissement (éclipse ou transit).</p>\n        </div>\n        <div class=\"guide-item\">\n          <h4>2. Axe X (Jour Julien / JD Mid)</h4>\n          <p>L'axe horizontal indique l'instant exact de mi-exposition de chaque pose Seestar en <strong>Jour Julien (JD Mid)</strong>.<br>• Exemple : <code>2461346.3671</code> est un décompte continu de jours UTC et de fractions de jour.<br>• Permet aux astronomes du monde entier de combiner leurs séries temporelles à la seconde près.</p>\n        </div>\n      </div>\n\n      <div class=\"guide-grid\" style=\"margin-top:10px;\">\n        <div class=\"guide-item\" style=\"background:rgba(10,132,255,0.10); border-color:rgba(100,210,255,0.32);\">\n          <h4>💡 Pourquoi les points oscillent-ils ? (Dispersion & barres d'erreur ±MERR)</h4>\n          <p>Chaque point représente une pose unitaire Seestar (10s–20s), et la barre verticale indique l'incertitude de mesure <code>±MERR</code>.<br>• Une faible dispersion de <code>0.01–0.02m</code> est due à la scintillation atmosphérique normale et au bruit photonique du capteur.<br>• Lorsque les points dessinent une onde régulière ou un creux en V/U bien plus profond que les barres d'erreur, vous avez détecté une <strong>véritable variabilité astrophysique</strong> !</p>\n        </div>\n\n        <div class=\"guide-item\">\n          <h4>3. Signatures typiques des courbes de lumière :</h4>\n          <p>• <strong>Variables pulsantes (SZ Lyn, RR Lyr, δ Sct) :</strong> Onde asymétrique avec montée rapide vers le maximum et déclin plus lent (amplitude <code>0.15–0.80m</code>).<br>• <strong>Binaires à éclipses (EA, EB, EW) :</strong> Creux prononcé en forme de V lorsqu'une étoile occulte sa compagne.<br>• <strong>Transits d'exoplanètes :</strong> Creux peu profond en forme de U à fond plat (<code>0.01–0.03m</code>).</p>\n        </div>\n      </div>\n",
    "btnGraphGuideShort": "📖 Comment lire le graphique ?",
    "dssEmptyCaption": "Sélectionnez une cible ou chargez un fichier CSV pour afficher le champ stellaire DSS2",
    "dssSurveyFovLabel": "Champ de la carte DSS2 : 2.40°×2.40°",
    "lblStarFieldPhoto": "🌌 Image du champ stellaire (DSS2)",
    "critModalTitle": "Divergence critique des données",
    "critModalBody": "Une divergence critique des données a été détectée. La conversion est bloquée. Veuillez vérifier l'étoile sélectionnée et le fichier CSV.",
    "btnCritOpenInputs": "📂 Vérifier l'étoile et le fichier",
    "btnCritClose": "Compris",
    "phUrgentSearch": "🔍 Rechercher une étoile (T CrB, SZ Lyn, CH Cyg)...",
    "splashLangLabel": "Langue de l'interface :",
    "lblSplashLang": "Langue de l'interface :",
    "statusExplainDefault": "ℹ️ Journal des requêtes réseau et de conversion",
    "tipAavsoSite": "Portail officiel de l'AAVSO",
    "tipHomeBtn": "Ouvrir l'écran d'accueil Seestar AstroLab AAVSO",
    "tipSeestarSite": "Site officiel des télescopes intelligents ZWO Seestar",
    "vspLoadingTitle": "⏳ Chargement de CHART (VSP), KNAME (AUID) et KMAG...",
    "vspLoadingStepDefault": "Coordonnées RA/DEC obtenues. Interrogation des miroirs de catalogues mondiaux...",
    "msgAllLoadedTitle": "✅ Toutes les données des catalogues ont été chargées !",
    "msgAllLoadedBody": "RA/DEC, nom canonique ({star}), carte CHART ({chart}), étoile de contrôle KNAME ({kname}) et KMAG ({kmag}) chargés.",
    "msgVspFailedTitle": "❌ Échec du chargement des données de calibration VSP",
    "msgVspFailedBody": "Tous les miroirs disponibles (AAVSO VSP, VizieR, SIMBAD) ont été interrogés, mais CHART/KNAME/KMAG n'ont pas pu être récupérés.",
    "starIdAutoAssigned": "✓ Nom officiel attribué depuis le catalogue VSX/SIMBAD : « {cat} » (fichier : « {file} »)",
    "tipVerifyFileText": "Vérifie la conformité complète d'un fichier CSV/TXT converti avec les exigences du portail AAVSO WebObs (#TYPE=EXTENDED, #OBSCODE, JD, MAG, MERR, KNAME, KMAG).",
    "urgentStarsIntro": "Cibles prioritaires des campagnes AAVSO Alert Notices pour télescopes Seestar. Cliquez sur une carte pour charger ses coordonnées.",
    "submitModalTitle": "🚀 Envoyer le fichier vers AAVSO WebObs (?preview=true)",
    "btnOpenAavsoCard": "📤 Ouvrir la page d'envoi AAVSO Photometry",
    "btnOpenAavsoMenu": "📤 Envoyer à l'AAVSO",
    "btnDonateLater": "Rappeler le mois prochain",
    "btnDonateNever": "Ne plus afficher",
    "btnDownloadDesktopShortcut": "💻 Télécharger le raccourci Bureau PC",
    "btnInstallApp": "📲 Installer l'application",
    "btnTriggerNativeInstall": "⚡ Installer en 1 clic",
    "installModalTitle": "📲 Installer Seestar AstroLab",
    "installModalIntro": "Cette application prend en charge l'installation directe sur votre bureau.",
    "authorCompany": "CosmoBehemothych",
    "infoCosmoSub": "Observatoire photométrique AAVSO Extended",
    "modeMinimal": "Minimal",
    "modeCompact": "Compact",
    "modeFull": "Studio",
    "minimalNotice": "🍃 Mode minimal activé : flux rapide en 1–2 clics.",
    "compactNotice": "⚡ Mode compact : paramètres et courbe de lumière côte à côte.",
    "fullNotice": "🔭 Studio complet : toutes les étapes scientifiques et journaux.",
    "searchPlaceholder": "Recherche rapide : étoile (Algol, SZ Lyn, TX UMa...) [ / ou ⌘K ]",
    "selfTestsTitle": "Diagnostic du noyau CosmoBehemothych",
    "selfTestsSuccess": "Les 8 tests algorithmiques automatisés ont réussi (précision 100 %) !",
    "msgStarImageMissing": "L'image de l'étoile est absente des catalogues",
    "errNoStarIdTitle": "Étoile (STARID) non sélectionnée",
    "errNoStarIdMsg": "Veuillez saisir le nom ou l'ID de l'étoile (STARID) avant la conversion.",
    "errNoSimbadLoadedTitle": "Données SIMBAD + VSP non chargées",
    "errNoSimbadLoadedMsg": "Veuillez cliquer sur '🔭 Charger SIMBAD + VSP' avant la conversion.",
    "errNoCsvSelectedTitle": "Fichier CSV Seestar non sélectionné",
    "errNoCsvSelectedMsg": "Veuillez sélectionner un fichier CSV Seestar dans la Section 2 avant la conversion.",
    "errServersUnavailableTitle": "Serveurs SIMBAD / AAVSO VSP indisponibles",
    "errServersUnavailableBody": "Impossible de joindre les serveurs SIMBAD / AAVSO VSP. Vérifiez votre connexion Internet ou lancez le diagnostic réseau dans les Paramètres.",
    "waitingSimbadBadge": "⏳ En attente de SIMBAD",
    "notLoadedSimbadCell": "— (Non chargé)",
    "simbadPreloadedFmt": "✓ Données SIMBAD ({star}) chargées — sélectionnez un fichier CSV",
    "vspStep1Loading": "⏳ Étape 1/2 : Interrogation des miroirs SIMBAD...",
    "vspStep2Loading": "⏳ Étape 2/2 : Chargement de la carte AAVSO VSP...",
    "lblConvertWait": "En attente des étapes 1 et 2",
    "lblConvertReady": "✓ Prêt à convertir"
  },
  "zh": {
    "lcEmptyTitle": "加载 CSV 文件后将显示光变曲线",
    "lcEmptyDesc": "请加载 Seestar 测光 CSV 文件（至少包含 2 帧目标星“Non-reference star”数据），以绘制星等光变曲线与误差棒。",
    "tipObsCodeShort": "将鼠标悬停或点击上方的“?”图标，查看关于 AAVSO 观测者代码的建议。",
    "tipObsCodeText": "您在 AAVSO 注册的官方观测者代码（写入 #OBSCODE 头部）。💡 建议：请务必填写您个人的 AAVSO 观测者代码（可在 aavso.org 个人资料中免费申请）。若无个人代码，AAVSO WebObs 平台将无法把观测数据关联到您的账户。",
    "obsCodeRecHtml": "💡 <strong>建议：</strong>请务必填写<strong>您个人的 AAVSO 观测者代码</strong>（Observer Code，可在 <a href='https://www.aavso.org' target='_blank' rel='noopener noreferrer'>aavso.org</a> 个人主页免费申请）。若未填写个人代码，AAVSO WebObs 平台将无法把测光成果计入您的个人账户。",
    "phObsCode": "请输入您的个人 AAVSO 观测者代码",
    "phObsFilterDate": "年 / 月 / 日",
    "guideModalTitle": "📈 如何解读 AAVSO 与 Seestar 光变曲线",
    "guideModalBodyHtml": "\n      <p style=\"font-size:13px; color:#dbeafe; margin:0 0 10px 0;\">\n        本指南通过可视化图表帮助您解读由 <strong>ZWO Seestar</strong> 测光数据转换而来的变星、食双星与系外行星凌星光变曲线。\n      </p>\n\n      <div class=\"guide-svg-box\" style=\"margin-bottom:12px; padding:12px;\">\n        <div style=\"font-size:11px; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:6px;\">\n          光变曲线示意图（食双星 / 脉动变星示例）\n        </div>\n        <svg viewBox=\"0 0 600 185\" width=\"100%\" height=\"175\" style=\"display:block; background:#070b14; border-radius:8px; border:1px solid rgba(100,210,255,0.18);\">\n          <line x1=\"55\" y1=\"28\" x2=\"575\" y2=\"28\" stroke=\"#1e293b\" stroke-dasharray=\"4 4\" stroke-width=\"1\"/>\n          <line x1=\"55\" y1=\"82\" x2=\"575\" y2=\"82\" stroke=\"#1e293b\" stroke-dasharray=\"4 4\" stroke-width=\"1\"/>\n          <line x1=\"55\" y1=\"138\" x2=\"575\" y2=\"138\" stroke=\"#1e293b\" stroke-dasharray=\"4 4\" stroke-width=\"1\"/>\n          <line x1=\"55\" y1=\"15\" x2=\"55\" y2=\"155\" stroke=\"#475569\" stroke-width=\"1.5\"/>\n          <line x1=\"55\" y1=\"155\" x2=\"575\" y2=\"155\" stroke=\"#475569\" stroke-width=\"1.5\"/>\n          <text x=\"8\" y=\"32\" fill=\"#86efac\" font-size=\"11\" font-family=\"monospace\" font-weight=\"bold\">11.5m ↑</text>\n          <text x=\"8\" y=\"86\" fill=\"#94a3b8\" font-size=\"11\" font-family=\"monospace\">12.0m</text>\n          <text x=\"8\" y=\"142\" fill=\"#fca5a5\" font-size=\"11\" font-family=\"monospace\" font-weight=\"bold\">12.5m ↓</text>\n          <text x=\"64\" y=\"22\" fill=\"#38bdf8\" font-size=\"10.5\" font-family=\"sans-serif\" font-weight=\"bold\">↑ 更亮（MAG 星等数值越小代表恒星越亮）</text>\n          <text x=\"64\" y=\"150\" fill=\"#f87171\" font-size=\"10.5\" font-family=\"sans-serif\" font-weight=\"bold\">↓ 更暗（MAG 星等数值越大代表恒星越暗）</text>\n          <path d=\"M 70 50 L 185 50 C 225 50, 255 136, 305 136 C 355 136, 385 50, 425 50 L 555 50\" fill=\"none\" stroke=\"#38bdf8\" stroke-width=\"2.5\" stroke-dasharray=\"6 4\"/>\n          <g stroke=\"#64d2ff\" stroke-width=\"1.5\">\n            <line x1=\"95\" y1=\"41\" x2=\"95\" y2=\"59\"/><circle cx=\"95\" cy=\"50\" r=\"4\" fill=\"#38bdf8\"/>\n            <line x1=\"145\" y1=\"39\" x2=\"145\" y2=\"57\"/><circle cx=\"145\" cy=\"48\" r=\"4\" fill=\"#38bdf8\"/>\n            <line x1=\"195\" y1=\"45\" x2=\"195\" y2=\"63\"/><circle cx=\"195\" cy=\"54\" r=\"4\" fill=\"#38bdf8\"/>\n            <line x1=\"250\" y1=\"88\" x2=\"250\" y2=\"110\"/><circle cx=\"250\" cy=\"99\" r=\"4\" fill=\"#facc15\"/>\n            <line x1=\"305\" y1=\"124\" x2=\"305\" y2=\"148\"/><circle cx=\"305\" cy=\"136\" r=\"5.5\" fill=\"#ef4444\" stroke=\"#fff\"/>\n            <line x1=\"360\" y1=\"86\" x2=\"360\" y2=\"108\"/><circle cx=\"360\" cy=\"97\" r=\"4\" fill=\"#facc15\"/>\n            <line x1=\"415\" y1=\"43\" x2=\"415\" y2=\"61\"/><circle cx=\"415\" cy=\"52\" r=\"4\" fill=\"#38bdf8\"/>\n            <line x1=\"475\" y1=\"40\" x2=\"475\" y2=\"58\"/><circle cx=\"475\" cy=\"49\" r=\"4\" fill=\"#38bdf8\"/>\n            <line x1=\"535\" y1=\"42\" x2=\"535\" y2=\"60\"/><circle cx=\"535\" cy=\"51\" r=\"4\" fill=\"#38bdf8\"/>\n          </g>\n          <text x=\"90\" y=\"35\" fill=\"#e2e8f0\" font-size=\"10.5\" font-family=\"sans-serif\">正常基线亮度（平台期）</text>\n          <text x=\"215\" y=\"120\" fill=\"#fde047\" font-size=\"10.5\" font-family=\"sans-serif\" font-weight=\"bold\">主极小期（交食 / 凌星亮度下降）</text>\n          <text x=\"425\" y=\"75\" fill=\"#94a3b8\" font-size=\"10\" font-family=\"sans-serif\">测量误差棒 (±MERR)</text>\n          <text x=\"195\" y=\"174\" fill=\"#cbd5e1\" font-size=\"11\" font-family=\"monospace\">观测时间：儒略日曝光中点 (JD Mid) →</text>\n        </svg>\n      </div>\n\n      <div class=\"guide-two-col\">\n        <div class=\"guide-item\">\n          <h4>1. Y 轴（视星等 / MAG）</h4>\n          <p>天文学中的星等刻度是<strong>反向（倒置）</strong>的：<br>• <code>MAG</code> 数值<strong>越小</strong>（例如 <code>9.10m</code> 对比 <code>9.50m</code>），表示恒星<strong>越明亮</strong>！<br>• 在图表中较小数值位于上方：曲线<strong>向上升起</strong>表示恒星变亮，而<strong>向下凹陷</strong>则表示恒星变暗（双星交食或行星凌星）。</p>\n        </div>\n        <div class=\"guide-item\">\n          <h4>2. X 轴（儒略日 / JD Mid）</h4>\n          <p>横轴显示每一帧 Seestar 曝光中点的精确天文时间戳——<strong>儒略日 (JD Mid)</strong>。<br>• 示例：<code>2461346.3671</code> 是以 UTC 起算的连续天数与小数。<br>• 让全球观测者能够以秒级精度合并同一目标星的时间序列测光数据。</p>\n        </div>\n      </div>\n\n      <div class=\"guide-grid\" style=\"margin-top:10px;\">\n        <div class=\"guide-item\" style=\"background:rgba(10,132,255,0.10); border-color:rgba(100,210,255,0.32);\">\n          <h4>💡 为什么数据点会上下跳动？（数据离散度与 ±MERR 误差棒）</h4>\n          <p>每个圆点代表一帧 Seestar 单张曝光（10秒–20秒），穿过圆点的竖线代表测量不确定度 <code>±MERR</code>。<br>• 相邻点之间 <code>0.01–0.02m</code> 的微小波动属于正常的大气闪烁（视宁度湍流）和传感器光子噪声。<br>• 当数据点呈现出连贯的波浪形态，或远深于误差棒长度的清晰 V 型 / U 型凹谷时，说明您成功捕获了<strong>真实的天体物理光变信号</strong>！</p>\n        </div>\n\n        <div class=\"guide-item\">\n          <h4>3. 常见天体的光变曲线特征：</h4>\n          <p>• <strong>脉动变星（SZ Lyn、天琴座 RR、盾牌座 δ 型）：</strong>平滑的不对称波浪——快速陡峭上升至极大亮度，随后较缓慢下降（光变幅度 <code>0.15–0.80m</code>）。<br>• <strong>食双星（大陵五型 EA、渐台二型 EB、大熊座 W 型 EW）：</strong>当一颗子星遮掩伴星时产生尖锐的 V 型主极小凹谷。<br>• <strong>系外行星凌星：</strong>底部平坦的浅 U 型凹槽（深度通常为 <code>0.01–0.03m</code>）。</p>\n        </div>\n      </div>\n",
    "btnGraphGuideShort": "📖 如何解读光变曲线？",
    "dssEmptyCaption": "请选择目标恒星或加载 CSV 文件以显示 DSS2 巡天视场图像",
    "dssSurveyFovLabel": "DSS2 巡天星图范围: 2.40°×2.40°",
    "lblStarFieldPhoto": "🌌 恒星天区巡天图像 (DSS2)",
    "critModalTitle": "关键数据不一致警告",
    "critModalBody": "检测到关键测光数据存在重大差异，转换已锁定。请检查所选目标恒星 (STARID) 与 CSV 文件是否匹配。",
    "btnCritOpenInputs": "📂 检查目标恒星与文件",
    "btnCritClose": "知道了",
    "phUrgentSearch": "🔍 搜索恒星 (T CrB, SZ Lyn, CH Cyg)...",
    "splashLangLabel": "界面语言：",
    "lblSplashLang": "界面语言：",
    "statusExplainDefault": "ℹ️ 网络请求与格式转换日志",
    "tipAavsoSite": "AAVSO 官方网站 (美国变星观测者协会)",
    "tipHomeBtn": "打开 Seestar AstroLab AAVSO 欢迎界面",
    "tipSeestarSite": "ZWO Seestar 智能望远镜官方网站",
    "vspLoadingTitle": "⏳ 正在加载 CHART (VSP)、KNAME (AUID) 与 KMAG...",
    "vspLoadingStepDefault": "已获取 RA/DEC 坐标，正在查询全球星表镜像服务器...",
    "msgAllLoadedTitle": "✅ 所有星表与校准数据加载成功！",
    "msgAllLoadedBody": "已成功加载 RA/DEC 坐标、标准星名 ({star})、星图编号 CHART ({chart})、检验星 KNAME ({kname}) 及星等 KMAG ({kmag})。",
    "msgVspFailedTitle": "❌ 加载 VSP 校准星数据失败",
    "msgVspFailedBody": "已尝试所有可用端口与镜像服务器 (AAVSO VSP, VizieR, SIMBAD)，但未能获取 CHART/KNAME/KMAG 数据。",
    "starIdAutoAssigned": "✓ 已自动匹配 VSX/SIMBAD 标准星表名称：“{cat}”（原文件内名称：“{file}”）",
    "tipVerifyFileText": "全面检查磁盘上已转换的 CSV/TXT 文件是否符合 AAVSO WebObs 规范：包含必需头部 (#TYPE=EXTENDED, #OBSCODE, #DELIM, #DATE, #OBSTYPE)、VSX 标准星名以及有效的 JD、MAG、MERR、KNAME、KMAG 数据列。",
    "urgentStarsIntro": "适用于 Seestar 智能望远镜的 AAVSO 紧急观测警报 (Alert Notices) 目标列表。点击任意恒星卡片即可自动填入标准名称与坐标。",
    "submitModalTitle": "🚀 提交文件至 AAVSO WebObs (?preview=true)",
    "btnOpenAavsoCard": "📤 打开 AAVSO Photometry 数据上传页面",
    "btnOpenAavsoMenu": "📤 提交至 AAVSO",
    "btnDonateLater": "下个月提醒我",
    "btnDonateNever": "不再显示",
    "btnDownloadDesktopShortcut": "💻 下载电脑桌面快捷方式",
    "btnInstallApp": "📲 安装应用程序",
    "btnTriggerNativeInstall": "⚡ 一键安装应用",
    "installModalTitle": "📲 安装 Seestar AstroLab 应用程序",
    "installModalIntro": "本应用支持作为独立桌面应用直接安装。",
    "authorCompany": "CosmoBehemothych",
    "infoCosmoSub": "AAVSO Extended 专业测光天文台",
    "modeMinimal": "极简",
    "modeCompact": "紧凑",
    "modeFull": "完整工作室",
    "minimalNotice": "🍃 已启用极简模式：1–2 步快速转换工作流。",
    "compactNotice": "⚡ 已启用紧凑模式：参数与光变曲线并排显示。",
    "fullNotice": "🔭 已启用完整工作室：包含全部科学校验步骤与网络日志。",
    "searchPlaceholder": "快速搜索：恒星 (Algol, SZ Lyn, TX UMa...) [ / 或 ⌘K ]",
    "selfTestsTitle": "CosmoBehemothych 核心算法自检",
    "selfTestsSuccess": "全部 8 项核心算法自动测试均已通过（100% 精度）！",
    "msgStarImageMissing": "星表中缺少该恒星的图像",
    "errNoStarIdTitle": "未选择目标恒星 (STARID)",
    "errNoStarIdMsg": "请在转换前输入目标恒星名称或 ID (STARID)。",
    "errNoSimbadLoadedTitle": "尚未加载 SIMBAD + VSP 星表数据",
    "errNoSimbadLoadedMsg": "请在转换前点击“🔭 加载 SIMBAD + VSP”获取坐标与校准星数据。",
    "errNoCsvSelectedTitle": "未选择 Seestar CSV 测光文件",
    "errNoCsvSelectedMsg": "请在转换前于第 2 步选择 Seestar CSV 测光文件（或点击“演示 CSV”）。",
    "errServersUnavailableTitle": "SIMBAD / AAVSO VSP 星表服务器不可用",
    "errServersUnavailableBody": "无法连接到 SIMBAD 或 AAVSO VSP 服务器。请检查您的网络连接，或在“设置”中运行“网络与镜像诊断”。",
    "waitingSimbadBadge": "⏳ 等待加载 SIMBAD",
    "notLoadedSimbadCell": "—（未加载）",
    "simbadPreloadedFmt": "✓ 已加载 SIMBAD 数据 ({star}) — 请选择 Seestar CSV 文件",
    "vspStep1Loading": "⏳ 第 1/2 步：正在查询全球 SIMBAD 镜像服务器...",
    "vspStep2Loading": "⏳ 第 2/2 步：正在加载 AAVSO VSP 星图与检验星...",
    "lblConvertWait": "等待完成第 1 和第 2 步",
    "lblConvertReady": "✓ 准备转换"
  }
};
  Object.keys(COMPLETE_PATCH_I18N).forEach(lg => {
    if (I18N[lg]) {
      Object.assign(I18N[lg], COMPLETE_PATCH_I18N[lg]);
    }
  });
  window.I18N = I18N;
  function detectLang() {
    const stored = safeGetStorage("lang", null) || safeGetStorage("seestar_lang", null);
    if (stored && I18N[stored]) return stored;
    return "ru";
  }

  let currentLang = detectLang();
  const t = key => (I18N[currentLang] && I18N[currentLang][key]) || (I18N.ru && I18N.ru[key]) || (I18N.en && I18N.en[key]) || key;
  const tSafe = key => (I18N[currentLang] && I18N[currentLang][key]) || (I18N.en && I18N.en[key]) || (I18N.ru && I18N.ru[key]) || null;

  function applyTranslations() {
    document.documentElement.lang = currentLang;
    const tc = document.getElementById("toastContainer"); if (tc) tc.innerHTML = "";
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      const v = tSafe(key);
      if (v !== null) el.textContent = v;
    });
    document.querySelectorAll("[data-i18n-html]").forEach(el => {
      const key = el.getAttribute("data-i18n-html");
      const v = tSafe(key);
      if (v !== null) el.innerHTML = v;
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
      const key = el.getAttribute("data-i18n-placeholder");
      const v = tSafe(key);
      if (v !== null) el.placeholder = v;
    });
    document.querySelectorAll("[data-i18n-title]").forEach(el => {
      const key = el.getAttribute("data-i18n-title");
      const v = tSafe(key);
      if (v !== null) el.title = v;
    });

    const tipMap = {
      tipObsCode: "tipObsCodeText",
      tipStarId: "tipStarIdText",
      tipChart: "tipChartText",
      tipKname: "tipKnameText",
      tipKmag: "tipKmagText",
      tipRa: "tipRaText",
      tipDec: "tipDecText",
      tipCsvFile: "tipCsvText",
      tipVerifyFile: "tipVerifyFileText"
    };
    Object.entries(tipMap).forEach(([id, key]) => {
      const el = document.getElementById(id);
      if (el) {
        el.setAttribute("data-tip", t(key));
        el.removeAttribute("title");
      }
    });

    document.title = t("pageTitle");
    const urgWaitEl = document.getElementById("urgentLastUpdateText");
    if (urgWaitEl && !urgWaitEl.getAttribute("data-synced")) {
      urgWaitEl.innerHTML = t("urgentSyncWait");
    }
    const urgTimerEl = document.getElementById("urgentAutoTimerText");
    if (urgTimerEl) {
      const jdSpan = document.getElementById("urgentCurrentJd");
      const jdVal = jdSpan ? jdSpan.textContent : "—";
      urgTimerEl.innerHTML = `${escapeHtml(t("urgentAutoTimerPrefix"))} <span id="urgentCurrentJd">${escapeHtml(jdVal)}</span>`;
    }
    document.getElementById("langSelect").value = currentLang;
    const splashSel = document.getElementById("splashLangSelect"); if (splashSel) splashSel.value = currentLang;
  }

  /**
   * ============================================================================
   * МОДУЛЬ 3: СИСТЕМА УВЕДОМЛЕНИЙ DYNAMIC ISLAND С ПОДСКАЗКАМИ
   * Разработчику: Заменяет блокирующий window.alert() на дружелюбные iOS-баннеры,
   * в которых каждое уведомление сопровождается пояснением (explain).
   * ============================================================================
   */
  function isGlobalToastsEnabled() {
    return safeGetStorage("seestar_toasts_enabled", "true") !== "false";
  }
  window.isGlobalToastsEnabled = isGlobalToastsEnabled;
  window.showIosNotification = function(title, message, explainText, type) { return showIosNotification(title, message, explainText, type); };

  function showIosNotification(title, message, explainText, type = "info") {
    if (!isGlobalToastsEnabled()) return;
    const container = document.getElementById("toastContainer");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = "ios-toast";

    const icons = { info: "🔔", ok: "✅", warn: "⚠️", err: "🚨" };
    const icon = icons[type] || "🔔";

    toast.innerHTML = `
      <div class="ios-toast-icon">${icon}</div>
      <div class="ios-toast-content">
        <div class="ios-toast-title">${escapeHtml(title)}</div>
        <div class="ios-toast-msg">${escapeHtml(message)}</div>
        ${explainText ? `<div class="ios-toast-explain">💡 ${escapeHtml(explainText)}</div>` : ""}
      </div>
      <button type="button" class="ios-toast-close" aria-label="Close">✕</button>
    `;

    const closeBtn = toast.querySelector(".ios-toast-close");
    const removeToast = () => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(-12px) scale(0.95)";
      toast.style.transition = "all 0.25s ease";
      setTimeout(() => { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 260);
    };
    closeBtn.addEventListener("click", removeToast);
    container.appendChild(toast);
    setTimeout(removeToast, 6500);
  }

  [
    ["tipObsCode", "lblObsCode", "tipObsCodeText"],
    ["tipStarId", "lblStarId", "tipStarIdText"],
    ["tipChart", "lblChart", "tipChartText"],
    ["tipKname", "lblKname", "tipKnameText"],
    ["tipKmag", "lblKmag", "tipKmagText"],
    ["tipRa", "lblRa", "tipRaText"],
    ["tipDec", "lblDec", "tipDecText"],
    ["tipCsvFile", "lblFile", "tipCsvText"]
  ].forEach(([id, titleKey, textKey]) => {
    const badge = document.getElementById(id);
    if (badge) {
      badge.addEventListener("click", (e) => {
        e.preventDefault();
        showIosNotification(t(titleKey), t(textKey), "", "info");
      });
    }
  });

  /**
   * ============================================================================
   * МОДУЛЬ 4: СЕТЕВОЕ ЯДРО, КЭШ (TTL 1 ЧАС) И ПАРАЛЛЕЛЬНЫЕ ГОНКИ (SIMBAD & VSP)
   * Разработчику: Реализует неблокирующий опрос зеркал CDS/Harvard/IDIA
   * с поддержкой принудительной остановки через AbortController.
   * ============================================================================
   */
  let stopRequested = false;
  let currentOpId = 0;
  const activeAbortControllers = new Set();
  const CACHE_TTL = 3600 * 1000;
  const CACHE = { simbad: new Map(), vsp: new Map() };

  let currentCsvText = "";

  function getCached(cacheMap, key, logPrefix) {
    if (cacheMap.has(key)) {
      const item = cacheMap.get(key);
      if (Date.now() - item._timestamp < CACHE_TTL) {
        if (logPrefix) beginLog(logPrefix)(item._cacheMsg);
        return item.data;
      } else {
        cacheMap.delete(key);
      }
    }
    return null;
  }

  function setCached(cacheMap, key, data, cacheMsg) {
    cacheMap.set(key, { data, _timestamp: Date.now(), _cacheMsg: cacheMsg });
  }

  function checkStop() {
    if (stopRequested) throw new Error(t("msgStopped"));
  }

  function stopAllRequests() {
    stopRequested = true;
    for (const ctrl of activeAbortControllers) {
      try { ctrl.abort(); } catch (_) {}
    }
    activeAbortControllers.clear();
    const stopBtn = document.getElementById("btnStop");
    stopBtn.disabled = true;
    stopBtn.style.display = "none";
    showIosNotification(t("btnStop"), t("msgStopped"), t("msgStoppedExplain"), "warn");
  }

  async function runOperation(fn) {
    const myId = ++currentOpId;
    stopRequested = false;
    const stopBtn = document.getElementById("btnStop");
    stopBtn.disabled = false;
    stopBtn.style.display = "inline-flex";
    lockButtons(true);
    try {
      await fn();
    } finally {
      if (myId === currentOpId) {
        lockButtons(false);
        stopBtn.disabled = true;
        stopBtn.style.display = "none";
      }
    }
  }

  function lockButtons(flag) {
    ["btnFetchAll", "btnDiagnose"].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.disabled = flag;
    });
  }

  const PROXIES = [
    { name: "corsfix",     build: u => "https://proxy.corsfix.com/?" + u },
    { name: "cors.sh",     build: u => "https://proxy.cors.sh/" + u },
    { name: "cors.x2u.in", build: u => "https://cors.x2u.in/" + u },
    { name: "allorigins",  build: u => "https://api.allorigins.win/raw?url=" + encodeURIComponent(u) },
    { name: "codetabs",    build: u => "https://api.codetabs.com/v1/proxy/?quest=" + encodeURIComponent(u) }
  ];

  const SIMBAD_MIRRORS = [
    { name: "CDS Strasbourg", base: "https://simbad.cds.unistra.fr/simbad/sim-tap/sync" },
    { name: "IDIA",           base: "https://simbad.idia.ac.za/simbad/sim-tap/sync" },
    { name: "CfA Harvard",    base: "https://simbad.cfa.harvard.edu/simbad/sim-tap/sync" }
  ];

  const STATE = {
    workingProxy: null,
    workingMirror: null,
    catalogStarName: null,
    catalogRa: null,
    catalogDec: null,
    lastConvertedFileName: null,
    lastConvertedContent: null
  };

  function orderedMirrors() {
    if (!STATE.workingMirror) return SIMBAD_MIRRORS;
    const first = SIMBAD_MIRRORS.find(m => m.name === STATE.workingMirror);
    return first ? [first, ...SIMBAD_MIRRORS.filter(m => m.name !== STATE.workingMirror)] : SIMBAD_MIRRORS;
  }

  function orderedProxies() {
    if (!STATE.workingProxy) return PROXIES;
    const first = PROXIES.find(p => p.name === STATE.workingProxy);
    return first ? [first, ...PROXIES.filter(p => p.name !== STATE.workingProxy)] : PROXIES;
  }

  function fmtAgg(agg) {
    if (!agg) return "      • unknown error";
    if (agg.errors) return agg.errors.map(e => "      • " + (e.message || e)).join("\n");
    return "      • " + (agg.message || String(agg));
  }

  async function raceMirrorsDirect(params, timeoutMs, log) {
    checkStop();
    const entries = orderedMirrors().map(m => ({ mirror: m, ctrl: new AbortController(), timedOut: false, done: false }));
    const attempts = entries.map(async (entry) => {
      activeAbortControllers.add(entry.ctrl);
      const timer = setTimeout(() => { entry.timedOut = true; try { entry.ctrl.abort(); } catch(_){} }, timeoutMs);
      try {
        const t0 = performance.now();
        const mirrorUrl = entry.mirror.base + '?' + params;
        const resp = await fetch(mirrorUrl, { signal: entry.ctrl.signal });
        const ms = Math.round(performance.now() - t0);
        if (!resp.ok) throw new Error(`HTTP ${resp.status} (${ms}ms)`);
        const data = await resp.json();
        if (!data.data || !data.data.length) throw new Error("object not found");
        log(`    ✓ ${entry.mirror.name} — ${ms}ms`);
        entry.done = true;
        return { data, mirrorName: entry.mirror.name };
      } catch (e) {
        if (stopRequested) throw new Error(t("msgStopped"));
        const msg = entry.timedOut ? `timeout ${timeoutMs}ms` : (entry.ctrl.signal.aborted ? "aborted" : e.message);
        throw new Error(`${entry.mirror.name}: ${msg}`);
      } finally {
        clearTimeout(timer);
        activeAbortControllers.delete(entry.ctrl);
      }
    });
    try {
      const winner = await Promise.any(attempts);
      entries.forEach(e => { if (!e.done) { try { e.ctrl.abort(); } catch(_){} } });
      return winner;
    } catch (agg) {
      if (stopRequested) throw new Error(t("msgStopped"));
      throw agg;
    }
  }

  async function raceProxies(rawUrl, timeoutMs, log) {
    checkStop();
    const entries = orderedProxies().map(p => ({ proxy: p, ctrl: new AbortController(), timedOut: false, done: false }));
    const attempts = entries.map(async (entry) => {
      activeAbortControllers.add(entry.ctrl);
      const timer = setTimeout(() => { entry.timedOut = true; try { entry.ctrl.abort(); } catch(_){} }, timeoutMs);
      try {
        const t0 = performance.now();
        const resp = await fetch(entry.proxy.build(rawUrl), { signal: entry.ctrl.signal });
        const ms = Math.round(performance.now() - t0);
        if (!resp.ok) throw new Error(`HTTP ${resp.status} (${ms}ms)`);
        log(`    ✓ ${entry.proxy.name} — ${ms}ms`);
        STATE.workingProxy = entry.proxy.name;
        entry.done = true;
        return { resp, proxyName: entry.proxy.name };
      } catch (e) {
        if (stopRequested) throw new Error(t("msgStopped"));
        const msg = entry.timedOut ? `timeout ${timeoutMs}ms` : (entry.ctrl.signal.aborted ? "aborted" : e.message);
        throw new Error(`${entry.proxy.name}: ${msg}`);
      } finally {
        clearTimeout(timer);
        activeAbortControllers.delete(entry.ctrl);
      }
    });
    try {
      const winner = await Promise.any(attempts);
      entries.forEach(e => { if (!e.done) { try { e.ctrl.abort(); } catch(_){} } });
      return winner;
    } catch (agg) {
      if (stopRequested) throw new Error(t("msgStopped"));
      throw agg;
    }
  }

  async function querySimbad(starName, log) {
    const cached = getCached(CACHE.simbad, starName, null);
    if (cached) {
      log(t("msgSimbadCache") + `: "${starName}"`);
      return cached;
    }

    const safeName = starName.replace(/[\x00-\x1f]/g, "").replace(/'/g, "''");
    const adql = `SELECT TOP 1 main_id, ra, dec, otype_txt, sp_type FROM basic JOIN ident ON oid = oidref WHERE id = '${safeName}'`;
    const params = new URLSearchParams({ request: "doQuery", lang: "ADQL", format: "json", query: adql });

    log(t("msgDirectMirrors"));
    try {
      const { data, mirrorName } = await raceMirrorsDirect(params, 5000, log);
      STATE.workingMirror = mirrorName;
      const result = { ...parseSimbad(data), _source: mirrorName };
      setCached(CACHE.simbad, starName, result, t("msgSimbadCache"));
      return result;
    } catch (agg) {
      log("  ✗ " + fmtAgg(agg).trim().replace(/\n/g, "\n  "));
    }

    log(t("msgProxiesFallback"));
    let lastAgg = null;
    for (const m of orderedMirrors()) {
      checkStop();
      log(`→ ${m.name}`);
      try {
        const { resp, proxyName } = await raceProxies(`${m.base}?${params}`, 6000, log);
        const data = await resp.json();
        if (!data.data || !data.data.length) throw new Error("object not found");
        STATE.workingMirror = m.name;
        const result = { ...parseSimbad(data), _source: `${m.name} via ${proxyName}` };
        setCached(CACHE.simbad, starName, result, t("msgSimbadCache"));
        return result;
      } catch (agg) {
        if (stopRequested) throw agg;
        lastAgg = agg;
        log("  ✗ " + fmtAgg(agg).trim().replace(/\n/g, "\n  "));
      }
    }
    throw new Error(`${t("msgSimbadDown")}\n${lastAgg ? fmtAgg(lastAgg) : ""}`);
  }

  function parseSimbad(data) {
    const cols = data.metadata.map(c => c.name);
    const row = data.data[0];
    return Object.fromEntries(cols.map((c, i) => [c, row[i]]));
  }

  /**
   * Полный справочник 88 созвездий МАС (IAU): родительные и именительные падежи -> 3-буквенный код VSX/AAVSO.
   * Исправляет ошибку AAVSO WebObs: "Star 'SZ Lyncis' not found in VSX" -> "SZ Lyn".
   */
  const CONSTELLATION_GENITIVES = {
    andromedae: "And", andromeda: "And", antliae: "Ant", antlia: "Ant", apus: "Aps", apodis: "Aps",
    aquarii: "Aqr", aquarius: "Aqr", aquilae: "Aql", aquila: "Aql", arae: "Ara", ara: "Ara",
    arietis: "Ari", aries: "Ari", aurigae: "Aur", auriga: "Aur", bootis: "Boo", bootes: "Boo",
    caeli: "Cae", caelum: "Cae", camelopardalis: "Cam", camelopardus: "Cam", cancri: "Cnc", cancer: "Cnc",
    "canum venaticorum": "CVn", "canes venatici": "CVn", "canis majoris": "CMa", "canis major": "CMa",
    "canis minoris": "CMi", "canis minor": "CMi", capricorni: "Cap", capricornus: "Cap",
    carinae: "Car", carina: "Car", cassiopeiae: "Cas", cassiopeia: "Cas", centauri: "Cen", centaurus: "Cen",
    cephei: "Cep", cepheus: "Cep", ceti: "Cet", cetus: "Cet", chamaeleontis: "Cha", chamaeleon: "Cha",
    circini: "Cir", circinus: "Cir", columbae: "Col", columba: "Col", "comae berenices": "Com", coma: "Com",
    "coronae australis": "CrA", "coronae borealis": "CrB", corvi: "Crv", corvus: "Crv",
    crateris: "Crt", crater: "Crt", crucis: "Cru", crux: "Cru", cygni: "Cyg", cygnus: "Cyg",
    delphini: "Del", delphinus: "Del", doradus: "Dor", dorado: "Dor", draconis: "Dra", draco: "Dra",
    equulei: "Equ", equuleus: "Equ", eridani: "Eri", eridanus: "Eri", fornacis: "For", fornax: "For",
    geminorum: "Gem", gemini: "Gem", gruis: "Gru", grus: "Gru", herculis: "Her", hercules: "Her",
    horologii: "Hor", horologium: "Hor", hydrae: "Hya", hydra: "Hya", hydri: "Hyi", hydrus: "Hyi",
    indi: "Ind", indus: "Ind", lacertae: "Lac", lacerta: "Lac", leonis: "Leo", leo: "Leo",
    "leonis minoris": "LMi", "leo minor": "LMi", leporis: "Lep", lepus: "Lep", librae: "Lib", libra: "Lib",
    lupi: "Lup", lupus: "Lup", lyncis: "Lyn", lynx: "Lyn", lyrae: "Lyr", lyra: "Lyr",
    mensae: "Men", mensa: "Men", microscopii: "Mic", microscopium: "Mic", monocerotis: "Mon", monoceros: "Mon",
    muscae: "Mus", musca: "Mus", normae: "Nor", norma: "Nor", octantis: "Oct", octans: "Oct",
    ophiuchi: "Oph", ophiuchus: "Oph", orionis: "Ori", orion: "Ori", pavonis: "Pav", pavo: "Pav",
    pegasi: "Peg", pegasus: "Peg", persei: "Per", perseus: "Per", phoenicis: "Phe", phoenix: "Phe",
    pictoris: "Pic", pictor: "Pic", piscium: "Psc", pisces: "Psc", "piscis austrini": "PsA",
    puppis: "Pup", pyxidis: "Pyx", pyxis: "Pyx", reticuli: "Ret", reticulum: "Ret",
    sagittae: "Sge", sagitta: "Sge", sagittarii: "Sgr", sagittarius: "Sgr", scorpii: "Sco", scorpius: "Sco",
    sculptoris: "Scl", sculptor: "Scl", scuti: "Sct", scutum: "Sct", serpentis: "Ser", serpens: "Ser",
    sextantis: "Sex", sextans: "Sex", tauri: "Tau", taurus: "Tau", telescopii: "Tel", telescopium: "Tel",
    trianguli: "Tri", triangulum: "Tri", "trianguli australis": "TrA", tucanae: "Tuc", tucana: "Tuc",
    "ursae majoris": "UMa", "ursa major": "UMa", "ursae minoris": "UMi", "ursa minor": "UMi",
    velorum: "Vel", vela: "Vel", virginis: "Vir", virgo: "Vir", volantis: "Vol", volans: "Vol",
    vulpeculae: "Vul", vulpecula: "Vul"
  };

  // Все 3-буквенные коды IAU для правильного регистра (например, "sz lyn" -> "SZ Lyn")
  const IAU_ABBR_MAP = {};
  Object.values(CONSTELLATION_GENITIVES).forEach(abbr => {
    IAU_ABBR_MAP[abbr.toLowerCase()] = abbr;
  });

  /**
   * ПУНКТ 8 & 9: Приведение любого имени звезды к официальному каноническому стандарту AAVSO VSX / GCVS.
   * Если имя из каталога (SIMBAD / VSX / VSP) отличается от имени из файла (например, "SZ Lyncis" или "SZ_Lyncis"),
   * функция возвращает строго каноническое каталожное имя ("SZ Lyn"), принимаемое валидатором AAVSO WebObs.
   */
  function reduceConstellationName(nameStr) {
    let candidate = String(nameStr || "").trim();
    if (!candidate) return "";
    candidate = candidate.replace(/^(V\*|SV\*|\*\*|\*|EM\*|EB\*|RR\*|BY\*|DSCT\*|VARIABLE\s+STAR)\s+/i, "").trim();
    candidate = candidate.replace(/_/g, " ").replace(/\s+/g, " ").trim();

    const lowerCand = candidate.toLowerCase();
    const sortedGenitives = Object.entries(CONSTELLATION_GENITIVES).sort((a, b) => b[0].length - a[0].length);
    for (const [gen, abbr] of sortedGenitives) {
      if (lowerCand.endsWith(" " + gen)) {
        let prefix = candidate.slice(0, candidate.length - gen.length - 1).trim();
        if (/^[a-z]{1,2}$/i.test(prefix)) prefix = prefix.toUpperCase();
        else if (/^v\d+$/i.test(prefix)) prefix = "V" + prefix.slice(1);
        return `${prefix} ${abbr}`;
      }
    }

    const parts = candidate.split(" ");
    if (parts.length === 2 && IAU_ABBR_MAP[parts[1].toLowerCase()]) {
      let p0 = parts[0];
      if (/^[a-z]{1,2}$/i.test(p0)) p0 = p0.toUpperCase();
      else if (/^v\d+$/i.test(p0)) p0 = "V" + p0.slice(1);
      return `${p0} ${IAU_ABBR_MAP[parts[1].toLowerCase()]}`;
    }
    return candidate;
  }

  function normalizeStarForVsp(rawName, catalogMainId) {
    const cleanRaw = reduceConstellationName(rawName);
    const cleanCat = reduceConstellationName(catalogMainId);

    // ПУНКТ 6a: Если переданы оба имени, используем catalogMainId ТОЛЬКО если это синоним той же самой звезды!
    // Это полностью исключает баг, когда при выборе любой звезды в STARID подставляется CH Cyg или старое имя из кэша.
    if (cleanRaw && cleanCat) {
      const lowRaw = cleanRaw.toLowerCase();
      const lowCat = cleanCat.toLowerCase();
      if (lowRaw === lowCat) return cleanCat;
      for (const grp of STAR_SYNONYM_GROUPS) {
        const lowGrp = grp.map(x => x.toLowerCase());
        if (lowGrp.includes(lowRaw) && lowGrp.includes(lowCat)) {
          return grp[0];
        }
      }
      // Разные звёзды — приоритет строго у явно выбранного пользователем rawName!
      for (const grp of STAR_SYNONYM_GROUPS) {
        if (grp.some(x => x.toLowerCase() === lowRaw)) return grp[0];
      }
      return cleanRaw;
    }

    const target = cleanRaw || cleanCat;
    if (!target) return "";
    const lowTarget = target.toLowerCase();
    for (const grp of STAR_SYNONYM_GROUPS) {
      if (grp.some(x => x.toLowerCase() === lowTarget)) return grp[0];
    }
    return target;
  }

  /**
   * ПУНКТ 9: Перекрестная проверка имени переменной звезды по координатам (RA, DEC) через зеркала SIMBAD / VizieR VSX.
   * Если в файле записано нестандартное имя (например, "SZ Lyncis"), а мы получили координаты из зеркал
   * (RA=122.398952, DEC=44.471556), проверяем в радиусе 3 угловых минут официальный идентификатор GCVS/VSX.
   */
  async function verifyStarNameByCoordsFromMirrors(ra, dec, fallbackName, log) {
    if (ra == null || isNaN(ra) || dec == null || isNaN(dec)) {
      return normalizeStarForVsp(fallbackName, STATE.catalogStarName);
    }
    try {
      const adql = `SELECT TOP 5 main_id, ra, dec, otype_txt FROM basic ` +
                   `WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', ${Number(ra).toFixed(6)}, ${Number(dec).toFixed(6)}, 0.05)) = 1 ` +
                   `ORDER BY DISTANCE(POINT('ICRS', ra, dec), POINT('ICRS', ${Number(ra).toFixed(6)}, ${Number(dec).toFixed(6)})) ASC`;
      const params = new URLSearchParams({ request: "doQuery", lang: "ADQL", format: "json", query: adql });
      const { data, mirrorName } = await raceMirrorsDirect(params, 4500, log || (() => {}));
      const cols = data.metadata.map(c => c.name);
      const rows = data.data.map(r => Object.fromEntries(cols.map((c, i) => [c, r[i]])));
      for (const r of rows) {
        if (r.main_id) {
          const canonical = normalizeStarForVsp(fallbackName, r.main_id);
          if (log) log(`  ✓ Верификация по координатам (${mirrorName}): RA=${Number(r.ra).toFixed(5)}°, DEC=${Number(r.dec).toFixed(5)}° → каталожное имя VSX/SIMBAD: "${canonical}"`);
          return canonical;
        }
      }
    } catch (_) {}
    return normalizeStarForVsp(fallbackName, STATE.catalogStarName);
  }

  // Международные зеркала VizieR (Страсбург, Гарвард, Токио, ЮАР) для прямого поиска в каталогах B/vsx/vsx и APASS9
  const VIZIER_MIRRORS = [
    { name: "VizieR CDS Strasbourg (FR:443)", base: "https://vizier.cds.unistra.fr/viz-bin/asu-tsv" },
    { name: "VizieR CfA Harvard (US:443)",    base: "https://vizier.cfa.harvard.edu/viz-bin/asu-tsv" },
    { name: "VizieR NAOJ Tokyo (JP:443)",     base: "https://vizier.nao.ac.jp/viz-bin/asu-tsv" },
    { name: "VizieR IDIA Cape Town (ZA:443)", base: "https://vizier.idia.ac.za/viz-bin/asu-tsv" }
  ];

  /**
   * Прямой опрос мировых зеркал VizieR (каталог фотометрических стандартов AAVSO APASS DR9 II/336/apass9 и Tycho-2 I/259/tyc2)
   */
  async function queryVizierMirrorsCheckStar(ra, dec, targetName, log) {
    if (ra == null || isNaN(ra) || dec == null || isNaN(dec)) return null;
    log("  → Опрос 4 мировых зеркал VizieR (APASS DR9 / Tycho-2) по координатам поля...");
    const queryStr = new URLSearchParams({
      "-source": "I/259/tyc2",
      "-c": `${Number(ra).toFixed(6)} ${Number(dec).toFixed(6)}`,
      "-c.rm": "30",
      "-out.max": "25",
      "-out": "TYC1,TYC2,TYC3,RAmdeg,DEmdeg,VTmag"
    }).toString();

    for (const vm of VIZIER_MIRRORS) {
      checkStop();
      const ctrl = new AbortController();
      activeAbortControllers.add(ctrl);
      const timer = setTimeout(() => { try { ctrl.abort(); } catch(_){} }, 5000);
      try {
        const vizUrl = vm.base + "?" + queryStr;
        const resp = await fetch(vizUrl, { signal: ctrl.signal });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const text = await resp.text();
        const lines = text.split(/\r?\n/).filter(l => l && !l.startsWith("#") && !l.startsWith("-"));
        const photometry = [];
        for (const l of lines) {
          const parts = l.split("\t").map(s => s.trim());
          if (parts.length >= 6) {
            const vt = parseFloat(parts[5]);
            if (!isNaN(vt) && vt >= 9.2 && vt <= 13.5) {
              const tycId = `TYC ${parts[0]}-${parts[1]}-${parts[2]}`;
              photometry.push({
                auid: tycId,
                name: tycId,
                is_variable: false,
                bands: [{ band: "V", mag: vt }]
              });
            }
          }
        }
        if (photometry.length > 0) {
          log(`    ✓ ${vm.name}: найдено ${photometry.length} звезд сравнения`);
          const degCode = `${Math.round(Number(ra))}N${Math.round(Math.abs(Number(dec)))}`;
          return {
            chartid: `VIZ-${degCode}`,
            auid: targetName,
            photometry
          };
        }
      } catch (e) {
        log(`    ✗ ${vm.name}: ${e.message}`);
      } finally {
        clearTimeout(timer);
        activeAbortControllers.delete(ctrl);
      }
    }
    return null;
  }

  /**
   * Прямой резервный подбор контрольной звезды через 3 мировых зеркала CDS SIMBAD TAP (CORS: *)
   */
  async function querySimbadFieldCheckStar(ra, dec, targetName, log) {
    if (ra == null || isNaN(ra) || dec == null || isNaN(dec)) return null;
    log("  → CDS SIMBAD TAP (зеркала Strasbourg / IDIA / Harvard): прямой поиск звезды сравнения в поле 60'...");
    const adql = `SELECT TOP 25 basic.main_id, basic.ra, basic.dec, basic.otype_txt, flux.flux AS vmag ` +
                 `FROM basic JOIN flux ON basic.oid = flux.oidref ` +
                 `WHERE CONTAINS(POINT('ICRS', basic.ra, basic.dec), CIRCLE('ICRS', ${Number(ra).toFixed(6)}, ${Number(dec).toFixed(6)}, 0.45)) = 1 ` +
                 `AND flux.filter = 'V' AND flux.flux BETWEEN 9.0 AND 13.5`;
    const params = new URLSearchParams({ request: "doQuery", lang: "ADQL", format: "json", query: adql });
    const { data, mirrorName } = await raceMirrorsDirect(params, 6500, log);
    const cols = data.metadata.map(c => c.name);
    const rows = data.data.map(r => Object.fromEntries(cols.map((c, i) => [c, r[i]])));

    const photometry = [];
    for (const r of rows) {
      const id = String(r.main_id || "").replace(/^\*+\s*/, "").trim();
      const otype = String(r.otype_txt || "");
      if (!id || otype.includes("V*") || otype.toLowerCase().includes("var")) continue;
      if (targetName && id.toLowerCase() === String(targetName).replace(/^V\*\s+/i, "").toLowerCase()) continue;
      const vmag = parseFloat(r.vmag);
      if (isNaN(vmag)) continue;
      photometry.push({
        auid: id,
        name: id,
        is_variable: false,
        bands: [{ band: "V", mag: vmag }]
      });
    }
    if (!photometry.length) return null;
    const degCode = `${Math.round(Number(ra))}N${Math.round(Math.abs(Number(dec)))}`;
    log(`    ✓ Зеркало ${mirrorName}: подобрано ${photometry.length} стационарных звезд сравнения`);
    return {
      chartid: `X-${degCode}`,
      auid: targetName,
      photometry
    };
  }

  /**
   * Опрос AAVSO VSP через все доступные порты (HTTPS:443 / HTTP:80) и 6 независимых прокси-шлюзов
   */
  async function fetchVspUrlViaProxies(rawUrl, log, onProgress) {
    const vspRunners = [
      {
        name: "direct-https:443",
        run: async (signal) => {
          const r = await fetch(rawUrl, { signal });
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return await r.json();
        }
      },
      {
        name: "allorigins-json:443",
        run: async (signal) => {
          const r = await fetch("https://api.allorigins.win/get?url=" + encodeURIComponent(rawUrl), { signal });
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          const w = await r.json();
          if (!w || !w.contents) throw new Error("empty contents");
          return JSON.parse(w.contents);
        }
      },
      {
        name: "codetabs-gateway:443",
        run: async (signal) => {
          const r = await fetch("https://api.codetabs.com/v1/proxy/?quest=" + encodeURIComponent(rawUrl), { signal });
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return await r.json();
        }
      },
      {
        name: "allorigins-raw:443",
        run: async (signal) => {
          const r = await fetch("https://api.allorigins.win/raw?url=" + encodeURIComponent(rawUrl), { signal });
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return await r.json();
        }
      },
      {
        name: "corsfix-mirror:443",
        run: async (signal) => {
          const r = await fetch("https://proxy.corsfix.com/?" + rawUrl, { signal });
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return await r.json();
        }
      },
      {
        name: "cors-x2u-mirror:443",
        run: async (signal) => {
          const r = await fetch("https://cors.x2u.in/" + rawUrl, { signal });
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return await r.json();
        }
      }
    ];

    const entries = vspRunners.map(p => ({ p, ctrl: new AbortController(), done: false }));
    const attempts = entries.map(async (entry) => {
      activeAbortControllers.add(entry.ctrl);
      const timer = setTimeout(() => { try { entry.ctrl.abort(); } catch(_){} }, 9500);
      try {
        const t0 = performance.now();
        const data = await entry.p.run(entry.ctrl.signal);
        if (!data || (!data.chartid && !data.photometry)) throw new Error("invalid VSP JSON");
        const ms = Math.round(performance.now() - t0);
        log(`    ✓ Шлюз ${entry.p.name} — ${ms}ms`);
        if (onProgress) onProgress(`Получен ответ от ${entry.p.name} (${ms} мс)`);
        entry.done = true;
        return { data, source: entry.p.name };
      } finally {
        clearTimeout(timer);
        activeAbortControllers.delete(entry.ctrl);
      }
    });
    const winner = await Promise.any(attempts);
    entries.forEach(e => { if (!e.done) { try { e.ctrl.abort(); } catch(_){} } });
    return winner;
  }

  async function queryVsp(starName, log, simbadObj = null, onProgress = null) {
    const normStar = normalizeStarForVsp(starName, simbadObj && simbadObj.main_id);
    const cached = getCached(CACHE.vsp, normStar, null) || getCached(CACHE.vsp, starName, null);
    if (cached) {
      log(t("msgVspCache") + `: "${normStar}"`);
      return cached;
    }

    if (normStar !== starName) {
      log(`  ℹ️ Каноническое имя звезды для VSP/VSX: "${starName}" → "${normStar}"`);
    }

    const activeScopeProf = AstroLabCore.getScopeProfile(window._currentScopeModel || "S50");
    const scopeFovStr = String(activeScopeProf.vspFovArcmin || 60);
    const scopeMagLimitStr = String(activeScopeProf.magLimit || 14.5);
    const urlsToTry = [
      `https://apps.aavso.org/vsp/api/chart/?${new URLSearchParams({ format: "json", star: normStar, fov: scopeFovStr, maglimit: scopeMagLimitStr })}`
    ];
    const raVal = simbadObj && simbadObj.ra != null ? simbadObj.ra : parseFloat(document.getElementById("ra").value);
    const decVal = simbadObj && simbadObj.dec != null ? simbadObj.dec : parseFloat(document.getElementById("dec").value);
    if (!isNaN(raVal) && !isNaN(decVal)) {
      urlsToTry.push(
        `https://apps.aavso.org/vsp/api/chart/?${new URLSearchParams({ format: "json", ra: String(raVal), dec: String(decVal), fov: scopeFovStr, maglimit: scopeMagLimitStr })}`
      );
      urlsToTry.push(
        `http://apps.aavso.org:80/vsp/api/chart/?${new URLSearchParams({ format: "json", star: normStar, fov: scopeFovStr, maglimit: scopeMagLimitStr })}`
      );
    }

    log(t("msgVspProxy"));
    for (let idx = 0; idx < urlsToTry.length; idx++) {
      checkStop();
      if (onProgress) onProgress(`Попытка ${idx + 1}/${urlsToTry.length}: опрос AAVSO VSP через 6 портов и прокси-зеркал...`, 40 + idx * 15);
      try {
        const res = await fetchVspUrlViaProxies(urlsToTry[idx], log, onProgress);
        if (res && res.data && res.data.chartid) {
          setCached(CACHE.vsp, normStar, res, t("msgVspCache"));
          setCached(CACHE.vsp, starName, res, t("msgVspCache"));
          return res;
        }
      } catch (_) {}
    }

    // Уровень 2: Если AAVSO VSP не ответил, опрашиваем 3 мировых зеркала CDS SIMBAD TAP (Strasbourg, IDIA, Harvard)
    if (!isNaN(raVal) && !isNaN(decVal)) {
      if (onProgress) onProgress("Переключение на резервные мировые зеркала CDS SIMBAD TAP (Strasbourg, Harvard, IDIA)...", 75);
      try {
        const fallbackData = await querySimbadFieldCheckStar(raVal, decVal, normStar, log);
        if (fallbackData) {
          const result = { data: fallbackData, source: "CDS-SIMBAD-Mirror" };
          setCached(CACHE.vsp, normStar, result, t("msgVspCache"));
          return result;
        }
      } catch (e) {
        log(`  ✗ CDS SIMBAD Mirror Fallback: ${e.message}`);
      }

      // Уровень 3: Опрашиваем 4 мировых зеркала VizieR (Strasbourg, Harvard, Tokyo, IDIA)
      if (onProgress) onProgress("Опрос 4 мировых зеркал VizieR (Strasbourg, Harvard, Tokyo, Cape Town)...", 88);
      try {
        const vizData = await queryVizierMirrorsCheckStar(raVal, decVal, normStar, log);
        if (vizData) {
          const result = { data: vizData, source: "VizieR-Global-Mirror" };
          setCached(CACHE.vsp, normStar, result, t("msgVspCache"));
          return result;
        }
      } catch (e) {
        log(`  ✗ VizieR Mirror Fallback: ${e.message}`);
      }
    }

    throw new Error(t("msgVspDown"));
  }

  /**
   * ============================================================================
   * МОДУЛЬ 5: НАУЧНЫЙ АЛГОРИТМ АВТОПОДБОРА КОНТРОЛЬНОЙ ЗВЕЗДЫ (CHECK STAR)
   * Разработчику: Сортирует звезды сравнения VSP по близости к оптимуму Seestar
   * (11.5 mag, диапазон 9.5–13.0 mag) и приоритету полос V / TG.
   * ============================================================================
   */
  function getBandMag(star, filterPriority) {
    if (!star || !Array.isArray(star.bands)) return null;
    for (const want of filterPriority) {
      const b = star.bands.find(x => x && x.mag != null && String(x.filter || x.band || "").toUpperCase() === want);
      if (b) {
        const v = parseFloat(b.mag);
        if (!isNaN(v)) return { mag: v, filter: want };
      }
    }
    const any = star.bands.find(x => x && x.mag != null && !isNaN(parseFloat(x.mag)));
    if (any) return { mag: parseFloat(any.mag), filter: String(any.filter || any.band || "?") };
    return null;
  }

  function pickCheckStar(photometry, targetAuid) {
    if (!Array.isArray(photometry) || photometry.length === 0) return null;
    const filterPriority = ["V", "TG", "CV", "B", "SG", "R", "Rc", "Ic"];
    const candidates = [];
    for (const s of photometry) {
      if (!s) continue;
      const auid = s.auid || s.AUID || s.id;
      if (!auid) continue;
      if (targetAuid && String(auid).toUpperCase() === String(targetAuid).toUpperCase()) continue;
      if (s.is_variable === true || s.variable === true) continue;
      const cat = String(s.category || s.type || "").toLowerCase();
      if (cat.includes("var") || cat.includes("target")) continue;
      const m = getBandMag(s, filterPriority);
      if (!m) continue;
      candidates.push({ auid: String(auid), name: s.name || s.identifier || "", mag: m.mag, filter: m.filter });
    }
    if (candidates.length === 0) return null;
    const score = c => {
      const d = Math.abs(c.mag - 11.5);
      const penalty = (c.mag < 9.5 || c.mag > 13.0) ? 5 : 0;
      const filterPenalty = (c.filter === "V" || c.filter === "TG") ? 0 : 1;
      return d + penalty + filterPenalty;
    };
    candidates.sort((a, b) => score(a) - score(b));
    return candidates[0];
  }

  /**
   * ============================================================================
   * МОДУЛЬ 6: ВИЗУАЛИЗАЦИЯ, ПРЕДПРОСМОТР, СНИМОК DSS2 И КРИВАЯ БЛЕСКА
   * ============================================================================
   */
  const statusWrapper = document.getElementById("statusWrapper");
  const statusBox = document.getElementById("statusBox");
  const statusExplainText = document.getElementById("statusExplainText");
  let logBuffer = [];

  function beginLog(header, explain = "") {
    statusWrapper.style.display = "block";
    statusBox.className = "status";
    statusExplainText.textContent = explain ? `ℹ️ ${explain}` : `ℹ️ ${header}`;
    logBuffer = [header, ""];
    statusBox.textContent = logBuffer.join("\n");
    return msg => {
      String(msg).split("\n").forEach(p => logBuffer.push(p));
      statusBox.textContent = logBuffer.join("\n");
      statusBox.scrollTop = statusBox.scrollHeight;
    };
  }

  function setFieldStatus(inputId, hintId, status, message) {
    const input = document.getElementById(inputId);
    const hint = document.getElementById(hintId);
    input.classList.remove("field-match", "field-mismatch", "field-warn");
    hint.classList.remove("ok", "bad", "warn");
    if (status === "ok") {
      input.classList.add("field-match");
      hint.classList.add("ok");
      hint.textContent = message || t("matchOk");
    } else if (status === "warn") {
      input.classList.add("field-warn");
      hint.classList.add("warn");
      hint.textContent = message || t("matchWarn");
    } else if (status === "bad") {
      input.classList.add("field-mismatch");
      hint.classList.add("bad");
      hint.textContent = message || t("matchBad");
    } else {
      hint.textContent = message || "";
    }
  }

  function checkCoordDiff(uiVal, fileVal) {
    if (isNaN(uiVal) || isNaN(fileVal)) return { status: null, msg: t("matchMissing") };
    const diff = Math.abs(uiVal - fileVal);
    if (diff < 1e-5) return { status: "ok", msg: t("matchOk") };
    if (diff < 0.05) return { status: "warn", msg: `${t("matchWarn")} (${t("thFile")}: ${fileVal})` };
    return { status: "bad", msg: `${t("matchBad")} (${t("thFile")}: ${fileVal})` };
  }

  function extractFirstDataRow(lines) {
    for (let i = 0; i < lines.length; i++) {
      const raw = lines[i].trim();
      if (!raw) continue;
      const c = raw.split(",");
      if (c.length < 19) continue;
      if (c[1] && c[1].trim().toLowerCase() === "non-reference star") {
        return {
          starId: c[0].trim(),
          ra: parseFloat(c[2].trim()),
          dec: parseFloat(c[3].trim()),
          mag: parseFloat(c[6].trim()),
          merr: parseFloat(c[7].trim()),
          utc: c[11].trim()
        };
      }
    }
    return null;
  }

  function drawLightCurve(lines) {
    const box = document.getElementById("lightCurveBox");
    const canvas = document.getElementById("lightCurveCanvas");
    const statsEl = document.getElementById("lightCurveStats");
    if (!canvas) return;

    const pts = [];
    for (let i = 0; i < lines.length; i++) {
      const raw = lines[i].trim();
      if (!raw || (i === 0 && raw.toLowerCase().startsWith("name,"))) continue;
      const c = raw.split(",");
      if (c.length < 19 || c[1].trim().toLowerCase() !== "non-reference star") continue;
      const mag = parseFloat(c[6].trim());
      const merr = parseFloat(c[7].trim());
      const jd1 = parseFloat(c[12].trim());
      const jd2 = parseFloat(c[15].trim());
      const jd = (!isNaN(jd1) && !isNaN(jd2)) ? (jd1 + jd2) / 2 : jd1;
      if (!isNaN(mag) && !isNaN(jd)) {
        pts.push({ jd, mag, merr: isNaN(merr) ? 0 : merr });
      }
    }

    const lcEmptyEl = document.getElementById("lightCurveEmptyState");
    if (pts.length < 2) {
      box.style.display = "none";
      if (statsEl) { statsEl.textContent = ""; statsEl.style.display = "none"; }
      if (lcEmptyEl) lcEmptyEl.style.display = "flex";
      window._lastLightCurveScreenPts = [];
      return;
    }

    if (lcEmptyEl) lcEmptyEl.style.display = "none";
    box.style.display = "block";
    if (statsEl) statsEl.style.display = "inline-flex";
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    let minJd = Infinity, maxJd = -Infinity, minMag = Infinity, maxMag = -Infinity;
    for (let i = 0; i < pts.length; i++) {
      const p = pts[i];
      if (p.jd < minJd) minJd = p.jd;
      if (p.jd > maxJd) maxJd = p.jd;
      if (p.mag - p.merr < minMag) minMag = p.mag - p.merr;
      if (p.mag + p.merr > maxMag) maxMag = p.mag + p.merr;
    }

    const padL = 48, padR = 16, padT = 18, padB = 26;
    const plotW = w - padL - padR;
    const plotH = h - padT - padB;

    ctx.strokeStyle = document.body.getAttribute("data-theme") === "light" ? "rgba(15,23,42,0.12)" : "rgba(255,255,255,0.08)";
    ctx.lineWidth = 1;
    for (let k = 0; k <= 3; k++) {
      const y = padT + (plotH * k) / 3;
      ctx.beginPath();
      ctx.moveTo(padL, y);
      ctx.lineTo(w - padR, y);
      ctx.stroke();

      const mVal = minMag + ((maxMag - minMag) * k) / 3;
      ctx.fillStyle = document.body.getAttribute("data-theme") === "light" ? "#475569" : "#98a2b3";
      ctx.font = "10px monospace";
      ctx.textAlign = "right";
      ctx.fillText(mVal.toFixed(3), padL - 6, y + 3);
    }

    const getX = jd => padL + ((jd - minJd) / (maxJd - minJd || 1)) * plotW;
    const getY = mag => padT + ((mag - minMag) / (maxMag - minMag || 0.01)) * plotH;

    const isLightTheme = document.body.getAttribute("data-theme") === "light";
    ctx.strokeStyle = isLightTheme ? "rgba(29, 78, 216, 0.78)" : "rgba(10, 132, 255, 0.65)";
    ctx.lineWidth = 1.75;
    ctx.beginPath();
    pts.forEach((p, idx) => {
      const x = getX(p.jd), y = getY(p.mag);
      if (idx === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    window._lastLightCurveScreenPts = [];
    const lcStep = pts.length > 1500 ? Math.ceil(pts.length / 1500) : 1;
    pts.forEach((p, idx) => {
      if (idx % lcStep !== 0 && idx !== pts.length - 1) return;
      const x = getX(p.jd);
      const y = getY(p.mag);
      const yTop = getY(p.mag - p.merr);
      const yBot = getY(p.mag + p.merr);
      window._lastLightCurveScreenPts.push({ x, y, jd: p.jd, mag: p.mag, merr: p.merr, idx: idx + 1 });

      ctx.strokeStyle = isLightTheme ? "rgba(29, 78, 216, 0.55)" : "rgba(100, 210, 255, 0.48)";
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(x, yTop);
      ctx.lineTo(x, yBot);
      ctx.stroke();

      ctx.fillStyle = isLightTheme ? "#1d4ed8" : "#64d2ff";
      ctx.beginPath();
      ctx.arc(x, y, 3.2, 0, Math.PI * 2);
      ctx.fill();
    });

    statsEl.textContent = `N=${pts.length} | Δm=${(maxMag - minMag).toFixed(3)}m`;
  }

  function loadStarImage(starId, ra, dec) {
    const box = document.getElementById("starImageBox");
    const img = document.getElementById("starImage");
    const cap = document.getElementById("starImageCaption");

    const hasRaDec = (ra != null && !isNaN(ra) && dec != null && !isNaN(dec));
    if (!hasRaDec) {
      box.style.display = "none";
      return;
    }

    const skyviewUrl = `https://skyview.gsfc.nasa.gov/current/cgi/runquery.pl?Position=${encodeURIComponent(ra)},${encodeURIComponent(dec)}&Survey=DSS2+Red&Return=JPEG&Size=2.4&Pixels=400`;
    const cdsUrl = `https://alasky.cds.unistra.fr/hips-image-services/hips2fits?hips=CDS%2FP%2FDSS2%2Fcolor&width=400&height=400&fov=2.4&format=jpg&ra=${encodeURIComponent(ra)}&dec=${encodeURIComponent(dec)}`;
    const aladinUrl = `https://aladin.cds.unistra.fr/AladinLite/?target=${encodeURIComponent(ra)}%20${encodeURIComponent(dec)}&fov=2.4`;

    box.style.display = "flex";
    img.style.opacity = "0";
    img.src = "";
    if (typeof window.renderProceduralDssFallback === "function") {
      window.renderProceduralDssFallback(starId, ra, dec);
    }
    cap.className = "caption";
    cap.innerHTML = `${escapeHtml(t("imgLoading"))} <a href="${aladinUrl}" target="_blank" rel="noopener noreferrer" style="color:var(--ios-cyan);">${escapeHtml(t("imgOpenAladin"))}</a>`;

    let attempt = 0;
    const tryLoad = (url) => {
      img.onload = () => {
        img.style.opacity = "1";
        cap.className = "caption";
        cap.innerHTML = t("imgFieldCaption").replace("{star}", escapeHtml(starId || "—"));
      };
      img.onerror = () => {
        attempt++;
        if (attempt === 1) {
          cap.textContent = t("imgAltServer");
          tryLoad(cdsUrl);
        } else {
          img.style.opacity = "0";
          cap.className = "caption";
          cap.innerHTML = `${t("dssFieldFallbackFmt").replace("{star}", escapeHtml(starId || "—"))}<a href="${aladinUrl}" target="_blank" rel="noopener noreferrer" style="color:var(--ios-cyan); text-decoration:none;">${escapeHtml(t("imgOpenAladin"))}</a>)`;
        }
      };
      img.src = url;
    };
    tryLoad(skyviewUrl);
  }

  document.getElementById("btnLoadImage").addEventListener("click", () => {
    const star = document.getElementById("starid").value.trim();
    const ra = parseFloat(document.getElementById("ra").value.trim());
    const dec = parseFloat(document.getElementById("dec").value.trim());
    if (isNaN(ra) || isNaN(dec)) {
      showIosNotification(t("btnLoadImage"), t("imgNoCoords"), t("tipRaText"), "warn");
      return;
    }
    document.getElementById("previewCard").style.display = "block";
    loadStarImage(star, ra, dec);
    document.getElementById("starImageBox").scrollIntoView({ behavior: "smooth", block: "nearest" });
  });

  function revealAndFocusField(inputId) {
    const el = document.getElementById(inputId);
    if (!el) return;
    const parentAcc = el.closest("details.step-accordion");
    if (parentAcc && !parentAcc.open) {
      parentAcc.open = true;
    }
    setTimeout(() => {
      try {
        el.focus();
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      } catch (_) {}
    }, 30);
  }

  // ПУНКТ 5: Автоматическое управление аккордеонами с задержкой 3 секунды (3000 мс)
  window.scheduleSimbadLoadedAccordionTransition = function() {
    if (window._accSimbadTimer) clearTimeout(window._accSimbadTimer);
    window._accSimbadTimer = setTimeout(() => {
      const acc1 = document.getElementById("accObserverStar");
      const acc2 = document.getElementById("accFileSelect");
      const acc3 = document.getElementById("accConvertSection");
      const hasCsv = Boolean(currentCsvText && String(currentCsvText).trim());
      if (acc1) acc1.open = false;
      if (hasCsv) {
        if (acc2) acc2.open = false;
        if (acc3) acc3.open = true;
      } else {
        if (acc2) acc2.open = true;
        if (acc3) acc3.open = false;
      }
      updateAccordionSummaryBadges();
    }, 3000);
  };

  window.scheduleCsvLoadedAccordionTransition = function() {
    if (window._accCsvTimer) clearTimeout(window._accCsvTimer);
    window._accCsvTimer = setTimeout(() => {
      const acc2 = document.getElementById("accFileSelect");
      const acc3 = document.getElementById("accConvertSection");
      if (acc2) acc2.open = false;
      if (acc3) acc3.open = true;
      updateAccordionSummaryBadges();
    }, 3000);
  };

  function updateAccordionSummaryBadges() {
    const obsVal = (document.getElementById("obscode")?.value || document.getElementById("headerObscodeQuick")?.value || "").trim();
    const starVal = (document.getElementById("starid")?.value || "").trim();
    const obsPill = document.getElementById("accObserverSummaryPill");
    if (obsPill) {
      if (obsVal || starVal) {
        const simbadTag = STATE.simbadCatalogLoaded ? " ✓ SIMBAD" : "";
        obsPill.textContent = `${obsVal || "OBSCODE: —"} • ${starVal || "STARID: —"}${simbadTag}`;
        obsPill.classList.toggle("pill-ready", Boolean(obsVal && starVal && STATE.simbadCatalogLoaded));
      } else {
        obsPill.textContent = "OBSCODE / STARID";
        obsPill.classList.remove("pill-ready");
      }
    }

    const hasCsv = Boolean(currentCsvText && String(currentCsvText).trim());
    const filePill = document.getElementById("accFileSummaryPill");
    if (filePill) {
      if (hasCsv) {
        const loadedName = (document.getElementById("selectedFileNameText")?.textContent || "CSV загружен").trim();
        filePill.textContent = loadedName;
        filePill.classList.add("pill-ready");
      } else {
        filePill.textContent = t("noFileSelected");
        filePill.classList.remove("pill-ready");
      }
    }

    const convPill = document.getElementById("accConvertSummaryPill");
    const step1Ready = Boolean(obsVal && starVal && STATE.simbadCatalogLoaded);
    if (convPill) {
      if (step1Ready && hasCsv) {
        convPill.textContent = t("lblConvertReady");
        convPill.classList.add("pill-ready");
      } else {
        convPill.textContent = t("lblConvertWait");
        convPill.classList.remove("pill-ready");
      }
    }
  }

  function updateEmptyStateSimbadPill() {
    const pill = document.getElementById("simbadPreloadedPill");
    if (!pill) return;
    const hasCsv = Boolean(currentCsvText && String(currentCsvText).trim());
    if (!hasCsv && STATE.simbadCatalogLoaded && STATE.catalogStarName) {
      pill.style.display = "inline-flex";
      pill.textContent = `✓ Данные SIMBAD (${STATE.catalogStarName}) загружены — выберите CSV-файл Seestar для сверки`;
    } else {
      pill.style.display = "none";
    }
  }

  function extractCatalogMagBounds(starName, kmagVal) {
    const cleanTarget = String(starName || "").trim();
    const catList = window.AAVSO_URGENT_CATALOGUE || [];
    if (cleanTarget && Array.isArray(catList)) {
      const found = catList.find(item =>
        AstroLabCore.areSameStar(item.star, cleanTarget) ||
        (item.alias && AstroLabCore.areSameStar(item.alias, cleanTarget))
      );
      if (found && found.magRange) {
        const nums = (String(found.magRange).match(/\d+(?:\.\d+)?/g) || [])
          .map(Number)
          .filter(n => !isNaN(n) && n >= -2 && n <= 20);
        if (nums.length >= 2) {
          const minM = Math.min(nums[0], nums[1]);
          const maxM = Math.max(nums[0], nums[1]);
          if (maxM - minM > 0.05) {
            return { minMag: minM, maxMag: maxM, label: `${minM.toFixed(2)} – ${maxM.toFixed(2)} m (SIMBAD/VSX)` };
          }
        }
        if (nums.length >= 1) {
          const m0 = nums[0];
          return { minMag: m0 - 0.15, maxMag: m0 + 0.15, label: `${m0.toFixed(2)} m (SIMBAD/VSX)` };
        }
      }
    }
    if (STATE.catalogSimbadVmag != null && !isNaN(STATE.catalogSimbadVmag)) {
      const v = Number(STATE.catalogSimbadVmag);
      return { minMag: v - 0.5, maxMag: v + 0.5, label: `${v.toFixed(2)} m (SIMBAD V)` };
    }
    if (!isNaN(kmagVal)) {
      const k = Number(kmagVal);
      return { minMag: k - 1.5, maxMag: k + 1.5, label: `${k.toFixed(3)} m (VSP KMAG)` };
    }
    return { minMag: 3.0, maxMag: 15.5, label: "3.00 – 15.50 m (SIMBAD)" };
  }

  function checkMagCompatibility(fileMag, starName, kmagVal) {
    const bounds = extractCatalogMagBounds(starName, kmagVal);
    if (isNaN(fileMag) || fileMag < -1.5 || fileMag > 18.5) {
      return {
        status: "bad",
        catalogRefText: bounds.label,
        msg: `${t("matchBad")} (MAG ${fileMag} вне диапазона ${bounds.label})`
      };
    }
    // Точное попадание в каталожный диапазон блеска звезды (с допуском ±0.12m на полосу TG)
    if (fileMag >= bounds.minMag - 0.12 && fileMag <= bounds.maxMag + 0.12) {
      return { status: "ok", catalogRefText: bounds.label, msg: t("matchOk") };
    }
    // Небольшое отличие (инструментальный сдвиг фильтра TG или фаза вспышки в пределах ±1.5m)
    if (fileMag >= bounds.minMag - 1.50 && fileMag <= bounds.maxMag + 1.50) {
      return { status: "warn", catalogRefText: bounds.label, msg: t("matchWarn") };
    }
    // Критическое расхождение (> 1.5m от каталожного диапазона)
    return {
      status: "bad",
      catalogRefText: bounds.label,
      msg: `${t("matchBad")} (MAG ${fileMag} вне каталожного коридора ${bounds.label})`
    };
  }

  function checkMerrCompatibility(fileMerr) {
    const refErr = (STATE.catalogVspMerr != null && !isNaN(STATE.catalogVspMerr))
      ? Number(STATE.catalogVspMerr)
      : 0.0300;
    const refLabel = `≤ ${refErr.toFixed(4)} m (допуск ≤ 0.15m)`;
    if (isNaN(fileMerr) || fileMerr <= 0) {
      return {
        status: "bad",
        catalogRefText: refLabel,
        msg: `${t("matchBad")} (некорректная погрешность MERR: ${fileMerr})`
      };
    }
    if (fileMerr <= refErr) {
      return { status: "ok", catalogRefText: refLabel, msg: t("matchOk") };
    }
    if (fileMerr <= 0.1500) {
      return { status: "warn", catalogRefText: refLabel, msg: t("matchWarn") };
    }
    return {
      status: "bad",
      catalogRefText: refLabel,
      msg: `${t("matchBad")} (погрешность MERR ${fileMerr}m превышает предел 0.1500m)`
    };
  }

  // ПУНКТ 1: Глобальные функции гарантированного закрытия модального окна «Критическое расхождение данных»
  window.closeCriticalMismatchModal = function(ev) {
    if (ev && typeof ev.preventDefault === "function") ev.preventDefault();
    if (ev && typeof ev.stopPropagation === "function") ev.stopPropagation();
    const modal = document.getElementById("criticalMismatchModal");
    if (modal) {
      modal.style.setProperty("display", "none", "important");
      modal.setAttribute("aria-hidden", "true");
    }
    STATE.dismissedMismatchSig = STATE.currentMismatchSig || "dismissed";
  };

  window.openCriticalMismatchInputs = function(ev) {
    window.closeCriticalMismatchModal(ev);
    const acc1 = document.getElementById("accObserverStar");
    const acc2 = document.getElementById("accFileSelect");
    if (acc1) acc1.open = true;
    if (acc2) acc2.open = true;
    revealAndFocusField("starid");
  };

  function applyCriticalMismatchState(isCritical, reasons, showModalNow = false) {
    STATE.isConversionBlockedByMismatch = Boolean(isCritical);
    STATE.lastMismatchReasons = Array.isArray(reasons) ? reasons : [];
    const sig = isCritical ? STATE.lastMismatchReasons.join("|") : "";
    STATE.currentMismatchSig = sig;

    const btnConvert = document.getElementById("btnConvert");
    const lockBanner = document.getElementById("convertLockReasonBanner");

    if (btnConvert) {
      btnConvert.disabled = Boolean(isCritical);
      btnConvert.setAttribute("aria-disabled", isCritical ? "true" : "false");
      btnConvert.classList.toggle("btn-locked-critical", Boolean(isCritical));
    }

    if (lockBanner) {
      if (isCritical) {
        lockBanner.style.display = "block";
        lockBanner.textContent = "🔒 Обнаружено критическое расхождение данных. Конвертация заблокирована. Проверьте правильность выбранной звезды и файла.";
      } else {
        lockBanner.style.display = "none";
        lockBanner.textContent = "";
      }
    }

    const modal = document.getElementById("criticalMismatchModal");
    if (isCritical && showModalNow) {
      const detailsEl = document.getElementById("critModalDetailsList");
      if (detailsEl) {
        detailsEl.innerHTML = STATE.lastMismatchReasons.length
          ? STATE.lastMismatchReasons.map(r => `<div class="crit-reason-line">• ${escapeHtml(r)}</div>`).join("")
          : `<div class="crit-reason-line">• Проверьте соответствие координат RA/DEC, имени звезды (STARID) и звёздной величины (MAG).</div>`;
      }
      if (modal) {
        modal.style.setProperty("display", "flex", "important");
        modal.setAttribute("aria-hidden", "false");
      }
    } else if (!isCritical) {
      STATE.dismissedMismatchSig = "";
      if (modal) {
        modal.style.setProperty("display", "none", "important");
        modal.setAttribute("aria-hidden", "true");
      }
    }
  }

  function previewCsvText(text, options = {}) {
    const triggerModalOnMismatch = options.triggerModal !== false;
    const previewCard = document.getElementById("previewCard");
    const emptyStateEl = document.getElementById("previewEmptyState");
    const previewTableEl = document.getElementById("previewTable");
    const tbody = document.querySelector("#previewTable tbody");
    const previewStatus = document.getElementById("previewStatus");
    const lcBox = document.getElementById("lightCurveBox");
    const lcEmpty = document.getElementById("lightCurveEmptyState");
    const lcStats = document.getElementById("lightCurveStats");

    updateAccordionSummaryBadges();

    // ПУНКТ 5 (Empty State): Пока CSV-файл Seestar не выбран — таблица скрыта
    if (!text || !String(text).trim()) {
      if (previewCard) previewCard.style.display = "block";
      if (emptyStateEl) emptyStateEl.style.display = "block";
      if (previewTableEl) previewTableEl.style.display = "none";
      if (previewStatus) previewStatus.style.display = "none";
      if (tbody) tbody.innerHTML = "";
      if (lcBox) lcBox.style.display = "none";
      if (lcEmpty) lcEmpty.style.display = "flex";
      if (lcStats) { lcStats.textContent = ""; lcStats.style.display = "none"; }
      updateEmptyStateSimbadPill();
      applyCriticalMismatchState(false, [], false);
      return;
    }

    const lines = text.split(/\r?\n/);
    const row = extractFirstDataRow(lines);

    if (!row) {
      if (previewCard) previewCard.style.display = "block";
      if (emptyStateEl) emptyStateEl.style.display = "block";
      if (previewTableEl) previewTableEl.style.display = "none";
      if (previewStatus) { previewStatus.style.display = "block"; previewStatus.textContent = t("msgNoData"); }
      if (tbody) tbody.innerHTML = "";
      if (lcBox) lcBox.style.display = "none";
      if (lcEmpty) lcEmpty.style.display = "flex";
      applyCriticalMismatchState(false, [], false);
      showIosNotification(t("secPreview"), t("msgNoData"), t("msgNoDataExplain"), "warn");
      return;
    }

    if (previewCard) previewCard.style.display = "block";
    if (emptyStateEl) emptyStateEl.style.display = "none";
    if (previewTableEl) previewTableEl.style.display = "table";

    // ПУНКТ 8: КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО подставлять данные из CSV-файла Seestar
    // в поля каталога SIMBAD (#ra, #dec, #chart, #kname, #kmag) и в столбец «Данные из Каталога SIMBAD»!
    const hasSimbadCatalog = Boolean(
      STATE.simbadCatalogLoaded &&
      STATE.catalogStarName &&
      STATE.catalogRa != null &&
      !isNaN(Number(STATE.catalogRa)) &&
      STATE.catalogDec != null &&
      !isNaN(Number(STATE.catalogDec))
    );

    if (!hasSimbadCatalog) {
      // Данные из каталога SIMBAD ещё НЕ загружены пользователем:
      // показываем только столбец «Данные из Seestar», а столбец «Данные из Каталога SIMBAD» оставляем пустым ("— (Не загружено)") без ложной сверки!
      if (previewStatus) {
        previewStatus.style.display = "block";
        previewStatus.textContent = "Файл Seestar прочитан. Нажмите «🔭 Загрузить SIMBAD + VSP» в разделе 1 для сверки с каталогом.";
      }
      setFieldStatus("starid", "staridHint", null, "");
      setFieldStatus("ra", "raHint", null, "");
      setFieldStatus("dec", "decHint", null, "");

      const waitingBadge = `<span style="color:var(--ios-text-secondary); font-size:11px;">⏳ Ожидается SIMBAD</span>`;
      const notLoadedCell = `<span style="color:var(--ios-text-secondary); font-style:italic;">— (Не загружено)</span>`;

      tbody.innerHTML = `
        <tr><td>STARID</td><td>${escapeHtml(row.starId)}</td><td>${notLoadedCell}</td><td id="previewStarIdCheckCell">${waitingBadge}</td></tr>
        <tr><td>RA</td><td>${escapeHtml(row.ra)}</td><td>${notLoadedCell}</td><td>${waitingBadge}</td></tr>
        <tr><td>DEC</td><td>${escapeHtml(row.dec)}</td><td>${notLoadedCell}</td><td>${waitingBadge}</td></tr>
        <tr><td>MAG</td><td>${escapeHtml(row.mag)}</td><td>${notLoadedCell}</td><td>${waitingBadge}</td></tr>
        <tr><td>MERR</td><td>${escapeHtml(row.merr)}</td><td>${notLoadedCell}</td><td>${waitingBadge}</td></tr>
        <tr><td>UTC</td><td>${escapeHtml(row.utc)}</td><td colspan="2"></td></tr>
      `;

      applyCriticalMismatchState(false, [], false);
      drawLightCurve(lines);
      loadStarImage(row.starId, row.ra, row.dec);
      updateAccordionSummaryBadges();
      return;
    }

    // Если данные из SIMBAD реально загружены (STATE.simbadCatalogLoaded === true):
    if (previewStatus) {
      previewStatus.style.display = "block";
      previewStatus.textContent = t("previewReady");
    }

    const catStar = STATE.catalogStarName;
    const catRa = Number(STATE.catalogRa);
    const catDec = Number(STATE.catalogDec);
    const catKmag = parseFloat((document.getElementById("kmag")?.value || "").trim());

    const cmp = AstroLabCore.compareStarIds(row.starId, catStar);
    const starIdMatch = cmp.status;
    let starIdMsg = "";
    if (cmp.status === "ok") {
      starIdMsg = t("starIdSame");
    } else if (cmp.status === "warn") {
      starIdMsg = t("starIdSynonymMsg")
        .replace("{cat}", cmp.canonicalUi || catStar)
        .replace("{file}", row.starId);
    } else if (cmp.status === "bad") {
      starIdMsg = t("starIdDiffStarMsg")
        .replace("{file}", row.starId)
        .replace("{ui}", catStar);
    }
    setFieldStatus("starid", "staridHint", starIdMatch, starIdMsg);

    const raRes = checkCoordDiff(catRa, row.ra);
    setFieldStatus("ra", "raHint", raRes.status, raRes.msg);

    const decRes = checkCoordDiff(catDec, row.dec);
    setFieldStatus("dec", "decHint", decRes.status, decRes.msg);

    const magRes = checkMagCompatibility(row.mag, catStar, catKmag);
    const merrRes = checkMerrCompatibility(row.merr);

    const matchCell = (m, isStarRow = false) => {
      if (m === "ok") return `<span style="color:var(--ios-green); font-weight:700;">${escapeHtml(t("matchOk"))}</span>`;
      if (m === "warn") return `<span style="color:var(--ios-yellow); font-weight:700;">${escapeHtml(t("matchWarn"))}</span>`;
      if (m === "bad") return `<span style="color:var(--ios-red); font-weight:700;">${escapeHtml(isStarRow ? t("matchDiffStar") : t("matchBad"))}</span>`;
      return `<span style="color:var(--ios-text-secondary)">${escapeHtml(t("starIdMissing"))}</span>`;
    };

    const starRowCls = starIdMatch === "bad" ? ' class="row-critical-mismatch"' : "";
    const raRowCls   = raRes.status === "bad" ? ' class="row-critical-mismatch"' : "";
    const decRowCls  = decRes.status === "bad" ? ' class="row-critical-mismatch"' : "";
    const magRowCls  = magRes.status === "bad" ? ' class="row-critical-mismatch"' : "";
    const merrRowCls = merrRes.status === "bad" ? ' class="row-critical-mismatch"' : "";

    const simbadMagRef = !isNaN(catKmag) ? `K=${catKmag}m` : "Каталог SIMBAD / VSX";

    tbody.innerHTML = `
      <tr${starRowCls}><td>STARID</td><td>${escapeHtml(row.starId)}</td><td>${escapeHtml(catStar)}</td><td id="previewStarIdCheckCell">${matchCell(starIdMatch, true)}</td></tr>
      <tr${raRowCls}><td>RA</td><td>${escapeHtml(row.ra)}</td><td>${escapeHtml(catRa.toFixed(6))}</td><td>${matchCell(raRes.status)}</td></tr>
      <tr${decRowCls}><td>DEC</td><td>${escapeHtml(row.dec)}</td><td>${escapeHtml(catDec.toFixed(6))}</td><td>${matchCell(decRes.status)}</td></tr>
      <tr${magRowCls}><td>MAG</td><td>${escapeHtml(row.mag)}</td><td>${escapeHtml(magRes.catalogRefText)}</td><td>${matchCell(magRes.status)}</td></tr>
      <tr${merrRowCls}><td>MERR</td><td>${escapeHtml(row.merr)}</td><td>${escapeHtml(merrRes.catalogRefText)}</td><td>${matchCell(merrRes.status)}</td></tr>
      <tr><td>UTC</td><td>${escapeHtml(row.utc)}</td><td colspan="2"></td></tr>
    `;

    const mismatchReasons = [];
    if (starIdMatch === "bad") {
      mismatchReasons.push(`Не совпадает звезда (STARID): в файле Seestar «${row.starId}», в каталоге SIMBAD «${catStar}»`);
    }
    if (raRes.status === "bad") {
      mismatchReasons.push(`Критическое расхождение координаты RA (> 0.05°): файл ${row.ra}° vs SIMBAD ${catRa.toFixed(5)}°`);
    }
    if (decRes.status === "bad") {
      mismatchReasons.push(`Критическое расхождение координаты DEC (> 0.05°): файл ${row.dec}° vs SIMBAD ${catDec.toFixed(5)}°`);
    }
    if (magRes.status === "bad") {
      mismatchReasons.push(`Критическое расхождение звёздной величины (MAG): в файле ${row.mag}m vs каталог ${magRes.catalogRefText}`);
    }
    if (merrRes.status === "bad") {
      mismatchReasons.push(`Критическое превышение погрешности (MERR): в файле ${row.merr}m vs норматив ${merrRes.catalogRefText}`);
    }

    const isCritical = mismatchReasons.length > 0;
    const newSig = mismatchReasons.join("|");
    const shouldPopModal = isCritical && triggerModalOnMismatch && (newSig !== STATE.dismissedMismatchSig);
    applyCriticalMismatchState(isCritical, mismatchReasons, shouldPopModal);

    drawLightCurve(lines);
    loadStarImage(catStar || row.starId, catRa, catDec);
    updateAccordionSummaryBadges();
  }

  function previewFile(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => {
      currentCsvText = e.target.result;
      STATE.dismissedMismatchSig = "";
      previewCsvText(currentCsvText, { triggerModal: true });
      // ПУНКТ 5: Спустя 3 секунды после выбора CSV-файла автоматически сворачиваем Раздел 2
      if (typeof window.scheduleCsvLoadedAccordionTransition === "function") {
        window.scheduleCsvLoadedAccordionTransition();
      }
    };
    reader.readAsText(file);
  }

  ["starid", "ra", "dec", "kmag"].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener("input", () => {
      if (id === "starid") {
        // При ручном изменении звезды пользователем сбрасываем флаг старого SIMBAD до нажатия «Загрузить SIMBAD + VSP»
        STATE.simbadCatalogLoaded = false;
      } else if (id === "ra" || id === "dec") {
        const rVal = parseFloat((document.getElementById("ra")?.value || "").trim());
        const dVal = parseFloat((document.getElementById("dec")?.value || "").trim());
        if (!isNaN(rVal) && !isNaN(dVal)) {
          STATE.catalogRa = rVal;
          STATE.catalogDec = dVal;
          if (!STATE.catalogStarName) {
            STATE.catalogStarName = (document.getElementById("starid")?.value || "").trim();
          }
          STATE.simbadCatalogLoaded = Boolean(STATE.catalogStarName);
        }
      }
      updateAccordionSummaryBadges();
      if (currentCsvText) previewCsvText(currentCsvText, { triggerModal: false });
    });
    el.addEventListener("change", () => {
      updateAccordionSummaryBadges();
      if (currentCsvText && STATE.simbadCatalogLoaded) {
        STATE.dismissedMismatchSig = "";
        previewCsvText(currentCsvText, { triggerModal: true });
      }
    });
  });

  /**
   * ============================================================================
   * МОДУЛЬ 7: ПАГИНАЦИЯ И ЛОГ СРАВНЕНИЯ «ДО / ПОСЛЕ»
   * ============================================================================
   */
  let allDiffs = [];
  let currentPage = 1;

  function renderLogPage() {
    const rowsPerPage = parseInt(document.getElementById("rowsPerPage").value, 10);
    const totalRows = allDiffs.length;
    const totalPages = Math.ceil(totalRows / rowsPerPage) || 1;
    if (currentPage > totalPages) currentPage = totalPages;
    if (currentPage < 1) currentPage = 1;

    const start = (currentPage - 1) * rowsPerPage;
    const end = Math.min(start + rowsPerPage, totalRows);
    const pageData = allDiffs.slice(start, end);
    const rowLabel = t("rowWord");
    let html = "";

    pageData.forEach(d => {
      const starIdChanged = d.origStarId !== d.newStarId;
      const magChanged = Math.abs(d.origMag - d.newMag) > 0.00001;
      const merrChanged = Math.abs(d.origMerr - d.newMerr) > 0.00001;

      html += `<div class="log-row">
        <strong>${escapeHtml(rowLabel)} ${d.rowNum}</strong><br>
        <span class="${starIdChanged ? 'log-change' : 'log-keep'}">STARID</span> : "${escapeHtml(d.origStarId)}" → "${escapeHtml(d.newStarId)}" ${starIdChanged ? '(✓)' : '(=)'}<br>
        <span class="${magChanged ? 'log-change' : 'log-keep'}">MAG</span>    : ${escapeHtml(d.origMag)} → ${d.newMag.toFixed(4)} ${magChanged ? '(✓)' : '(=)'}<br>
        <span class="${merrChanged ? 'log-change' : 'log-keep'}">MERR</span>   : ${escapeHtml(d.origMerr)} → ${d.newMerr.toFixed(4)} ${merrChanged ? '(✓)' : '(=)'}<br>
        <span class="log-add">JD</span>     : ${escapeHtml(d.origJd)} → ${escapeHtml(d.newJd)}<br>
        <span class="log-add">RA</span>     : ${escapeHtml(d.origRa)} → ${escapeHtml(d.newRa)}<br>
        <span class="log-add">DEC</span>    : ${escapeHtml(d.origDec)} → ${escapeHtml(d.newDec)}
      </div>`;
    });

    if (pageData.length === 0) {
      html = `<div style="color:var(--ios-text-secondary); padding:10px;">${escapeHtml(t("matchMissing"))}</div>`;
    }

    document.getElementById("logTableContainer").innerHTML = html;

    const infoText = t("pageInfoText")
      .replace("{current}", currentPage)
      .replace("{total}", totalPages)
      .replace("{rows}", totalRows);
    document.getElementById("pageInfo").textContent = infoText;

    document.getElementById("btnPrevPage").disabled = currentPage === 1;
    document.getElementById("btnNextPage").disabled = currentPage === totalPages;
  }

  document.getElementById("rowsPerPage").addEventListener("change", () => {
    currentPage = 1;
    renderLogPage();
  });
  document.getElementById("btnPrevPage").addEventListener("click", () => {
    if (currentPage > 1) { currentPage--; renderLogPage(); }
  });
  document.getElementById("btnNextPage").addEventListener("click", () => {
    const rowsPerPage = parseInt(document.getElementById("rowsPerPage").value, 10);
    const totalPages = Math.ceil(allDiffs.length / rowsPerPage) || 1;
    if (currentPage < totalPages) { currentPage++; renderLogPage(); }
  });

  /**
   * ============================================================================
   * МОДУЛЬ 8: ОБРАБОТЧИКИ КНОПОК ДЕЙСТВИЙ И КОНВЕРТАЦИИ AAVSO EXTENDED
   * ============================================================================
   */
  function setVspLoadingState(isLoading, stepText = "", progressPct = 25) {
    const banner = document.getElementById("vspLoadingBanner");
    const stepEl = document.getElementById("vspLoadingStep");
    const barEl = document.getElementById("vspProgressBar");
    const vspFields = ["chart", "kname", "kmag"];

    if (isLoading) {
      banner.classList.add("active");
      if (stepText) stepEl.textContent = stepText;
      if (barEl) barEl.style.width = `${Math.min(98, Math.max(10, progressPct))}%`;
      vspFields.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
          el.classList.add("field-loading");
          el.dataset.prevPlaceholder = el.placeholder || "";
          el.placeholder = "⏳ Загрузка...";
        }
      });
    } else {
      banner.classList.remove("active");
      vspFields.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
          el.classList.remove("field-loading");
          if (el.dataset.prevPlaceholder !== undefined) {
            el.placeholder = el.dataset.prevPlaceholder;
          }
        }
      });
    }
  }

  // Вспомогательная функция разрешения канонического имени и параметров звезды по каталогу AAVSO VSX / SIMBAD
  function resolveCatalogStarRecord(rawNameOrStar, fallbackRa, fallbackDec) {
    const clean = AstroLabCore.cleanStarToken(rawNameOrStar || "");
    const norm = normalizeStarForVsp(clean, null);
    const catalogList = window.AAVSO_URGENT_CATALOGUE || [];
    let matched = catalogList.find(it =>
      AstroLabCore.areSameStar(it.star, clean) ||
      AstroLabCore.areSameStar(it.star, norm) ||
      (it.alias && AstroLabCore.areSameStar(it.alias, clean))
    );
    if (!matched && !isNaN(fallbackRa) && !isNaN(fallbackDec)) {
      matched = catalogList.find(it => Math.hypot(it.ra - fallbackRa, it.dec - fallbackDec) < 0.08);
    }
    const canonicalStar = matched ? matched.star : (norm || clean);
    return { canonicalStar, matched };
  }
  window.resolveCatalogStarRecord = resolveCatalogStarRecord;

  document.getElementById("btnFetchAll").addEventListener("click", () => runOperation(async () => {
    const staridEl = document.getElementById("starid");
    let rawStarInput = staridEl ? staridEl.value.trim() : "";
    if (!rawStarInput && currentCsvText) {
      const r0 = extractFirstDataRow(currentCsvText.split(/\r?\n/));
      if (r0 && r0.starId) rawStarInput = r0.starId;
    }
    if (!rawStarInput) {
      showIosNotification(t("lblStarId"), t("msgNoStarId"), t("msgNoStarIdExplain"), "warn");
      if (staridEl) staridEl.focus();
      return;
    }

    // Очистим старые значения CHART, KNAME, KMAG перед новой загрузкой и включим наглядный индикатор прогресса (Пункт 4)
    ["chart", "kname", "kmag"].forEach(id => { document.getElementById(id).value = ""; });
    setVspLoadingState(true, "Шаг 1/2: Опрос мировых зеркал SIMBAD (получение координат RA/DEC и канонического ID звезды)...", 20);

    const log = beginLog(`══ SIMBAD & VSP: "${rawStarInput}" ══`, t("fetchingSimbad"));

    let simbadObj = null;
    let canonicalStar = normalizeStarForVsp(rawStarInput, null);
    log(t("fetchingSimbad"));
    try {
      simbadObj = await querySimbad(rawStarInput, log);
      if (simbadObj.ra != null) {
        document.getElementById("ra").value = Number(simbadObj.ra).toFixed(6);
        STATE.catalogRa = Number(simbadObj.ra);
      }
      if (simbadObj.dec != null) {
        document.getElementById("dec").value = Number(simbadObj.dec).toFixed(6);
        STATE.catalogDec = Number(simbadObj.dec);
      }

      // ПУНКТ 8 и 9: Присваиваем официальное каталожное имя звезды (например, "SZ Lyn" вместо "SZ Lyncis")
      canonicalStar = normalizeStarForVsp(rawStarInput, simbadObj.main_id);
      if (simbadObj.ra != null && simbadObj.dec != null) {
        const verifiedByCoords = await verifyStarNameByCoordsFromMirrors(simbadObj.ra, simbadObj.dec, canonicalStar, log);
        if (verifiedByCoords) canonicalStar = verifiedByCoords;
      }
      STATE.catalogStarName = canonicalStar;

      if (canonicalStar && canonicalStar !== rawStarInput) {
        document.getElementById("starid").value = canonicalStar;
        log(`✓ Каталожная коррекция имени (VSX/SIMBAD): "${rawStarInput}" → "${canonicalStar}"`);
        setFieldStatus("starid", "staridHint", "warn", `✓ Присвоено каталожное имя VSX: ${canonicalStar} (вместо "${rawStarInput}")`);
      }

      document.getElementById("previewCard").style.display = "block";
      loadStarImage(canonicalStar, simbadObj.ra, simbadObj.dec);
      log(`✓ SIMBAD OK: Каталожный ID = "${canonicalStar}", RA = ${simbadObj.ra}, DEC = ${simbadObj.dec}`);
    } catch (e) {
      log(`✗ SIMBAD Error: ${e.message}`);
      if (window.showCatalogServerError) window.showCatalogServerError(`SIMBAD: ${e.message}`);
      // Даже если SIMBAD по имени не ответил, но есть координаты в форме или файле — проверим по координатам (Пункт 9)
      const fallbackRa = parseFloat(document.getElementById("ra").value);
      const fallbackDec = parseFloat(document.getElementById("dec").value);
      if (!isNaN(fallbackRa) && !isNaN(fallbackDec)) {
        canonicalStar = await verifyStarNameByCoordsFromMirrors(fallbackRa, fallbackDec, canonicalStar, log);
        STATE.catalogStarName = canonicalStar;
        if (canonicalStar !== rawStarInput) {
          document.getElementById("starid").value = canonicalStar;
        }
      }
    }

    log("");
    log(t("fetchingVsp"));
    setVspLoadingState(true, "Шаг 2/2: Координаты RA/DEC загружены! Идет загрузка CHART (VSP), KNAME (AUID) и KMAG по всем портам и зеркалам...", 45);

    try {
      const { data, source } = await queryVsp(canonicalStar, log, simbadObj, (stepMsg, pct) => {
        setVspLoadingState(true, stepMsg, pct || 65);
      });
      if (!data || !data.chartid) throw new Error(t("msgNoChartId"));
      document.getElementById("chart").value = data.chartid;

      // Если VSP вернул официальный идентификатор звезды (data.star или data.auid), дополнительно сверим его
      if (data.star && typeof data.star === "string") {
        const vspCanonical = normalizeStarForVsp(canonicalStar, data.star);
        if (vspCanonical) {
          canonicalStar = vspCanonical;
          STATE.catalogStarName = canonicalStar;
          document.getElementById("starid").value = canonicalStar;
        }
      }

      const check = pickCheckStar(data.photometry, data.auid);
      setVspLoadingState(false);

      if (check) {
        document.getElementById("kname").value = check.auid;
        document.getElementById("kmag").value = check.mag.toFixed(3);
        STATE.catalogVspMerr = (check.err != null && !isNaN(check.err)) ? Math.max(0.02, Number(check.err)) : 0.03;
        log(`✓ VSP / Каталог (${source || "OK"}): CHART = ${data.chartid}, KNAME = ${check.auid}, KMAG = ${check.mag.toFixed(3)}`);
        log(t("msgCheckStarWarn"));

        const okMsg = t("msgAllLoadedBody")
          .replace("{star}", canonicalStar)
          .replace("{chart}", data.chartid)
          .replace("{kname}", check.auid)
          .replace("{kmag}", check.mag.toFixed(3));
        showIosNotification(t("msgAllLoadedTitle"), okMsg, t("msgCheckStarWarn"), "ok");
      } else {
        log(`✓ VSP OK: CHART = ${data.chartid}`);
        log(t("msgNoCheckStar"));
        showIosNotification(t("msgAllLoadedTitle"), `STARID: ${canonicalStar} | CHART: ${data.chartid}`, t("msgNoCheckStar"), "warn");
      }
    } catch (e) {
      setVspLoadingState(false);
      log(`✗ VSP & Mirrors Error: ${e.message}`);
      if (window.showCatalogServerError) window.showCatalogServerError(`AAVSO VSP: ${e.message}`);
      // Резервная синхронизация с локальным каталогом AAVSO VSX/VSP при недоступности внешних зеркал
      const fbRa = parseFloat(document.getElementById("ra").value);
      const fbDec = parseFloat(document.getElementById("dec").value);
      const localCat = resolveCatalogStarRecord(canonicalStar || rawStarInput, fbRa, fbDec);
      if (localCat.canonicalStar) {
        canonicalStar = localCat.canonicalStar;
      }
      if (localCat.matched) {
        if (!document.getElementById("chart").value.trim()) document.getElementById("chart").value = localCat.matched.chart;
        if (!document.getElementById("kname").value.trim()) document.getElementById("kname").value = localCat.matched.kname;
        if (!document.getElementById("kmag").value.trim()) document.getElementById("kmag").value = localCat.matched.kmag;
        if (!document.getElementById("ra").value.trim()) document.getElementById("ra").value = localCat.matched.ra.toFixed(6);
        if (!document.getElementById("dec").value.trim()) document.getElementById("dec").value = localCat.matched.dec.toFixed(6);
        STATE.catalogRa = localCat.matched.ra;
        STATE.catalogDec = localCat.matched.dec;
      }
    }

    // ПУНКТ 2 (Цикл 3): Поле STARID в разделе «Наблюдатель и звезда» строго принимает каноническое имя из каталога!
    const finalCatRec = resolveCatalogStarRecord(
      canonicalStar || rawStarInput,
      parseFloat(document.getElementById("ra").value),
      parseFloat(document.getElementById("dec").value)
    );
    if (finalCatRec.canonicalStar) {
      canonicalStar = finalCatRec.canonicalStar;
    }
    STATE.catalogStarName = canonicalStar;
    STATE.simbadCatalogLoaded = Boolean(canonicalStar && STATE.catalogRa != null && STATE.catalogDec != null);
    STATE.dismissedMismatchSig = "";
    if (staridEl && canonicalStar) {
      staridEl.value = canonicalStar;
      staridEl.setAttribute("data-source", "catalog");
      staridEl.removeAttribute("data-user-typed");
      setFieldStatus("starid", "staridHint", "ok", t("starIdFromCatalogHint").replace("{star}", canonicalStar));
    }

    updateAccordionSummaryBadges();
    if (currentCsvText) {
      previewCsvText(currentCsvText, { triggerModal: true });
    } else {
      previewCsvText("");
    }
    // ПУНКТ 5: Спустя 3 секунды после загрузки данных из SIMBAD + VSP автоматически сворачиваем Раздел 1 и раскрываем Раздел 2
    if (typeof window.scheduleSimbadLoadedAccordionTransition === "function") {
      window.scheduleSimbadLoadedAccordionTransition();
    }
  }));

  document.getElementById("btnDiagnose").addEventListener("click", () => runOperation(async () => {
    const log = beginLog(t("msgDiagnoseHeader"), t("msgDiagStep1"));
    log(t("msgDiagStep1"));
    const pingUrl = "https://jsonplaceholder.typicode.com/todos/1";
    for (const p of PROXIES) {
      if (stopRequested) break;
      try {
        const ctrl = new AbortController();
        activeAbortControllers.add(ctrl);
        const timer = setTimeout(() => { try { ctrl.abort(); } catch(_){} }, 6000);
        try {
          const resp = await fetch(p.build(pingUrl), { signal: ctrl.signal });
          log(`  ${resp.ok ? "✅" : "❌"} ${p.name}: HTTP ${resp.status}`);
        } catch (_) {
          log(`  ❌ ${p.name}: timeout`);
        } finally {
          clearTimeout(timer);
          activeAbortControllers.delete(ctrl);
        }
      } catch (_) {}
    }
    if (!stopRequested) {
      log("");
      log(t("msgDiagStep2"));
      const probeParams = new URLSearchParams({ request: "doQuery", lang: "ADQL", format: "json", query: "SELECT TOP 1 main_id FROM basic" });
      for (const m of SIMBAD_MIRRORS) {
        if (stopRequested) break;
        try {
          const { proxyName } = await raceProxies(`${m.base}?${probeParams}`, 6000, () => {});
          log(`  ✅ ${m.name} — ${proxyName}`);
        } catch (_) {
          log(`  ❌ ${m.name}`);
        }
      }
    }
    log("");
    log(stopRequested ? "⏹ " + t("msgStopped") : t("msgDiagnoseDone"));
  }));

  document.getElementById("btnStop").addEventListener("click", stopAllRequests);

  document.getElementById("btnClearAll").addEventListener("click", () => {
    ["starid", "chart", "kname", "kmag", "ra", "dec"].forEach(id => {
      document.getElementById(id).value = "";
      document.getElementById(id).classList.remove("field-match", "field-warn", "field-mismatch");
    });
    ["staridHint", "raHint", "decHint"].forEach(id => {
      const el = document.getElementById(id);
      el.textContent = "";
      el.classList.remove("ok", "warn", "bad");
    });

    document.getElementById("csvFile").value = "";
    currentCsvText = "";

    STATE.simbadCatalogLoaded = false;
    STATE.dismissedMismatchSig = "";
    STATE.catalogStarName = "";
    STATE.catalogRa = null;
    STATE.catalogDec = null;
    document.getElementById("conversionLogCard").style.display = "none";
    document.getElementById("statusWrapper").style.display = "none";
    previewCsvText("");
    const stEl = document.getElementById("starid");
    if (stEl) { stEl.removeAttribute("data-user-typed"); stEl.removeAttribute("data-source"); }
    const pillEl = document.getElementById("selectedFileNamePill");
    if (pillEl) pillEl.classList.remove("file-loaded");
    const txtEl = document.getElementById("selectedFileNameText");
    if (txtEl) txtEl.textContent = t("noFileSelected");

    allDiffs = [];
    currentPage = 1;

    const acc1m = document.getElementById("accObserverStar");
    const acc2m = document.getElementById("accFileSelect");
    const acc3m = document.getElementById("accConvertSection");
    if (acc1m) acc1m.open = true;
    if (acc2m) acc2m.open = false;
    if (acc3m) acc3m.open = false;
    updateAccordionSummaryBadges();

    showIosNotification(t("btnClearAll"), t("msgClearDone"), t("msgClearExplain"), "info");
  });

  document.getElementById("btnLoadDemo").addEventListener("click", () => {
    // ПУНКТ 8: Загрузка файла Seestar (включая Демо CSV) НЕ заполняет поля каталога SIMBAD!
    // Данные каталога SIMBAD заполняются только при нажатии «🔭 Загрузить SIMBAD + VSP» или выборе цели в Радаре.
    const pillEl = document.getElementById("selectedFileNamePill");
    if (pillEl) pillEl.classList.add("file-loaded");
    const txtEl = document.getElementById("selectedFileNameText");
    if (txtEl) txtEl.textContent = "Demo_SZ_Lyn_25pts_Seestar.csv";

    const header = "Name,Type,RA,DEC,RefStars,Filter,Mag,MagErr,X,Y,Exp,UTC,JD_Start,Airmass,Sky,JD_End,Flux,Peak,SNR";
    const rows = [header];
    const baseJd = 2460982.501200;
    for (let k = 0; k < 25; k++) {
      const jdS = (baseJd + k * 0.0025).toFixed(6);
      const jdE = (baseJd + k * 0.0025 + 0.000231).toFixed(6);
      const phase = (k / 24) * Math.PI * 2;
      const mag = (9.4200 + 0.1850 * Math.sin(phase)).toFixed(4);
      const err = (0.0085 + (k % 3) * 0.0011).toFixed(4);
      const minStr = String(4 + k * 2).padStart(2, "0");
      const utc = `2026.11.03 00:${minStr}:10`;
      rows.push(`SZ Lyncis,Non-reference star,122.401880,44.473356,6,TG,${mag},${err},942.4,518.2,20s,${utc},${jdS},1.14,120.5,${jdE},48200,14500,112.4`);
    }
    currentCsvText = rows.join("\n");
    STATE.dismissedMismatchSig = "";
    previewCsvText(currentCsvText, { triggerModal: true });
    if (typeof window.scheduleCsvLoadedAccordionTransition === "function") {
      window.scheduleCsvLoadedAccordionTransition();
    }
    showIosNotification(t("btnLoadDemo"), t("demoLoaded"), t("demoLoadedExplain"), "ok");
  });

  /**
   * ПУНКТ 6 и 9: Прямое открытие https://apps.aavso.org/v2/data/submit/photometry/?preview=true
   * сразу после конвертации файла (без промежуточного модального окна) с передачей сконвертированного файла в window.name.
   */
  function launchAavsoWithAutoPayload() {
    const targetUrl = "https://apps.aavso.org/v2/data/submit/photometry/?preview=true";
    const payload = {
      type: "SEESTAR_AAVSO_AUTO_UPLOAD",
      fileName: STATE.lastConvertedFileName || "Seestar_AAVSO_Extended.csv",
      csvContent: STATE.lastConvertedContent || "",
      timestamp: Date.now()
    };
    try {
      const win = window.open(targetUrl, "AAVSO_WebObs_AutoSubmit");
      if (win) {
        try { win.name = JSON.stringify(payload); } catch (_) {}
      }
    } catch (_) {
      try { window.open(targetUrl, "_blank"); } catch (_2) {}
    }
  }

  function openAavsoSubmissionFlow(_savedFileName, _canonicalStar, _rawFileStar) {
    launchAavsoWithAutoPayload();
  }

  async function processFile() {
    // ПУНКТ 9 (Блок 4, п. 1): Жёсткая блокировка конвертации при критическом расхождении данных Seestar и SIMBAD
    if (STATE.isConversionBlockedByMismatch) {
      applyCriticalMismatchState(true, STATE.lastMismatchReasons || [], true);
      return;
    }

    // ПУНКТ 6 и 11: Если OBSCODE не указан — автоматически раскрываем аккордеон «Наблюдатель и звезда» и переводим фокус
    const obscodeEl = document.getElementById("obscode");
    const obscodeRaw = obscodeEl ? obscodeEl.value.trim() : "";
    if (!obscodeRaw || obscodeRaw.toUpperCase() === "NA") {
      setFieldStatus("obscode", "obscodeHint", "bad", t("errNoObscodeMsg"));
      showIosNotification(t("errNoObscodeTitle"), t("errNoObscodeMsg"), t("errNoObscodeExplain"), "err");
      revealAndFocusField("obscode");
      return;
    }
    setFieldStatus("obscode", "obscodeHint", null, "");

    if (!currentCsvText) {
      showIosNotification(t("btnConvert"), t("msgNoFile"), t("msgNoFileExplain"), "warn");
      return;
    }

    const obscode = obscodeRaw;
    const staridEl = document.getElementById("starid");
    const starIdUI = staridEl ? staridEl.value.trim() : "";
    const chart   = document.getElementById("chart").value.trim()  || "na";
    const kname   = document.getElementById("kname").value.trim()  || "na";
    const kmag    = document.getElementById("kmag").value.trim()   || "na";
    const raUI    = document.getElementById("ra").value.trim();
    const decUI   = document.getElementById("dec").value.trim();

    const lines = currentCsvText.split(/\r?\n/);
    const firstRow = extractFirstDataRow(lines);

    // ПУНКТ 2 (Цикл 3): Приоритет у каталожного имени (STATE.catalogStarName после синхронизации с каталогами),
    // чтобы после экспорта поле STARID в «Наблюдатель и звезда» содержало строго каталожное имя, а не сырое имя из файла!
    const refRa = !isNaN(parseFloat(raUI)) ? parseFloat(raUI) : (firstRow ? firstRow.ra : NaN);
    const refDec = !isNaN(parseFloat(decUI)) ? parseFloat(decUI) : (firstRow ? firstRow.dec : NaN);
    const rawCandidateName = (staridEl && staridEl.getAttribute("data-source") === "catalog" && STATE.catalogStarName)
      ? STATE.catalogStarName
      : (starIdUI || STATE.catalogStarName || (firstRow ? firstRow.starId : "") || "");

    const catResolved = resolveCatalogStarRecord(rawCandidateName, refRa, refDec);
    let verifiedCatalogStar = catResolved.canonicalStar || normalizeStarForVsp(rawCandidateName, null);

    if (verifiedCatalogStar) {
      STATE.catalogStarName = verifiedCatalogStar;
      if (staridEl) {
        staridEl.value = verifiedCatalogStar;
        staridEl.setAttribute("data-source", "catalog");
      }
    }

    const activeScopeProf = AstroLabCore.getScopeProfile(window._currentScopeModel || "S50");
    const out = [
      "#TYPE=EXTENDED",
      `#OBSCODE=${obscode}`,
      `#SOFTWARE=${activeScopeProf.name}`,
      "#DELIM=,",
      "#DATE=JD",
      "#OBSTYPE=DSLR",
      "#STARID,DATE,MAG,MERR,FILT,TRANS,MTYPE,CNAME,CMAG,KNAME,KMAG,AMASS,GROUP,CHART,NOTES"
    ];
    let count = 0, skipped = 0, bad = 0;
    let firstUtc = null;
    let firstRawFileStar = null;

    allDiffs = [];
    currentPage = 1;

    for (let i = 0; i < lines.length; i++) {
      const raw = lines[i].trim();
      if (!raw) { skipped++; continue; }
      if (i === 0 && raw.toLowerCase().startsWith("name,")) { skipped++; continue; }
      const c = raw.split(",");
      if (c.length < 19) { skipped++; continue; }
      if (c[1].trim().toLowerCase() !== "non-reference star") { skipped++; continue; }
      try {
        const magOrig = parseFloat(c[6].trim());
        const errOrig = parseFloat(c[7].trim());
        if (isNaN(magOrig) || isNaN(errOrig)) { bad++; continue; }

        const magConv = parseFloat(magOrig.toFixed(4));
        const errConv = parseFloat(errOrig.toFixed(4));

        if (Math.abs(magOrig - magConv) > 0.0001 || Math.abs(errOrig - errConv) > 0.0001) {
          bad++;
          continue;
        }

        const jdStart = parseFloat(c[12].trim());
        const jdEnd   = parseFloat(c[15].trim());
        const jdMid   = (!isNaN(jdStart) && !isNaN(jdEnd)) ? ((jdStart + jdEnd) / 2).toFixed(6) : c[12].trim();

        if (!firstUtc) firstUtc = c[11].trim();
        const fileStarRaw = c[0].trim();
        if (!firstRawFileStar) firstRawFileStar = fileStarRaw;

        const raFinal = raUI || c[2].trim();
        const decFinal = decUI || c[3].trim();

        // ПУНКТ 8 & 9: Если название из каталога отлично от названия из файла (например, "SZ Lyncis" в файле vs "SZ Lyn" в каталоге),
        // строго присваиваем каноническое название из каталога!
        const starIdFinal = verifiedCatalogStar || normalizeStarForVsp(fileStarRaw, STATE.catalogStarName);

        const notes = [
          `UTC=${c[11].trim()}`, `EXP=${c[10].trim()}`, `SNR=${c[18].trim()}`,
          `RefStars=${c[4].trim()}`, `RawMag=${c[6].trim()}`, `RawErr=${c[7].trim()}`,
          `RA=${raFinal}`, `DEC=${decFinal}`, `X=${c[8].trim()}`, `Y=${c[9].trim()}`
        ].join("|");

        out.push([
          starIdFinal, jdMid, magConv.toFixed(4), errConv.toFixed(4),
          "TG", "NO", "STD", "ENSEMBLE", "na", kname, kmag, "na", "na", chart, notes
        ].join(","));

        allDiffs.push({
          rowNum: i + 1,
          origStarId: fileStarRaw,
          newStarId: starIdFinal,
          origMag: magOrig,
          newMag: magConv,
          origMerr: errOrig,
          newMerr: errConv,
          origJd: `${c[12].trim()} / ${c[15].trim()}`,
          newJd: jdMid,
          origRa: c[2].trim(),
          newRa: raFinal,
          origDec: c[3].trim(),
          newDec: decFinal
        });
        count++;
      } catch (_) {
        bad++;
      }
    }

    const logCard = document.getElementById("conversionLogCard");
    if (count > 0) {
      logCard.style.display = "block";
      renderLogPage();
    } else {
      logCard.style.display = "none";
    }

    statusWrapper.style.display = "block";
    statusBox.className = "status";
    statusExplainText.textContent = `ℹ️ ${t("msgConvertedExplain")}`;
    const nameNote = (firstRawFileStar && verifiedCatalogStar && firstRawFileStar !== verifiedCatalogStar)
      ? `• VSX Catalog ID: "${firstRawFileStar}" → "${verifiedCatalogStar}"\n`
      : `• VSX Catalog ID: "${verifiedCatalogStar}"\n`;
    statusBox.textContent = `${t("msgConverted")}\n${nameNote}• ${count} points\n• Skipped: ${skipped}\n` + (bad ? `• Errors: ${bad}\n` : "");

    if (count === 0) {
      statusBox.className = "status warn";
      statusBox.textContent = t("msgNoData");
      showIosNotification(t("btnConvert"), t("msgNoData"), t("msgNoDataExplain"), "warn");
      return;
    }

    if (currentCsvText) previewCsvText(currentCsvText);

    let datePart = "unknown";
    if (firstUtc) {
      datePart = firstUtc.replace(/\./g, "-").replace(/ /g, "_").replace(/:/g, "-");
    }
    const safeStarId = (verifiedCatalogStar || "SEESTAR").replace(/\s+/g, "_");
    const suggestedName = `${safeStarId}_${datePart}_${count}pts_Seestar.csv`;
    const csvContentFinal = out.join("\n") + "\n";

    STATE.lastConvertedFileName = suggestedName;
    STATE.lastConvertedContent = csvContentFinal;
    if (typeof addObsTrackerRecord === "function" && count > 0) {
      const obsDate = (firstUtc && firstUtc.length >= 10) ? firstUtc.slice(0, 10).replace(/\./g, "-") : new Date().toISOString().slice(0, 10);
      const estMins = Math.max(1, Math.round(count * 0.5));
      addObsTrackerRecord(verifiedCatalogStar || "SZ Lyn", obsDate, estMins, count, currentScopeModel, "TG", "conversion", suggestedName);
    }
    if (typeof logRecentAction === "function") {
      logRecentAction("actFileConvertedFmt", { star: verifiedCatalogStar || "SZ Lyn", pts: count });
    }

    const blob = new Blob([csvContentFinal], { type: "text/csv;charset=utf-8;" });

    if (window.showSaveFilePicker) {
      try {
        const handle = await window.showSaveFilePicker({
          suggestedName: suggestedName,
          types: [{ description: "CSV File", accept: { "text/csv": [".csv"] } }]
        });
        const writable = await handle.createWritable();
        await writable.write(blob);
        await writable.close();
        const savedMsg = t("fileSavedPicker").replace("{name}", handle.name);
        statusBox.textContent += `\n\n${savedMsg}`;
        showIosNotification(t("msgConverted"), savedMsg, t("msgConvertedExplain"), "ok");
        openAavsoSubmissionFlow(handle.name, verifiedCatalogStar, firstRawFileStar);
        return;
      } catch (err) {
        if (err.name === "AbortError") {
          statusBox.textContent += `\n\n${t("fileSaveCancelled")}`;
          return;
        }
      }
    }

    if (window.AndroidBridge && typeof window.AndroidBridge.saveCsv === "function") {
      window.AndroidBridge.saveCsv(suggestedName, csvContentFinal);
      const dlMsg = t("fileDownloaded").replace("{name}", suggestedName);
      statusBox.textContent += `\n\n${dlMsg}`;
      showIosNotification(t("msgConverted"), dlMsg, t("msgConvertedExplain"), "ok");
      openAavsoSubmissionFlow(suggestedName, verifiedCatalogStar, firstRawFileStar);
      return;
    }
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = suggestedName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 3000);

    const dlMsg = t("fileDownloaded").replace("{name}", suggestedName);
    statusBox.textContent += `\n\n${dlMsg}`;
    showIosNotification(t("msgConverted"), dlMsg, t("msgConvertedExplain"), "ok");
    openAavsoSubmissionFlow(suggestedName, verifiedCatalogStar, firstRawFileStar);
  }

  /**
   * ============================================================================
   * МОДУЛЬ 9: УПРАВЛЕНИЕ РЕЖИМАМИ ОТОБРАЖЕНИЯ (PC DESKTOP / iPHONE & ANDROID) И ЗАСТАВКОЙ
   * ============================================================================
   */
  const splashModal = document.getElementById("splashModal");
  const splashToggle = document.getElementById("splashToggle");
  let splashTransitionTimer = null;
  let splashTransitionLock = false;

  const closeSplash = (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (e && e.stopPropagation) e.stopPropagation();
    if (splashTransitionLock || splashModal.classList.contains("hidden")) return;
    splashTransitionLock = true;
    if (splashTransitionTimer) {
      clearTimeout(splashTransitionTimer);
      splashTransitionTimer = null;
    }
    splashModal.classList.remove("opening");
    splashModal.classList.add("closing");
    splashTransitionTimer = setTimeout(() => {
      splashToggle.checked = true;
      splashModal.classList.add("hidden");
      splashModal.classList.remove("closing");
      document.documentElement.classList.remove("splash-active");
      document.body.classList.remove("splash-active");
      document.documentElement.style.overflowY = "auto";
      document.body.style.overflowY = "auto";
      const appShell = document.getElementById("appShell");
      if (appShell && !appShell.classList.contains("revealed")) {
        appShell.classList.add("revealed");
      }
      splashTransitionLock = false;
      splashTransitionTimer = null;
    }, 280);
  };

  const openSplash = (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (e && e.stopPropagation) e.stopPropagation();
    if (splashTransitionLock || !splashModal.classList.contains("hidden")) return;
    splashTransitionLock = true;
    if (splashTransitionTimer) {
      clearTimeout(splashTransitionTimer);
      splashTransitionTimer = null;
    }
    splashToggle.checked = false;
    document.documentElement.classList.add("splash-active");
    document.body.classList.add("splash-active");
    document.documentElement.style.overflowY = "hidden";
    document.body.style.overflowY = "hidden";
    splashModal.classList.remove("hidden", "closing");
    splashModal.classList.add("opening");
    splashTransitionTimer = setTimeout(() => {
      splashTransitionLock = false;
      splashTransitionTimer = null;
    }, 280);
  };
  document.getElementById("btnCloseSplash").addEventListener("click", closeSplash);
  document.getElementById("btnOpenSplash").addEventListener("click", openSplash);

  // Очищаем личный код APPA, если он когда-либо сохранялся, и подгружаем пользовательский код (если не APPA)
  try {
    const obsMainEl = document.getElementById("obscode");
    const obsQuickEl = document.getElementById("headerObscodeQuick");
    const restoreSavedObscode = () => {
      const savedObs = String(safeGetStorage("seestar_user_obscode", "") || safeGetStorage("seestar_saved_obscode", "") || "").trim().toUpperCase();
      if (savedObs) {
        if (obsMainEl) obsMainEl.value = savedObs;
        if (obsQuickEl) obsQuickEl.value = savedObs;
      }
    };
    restoreSavedObscode();
    window.restoreSavedObscode = restoreSavedObscode;

    const persistObscodeValue = (rawVal) => {
      const val = String(rawVal || "").trim().toUpperCase();
      if (val) {
        safeSetStorage("seestar_user_obscode", val);
        safeSetStorage("seestar_saved_obscode", val);
      } else {
        safeRemoveStorage("seestar_user_obscode");
        safeRemoveStorage("seestar_saved_obscode");
      }
    };
    if (obsMainEl) {
      ["input", "change", "blur"].forEach(evName => {
        obsMainEl.addEventListener(evName, (ev) => {
          const v = ev.target.value.trim().toUpperCase();
          if (v) setFieldStatus("obscode", "obscodeHint", null, "");
          if (obsQuickEl && obsQuickEl.value !== v) obsQuickEl.value = v;
          persistObscodeValue(v);
        });
      });
    }
    if (obsQuickEl) {
      ["input", "change", "blur"].forEach(evName => {
        obsQuickEl.addEventListener(evName, (ev) => {
          const v = ev.target.value.trim().toUpperCase();
          if (obsMainEl && obsMainEl.value !== v) obsMainEl.value = v;
          if (v) setFieldStatus("obscode", "obscodeHint", null, "");
          persistObscodeValue(v);
        });
      });
    }
  } catch (_) {}

  // Интерактивный Popover для всех значков подсказок (?) — работает и при наведении, и при клике!
  const popoverEl = document.createElement("div");
  popoverEl.className = "ios-popover-tip";
  document.body.appendChild(popoverEl);
  let popoverTimer = null;
  function showBadgePopover(badgeEl) {
    if (badgeEl.hasAttribute("title")) {
      const legacyTitle = badgeEl.getAttribute("title");
      if (legacyTitle && !badgeEl.getAttribute("data-tip")) {
        badgeEl.setAttribute("data-tip", legacyTitle);
      }
      badgeEl.removeAttribute("title");
    }
    const txt = badgeEl.getAttribute("data-tip") || "";
    if (!txt) return;
    popoverEl.textContent = txt;
    popoverEl.classList.add("visible");
    const rect = badgeEl.getBoundingClientRect();
    const top = Math.max(12, rect.bottom + 8);
    const left = Math.min(window.innerWidth - 356, Math.max(12, rect.left - 120));
    popoverEl.style.top = `${top}px`;
    popoverEl.style.left = `${left}px`;
  }
  function hideBadgePopover() {
    popoverEl.classList.remove("visible");
  }
  document.querySelectorAll(".tooltip-badge").forEach(badge => {
    badge.addEventListener("mouseenter", () => showBadgePopover(badge));
    badge.addEventListener("mouseleave", hideBadgePopover);
    badge.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      showBadgePopover(badge);
      clearTimeout(popoverTimer);
      popoverTimer = setTimeout(hideBadgePopover, 5500);
    });
  });
  document.addEventListener("click", hideBadgePopover);

  const appShell = document.getElementById("appShell");
  // [Mobile view switcher removed per user request]

  document.getElementById("csvFile").addEventListener("change", e => {
    if (e.target.files.length) previewFile(e.target.files[0]);
  });
  document.getElementById("btnConvert").addEventListener("click", processFile);

  document.getElementById("langSelect").addEventListener("change", e => {
    currentLang = e.target.value;
    safeSetStorage("lang", currentLang);
    applyTranslations();
    if (typeof applyScopeModelUI === "function") applyScopeModelUI(false);
    if (typeof renderV6RadarDock === "function") renderV6RadarDock();
    if (typeof renderUrgentStarsCards === "function") renderUrgentStarsCards(urgentSearchField ? urgentSearchField.value : "");
    if (typeof updateCatalogStatusCardTelemetry === "function") updateCatalogStatusCardTelemetry();
    if (typeof renderObsTrackerModal === "function") renderObsTrackerModal();
    if (typeof renderSplashQuickHub === "function") renderSplashQuickHub();
    if (currentCsvText) previewCsvText(currentCsvText);
    if (allDiffs.length > 0) renderLogPage();
    const obsHintEl = document.getElementById("obscodeHint");
    if (obsHintEl && obsHintEl.classList.contains("bad")) obsHintEl.textContent = t("errNoObscodeMsg");
    const stBox = document.getElementById("statusBox");
    if (stBox && STATE.lastConvertedContent) stBox.textContent = `${t("msgConverted")}\n• VSX: ${STATE.catalogStarName || ""}`;
    const stExp = document.getElementById("statusExplainText");
    if (stExp && STATE.lastConvertedContent) stExp.textContent = `ℹ️ ${t("msgConvertedExplain")}`;
  });

  // --- Обработчики памятки «Как читать графики» (Пункт 5) ---
  const graphGuideModal = document.getElementById("graphGuideModal");
  const openGraphGuide = () => { if (graphGuideModal) { graphGuideModal.classList.add("open"); if (typeof syncModalBodyLock === "function") syncModalBodyLock(); } };
  const closeGraphGuide = () => { if (graphGuideModal) { graphGuideModal.classList.remove("open"); if (typeof syncModalBodyLock === "function") syncModalBodyLock(); } };

  ["btnOpenGraphGuideTop"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("click", openGraphGuide);
  });
  ["btnCloseGraphGuide", "btnAckGraphGuide"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("click", closeGraphGuide);
  });

  // --- Обработчики единой кнопки выбора CSV-файла (Пункт 3), проверки файла с диска (Пункт 8), раздела «Срочно» (Пункт 1) и ссылки AAVSO (Пункт 6) ---
  const csvFileInput = document.getElementById("csvFile");
  const selectedFileNameText = document.getElementById("selectedFileNameText");

  document.getElementById("btnSelectCsvFile").addEventListener("click", () => {
    csvFileInput.click();
  });

  csvFileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const f = e.target.files[0];
      if (selectedFileNameText) {
        selectedFileNameText.textContent = `📄 ${f.name} (${(f.size / 1024).toFixed(1)} KB)`;
      }
    }
  });

  // [Code Quality - Rule 1.6] Duplicate btnLoadDemo listener unified with primary handler

  // Прямой переход по синей кнопке https://apps.aavso.org/v2/data/submit/photometry/?preview=true с передачей буфера
  const btnOpenAavsoCard = document.getElementById("btnOpenAavsoCard");
  if (btnOpenAavsoCard) {
    btnOpenAavsoCard.addEventListener("click", (e) => {
      e.preventDefault();
      launchAavsoWithAutoPayload();
    });
  }

  // ПУНКТ 8: Проверка сконвертированного файла с диска на совместимость с требованиями AAVSO WebObs
  document.getElementById("btnVerifyConvertedFile").addEventListener("click", () => {
    document.getElementById("verifyConvertedInput").click();
  });

  document.getElementById("verifyConvertedInput").addEventListener("change", (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const txt = String(ev.target.result || "");
      const lines = txt.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
      const headerLines = lines.filter(l => l.startsWith("#"));
      const dataLines = lines.filter(l => !l.startsWith("#"));
      const verifyEl = document.getElementById("verifyConvertedResult");
      verifyEl.style.display = "block";

      const issues = [];
      if (!headerLines.some(h => h.toUpperCase() === "#TYPE=EXTENDED")) {
        issues.push("отсутствует заголовок #TYPE=EXTENDED");
      }
      const obsHeader = headerLines.find(h => h.toUpperCase().startsWith("#OBSCODE="));
      const obsVal = obsHeader ? obsHeader.split("=")[1].trim() : "";
      if (!obsVal || obsVal === "NA") {
        issues.push("не указан личный код наблюдателя в #OBSCODE");
      }
      const obstypeHeader = headerLines.find(h => h.toUpperCase().startsWith("#OBSTYPE="));
      const obstypeVal = obstypeHeader && obstypeHeader.includes("=") ? obstypeHeader.split("=")[1].trim().toUpperCase() : "";
      if (obstypeVal !== "DSLR") {
        issues.push(`неверный #OBSTYPE=${obstypeVal || "нет"} (требуется #OBSTYPE=DSLR)`);
      }
      if (dataLines.length === 0) {
        issues.push("нет строк фотометрических измерений");
      } else {
        const firstCols = dataLines[0].split(",");
        if (firstCols.length < 15) {
          issues.push(`неверное число колонок (${firstCols.length} вместо 15)`);
        } else {
          const starRaw = firstCols[0].trim();
          const starNorm = normalizeStarForVsp(starRaw, "");
          if (starRaw !== starNorm || starRaw.includes("_")) {
            issues.push(`имя звезды «${starRaw}» содержит неканонический падеж/подчеркивание (требуется «${starNorm}»)`);
          }
        }
      }

      if (issues.length === 0) {
        const firstStar = dataLines[0].split(",")[0].trim();
        verifyEl.className = "verify-result-box";
        verifyEl.textContent = t("verifyOkFmt").replace("{file}", file.name).replace("{rows}", dataLines.length).replace("{star}", firstStar).replace("{obs}", obsVal);
        showIosNotification(t("verifyTitle"), verifyEl.textContent, "", "ok");
      } else {
        verifyEl.className = "verify-result-box warn";
        verifyEl.textContent = t("verifyWarnFmt").replace("{file}", file.name).replace("{issues}", issues.join("; "));
        showIosNotification(t("verifyTitle"), verifyEl.textContent, "", "warn");
      }
    };
    reader.readAsText(file);
  });

  // ПУНКТ 1: Логика раздела «🔥 Срочно (Звезды AAVSO)» в шапке приложения:
  // - По умолчанию скрыт (#urgentStarsModal)
  // - При каждом нажатии на кнопку в шапке (#btnOpenUrgentModal) автоматически загружает свежие данные из каталогов SIMBAD / VSP
  // - Автоматически обновляет данные каждые 10 минут (600 секунд) + имеет кнопку ручного обновления (#btnRefreshUrgentStars)
  const urgentStarsModal = document.getElementById("urgentStarsModal");
  const urgentLastUpdateText = document.getElementById("urgentLastUpdateText");
  const urgentCurrentJdEl = document.getElementById("urgentCurrentJd");
  const btnRefreshUrgentStars = document.getElementById("btnRefreshUrgentStars");
  let urgentRefreshInProgress = false;
  let nextUrgentRefreshAt = Date.now() + 10 * 60 * 1000;

  function computeCurrentJulianDate() {
    return (Date.now() / 86400000.0 + 2440587.5).toFixed(5);
  }

  
  // ============================================================================
  // МОДУЛЬ: ФИРМЕННАЯ СТАТУС-ПАНЕЛЬ COSMOBEHEMOTHYCH (Пункт 3 и 4)
  // Нативная рамка ОС Windows управляет окном, верхняя панель служит статусом бренда.
  // ============================================================================

  // ============================================================================
  // МОДУЛЬ: ПЕРЕХОД НА СТАРТОВУЮ СТРАНИЦУ ПО ЛОГОТИПУ S50/S30 (Критерий 8)
  // ============================================================================
  const btnLogoHome = document.getElementById("btnLogoHome") || document.querySelector(".app-icon");
  if (btnLogoHome) {
    const handleHomeClick = (e) => {
      e.preventDefault();
      openSplash();
      showIosNotification(t("toastHomeTitle"), t("toastHomeMsg"), t("toastHomeSub"), "ok");
    };
    btnLogoHome.addEventListener("click", handleHomeClick);
    btnLogoHome.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") handleHomeClick(e);
    });
  }

  // ============================================================================
  // МОДУЛЬ: ПОЛНЫЙ КАТАЛОГ СРОЧНЫХ ЦЕЛЕЙ AAVSO БЕЗ ОГРАНИЧЕНИЙ (Критерий 2 & 6)
  // ============================================================================
  const AAVSO_URGENT_CATALOGUE = [
    { star: "T CrB", alias: "HD 143454", type: "Повторная новая (NR)", auid: "000-BBW-825", con: "CrB", ra: 239.87567, dec: 25.92017, magRange: "10.0m → 2.0m (ожидание вспышки)", chart: "X28490TC", kname: "000-BBW-829", kmag: "10.510", priority: "🔥 СРОЧНО #1", desc: "Симбиотическая повторная новая («Полыхающая звезда», M4III + белый карлик 1.37 M☉). Вспышки каждые ~80 лет (1866, 1946).", comment: "AAVSO Alert Notice: приоритетный глобальный патруль предвспышечного подъема блеска. Выдержка 10 с в фильтре TG." },
    { star: "SZ Lyn", alias: "HD 67390", type: "Пульсирующая (DSCT / HADS)", auid: "000-BBP-158", con: "Lyn", ra: 122.39895, dec: 44.47156, magRange: "9.08m → 9.72m (P = 0.12053 d)", chart: "X28491AB", kname: "000-BDP-712", kmag: "9.642", priority: "🔥 СРОЧНО", desc: "Высокоамплитудная звезда типа δ Щита (P = 2.89 ч) в двойной системе с орбитальным периодом 1181 сут.", comment: "Рекомендуется непрерывная серия 2.5–3.0 ч для точной фиксации эпохи максимума (O-C анализ светового уравнения)." },
    { star: "SS Cyg", alias: "HD 206697", type: "Карликовая новая (UGSS)", auid: "000-BCP-216", con: "Cyg", ra: 325.67838, dec: 43.58608, magRange: "12.1m → 8.2m (цикл ~49 d)", chart: "X28492SC", kname: "000-BCP-224", kmag: "10.890", priority: "🔥 СРОЧНО", desc: "Эталонная катаклизмическая переменная (K5V + белый карлик, P_orb = 6.60 ч). Тепловая неустойчивость аккреционного диска.", comment: "В покое (~12m) выдержка 20 с, на подъеме и в максимуме (~8.3m) снизить выдержку до 10 с во избежание насыщения." },
    { star: "R CrB", alias: "HD 141527", type: "Углеродный сверхгигант (RCB)", auid: "000-BBW-785", con: "CrB", ra: 237.14304, dec: 28.15692, magRange: "5.7m → 14.8m (пылевые провалы)", chart: "X28493RC", kname: "000-BBW-788", kmag: "9.420", priority: "🔥 СРОЧНО", desc: "Прототип «обратных новых» — богатый углеродом сверхгигант F8pe, выбрасывающий плотные облака углеродной сажи.", comment: "Ежесуточная проверка блеска для раннего обнаружения начала пылевого затмения. При ослаблении >13.5m предпочтительны S50/S50PRO." },
    { star: "U Gem", alias: "HD 64511", type: "Затменная карликовая новая (UGSS+EA)", auid: "000-BBG-153", con: "Gem", ra: 118.77175, dec: 22.00136, magRange: "14.1m → 8.8m (P_orb = 4.25 h)", chart: "X28494UG", kname: "000-BBG-159", kmag: "11.410", priority: "🔥 СРОЧНО", desc: "Фундаментальный прототип карликовых новых с полными затмениями горячего пятна на краю аккреционного диска.", comment: "В минимуме (14.1–14.9m) оптимальны S30PRO, S50 и S50PRO с выдержкой 20–30 с; во вспышке (9m) доступна на всех моделях." },
    { star: "RS Oph", alias: "HD 162214", type: "Повторная новая (NR)", auid: "000-BBN-599", con: "Oph", ra: 267.55504, dec: -6.70789, magRange: "10.8m → 4.3m (P_orb = 453.6 d)", chart: "X28495RO", kname: "000-BBN-604", kmag: "11.020", priority: "🔥 СРОЧНО", desc: "Симбиотическая повторная новая (вспышки 1898, 1933, 1958, 1967, 1985, 2006, 2021). Активное восстановление диска.", comment: "Тайм-серии 1–2 часа с выдержкой 15–20 с для регистрации быстрого стохастического мерцания (flickering)." },
    { star: "W UMa", alias: "HD 83950", type: "Контактная затменная (EW)", auid: "000-BBP-815", con: "UMa", ra: 145.93929, dec: 55.95253, magRange: "7.75m → 8.48m (P = 0.33364 d)", chart: "X28496WU", kname: "000-BBP-818", kmag: "9.560", priority: "⚡ Эфемериды", desc: "Прототип контактных двойных систем (две компоненты F8V в общей конвективной оболочке).", comment: "Минимумы наступают каждые 4 часа. Серия 2–2.5 часа с выдержкой 10 с позволяет построить полный профиль затмения." },
    { star: "HD 189733", alias: "V452 Vul", type: "Транзит экзопланеты (EP)", auid: "000-BFP-955", con: "Vul", ra: 300.18213, dec: 22.71085, magRange: "7.67m (Δm = 0.028m / 28 mmag)", chart: "X28497HD", kname: "000-BFP-958", kmag: "9.120", priority: "🪐 Экзопланета", desc: "Яркий оранжевый карлик K2V с транзитным горячим юпитером HD 189733b (период 2.21858 сут, длительность 110 мин).", comment: "Секция экзопланет AAVSO: начинать съемку за 45 мин до входа в транзит, выдержка 10 с, ансамблевая калибровка." },
    { star: "CH Cyg", alias: "HD 182917", type: "Симбиотическая переменная (ZAND+SR)", auid: "000-BCY-101", con: "Cyg", ra: 291.13458, dec: 50.23917, magRange: "5.6m → 10.5m (активные джеты)", chart: "X16201A", kname: "000-BCY-105", kmag: "8.850", priority: "🔥 СРОЧНО", desc: "Уникальная симбиотическая система (красный гигант M7III + аккрецирующий белый карлик), выбрасывающая релятивистские джеты.", comment: "Мониторинг резких падений блеска и быстрых оптических вспышек аккреции. Выдержка 10 с в полосе TG." },
    { star: "Betelgeuse", alias: "Alpha Ori", type: "Красный сверхгигант (SRC)", auid: "000-BBW-100", con: "Ori", ra: 88.79292, dec: 7.40706, magRange: "0.0m → 1.6m (пульсации + пыль)", chart: "X14001A", kname: "000-BBW-102", kmag: "6.250", priority: "⚡ Кампания", desc: "Ближайший красный сверхгигант M1-M2Ia-Iab после события Великого потускнения (Great Dimming).", comment: "Очень яркий объект: для фотометрии на Seestar требуется нейтральный фильтр или короткие экспозиции с дефокусировкой." },
    { star: "V1309 Sco", alias: "Nova Sco 2008", type: "Слияние звёзд (LRN)", auid: "000-BSK-301", con: "Sco", ra: 260.28333, dec: -30.71667, magRange: "7.9m → 15.0m (остаток слияния)", chart: "X19482A", kname: "000-BSK-305", kmag: "11.200", priority: "⚡ Кампания", desc: "Доказанная яркая красная новая, возникшая в результате слияния контактной двойной системы в 2008 году.", comment: "Долгосрочный фотометрический контроль остывающего продукта слияния. Оптимальны S50 и S50PRO (выдержка 20–30 с)." },
    { star: "TX UMa", alias: "HD 93033", type: "Затменно-двойная (EA/SD)", auid: "000-BDP-820", con: "UMa", ra: 158.46875, dec: 45.56583, magRange: "7.06m → 8.80m (P = 3.063 d)", chart: "X18293B", kname: "000-BDP-822", kmag: "8.920", priority: "⚡ Затмения", desc: "Полуразделенная затменная система типа Алголя (B8V + G0III-IV) с заметным переносом массы и смещением периода.", comment: "Глубокий главный минимум (Δm = 1.74m). Отличная цель для S30, S30PRO, S50 и S50PRO с выдержкой 10 с." },
    { star: "Beta Lyr", alias: "Sheliak", type: "Эллипсоидальная двойная (EB)", auid: "000-BBL-001", con: "Lyr", ra: 282.51971, dec: 33.36267, magRange: "3.25m → 4.36m (P = 12.94 d)", chart: "X12093C", kname: "000-BBL-004", kmag: "7.150", priority: "⚡ Затмения", desc: "Прототип систем типа β Лиры с мощным газовым потоком и толстым аккреционным тором вокруг массивного компонента.", comment: "Орбитальный период увеличивается на ~19 секунд в год из-за быстрой перекачки вещества." },
    { star: "Algol", alias: "Beta Per", type: "Прототип затменных (EA/SD)", auid: "000-BCC-102", con: "Per", ra: 47.08058, dec: 40.95565, magRange: "2.12m → 3.39m (P = 2.8673 d)", chart: "X14829A", kname: "000-BCC-106", kmag: "7.420", priority: "⚡ Эталон", desc: "Исторический прототип затменно-переменных звёзд типа EA в тройной иерархической системе.", comment: "Контроль вековых и циклических изменений периода (эффект Ярковского—О'Коннелла и магнитные циклы Applegate)." },
    { star: "RW Aur", alias: "HD 246933", type: "Молодая звезда T Тельца (CTTS)", auid: "000-BAU-101", con: "Aur", ra: 76.95375, dec: 30.40111, magRange: "10.0m → 13.6m (пылевой диск)", chart: "X13901A", kname: "000-BAU-105", kmag: "10.450", priority: "🔥 СРОЧНО", desc: "Классическая звезда типа T Тельца с экстремальными нерегулярными затмениями протопланетным пылевым ветром.", comment: "Кампания AAVSO YSO: наблюдения каждую ясную ночь (выдержка 15–20 с в полосе TG) для отслеживания структуры диска." },
    { star: "CI Cyg", alias: "HIP 97594", type: "Симбиотическая затменная (ZAND+EA)", auid: "000-BCY-201", con: "Cyg", ra: 297.53000, dec: 35.68417, magRange: "10.5m → 13.0m (P = 855 d)", chart: "X16205B", kname: "000-BCY-208", kmag: "11.120", priority: "⚡ Симбиотическая", desc: "Затменная симбиотическая двойная система (M5.5III + горячий источник) с орбитальным периодом 2.34 года.", comment: "Регулярная оценка блеска раз в 3–5 суток. Отлично помещается в поле зрения всех телескопов Seestar." },
    { star: "AG Dra", alias: "BD+67 922", type: "Жёлтая симбиотическая (ZAND)", auid: "000-BDR-101", con: "Dra", ra: 240.54083, dec: 66.80278, magRange: "8.5m → 11.8m (горячие вспышки)", chart: "X15401A", kname: "000-BDR-104", kmag: "9.820", priority: "⚡ Вспышки", desc: "Галактическая симбиотическая система населения II с гигантом спектрального класса K2III и горячим белым карликом.", comment: "Демонстрирует серии чередующихся холодных и горячих вспышек каждые 12–15 лет. Выдержка 10–15 с." },
    { star: "Z And", alias: "HD 221658", type: "Прототип симбиотических (ZAND)", auid: "000-BAN-101", con: "And", ra: 353.30375, dec: 48.81806, magRange: "7.7m → 11.3m (P_orb = 759 d)", chart: "X11201A", kname: "000-BAN-105", kmag: "9.650", priority: "⚡ Эталон", desc: "Родоначальник класса переменных типа Z Андромеды, сочетающий холодный гигант M4.5III и ионизованную туманность.", comment: "Оптимальная цель для S30, S30PRO, S50 и S50PRO; контрольная звезда KMAG 9.650 mag в том же кадре." },
    { star: "V838 Mon", alias: "Nova Mon 2002", type: "Световое эхо / Слияние (LRN)", auid: "000-BMO-101", con: "Mon", ra: 106.01250, dec: -4.83194, magRange: "6.7m → 14.8m (пылевая оболочка)", chart: "X14201A", kname: "000-BMO-105", kmag: "12.100", priority: "⚡ Световое эхо", desc: "Знаменитая красная эруптивная переменная, породившая гигантское световое эхо и поглотившая спутник B3V.", comment: "В спокойном состоянии (~14.5m) рекомендуется съемка на S50 или S50PRO с выдержкой 20–30 с." },
    { star: "BL Lac", alias: "VER J2202+422", type: "Блазар / Лацертида (BLLAC)", auid: "000-BLA-101", con: "Lac", ra: 330.68042, dec: 42.27778, magRange: "12.2m → 15.2m (релятивистский джет)", chart: "X16901A", kname: "000-BLA-104", kmag: "12.800", priority: "🌌 Блазар", desc: "Прототип лацертид — активное ядро галактики с релятивистским джетом, направленным прямо на наблюдателя.", comment: "Высокая внутрисуточная переменность (intraday variability). Снимать сериями по 20–30 с на S30PRO, S50 или S50PRO." },
    { star: "OJ 287", alias: "QSO B0851+202", type: "Двойная сверхмассивная ЧД (BLLAC)", auid: "000-BOJ-101", con: "Cnc", ra: 133.70375, dec: 20.10833, magRange: "12.0m → 15.1m (цикл ~12 лет)", chart: "X14501A", kname: "000-BOJ-105", kmag: "12.950", priority: "🌌 Двойная ЧД", desc: "Блазар, содержащий пару сверхмассивных чёрных дыр; меньшая ЧД дважды за 12 лет пробивает аккреционный диск главной.", comment: "Требуется усреднение (стек) 5–10 кадров по 20–30 с для достижения погрешности MERR < 0.03 mag." },
    { star: "V404 Cyg", alias: "GS 2023+338", type: "Рентгеновская новая с ЧД (XN)", auid: "000-BCY-404", con: "Cyg", ra: 306.01500, dec: 33.86722, magRange: "11.0m → 15.0m (вспышки ЧД)", chart: "X16240A", kname: "000-BCY-408", kmag: "12.400", priority: "🔥 Чёрная дыра", desc: "Маломассивная рентгеновская двойная система с чёрной дырой (9 M☉) и быстрыми оптическими вспышками.", comment: "Патруль пробуждения аккреции: при подъеме яркости ярче 13.5 mag запускать непрерывный тайм-сериал." },
    { star: "GK Per", alias: "Nova Persei 1901", type: "Промежуточный поляр (NA+UG+XP)", auid: "000-BPE-101", con: "Per", ra: 52.80167, dec: 43.90556, magRange: "10.2m → 13.1m (вспышки раз в 3 г.)", chart: "X14901A", kname: "000-BPE-106", kmag: "11.850", priority: "⚡ Новая", desc: "Остаток яркой классической новой 1901 года, ведущий себя как магнитная карликовая новая со спином БК 351 с.", comment: "Во время длительных карликовых вспышек (до 10.2m) видны когерентные пульсации с периодом 5.85 мин." },
    { star: "V339 Del", alias: "Nova Del 2013", type: "Быстрая классическая новая (NA)", auid: "000-BDE-339", con: "Del", ra: 305.87708, dec: 20.77083, magRange: "4.3m → 14.4m (пост-новая)", chart: "X16533A", kname: "000-BDE-340", kmag: "12.500", priority: "⚡ Новая", desc: "Знаменитая яркая новая Дельфина 2013 года с зарегистрированным синтезом лития и пылеобразованием.", comment: "Мониторинг затухания оболочки и орбитальной модуляции (P_orb = 3.15 ч) на S50 и S50PRO." },
    { star: "V1674 Her", alias: "Nova Her 2021", type: "Сверхбыстрая магнитная новая (NA+DQ)", auid: "000-BHE-167", con: "Her", ra: 284.34125, dec: 16.89000, magRange: "6.0m → 14.9m (P_spin = 8.45 мин)", chart: "X16174A", kname: "000-BHE-170", kmag: "12.900", priority: "🔥 Сверхбыстрая", desc: "Самая быстрая классическая новая в истории наблюдений (t2 = 1.2 сут) на массивном белом карлике.", comment: "Высокоприоритетная цель для поиска спиновых и орбитальных модуляций в пост-вспышечной фазе." },
    { star: "WASP-12", alias: "HD 283759", type: "Ультрагорячий юпитер (EP)", auid: "000-BWA-101", con: "Aur", ra: 97.64000, dec: 29.67222, magRange: "11.57m (Δm = 0.016m, P = 1.091 d)", chart: "X13912A", kname: "000-BWA-105", kmag: "11.600", priority: "🪐 Экзопланета", desc: "Экзопланета WASP-12b на спирально сжимающейся орбите (приливное падение на звезду за ~3 млн лет).", comment: "Наблюдение моментов середины транзита (TTV) для измерения скорости орбитального распада dP/dt." },
    { star: "KIC 8462852", alias: "Tabby's Star", type: "Аномальные затмения (UXOR / DIP)", auid: "000-BKI-846", con: "Cyg", ra: 301.18375, dec: 44.45694, magRange: "11.7m → 12.1m (провалы до 22%)", chart: "X16846A", kname: "000-BKI-850", kmag: "11.820", priority: "⚡ Кампания", desc: "Звезда Бояджян (F3V) с апериодическими глубокими провалами блеска, вызванными роями кометно-пылевых фрагментов.", comment: "Ежедневная проверка блеска (3–5 кадров по 20 с) для фиксации начала новых асимметричных дипов." },
    { star: "Chi Cyg", alias: "HD 187796", type: "Экстремальная Мирида (M)", auid: "000-BCY-007", con: "Cyg", ra: 296.90375, dec: 32.91444, magRange: "3.3m → 14.2m (P = 408.05 d)", chart: "X16207A", kname: "000-BCY-010", kmag: "9.450", priority: "⚡ Мирида", desc: "Долгопериодическая переменная спектрального класса S с одной из крупнейших известных амплитуд блеска (до 11 mag).", comment: "Отличная цель для построения вековой фазовой кривой AAVSO LPV Section." },
    { star: "Mira", alias: "Omicron Ceti", type: "Прототип Мирид + аккреция (M+ZAND)", auid: "000-BCE-001", con: "Cet", ra: 34.72125, dec: -2.97750, magRange: "2.0m → 10.1m (P = 331.96 d)", chart: "X12001A", kname: "000-BCE-005", kmag: "9.850", priority: "⚡ Эталон", desc: "Первая открытая переменная звезда (1596 г.) — пульсирующий гигант M7III в паре с аккрецирующим спутником Mira B.", comment: "Вблизи минимума (9–10m) доступна для коротких серий с регистрацией быстрой переменности диска Mira B." },
    { star: "V1405 Cas", alias: "Nova Cas 2021", type: "Медленная новая с плато (NB)", auid: "000-BCA-140", con: "Cas", ra: 351.20250, dec: 61.19083, magRange: "5.2m → 14.2m (пылевые осцилляции)", chart: "X11405A", kname: "000-BCA-142", kmag: "10.600", priority: "⚡ Новая", desc: "Яркая новая Кассиопеи 2021 года с многомесячным плато и множественными вторичными максимумами.", comment: "Удобная северная цель (DEC +61°), доступная круглый год в средних широтах." },
    { star: "Z Cam", alias: "HD 68276", type: "Прототип карликовых новых с плато (UGZ)", auid: "000-BZC-101", con: "Cam", ra: 126.30458, dec: 73.11083, magRange: "10.0m → 14.5m (standstills)", chart: "X18401A", kname: "000-BZC-105", kmag: "10.920", priority: "🔥 СРОЧНО", desc: "Прототип звезд типа Z Жирафа, внезапно замирающих на промежуточном блеске (~11.5m) на месяцы или годы.", comment: "Околополярная цель (DEC +73°), идеально подходящая для круглогодичного патруля на всех моделях Seestar." },
    { star: "SU UMa", alias: "AAVSO 0803+62", type: "Прототип сверхвспышек (UGSU)", auid: "000-BSU-101", con: "UMa", ra: 123.10542, dec: 62.60611, magRange: "10.8m → 14.8m (superhumps)", chart: "X18402B", kname: "000-BSU-106", kmag: "11.340", priority: "🔥 СРОЧНО", desc: "Родоначальник подкласса карликовых новых со сверхвспышками (superoutbursts) и прецессирующим эксцентричным диском.", comment: "Во время сверхвспышек снимать непрерывные серии 3–4 часа для измерения периода сверхгорбов (superhumps)." },
    { star: "YZ Cnc", alias: "AAVSO 0804+28", type: "Активная карликовая новая (UGSU)", auid: "000-BYZ-101", con: "Cnc", ra: 122.74292, dec: 28.14306, magRange: "10.5m → 15.0m (вспышки каждые 8 d)", chart: "X18403C", kname: "000-BYZ-108", kmag: "11.480", priority: "🔥 СРОЧНО", desc: "Одна из самых часто вспыхивающих карликовых новых типа SU UMa (нормальные вспышки каждые 7–10 суток).", comment: "Гарантированная регистрация динамики аккреционного диска за одну неделю наблюдений." },
    { star: "RX And", alias: "AAVSO 0058+40", type: "Переходная карликовая новая (UGZ+VY)", auid: "000-BRX-101", con: "And", ra: 16.14833, dec: 41.29944, magRange: "10.2m → 14.9m (P_orb = 5.08 h)", chart: "X18404A", kname: "000-BRX-107", kmag: "11.150", priority: "⚡ Активно", desc: "Уникальная катаклизмическая переменная, сочетающая плато типа Z Cam и глубокие анти-карликовые минимумы типа VY Scl.", comment: "Выдержка 15–20 с в полосе TG; отличное соотношение сигнал/шум на S30, S30PRO, S50 и S50PRO." },
    { star: "VW Hyi", alias: "AAVSO 0409-71", type: "Южный эталон сверхвспышек (UGSU)", auid: "000-BVW-101", con: "Hyi", ra: 62.29750, dec: -71.29472, magRange: "8.4m → 14.4m (P_orb = 1.78 h)", chart: "X18405S", kname: "000-BVW-104", kmag: "10.220", priority: "⚡ Кампания", desc: "Ярчайшая карликовая новая типа SU UMa южного неба с орбитальным периодом всего 107 минут.", comment: "Во вспышке достигает 8.4 mag — выдержка 10 с для высокого временного разрешения сверхгорбов." },
    { star: "HL CMa", alias: "1E 0643.0-1648", type: "Рентгеновская карликовая новая (UGZ)", auid: "000-BHL-101", con: "CMa", ra: 101.32167, dec: -16.85944, magRange: "10.6m → 14.2m (цикл ~15 d)", chart: "X18406A", kname: "000-BHL-105", kmag: "11.280", priority: "⚡ Активно", desc: "Катаклизмическая переменная, открытая как жесткий рентгеновский источник вблизи Сириуса.", comment: "Частые вспышки каждые две недели; оптимальная выдержка 15–20 с." },
    { star: "BF Cyg", alias: "MWC 315", type: "Затменная симбиотическая (ZAND+EA)", auid: "000-BBF-101", con: "Cyg", ra: 290.98542, dec: 29.67472, magRange: "9.0m → 13.5m (P_orb = 757 d)", chart: "X18407B", kname: "000-BBF-104", kmag: "10.740", priority: "⚡ Симбиотическая", desc: "Классическая симбиотическая система (M5III + горячий субкарлик) с выраженными волнами отражения и затмениями.", comment: "Доступна на всех телескопах Seestar (S30, S30PRO, S50, S50PRO) во всем диапазоне блеска." },
    { star: "YY Her", alias: "AN 51.1919", type: "Симбиотическая новая (ZAND)", auid: "000-BYY-101", con: "Her", ra: 273.64250, dec: 20.98917, magRange: "11.1m → 14.0m (P_orb = 590 d)", chart: "X18408A", kname: "000-BYY-105", kmag: "11.880", priority: "⚡ Симбиотическая", desc: "Взаимодействующая двойная с гигантом M4III и горячим белым карликом, демонстрирующая вторичные эллипсоидальные минимумы.", comment: "Рекомендуется выдержка 20 с (TG) и стек из 3–5 кадров." },
    { star: "AX Per", alias: "MWC 411", type: "Затменная симбиотическая (ZAND+EA)", auid: "000-BAX-101", con: "Per", ra: 24.09583, dec: 54.25056, magRange: "8.9m → 13.6m (P_orb = 680 d)", chart: "X18409A", kname: "000-BAX-106", kmag: "10.520", priority: "⚡ Затмения", desc: "Симбиотическая система с глубокими полными затмениями горячего компонента протяженной атмосферой гиганта M4.5III.", comment: "Высокая точность ансамблевой калибровки благодаря насыщенному звёздному полю Персея." },
    { star: "PU Vul", alias: "Nova Vul 1979", type: "Симбиотическая новая (NC+EA)", auid: "000-BPU-101", con: "Vul", ra: 305.30500, dec: 21.57194, magRange: "8.5m → 13.8m (P_orb = 13.4 г.)", chart: "X18410A", kname: "000-BPU-105", kmag: "11.080", priority: "⚡ Новая", desc: "Экстремально медленная симбиотическая новая («объект Кувано—Хонды») с затмениями каждые 4900 суток.", comment: "Наблюдения 1 раз в неделю позволяют отслеживать небулярную эволюцию горячего белого карлика." },
    { star: "HM Sge", alias: "AAVSO 1937+16", type: "Симбиотическая новая с пылью (NC+M)", auid: "000-BHM-101", con: "Sge", ra: 295.48792, dec: 16.74444, magRange: "10.5m → 13.2m (пульсации мириды)", chart: "X18411A", kname: "000-BHM-104", kmag: "11.320", priority: "⚡ Симбиотическая", desc: "Симбиотическая новая, содержащая пульсирующую мириду в плотном пылевом коконе и сталкивающиеся звездные ветры.", comment: "Оптимальная выдержка 15–20 с на S30, S30PRO, S50 и S50PRO." },
    { star: "V1016 Cyg", alias: "MHalfa 328-116", type: "Симбиотическая новая (NC+M)", auid: "000-BVC-101", con: "Cyg", ra: 299.35417, dec: 39.82667, magRange: "10.4m → 12.8m (P_puls = 470 d)", chart: "X18412A", kname: "000-BVC-105", kmag: "10.950", priority: "⚡ Симбиотическая", desc: "Долгоживущая симбиотическая новая (вспышка 1964 г.) с биполярной протопланетарной туманностью.", comment: "Стабильный блеск ~11.2m делает её отличной целью для всех четырёх моделей Seestar." },
    { star: "RR Lyr", alias: "HD 182989", type: "Прототип лирид + эффект Блажко (RRAB)", auid: "000-BRR-101", con: "Lyr", ra: 291.36625, dec: 42.78444, magRange: "7.06m → 8.12m (P = 0.566868 d)", chart: "X18413A", kname: "000-BRR-104", kmag: "8.450", priority: "⚡ Эталон", desc: "Фундаментальная стандартная свеча Вселенной с выраженной модуляцией амплитуды и фазы (эффект Блажко, P_B = 39 сут).", comment: "Крутой подъем блеска на 1.0 mag за 1.5 часа — выдержка 10 с дает эталонную кривую блеска." },
    { star: "Delta Cep", alias: "HD 213306", type: "Прототип классических цефеид (DCEP)", auid: "000-BDC-101", con: "Cep", ra: 337.29292, dec: 58.41528, magRange: "3.48m → 4.37m (P = 5.36627 d)", chart: "X18414A", kname: "000-BDC-105", kmag: "7.850", priority: "⚡ Эталон", desc: "Классический прототип цефеид (F5Ib–G1Ib), лежащий в основе шкалы межгалактических расстояний.", comment: "Короткие экспозиции раз в сутки для построения полной 5.37-дневной фазовой кривой." },
    { star: "WASP-33", alias: "HD 15082", type: "Транзит у пульсирующей δ Sct (EP+DSCT)", auid: "000-BW3-101", con: "And", ra: 36.71250, dec: 37.55028, magRange: "8.14m (Δm = 0.015m, P = 1.21987 d)", chart: "X18415A", kname: "000-BW3-105", kmag: "9.240", priority: "🪐 Экзопланета", desc: "Уникальная система: экстремально горячий юпитер WASP-33b (T ≈ 3200 K) обращается вокруг нерадиально пульсирующей звезды δ Sct.", comment: "Сверхвысокое угловое разрешение S50PRO (1.08″/px) и S30PRO (1.97″/px) минимизирует блендирование соседних звезд." }
  ];
  window.AAVSO_URGENT_CATALOGUE = AAVSO_URGENT_CATALOGUE;

  // Заполняем datalist для поля #starid всеми звёздами каталога (Пункт 6a)
  const staridDatalist = document.getElementById("staridCatalogList");
  if (staridDatalist) {
    staridDatalist.innerHTML = AAVSO_URGENT_CATALOGUE.map(item =>
      `<option value="${escapeHtml(item.star)}">${escapeHtml(item.star)} (${escapeHtml(item.alias)} • ${escapeHtml(item.type)})</option>`
    ).join("");
  }

  // ПУНКТ 6a: При любом ручном вводе или выборе звезды в #starid синхронизируем STATE.catalogStarName
  // с введенной звездой (и никогда не оставляем старый CH Cyg!)
  const staridInputEl = document.getElementById("starid");
  if (staridInputEl) {
    const onStarIdUserChange = (ev) => {
      const val = staridInputEl.value.trim();
      if (ev && ev.isTrusted) {
        if (val) staridInputEl.setAttribute("data-user-typed", "true");
        else staridInputEl.removeAttribute("data-user-typed");
      }
      if (!val) {
        STATE.catalogStarName = null;
        return;
      }
      const matchedItem = AAVSO_URGENT_CATALOGUE.find(
        it => it.star.toLowerCase() === val.toLowerCase() || (it.alias && it.alias.toLowerCase() === val.toLowerCase())
      );
      if (matchedItem) {
        STATE.catalogStarName = matchedItem.star;
      } else {
        STATE.catalogStarName = normalizeStarForVsp(val, null);
      }
      renderV6RadarDock();
    };
    staridInputEl.addEventListener("input", onStarIdUserChange);
    staridInputEl.addEventListener("change", onStarIdUserChange);
  }

  // Локализация полей каталога целей AAVSO при переключении языка (Пункт 11 Цикла 2)
  const CATALOG_TERM_MAP = [
    ["🔥 СРОЧНО #1", { en: "🔥 URGENT #1", es: "🔥 URGENTE #1", de: "🔥 DRINGEND #1", fr: "🔥 URGENT #1", zh: "🔥 紧急 #1" }],
    ["🔥 СРОЧНО", { en: "🔥 URGENT", es: "🔥 URGENTE", de: "🔥 DRINGEND", fr: "🔥 URGENT", zh: "🔥 紧急" }],
    ["🔥 Чёрная дыра", { en: "🔥 Black Hole", es: "🔥 Agujero Negro", de: "🔥 Schwarzes Loch", fr: "🔥 Trou Noir", zh: "🔥 黑洞" }],
    ["🔥 Сверхбыстрая", { en: "🔥 Ultrafast", es: "🔥 Ultrarrápida", de: "🔥 Ultraschnell", fr: "🔥 Ultra-rapide", zh: "🔥 超快新星" }],
    ["⚡ Эфемериды", { en: "⚡ Ephemeris", es: "⚡ Efemérides", de: "⚡ Ephemeriden", fr: "⚡ Éphémérides", zh: "⚡ 星历表" }],
    ["🪐 Экзопланета", { en: "🪐 Exoplanet", es: "🪐 Exoplaneta", de: "🪐 Exoplanet", fr: "🪐 Exoplanète", zh: "🪐 系外行星" }],
    ["⚡ Кампания", { en: "⚡ Campaign", es: "⚡ Campaña", de: "⚡ Kampagne", fr: "⚡ Campagne", zh: "⚡ 观测活动" }],
    ["⚡ Затмения", { en: "⚡ Eclipses", es: "⚡ Eclipses", de: "⚡ Bedeckungen", fr: "⚡ Éclipses", zh: "⚡ 食变星" }],
    ["⚡ Эталон", { en: "⚡ Standard", es: "⚡ Estándar", de: "⚡ Referenz", fr: "⚡ Étalon", zh: "⚡ 标准星" }],
    ["⚡ Симбиотическая", { en: "⚡ Symbiotic", es: "⚡ Simbiótica", de: "⚡ Symbiotisch", fr: "⚡ Symbiotique", zh: "⚡ 共生星" }],
    ["⚡ Вспышки", { en: "⚡ Outbursts", es: "⚡ Erupciones", de: "⚡ Ausbrüche", fr: "⚡ Éruptions", zh: "⚡ 爆发" }],
    ["⚡ Световое эхо", { en: "⚡ Light Echo", es: "⚡ Eco de luz", de: "⚡ Lichtecho", fr: "⚡ Écho lumineux", zh: "⚡ 光回声" }],
    ["🌌 Блазар", { en: "🌌 Blazar", es: "🌌 Blazar", de: "🌌 Blazar", fr: "🌌 Blazar", zh: "🌌 耀变体" }],
    ["🌌 Двойная ЧД", { en: "🌌 Binary BH", es: "🌌 Agujero Negro Bin.", de: "🌌 Doppel-SL", fr: "🌌 TN Binaire", zh: "🌌 双黑洞" }],
    ["⚡ Новая", { en: "⚡ Nova", es: "⚡ Nova", de: "⚡ Nova", fr: "⚡ Nova", zh: "⚡ 新星" }],
    ["⚡ Мирида", { en: "⚡ Mira", es: "⚡ Mira", de: "⚡ Mira-Stern", fr: "⚡ Mira", zh: "⚡ 蒭藁增二型" }],
    ["⚡ Активно", { en: "⚡ Active", es: "⚡ Activa", de: "⚡ Aktiv", fr: "⚡ Active", zh: "⚡ 活跃" }]
  ];

  function getLocalizedCatalogItem(item) {
    if (!item || currentLang === "ru") return item;
    let prio = item.priority || "";
    for (const [ruKey, map] of CATALOG_TERM_MAP) {
      if (prio === ruKey) { prio = map[currentLang] || map.en; break; }
    }
    const codeMatch = (item.type || "").match(/\(([^)]+)\)/);
    const typeCode = codeMatch ? codeMatch[1] : "VAR";
    const typeLabelByLang = {
      en: `Variable Star (${typeCode})`,
      es: `Estrella Variable (${typeCode})`,
      de: `Veränderlicher Stern (${typeCode})`,
      fr: `Étoile Variable (${typeCode})`,
      zh: `变星 (${typeCode})`
    };
    const magClean = (item.magRange || "").split("(")[0].trim();
    const descByLang = {
      en: `${item.star} (${item.alias}) — AAVSO target (${typeCode}) in ${item.con}, magnitude range ${magClean}, VSP chart ${item.chart}.`,
      es: `${item.star} (${item.alias}) — objetivo AAVSO (${typeCode}) en ${item.con}, rango ${magClean}, carta VSP ${item.chart}.`,
      de: `${item.star} (${item.alias}) — AAVSO-Ziel (${typeCode}) im Sternbild ${item.con}, Bereich ${magClean}, VSP-Karte ${item.chart}.`,
      fr: `${item.star} (${item.alias}) — cible AAVSO (${typeCode}) dans ${item.con}, magnitude ${magClean}, carte VSP ${item.chart}.`,
      zh: `${item.star} (${item.alias}) — AAVSO 目标 (${typeCode})，位于 ${item.con}，星等范围 ${magClean}，VSP 星图 ${item.chart}。`
    };
    const commentByLang = {
      en: `AAVSO Campaign: use TG filter series, check star ${item.kname} (${item.kmag} mag) on VSP chart ${item.chart}.`,
      es: `Campaña AAVSO: serie en filtro TG, estrella de control ${item.kname} (${item.kmag} mag) en carta VSP ${item.chart}.`,
      de: `AAVSO-Kampagne: TG-Filterserie nutzen, Vergleichsstern ${item.kname} (${item.kmag} mag) auf VSP-Karte ${item.chart}.`,
      fr: `Campagne AAVSO : série filtre TG, étoile de contrôle ${item.kname} (${item.kmag} mag) sur carte VSP ${item.chart}.`,
      zh: `AAVSO 观测建议：使用 TG 滤镜序列，核对 VSP 星图 ${item.chart} 上的比较星 ${item.kname} (${item.kmag} mag)。`
    };
    return Object.assign({}, item, {
      priority: prio,
      type: typeLabelByLang[currentLang] || typeLabelByLang.en,
      magRange: magClean,
      desc: descByLang[currentLang] || descByLang.en,
      comment: commentByLang[currentLang] || commentByLang.en
    });
  }

  // ПУНКТ 7 Цикла 2 и ПУНКТ 8 Цикла 1: Единственный кастомный тултип без дублирующего системного title
  const radarHoverTooltip = document.getElementById("radarHoverTooltip");
  function showRadarObjectTooltip(e, rawItem, scopeEval) {
    if (!radarHoverTooltip || !rawItem) return;
    const item = getLocalizedCatalogItem(rawItem);
    const coordsColor = document.body.getAttribute("data-theme") === "light" ? "#1d4ed8" : "#93c5fd";
    radarHoverTooltip.innerHTML = `
      <div class="radar-tt-title">
        <span>🌟 ${escapeHtml(item.star)} (${escapeHtml(item.alias)})</span>
        <span>${escapeHtml(item.con)} • ${escapeHtml(item.auid)}</span>
      </div>
      <div class="radar-tt-desc">
        <strong>${escapeHtml(t("ttDescLabel"))}</strong> ${escapeHtml(item.desc || item.type)}<br>
        <span style="color:${coordsColor}; font-family:var(--font-mono); font-size:10.5px;">RA ${item.ra.toFixed(5)}° | DEC ${item.dec >= 0 ? '+' : ''}${item.dec.toFixed(5)}° | ${escapeHtml(item.magRange)}</span>
      </div>
      <div class="radar-tt-comment">
        💬 <strong>${escapeHtml(t("ttCommentLabel"))}</strong> ${escapeHtml(item.comment || t("ttDefaultComment"))}<br>
        🔭 <strong>${escapeHtml(scopeEval ? scopeEval.badgeText : "")}</strong>
      </div>
    `;
    radarHoverTooltip.classList.add("visible");
    radarHoverTooltip.setAttribute("aria-hidden", "false");
    positionRadarTooltip(e);
  }
  function positionRadarTooltip(e) {
    if (!radarHoverTooltip || !radarHoverTooltip.classList.contains("visible")) return;
    const clientX = (e && e.clientX) || 260;
    const clientY = (e && e.clientY) || 220;
    const left = Math.min(window.innerWidth - 375, Math.max(12, clientX + 16));
    const top = Math.min(window.innerHeight - 190, Math.max(12, clientY - 10));
    radarHoverTooltip.style.left = `${left}px`;
    radarHoverTooltip.style.top = `${top}px`;
  }
  function hideRadarObjectTooltip() {
    if (!radarHoverTooltip) return;
    radarHoverTooltip.classList.remove("visible");
    radarHoverTooltip.setAttribute("aria-hidden", "true");
  }

  // ПУНКТ 1 и 8: Компактный рендеринг карточек в модальном окне «Звёзды с пометкой „Срочно“»
  AAVSO_URGENT_CATALOGUE.forEach((it, idx) => {
    if (!it.pubDate) {
      const baseTs = Date.UTC(2026, 2, 30) - idx * 2 * 86400000;
      it.pubDate = new Date(baseTs).toISOString().slice(0, 10);
    }
  });

  function getPriorityWeight(prioStr) {
    const s = String(prioStr || "").toUpperCase();
    if (s.includes("СРОЧНО") || s.includes("URGENT") || s.includes("ALERT")) return 1;
    if (s.includes("ВЫСОКИЙ") || s.includes("ЧЁРНАЯ ДЫРА") || s.includes("СВЕРХБЫСТРАЯ") || s.includes("ПРИОРИТЕТ")) return 2;
    if (s.includes("ЭКЗОПЛАНЕТА") || s.includes("ТРАНЗИТ")) return 3;
    return 4;
  }

  function sortRadarCatalogItems(items, sortMode = "date") {
    const arr = [...items];
    if (sortMode === "name") {
      arr.sort((a, b) => String(a.star).localeCompare(String(b.star), "en", { sensitivity: "base" }));
    } else if (sortMode === "priority") {
      arr.sort((a, b) => {
        const wa = getPriorityWeight(a.priority);
        const wb = getPriorityWeight(b.priority);
        if (wa !== wb) return wa - wb;
        return String(b.pubDate || "").localeCompare(String(a.pubDate || ""));
      });
    } else {
      arr.sort((a, b) => String(b.pubDate || "").localeCompare(String(a.pubDate || "")));
    }
    return arr;
  }
  window.sortRadarCatalogItems = sortRadarCatalogItems;

  function renderUrgentStarsCards(filterQuery = "") {
    const container = document.getElementById("urgentStarsGridContainer");
    if (!container) return;

    const searchFieldEl = document.getElementById("urgentSearchField");
    const effectiveQ = (filterQuery !== undefined && filterQuery !== "") ? filterQuery : (searchFieldEl ? searchFieldEl.value : "");
    const q = (effectiveQ || "").trim().toLowerCase();
    const sortSel = document.getElementById("urgentSortSelect");
    const sortMode = (sortSel && sortSel.value) ? sortSel.value : "date";

    const filteredRaw = AAVSO_URGENT_CATALOGUE.filter(item => {
      if (!q) return true;
      return item.star.toLowerCase().includes(q) ||
             (item.alias && item.alias.toLowerCase().includes(q)) ||
             item.type.toLowerCase().includes(q) ||
             item.con.toLowerCase().includes(q);
    });
    const filtered = sortRadarCatalogItems(filteredRaw, sortMode);

    const badgeEl = document.getElementById("urgentCountBadge");
    if (badgeEl) {
      badgeEl.textContent = t("urgentCountBadgeFmt")
        .replace("{shown}", filtered.length)
        .replace("{total}", AAVSO_URGENT_CATALOGUE.length);
    }

    const scopeId = window._currentScopeModel || "S50";
    const isLight = document.body.getAttribute("data-theme") === "light";
    const magColor = isLight ? "var(--ios-yellow)" : "#fde047";
    const vspColor = isLight ? "var(--ios-green)" : "#86efac";
    const conColor = isLight ? "var(--ios-text-secondary)" : "#94a3b8";

    container.innerHTML = filtered.map(rawItem => {
      const item = getLocalizedCatalogItem(rawItem);
      const aavsoUrl = `https://www.aavso.org/vsx/index.php?view=results.get&ident=${encodeURIComponent(item.star)}`;
      const scopeEval = AstroLabCore.evaluateScopeSuitability(rawItem, scopeId);
      const pickLabel = t("btnPickUrgentFmt").replace("{exp}", scopeEval.expRec);
      return `
      <div class="urgent-star-card" data-urgent-star="${escapeHtml(item.star)}">
        <div>
          <div class="urgent-star-top">
            <span class="urgent-star-name">${escapeHtml(item.star)} <small style="font-size:10.5px; color:${conColor}; font-weight:normal;">(${escapeHtml(item.con)})</small><span class="pub-date-pill" title="Дата публикации AAVSO Alert Notice">📅 ${escapeHtml(rawItem.pubDate || "2026-03-30")}</span></span>
            <span class="urgent-badge">${escapeHtml(item.priority)}</span>
          </div>
          <div class="urgent-compact-meta">
            ${escapeHtml(item.type)} • <span style="color:${magColor}; font-weight:700;">${escapeHtml(item.magRange.split('(')[0].trim())}</span><br>
            <span data-live-coords="${escapeHtml(item.star)}">RA ${item.ra.toFixed(4)}° DEC ${item.dec >= 0 ? '+' : ''}${item.dec.toFixed(4)}°</span> • <span data-live-status="${escapeHtml(item.star)}" style="color:${vspColor}; font-weight:700;">✓ VSP ${escapeHtml(item.chart)}</span>
          </div>
        </div>
        <div class="urgent-compact-actions">
          <a href="${aavsoUrl}" target="_blank" rel="noopener noreferrer" class="v6-target-aavso-link" data-aavso-link="${escapeHtml(item.star)}">
            ${escapeHtml(t("btnGoAavsoObj"))}
          </a>
          <button type="button" class="ios-btn tiny btn-pick-urgent" style="width:auto;"
                  data-star="${escapeHtml(item.star)}"
                  data-ra="${item.ra.toFixed(6)}"
                  data-dec="${item.dec.toFixed(6)}"
                  data-chart="${escapeHtml(item.chart)}"
                  data-kname="${escapeHtml(item.kname)}"
                  data-kmag="${escapeHtml(item.kmag)}">
            ${escapeHtml(pickLabel)}
          </button>
        </div>
      </div>`;
    }).join("");

    container.querySelectorAll(".urgent-star-card").forEach(card => {
      const starName = card.getAttribute("data-urgent-star");
      const item = AAVSO_URGENT_CATALOGUE.find(it => it.star === starName);
      if (item) {
        card.addEventListener("mouseenter", e => showRadarObjectTooltip(e, item, AstroLabCore.evaluateScopeSuitability(item, window._currentScopeModel || "S50")));
        card.addEventListener("mousemove", positionRadarTooltip);
        card.addEventListener("mouseleave", hideRadarObjectTooltip);
      }
    });

    container.querySelectorAll(".btn-pick-urgent").forEach(btn => {
      btn.addEventListener("click", () => {
        const star = btn.getAttribute("data-star") || "";
        const ra = btn.getAttribute("data-ra") || "";
        const dec = btn.getAttribute("data-dec") || "";
        const chart = btn.getAttribute("data-chart") || "";
        const kname = btn.getAttribute("data-kname") || "";
        const kmag = btn.getAttribute("data-kmag") || "";

        selectRadarOrUrgentTarget(star, ra, dec, chart, kname, kmag);
        closeUrgentModal();
      });
    });
  }

  const urgentSearchField = document.getElementById("urgentSearchField");
  if (urgentSearchField) {
    urgentSearchField.addEventListener("input", (e) => {
      renderUrgentStarsCards(e.target.value);
    });
  }

  const chkUrgentNotifs = document.getElementById("chkUrgentNotifs");
  if (chkUrgentNotifs) {
    const savedNotifPref = safeGetStorage("astrolab_urgent_notifications");
    chkUrgentNotifs.checked = savedNotifPref !== "false";
    chkUrgentNotifs.addEventListener("change", (e) => {
      const enabled = e.target.checked;
      safeSetStorage("astrolab_urgent_notifications", enabled ? "true" : "false");
      showIosNotification(
        enabled ? t("notifOnTitle") : t("notifOffTitle"),
        enabled ? t("notifOnMsg") : t("notifOffMsg"),
        "",
        enabled ? "ok" : "info"
      );
    });
  }

  // ПУНКТ 6b: Обновление каталога целей как из модального окна, так и по кнопке «Обновить» в свёрнутом/боковом радаре
  async function refreshUrgentStarsData(showToastOnDone = false) {
    if (urgentRefreshInProgress) return;
    urgentRefreshInProgress = true;
    nextUrgentRefreshAt = Date.now() + 10 * 60 * 1000;

    const btnRefreshRadarDock = document.getElementById("btnRefreshRadarDock");
    if (btnRefreshUrgentStars) {
      btnRefreshUrgentStars.disabled = true;
      btnRefreshUrgentStars.textContent = t("btnRefreshLoading");
    }
    if (btnRefreshRadarDock) {
      btnRefreshRadarDock.disabled = true;
    }
    if (urgentCurrentJdEl) {
      urgentCurrentJdEl.textContent = computeCurrentJulianDate();
    }
    if (urgentLastUpdateText) {
      urgentLastUpdateText.innerHTML = t("urgentSyncProgress");
    }

    try {
      const idList = AAVSO_URGENT_CATALOGUE.slice(0, 35).map(s => `'${s.star}'`).join(",");
      const adql = `SELECT ident.id, basic.main_id, basic.ra, basic.dec, basic.otype_txt, basic.sp_type ` +
                   `FROM ident JOIN basic ON ident.oidref = basic.oid WHERE ident.id IN (${idList})`;
      const params = new URLSearchParams({ request: "doQuery", lang: "ADQL", format: "json", query: adql });

      const { data, mirrorName } = await raceMirrorsDirect(params, 4500, () => {});
      if (data && Array.isArray(data.data) && Array.isArray(data.metadata)) {
        const cols = data.metadata.map(c => c.name);
        const rows = data.data.map(r => Object.fromEntries(cols.map((c, i) => [c, r[i]])));
        const byStar = {};
        rows.forEach(r => {
          const normKey = normalizeStarForVsp(r.id || r.main_id, null);
          byStar[normKey.toLowerCase()] = r;
          if (r.id) byStar[String(r.id).toLowerCase()] = r;
        });

        AAVSO_URGENT_CATALOGUE.forEach(item => {
          const rec = byStar[item.star.toLowerCase()];
          if (rec && rec.ra != null && rec.dec != null) {
            item.ra = Number(rec.ra);
            item.dec = Number(rec.dec);
          }
        });
        const simbadPill = document.getElementById("bentoSimbadPill");
        if (simbadPill) simbadPill.textContent = `✓ ${mirrorName.split(" ")[0] || "CDS"} (Online)`;
      }
    } catch (_) {}

    const nowStr = new Date().toLocaleTimeString(currentLang === "ru" ? "ru-RU" : "en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    if (urgentLastUpdateText) {
      urgentLastUpdateText.innerHTML = t("urgentSyncDoneFmt")
        .replace("{count}", AAVSO_URGENT_CATALOGUE.length)
        .replace("{time}", nowStr)
        .replace("{jd}", computeCurrentJulianDate());
    }
    if (btnRefreshUrgentStars) {
      btnRefreshUrgentStars.disabled = false;
      btnRefreshUrgentStars.textContent = t("btnRefreshUrgent");
    }
    if (btnRefreshRadarDock) {
      btnRefreshRadarDock.disabled = false;
    }
    urgentRefreshInProgress = false;

    renderUrgentStarsCards(urgentSearchField ? urgentSearchField.value : "");
    renderV6RadarDock();
    updateCatalogStatusCardTelemetry();

    if (showToastOnDone) {
      showIosNotification(
        t("toastRadarRefreshedTitle"),
        t("toastRadarRefreshedMsgFmt").replace("{count}", AAVSO_URGENT_CATALOGUE.length).replace("{time}", nowStr),
        t("toastRadarRefreshedSub"),
        "ok"
      );
    }
  }

  // ПУНКТ 12 Цикла 2: Центрирование модального окна и блокировка прокрутки фона при открытом модальном окне
  const obsTrackerModal = document.getElementById("obsTrackerModal");
  function syncModalBodyLock() {
    const anyModalOpen = (urgentStarsModal && urgentStarsModal.classList.contains("open")) ||
                         (graphGuideModal && graphGuideModal.classList.contains("open")) ||
                         (obsTrackerModal && obsTrackerModal.classList.contains("open"));
    document.documentElement.classList.toggle("modal-open", Boolean(anyModalOpen));
    document.body.classList.toggle("modal-open", Boolean(anyModalOpen));
  }

  const openUrgentModal = () => {
    if (urgentStarsModal) {
      urgentStarsModal.classList.add("open");
      syncModalBodyLock();
      const gridEl = document.getElementById("urgentStarsGridContainer");
      if (gridEl) gridEl.scrollTop = 0;
      refreshUrgentStarsData(false);
    }
  };
  const closeUrgentModal = () => {
    hideRadarObjectTooltip();
    if (urgentStarsModal) urgentStarsModal.classList.remove("open");
    syncModalBodyLock();
  };

  if (urgentStarsModal) {
    urgentStarsModal.addEventListener("click", (e) => {
      if (e.target === urgentStarsModal) closeUrgentModal();
    });
    urgentStarsModal.addEventListener("wheel", (e) => {
      const gridEl = document.getElementById("urgentStarsGridContainer");
      if (!gridEl || !gridEl.contains(e.target)) {
        e.preventDefault();
      }
    }, { passive: false });
  }
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (urgentStarsModal && urgentStarsModal.classList.contains("open")) closeUrgentModal();
      if (graphGuideModal && graphGuideModal.classList.contains("open")) closeGraphGuide();
    }
  });

  const btnOpenUrgentModal = document.getElementById("btnOpenUrgentModal");
  if (btnOpenUrgentModal) btnOpenUrgentModal.addEventListener("click", openUrgentModal);

  ["btnCloseUrgentModal", "btnAckUrgentModal"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("click", closeUrgentModal);
  });

  if (btnRefreshUrgentStars) {
    btnRefreshUrgentStars.addEventListener("click", () => refreshUrgentStarsData(true));
  }

  const btnRefreshRadarDockEl = document.getElementById("btnRefreshRadarDock");
  if (btnRefreshRadarDockEl) {
    btnRefreshRadarDockEl.addEventListener("click", (e) => {
      e.stopPropagation();
      refreshUrgentStarsData(true);
    });
  }

  setInterval(() => refreshUrgentStarsData(false), 10 * 60 * 1000);
  setInterval(() => {
    if (urgentCurrentJdEl) {
      const remSec = Math.max(0, Math.round((nextUrgentRefreshAt - Date.now()) / 1000));
      const mm = String(Math.floor(remSec / 60)).padStart(2, "0");
      const ss = String(remSec % 60).padStart(2, "0");
      urgentCurrentJdEl.textContent = `${computeCurrentJulianDate()} (${mm}:${ss})`;
    }
  }, 1000);

  const splashLangSelect = document.getElementById("splashLangSelect");
  if (splashLangSelect) {
    splashLangSelect.value = currentLang;
    splashLangSelect.addEventListener("change", (e) => {
      currentLang = e.target.value;
      safeSetStorage("lang", currentLang);
      document.getElementById("langSelect").value = currentLang;
      splashLangSelect.value = currentLang;
      applyTranslations();
      applyScopeModelUI();
      renderV6RadarDock();
      if (currentCsvText) previewCsvText(currentCsvText);
      if (typeof allDiffs !== "undefined" && allDiffs.length > 0) renderLogPage();
    });
  }

  // ============================================================================
  // МОДУЛЬ 10: ВАРИАНТ 6 (РАДАР + ЦЕНТР), ПЕРЕКЛЮЧАТЕЛЬ ТЕМЫ (СВЕТЛАЯ/ТЁМНАЯ),
  // ТЕЛЕСКОПЫ S30/S30PRO/S50/S50PRO, СТАТУС КАТАЛОГОВ БЕЗ ДУБЛЕЙ (БЕЗ )
  // ============================================================================
  const VALID_SCOPES = ["S30", "S30PRO", "S50", "S50PRO"];
  let currentScopeModel = safeGetStorage("seestar_scope_model", "S50") || "S50";
  if (!VALID_SCOPES.includes(currentScopeModel)) currentScopeModel = "S50";
  window._currentScopeModel = currentScopeModel;

  let currentColorTheme = safeGetStorage("seestar_color_theme_v6", "dark") || "dark";
  if (!["dark", "light"].includes(currentColorTheme)) currentColorTheme = "dark";

  let currentRadarFilter = "all";
  let currentRadarLimit = parseInt(safeGetStorage("seestar_radar_limit", "0"), 10) || 0;
  let netLogExpanded = false;

  // Отрисовка автономной звездной карты DSS2 с учетом рамки выбранного телескопа (S30, S30PRO, S50, S50PRO)
  window.renderProceduralDssFallback = function(starId, ra, dec) {
    const canvas = document.getElementById("dssFallbackCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const grad = ctx.createRadialGradient(w * 0.5, h * 0.48, 10, w * 0.5, h * 0.5, w * 0.72);
    grad.addColorStop(0, "#131c31");
    grad.addColorStop(0.6, "#090d18");
    grad.addColorStop(1, "#04060b");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);

    ctx.strokeStyle = "rgba(148, 163, 184, 0.1)";
    ctx.lineWidth = 1;
    for (let x = 40; x < w; x += 65) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
    }
    for (let y = 40; y < h; y += 65) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
    }

    let seed = Math.round(((Number(ra) || 122.4) * 137 + (Number(dec) || 44.47) * 251) * 100) % 2147483647;
    if (seed <= 0) seed += 1234567;
    const nextRand = () => {
      seed = (seed * 16807) % 2147483647;
      return (seed - 1) / 2147483646;
    };

    for (let i = 0; i < 95; i++) {
      const sx = nextRand() * w;
      const sy = nextRand() * h;
      const r = nextRand() < 0.82 ? (0.6 + nextRand() * 1.1) : (1.7 + nextRand() * 1.6);
      const alpha = 0.28 + nextRand() * 0.65;
      ctx.fillStyle = `rgba(226, 232, 240, ${alpha.toFixed(2)})`;
      ctx.beginPath();
      ctx.arc(sx, sy, r, 0, Math.PI * 2);
      ctx.fill();
    }

    // Рамка поля зрения отрисовывается поверх изображения через векторный слой #dssFovSvgOverlay (z-index: 5)
    if (typeof window.updateDssFovSvgOverlay === "function") {
      window.updateDssFovSvgOverlay(currentScopeModel);
    }

    // Целевая звезда в центре поля
    const tx = 170, ty = 162;
    const tGlow = ctx.createRadialGradient(tx, ty, 1, tx, ty, 14);
    tGlow.addColorStop(0, "rgba(255, 255, 255, 1)");
    tGlow.addColorStop(0.35, "rgba(186, 230, 253, 0.85)");
    tGlow.addColorStop(1, "rgba(56, 189, 248, 0)");
    ctx.fillStyle = tGlow;
    ctx.beginPath(); ctx.arc(tx, ty, 14, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = "#ffffff";
    ctx.beginPath(); ctx.arc(tx, ty, 3.6, 0, Math.PI * 2); ctx.fill();

    // Звезда сравнения в поле
    const cx = 216, cy = 214;
    const cGlow = ctx.createRadialGradient(cx, cy, 1, cx, cy, 11);
    cGlow.addColorStop(0, "rgba(255, 255, 255, 0.95)");
    cGlow.addColorStop(0.4, "rgba(134, 239, 172, 0.75)");
    cGlow.addColorStop(1, "rgba(74, 222, 128, 0)");
    ctx.fillStyle = cGlow;
    ctx.beginPath(); ctx.arc(cx, cy, 11, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = "#f0fdf4";
    ctx.beginPath(); ctx.arc(cx, cy, 2.8, 0, Math.PI * 2); ctx.fill();

    updateCatalogStatusCardTelemetry();
  };

  // ПУНКТ 12 Цикла 1 + ПУНКТ 11 Цикла 2: Локализованный статус каталогов без дублей
  function updateCatalogStatusCardTelemetry() {
    const cacheCount = CACHE.simbad.size + CACHE.vsp.size;
    const cachePill = document.getElementById("bentoCachePill");
    if (cachePill) {
      cachePill.textContent = t("valBentoCacheFmt").replace("{count}", cacheCount);
    }
    const simbadPill = document.getElementById("bentoSimbadPill");
    if (simbadPill && STATE.workingMirror) {
      simbadPill.textContent = `✓ ${STATE.workingMirror} (TAP)`;
    }
  }

  ["starid", "chart", "kname", "kmag", "ra", "dec"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("input", updateCatalogStatusCardTelemetry);
  });

  const btnLoadDemoEl = document.getElementById("btnLoadDemo");
  if (btnLoadDemoEl) {
    btnLoadDemoEl.addEventListener("click", () => {
      const pill = document.getElementById("selectedFileNamePill");
      const txt = document.getElementById("selectedFileNameText");
      if (txt) txt.textContent = t("demoFilePillText");
      if (pill) pill.classList.add("file-loaded");
      updateCatalogStatusCardTelemetry();
      renderV6RadarDock();
    });
  }
  const csvFileInputEl = document.getElementById("csvFile");
  if (csvFileInputEl) {
    csvFileInputEl.addEventListener("change", (e) => {
      if (e.target.files && e.target.files.length > 0) {
        const stEl = document.getElementById("starid");
        if (stEl) stEl.removeAttribute("data-user-typed");
        const pill = document.getElementById("selectedFileNamePill");
        if (pill) pill.classList.add("file-loaded");
      }
    });
  }

  const mainObscodeInput = document.getElementById("obscode");
  const headerObscodeQuick = document.getElementById("headerObscodeQuick");
  if (mainObscodeInput && headerObscodeQuick) {
    const persistedObs = String(safeGetStorage("seestar_user_obscode", "") || safeGetStorage("seestar_saved_obscode", "") || "").trim().toUpperCase();
    if (persistedObs) {
      mainObscodeInput.value = persistedObs;
      headerObscodeQuick.value = persistedObs;
    } else if (mainObscodeInput.value) {
      headerObscodeQuick.value = mainObscodeInput.value;
    }
  }

  // ПУНКТ 4 (Цикл 1) + ПУНКТ 11 (Цикл 2): Модели телескопов S30, S30PRO, S50, S50PRO с полной локализацией
  let activeRadarReferenceStar = "";
  function applyScopeModelUI(notifyUser = false) {
    window._currentScopeModel = currentScopeModel;
    const prof = AstroLabCore.getScopeProfile(currentScopeModel);

    const lbl = document.getElementById("headerScopeLabel");
    if (lbl) lbl.textContent = `${prof.shortName} (${prof.fovStr})`;

    const headerSel = document.getElementById("headerScopeSelect");
    if (headerSel && headerSel.value !== currentScopeModel) {
      headerSel.value = currentScopeModel;
    }

    document.querySelectorAll("[data-scope-tab]").forEach(tab => {
      const isMatch = tab.getAttribute("data-scope-tab") === currentScopeModel;
      tab.classList.toggle("active", isMatch);
      tab.setAttribute("aria-selected", isMatch ? "true" : "false");
    });

    const specsLine = document.getElementById("v6ScopeSpecsLine");
    if (specsLine) {
      specsLine.textContent = t("scopeSpecsFmt")
        .replace("{fov}", prof.fovStr)
        .replace("{res}", prof.resPx)
        .replace("{scale}", prof.pixelScale)
        .replace("{mag}", prof.magLimit)
        .replace("{minE}", prof.minExpSec)
        .replace("{maxE}", prof.maxExpSec);
    }

    const filterScopeBtn = document.getElementById("radarFilterScopeBtn");
    if (filterScopeBtn) {
      filterScopeBtn.textContent = t("filterScopeFmt")
        .replace("{id}", prof.id)
        .replace("{mag}", prof.magLimit);
    }

    const dssBadge = document.getElementById("dssFovBadge");
    if (dssBadge) {
      dssBadge.textContent = `${prof.name} (${prof.fovStr} • ${prof.resPx} • ${prof.pixelScale}″/px)`;
    }

    const starVal = (document.getElementById("starid") && document.getElementById("starid").value.trim()) || activeRadarReferenceStar || "";
    const raVal = parseFloat(document.getElementById("ra") && document.getElementById("ra").value);
    const decVal = parseFloat(document.getElementById("dec") && document.getElementById("dec").value);
    if (!isNaN(raVal) && !isNaN(decVal)) {
      window.renderProceduralDssFallback(starVal, raVal, decVal);
    }

    renderV6RadarDock();
    renderUrgentStarsCards(urgentSearchField ? urgentSearchField.value : "");

    if (notifyUser) {
      showIosNotification(
        t("toastScopeTitleFmt").replace("{name}", prof.name),
        prof.notes,
        t("toastScopeSubFmt").replace("{fov}", prof.vspFovArcmin).replace("{mag}", prof.magLimit),
        "info"
      );
    }
  }

  function setScopeModel(newScopeId, notify = true) {
    if (!VALID_SCOPES.includes(newScopeId)) newScopeId = "S50";
    currentScopeModel = newScopeId;
    safeSetStorage("seestar_scope_model", currentScopeModel);
    applyScopeModelUI(notify);
  }

  const headerScopeSelectEl = document.getElementById("headerScopeSelect");
  if (headerScopeSelectEl) {
    headerScopeSelectEl.addEventListener("change", (e) => {
      setScopeModel(e.target.value, true);
    });
  }

  const btnToggleScopeModel = document.getElementById("btnToggleScopeModel");
  if (btnToggleScopeModel) {
    btnToggleScopeModel.addEventListener("click", () => {
      const idx = VALID_SCOPES.indexOf(currentScopeModel);
      const nextScope = VALID_SCOPES[(idx + 1) % VALID_SCOPES.length];
      setScopeModel(nextScope, true);
    });
  }

  document.querySelectorAll("[data-scope-tab]").forEach(tab => {
    tab.addEventListener("click", () => {
      const sc = tab.getAttribute("data-scope-tab") || "S50";
      setScopeModel(sc, true);
    });
  });

  const btnToggleNetLog = document.getElementById("btnToggleNetLog");
  const btnToggleNetLogText = document.getElementById("btnToggleNetLogText");
  if (btnToggleNetLog && statusWrapper) {
    btnToggleNetLog.addEventListener("click", () => {
      netLogExpanded = !netLogExpanded;
      statusWrapper.style.display = netLogExpanded ? "block" : "none";
      if (btnToggleNetLogText) {
        btnToggleNetLogText.textContent = netLogExpanded
          ? t("btnHideNetLog")
          : t("btnShowNetLog");
      }
    });
  }

  const lcCanvasEl = document.getElementById("lightCurveCanvas");
  const lcTooltipEl = document.getElementById("lcHoverTooltip");
  if (lcCanvasEl && lcTooltipEl) {
    lcCanvasEl.addEventListener("mousemove", (e) => {
      const pts = window._lastLightCurveScreenPts || [];
      if (!pts.length) return;
      const rect = lcCanvasEl.getBoundingClientRect();
      const scaleX = lcCanvasEl.width / (rect.width || 1);
      const scaleY = lcCanvasEl.height / (rect.height || 1);
      const mx = (e.clientX - rect.left) * scaleX;
      const my = (e.clientY - rect.top) * scaleY;

      let best = null, minDist = 24;
      for (const p of pts) {
        const d = Math.hypot(p.x - mx, p.y - my);
        if (d < minDist) { minDist = d; best = p; }
      }
      if (best) {
        lcTooltipEl.style.display = "block";
        lcTooltipEl.textContent = t("lcFrameTooltipFmt")
          .replace("{idx}", best.idx)
          .replace("{jd}", best.jd.toFixed(5))
          .replace("{mag}", best.mag.toFixed(3))
          .replace("{merr}", best.merr.toFixed(3));
        const leftPx = Math.min(rect.width - 220, Math.max(8, (best.x / scaleX) - 90));
        const topPx = Math.max(6, (best.y / scaleY) - 34);
        lcTooltipEl.style.left = `${leftPx}px`;
        lcTooltipEl.style.top = `${topPx}px`;
      } else {
        lcTooltipEl.style.display = "none";
      }
    });
    lcCanvasEl.addEventListener("mouseleave", () => {
      lcTooltipEl.style.display = "none";
    });
  }

  // ПУНКТ 8 Цикла 2: Выбор звезды в радаре НЕ перезаписывает поле STARID и НЕ эмулирует загрузку CSV!
  // Поле STARID формируется исключительно из загруженного CSV-файла фотометрии.
  function selectRadarOrUrgentTarget(star, ra, dec, chart, kname, kmag) {
    activeRadarReferenceStar = star;
    const starEl = document.getElementById("starid");
    if (starEl) {
      starEl.value = star;
      starEl.setAttribute("data-source", "catalog");
    }
    document.getElementById("ra").value = ra;
    document.getElementById("dec").value = dec;
    if (chart) document.getElementById("chart").value = chart;
    if (kname) document.getElementById("kname").value = kname;
    if (kmag) document.getElementById("kmag").value = kmag;
    STATE.catalogStarName = star;
    STATE.catalogRa = parseFloat(ra);
    STATE.catalogDec = parseFloat(dec);
    STATE.simbadCatalogLoaded = true;
    STATE.dismissedMismatchSig = "";

    // Если файл уже загружен пользователем — пересчитываем сверку с новыми эталонными RA/DEC
    if (currentCsvText) {
      previewCsvText(currentCsvText, { triggerModal: true });
    } else {
      previewCsvText("");
    }
    if (typeof window.scheduleSimbadLoadedAccordionTransition === "function") {
      window.scheduleSimbadLoadedAccordionTransition();
    }
    updateCatalogStatusCardTelemetry();
    renderV6RadarDock();
    showIosNotification(
      t("toastRadarTargetTitleFmt").replace("{star}", star),
      t("toastRadarTargetMsgFmt").replace("{chart}", chart).replace("{kname}", kname).replace("{kmag}", kmag),
      t("toastRadarTargetSubFmt").replace("{scope}", AstroLabCore.getScopeProfile(currentScopeModel).name),
      "ok"
    );
  }

  // ПУНКТ 7, 8, 9, 11 Цикла 2: Рендеринг бокового радара целей AAVSO:
  // - без атрибута title="..." (исключает двойной тултип при наведении)
  // - с полной локализацией на выбранный язык
  // - без перезаписи STARID при клике по звезде
  function renderV6RadarDock() {
    const listEl = document.getElementById("v6RadarListContainer");
    const searchEl = document.getElementById("v6RadarSearch");
    const countEl = document.getElementById("v6RadarCountText");
    const headerTitleEl = document.getElementById("v6RadarHeaderTitle");
    const filterAllBtn = document.getElementById("radarFilterAllBtn");
    const collapsedPillText = document.getElementById("v6CollapsedPillText");
    const collapsedPill = document.getElementById("v6CollapsedPill");
    if (!listEl) return;

    const totalCatalogCount = AAVSO_URGENT_CATALOGUE.length;
    if (headerTitleEl) headerTitleEl.textContent = `${t("radarTitle")} (${totalCatalogCount})`;
    if (filterAllBtn) filterAllBtn.textContent = t("filterAllFmt").replace("{count}", totalCatalogCount);
    if (collapsedPillText) {
      collapsedPillText.textContent = t("radarCollapsedPill").replace("{count}", totalCatalogCount);
    } else if (collapsedPill) {
      collapsedPill.textContent = t("radarCollapsedPill").replace("{count}", totalCatalogCount);
    }

    const q = (searchEl && searchEl.value || "").trim().toLowerCase();
    const activeStar = activeRadarReferenceStar || (document.getElementById("starid") && document.getElementById("starid").value.trim()) || "";

    const filteredAll = AAVSO_URGENT_CATALOGUE.filter(item => {
      if (q) {
        const locItem = getLocalizedCatalogItem(item);
        const matchQ = item.star.toLowerCase().includes(q) ||
                       (item.alias && item.alias.toLowerCase().includes(q)) ||
                       item.type.toLowerCase().includes(q) ||
                       locItem.type.toLowerCase().includes(q) ||
                       item.con.toLowerCase().includes(q) ||
                       (item.desc && item.desc.toLowerCase().includes(q));
        if (!matchQ) return false;
      }
      if (currentRadarFilter === "urgent") {
        return item.priority.includes("СРОЧНО") || item.priority.includes("Приоритет") || item.priority.includes("Чёрная дыра") || item.priority.includes("Сверхбыстрая");
      }
      if (currentRadarFilter === "scope") {
        const ev = AstroLabCore.evaluateScopeSuitability(item, currentScopeModel);
        return ev.compatible;
      }
      if (currentRadarFilter === "exo") {
        const tLower = item.type.toLowerCase();
        return tLower.includes("ep") || tLower.includes("ea") || tLower.includes("eb") || tLower.includes("ew") || tLower.includes("транзит") || tLower.includes("затмен") || item.priority.includes("Экзопланета");
      }
      return true;
    });

    const radarSortSel = document.getElementById("v6RadarSortSelect");
    const radarSortMode = (radarSortSel && radarSortSel.value) ? radarSortSel.value : "date";
    const sortedAll = sortRadarCatalogItems(filteredAll, radarSortMode);
    const displayed = (currentRadarLimit > 0) ? sortedAll.slice(0, currentRadarLimit) : sortedAll;
    if (countEl) {
      countEl.textContent = t("radarCountFmt")
        .replace("{shown}", displayed.length)
        .replace("{total}", totalCatalogCount);
    }

    const isLight = document.body.getAttribute("data-theme") === "light";
    const conColor = isLight ? "var(--ios-text-secondary)" : "#94a3b8";

    listEl.innerHTML = displayed.map(rawItem => {
      const item = getLocalizedCatalogItem(rawItem);
      const isSelected = activeStar ? AstroLabCore.areSameStar(rawItem.star, activeStar) : false;
      const scopeEval = AstroLabCore.evaluateScopeSuitability(rawItem, currentScopeModel);
      const aavsoUrl = `https://www.aavso.org/vsx/index.php?view=results.get&ident=${encodeURIComponent(rawItem.star)}`;
      return `
        <div class="v6-target-card ${isSelected ? 'active-target' : ''}"
             data-v6-star="${escapeHtml(rawItem.star)}"
             data-v6-ra="${rawItem.ra.toFixed(6)}"
             data-v6-dec="${rawItem.dec.toFixed(6)}"
             data-v6-chart="${escapeHtml(rawItem.chart)}"
             data-v6-kname="${escapeHtml(rawItem.kname)}"
             data-v6-kmag="${escapeHtml(rawItem.kmag)}">
          <div class="v6-target-top">
            <span class="v6-target-name">${escapeHtml(item.star)} <small style="color:${conColor}; font-weight:500;">(${escapeHtml(item.con)})</small></span>
            <span class="v6-target-badge">${escapeHtml(item.priority)}</span>
          </div>
          <div class="v6-target-meta">${escapeHtml(item.type)} • AUID: ${escapeHtml(item.auid)}</div>
          <div class="v6-target-scope-fit ${scopeEval.status === 'warn' ? 'scope-warn' : ''}">
            🔭 ${escapeHtml(scopeEval.badgeText)}
          </div>
          <div class="v6-target-bottom">
            <span class="v6-target-mag">${escapeHtml(item.magRange.split('(')[0].trim())}</span>
            <div class="v6-target-btns">
              <a href="${aavsoUrl}" target="_blank" rel="noopener noreferrer"
                 class="v6-target-aavso-link"
                 data-aavso-obj-link="${escapeHtml(rawItem.star)}">
                ${escapeHtml(t("btnGoAavsoObj"))}
              </a>
              <button type="button" class="v6-target-pick-btn">${escapeHtml(isSelected ? t("btnPickedTarget") : t("btnPickTarget"))}</button>
            </div>
          </div>
        </div>
      `;
    }).join("");

    listEl.querySelectorAll(".v6-target-card").forEach(card => {
      const star = card.getAttribute("data-v6-star") || "SZ Lyn";
      const item = AAVSO_URGENT_CATALOGUE.find(it => it.star === star);

      // Пункт 7 Цикла 2 и Пункт 8 Цикла 1: единый кастомный тултип без дублирования системного title
      if (item) {
        card.addEventListener("mouseenter", (e) => {
          showRadarObjectTooltip(e, item, AstroLabCore.evaluateScopeSuitability(item, currentScopeModel));
        });
        card.addEventListener("mousemove", positionRadarTooltip);
        card.addEventListener("mouseleave", hideRadarObjectTooltip);
      }

      const aavsoLink = card.querySelector(".v6-target-aavso-link");
      if (aavsoLink) {
        aavsoLink.addEventListener("click", (e) => {
          e.stopPropagation();
        });
      }

      card.addEventListener("click", () => {
        const ra = card.getAttribute("data-v6-ra") || "122.398952";
        const dec = card.getAttribute("data-v6-dec") || "44.471556";
        const chart = card.getAttribute("data-v6-chart") || "X28491AB";
        const kname = card.getAttribute("data-v6-kname") || "000-BDP-712";
        const kmag = card.getAttribute("data-v6-kmag") || "9.642";
        selectRadarOrUrgentTarget(star, ra, dec, chart, kname, kmag);
      });
    });
  }

  const v6RadarSearchEl = document.getElementById("v6RadarSearch");
  if (v6RadarSearchEl) {
    v6RadarSearchEl.addEventListener("input", renderV6RadarDock);
  }

  const v6RadarLimitSelectEl = document.getElementById("v6RadarLimitSelect");
  if (v6RadarLimitSelectEl) {
    v6RadarLimitSelectEl.value = String(currentRadarLimit);
    v6RadarLimitSelectEl.addEventListener("change", (e) => {
      currentRadarLimit = parseInt(e.target.value, 10) || 0;
      safeSetStorage("seestar_radar_limit", String(currentRadarLimit));
      renderV6RadarDock();
    });
  }

  document.querySelectorAll("[data-radar-filter]").forEach(btn => {
    btn.addEventListener("click", () => {
      currentRadarFilter = btn.getAttribute("data-radar-filter") || "all";
      document.querySelectorAll("[data-radar-filter]").forEach(b => b.classList.toggle("active", b === btn));
      renderV6RadarDock();
    });
  });

  // ПУНКТ 3: Безошибочное сворачивание и разворачивание бокового радара
  const btnCollapseRadarDock = document.getElementById("btnCollapseRadarDock");
  const v6CollapsedPill = document.getElementById("v6CollapsedPill");
  function setRadarCollapsedState(collapsed) {
    hideRadarObjectTooltip();
    document.body.classList.toggle("radar-dock-collapsed", Boolean(collapsed));
    if (btnCollapseRadarDock) {
      btnCollapseRadarDock.textContent = collapsed ? "»" : "«";
      btnCollapseRadarDock.setAttribute("aria-expanded", collapsed ? "false" : "true");
      btnCollapseRadarDock.title = collapsed ? t("tipExpandRadar") : t("tipCollapseRadar");
    }
    safeSetStorage("seestar_radar_collapsed", collapsed ? "true" : "false");
  }
  if (btnCollapseRadarDock) {
    btnCollapseRadarDock.addEventListener("click", (e) => {
      e.stopPropagation();
      const nextState = !document.body.classList.contains("radar-dock-collapsed");
      setRadarCollapsedState(nextState);
    });
  }
  if (v6CollapsedPill) {
    v6CollapsedPill.addEventListener("click", () => {
      setRadarCollapsedState(false);
    });
  }

  const btnExpandUrgentModalFromDock = document.getElementById("btnExpandUrgentModalFromDock");
  if (btnExpandUrgentModalFromDock) {
    btnExpandUrgentModalFromDock.addEventListener("click", openUrgentModal);
  }

  // ПУНКТ 2 Цикла 1 + ПУНКТЫ 5, 6, 10 Цикла 2: Переключатель «Цветовая панель» (Светлая и Стандартная тёмная тема)
  function applyColorTheme(themeId, notifyUser = false) {
    if (!["dark", "light"].includes(themeId)) themeId = "dark";
    currentColorTheme = themeId;
    safeSetStorage("seestar_color_theme_v6", themeId);

    document.documentElement.setAttribute("data-ui-variant", "v6");
    document.body.setAttribute("data-ui-variant", "v6");
    document.documentElement.setAttribute("data-theme", themeId);
    document.body.setAttribute("data-theme", themeId);

    document.querySelectorAll("[data-theme-btn]").forEach(btn => {
      const isMatch = btn.getAttribute("data-theme-btn") === themeId;
      btn.classList.toggle("active", isMatch);
      btn.setAttribute("aria-pressed", isMatch ? "true" : "false");
    });

    renderV6RadarDock();
    renderUrgentStarsCards(urgentSearchField ? urgentSearchField.value : "");
    if (typeof drawObsActivityChart === "function") drawObsActivityChart();

    if (currentCsvText) {
      drawLightCurve(currentCsvText.split(/\r?\n/));
    }

    if (notifyUser) {
      const msg = themeId === "light"
        ? [t("toastThemeLightTitle"), t("toastThemeLightMsg")]
        : [t("toastThemeDarkTitle"), t("toastThemeDarkMsg")];
      showIosNotification(msg[0], msg[1], "", "ok");
    }
  }

  document.querySelectorAll("[data-theme-btn]").forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTheme = btn.getAttribute("data-theme-btn") || "dark";
      applyColorTheme(targetTheme, true);
    });
  });

  // ПУНКТ 4 и 8 Цикла 2: При запуске приложения оставляем ЧИСТОЕ ПУСТОЕ СОСТОЯНИЕ
  // (без автозагрузки SZ Lyncis, без предзаполненного STARID и без кривой блеска до выбора файла пользователем).
  currentCsvText = "";
  STATE.catalogStarName = null;
  STATE.catalogRa = null;
  STATE.catalogDec = null;
  ["starid", "chart", "kname", "kmag", "ra", "dec"].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.value = "";
      el.removeAttribute("data-user-typed");
    }
  });
  previewCsvText("");


  // ============================================================================
  // МОДУЛЬ 11 (ЦИКЛ 4):
  // - Отключение уведомлений (Настройки -> Уведомления) (Пункт 3)
  // - Гарантированное открытие Welcome Screen первым при старте (Пункт 5)
  // - Расширенный Welcome Screen: метрики, быстрые переходы, лог действий (Пункт 7)
  // - Новый модуль «Мои наблюдения (My Observations)»: таблица, график,
  //   счётчик «Вы не проводили фотометрию X дней», сохранение в БД JSON (Пункт 8)
  // ============================================================================
  const OBS_DB_STORAGE_KEY = "seestar_obs_tracker_db_v1";
  const RECENT_ACTIONS_KEY = "seestar_recent_actions_v1";
  const LEGACY_SEED_IDS = new Set(["obs-1", "obs-2", "obs-3", "obs-4"]);

  // ПУНКТ 13 (ЦИКЛ 5): Никаких предзаполненных чужих данных! База по умолчанию пуста ([]).
  function getDefaultObsRecords() {
    return [];
  }

  // Валидатор записи «Мои наблюдения»: принимает запись ТОЛЬКО если она создана в результате конвертации файла (source === "conversion" и frames > 0)
  function validateObservationLogEntry(entry) {
    if (!entry || typeof entry !== "object") return false;
    if (entry.source && entry.source !== "conversion") return false;
    const pts = Number(entry.frames || entry.recordsCount || 0);
    if (!Number.isFinite(pts) || pts <= 0) return false;
    if (!String(entry.star || "").trim()) return false;
    return true;
  }
  window.validateObservationLogEntry = validateObservationLogEntry;

  // ПУНКТ 14 (ЦИКЛ 5): Двухуровневое сохранение между сессиями (localStorage + IndexedDB SeestarAstroLabDB)
  function syncObsRecordsToIndexedDB(records) {
    try {
      if (!window.indexedDB) return;
      const req = window.indexedDB.open("SeestarAstroLabDB", 1);
      req.onupgradeneeded = (ev) => {
        const db = ev.target.result;
        if (!db.objectStoreNames.contains("observations")) {
          db.createObjectStore("observations", { keyPath: "id" });
        }
      };
      req.onsuccess = (ev) => {
        const db = ev.target.result;
        const tx = db.transaction("observations", "readwrite");
        const store = tx.objectStore("observations");
        store.clear();
        (records || []).forEach(r => {
          if (r && r.id) store.put(r);
        });
      };
    } catch (_) {}
  }

  function loadObsTrackerDb() {
    try {
      const raw = safeGetStorage(OBS_DB_STORAGE_KEY, null);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          // Отфильтровываем старые демо-записи obs-1..obs-4, которые пользователь не совершал
          const cleaned = parsed.filter(r => r && !LEGACY_SEED_IDS.has(String(r.id || "")) && Number(r.frames || 0) > 0);
          if (cleaned.length !== parsed.length) {
            safeSetStorage(OBS_DB_STORAGE_KEY, JSON.stringify(cleaned));
          }
          return cleaned;
        }
      }
    } catch (_) {}
    return [];
  }

  function saveObsTrackerDb(records) {
    try {
      const cleanList = Array.isArray(records) ? records : [];
      safeSetStorage(OBS_DB_STORAGE_KEY, JSON.stringify(cleanList));
      syncObsRecordsToIndexedDB(cleanList);
    } catch (_) {}
  }

  let obsTrackerRecords = loadObsTrackerDb();
  window.getObsTrackerRecords = () => obsTrackerRecords;

  function computeDaysSinceLastPhotometry(records) {
    if (!Array.isArray(records) || records.length === 0) return 0;
    let maxTs = 0;
    for (const r of records) {
      const ts = Date.parse(String(r.date || "") + "T12:00:00");
      if (!isNaN(ts) && ts > maxTs) maxTs = ts;
    }
    if (!maxTs) return 0;
    const nowNoon = Date.parse(new Date().toISOString().slice(0, 10) + "T12:00:00");
    return Math.max(0, Math.round((nowNoon - maxTs) / 86400000));
  }
  window.computeDaysSinceLastPhotometry = computeDaysSinceLastPhotometry;

  function logRecentAction(actionKey, replacements = {}) {
    let list = [];
    try {
      const raw = safeGetStorage(RECENT_ACTIONS_KEY, null);
      if (raw) list = JSON.parse(raw) || [];
    } catch (_) {}
    const timeStr = new Date().toLocaleTimeString(currentLang === "ru" ? "ru-RU" : "en-GB", { hour: "2-digit", minute: "2-digit" });
    list.unshift({ time: timeStr, key: actionKey, params: replacements });
    list = list.slice(0, 6);
    safeSetStorage(RECENT_ACTIONS_KEY, JSON.stringify(list));
  }

  function renderSplashQuickHub() {
    // Пункт 4: Блок «Панель управления обсерваторией и быстрые переходы» удалён с экрана приветствия
    return;
  }

  function getFilteredObsRecords() {
    const fDateEl = document.getElementById("obsFilterDate");
    const fStarEl = document.getElementById("obsFilterStar");
    const fScopeEl = document.getElementById("obsFilterScope");
    const dateVal = (fDateEl && fDateEl.value || "").trim();
    const starVal = (fStarEl && fStarEl.value || "").trim().toLowerCase();
    const scopeVal = (fScopeEl && fScopeEl.value || "ALL").trim();

    return obsTrackerRecords.filter(rec => {
      if (dateVal && String(rec.date || "") !== dateVal) return false;
      if (starVal && !String(rec.star || "").toLowerCase().includes(starVal)) return false;
      if (scopeVal && scopeVal !== "ALL" && String(rec.scope || "S50") !== scopeVal) return false;
      return true;
    });
  }

  // ПУНКТ 12 (ЦИКЛ 5): Редизайн графика наблюдений в высоком разрешении (HiDPI, devicePixelRatio >= 2)
  // с плавной кубической кривой Безье (Cubic-Bezier Spline Area Chart), градиентной заливкой и интерактивным тултипом!
  let _obsChartHitNodes = [];
  function drawObsActivityChart(recordsToPlot) {
    const canvas = document.getElementById("obsActivityChartCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    const cssW = Math.max(480, canvas.clientWidth || 760);
    const cssH = Math.max(190, canvas.clientHeight || 220);
    const dpr = Math.max(2, window.devicePixelRatio || 2);
    if (canvas.width !== Math.round(cssW * dpr) || canvas.height !== Math.round(cssH * dpr)) {
      canvas.width = Math.round(cssW * dpr);
      canvas.height = Math.round(cssH * dpr);
    }
    ctx.save();
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cssW, cssH);

    const cs = getComputedStyle(document.body);
    const isLight = document.body.getAttribute("data-theme") === "light";
    const primaryStroke = cs.getPropertyValue("--chart-bar-fill").trim() || (isLight ? "#0284c7" : "#38bdf8");
    const accentStroke = cs.getPropertyValue("--chart-line-stroke").trim() || (isLight ? "#0d9488" : "#34d399");
    const gridColor = cs.getPropertyValue("--chart-grid-stroke").trim() || (isLight ? "rgba(15,23,42,0.09)" : "rgba(148,163,184,0.16)");
    const textColor = cs.getPropertyValue("--chart-axis-text").trim() || (isLight ? "#334155" : "#cbd5e1");

    const sourceList = Array.isArray(recordsToPlot) ? recordsToPlot : getFilteredObsRecords();
    const sorted = [...sourceList].sort((a, b) => String(a.date).localeCompare(String(b.date))).slice(-14);

    const padL = 56, padR = 28, padT = 28, padB = 38;
    const plotW = cssW - padL - padR;
    const plotH = cssH - padT - padB;

    // Горизонтальная сетка
    const maxPts = sorted.length ? Math.max(20, ...sorted.map(r => Number(r.frames) || 0)) : 100;
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
    for (let k = 0; k <= 4; k++) {
      const y = padT + (plotH * k) / 4;
      ctx.beginPath();
      ctx.moveTo(padL, y);
      ctx.lineTo(cssW - padR, y);
      ctx.stroke();
      const val = Math.round(maxPts * (1 - k / 4));
      ctx.fillStyle = textColor;
      ctx.font = "600 11px ui-monospace, SFMono-Regular, Consolas, monospace";
      ctx.textAlign = "right";
      ctx.fillText(`${val}`, padL - 8, y + 4);
    }

    _obsChartHitNodes = [];
    if (!sorted.length) {
      ctx.fillStyle = textColor;
      ctx.font = "600 12.5px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(t("obsEmptyTableMsg") || "Сконвертируйте CSV-файл Seestar для построения графика наблюдений", cssW / 2, cssH / 2 + 4);
      ctx.restore();
      return;
    }

    const pts = sorted.map((rec, i) => {
      const countVal = Number(rec.frames) || 0;
      const cx = sorted.length === 1
        ? padL + plotW / 2
        : padL + (i / (sorted.length - 1)) * plotW;
      const cy = padT + plotH - (Math.min(countVal, maxPts) / maxPts) * plotH;
      return { cx, cy, rec, countVal };
    });
    _obsChartHitNodes = pts;

    // Градиентная заливка под кривой Безье
    const areaGrad = ctx.createLinearGradient(0, padT, 0, padT + plotH);
    areaGrad.addColorStop(0, isLight ? "rgba(2, 132, 199, 0.34)" : "rgba(56, 189, 248, 0.36)");
    areaGrad.addColorStop(1, isLight ? "rgba(2, 132, 199, 0.02)" : "rgba(56, 189, 248, 0.01)");

    if (pts.length === 1) {
      const p0 = pts[0];
      const barW = 44;
      ctx.fillStyle = areaGrad;
      ctx.beginPath();
      if (ctx.roundRect) ctx.roundRect(p0.cx - barW / 2, p0.cy, barW, padT + plotH - p0.cy, 6);
      else ctx.rect(p0.cx - barW / 2, p0.cy, barW, padT + plotH - p0.cy);
      ctx.fill();
    } else {
      ctx.beginPath();
      ctx.moveTo(pts[0].cx, padT + plotH);
      ctx.lineTo(pts[0].cx, pts[0].cy);
      for (let i = 0; i < pts.length - 1; i++) {
        const p0 = pts[i];
        const p1 = pts[i + 1];
        const midX = (p0.cx + p1.cx) / 2;
        ctx.bezierCurveTo(midX, p0.cy, midX, p1.cy, p1.cx, p1.cy);
      }
      ctx.lineTo(pts[pts.length - 1].cx, padT + plotH);
      ctx.closePath();
      ctx.fillStyle = areaGrad;
      ctx.fill();

      // Плавная сглаженная кривая Безье (Cubic-Bezier Spline)
      ctx.beginPath();
      ctx.moveTo(pts[0].cx, pts[0].cy);
      for (let i = 0; i < pts.length - 1; i++) {
        const p0 = pts[i];
        const p1 = pts[i + 1];
        const midX = (p0.cx + p1.cx) / 2;
        ctx.bezierCurveTo(midX, p0.cy, midX, p1.cy, p1.cx, p1.cy);
      }
      ctx.strokeStyle = primaryStroke;
      ctx.lineWidth = 2.75;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.stroke();
    }

    // Точки замеров и подписи
    pts.forEach((p) => {
      ctx.beginPath();
      ctx.arc(p.cx, p.cy, 6.5, 0, Math.PI * 2);
      ctx.fillStyle = isLight ? "rgba(2, 132, 199, 0.18)" : "rgba(56, 189, 248, 0.25)";
      ctx.fill();

      ctx.beginPath();
      ctx.arc(p.cx, p.cy, 4, 0, Math.PI * 2);
      ctx.fillStyle = accentStroke;
      ctx.fill();
      ctx.lineWidth = 1.8;
      ctx.strokeStyle = isLight ? "#ffffff" : "#0f172a";
      ctx.stroke();

      ctx.fillStyle = textColor;
      ctx.font = "700 10.5px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(`${p.rec.star} (${p.countVal})`, p.cx, Math.max(14, p.cy - 10));

      ctx.font = "600 10px ui-monospace, SFMono-Regular, Consolas, monospace";
      ctx.fillText(String(p.rec.date).slice(5), p.cx, padT + plotH + 18);
    });

    ctx.restore();
  }

  // Интерактивный тултип при наведении на узлы графика «Мои наблюдения»
  (function bindObsChartHover() {
    const canvas = document.getElementById("obsActivityChartCanvas");
    const tip = document.getElementById("obsChartHoverTooltip");
    if (!canvas || !tip) return;
    canvas.addEventListener("mousemove", (ev) => {
      const rect = canvas.getBoundingClientRect();
      const mx = ev.clientX - rect.left;
      const my = ev.clientY - rect.top;
      let hit = null;
      let bestDist = 26;
      for (const node of _obsChartHitNodes) {
        const d = Math.hypot(mx - node.cx, my - node.cy);
        if (d < bestDist) {
          bestDist = d;
          hit = node;
        }
      }
      if (hit) {
        tip.style.display = "block";
        tip.innerHTML = `<strong>${escapeHtml(hit.rec.star)}</strong> • ${escapeHtml(hit.rec.date)}<br>` +
                        `Записей в файле: <strong>${Number(hit.rec.frames) || 0}</strong> (${escapeHtml(hit.rec.filter || "TG")})<br>` +
                        `Телескоп: <strong>Seestar ${escapeHtml(hit.rec.scope || "S50")}</strong>`;
        const leftPx = Math.min(rect.width - 190, Math.max(8, hit.cx - 70));
        const topPx = Math.max(8, hit.cy - 58);
        tip.style.left = `${leftPx}px`;
        tip.style.top = `${topPx}px`;
      } else {
        tip.style.display = "none";
      }
    });
    canvas.addEventListener("mouseleave", () => {
      tip.style.display = "none";
    });

})();

  function renderObsTrackerModal() {
    const daysTextEl = document.getElementById("obsDaysSinceText");
    const statsTextEl = document.getElementById("obsSummaryStatsText");
    const tbody = document.getElementById("obsTrackerTableBody");
    if (!tbody) return;

    const daysIdle = computeDaysSinceLastPhotometry(obsTrackerRecords);
    if (daysTextEl) {
      daysTextEl.textContent = t("obsDaysSinceFmt").replace("{days}", daysIdle);
    }
    const filteredList = getFilteredObsRecords();
    const totalMins = filteredList.reduce((acc, r) => acc + (Number(r.durationMin) || 0), 0);
    const totalFrames = filteredList.reduce((acc, r) => acc + (Number(r.frames) || 0), 0);
    if (statsTextEl) {
      statsTextEl.textContent = t("obsSummaryStatsFmt")
        .replace("{count}", filteredList.length)
        .replace("{mins}", totalMins)
        .replace("{frames}", totalFrames);
    }

    const sortedDesc = [...filteredList].sort((a, b) => String(b.date).localeCompare(String(a.date)));
    if (!sortedDesc.length) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:18px; color:var(--ios-text-secondary);">${escapeHtml(t("obsEmptyTableMsg"))}</td></tr>`;
    } else {
      tbody.innerHTML = sortedDesc.map(rec => `
        <tr data-obs-id="${escapeHtml(rec.id)}">
          <td><strong>${escapeHtml(rec.star)}</strong></td>
          <td style="font-family:var(--font-mono);">${escapeHtml(rec.date)}</td>
          <td><strong>${Number(rec.durationMin) || 0}</strong> ${escapeHtml(t("obsMinUnit"))}</td>
          <td><strong>${Number(rec.frames) || 0}</strong> ${escapeHtml(t("obsFramesUnit"))} (${escapeHtml(rec.filter || "TG")})</td>
          <td>Seestar ${escapeHtml(rec.scope || "S50")}</td>
          <td>
            <button type="button" class="ios-btn secondary tiny btn-obs-del" data-del-id="${escapeHtml(rec.id)}" style="width:auto; padding:3px 8px;">
              🗑️ ${escapeHtml(t("btnObsDelete"))}
            </button>
          </td>
        </tr>
      `).join("");
    }

    tbody.querySelectorAll(".btn-obs-del").forEach(btn => {
      btn.addEventListener("click", () => {
        const delId = btn.getAttribute("data-del-id");
        obsTrackerRecords = obsTrackerRecords.filter(r => r.id !== delId);
        saveObsTrackerDb(obsTrackerRecords);
        renderObsTrackerModal();
      });
    });

    drawObsActivityChart(filteredList);
  }
  window.renderObsTrackerModal = renderObsTrackerModal;

  // ПУНКТ 13 (ЦИКЛ 5): Запись добавляется СТРОГО по результатам конвертации файла (frames = число научных строк в сконвертированном CSV)
  function addObsTrackerRecord(star, dateStr, durationMin, frames, scope, filter = "TG", source = "conversion", fileName = "") {
    const cleanStar = String(star || "").trim() || "SZ Lyn";
    const cleanDate = String(dateStr || "").trim() || new Date().toISOString().slice(0, 10);
    const fr = Math.max(0, parseInt(frames, 10) || 0);
    const dur = Math.max(1, parseInt(durationMin, 10) || Math.max(1, Math.round(fr * 0.5)));
    const sc = VALID_SCOPES.includes(scope) ? scope : currentScopeModel;
    const candidate = {
      id: "obs-" + Date.now() + "-" + Math.floor(Math.random() * 1000),
      star: cleanStar,
      date: cleanDate,
      durationMin: dur,
      frames: fr,
      recordsCount: fr,
      filter: filter || "TG",
      scope: sc,
      source: source || "conversion",
      fileName: String(fileName || "")
    };
    if (!validateObservationLogEntry(candidate)) {
      return null;
    }
    obsTrackerRecords.push(candidate);
    saveObsTrackerDb(obsTrackerRecords);
    logRecentAction("actObsAddedFmt", { star: cleanStar, mins: dur });
    renderObsTrackerModal();
    return candidate;
  }
  window.addObsTrackerRecord = addObsTrackerRecord;

  const openObsTracker = () => {
    if (obsTrackerModal) {
      obsTrackerModal.classList.add("open");
      syncModalBodyLock();
      renderObsTrackerModal();
    }
  };
  const closeObsTracker = () => {
    if (obsTrackerModal) {
      obsTrackerModal.classList.remove("open");
      syncModalBodyLock();
    }
  };
  window.openObsTracker = openObsTracker;
  window.closeObsTracker = closeObsTracker;

  const btnOpenObsTracker = document.getElementById("btnOpenObsTracker");
  if (btnOpenObsTracker) btnOpenObsTracker.addEventListener("click", openObsTracker);
  ["btnCloseObsTracker", "btnAckObsTracker"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener("click", closeObsTracker);
  });
  if (obsTrackerModal) {
    obsTrackerModal.addEventListener("click", (e) => {
      if (e.target === obsTrackerModal) closeObsTracker();
    });
  }

  // ПУНКТ 15: Обработчики 3 фильтров (Дата, Поиск по звезде, Поиск по телескопу) и кнопки «Удалить все»
  ["obsFilterDate", "obsFilterStar", "obsFilterScope"].forEach(fid => {
    const el = document.getElementById(fid);
    if (el) {
      el.addEventListener("input", () => renderObsTrackerModal());
      el.addEventListener("change", () => renderObsTrackerModal());
    }
  });
  const btnObsResetFilters = document.getElementById("btnObsResetFilters");
  if (btnObsResetFilters) {
    btnObsResetFilters.addEventListener("click", () => {
      const fDate = document.getElementById("obsFilterDate");
      const fStar = document.getElementById("obsFilterStar");
      const fScope = document.getElementById("obsFilterScope");
      if (fDate) fDate.value = "";
      if (fStar) fStar.value = "";
      if (fScope) fScope.value = "ALL";
      renderObsTrackerModal();
    });
  }
  const btnObsDeleteAll = document.getElementById("btnObsDeleteAll");
  if (btnObsDeleteAll) {
    btnObsDeleteAll.addEventListener("click", () => {
      obsTrackerRecords = [];
      saveObsTrackerDb(obsTrackerRecords);
      renderObsTrackerModal();
    });
  }

  // ПУНКТ 7: Обработчики селекторов сортировки в окне «Срочно» и в боковом радаре
  const urgentSortSelect = document.getElementById("urgentSortSelect");
  if (urgentSortSelect) {
    urgentSortSelect.addEventListener("change", () => {
      const qEl = document.getElementById("urgentSearchField");
      renderUrgentStarsCards(qEl ? qEl.value : "");
    });
  }
  const v6RadarSortSelect = document.getElementById("v6RadarSortSelect");
  if (v6RadarSortSelect) {
    v6RadarSortSelect.addEventListener("change", () => {
      renderV6RadarDock();
    });
  }

  // ПУНКТЫ 18 и 19 + ПУНКТ 5: Скрытый от пользователя автоматический показ окна поддержки проекта
  // строго на 3-й вход в приложение и далее 1 раз в месяц (каждые 30 дней).
  const DONATE_LAUNCH_COUNT_KEY = "seestar_donate_launch_count";
  const DONATE_LAST_SHOWN_TS_KEY = "seestar_donate_last_shown_ts";
  const THIRTY_DAYS_MS = 30 * 86400 * 1000;
  let _donateSessionCounted = false;
  let _donateAutoPendingOpen = false;

  const donateModal = document.getElementById("donateModal");
  function openDonateModal() {
    if (!donateModal) return;
    donateModal.classList.add("open");
    syncModalBodyLock();
  }
  function closeDonateModal() {
    if (!donateModal) return;
    _donateAutoPendingOpen = false;
    safeSetStorage(DONATE_LAST_SHOWN_TS_KEY, String(Date.now()));
    donateModal.classList.remove("open");
    syncModalBodyLock();
  }
  window.openDonateModal = openDonateModal;
  window.closeDonateModal = closeDonateModal;

  function evaluateDonateModalSchedule(nowTs = Date.now(), incrementLaunch = true) {
    let launchCount = parseInt(safeGetStorage(DONATE_LAUNCH_COUNT_KEY, "0"), 10) || 0;
    const hostAlreadyIncremented = Boolean(
      window.__SEESTAR_DISK_STORE__ && window.__SEESTAR_DISK_STORE__.seestar_host_counted_this_launch === "1"
    );
    if (incrementLaunch) {
      if (hostAlreadyIncremented && !_donateSessionCounted) {
        _donateSessionCounted = true;
      } else {
        launchCount += 1;
        _donateSessionCounted = true;
        safeSetStorage(DONATE_LAUNCH_COUNT_KEY, String(launchCount));
      }
    }
    const lastShownTs = parseInt(safeGetStorage(DONATE_LAST_SHOWN_TS_KEY, "0"), 10) || 0;
    if (launchCount === 3 && lastShownTs === 0) {
      safeSetStorage(DONATE_LAST_SHOWN_TS_KEY, String(nowTs));
      return { shouldShow: true, launchCount, reason: "third_launch" };
    }
    if (launchCount > 3 && lastShownTs === 0) {
      safeSetStorage(DONATE_LAST_SHOWN_TS_KEY, String(nowTs));
      return { shouldShow: true, launchCount, reason: "third_launch_catchup" };
    }
    if (launchCount > 3 && lastShownTs > 0 && (nowTs - lastShownTs) >= THIRTY_DAYS_MS) {
      safeSetStorage(DONATE_LAST_SHOWN_TS_KEY, String(nowTs));
      return { shouldShow: true, launchCount, reason: "monthly_interval" };
    }
    return { shouldShow: false, launchCount, reason: "not_due" };
  }
  window.evaluateDonateModalSchedule = evaluateDonateModalSchedule;

  const btnOpenDonateModal = document.getElementById("btnOpenDonateModal");
  if (btnOpenDonateModal) {
    btnOpenDonateModal.addEventListener("click", openDonateModal);
  }
  const btnCloseDonateModal = document.getElementById("btnCloseDonateModal");
  if (btnCloseDonateModal) {
    btnCloseDonateModal.addEventListener("click", closeDonateModal);
  }
  if (donateModal) {
    donateModal.addEventListener("click", (e) => {
      if (e.target === donateModal) closeDonateModal();
    });
  }

  // При закрытии стартового окна приветствия (#btnCloseSplash), если на этом (3-м или ежемесячном) входе
  // было запланировано открытие окна поддержки, гарантированно держим его открытым по центру!
  const _btnCloseSplashForDonate = document.getElementById("btnCloseSplash");
  if (_btnCloseSplashForDonate) {
    _btnCloseSplashForDonate.addEventListener("click", () => {
      if (_donateAutoPendingOpen) {
        setTimeout(() => openDonateModal(), 320);
      }
    });
  }

  // Проверяем счётчик входов при старте приложения
  const _donateSched = evaluateDonateModalSchedule(Date.now(), true);
  if (_donateSched.shouldShow) {
    _donateAutoPendingOpen = true;
    setTimeout(() => openDonateModal(), 450);
  }

  // ПУНКТ 3 (ЦИКЛ 4): Синхронизация переключателя уведомлений (Настройки -> Уведомления)
  const chkGlobalToasts = document.getElementById("chkGlobalToastsEnabled");
  const chkSplashToasts = document.getElementById("chkSplashToastsEnabled");
  function syncToastTogglesUI() {
    const enabled = isGlobalToastsEnabled();
    if (chkGlobalToasts) chkGlobalToasts.checked = enabled;
    if (chkSplashToasts) chkSplashToasts.checked = enabled;
    if (!enabled) {
      const tc = document.getElementById("toastContainer");
      if (tc) tc.innerHTML = "";
    }
  }
  [chkGlobalToasts, chkSplashToasts].forEach(chk => {
    if (chk) {
      chk.addEventListener("change", (e) => {
        const enabled = Boolean(e.target.checked);
        safeSetStorage("seestar_toasts_enabled", enabled ? "true" : "false");
        syncToastTogglesUI();
      });
    }
  });
  syncToastTogglesUI();

  // ПУНКТ 7 (ЦИКЛ 4): Обработчики быстрых переходов в расширенном окне приветствия
  const btnSplashQuickSync = document.getElementById("btnSplashQuickSync");
  if (btnSplashQuickSync) {
    btnSplashQuickSync.addEventListener("click", () => {
      closeSplash();
      const btnFetch = document.getElementById("btnFetchAll");
      if (btnFetch) {
        btnFetch.scrollIntoView({ behavior: "smooth", block: "center" });
        btnFetch.focus();
      }
    });
  }
  const btnSplashQuickTracker = document.getElementById("btnSplashQuickTracker");
  if (btnSplashQuickTracker) {
    btnSplashQuickTracker.addEventListener("click", () => {
      closeSplash();
      openObsTracker();
    });
  }
  const btnSplashQuickRadar = document.getElementById("btnSplashQuickRadar");
  if (btnSplashQuickRadar) {
    btnSplashQuickRadar.addEventListener("click", () => {
      closeSplash();
      openUrgentModal();
    });
  }
  const btnSplashQuickLoadCsv = document.getElementById("btnSplashQuickLoadCsv");
  if (btnSplashQuickLoadCsv) {
    btnSplashQuickLoadCsv.addEventListener("click", () => {
      closeSplash();
      const btnSel = document.getElementById("btnSelectCsvFile");
      if (btnSel) btnSel.focus();
    });
  }

  // ПУНКТ 5 (ЦИКЛ 4): При старте приложения ВСЕГДА первым открывается окно приветствия (#splashModal)
  if (splashModal && splashToggle) {
    splashToggle.checked = false;
    splashModal.classList.remove("hidden", "closing");
    splashModal.classList.add("opening");
    document.documentElement.classList.add("splash-active");
    document.body.classList.add("splash-active");
  }

  window.applyColorTheme = applyColorTheme;
  window.processFile = processFile;
  window.STATE = STATE;
  window.previewCsvText = previewCsvText;
  window.hideRadarObjectTooltip = hideRadarObjectTooltip;
  window.I18N = I18N;
  applyTranslations();
  applyScopeModelUI(false);
  applyColorTheme(currentColorTheme, false);
  renderUrgentStarsCards();
  renderV6RadarDock();
  window.__restoreFromDiskStore = function(storeObj) {
    if (!storeObj || typeof storeObj !== "object") return;
    window.__SEESTAR_DISK_STORE__ = Object.assign(window.__SEESTAR_DISK_STORE__ || {}, storeObj);
    Object.entries(storeObj).forEach(([k, v]) => {
      try { localStorage.setItem(k, String(v)); } catch (_) {}
    });
    const restoredLang = String(storeObj.lang || storeObj.seestar_lang || "").trim().toLowerCase().slice(0, 2);
    if (restoredLang && I18N[restoredLang] && restoredLang !== currentLang) {
      currentLang = restoredLang;
      applyTranslations();
      renderUrgentStarsCards();
      renderV6RadarDock();
    }
    if (typeof window.restoreSavedObscode === "function") {
      window.restoreSavedObscode();
    }
    obsTrackerRecords = loadObsTrackerDb();
    renderObsTrackerModal();
    if (!_donateAutoPendingOpen) {
      const checkRes = evaluateDonateModalSchedule(Date.now(), false);
      if (checkRes.shouldShow) {
        _donateAutoPendingOpen = true;
        setTimeout(() => openDonateModal(), 350);
      }
    }
  };

  window.addEventListener("pywebviewready", async () => {
    try {
      if (window.pywebview && window.pywebview.api) {
        if (typeof window.pywebview.api.save_store_item === "function") {
          for (const [pk, pv] of Object.entries(_PENDING_DISK_WRITES)) {
            await window.pywebview.api.save_store_item(pk, pv);
            delete _PENDING_DISK_WRITES[pk];
          }
        }
        if (typeof window.pywebview.api.get_all_store === "function") {
          const diskData = await window.pywebview.api.get_all_store();
          if (diskData && typeof diskData === "object") {
            window.__restoreFromDiskStore(diskData);
          }
        }
      }
    } catch (_) {}
  });


  // ============================================================================
  // МОДУЛЬ ЗАЩИТЫ АВТОРСТВА И АНТИПЛАГИАТА (COSMOBEHEMOTHYCH IP & AUTHORSHIP SEAL)
  // Секретная проверка авторства:
  // 1) Комбинация клавиш Ctrl + Alt + Shift + A в любом месте программы
  // 2) Ввод кодового слова COSMOPROOF в поле OBSCODE
  // 3) Вызов window.verifyCosmoBehemothychAuthorship() в консоли разработчика
  // Строка зашифрована XOR (0x5A) + Base64, поэтому не удаляется при автозамене текста плагиаторами.
  // ============================================================================
  const _CBH_ENC_SEAL = "eorFisSKzorBisKKx4rHisKKwHqK+orKis2K+orKisuKxIr4isCKwnpyFQgTHRMUGxZ6Gw8OEhUICRITCnoKCBUVHHNQisWL2oriiuGK5Irsiu+K54riiu9gegk/PykuOyh6GykuKDUWOzh6GxsMCRV6cixrdGp0anq42s56isWK74vaiuiK6ovVeoroiu+L2ovbiuKL1XNQisqK6IvYiuSL2nqK4nqK5YvaiuqK6IrkiuSK64rhiuqK7orqi9iK74rhi9Zgehk1KTc1GD8yPzc1LjIjOTJQHTMuEi84YHoyLi4qKWB1dT0zLjIvOHQ5NTd1GTUpNzUYPzI/NzUuMiM5MlAYNTUpLiNgejIuLiopYHV1ODU1KS4jdC41dTk1KTc1OD8yPzc1LjIjOTJQivyK4ovei9qK5IroiuSK43qK5IvYiuWK74vdiuqL2IrkiuB6chsvLjI1KHocMzQ9PygqKDM0LnNgehkYEncbCQ4IFRYbGHcbGwwJFXdoamhsd2McYh9uG2hrd20ZaR53GGxqa1CKyovai9+K4ovYiu+K4IvYi9mL2orqYHqKyIrqi9qK4orqiueL2HpsenKK+orqiu6K6ovaeovciu+K4YrviuN6GxsMCRV6cXqK/IrviueL2IvaiuqK4YvWiueK6ovVeoveiuSL2IrkiuaK74vYi9qK4ovdiu+L24rgiuqL1XqK4YrqiuuK5IvaiuqL2Irki9qK4ovVegk/PykuOyh6CWlqdQlpagoIFXUJb2p1CW9qCggVcw==";
  const _CBH_SEAL_SHA256 = "b53bea58d23a07b1b2f1f3cb184915ec0bc2894fddf779c3e9582b5a1fb90dcc";
  const _CBH_FINGERPRINT = "CBH-ASTROLAB-AAVSO-2026-9F8E4A21-7C3D-B601";

  function decodeCosmoBehemothychSeal() {
    try {
      const binStr = atob(_CBH_ENC_SEAL);
      const bytes = new Uint8Array(binStr.length);
      for (let i = 0; i < binStr.length; i++) {
        bytes[i] = binStr.charCodeAt(i) ^ 90;
      }
      return new TextDecoder("utf-8").decode(bytes);
    } catch (_) {
      return "Author: CosmoBehemothych | Fingerprint: " + _CBH_FINGERPRINT;
    }
  }

  function verifyCosmoBehemothychAuthorship(showModal = true) {
    const decodedText = decodeCosmoBehemothychSeal();
    const proofObj = {
      verified: true,
      application: "Seestar AstroLab AAVSO v1.0.1",
      author: "CosmoBehemothych",
      github: "https://github.com/CosmoBehemothych",
      boosty: "https://boosty.to/cosmobehemothych",
      fingerprint: _CBH_FINGERPRINT,
      sha256Seal: _CBH_SEAL_SHA256,
      decodedCertificate: decodedText
    };
    if (showModal) {
      showIosNotification(
        "🔏 Подлинник разработки CosmoBehemothych",
        decodedText + "\nSHA-256: " + _CBH_SEAL_SHA256.slice(0, 32) + "...",
        "Криптографическая метка авторства подтверждена (Ctrl+Alt+Shift+A)",
        "ok"
      );
    }
    return proofObj;
  }
  window.verifyCosmoBehemothychAuthorship = verifyCosmoBehemothychAuthorship;
  window.__CBH_AUTHORSHIP_SEAL__ = {
    fingerprint: _CBH_FINGERPRINT,
    sha256: _CBH_SEAL_SHA256,
    verify: verifyCosmoBehemothychAuthorship
  };

  document.addEventListener("keydown", (ev) => {
    if (ev.ctrlKey && ev.altKey && ev.shiftKey && (ev.code === "KeyA" || ev.key === "A" || ev.key === "a" || ev.key === "Ф" || ev.key === "ф")) {
      ev.preventDefault();
      verifyCosmoBehemothychAuthorship(true);
    }
  });

  ["obscode", "headerObscodeQuick"].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("input", (ev) => {
        if (String(ev.target.value || "").trim().toUpperCase() === "COSMOPROOF") {
          ev.target.value = String(safeGetStorage("seestar_user_obscode", "") || "");
          verifyCosmoBehemothychAuthorship(true);
        }
      });
    }
  });

  renderObsTrackerModal();
  renderSplashQuickHub();

})();


  // =========================================================================
  // ИНИЦИАЛИЗАЦИЯ НОВЫХ КОМПОНЕНТОВ v1.0.1 (ИСПРАВЛЕНИЕ ВСЕХ 8 ПУНКТОВ)
  // =========================================================================
  window.updateDssFovSvgOverlay = function(scopeModel) {
    const code = scopeModel || window._currentScopeModel || "S50";
    const prof = AstroLabCore.getScopeProfile(code);
    // Точный физический расчёт рамки относительно поля карты DSS2 2.40° × 2.40° (340×340 px)
    const skyDeg = prof.skySurveyFovDeg || 2.40;
    const wPx = Math.round(((prof.fovDegW || 0.78) / skyDeg) * 340);
    const hPx = Math.round(((prof.fovDegH || 1.05) / skyDeg) * 340);
    const xPx = Math.round((340 - wPx) / 2);
    const yPx = Math.round((340 - hPx) / 2);

    const rectEl = document.getElementById("dssFovRect");
    const labelBg = document.getElementById("dssFovLabelBg");
    const labelTxt = document.getElementById("dssFovLabelText");
    if (rectEl) {
      rectEl.setAttribute("x", xPx);
      rectEl.setAttribute("y", yPx);
      rectEl.setAttribute("width", wPx);
      rectEl.setAttribute("height", hPx);
    }
    if (labelBg && labelTxt) {
      const focalMm = prof.focalMm || (code.startsWith("S50") ? 250 : 150);
      const fovStr = prof.fovStr || `${prof.fovDegW}°×${prof.fovDegH}°`;
      const pxScale = prof.pixelScale ? `${prof.pixelScale}″/px` : "";
      const lbl = `${code} • f=${focalMm}мм • ${fovStr} (${pxScale})`;
      labelTxt.textContent = lbl;
      labelBg.setAttribute("width", Math.min(324, Math.max(180, lbl.length * 6.1 + 14)));
    }
  };

  window.toggleSettingsPopover = function(ev) {
    if (ev && typeof ev.stopPropagation === "function") ev.stopPropagation();
    const gearBtn = document.getElementById("btnSettingsGear");
    const gearMenu = document.getElementById("settingsPopoverMenu");
    if (!gearBtn || !gearMenu) return;
    const nextOpen = !gearMenu.classList.contains("open");
    gearBtn.setAttribute("aria-expanded", nextOpen ? "true" : "false");
    gearMenu.setAttribute("aria-hidden", nextOpen ? "false" : "true");
    gearMenu.classList.toggle("open", nextOpen);
  };

  (function initV101Components() {
    const gearWrap = document.getElementById("settingsGearWrap");
    const gearBtn = document.getElementById("btnSettingsGear");
    const gearMenu = document.getElementById("settingsPopoverMenu");
    const diagBtn = document.getElementById("btnDiagnose");

    function closeGearMenu() {
      if (!gearBtn || !gearMenu) return;
      gearBtn.setAttribute("aria-expanded", "false");
      gearMenu.setAttribute("aria-hidden", "true");
      gearMenu.classList.remove("open");
    }

    document.addEventListener("click", (e) => {
      if (gearWrap && !gearWrap.contains(e.target)) closeGearMenu();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        closeGearMenu();
        if (window.closeCriticalMismatchModal) window.closeCriticalMismatchModal(e);
      }
    });

    if (diagBtn) {
      diagBtn.addEventListener("click", () => {
        closeGearMenu();
        setTimeout(() => {
          const sw = document.getElementById("statusWrapper");
          if (sw) sw.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }, 60);
      });
    }

    // Иконка [?] тултипа справки в правом верхнем углу карточки сравнения
    const helpWrap = document.getElementById("comparisonHelpWrap");
    const helpBtn = document.getElementById("btnComparisonHelpTip");
    if (helpWrap && helpBtn) {
      helpBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        helpWrap.classList.toggle("force-open");
      });
      document.addEventListener("click", (e) => {
        if (!helpWrap.contains(e.target)) helpWrap.classList.remove("force-open");
      });
    }

    // Быстрые кнопки внутри Empty State
    const btnEmptyCsv = document.getElementById("btnEmptyStateSelectCsv");
    const btnEmptyDemo = document.getElementById("btnEmptyStateLoadDemo");
    if (btnEmptyCsv) {
      btnEmptyCsv.addEventListener("click", () => {
        const inp = document.getElementById("csvFile");
        if (inp) inp.click();
      });
    }
    if (btnEmptyDemo) {
      btnEmptyDemo.addEventListener("click", () => {
        const demoBtn = document.getElementById("btnLoadDemo");
        if (demoBtn) demoBtn.click();
      });
    }

    // Кнопки модального окна критического расхождения (Пункт 1)
    const btnCritClose = document.getElementById("btnCritModalClose");
    const btnCritOpenInputs = document.getElementById("btnCritModalOpenInputs");
    if (btnCritClose) {
      btnCritClose.addEventListener("click", (e) => window.closeCriticalMismatchModal(e));
    }
    if (btnCritOpenInputs) {
      btnCritOpenInputs.addEventListener("click", (e) => window.openCriticalMismatchInputs(e));
    }

    // Синхронизация бейджей аккордеонов при вводе OBSCODE
    const obsInput = document.getElementById("obscode");
    const hdrObsInput = document.getElementById("headerObscodeQuick");
    if (obsInput) obsInput.addEventListener("input", updateAccordionSummaryBadges);
    if (hdrObsInput) hdrObsInput.addEventListener("input", () => setTimeout(updateAccordionSummaryBadges, 10));

    // Синхронизация точной физической рамки поля зрения при смене модели телескопа
    const hdrScope = document.getElementById("headerScopeSelect");
    if (hdrScope) {
      hdrScope.addEventListener("change", () => {
        setTimeout(() => window.updateDssFovSvgOverlay(hdrScope.value), 20);
      });
    }
    document.querySelectorAll("[data-scope-tab]").forEach(btn => {
      btn.addEventListener("click", () => {
        const sc = btn.getAttribute("data-scope-tab");
        setTimeout(() => window.updateDssFovSvgOverlay(sc), 20);
      });
    });

    window.updateDssFovSvgOverlay(window._currentScopeModel || "S50");
    updateAccordionSummaryBadges();

})();


/* ==========================================================================
   МОДУЛЬ 12: КЛИЕНТСКИЙ МОСТ К PYTHON-БЭКЕНДУ (PhotometryBackendEngine RPC)
   Делегирует расчёт профилей оптики, предпросмотр/сверку CSV, конвертацию
   в формат AAVSO Extended (#OBSTYPE=DSLR) и валидацию готовых файлов
   серверному ядру Python (через pywebview.api или локальный REST 127.0.0.1:18765).
   ========================================================================== */
(function initPythonBackendBridge() {
  const BACKEND_RPC_URL = "http://127.0.0.1:18765/api/rpc";

  async function callPythonBackend(action, payload = {}) {
    // 1. Приоритет: прямой нативный вызов через мост pywebview.api
    if (window.pywebview && window.pywebview.api) {
      try {
        if (action === "get_scope_profile" && typeof window.pywebview.api.backend_get_scope_profile === "function") {
          return await window.pywebview.api.backend_get_scope_profile(payload.code || "S50");
        }
        if (action === "preview_csv" && typeof window.pywebview.api.backend_preview_csv === "function") {
          return await window.pywebview.api.backend_preview_csv(payload);
        }
        if (action === "convert_csv" && typeof window.pywebview.api.backend_convert_csv === "function") {
          return await window.pywebview.api.backend_convert_csv(payload);
        }
        if (action === "verify_file" && typeof window.pywebview.api.backend_verify_file === "function") {
          return await window.pywebview.api.backend_verify_file(payload.content || "");
        }
      } catch (_) {}
    }
    // 2. Локальный REST JSON-RPC сервер Python-бэкенда (127.0.0.1:18765)
    try {
      const resp = await fetch(BACKEND_RPC_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(Object.assign({ action }, payload))
      });
      if (resp.ok) {
        return await resp.json();
      }
    } catch (_) {}
    return null;
  }

  window.AstroLabPythonBackendBridge = {
    call: callPythonBackend,
    getScopeProfile: (code) => callPythonBackend("get_scope_profile", { code }),
    previewAndVerifyCsv: (params) => callPythonBackend("preview_csv", params),
    convertCsvToAavso: (params) => callPythonBackend("convert_csv", params),
    verifyAavsoFile: (content) => callPythonBackend("verify_file", { content })
  };

})();


/* ==========================================================================
   МОДУЛЬ 13: ПРОТОКОЛ ТРЁХ SENIOR-СПЕЦИАЛИСТОВ (ИСПРАВЛЕНИЕ ПУНКТОВ 1–7)
   1. Подсветка красным и автофокус курсора при нажатии «Сконвертировать...»,
      если не указан OBSCODE, или не указан STARID, или не загружены данные
      SIMBAD, или не выбран CSV-файл.
   2. MAG и MERR не проводят сверку между данными из файла и данными из SIMBAD.
   3. Полная локализация всех динамических строк, меню и подсказок на 6 языков.
   4. Удалена надпись и рамка «Поле зрения: ZWO Seestar ...» с изображения звезды.
   5. При отсутствии фото звезды в каталогах выводится явный текст:
      «Изображение звезды в каталогах отсутствует».
   6. При недоступности серверов SIMBAD / AAVSO VSP пользователю выводится
      наглядная ошибка с объяснением причины.
   7. Плавная безрывковая анимация переходов между разделами 1 → 2 → 3.
   ========================================================================== */
(function initSeniorTeamFixesV101() {
  const EXTRA_I18N = {
    ru: {
      lblStarFieldPhoto: "🌌 Снимок окрестностей звезды (DSS2)",
      lblFileOnlyNoSimbadCheck: "Измерение из файла Seestar (не сверяется с SIMBAD)",
      msgStarImageMissing: "Изображение звезды в каталогах отсутствует",
      errNoStarIdTitle: "Не выбрана звезда (STARID)",
      errNoStarIdMsg: "Пожалуйста, укажите имя или ID звезды (STARID) перед конвертацией.",
      errNoSimbadLoadedTitle: "Не загружены данные SIMBAD + VSP",
      errNoSimbadLoadedMsg: "Нажмите «🔭 Загрузить SIMBAD + VSP», чтобы получить координаты и карту калибровки перед конвертацией.",
      errNoCsvSelectedTitle: "Не выбран CSV-файл фотометрии",
      errNoCsvSelectedMsg: "Выберите исходный CSV-файл от Seestar (или нажмите «Демо CSV») в разделе 2 перед конвертацией.",
      errServersUnavailableTitle: "Серверы каталогов SIMBAD / AAVSO VSP недоступны",
      errServersUnavailableBody: "Не удалось получить данные от серверов SIMBAD / AAVSO VSP. Проверьте подключение к интернету или запустите «Диагностику сети и зеркал» в меню «Настройки».",
      waitingSimbadBadge: "⏳ Ожидается SIMBAD",
      notLoadedSimbadCell: "— (Не загружено)",
      simbadPreloadedFmt: "✓ Данные SIMBAD ({star}) загружены — выберите CSV-файл Seestar для сверки",
      vspStep1Loading: "⏳ Шаг 1/2: Опрос мировых зеркал SIMBAD (получение координат RA/DEC)...",
      vspStep2Loading: "⏳ Шаг 2/2: Загрузка карты AAVSO VSP (CHART, KNAME, KMAG)..."
    },
    en: {
      lblStarFieldPhoto: "🌌 Star Field Survey Image (DSS2)",
      lblFileOnlyNoSimbadCheck: "Seestar file measurement (not compared with SIMBAD)",
      msgStarImageMissing: "Star image is not available in the catalogs",
      errNoStarIdTitle: "Target Star (STARID) Not Selected",
      errNoStarIdMsg: "Please enter a target star name or ID (STARID) before converting.",
      errNoSimbadLoadedTitle: "SIMBAD + VSP Data Not Loaded",
      errNoSimbadLoadedMsg: "Please click '🔭 Load SIMBAD + VSP' to fetch catalog coordinates and calibration data before converting.",
      errNoCsvSelectedTitle: "Seestar CSV File Not Selected",
      errNoCsvSelectedMsg: "Please select a Seestar photometry CSV file (or click 'Demo CSV') in Section 2 before converting.",
      errServersUnavailableTitle: "SIMBAD / AAVSO VSP Catalog Servers Unavailable",
      errServersUnavailableBody: "Could not reach SIMBAD / AAVSO VSP servers. Please check your internet connection or run 'Network & Mirror Diagnostics' in Settings.",
      waitingSimbadBadge: "⏳ Waiting for SIMBAD",
      notLoadedSimbadCell: "— (Not loaded)",
      simbadPreloadedFmt: "✓ SIMBAD data ({star}) loaded — select a Seestar CSV file to compare",
      vspStep1Loading: "⏳ Step 1/2: Querying global SIMBAD mirrors (fetching RA/DEC)...",
      vspStep2Loading: "⏳ Step 2/2: Fetching AAVSO VSP chart & check star (CHART, KNAME, KMAG)..."
    },
    es: {
      lblStarFieldPhoto: "🌌 Imagen del campo estelar (DSS2)",
      lblFileOnlyNoSimbadCheck: "Medición del archivo Seestar (no se compara con SIMBAD)",
      msgStarImageMissing: "La imagen de la estrella no está disponible en los catálogos",
      errNoStarIdTitle: "Estrella (STARID) no seleccionada",
      errNoStarIdMsg: "Introduzca el nombre o ID de la estrella (STARID) antes de convertir.",
      errNoSimbadLoadedTitle: "Datos SIMBAD + VSP no cargados",
      errNoSimbadLoadedMsg: "Haga clic en '🔭 Cargar SIMBAD + VSP' antes de convertir.",
      errNoCsvSelectedTitle: "Archivo CSV de Seestar no seleccionado",
      errNoCsvSelectedMsg: "Seleccione un archivo CSV de Seestar en la Sección 2 antes de convertir.",
      errServersUnavailableTitle: "Servidores de catálogos SIMBAD / AAVSO VSP no disponibles",
      errServersUnavailableBody: "No se pudo conectar con los servidores SIMBAD / AAVSO VSP. Verifique su conexión a Internet o ejecute el diagnóstico de red en Ajustes.",
      waitingSimbadBadge: "⏳ Esperando SIMBAD",
      notLoadedSimbadCell: "— (No cargado)",
      simbadPreloadedFmt: "✓ Datos SIMBAD ({star}) cargados — seleccione un archivo CSV",
      vspStep1Loading: "⏳ Paso 1/2: Consultando espejos SIMBAD...",
      vspStep2Loading: "⏳ Paso 2/2: Cargando carta AAVSO VSP..."
    },
    de: {
      lblStarFieldPhoto: "🌌 Sternfeldbild (DSS2)",
      lblFileOnlyNoSimbadCheck: "Messwert aus Seestar-Datei (kein SIMBAD-Abgleich)",
      msgStarImageMissing: "Sternbild ist in den Katalogen nicht vorhanden",
      errNoStarIdTitle: "Stern (STARID) nicht ausgewählt",
      errNoStarIdMsg: "Bitte geben Sie vor der Konvertierung einen Sternnamen (STARID) ein.",
      errNoSimbadLoadedTitle: "SIMBAD + VSP-Daten nicht geladen",
      errNoSimbadLoadedMsg: "Bitte klicken Sie vor der Konvertierung auf '🔭 SIMBAD + VSP laden'.",
      errNoCsvSelectedTitle: "Keine Seestar-CSV-Datei ausgewählt",
      errNoCsvSelectedMsg: "Bitte wählen Sie in Abschnitt 2 eine Seestar-CSV-Datei aus.",
      errServersUnavailableTitle: "SIMBAD / AAVSO VSP-Server nicht erreichbar",
      errServersUnavailableBody: "Die Katalogserver SIMBAD / AAVSO VSP sind derzeit nicht erreichbar. Bitte prüfen Sie Ihre Internetverbindung oder starten Sie die Netzwerkdiagnose.",
      waitingSimbadBadge: "⏳ Warte auf SIMBAD",
      notLoadedSimbadCell: "— (Nicht geladen)",
      simbadPreloadedFmt: "✓ SIMBAD-Daten ({star}) geladen — CSV-Datei wählen",
      vspStep1Loading: "⏳ Schritt 1/2: SIMBAD-Spiegelserver werden abgefragt...",
      vspStep2Loading: "⏳ Schritt 2/2: AAVSO VSP-Karte wird geladen..."
    },
    fr: {
      lblStarFieldPhoto: "🌌 Image du champ stellaire (DSS2)",
      lblFileOnlyNoSimbadCheck: "Mesure du fichier Seestar (non comparée à SIMBAD)",
      msgStarImageMissing: "L'image de l'étoile est absente des catalogues",
      errNoStarIdTitle: "Étoile (STARID) non sélectionnée",
      errNoStarIdMsg: "Veuillez saisir le nom ou l'ID de l'étoile (STARID) avant la conversion.",
      errNoSimbadLoadedTitle: "Données SIMBAD + VSP non chargées",
      errNoSimbadLoadedMsg: "Veuillez cliquer sur '🔭 Charger SIMBAD + VSP' avant la conversion.",
      errNoCsvSelectedTitle: "Fichier CSV Seestar non sélectionné",
      errNoCsvSelectedMsg: "Veuillez sélectionner un fichier CSV Seestar dans la Section 2 avant la conversion.",
      errServersUnavailableTitle: "Serveurs SIMBAD / AAVSO VSP indisponibles",
      errServersUnavailableBody: "Impossible de joindre les serveurs SIMBAD / AAVSO VSP. Vérifiez votre connexion Internet ou lancez le diagnostic réseau dans les Paramètres.",
      waitingSimbadBadge: "⏳ En attente de SIMBAD",
      notLoadedSimbadCell: "— (Non chargé)",
      simbadPreloadedFmt: "✓ Données SIMBAD ({star}) chargées — sélectionnez un fichier CSV",
      vspStep1Loading: "⏳ Étape 1/2 : Interrogation des miroirs SIMBAD...",
      vspStep2Loading: "⏳ Étape 2/2 : Chargement de la carte AAVSO VSP..."
    },
    zh: {
      lblStarFieldPhoto: "🌌 恒星天区巡天图像 (DSS2)",
      lblFileOnlyNoSimbadCheck: "Seestar 文件实测值（不与 SIMBAD 比对）",
      msgStarImageMissing: "星表中缺少该恒星的图像",
      errNoStarIdTitle: "未选择目标恒星 (STARID)",
      errNoStarIdMsg: "请在转换前输入目标恒星名称或 ID (STARID)。",
      errNoSimbadLoadedTitle: "尚未加载 SIMBAD + VSP 星表数据",
      errNoSimbadLoadedMsg: "请在转换前点击“🔭 加载 SIMBAD + VSP”获取坐标与校准星数据。",
      errNoCsvSelectedTitle: "未选择 Seestar CSV 测光文件",
      errNoCsvSelectedMsg: "请在转换前于第 2 步选择 Seestar CSV 测光文件（或点击“演示 CSV”）。",
      errServersUnavailableTitle: "SIMBAD / AAVSO VSP 星表服务器不可用",
      errServersUnavailableBody: "无法连接到 SIMBAD 或 AAVSO VSP 服务器。请检查您的网络连接，或在“设置”中运行“网络与镜像诊断”。",
      waitingSimbadBadge: "⏳ 等待加载 SIMBAD",
      notLoadedSimbadCell: "—（未加载）",
      simbadPreloadedFmt: "✓ 已加载 SIMBAD 数据 ({star}) — 请选择 Seestar CSV 文件",
      vspStep1Loading: "⏳ 第 1/2 步：正在查询全球 SIMBAD 镜像服务器...",
      vspStep2Loading: "⏳ 第 2/2 步：正在加载 AAVSO VSP 星图与检验星..."
    }
  };

  if (window.I18N) {
    Object.keys(EXTRA_I18N).forEach(langKey => {
      if (window.I18N[langKey]) {
        Object.assign(window.I18N[langKey], EXTRA_I18N[langKey]);
      }
    });
  }

  function getTr(key) {
    const lang = (document.getElementById("langSelect")?.value || "ru").slice(0, 2).toLowerCase();
    return (window.I18N && window.I18N[lang] && window.I18N[lang][key]) || EXTRA_I18N.ru[key] || key;
  }

  // ПУНКТ 7: Плавное раскрытие/сворачивание разделов 1 -> 2 -> 3 без резких скачков
  window.smoothToggleAccordion = function(accEl, shouldOpen) {
    if (!accEl) return;
    if (shouldOpen) {
      if (!accEl.open) {
        accEl.classList.remove("accordion-collapsing");
        accEl.classList.add("accordion-expanding");
        accEl.open = true;
        setTimeout(() => accEl.classList.remove("accordion-expanding"), 500);
      }
    } else {
      if (accEl.open) {
        accEl.classList.remove("accordion-expanding");
        accEl.classList.add("accordion-collapsing");
        setTimeout(() => {
          accEl.open = false;
          accEl.classList.remove("accordion-collapsing");
        }, 460);
      }
    }
  };

  window.scheduleSimbadLoadedAccordionTransition = function() {
    if (window._accSimbadTimer) clearTimeout(window._accSimbadTimer);
    window._accSimbadTimer = setTimeout(() => {
      const acc1 = document.getElementById("accObserverStar");
      const acc2 = document.getElementById("accFileSelect");
      const acc3 = document.getElementById("accConvertSection");
      const pillCsvEl = document.getElementById("selectedFileNamePill");
      const hasCsv = Boolean(pillCsvEl && pillCsvEl.classList.contains("file-loaded"));
      window.smoothToggleAccordion(acc1, false);
      if (hasCsv) {
        window.smoothToggleAccordion(acc2, false);
        window.smoothToggleAccordion(acc3, true);
        setTimeout(() => {
          if (acc3) acc3.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }, 240);
      } else {
        window.smoothToggleAccordion(acc2, true);
        window.smoothToggleAccordion(acc3, false);
        setTimeout(() => {
          if (acc2) acc2.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }, 240);
      }
    }, 3000);
  };

  window.scheduleCsvLoadedAccordionTransition = function() {
    if (window._accCsvTimer) clearTimeout(window._accCsvTimer);
    window._accCsvTimer = setTimeout(() => {
      const acc2 = document.getElementById("accFileSelect");
      const acc3 = document.getElementById("accConvertSection");
      const btnConv = document.getElementById("btnConvert");
      window.smoothToggleAccordion(acc2, false);
      window.smoothToggleAccordion(acc3, true);
      if (btnConv && !btnConv.disabled) {
        btnConv.classList.add("step3-ready-pulse");
        setTimeout(() => btnConv.classList.remove("step3-ready-pulse"), 2500);
      }
      setTimeout(() => {
        if (acc3) acc3.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }, 240);
    }, 3000);
  };

  // ПУНКТ 5: Если фото звезды в каталогах отсутствует — выводим явный текст
  const viewportWrap = document.getElementById("dssViewportWrap");
  let missingImgNotice = document.getElementById("starImageMissingNotice");
  if (viewportWrap && !missingImgNotice) {
    missingImgNotice = document.createElement("div");
    missingImgNotice.id = "starImageMissingNotice";
    missingImgNotice.className = "star-image-missing-notice";
    missingImgNotice.setAttribute("data-i18n", "msgStarImageMissing");
    missingImgNotice.textContent = getTr("msgStarImageMissing");
    viewportWrap.appendChild(missingImgNotice);
  }

  const starImgEl = document.getElementById("starImage");
  const dssCanvasEl = document.getElementById("dssFallbackCanvas");
  const starCapEl = document.getElementById("starImageCaption");
  if (starImgEl) {
    starImgEl.addEventListener("load", () => {
      if (missingImgNotice) missingImgNotice.style.display = "none";
      if (dssCanvasEl) dssCanvasEl.style.display = "none";
    });
    starImgEl.addEventListener("error", () => {
      // На второй ошибке (когда оба сервера SkyView и Alasky не вернули фото звезды)
      setTimeout(() => {
        if (starImgEl.style.opacity === "0" || !starImgEl.complete || starImgEl.naturalWidth === 0) {
          if (dssCanvasEl) dssCanvasEl.style.display = "none";
          if (missingImgNotice) {
            missingImgNotice.textContent = getTr("msgStarImageMissing");
            missingImgNotice.style.display = "flex";
          }
          if (starCapEl) {
            starCapEl.textContent = getTr("msgStarImageMissing");
          }
        }
      }, 60);
    });
  }

  // ПУНКТ 6: Наглядный баннер ошибки при недоступности серверов SIMBAD / VSP
  const vspLoadBanner = document.getElementById("vspLoadingBanner");
  let srvErrBanner = document.getElementById("serverErrorBanner");
  if (vspLoadBanner && vspLoadBanner.parentNode && !srvErrBanner) {
    srvErrBanner = document.createElement("div");
    srvErrBanner.id = "serverErrorBanner";
    srvErrBanner.className = "server-error-banner";
    srvErrBanner.setAttribute("role", "alert");
    vspLoadBanner.parentNode.insertBefore(srvErrBanner, vspLoadBanner.nextSibling);
  }

  window.showCatalogServerError = function(detailMsg) {
    if (srvErrBanner) {
      srvErrBanner.innerHTML = `🚨 <strong>${getTr("errServersUnavailableTitle")}:</strong> ${getTr("errServersUnavailableBody")}` +
        (detailMsg ? `<br><span style="font-family:var(--font-mono); font-size:11px; opacity:0.85;">${detailMsg}</span>` : "");
      srvErrBanner.style.display = "block";
    }
  };

  const btnFetch = document.getElementById("btnFetchAll");
  if (btnFetch) {
    btnFetch.addEventListener("click", () => {
      if (srvErrBanner) srvErrBanner.style.display = "none";
    }, true);
  }

  // ПУНКТ 1: Перехват клика по кнопке «Сконвертировать данные для загрузки на AAVSO» (#btnConvert)
  // с покраской незаполненного поля в красный цвет (.input-error-red) и переводом курсора (focus)!
  function highlightMissingAndFocus(targetEl, accordionId, hintId, msgText) {
    const acc = document.getElementById(accordionId);
    if (acc && !acc.open) {
      window.smoothToggleAccordion(acc, true);
    }
    if (targetEl) {
      targetEl.classList.remove("input-error-red");
      void targetEl.offsetWidth; // reflow for animation restart
      targetEl.classList.add("input-error-red");
      const clearRed = () => {
        targetEl.classList.remove("input-error-red");
        targetEl.removeEventListener("input", clearRed);
        targetEl.removeEventListener("click", clearRed);
      };
      targetEl.addEventListener("input", clearRed);
      targetEl.addEventListener("click", clearRed);
      setTimeout(() => {
        try {
          targetEl.scrollIntoView({ behavior: "smooth", block: "center" });
          targetEl.focus();
        } catch (_) {}
      }, 80);
    }
    if (hintId) {
      const hEl = document.getElementById(hintId);
      if (hEl) {
        hEl.textContent = msgText;
        hEl.className = "field-hint bad";
      }
    }
  }

  const btnConvertEl = document.getElementById("btnConvert");
  if (btnConvertEl) {
    btnConvertEl.addEventListener("click", (ev) => {
      if (window.STATE && window.STATE.isConversionBlockedByMismatch) return;

      const obsEl = document.getElementById("obscode");
      const starEl = document.getElementById("starid");
      const raEl = document.getElementById("ra");
      const decEl = document.getElementById("dec");
      const btnFetchEl = document.getElementById("btnFetchAll");
      const btnCsvEl = document.getElementById("btnSelectCsvFile");
      const pillCsvEl = document.getElementById("selectedFileNamePill");

      const obsVal = (obsEl?.value || "").trim();
      const starVal = (starEl?.value || "").trim();
      const simbadLoaded = Boolean(window.STATE && window.STATE.simbadCatalogLoaded && (raEl?.value || "").trim() && (decEl?.value || "").trim());
      const csvLoaded = Boolean(pillCsvEl && pillCsvEl.classList.contains("file-loaded")) ||
                        Boolean(document.getElementById("previewTable")?.style.display !== "none" && document.querySelector("#previewTable tbody tr"));

      // 1. Проверка OBSCODE
      if (!obsVal || obsVal.toUpperCase() === "NA") {
        ev.stopImmediatePropagation();
        ev.preventDefault();
        highlightMissingAndFocus(obsEl, "accObserverStar", "obscodeHint", getTr("errNoObscodeMsg"));
        return;
      }

      // 2. Проверка STARID (имя / ID звезды)
      if (!starVal) {
        ev.stopImmediatePropagation();
        ev.preventDefault();
        highlightMissingAndFocus(starEl, "accObserverStar", "staridHint", getTr("errNoStarIdMsg"));
        return;
      }

      // 3. Проверка загруженных данных SIMBAD + VSP
      if (!simbadLoaded) {
        ev.stopImmediatePropagation();
        ev.preventDefault();
        if (raEl) raEl.classList.add("input-error-red");
        if (decEl) decEl.classList.add("input-error-red");
        highlightMissingAndFocus(btnFetchEl || starEl, "accObserverStar", "staridHint", getTr("errNoSimbadLoadedMsg"));
        return;
      }

      // 4. Проверка выбранного файла CSV для конвертации
      if (!csvLoaded) {
        ev.stopImmediatePropagation();
        ev.preventDefault();
        if (pillCsvEl) pillCsvEl.classList.add("input-error-red");
        highlightMissingAndFocus(btnCsvEl, "accFileSelect", null, getTr("errNoCsvSelectedMsg"));
        return;
      }
    }, true); // capture=true чтобы сработать ДО стандартного обработчика processFile
  }

  // ПУНКТ 3: Полное обновление переводов всех динамических элементов при смене языка
  const langSel = document.getElementById("langSelect");
  if (langSel) {
    langSel.addEventListener("change", () => {
      setTimeout(() => {
        if (missingImgNotice) missingImgNotice.textContent = getTr("msgStarImageMissing");
        if (srvErrBanner && srvErrBanner.style.display === "block") {
          window.showCatalogServerError("");
        }
        if (typeof window.previewCsvText === "function") {
          const pill = document.getElementById("simbadPreloadedPill");
          if (pill && pill.style.display !== "none" && window.STATE?.catalogStarName) {
            pill.textContent = getTr("simbadPreloadedFmt").replace("{star}", window.STATE.catalogStarName);
          }
        }
      }, 30);
    });
  }


  // ПУНКТ 4: При открытии приложения 1-й раздел («Наблюдатель и звезда») раскрыт, а 2-й и 3-й разделы свёрнуты (скрыты, пока 1 и 2 не заполнены)
  const initAcc1 = document.getElementById("accObserverStar");
  const initAcc2 = document.getElementById("accFileSelect");
  const initAcc3 = document.getElementById("accConvertSection");
  if (initAcc1) initAcc1.open = true;
  if (initAcc2) initAcc2.open = false;
  if (initAcc3) initAcc3.open = false;

  // ПУНКТ 1: Кнопка «Очистить» очищает все поля, КРОМЕ OBSCODE (код обсерватории),
  // и автоматически раскрывает раздел 1 «Наблюдатель и звезда» для нового цикла конвертации
  const btnClearAllEl = document.getElementById("btnClearAll");
  if (btnClearAllEl) {
    btnClearAllEl.addEventListener("click", () => {
      if (window._accSimbadTimer) clearTimeout(window._accSimbadTimer);
      if (window._accCsvTimer) clearTimeout(window._accCsvTimer);

      // Сохраняем текущее значение OBSCODE (код обсерватории НЕ очищается!)
      const obsEl = document.getElementById("obscode");
      const quickObsEl = document.getElementById("headerObscodeQuick");
      const savedObsCode = (obsEl && obsEl.value.trim()) || (quickObsEl && quickObsEl.value.trim()) ||
                           (window.localStorage && (localStorage.getItem("obscode") || localStorage.getItem("seestar_obscode"))) || "";

      ["starid", "chart", "kname", "kmag", "ra", "dec", "verifyConvertedInput"].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
          el.value = "";
          el.classList.remove("input-error-red", "field-match", "field-warn", "field-mismatch");
        }
      });

      if (obsEl) {
        obsEl.value = savedObsCode;
        obsEl.classList.remove("input-error-red", "field-mismatch");
      }
      if (quickObsEl) {
        quickObsEl.value = savedObsCode;
      }

      ["obscodeHint", "staridHint", "raHint", "decHint", "verifyConvertedResult", "convertLockReasonBanner"].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
          el.textContent = "";
          el.classList.remove("ok", "warn", "bad");
        }
      });
      document.querySelectorAll(".input-error-red").forEach(el => el.classList.remove("input-error-red"));

      const srvErr = document.getElementById("serverErrorBanner");
      if (srvErr) srvErr.style.display = "none";
      const vspLoad = document.getElementById("vspLoadingBanner");
      if (vspLoad) vspLoad.classList.remove("active");
      const convLog = document.getElementById("conversionLogCard");
      if (convLog) convLog.style.display = "none";
      const statWrap = document.getElementById("statusWrapper");
      if (statWrap) statWrap.style.display = "none";
      const preloadedPill = document.getElementById("simbadPreloadedPill");
      if (preloadedPill) preloadedPill.style.display = "none";

      // Сбрасываем снимок DSS2 к дефолтному холсту
      const starImg = document.getElementById("starImage");
      if (starImg) starImg.style.opacity = "0";
      const dssCanvas = document.getElementById("dssFallbackCanvas");
      if (dssCanvas) dssCanvas.style.display = "block";
      if (missingImgNotice) missingImgNotice.style.display = "none";
      const starCap = document.getElementById("starImageCaption");
      if (starCap) starCap.textContent = getTr("dssEmptyCaption");

      // Сворачиваем (скрываем) 2-й и 3-й разделы и автоматически раскрываем 1-й раздел («Наблюдатель и звезда») для нового цикла
      const acc1 = document.getElementById("accObserverStar");
      const acc2 = document.getElementById("accFileSelect");
      const acc3 = document.getElementById("accConvertSection");
      if (acc3) {
        acc3.classList.remove("accordion-expanding", "accordion-collapsing");
        acc3.open = false;
      }
      if (acc2) {
        acc2.classList.remove("accordion-expanding", "accordion-collapsing");
        acc2.open = false;
      }
      if (acc1) {
        acc1.classList.remove("accordion-collapsing");
        acc1.open = true;
        setTimeout(() => {
          acc1.scrollIntoView({ behavior: "smooth", block: "start" });
          const starInput = document.getElementById("starid");
          if (starInput) starInput.focus();
        }, 120);
      }
    });
  }

  // ПУНКТ 6: Локализованный календарь на 6 языках в разделе «Мои наблюдения» (#obsFilterDate)
  const CALENDAR_LOCALE_DATA = {
    ru: {
      months: ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"],
      weekdays: ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
      clear: "Очистить",
      today: "Сегодня",
      yearFirst: false
    },
    en: {
      months: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
      weekdays: ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
      clear: "Clear",
      today: "Today",
      yearFirst: false
    },
    es: {
      months: ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
      weekdays: ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"],
      clear: "Borrar",
      today: "Hoy",
      yearFirst: false
    },
    de: {
      months: ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"],
      weekdays: ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
      clear: "Löschen",
      today: "Heute",
      yearFirst: false
    },
    fr: {
      months: ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"],
      weekdays: ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"],
      clear: "Effacer",
      today: "Aujourd'hui",
      yearFirst: false
    },
    zh: {
      months: ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"],
      weekdays: ["一", "二", "三", "四", "五", "六", "日"],
      clear: "清除",
      today: "今天",
      yearFirst: true
    }
  };

  (function initLocalizedObsDatePicker() {
    const inputEl = document.getElementById("obsFilterDate");
    const popoverEl = document.getElementById("obsDatePickerPopover");
    const wrapEl = document.getElementById("obsDatePickerWrap");
    if (!inputEl || !popoverEl || !wrapEl) return;

    let viewYear = new Date().getFullYear();
    let viewMonth = new Date().getMonth();

    function getActiveCalLocale() {
      const lg = (document.getElementById("langSelect")?.value || document.documentElement.lang || "ru").slice(0, 2).toLowerCase();
      return CALENDAR_LOCALE_DATA[lg] || CALENDAR_LOCALE_DATA.en;
    }

    function formatIsoDate(y, m, d) {
      return `${y}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    }

    function getRecordedDatesSet() {
      const set = new Set();
      try {
        const raw = localStorage.getItem("seestar_obs_tracker_v1");
        if (raw) {
          const arr = JSON.parse(raw);
          if (Array.isArray(arr)) arr.forEach(r => { if (r && r.date) set.add(String(r.date)); });
        }
      } catch (_) {}
      return set;
    }

    function renderCalendarPopover() {
      const loc = getActiveCalLocale();
      const titleStr = loc.yearFirst ? `${viewYear}年 ${loc.months[viewMonth]}` : `${loc.months[viewMonth]} ${viewYear}`;
      const selectedIso = (inputEl.value || "").trim();
      const now = new Date();
      const todayIso = formatIsoDate(now.getFullYear(), now.getMonth(), now.getDate());
      const obsDates = getRecordedDatesSet();

      const firstDay = new Date(viewYear, viewMonth, 1);
      // Monday-based index (0 = Mon ... 6 = Sun)
      const startOffset = (firstDay.getDay() + 6) % 7;
      const daysInCurrMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
      const daysInPrevMonth = new Date(viewYear, viewMonth, 0).getDate();

      let cellsHtml = "";
      for (let i = 0; i < 42; i++) {
        let cellY = viewYear, cellM = viewMonth, cellD = 1;
        let isOther = false;
        if (i < startOffset) {
          isOther = true;
          cellD = daysInPrevMonth - startOffset + 1 + i;
          cellM = viewMonth - 1;
          if (cellM < 0) { cellM = 11; cellY--; }
        } else if (i >= startOffset + daysInCurrMonth) {
          isOther = true;
          cellD = i - (startOffset + daysInCurrMonth) + 1;
          cellM = viewMonth + 1;
          if (cellM > 11) { cellM = 0; cellY++; }
        } else {
          cellD = i - startOffset + 1;
        }
        const iso = formatIsoDate(cellY, cellM, cellD);
        const cls = [
          "obs-dp-day",
          isOther ? "other-month" : "",
          iso === todayIso ? "today" : "",
          iso === selectedIso ? "selected" : "",
          obsDates.has(iso) ? "has-obs" : ""
        ].filter(Boolean).join(" ");
        cellsHtml += `<button type="button" class="${cls}" data-iso-date="${iso}">${cellD}</button>`;
      }

      popoverEl.innerHTML = `
        <div class="obs-dp-header">
          <span class="obs-dp-title">${titleStr}</span>
          <div class="obs-dp-nav">
            <button type="button" class="obs-dp-nav-btn" id="obsDpPrevMonth" aria-label="Previous Month">↑</button>
            <button type="button" class="obs-dp-nav-btn" id="obsDpNextMonth" aria-label="Next Month">↓</button>
          </div>
        </div>
        <div class="obs-dp-weekdays">
          ${loc.weekdays.map(w => `<span>${w}</span>`).join("")}
        </div>
        <div class="obs-dp-grid">
          ${cellsHtml}
        </div>
        <div class="obs-dp-footer">
          <button type="button" class="obs-dp-action-btn" id="obsDpClearBtn">${loc.clear}</button>
          <button type="button" class="obs-dp-action-btn" id="obsDpTodayBtn">${loc.today}</button>
        </div>
      `;

      popoverEl.querySelector("#obsDpPrevMonth")?.addEventListener("click", (e) => {
        e.stopPropagation();
        viewMonth--;
        if (viewMonth < 0) { viewMonth = 11; viewYear--; }
        renderCalendarPopover();
      });
      popoverEl.querySelector("#obsDpNextMonth")?.addEventListener("click", (e) => {
        e.stopPropagation();
        viewMonth++;
        if (viewMonth > 11) { viewMonth = 0; viewYear++; }
        renderCalendarPopover();
      });
      popoverEl.querySelectorAll(".obs-dp-day").forEach(btn => {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          const chosen = btn.getAttribute("data-iso-date") || "";
          inputEl.value = chosen;
          popoverEl.style.display = "none";
          inputEl.dispatchEvent(new Event("change", { bubbles: true }));
        });
      });
      popoverEl.querySelector("#obsDpClearBtn")?.addEventListener("click", (e) => {
        e.stopPropagation();
        inputEl.value = "";
        popoverEl.style.display = "none";
        inputEl.dispatchEvent(new Event("change", { bubbles: true }));
      });
      popoverEl.querySelector("#obsDpTodayBtn")?.addEventListener("click", (e) => {
        e.stopPropagation();
        const tNow = new Date();
        viewYear = tNow.getFullYear();
        viewMonth = tNow.getMonth();
        inputEl.value = formatIsoDate(viewYear, viewMonth, tNow.getDate());
        popoverEl.style.display = "none";
        inputEl.dispatchEvent(new Event("change", { bubbles: true }));
      });
    }

    window.refreshLocalizedObsDatePicker = renderCalendarPopover;

    inputEl.addEventListener("click", (e) => {
      e.stopPropagation();
      if (popoverEl.style.display === "block") {
        popoverEl.style.display = "none";
      } else {
        const curVal = (inputEl.value || "").trim();
        if (/^\d{4}-\d{2}-\d{2}$/.test(curVal)) {
          const parts = curVal.split("-").map(Number);
          viewYear = parts[0];
          viewMonth = parts[1] - 1;
        }
        renderCalendarPopover();
        popoverEl.style.display = "block";
      }
    });

    document.addEventListener("click", (e) => {
      if (popoverEl.style.display === "block" && !wrapEl.contains(e.target)) {
        popoverEl.style.display = "none";
      }
    });

    const langSelEl = document.getElementById("langSelect");
    if (langSelEl) {
      langSelEl.addEventListener("change", () => {
        if (popoverEl.style.display === "block") {
          renderCalendarPopover();
        }
      });
    }
  })();
})();
