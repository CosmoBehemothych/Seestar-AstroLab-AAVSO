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
        final_content_str = "\n".join(out_lines) + "\n"
        try:
            AavsoNativeAndStorageService.save_converted_session(
                star_name=canonical_target or first_raw_star or starid_ui,
                obscode=obs_clean,
                scope_model=scope_model,
                file_name=suggested_name,
                aavso_csv_content=final_content_str,
            )
        except Exception:
            pass

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
# 5. НАТИВНАЯ ИНТЕГРАЦИЯ С AAVSO (VSX, VSP, AID LIGHT CURVE, TARGET TOOL)
#    И ХРАНИЛИЩЕ ИСТОРИИ КОНВЕРТАЦИЙ В ПАПКЕ ПРОГРАММЫ (Converted_Photometry_Storage)
# ==============================================================================
import csv as _csv
import io as _io
import xml.etree.ElementTree as _ET


def get_program_converted_storage_dir() -> str:
    """
    Возвращает путь к отдельному разделу в папке с программой:
    `<Папка_программы>/Converted_Photometry_Storage`
    (если папка программы доступна только для чтения, создаёт также зеркало в %APPDATA%).
    """
    base_candidates = []
    if getattr(os.sys, "frozen", False):
        exe_dir = os.path.dirname(os.path.abspath(os.sys.executable))
        base_candidates.append(exe_dir)
    here = os.path.dirname(os.path.abspath(__file__))
    # Поднимаемся из backend/ в корень программы (установленной или Source_and_Build)
    prog_root = os.path.dirname(here)
    if prog_root.lower().endswith(".exe"):
        prog_root = os.path.dirname(prog_root)
    base_candidates.append(prog_root)
    base_candidates.append(os.path.dirname(prog_root))

    for base in base_candidates:
        if not base:
            continue
        target = os.path.join(base, "Converted_Photometry_Storage")
        try:
            os.makedirs(os.path.join(target, "sessions"), exist_ok=True)
            db_p = os.path.join(target, "user_converted_photometry_db.json")
            if not os.path.isfile(db_p):
                with open(db_p, "w", encoding="utf-8") as f:
                    json.dump({"version": APP_VERSION, "sessions": [], "points": []}, f, ensure_ascii=False, indent=2)
            return target
        except Exception:
            continue

    appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    fallback = os.path.join(appdata, "Seestar_AstroLab", "Converted_Photometry_Storage")
    os.makedirs(os.path.join(fallback, "sessions"), exist_ok=True)
    return fallback


class AavsoNativeAndStorageService:
    """
    Отвечает за:
    1. Сохранение и чтение всех ранее сконвертированных пользователем данных
       в отдельном разделе папки с программой (`Converted_Photometry_Storage/`).
    2. Загрузку данных о звёздах и срочных запросах напрямую из AAVSO (VSX, VSP,
       REST API v2, Target Tool API, VizieR B/vsx/vsx) вместо SIMBAD.
    3. Загрузку уже известной кривой блеска из базы AAVSO AID (с разделением на
       вклад пользователя и данные других участников AAVSO).
    4. Строгий запрет на выдумывание данных: если данных в базе AAVSO или в
       локальном хранилище нет, возвращает явный статус ошибки без генерации фейковых точек.
    """
    _lock = threading.Lock()

    @classmethod
    def get_storage_db_path(cls) -> str:
        st_dir = get_program_converted_storage_dir()
        return os.path.join(st_dir, "user_converted_photometry_db.json")

    @classmethod
    def load_storage_db(cls) -> Dict[str, Any]:
        db_path = cls.get_storage_db_path()
        if os.path.isfile(db_path):
            try:
                with open(db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    data.setdefault("sessions", [])
                    data.setdefault("points", [])
                    return data
            except Exception:
                pass
        return {"version": APP_VERSION, "sessions": [], "points": []}

    @classmethod
    def save_converted_session(
        cls,
        star_name: str,
        obscode: str,
        scope_model: str,
        file_name: str,
        aavso_csv_content: str,
        points: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Сохраняет сконвертированный отчёт в папку `<Папка_программы>/Converted_Photometry_Storage/sessions/`
        и добавляет все сконвертированные точки в `user_converted_photometry_db.json`.
        """
        canonical_star = PhotometryBackendEngine.normalize_star_for_vsp(star_name)
        st_dir = get_program_converted_storage_dir()
        sessions_dir = os.path.join(st_dir, "sessions")
        os.makedirs(sessions_dir, exist_ok=True)

        safe_fname = re.sub(r'[<>:"/\\|?*]+', "_", str(file_name or "Seestar_AAVSO.csv").strip())
        saved_csv_path = os.path.join(sessions_dir, safe_fname)
        if aavso_csv_content:
            try:
                with open(saved_csv_path, "w", encoding="utf-8") as f:
                    f.write(aavso_csv_content)
            except Exception:
                pass

        # Если список точек не передан явно, парсим их из самого сконвертированного файла AAFF Extended
        extracted_pts: List[Dict[str, Any]] = []
        if points and isinstance(points, list):
            for p in points:
                try:
                    extracted_pts.append({
                        "star": canonical_star or str(p.get("star") or star_name).strip(),
                        "jd": round(float(p["jd"]), 6),
                        "mag": round(float(p["mag"]), 4),
                        "merr": round(float(p.get("merr", 0.015)), 4),
                        "band": str(p.get("band") or p.get("filter") or "TG").strip(),
                        "obscode": str(obscode or p.get("obscode") or "").strip().upper(),
                        "utc": str(p.get("utc") or ""),
                        "scope": str(scope_model or "S50"),
                        "fileName": safe_fname,
                    })
                except Exception:
                    continue
        elif aavso_csv_content:
            for line in aavso_csv_content.splitlines():
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                cols = [c.strip() for c in s.split(",")]
                if len(cols) >= 5:
                    try:
                        extracted_pts.append({
                            "star": PhotometryBackendEngine.normalize_star_for_vsp(cols[0]) or canonical_star,
                            "jd": round(float(cols[1]), 6),
                            "mag": round(float(cols[2]), 4),
                            "merr": round(float(cols[3]), 4),
                            "band": cols[4] or "TG",
                            "obscode": str(obscode or "").strip().upper(),
                            "utc": "",
                            "scope": str(scope_model or "S50"),
                            "fileName": safe_fname,
                        })
                    except Exception:
                        continue

        now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with cls._lock:
            db = cls.load_storage_db()
            existing_keys = {
                (PhotometryBackendEngine.get_canonical_star_key(pt.get("star")), round(float(pt.get("jd", 0.0)), 6))
                for pt in db.get("points", [])
                if pt.get("jd") is not None
            }
            added_count = 0
            for pt in extracted_pts:
                k = (PhotometryBackendEngine.get_canonical_star_key(pt["star"]), pt["jd"])
                if k not in existing_keys:
                    pt["convertedAt"] = now_iso
                    db["points"].append(pt)
                    existing_keys.add(k)
                    added_count += 1

            session_meta = {
                "id": f"sess-{int(time.time() * 1000)}",
                "star": canonical_star or star_name,
                "obscode": str(obscode or "").strip().upper(),
                "scope": str(scope_model or "S50"),
                "fileName": safe_fname,
                "savedPath": saved_csv_path,
                "pointsCount": len(extracted_pts),
                "newUniquePointsAdded": added_count,
                "convertedAt": now_iso,
            }
            db["sessions"].append(session_meta)
            try:
                with open(cls.get_storage_db_path(), "w", encoding="utf-8") as f:
                    json.dump(db, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        return cls.get_converted_history(canonical_star or star_name)

    @classmethod
    def get_converted_history(cls, star_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Возвращает все ранее сконвертированные пользователем точки из папки
        `<Папка_программы>/Converted_Photometry_Storage/`.
        Если данных нет — НЕ выдумывает их, а возвращает честный флаг `hasData: False` и текст ошибки.
        """
        st_dir = get_program_converted_storage_dir()
        db = cls.load_storage_db()
        all_pts = db.get("points", [])
        all_sessions = db.get("sessions", [])

        if star_name and str(star_name).strip():
            target_clean = str(star_name).strip()
            filtered_pts = [
                p for p in all_pts
                if PhotometryBackendEngine.are_same_star(p.get("star"), target_clean)
            ]
            filtered_sessions = [
                s for s in all_sessions
                if PhotometryBackendEngine.are_same_star(s.get("star"), target_clean)
            ]
        else:
            filtered_pts = list(all_pts)
            filtered_sessions = list(all_sessions)

        filtered_pts.sort(key=lambda x: float(x.get("jd", 0.0)))
        has_data = len(filtered_pts) > 0
        err_msg = ""
        if not has_data:
            if star_name:
                err_msg = (
                    f"В локальном разделе программы (Converted_Photometry_Storage) пока нет "
                    f"ранее сконвертированных вами данных для звезды «{star_name}»."
                )
            else:
                err_msg = "В локальном разделе программы (Converted_Photometry_Storage) пока нет сконвертированных файлов."

        return {
            "ok": True,
            "hasData": has_data,
            "storageDir": st_dir,
            "dbPath": cls.get_storage_db_path(),
            "star": star_name or "ALL",
            "pointsCount": len(filtered_pts),
            "sessionsCount": len(filtered_sessions),
            "totalPointsAllStars": len(all_pts),
            "totalSessionsAllStars": len(all_sessions),
            "points": filtered_pts,
            "sessions": filtered_sessions[-50:],
            "error": err_msg,
        }

    @classmethod
    def query_aavso_star(
        cls,
        star_name: str,
        scope_model: str = "S50",
        api_token: str = "",
    ) -> Dict[str, Any]:
        """
        Загружает данные о звезде напрямую из каталогов AAVSO (VSX VOTable, VSP API,
        AAVSO REST API v2 /v2/api/stars/search/, VizieR B/vsx/vsx) вместо SIMBAD.
        Если звезды нет в каталогах AAVSO — НЕ выдумывает данные, а возвращает ошибку.
        """
        raw_q = str(star_name or "").strip()
        if not raw_q:
            return {"ok": False, "error": "Не указан идентификатор звезды (STARID)."}

        norm_q = PhotometryBackendEngine.normalize_star_for_vsp(raw_q)
        # Нормализация Vnnn -> V0nnn для VSX/VizieR
        vsx_q = re.sub(r"^[vV](\d{3})\s+([A-Za-z]{3})$", r"V0\1 \2", norm_q)
        prof = PhotometryBackendEngine.get_scope_profile(scope_model)
        fov_arcmin = prof.get("vspFovArcmin", 60)
        mag_limit = prof.get("magLimit", 14.5)

        result: Dict[str, Any] = {
            "ok": False,
            "star": norm_q,
            "main_id": norm_q,
            "auid": "",
            "ra": None,
            "dec": None,
            "otype_txt": "",
            "sp_type": "",
            "magRange": "",
            "period": None,
            "chartid": "",
            "kname": "",
            "kmag": "",
            "kerr": 0.02,
            "photometry": [],
            "source": "",
        }

        # 1. Официальный AAVSO REST API v2 (/v2/api/stars/search/) при наличии токена
        tok = str(api_token or "").strip()
        if tok:
            try:
                u_v2 = f"https://apps.aavso.org/v2/api/stars/search/?{urllib.parse.urlencode({'name': norm_q})}"
                req = urllib.request.Request(
                    u_v2,
                    headers={"Authorization": f"Token {tok}", "User-Agent": f"SeestarAstroLab/{APP_VERSION}"},
                )
                with urllib.request.urlopen(req, timeout=7.0) as resp:
                    v2_data = json.loads(resp.read().decode("utf-8", errors="replace"))
                items = v2_data.get("results", v2_data) if isinstance(v2_data, dict) else v2_data
                if isinstance(items, list) and items:
                    it0 = items[0]
                    result["main_id"] = it0.get("name") or norm_q
                    result["star"] = result["main_id"]
                    result["auid"] = it0.get("auid") or ""
                    result["ra"] = float(it0["ra"]) if it0.get("ra") is not None else None
                    result["dec"] = float(it0["dec"]) if it0.get("dec") is not None else None
                    result["otype_txt"] = it0.get("var_type") or it0.get("type") or "Variable"
                    if it0.get("max_mag") is not None and it0.get("min_mag") is not None:
                        result["magRange"] = f"{it0['max_mag']} - {it0['min_mag']}"
                    result["period"] = it0.get("period")
                    result["source"] = "AAVSO API v2 (Stars)"
                    result["ok"] = result["ra"] is not None and result["dec"] is not None
            except Exception:
                pass

        # 2. Официальный AAVSO VSX VOTable API (https://www.aavso.org/vsx/index.php?view=query.votable&ident=...)
        if not result["ok"]:
            for cand_ident in (norm_q, vsx_q, raw_q):
                try:
                    u_vsx = f"https://www.aavso.org/vsx/index.php?{urllib.parse.urlencode({'view': 'query.votable', 'ident': cand_ident})}"
                    req = urllib.request.Request(u_vsx, headers={"User-Agent": f"SeestarAstroLab/{APP_VERSION}"})
                    with urllib.request.urlopen(req, timeout=7.0) as resp:
                        xml_str = resp.read().decode("utf-8", errors="replace")
                    if "<VOTABLE" in xml_str.upper():
                        root = _ET.fromstring(xml_str)
                        fields = []
                        for el in root.iter():
                            tag = el.tag.split("}")[-1].upper()
                            if tag == "FIELD":
                                fields.append((el.attrib.get("name") or el.attrib.get("ID") or "").lower())
                            elif tag == "TR":
                                tds = [(td.text or "").strip() for td in el if td.tag.split("}")[-1].upper() == "TD"]
                                if fields and tds:
                                    rmap = dict(zip(fields, tds))
                                    ra_v = rmap.get("radeg") or rmap.get("ra") or rmap.get("raj2000")
                                    dec_v = rmap.get("dedeg") or rmap.get("dec") or rmap.get("dej2000")
                                    if ra_v and dec_v:
                                        result["ra"] = float(ra_v)
                                        result["dec"] = float(dec_v)
                                        result["main_id"] = rmap.get("name") or norm_q
                                        result["star"] = result["main_id"]
                                        result["auid"] = rmap.get("auid") or result["auid"]
                                        result["otype_txt"] = rmap.get("vartype") or rmap.get("type") or "Variable"
                                        mx = rmap.get("maxmag") or rmap.get("max")
                                        mn = rmap.get("minmag") or rmap.get("min")
                                        if mx and mn:
                                            result["magRange"] = f"{mx} - {mn}"
                                        result["period"] = rmap.get("period")
                                        result["source"] = "AAVSO VSX Direct"
                                        result["ok"] = True
                                        break
                        if result["ok"]:
                            break
                except Exception:
                    continue

        # 3. Официальный AAVSO VSP API (https://apps.aavso.org/vsp/api/chart/?format=json&...)
        vsp_urls = [
            f"https://apps.aavso.org/vsp/api/chart/?{urllib.parse.urlencode({'format': 'json', 'star': norm_q, 'fov': str(fov_arcmin), 'maglimit': str(mag_limit)})}"
        ]
        if result["ra"] is not None and result["dec"] is not None:
            vsp_urls.append(
                f"https://apps.aavso.org/vsp/api/chart/?{urllib.parse.urlencode({'format': 'json', 'ra': str(result['ra']), 'dec': str(result['dec']), 'fov': str(fov_arcmin), 'maglimit': str(mag_limit)})}"
            )
        for vu in vsp_urls:
            try:
                req = urllib.request.Request(vu, headers={"User-Agent": f"SeestarAstroLab/{APP_VERSION}"})
                with urllib.request.urlopen(req, timeout=8.0) as resp:
                    vsp_json = json.loads(resp.read().decode("utf-8", errors="replace"))
                if isinstance(vsp_json, dict) and vsp_json.get("chartid"):
                    result["chartid"] = str(vsp_json.get("chartid") or "")
                    if vsp_json.get("auid") and not result["auid"]:
                        result["auid"] = str(vsp_json["auid"])
                    if vsp_json.get("star"):
                        result["main_id"] = PhotometryBackendEngine.normalize_star_for_vsp(vsp_json["star"])
                        result["star"] = result["main_id"]
                    if not result["ok"] and vsp_json.get("ra") and vsp_json.get("dec"):
                        result["ra"], result["dec"] = cls._parse_hms_dms(vsp_json["ra"], vsp_json["dec"])
                        result["source"] = "AAVSO VSP API"
                        result["ok"] = True
                    phot = vsp_json.get("photometry") or []
                    result["photometry"] = phot
                    chk = PhotometryBackendEngine.pick_check_star(
                        phot, result["auid"], prof.get("optCheckMin", 9.0), prof.get("optCheckMax", 13.5)
                    )
                    if chk:
                        result["kname"] = chk["auid"]
                        result["kmag"] = f"{chk['mag']:.3f}"
                        result["kerr"] = chk.get("err", 0.02)
                    break
            except Exception:
                continue

        # 4. Еженедельное зеркало каталога AAVSO VSX в VizieR (B/vsx/vsx)
        if not result["ok"]:
            adql = (
                'SELECT TOP 1 "Name", "RAJ2000", "DEJ2000", "Type", "max", "min", "Period" '
                'FROM "B/vsx/vsx" '
                f"WHERE \"Name\" = '{vsx_q.replace(chr(39), '')}' OR \"Name\" = '{norm_q.replace(chr(39), '')}'"
            )
            for vm in VIZIER_MIRRORS:
                try:
                    q_str = urllib.parse.urlencode({"request": "doQuery", "lang": "ADQL", "format": "json", "query": adql})
                    req = urllib.request.Request(f"{vm['base']}?{q_str}", headers={"User-Agent": f"SeestarAstroLab/{APP_VERSION}"})
                    with urllib.request.urlopen(req, timeout=7.0) as resp:
                        vj = json.loads(resp.read().decode("utf-8", errors="replace"))
                    rows = vj.get("data") or []
                    if rows:
                        r0 = rows[0]
                        result["main_id"] = str(r0[0]).strip()
                        result["star"] = result["main_id"]
                        result["ra"] = float(r0[1])
                        result["dec"] = float(r0[2])
                        result["otype_txt"] = str(r0[3] or "Variable")
                        if r0[4] is not None and r0[5] is not None:
                            result["magRange"] = f"{r0[4]} - {r0[5]}"
                        result["period"] = r0[6]
                        result["source"] = f"AAVSO VSX ({vm['name']})"
                        result["ok"] = True
                        break
                except Exception:
                    continue

        if not result["ok"]:
            result["error"] = (
                f"Ошибка: Звезда «{raw_q}» не найдена в базах данных AAVSO (VSX / VSP). "
                ""
            )
        return result

    @classmethod
    def fetch_aavso_light_curve(
        cls,
        star_name: str,
        days_back: int = 180,
        api_token: str = "",
        user_obscode: str = "",
        max_points: int = 400,
    ) -> Dict[str, Any]:
        """
        Загружает УЖЕ ИЗВЕСТНУЮ кривую блеска звезды из базы AAVSO AID:
        1) Официальный AAVSO REST API v2: GET https://apps.aavso.org/v2/api/observations/photometry/?target=...
        2) Официальный веб-эндпоинт кривых блеска AAVSO:
           GET https://www.aavso.org/vsx/index.php?view=api.delim&ident=...&fromjd=...&tojd=...&delimiter=,
        Разделяет точки на:
          - `otherObserversPoints` (данные других участников AAVSO);
          - `userAavsoPoints` (точки в базе AAVSO с кодом `user_obscode`).
        Также подгружает локально сохранённые ранее сконвертированные точки пользователя
        из папки `<Папка_программы>/Converted_Photometry_Storage/`.
        КРИТИЧЕСКОЕ ПРАВИЛО: Если в AAVSO данных нет — НИКОГДА не выдумывает точки!
        Возвращает явное сообщение об ошибке.
        """
        clean_star = PhotometryBackendEngine.normalize_star_for_vsp(star_name)
        if not clean_star:
            return {
                "ok": False,
                "hasAavsoData": False,
                "error": "Не указано имя звезды (STARID) для запроса кривой блеска из AAVSO.",
                "otherObserversPoints": [],
                "userAavsoPoints": [],
                "localConvertedHistory": cls.get_converted_history(""),
            }

        now_jd = (time.time() / 86400.0) + 2440587.5
        from_jd = now_jd - max(10, int(days_back or 180))
        u_obs = str(user_obscode or "").strip().upper()
        tok = str(api_token or "").strip()

        band_map = {
            "0": "Vis.", "2": "V", "3": "B", "4": "R", "5": "I",
            "7": "U", "8": "CV", "9": "CR", "21": "TB", "22": "TG",
            "23": "TR", "41": "SG", "42": "SR", "43": "SI",
            "50": "TB", "51": "TG", "52": "TR",
        }

        raw_points: List[Dict[str, Any]] = []
        source_used = ""
        network_errors: List[str] = []

        # Канал 1: AAVSO REST API v2 (/v2/api/observations/photometry/)
        if tok:
            try:
                q = urllib.parse.urlencode({"target": clean_star})
                url = f"https://apps.aavso.org/v2/api/observations/photometry/?{q}"
                req = urllib.request.Request(
                    url,
                    headers={"Authorization": f"Token {tok}", "User-Agent": f"SeestarAstroLab/{APP_VERSION}"},
                )
                with urllib.request.urlopen(req, timeout=9.0) as resp:
                    data = json.loads(resp.read().decode("utf-8", errors="replace"))
                for item in (data.get("results") or [])[:max_points]:
                    if item.get("fainterthan"):
                        continue
                    jd_v = float(item["jd_dbl"])
                    mag_v = float(str(item["magnitude"]).lstrip("<"))
                    if jd_v < from_jd:
                        continue
                    err_v = float(item.get("uncertainty") or 0.02)
                    b_raw = str(item.get("band") or "V")
                    raw_points.append({
                        "jd": round(jd_v, 6),
                        "mag": round(mag_v, 4),
                        "merr": round(err_v, 4),
                        "band": band_map.get(b_raw, b_raw),
                        "obscode": str(item.get("obscode") or "").strip().upper(),
                        "source": "AAVSO_API_V2",
                    })
                if raw_points:
                    source_used = "AAVSO API v2 (/v2/api/observations/photometry/)"
            except Exception as e:
                network_errors.append(f"AAVSO API v2: {e}")

        # Канал 2: Официальный эндпоинт выгрузки кривой блеска AAVSO (api.delim)
        if not raw_points:
            try:
                q_params = {
                    "view": "api.delim",
                    "ident": clean_star,
                    "fromjd": f"{from_jd:.4f}",
                    "tojd": f"{now_jd:.4f}",
                    "delimiter": ",",
                }
                url = f"https://www.aavso.org/vsx/index.php?{urllib.parse.urlencode(q_params)}"
                req = urllib.request.Request(url, headers={"User-Agent": f"SeestarAstroLab/{APP_VERSION}"})
                with urllib.request.urlopen(req, timeout=9.0) as resp:
                    csv_text = resp.read().decode("utf-8", errors="replace")
                reader = _csv.DictReader(_io.StringIO(csv_text))
                for row in reader:
                    jd_str = row.get("JD") or row.get("jd")
                    mag_str = str(row.get("Magnitude") or row.get("mag") or "").strip()
                    if not jd_str or not mag_str or mag_str.startswith("<"):
                        continue
                    try:
                        jd_v = float(jd_str)
                        mag_v = float(mag_str)
                        err_v = float(row.get("Uncertainty") or row.get("uncert") or 0.02)
                        band_v = str(row.get("Band") or row.get("band") or "V").strip()
                        obs_v = str(row.get("Observer Code") or row.get("obscode") or "").strip().upper()
                        raw_points.append({
                            "jd": round(jd_v, 6),
                            "mag": round(mag_v, 4),
                            "merr": round(err_v, 4),
                            "band": band_v,
                            "obscode": obs_v,
                            "source": "AAVSO_AID_DELIM",
                        })
                        if len(raw_points) >= max_points:
                            break
                    except Exception:
                        continue
                if raw_points:
                    source_used = "AAVSO AID (vsx/index.php?view=api.delim)"
            except Exception as e:
                network_errors.append(f"AAVSO AID api.delim: {e}")

        raw_points.sort(key=lambda x: x["jd"])
        other_pts = [p for p in raw_points if not u_obs or p.get("obscode") != u_obs]
        user_aavso_pts = [p for p in raw_points if u_obs and p.get("obscode") == u_obs]

        local_history = cls.get_converted_history(clean_star)
        has_aavso = len(raw_points) >= 5

        aavso_err_msg = ""
        if len(raw_points) == 0:
            detail = f" ({'; '.join(network_errors)})" if network_errors else ""
            aavso_err_msg = (
                f"В базе AAVSO (AID) не найдено наблюдений для звезды «{clean_star}» "
                f"за последние {days_back} сут.{detail}"
            )
        elif len(raw_points) < 5:
            aavso_err_msg = (
                f"В базе AAVSO (AID) недостаточно точек для построения кривой блеска звезды «{clean_star}» "
                f"(найдено точек: {len(raw_points)})."
            )
            raw_points = []
            other_pts = []
            user_aavso_pts = []

        return {
            "ok": has_aavso or local_history.get("hasData", False),
            "star": clean_star,
            "hasAavsoData": has_aavso,
            "sourceUsed": source_used,
            "totalAavsoPoints": len(raw_points),
            "otherObserversCount": len(other_pts),
            "userAavsoCount": len(user_aavso_pts),
            "otherObserversPoints": other_pts,
            "userAavsoPoints": user_aavso_pts,
            "localConvertedHistory": local_history,
            "aavsoError": aavso_err_msg,
        }

    @staticmethod
    def _parse_hms_dms(ra_val: Any, dec_val: Any) -> Tuple[float, float]:
        def _conv(v: Any, is_ra: bool) -> float:
            if isinstance(v, (int, float)):
                return float(v)
            s = str(v).strip().replace(":", " ")
            try:
                return float(s)
            except ValueError:
                pass
            parts = [float(p) for p in s.split() if p]
            if not parts:
                return 0.0
            sign = -1.0 if s.startswith("-") else 1.0
            deg = abs(parts[0]) + (parts[1] / 60.0 if len(parts) > 1 else 0.0) + (parts[2] / 3600.0 if len(parts) > 2 else 0.0)
            return deg * 15.0 if is_ra else sign * deg

        return _conv(ra_val, True), _conv(dec_val, False)


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
        elif action == "save_converted_session":
            res = AavsoNativeAndStorageService.save_converted_session(
                star_name=body.get("star", ""),
                obscode=body.get("obscode", ""),
                scope_model=body.get("scopeModel", "S50"),
                file_name=body.get("fileName", "Seestar_AAVSO.csv"),
                aavso_csv_content=body.get("content", ""),
                points=body.get("points"),
            )
            self._send_json(res)
        elif action == "get_converted_history":
            res = AavsoNativeAndStorageService.get_converted_history(body.get("star"))
            self._send_json(res)
        elif action == "query_aavso_star":
            res = AavsoNativeAndStorageService.query_aavso_star(
                star_name=body.get("star", ""),
                scope_model=body.get("scopeModel", "S50"),
                api_token=body.get("apiToken", ""),
            )
            self._send_json(res)
        elif action == "fetch_aavso_light_curve":
            res = AavsoNativeAndStorageService.fetch_aavso_light_curve(
                star_name=body.get("star", ""),
                days_back=int(body.get("daysBack", 180) or 180),
                api_token=body.get("apiToken", ""),
                user_obscode=body.get("obscode", ""),
            )
            self._send_json(res)
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
