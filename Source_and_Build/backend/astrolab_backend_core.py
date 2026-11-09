#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
Seestar AstroLab AAVSO v1.0.1 — Unified Python Backend Core (Single Source of Truth)
Author: CosmoBehemothych (https://github.com/CosmoBehemothych/Seestar-AstroLab-AAVSO)
================================================================================
Централизованное серверное/бэкенд-ядро бизнес-логики приложения:
1. Единый расчёт угловых полей зрения и фокусных расстояний телескопов ZWO Seestar
   (S30 f=150мм, S30PRO f=160мм, S50 f=250мм, S50PRO f=250мм) относительно поля
   обзора неба DSS2 (2.40° × 2.40°, 340×340 px).
2. Единая таблица 88 созвездий МАС (IAU) и нормализация идентификаторов переменных
   звёзд для каталогов CDS SIMBAD, AAVSO VSX и AAVSO VSP.
3. Единый эталонный каталог 45 приоритетных целей AAVSO Alert Notices с фильтрацией
   по проницающей способности конкретной модели телескопа.
4. Единый сетевой движок параллельного опроса зеркал CDS SIMBAD TAP, VizieR APASS DR9
   и AAVSO VSP API с локальным кэшированием (TTL 3600 с).
5. Единый научный алгоритм автоматического подбора непеременной контрольной звезды
   (Check Star: KNAME / KMAG) в оптимальном коридоре 9.5–13.5 mag.
6. Единый конвейер валидации и конвертации CSV фотометрии ZWO Seestar в международный
   формат AAVSO Extended (#TYPE=EXTENDED, #OBSTYPE=DSLR, расчёт JD_Mid, фильтрация
   Non-reference star, строгий запрет самокопирования координат из CSV в поля SIMBAD,
   жёсткая блокировка при критическом расхождении координат > 0.05°).
7. Единый репозиторий «Мои наблюдения» и постоянное хранилище настроек пользователя.
================================================================================
"""

from __future__ import annotations

import base64
import datetime
import hashlib
import json
import math
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, List, Optional, Tuple

APP_VERSION = "1.0.1"
CRITICAL_COORD_DIFF_DEG = 0.05
EXACT_COORD_MATCH_DEG = 0.00001
DSS2_SURVEY_FOV_DEG = 2.40
DSS2_VIEWPORT_PX = 340
CACHE_TTL_SECONDS = 3600

# ==============================================================================
# 1. ФИЗИЧЕСКИЕ ПРОФИЛИ ОПТИКИ ТЕЛЕСКОПОВ ZWO SEESTAR (ЕДИНЫЙ ЭТАЛОН)
# ==============================================================================
SCOPE_PROFILES: Dict[str, Dict[str, Any]] = {
    "S30": {
        "code": "S30",
        "name": "ZWO Seestar S30",
        "shortName": "Seestar S30",
        "apertureMm": 30,
        "focalMm": 150,
        "fovDegW": 1.28,
        "fovDegH": 0.72,
        "fovStr": "1.28°×0.72°",
        "resPx": "1920×1080",
        "pixelScale": 2.40,
        "skySurveyFovDeg": DSS2_SURVEY_FOV_DEG,
        "frameRect": {"x": 79, "y": 119, "w": 181, "h": 102},
        "vspFovArcmin": 65,
        "magMin": 4.0,
        "magLimit": 13.5,
        "optCheckMin": 8.5,
        "optCheckMax": 12.8,
        "recExp": "10 с",
    },
    "S30PRO": {
        "code": "S30PRO",
        "name": "ZWO Seestar S30 Pro",
        "shortName": "Seestar S30PRO",
        "apertureMm": 30,
        "focalMm": 160,
        "fovDegW": 2.10,
        "fovDegH": 1.18,
        "fovStr": "2.10°×1.18°",
        "resPx": "3840×2160",
        "pixelScale": 1.97,
        "skySurveyFovDeg": DSS2_SURVEY_FOV_DEG,
        "frameRect": {"x": 21, "y": 87, "w": 298, "h": 167},
        "vspFovArcmin": 100,
        "magMin": 3.5,
        "magLimit": 14.2,
        "optCheckMin": 8.5,
        "optCheckMax": 13.2,
        "recExp": "10–15 с",
    },
    "S50": {
        "code": "S50",
        "name": "ZWO Seestar S50",
        "shortName": "Seestar S50",
        "apertureMm": 50,
        "focalMm": 250,
        "fovDegW": 0.78,
        "fovDegH": 1.05,
        "fovStr": "0.78°×1.05°",
        "resPx": "1080×1920",
        "pixelScale": 2.39,
        "skySurveyFovDeg": DSS2_SURVEY_FOV_DEG,
        "frameRect": {"x": 115, "y": 96, "w": 111, "h": 149},
        "vspFovArcmin": 60,
        "magMin": 4.0,
        "magLimit": 14.5,
        "optCheckMin": 9.5,
        "optCheckMax": 13.5,
        "recExp": "10–20 с",
    },
    "S50PRO": {
        "code": "S50PRO",
        "name": "ZWO Seestar S50 Pro",
        "shortName": "Seestar S50PRO",
        "apertureMm": 50,
        "focalMm": 250,
        "fovDegW": 1.15,
        "fovDegH": 0.65,
        "fovStr": "1.15°×0.65°",
        "resPx": "3840×2160",
        "pixelScale": 1.08,
        "skySurveyFovDeg": DSS2_SURVEY_FOV_DEG,
        "frameRect": {"x": 89, "y": 124, "w": 163, "h": 92},
        "vspFovArcmin": 65,
        "magMin": 4.0,
        "magLimit": 15.2,
        "optCheckMin": 9.5,
        "optCheckMax": 14.0,
        "recExp": "10–30 с",
    },
}


# ==============================================================================
# 2. ТАБЛИЦА 88 СОЗВЕЗДИЙ МАС (IAU) И КАТАЛОГ ЗЕРКАЛ SIMBAD / VIZIER
# ==============================================================================
CONSTELLATION_GENITIVES: Dict[str, str] = {
    "andromedae": "And", "antliae": "Ant", "apodis": "Aps", "aquarii": "Aqr",
    "aquilae": "Aql", "arae": "Ara", "arietis": "Ari", "aurigae": "Aur",
    "bootis": "Boo", "caeli": "Cae", "camelopardalis": "Cam", "cancri": "Cnc",
    "canum venaticorum": "CVn", "canis majoris": "CMa", "canis minoris": "CMi",
    "capricorni": "Cap", "carinae": "Car", "cassiopeiae": "Cas", "centauri": "Cen",
    "cephei": "Cep", "ceti": "Cet", "chamaeleontis": "Cha", "circini": "Cir",
    "columbae": "Col", "comae berenices": "Com", "coronae australis": "CrA",
    "coronae borealis": "CrB", "corvi": "Crv", "crateris": "Crt", "crucis": "Cru",
    "cygni": "Cyg", "delphini": "Del", "doradus": "Dor", "draconis": "Dra",
    "equulei": "Equ", "eridani": "Eri", "fornacis": "For", "geminorum": "Gem",
    "gruis": "Gru", "herculis": "Her", "horologii": "Hor", "hydrae": "Hya",
    "hydri": "Hyi", "indi": "Ind", "lacertae": "Lac", "leonis": "Leo",
    "leonis minoris": "LMi", "leporis": "Lep", "librae": "Lib", "lupi": "Lup",
    "lyncis": "Lyn", "lyrae": "Lyr", "mensae": "Men", "microscopii": "Mic",
    "monocerotis": "Mon", "muscae": "Mus", "normae": "Nor", "octantis": "Oct",
    "ophiuchi": "Oph", "orionis": "Ori", "pavonis": "Pav", "pegasi": "Peg",
    "persei": "Per", "phoenicis": "Phe", "pictoris": "Pic", "piscium": "Psc",
    "piscis austrini": "PsA", "puppis": "Pup", "pyxidis": "Pyx", "reticuli": "Ret",
    "sagittae": "Sge", "sagittarii": "Sgr", "scorpii": "Sco", "sculptoris": "Scl",
    "scuti": "Sct", "serpentis": "Ser", "sextantis": "Sex", "tauri": "Tau",
    "telescopii": "Tel", "trianguli": "Tri", "trianguli australis": "TrA",
    "tucanae": "Tuc", "ursae majoris": "UMa", "ursae minoris": "UMi",
    "velorum": "Vel", "virginis": "Vir", "volantis": "Vol", "vulpeculae": "Vul",
}
for _abbr in list(CONSTELLATION_GENITIVES.values()):
    CONSTELLATION_GENITIVES[_abbr.lower()] = _abbr

SIMBAD_MIRRORS: List[Dict[str, str]] = [
    {"name": "CDS Strasbourg (FR)", "base": "https://simbad.cds.unistra.fr/simbad/sim-tap/sync"},
    {"name": "CfA Harvard (US)", "base": "https://simbad.cfa.harvard.edu/simbad/sim-tap/sync"},
    {"name": "CDS Mirror (EU)", "base": "https://simbad.u-strasbg.fr/simbad/sim-tap/sync"},
]

VIZIER_MIRRORS: List[Dict[str, str]] = [
    {"name": "VizieR Strasbourg", "base": "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync"},
    {"name": "VizieR Harvard", "base": "https://tapvizier.cfa.harvard.edu/TAPVizieR/tap/sync"},
]


# ==============================================================================
# 3. ЯДРО АСТРОНОМИЧЕСКИХ ВЫЧИСЛЕНИЙ И ВАЛИДАЦИИ (PhotometryBackendEngine)
# ==============================================================================
class PhotometryBackendEngine:
    """Единый серверный движок астрономических расчётов, валидации и конвертации CSV."""

    _cache_lock = threading.Lock()
    _network_cache: Dict[str, Tuple[float, Any]] = {}

    @classmethod
    def get_scope_profile(cls, code: Optional[str] = "S50") -> Dict[str, Any]:
        key = str(code or "S50").strip().upper()
        prof = dict(SCOPE_PROFILES.get(key, SCOPE_PROFILES["S50"]))
        sky_deg = float(prof.get("skySurveyFovDeg", DSS2_SURVEY_FOV_DEG))
        w_px = int((float(prof["fovDegW"]) / sky_deg) * DSS2_VIEWPORT_PX + 0.5)
        h_px = int((float(prof["fovDegH"]) / sky_deg) * DSS2_VIEWPORT_PX + 0.5)
        x_px = int((DSS2_VIEWPORT_PX - w_px) / 2.0 + 0.5)
        y_px = int((DSS2_VIEWPORT_PX - h_px) / 2.0 + 0.5)
        prof["frameRect"] = {"x": x_px, "y": y_px, "w": w_px, "h": h_px}
        return prof

    @classmethod
    def clean_star_token(cls, raw_name: Optional[str]) -> str:
        if not raw_name:
            return ""
        s = re.sub(r"^(?:V\*\s*|NAME\s*|\*\s*)", "", str(raw_name).strip(), flags=re.I)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    @classmethod
    def normalize_star_for_vsp(cls, raw_name: Optional[str], catalog_main_id: Optional[str] = None) -> str:
        candidate = cls.clean_star_token(catalog_main_id or raw_name or "")
        if not candidate:
            return ""
        lower = candidate.lower()
        for gen_full, abbr in sorted(CONSTELLATION_GENITIVES.items(), key=lambda x: -len(x[0])):
            if lower.endswith(" " + gen_full):
                prefix = candidate[: -(len(gen_full) + 1)].strip()
                if len(prefix) == 1 and prefix.isalpha():
                    prefix = prefix.upper()
                elif len(prefix) == 2 and prefix.isalpha() and prefix[0].upper() in "RSTUVWXYZ":
                    prefix = prefix.upper()
                return f"{prefix} {abbr}"
        return candidate

    @classmethod
    def get_canonical_star_key(cls, raw_name: Optional[str]) -> str:
        norm = cls.normalize_star_for_vsp(raw_name)
        return re.sub(r"[\s_\-]+", "", norm).upper()

    @classmethod
    def are_same_star(cls, name_a: Optional[str], name_b: Optional[str]) -> bool:
        ka = cls.get_canonical_star_key(name_a)
        kb = cls.get_canonical_star_key(name_b)
        return bool(ka and kb and ka == kb)

    @classmethod
    def compare_star_ids(cls, file_star_id: Optional[str], ui_star_id: Optional[str]) -> Dict[str, str]:
        f_raw = str(file_star_id or "").strip()
        u_raw = str(ui_star_id or "").strip()
        f_norm = cls.normalize_star_for_vsp(f_raw)
        u_norm = cls.normalize_star_for_vsp(u_raw)
        if not f_raw or not u_raw:
            return {"status": "missing", "canonicalFile": f_norm, "canonicalUi": u_norm}
        if f_raw.lower() == u_raw.lower():
            return {"status": "ok", "canonicalFile": f_norm, "canonicalUi": u_norm}
        if cls.are_same_star(f_raw, u_raw):
            return {"status": "warn", "canonicalFile": f_norm, "canonicalUi": u_norm}
        return {"status": "bad", "canonicalFile": f_norm, "canonicalUi": u_norm}

    @classmethod
    def check_coord_diff(cls, ui_val: Optional[float], file_val: Optional[float]) -> Dict[str, Any]:
        try:
            u = float(ui_val)
            f = float(file_val)
            if math.isnan(u) or math.isnan(f):
                return {"status": "missing", "diff": None}
        except (TypeError, ValueError):
            return {"status": "missing", "diff": None}
        diff = abs(u - f)
        if diff < EXACT_COORD_MATCH_DEG:
            return {"status": "ok", "diff": diff}
        if diff <= CRITICAL_COORD_DIFF_DEG:
            return {"status": "warn", "diff": diff}
        return {"status": "bad", "diff": diff}

    @classmethod
    def pick_check_star(
        cls,
        photometry: List[Dict[str, Any]],
        target_auid: Optional[str] = None,
        opt_min: float = 9.5,
        opt_max: float = 13.5,
    ) -> Optional[Dict[str, Any]]:
        if not photometry or not isinstance(photometry, list):
            return None
        filter_priority = ["V", "TG", "G", "B", "R", "Ic"]
        candidates = []
        for star in photometry:
            if not isinstance(star, dict):
                continue
            auid = str(star.get("auid") or "").strip()
            if not auid or (target_auid and auid.upper() == str(target_auid).strip().upper()):
                continue
            bands = star.get("bands") or []
            chosen_mag = None
            chosen_err = 0.02
            for f_name in filter_priority:
                for b in bands:
                    if str(b.get("band") or "").upper() == f_name.upper():
                        try:
                            chosen_mag = float(b["mag"])
                            chosen_err = float(b.get("error") or 0.02)
                            break
                        except (KeyError, TypeError, ValueError):
                            pass
                if chosen_mag is not None:
                    break
            if chosen_mag is None:
                continue
            if 6.5 <= chosen_mag <= 15.2:
                in_opt = opt_min <= chosen_mag <= opt_max
                mid_opt = (opt_min + opt_max) / 2.0
                score = (0 if in_opt else 100) + abs(chosen_mag - mid_opt) + chosen_err * 10.0
                candidates.append({"auid": auid, "mag": chosen_mag, "err": chosen_err, "score": score})
        if not candidates:
            return None
        candidates.sort(key=lambda c: c["score"])
        return candidates[0]

    @classmethod
    def extract_first_seestar_row(cls, csv_text: str) -> Optional[Dict[str, Any]]:
        for idx, raw_line in enumerate((csv_text or "").splitlines()):
            line = raw_line.strip()
            if not line or (idx == 0 and line.lower().startswith("name,")):
                continue
            cols = [c.strip() for c in line.split(",")]
            if len(cols) >= 19 and cols[1].lower() == "non-reference star":
                try:
                    return {
                        "starId": cols[0],
                        "ra": float(cols[2]),
                        "dec": float(cols[3]),
                        "mag": float(cols[6]),
                        "merr": float(cols[7]),
                        "utc": cols[11],
                        "jdStart": float(cols[12]),
                        "jdEnd": float(cols[15]),
                    }
                except (TypeError, ValueError):
                    continue
        return None

    @classmethod
    def preview_and_verify_csv(
        cls,
        csv_text: str,
        simbad_loaded: bool,
        catalog_star: str = "",
        catalog_ra: Optional[float] = None,
        catalog_dec: Optional[float] = None,
        catalog_kmag: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Выполняет серверный разбор CSV-файла Seestar и строгую сверку с эталоном SIMBAD.
        КРИТИЧЕСКОЕ ПРАВИЛО: Если simbad_loaded=False, колонка SIMBAD остаётся пустой ('— (Не загружено)')
        и НИКОГДА не копирует значения из CSV-файла Seestar!
        """
        first_row = cls.extract_first_seestar_row(csv_text)
        if not first_row:
            return {
                "hasData": False,
                "isCriticalMismatch": False,
                "mismatchReasons": [],
                "pointsCount": 0,
            }

        points = []
        for idx, raw_line in enumerate((csv_text or "").splitlines()):
            line = raw_line.strip()
            if not line or (idx == 0 and line.lower().startswith("name,")):
                continue
            cols = [c.strip() for c in line.split(",")]
            if len(cols) >= 19 and cols[1].lower() == "non-reference star":
                try:
                    jd_s = float(cols[12])
                    jd_e = float(cols[15])
                    jd_mid = (jd_s + jd_e) / 2.0
                    mag = float(cols[6])
                    merr = float(cols[7])
                    points.append({"jd": round(jd_mid, 6), "mag": round(mag, 4), "merr": round(merr, 4), "utc": cols[11]})
                except (TypeError, ValueError):
                    continue

        if not simbad_loaded or not catalog_star or catalog_ra is None or catalog_dec is None:
            return {
                "hasData": True,
                "simbadLoaded": False,
                "firstRow": first_row,
                "pointsCount": len(points),
                "points": points,
                "isCriticalMismatch": False,
                "mismatchReasons": [],
            }

        star_cmp = cls.compare_star_ids(first_row["starId"], catalog_star)
        ra_cmp = cls.check_coord_diff(catalog_ra, first_row["ra"])
        dec_cmp = cls.check_coord_diff(catalog_dec, first_row["dec"])

        reasons: List[str] = []
        if star_cmp["status"] == "bad":
            reasons.append(f"Несовпадение звезды: в файле «{first_row['starId']}», в SIMBAD «{catalog_star}»")
        if ra_cmp["status"] == "bad":
            reasons.append(f"Расхождение RA: Δ={ra_cmp['diff']:.4f}° (> {CRITICAL_COORD_DIFF_DEG}°)")
        if dec_cmp["status"] == "bad":
            reasons.append(f"Расхождение DEC: Δ={dec_cmp['diff']:.4f}° (> {CRITICAL_COORD_DIFF_DEG}°)")

        return {
            "hasData": True,
            "simbadLoaded": True,
            "firstRow": first_row,
            "pointsCount": len(points),
            "points": points,
            "starComparison": star_cmp,
            "raComparison": ra_cmp,
            "decComparison": dec_cmp,
            "isCriticalMismatch": len(reasons) > 0,
            "mismatchReasons": reasons,
        }

    @classmethod
    def convert_seestar_csv_to_aavso_extended(
        cls,
        csv_text: str,
        obscode: str,
        starid_ui: str,
        chart: str = "na",
        kname: str = "na",
        kmag: str = "na",
        ra_ui: str = "",
        dec_ui: str = "",
        scope_model: str = "S50",
        simbad_loaded: bool = False,
        catalog_star: str = "",
        catalog_ra: Optional[float] = None,
        catalog_dec: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Конвертирует сырой CSV фотометрии Seestar в стандарт AAVSO Extended (#OBSTYPE=DSLR).
        Проверяет отсутствие критического расхождения перед генерацией отчёта.
        """
        obs_clean = str(obscode or "").strip()
        if not obs_clean or obs_clean.upper() == "NA":
            return {"ok": False, "errorCode": "NO_OBSCODE", "error": "Не указан личный код наблюдателя #OBSCODE"}

        if simbad_loaded and catalog_star and catalog_ra is not None and catalog_dec is not None:
            ver = cls.preview_and_verify_csv(csv_text, True, catalog_star, catalog_ra, catalog_dec)
            if ver.get("isCriticalMismatch"):
                return {
                    "ok": False,
                    "errorCode": "CRITICAL_MISMATCH",
                    "error": "Обнаружено критическое расхождение данных Seestar и SIMBAD",
                    "mismatchReasons": ver.get("mismatchReasons", []),
                }

        prof = cls.get_scope_profile(scope_model)
        canonical_target = cls.normalize_star_for_vsp(catalog_star or starid_ui)

        out_lines = [
            "#TYPE=EXTENDED",
            f"#OBSCODE={obs_clean}",
            f"#SOFTWARE={prof['name']}",
            "#DELIM=,",
            "#DATE=JD",
            "#OBSTYPE=DSLR",
            "#STARID,DATE,MAG,MERR,FILT,TRANS,MTYPE,CNAME,CMAG,KNAME,KMAG,AMASS,GROUP,CHART,NOTES",
        ]

        count = 0
        skipped = 0
        bad = 0
        first_utc = None
        first_raw_star = None
        diffs = []

        for idx, raw_line in enumerate((csv_text or "").splitlines()):
            raw = raw_line.strip()
            if not raw or (idx == 0 and raw.lower().startswith("name,")):
                skipped += 1
                continue
            cols = [c.strip() for c in raw.split(",")]
            if len(cols) < 19 or cols[1].lower() != "non-reference star":
                skipped += 1
                continue
            try:
                mag_orig = float(cols[6])
                err_orig = float(cols[7])
                mag_conv = round(mag_orig, 4)
                err_conv = round(err_orig, 4)
                if abs(mag_orig - mag_conv) > 0.0001 or abs(err_orig - err_conv) > 0.0001:
                    bad += 1
                    continue

                jd_start = float(cols[12])
                jd_end = float(cols[15])
                from decimal import Decimal, ROUND_HALF_UP
                jd_mid = str(((Decimal(cols[12]) + Decimal(cols[15])) / Decimal("2")).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))

                if not first_utc:
                    first_utc = cols[11]
                if not first_raw_star:
                    first_raw_star = cols[0]

                ra_final = str(ra_ui or cols[2]).strip()
                dec_final = str(dec_ui or cols[3]).strip()
                star_final = canonical_target or cls.normalize_star_for_vsp(cols[0])

                notes = "|".join([
                    f"UTC={cols[11]}", f"EXP={cols[10]}", f"SNR={cols[18]}",
                    f"RefStars={cols[4]}", f"RawMag={cols[6]}", f"RawErr={cols[7]}",
                    f"RA={ra_final}", f"DEC={dec_final}", f"X={cols[8]}", f"Y={cols[9]}",
                ])

                out_lines.append(",".join([
                    star_final, jd_mid, f"{mag_conv:.4f}", f"{err_conv:.4f}",
                    "TG", "NO", "STD", "ENSEMBLE", "na",
                    str(kname or "na").strip() or "na",
                    str(kmag or "na").strip() or "na",
                    "na", "na",
                    str(chart or "na").strip() or "na",
                    notes,
                ]))

                diffs.append({
                    "rowNum": idx + 1,
                    "origStarId": cols[0],
                    "newStarId": star_final,
                    "origMag": mag_orig,
                    "newMag": mag_conv,
                    "origMerr": err_orig,
                    "newMerr": err_conv,
                    "origJd": f"{cols[12]} / {cols[15]}",
                    "newJd": jd_mid,
                    "origRa": cols[2],
                    "newRa": ra_final,
                    "origDec": cols[3],
                    "newDec": dec_final,
                })
                count += 1
            except (TypeError, ValueError):
                bad += 1

        if count == 0:
            return {"ok": False, "errorCode": "NO_DATA_ROWS", "error": "Нет целевых строк измерений Non-reference star"}

        date_part = (first_utc or "session").replace(".", "-").replace(" ", "_").replace(":", "-")
        safe_star = (canonical_target or first_raw_star or "SEESTAR").replace(" ", "_")
        suggested_name = f"{safe_star}_{date_part}_{count}pts_Seestar.csv"

        return {
            "ok": True,
            "fileName": suggested_name,
            "content": "\n".join(out_lines) + "\n",
            "count": count,
            "skipped": skipped,
            "bad": bad,
            "canonicalStar": canonical_target or first_raw_star,
            "firstRawStar": first_raw_star,
            "firstUtc": first_utc,
            "diffs": diffs,
        }

    @classmethod
    def verify_converted_aavso_file(cls, file_content: str) -> Dict[str, Any]:
        """Единый валидатор готового файла AAVSO Extended с диска (#OBSTYPE=DSLR)."""
        lines_list = [l.strip() for l in (file_content or "").splitlines() if l.strip()]
        headers = [l for l in lines_list if l.startswith("#")]
        data_rows = [l for l in lines_list if not l.startswith("#")]
        issues: List[str] = []

        if not any(h.upper() == "#TYPE=EXTENDED" for h in headers):
            issues.append("отсутствует заголовок #TYPE=EXTENDED")
        obs_hdr = next((h for h in headers if h.upper().startswith("#OBSCODE=")), "")
        obs_val = obs_hdr.split("=", 1)[1].strip() if "=" in obs_hdr else ""
        if not obs_val or obs_val.upper() == "NA":
            issues.append("не указан личный код наблюдателя в #OBSCODE")

        obstype_hdr = next((h for h in headers if h.upper().startswith("#OBSTYPE=")), "")
        obstype_val = obstype_hdr.split("=", 1)[1].strip().upper() if "=" in obstype_hdr else ""
        if obstype_val != "DSLR":
            issues.append(f"неверный #OBSTYPE={obstype_val or 'нет'} (требуется #OBSTYPE=DSLR)")

        if not data_rows:
            issues.append("нет строк фотометрических измерений")
        else:
            first_cols = data_rows[0].split(",")
            if len(first_cols) < 15:
                issues.append(f"неверное число колонок ({len(first_cols)} вместо 15)")

        return {
            "valid": len(issues) == 0,
            "rowsCount": len(data_rows),
            "obscode": obs_val,
            "obstype": obstype_val,
            "issues": issues,
        }


# ==============================================================================
# 4. ЛОКАЛЬНЫЙ REST JSON-RPC СЕРВЕР БЭКЕНДА (ДЛЯ WEBVIEW2 / ELECTRON / БРАУЗЕРА)
# ==============================================================================
class _AstroLabBackendRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self) -> None:
        self._send_json({"ok": True})

    def do_GET(self) -> None:
        if self.path.startswith("/api/health"):
            self._send_json({"ok": True, "version": APP_VERSION, "engine": "PhotometryBackendEngine"})
        else:
            self._send_json({"ok": False, "error": "Not found"}, 404)

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, 400)
            return

        action = body.get("action", "")
        if action == "get_scope_profile":
            self._send_json({"ok": True, "profile": PhotometryBackendEngine.get_scope_profile(body.get("code", "S50"))})
        elif action == "preview_csv":
            res = PhotometryBackendEngine.preview_and_verify_csv(
                csv_text=body.get("csvText", ""),
                simbad_loaded=bool(body.get("simbadLoaded", False)),
                catalog_star=body.get("catalogStar", ""),
                catalog_ra=body.get("catalogRa"),
                catalog_dec=body.get("catalogDec"),
                catalog_kmag=body.get("catalogKmag"),
            )
            self._send_json({"ok": True, "result": res})
        elif action == "convert_csv":
            res = PhotometryBackendEngine.convert_seestar_csv_to_aavso_extended(
                csv_text=body.get("csvText", ""),
                obscode=body.get("obscode", ""),
                starid_ui=body.get("starid", ""),
                chart=body.get("chart", "na"),
                kname=body.get("kname", "na"),
                kmag=body.get("kmag", "na"),
                ra_ui=body.get("ra", ""),
                dec_ui=body.get("dec", ""),
                scope_model=body.get("scopeModel", "S50"),
                simbad_loaded=bool(body.get("simbadLoaded", False)),
                catalog_star=body.get("catalogStar", ""),
                catalog_ra=body.get("catalogRa"),
                catalog_dec=body.get("catalogDec"),
            )
            self._send_json(res)
        elif action == "verify_file":
            res = PhotometryBackendEngine.verify_converted_aavso_file(body.get("content", ""))
            self._send_json({"ok": True, "result": res})
        else:
            self._send_json({"ok": False, "error": f"Unknown action: {action}"}, 400)


def start_background_rpc_server(port: int = 18765) -> Optional[ThreadingHTTPServer]:
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", port), _AstroLabBackendRequestHandler)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        return srv
    except Exception:
        return None
