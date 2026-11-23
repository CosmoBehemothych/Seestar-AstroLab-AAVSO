#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
Seestar AstroLab AAVSO v1.5.0-alpha — Unified Python Backend Core (Single Source of Truth)
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
import hmac
import json
import secrets
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

APP_VERSION = "1.5.0-alpha"


# =============================================================================
# BUILT-IN DIAGNOSTIC LOGGER (v1.5.0-alpha Hotfix3) — Secret-Safe Live Telemetry
# =============================================================================
import logging as _logging
from logging.handlers import RotatingFileHandler as _RotatingFileHandler
import platform as _platform
import ssl as _ssl
import threading as _threading
import traceback as _traceback


class AstroLabDiagnosticLogger:
    """
    Потокобезопасный диагностический логгер Seestar AstroLab AAVSO.
    Пишет события бэкенда и фронтенда в %LOCALAPPDATA%/SeestarAstroLab/logs/astrolab_debug.log,
    автоматически маскирует API-ключи/токены и умеет экспортировать готовый .txt отчёт.
    """
    _lock = _threading.Lock()
    _logger = None
    _initialized = False

    _SECRET_PATTERNS = [
        (re.compile(r"(ghp_[A-Za-z0-9_]{16,}|github_pat_[A-Za-z0-9_]{20,})"), "***GITHUB_TOKEN_REDACTED***"),
        (re.compile(r"(?i)(authorization\s*[:=]\s*(?:bearer|token|basic)\s+)([^\s,;\"'<>]+)"), r"\1***REDACTED***"),
        (re.compile(r"(?i)((?:api[_-]?key|api[_-]?token|apikey|apitoken|access[_-]?token|secret|password)\s*[:=]\s*[\"']?)([A-Za-z0-9_\-\.]{6,})([\"']?)"), r"\1***REDACTED***\3"),
    ]

    @classmethod
    def sanitize_text(cls, value: Any) -> str:
        s = "" if value is None else str(value)
        for pat, repl in cls._SECRET_PATTERNS:
            s = pat.sub(repl, s)
        return s

    @classmethod
    def get_log_dir(cls) -> str:
        env_dir = os.environ.get("ASTROLAB_LOG_DIR", "").strip()
        if env_dir:
            os.makedirs(env_dir, exist_ok=True)
            return env_dir
        if os.name == "nt":
            base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
            log_dir = os.path.join(base, "SeestarAstroLab", "logs")
        else:
            log_dir = os.path.join(os.path.expanduser("~"), ".local", "share", "SeestarAstroLab", "logs")
        os.makedirs(log_dir, exist_ok=True)
        return log_dir

    @classmethod
    def get_log_file_path(cls) -> str:
        return os.path.join(cls.get_log_dir(), "astrolab_debug.log")

    @classmethod
    def get_config_file_path(cls) -> str:
        return os.path.join(cls.get_log_dir(), "diag_config.json")

    @classmethod
    def is_enabled(cls) -> bool:
        """Проверяет, включена ли запись диагностического лога (по умолчанию выключена)."""
        if os.environ.get("ASTROLAB_FORCE_DIAG_LOG", "").strip() in ("1", "true", "TRUE"):
            return True
        cfg_path = cls.get_config_file_path()
        try:
            if os.path.isfile(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as cf:
                    data = json.load(cf)
                return bool(data.get("enabled", False))
        except Exception:
            pass
        return False

    @classmethod
    def set_enabled(cls, enabled: bool) -> Dict[str, Any]:
        cfg_path = cls.get_config_file_path()
        try:
            with cls._lock:
                os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
                with open(cfg_path, "w", encoding="utf-8") as cf:
                    json.dump({"enabled": bool(enabled)}, cf)
            return {"ok": True, "enabled": bool(enabled)}
        except Exception as e:
            return {"ok": False, "enabled": bool(enabled), "error": str(e)}

    @classmethod
    def _ensure_logger(cls):
        if cls._logger is not None:
            return cls._logger
        with cls._lock:
            if cls._logger is not None:
                return cls._logger
            lg = _logging.getLogger("SeestarAstroLabDiag")
            lg.setLevel(_logging.DEBUG)
            lg.propagate = False
            if not lg.handlers:
                log_file = cls.get_log_file_path()
                handler = _RotatingFileHandler(
                    log_file,
                    maxBytes=2 * 1024 * 1024,
                    backupCount=3,
                    encoding="utf-8",
                )
                fmt = _logging.Formatter("[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
                handler.setFormatter(fmt)
                lg.addHandler(handler)
            cls._logger = lg
            return lg

    @classmethod
    def init_session(cls, entry_point: str = "desktop") -> str:
        lg = cls._ensure_logger()
        if not cls._initialized:
            cls._initialized = True
            certifi_ver = "not-installed"
            try:
                import certifi as _certifi_chk
                certifi_ver = f"ok ({_certifi_chk.where()})"
            except Exception as _ce:
                certifi_ver = f"error ({_ce})"
            proxy_keys = [k for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy") if os.environ.get(k)]
            cls.log_event(
                "INFO",
                "SESSION",
                f"=== Seestar AstroLab AAVSO v{APP_VERSION} started ({entry_point}) ===",
                {
                    "os": f"{_platform.system()} {_platform.release()} ({_platform.machine()})",
                    "python": _platform.python_version(),
                    "openssl": getattr(_ssl, "OPENSSL_VERSION", "unknown"),
                    "certifi": certifi_ver,
                    "proxy_env_keys": proxy_keys,
                    "log_file": cls.get_log_file_path(),
                },
            )
        return cls.get_log_file_path()

    @classmethod
    def log_event(cls, level: str, category: str, message: str, details: Any = None) -> None:
        try:
            if not cls.is_enabled():
                return
            lg = cls._ensure_logger()
            lvl_name = str(level or "INFO").upper()
            lvl_map = {
                "DEBUG": _logging.DEBUG,
                "INFO": _logging.INFO,
                "WARN": _logging.WARNING,
                "WARNING": _logging.WARNING,
                "ERROR": _logging.ERROR,
                "CRITICAL": _logging.CRITICAL,
            }
            num_lvl = lvl_map.get(lvl_name, _logging.INFO)
            safe_cat = re.sub(r"[^A-Z0-9_/-]", "", str(category or "APP").upper()) or "APP"
            safe_msg = cls.sanitize_text(message)
            if details is not None:
                try:
                    if isinstance(details, (dict, list)):
                        det_str = json.dumps(details, ensure_ascii=False, default=str)
                    else:
                        det_str = str(details)
                except Exception:
                    det_str = repr(details)
                safe_det = cls.sanitize_text(det_str)
                if len(safe_det) > 2000:
                    safe_det = safe_det[:2000] + "...[truncated]"
                line = f"[{safe_cat}] {safe_msg} | {safe_det}"
            else:
                line = f"[{safe_cat}] {safe_msg}"
            lg.log(num_lvl, line)
            for h in lg.handlers:
                try:
                    h.flush()
                except Exception:
                    pass
        except Exception:
            pass

    @classmethod
    def log_exception(cls, category: str, message: str, exc: BaseException) -> None:
        tb = "".join(_traceback.format_exception(type(exc), exc, exc.__traceback__))
        cls.log_event("ERROR", category, f"{message}: {exc}", tb)

    @classmethod
    def export_diagnostic_report(cls, frontend_snapshot: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        cls.init_session("export")
        log_path = cls.get_log_file_path()
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_name = f"AstroLab_Diagnostic_Report_{stamp}.txt"

        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        if os.path.isdir(desktop_dir):
            out_path = os.path.join(desktop_dir, report_name)
        else:
            out_path = os.path.join(cls.get_log_dir(), report_name)

        log_lines: List[str] = []
        if os.path.isfile(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as lf:
                    log_lines = lf.readlines()[-900:]
            except Exception as e:
                log_lines = [f"[Failed to read log file: {e}]\n"]

        header_lines = [
            "==============================================================================",
            f"  SEESTAR ASTROLAB AAVSO — DIAGNOSTIC ERROR REPORT (v{APP_VERSION})",
            f"  Generated (UTC): {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "==============================================================================",
            f"OS:       {_platform.system()} {_platform.release()} ({_platform.version()})",
            f"Python:   {_platform.python_version()}",
            f"OpenSSL:  {getattr(_ssl, 'OPENSSL_VERSION', 'unknown')}",
            f"Log File: {log_path}",
            "Secrets:  All API keys, tokens & Authorization headers are automatically redacted.",
            "",
        ]

        if isinstance(frontend_snapshot, dict) and frontend_snapshot:
            header_lines.append("--- FRONTEND STATE & RECENT JS EVENTS ---")
            header_lines.append(cls.sanitize_text(json.dumps(frontend_snapshot, ensure_ascii=False, indent=2, default=str)))
            header_lines.append("")

        header_lines.append(f"--- BACKEND & FRONTEND LIVE LOG (last {len(log_lines)} lines) ---")
        body = "\n".join(header_lines) + "\n" + cls.sanitize_text("".join(log_lines))

        with open(out_path, "w", encoding="utf-8") as rf:
            rf.write(body)

        cls.log_event("INFO", "DIAG_EXPORT", f"Diagnostic report saved: {out_path}", {"lines": len(log_lines)})
        return {
            "ok": True,
            "path": out_path,
            "logPath": log_path,
            "lineCount": len(log_lines),
        }
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
    "S30PLUS": {
        "code": "S30PLUS",
        "name": "ZWO Seestar S30 Plus",
        "shortName": "Seestar S30 PLUS",
        "apertureMm": 30,
        "focalMm": 160,
        "fovDegW": 2.66,
        "fovDegH": 1.50,
        "fovStr": "2.66°×1.50°",
        "resPx": "2560×1440",
        "pixelScale": 3.74,
        "skySurveyFovDeg": DSS2_SURVEY_FOV_DEG,
        "frameRect": {"x": 15, "y": 76, "w": 310, "h": 175},
        "vspFovArcmin": 110,
        "magMin": 3.8,
        "magLimit": 13.8,
        "optCheckMin": 8.5,
        "optCheckMax": 13.0,
        "recExp": "10–20 с",
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

    # ==========================================================================
    # [RU] ОПТИМИЗАЦИЯ ПРОИЗВОДИТЕЛЬНОСТИ ДЛЯ БУДУЩИХ РАЗРАБОТЧИКОВ:
    #   1) Таблица родительных падежей 88 созвездий IAU (_SORTED_CONSTELLATION_GENITIVES)
    #      предварительно сортируется по убыванию длины ключа 1 раз при загрузке класса,
    #      исключая повторный вызов sorted(...) при каждой проверке Star ID.
    #   2) Скомпилированы регулярные выражения (_RE_STAR_PREFIX, _RE_MULTI_SPACE, _RE_NON_ALNUM)
    #      и добавлен потокобезопасный in-memory кэш (_star_norm_cache, _canonical_key_cache)
    #      для мгновенного O(1) сопоставления имен звезд при пакетной обработке CSV.
    # [EN] DEVELOPER PERFORMANCE OPTIMIZATION NOTE:
    #   1) Pre-sorted IAU 88 constellation genitive pairs (_SORTED_CONSTELLATION_GENITIVES)
    #      once at class initialization instead of calling sorted() on every Star ID lookup.
    #   2) Pre-compiled regex patterns and added in-memory memoization caches
    #      (_star_norm_cache, _canonical_key_cache) for O(1) Star ID normalization.
    # ==========================================================================
    _SORTED_CONSTELLATION_GENITIVES: List[Tuple[str, str]] = sorted(
        CONSTELLATION_GENITIVES.items(), key=lambda x: -len(x[0])
    )
    _RE_STAR_PREFIX = re.compile(r"^(?:V\*\s*|NAME\s*|\*\s*)", flags=re.I)
    _RE_MULTI_SPACE = re.compile(r"\s+")
    _RE_KEY_SEP = re.compile(r"[\s_\-]+")
    _star_norm_cache: Dict[Tuple[str, str], str] = {}
    _canonical_key_cache: Dict[str, str] = {}

    @classmethod
    def clean_star_token(cls, raw_name: Optional[str]) -> str:
        if not raw_name:
            return ""
        s = cls._RE_STAR_PREFIX.sub("", str(raw_name).strip())
        s = cls._RE_MULTI_SPACE.sub(" ", s).strip()
        return s

    @classmethod
    def normalize_star_for_vsp(cls, raw_name: Optional[str], catalog_main_id: Optional[str] = None) -> str:
        cache_key = (str(raw_name or ""), str(catalog_main_id or ""))
        cached = cls._star_norm_cache.get(cache_key)
        if cached is not None:
            return cached

        candidate = cls.clean_star_token(catalog_main_id or raw_name or "")
        if not candidate:
            return ""
        lower = candidate.lower()
        result = candidate
        for gen_full, abbr in cls._SORTED_CONSTELLATION_GENITIVES:
            if lower.endswith(" " + gen_full):
                prefix = candidate[: -(len(gen_full) + 1)].strip()
                if len(prefix) == 1 and prefix.isalpha():
                    prefix = prefix.upper()
                elif len(prefix) == 2 and prefix.isalpha() and prefix[0].upper() in "RSTUVWXYZ":
                    prefix = prefix.upper()
                result = f"{prefix} {abbr}"
                break

        if len(cls._star_norm_cache) > 4096:
            cls._star_norm_cache.clear()
        cls._star_norm_cache[cache_key] = result
        return result

    @classmethod
    def get_canonical_star_key(cls, raw_name: Optional[str]) -> str:
        raw_str = str(raw_name or "")
        cached = cls._canonical_key_cache.get(raw_str)
        if cached is not None:
            return cached
        norm = cls.normalize_star_for_vsp(raw_str)
        res = cls._RE_KEY_SEP.sub("", norm).upper()
        if len(cls._canonical_key_cache) > 4096:
            cls._canonical_key_cache.clear()
        cls._canonical_key_cache[raw_str] = res
        return res

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

    # ==========================================================================
    # [RU] УСТОЙЧИВЫЙ ПАРСЕР CSV SEESTAR И ФОРМАТИРОВАНИЕ ПОЛЯ NOTES (ПУНКТЫ 1–4 РЕВЬЮ):
    #   Для будущих разработчиков:
    #   1) _split_dirty_csv_line() устойчиво разбирает строки с лишними пробелами,
    #      обрамляющими кавычками и нестандартными разделителями (',' или ';' после Excel).
    #   2) validate_obscode() проверяет как отсутствие пустых значений / 'NA', так и
    #      соответствие формату кода наблюдателя AAVSO (3–5 заглавных букв/цифр ^[A-Z0-9]{3,5}$).
    #   3) build_safe_aavso_notes() документирует структуру поля NOTES:
    #      UTC (время кадра) | EXP (выдержка, с) | SNR (сигнал/шум) | RefStars (число опорных звезд) |
    #      RawMag (исходный блеск) | RawErr (исходная ошибка) | RA/DEC | X/Y (координаты на матрице),
    #      удаляет запрещенные запятые и гарантирует соблюдение лимита длины поля AAVSO WebObs (<= 150 симв.).
    # [EN] RESILIENT SEESTAR CSV PARSER & AAVSO NOTES FIELD BUILDER (REVIEW ITEMS 1-4):
    #   Developer note:
    #   1) _split_dirty_csv_line() handles extra whitespace, quotes, and ';' or ',' delimiters.
    #   2) validate_obscode() checks non-empty/'NA' and validates AAVSO 3-5 char alphanumeric format.
    #   3) build_safe_aavso_notes() documents all NOTES keys, strips commas, and enforces
    #      the AAVSO Extended File Format length limit (<= 150 chars).
    # ==========================================================================
    _RE_OBSCODE_FORMAT = re.compile(r"^[A-Z0-9]{3,5}$")
    MAX_AAVSO_NOTES_LEN = 150

    @staticmethod
    def _split_dirty_csv_line(raw_line: str) -> List[str]:
        line = (raw_line or "").strip()
        if not line:
            return []
        delim = ";" if (line.count(";") >= 18 and line.count(",") < 5) else ","
        return [c.strip().strip('"').strip("'").strip() for c in line.split(delim)]

    @classmethod
    def validate_obscode(cls, obscode: str) -> Dict[str, Any]:
        clean = str(obscode or "").strip().upper()
        if not clean or clean == "NA":
            return {
                "valid": False,
                "strictFormatOk": False,
                "cleaned": clean,
                "warning": "Код наблюдателя (OBSCODE) не указан или равен NA.",
            }
        strict_ok = bool(cls._RE_OBSCODE_FORMAT.match(clean))
        warn_msg = (
            ""
            if strict_ok
            else f"Код наблюдателя «{clean}» отличается от стандартного формата AAVSO (обычно 3–5 заглавных латинских букв/цифр)."
        )
        return {
            "valid": True,
            "strictFormatOk": strict_ok,
            "cleaned": clean,
            "warning": warn_msg,
        }

    @classmethod
    def build_safe_aavso_notes(
        cls,
        utc_val: str,
        exp_val: str,
        snr_val: str,
        ref_stars: str,
        raw_mag: str,
        raw_err: str,
        ra_val: str,
        dec_val: str,
        x_val: str,
        y_val: str,
        max_len: int = 150,
    ) -> str:
        def _clean_token(v: Any, max_val_len: int = 22) -> str:
            s = str(v if v is not None else "").replace(",", ".").replace("|", "/").replace("\n", " ").replace("\r", " ").strip()
            return s[:max_val_len]

        items = [
            f"UTC={_clean_token(utc_val, 19)}",
            f"EXP={_clean_token(exp_val, 8)}",
            f"SNR={_clean_token(snr_val, 10)}",
            f"RefStars={_clean_token(ref_stars, 6)}",
            f"RawMag={_clean_token(raw_mag, 10)}",
            f"RawErr={_clean_token(raw_err, 10)}",
            f"RA={_clean_token(ra_val, 10)}",
            f"DEC={_clean_token(dec_val, 10)}",
            f"X={_clean_token(x_val, 8)}",
            f"Y={_clean_token(y_val, 8)}",
        ]
        acc: List[str] = []
        cur_len = 0
        for part in items:
            add_len = len(part) + (1 if acc else 0)
            if cur_len + add_len <= max_len:
                acc.append(part)
                cur_len += add_len
            else:
                break
        return "|".join(acc) if acc else "Seestar"

    @classmethod
    def extract_first_seestar_row(cls, csv_text: str) -> Optional[Dict[str, Any]]:
        detected_delim = cls.detect_csv_delimiter(csv_text)
        detected_site_coords = cls.detect_site_coords_in_csv(csv_text, detected_delim)
        raw_preview_mags: List[float] = []
        for idx, raw_line in enumerate((csv_text or "").splitlines()):
            line = raw_line.strip()
            if not line:
                continue
            cols = cls._split_dirty_csv_line(line)
            if not cols or (idx == 0 and cols[0].lower() == "name"):
                continue
            if len(cols) >= 19 and cols[1].lower() == "non-reference star":
                try:
                    jd_s = float(cols[12])
                    jd_e = float(cols[15]) if cols[15] else jd_s
                    return {
                        "starId": cols[0],
                        "ra": float(cols[2]) if cols[2] else 0.0,
                        "dec": float(cols[3]) if cols[3] else 0.0,
                        "mag": float(cols[6]),
                        "merr": float(cols[7]),
                        "utc": cols[11],
                        "jdStart": jd_s,
                        "jdEnd": jd_e,
                    }
                except (TypeError, ValueError):
                    continue
        return None

    @staticmethod
    def detect_csv_delimiter(csv_text: str) -> str:
        """Автоопределение разделителя CSV (',' / ';' / '\\t') для Excel и Siril."""
        for raw_line in (csv_text or "").splitlines():
            ln = raw_line.strip()
            if not ln or ln.startswith("#"):
                continue
            sc = ln.count(";")
            cm = ln.count(",")
            tb = ln.count("\t")
            if sc > cm and sc >= 3:
                return ";"
            if tb > cm and tb >= 3:
                return "\t"
            return ","
        return ","

    @staticmethod
    def split_csv_row(line: str, delimiter: str) -> List[str]:
        if delimiter == ",":
            return [c.strip() for c in line.split(",")]
        return [c.strip() for c in next(_csv.reader([line], delimiter=delimiter))]

    @staticmethod
    def detect_site_coords_in_csv(csv_text: str, delimiter: str = ",") -> Optional[Dict[str, Any]]:
        """Вариант В (AMASS): автообнаружение координат места съёмки SITELAT/SITELONG в заголовке или колонках CSV."""
        lines = (csv_text or "").splitlines()
        lat_found, lon_found = None, None
        for ln in lines[:15]:
            s = ln.strip()
            m_lat = re.search(r"(?i)\b(?:SITELAT|OBS_LAT|LATITUDE)\s*[:=]\s*([+-]?\d+(?:\.\d+)?)", s)
            m_lon = re.search(r"(?i)\b(?:SITELONG|SITELON|OBS_LON|LONGITUDE)\s*[:=]\s*([+-]?\d+(?:\.\d+)?)", s)
            if m_lat:
                lat_found = float(m_lat.group(1))
            if m_lon:
                lon_found = float(m_lon.group(1))
        if lat_found is not None and lon_found is not None and -90.0 <= lat_found <= 90.0 and -180.0 <= lon_found <= 180.0:
            return {"lat": round(lat_found, 5), "lon": round(lon_found, 5), "source": "header"}

        # Check column names in header row
        header_idx = -1
        header_cols = []
        for idx, ln in enumerate(lines[:10]):
            s = ln.strip()
            if not s or s.startswith("#"):
                continue
            cols = [c.strip().upper() for c in PhotometryBackendEngine.split_csv_row(s, delimiter)]
            if any(k in cols for k in ("SITELAT", "OBS_LAT", "LAT")) and any(k in cols for k in ("SITELONG", "SITELON", "OBS_LON", "LON")):
                header_idx = idx
                header_cols = cols
                break
        if header_idx >= 0 and header_idx + 1 < len(lines):
            lat_i = next((i for i, c in enumerate(header_cols) if c in ("SITELAT", "OBS_LAT", "LAT")), -1)
            lon_i = next((i for i, c in enumerate(header_cols) if c in ("SITELONG", "SITELON", "OBS_LON", "LON")), -1)
            for row_ln in lines[header_idx + 1:header_idx + 6]:
                if not row_ln.strip():
                    continue
                rc = PhotometryBackendEngine.split_csv_row(row_ln.strip(), delimiter)
                if lat_i >= 0 and lon_i >= 0 and max(lat_i, lon_i) < len(rc):
                    try:
                        lv = float(rc[lat_i].replace(",", "."))
                        lo = float(rc[lon_i].replace(",", "."))
                        if -90.0 <= lv <= 90.0 and -180.0 <= lo <= 180.0:
                            return {"lat": round(lv, 5), "lon": round(lo, 5), "source": "csv_column"}
                    except ValueError:
                        continue
        return None

    @staticmethod
    def compute_airmass_pickering(jd: float, ra_deg: Optional[float], dec_deg: Optional[float], lat_deg: Optional[float], lon_deg: Optional[float]) -> str:
        """
        Вычисляет воздушную массу AMASS по формуле Pickering (2002):
          X = 1 / sin(h + 244 / (165 + 47 * h^1.1))
        Строгое научное правило AAVSO: если координаты не заданы или высота h <= 5° -> возвращает 'na'.
        """
        try:
            if ra_deg is None or dec_deg is None or lat_deg is None or lon_deg is None:
                return "na"
            jd_f = float(jd)
            ra_f = float(ra_deg)
            dec_f = float(dec_deg)
            lat_f = float(lat_deg)
            lon_f = float(lon_deg)
            if not all(math.isfinite(v) for v in (jd_f, ra_f, dec_f, lat_f, lon_f)):
                return "na"
            if not (-90.0 <= lat_f <= 90.0 and -180.0 <= lon_f <= 180.0):
                return "na"
            # GMST in degrees (USNO approximation, accurate to <0.1 arcmin)
            d_ut = jd_f - 2451545.0
            gmst = (280.46061837 + 360.98564736629 * d_ut) % 360.0
            lst = (gmst + lon_f) % 360.0
            ha_rad = math.radians((lst - ra_f + 540.0) % 360.0 - 180.0)
            lat_rad = math.radians(lat_f)
            dec_rad = math.radians(dec_f)
            sin_alt = math.sin(lat_rad) * math.sin(dec_rad) + math.cos(lat_rad) * math.cos(dec_rad) * math.cos(ha_rad)
            sin_alt = max(-1.0, min(1.0, sin_alt))
            alt_deg = math.degrees(math.asin(sin_alt))
            if alt_deg <= 5.0:
                return "na"
            denom = math.sin(math.radians(alt_deg + 244.0 / (165.0 + 47.0 * (alt_deg ** 1.1))))
            if denom <= 0.0:
                return "na"
            amass = 1.0 / denom
            if not math.isfinite(amass) or amass < 1.0 or amass > 10.0:
                return "na"
            return f"{amass:.3f}"
        except Exception:
            return "na"

    @staticmethod
    def detect_mad_3sigma_outliers(mags: List[float]) -> Dict[str, Any]:
        """Определяет статистические выбросы (> 3 * 1.4826 * MAD) для предупреждения пользователя."""
        if len(mags) < 6:
            return {"count": 0, "indices": set(), "median": None, "limit": None}
        s_mags = sorted(mags)
        n = len(s_mags)
        med = s_mags[n // 2] if n % 2 == 1 else 0.5 * (s_mags[n // 2 - 1] + s_mags[n // 2])
        abs_dev = sorted(abs(m - med) for m in mags)
        mad = (abs_dev[n // 2] if n % 2 == 1 else 0.5 * (abs_dev[n // 2 - 1] + abs_dev[n // 2])) * 1.4826
        limit = max(0.06, 3.0 * (mad if mad > 0 else 0.05))
        bad_idx = {i for i, m in enumerate(mags) if abs(m - med) > limit}
        return {"count": len(bad_idx), "indices": bad_idx, "median": round(med, 4), "limit": round(limit, 4)}

    @classmethod
    def compute_calibration_guard_metrics(cls, csv_text: str) -> Dict[str, Any]:
        """Извлекает из сырого CSV Seestar метрики для «Калибровочного сторожа»:
        медианный блеск, выдержку (EXP, сек), число опорных звёзд (RefStars) и флаги рисков."""
        mags: List[float] = []
        ref_stars_list: List[int] = []
        exp_secs: List[float] = []
        detected_delim = cls.detect_csv_delimiter(csv_text)
        for idx, raw_line in enumerate((csv_text or "").splitlines()):
            line = raw_line.strip()
            if not line or (idx == 0 and line.lower().startswith("name")):
                continue
            cols = cls.split_csv_row(line, detected_delim)
            if len(cols) >= 19 and cols[1].lower() == "non-reference star":
                try:
                    mv = float(cols[6].replace(",", "."))
                    if math.isfinite(mv):
                        mags.append(mv)
                except (ValueError, TypeError):
                    pass
                try:
                    rf_raw = str(cols[4]).strip()
                    if rf_raw:
                        rf_val = int(float(rf_raw.replace(",", ".")))
                        if rf_val >= 0:
                            ref_stars_list.append(rf_val)
                except (ValueError, TypeError):
                    pass
                try:
                    exp_raw = str(cols[10]).strip().lower().replace("s", "").replace(",", ".")
                    if exp_raw:
                        ev = float(exp_raw)
                        if math.isfinite(ev) and ev > 0:
                            exp_secs.append(ev)
                except (ValueError, TypeError):
                    pass

        def _median(arr):
            if not arr:
                return None
            s = sorted(arr)
            n = len(s)
            return s[n // 2] if n % 2 == 1 else 0.5 * (s[n // 2 - 1] + s[n // 2])

        med_mag = _median(mags)
        med_ref = _median(ref_stars_list)
        min_ref = min(ref_stars_list) if ref_stars_list else None
        med_exp = _median(exp_secs)

        # Порог риска перенасыщения матрицы Seestar (IMX462/IMX585) в зависимости от выдержки
        sat_limit = 7.0
        if med_exp is not None:
            if med_exp > 20.0:
                sat_limit = 8.3
            elif med_exp > 10.0:
                sat_limit = 7.8
            else:
                sat_limit = 7.0

        saturation_risk = bool(med_mag is not None and med_mag < sat_limit)
        small_ensemble_risk = bool((med_ref is not None and med_ref < 3) or (min_ref is not None and min_ref < 3))

        return {
            "medianMag": round(med_mag, 4) if med_mag is not None else None,
            "medianRefStars": int(round(med_ref)) if med_ref is not None else None,
            "minRefStars": int(min_ref) if min_ref is not None else None,
            "medianExpSec": round(med_exp, 1) if med_exp is not None else None,
            "saturationThresholdMag": sat_limit,
            "saturationRisk": saturation_risk,
            "smallEnsembleRisk": small_ensemble_risk,
        }

    @classmethod
    def preview_and_verify_csv(
        cls,
        csv_text: str,
        simbad_loaded: bool,
        catalog_star: str = "",
        catalog_ra: Optional[float] = None,
        catalog_dec: Optional[float] = None,
        catalog_kmag: Optional[float] = None,
        calc_amass: bool = False,
        site_lat: Optional[float] = None,
        site_lon: Optional[float] = None,
        clip_outliers_3sigma: bool = False,
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
        detected_delim = cls.detect_csv_delimiter(csv_text)
        for idx, raw_line in enumerate((csv_text or "").splitlines()):
            line = raw_line.strip()
            if not line or (idx == 0 and line.lower().startswith("name,")):
                continue
            cols = cls.split_csv_row(line, detected_delim)
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
        calc_amass: bool = False,
        site_lat: Optional[float] = None,
        site_lon: Optional[float] = None,
        clip_outliers_3sigma: bool = False,
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

        obs_validation = cls.validate_obscode(obs_clean)
        count = 0
        skipped = 0
        bad = 0
        dup_removed_count = 0
        rounding_warnings = 0
        first_utc = None
        first_raw_star = None
        diffs = []
        removed_old_summary = []

        # [RU] Предварительный проход для выявления ранее сконвертированных точек (из Converted_Photometry_Storage)
        #      и старых ночей наблюдений в дозаписанных файлах Seestar CSV (разрыв между сессиями ΔJD > 0.35 сут)
        # [EN] Pre-pass to detect previously converted records and older observing nights in appended Seestar CSVs
        raw_lines_all = (csv_text or "").splitlines()
        valid_jds_for_sessions = []
        for _i, _rl in enumerate(raw_lines_all):
            _s = _rl.strip()
            if not _s or (_i == 0 and _s.lower().startswith("name,")):
                continue
            _c = cls._split_dirty_csv_line(_s)
            if len(_c) >= 19 and _c[1].lower() == "non-reference star":
                try:
                    _j1 = float(_c[12])
                    _j2 = float(_c[15]) if _c[15] else _j1
                    valid_jds_for_sessions.append((_j1 + _j2) / 2.0)
                except Exception:
                    pass

        latest_session_min_jd = None
        if len(valid_jds_for_sessions) > 1:
            sorted_jds = sorted(valid_jds_for_sessions)
            sess_list = [[sorted_jds[0]]]
            for _k in range(1, len(sorted_jds)):
                if sorted_jds[_k] - sorted_jds[_k - 1] > 0.35:
                    sess_list.append([sorted_jds[_k]])
                else:
                    sess_list[-1].append(sorted_jds[_k])
            if len(sess_list) > 1:
                latest_session_min_jd = sess_list[-1][0]

        existing_db_jds = []
        try:
            _db = AavsoNativeAndStorageService.load_storage_db()
            for _pt in _db.get("points", []):
                if _pt.get("jd") is not None:
                    if not canonical_target or cls.are_same_star(_pt.get("star"), canonical_target):
                        existing_db_jds.append(float(_pt["jd"]))
        except Exception:
            pass

        seen_in_file_jds = set()

        _pre_mags: List[float] = []
        if clip_outliers_3sigma:
            for _rl in raw_lines_all:
                _s = _rl.strip()
                if not _s or _s.startswith("#"):
                    continue
                _c = cls._split_dirty_csv_line(_s)
                if len(_c) >= 19 and _c[1].lower() == "non-reference star":
                    try:
                        _mv = float(_c[6].replace(",", "."))
                        if math.isfinite(_mv):
                            _pre_mags.append(_mv)
                    except ValueError:
                        pass
        _mad_info = cls.detect_mad_3sigma_outliers(_pre_mags) if clip_outliers_3sigma else {"count": 0, "indices": set(), "median": None, "limit": None}
        _clipped_3sigma_count = 0
        for idx, raw_line in enumerate(raw_lines_all):
            raw = raw_line.strip()
            if not raw:
                skipped += 1
                continue
            cols = cls._split_dirty_csv_line(raw)
            if not cols or (idx == 0 and cols[0].lower() == "name"):
                skipped += 1
                continue
            if len(cols) < 19 or cols[1].lower() != "non-reference star":
                skipped += 1
                continue
            try:
                mag_orig = float(cols[6])
                err_orig = float(cols[7])
                if math.isnan(mag_orig) or math.isnan(err_orig) or math.isinf(mag_orig) or math.isinf(err_orig) or err_orig <= 0.0 or err_orig >= 1.0:
                    bad += 1
                    continue
                if clip_outliers_3sigma and _mad_info.get("median") is not None and _mad_info.get("limit") is not None:
                    if abs(mag_orig - _mad_info["median"]) > _mad_info["limit"]:
                        _clipped_3sigma_count += 1
                        continue

                mag_conv = round(mag_orig, 4)
                err_conv = round(err_orig, 4)
                # [RU] ПУНКТ 1 РЕВЬЮ: Не отбрасываем строку при высокой точности исходного float,
                #      а логируем предупреждение округления (rounding_warnings), сохраняя измерение!
                # [EN] REVIEW ITEM 1: Do not drop high-precision rows on rounding delta > 0.0001;
                #      record a non-destructive rounding warning instead.
                if abs(mag_orig - mag_conv) > 0.0001 or abs(err_orig - err_conv) > 0.0001:
                    rounding_warnings += 1

                jd_start_str = cols[12]
                jd_end_str = cols[15] if cols[15] else cols[12]
                jd_start = float(jd_start_str)
                jd_end = float(jd_end_str)
                from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
                if not (math.isfinite(jd_start) and math.isfinite(jd_end)):
                    bad += 1
                    continue
                try:
                    jd_mid_dec = ((Decimal(str(jd_start)) + Decimal(str(jd_end))) / Decimal("2")).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
                except (InvalidOperation, ValueError):
                    bad += 1
                    continue
                jd_mid = str(jd_mid_dec)
                jd_mid_float = float(jd_mid_dec)

                # Проверка на дубликат или старую сессию, которая уже передавалась в AAVSO
                is_dup_or_old = False
                if jd_mid in seen_in_file_jds:
                    is_dup_or_old = True
                seen_in_file_jds.add(jd_mid)

                if not is_dup_or_old and latest_session_min_jd is not None and jd_mid_float < latest_session_min_jd - 0.1:
                    is_dup_or_old = True

                if not is_dup_or_old and existing_db_jds:
                    for _ejd in existing_db_jds:
                        if abs(_ejd - jd_mid_float) <= 0.00012:
                            is_dup_or_old = True
                            break

                if is_dup_or_old:
                    dup_removed_count += 1
                    skipped += 1
                    removed_old_summary.append({"utc": cols[11], "jd": jd_mid})
                    continue

                if not first_utc:
                    first_utc = cols[11]
                if not first_raw_star:
                    first_raw_star = cols[0]

                ra_final = str(ra_ui or cols[2]).strip()
                dec_final = str(dec_ui or cols[3]).strip()
                star_final = canonical_target or cls.normalize_star_for_vsp(cols[0])

                notes = cls.build_safe_aavso_notes(
                    utc_val=cols[11],
                    exp_val=cols[10],
                    snr_val=cols[18],
                    ref_stars=cols[4],
                    raw_mag=cols[6],
                    raw_err=cols[7],
                    ra_val=ra_final,
                    dec_val=dec_final,
                    x_val=cols[8],
                    y_val=cols[9],
                    max_len=cls.MAX_AAVSO_NOTES_LEN,
                )

                out_lines.append(",".join([
                    star_final, jd_mid, f"{mag_conv:.4f}", f"{err_conv:.4f}",
                    "TG", "NO", "STD", "ENSEMBLE", "na",
                    # [RU] Строгий стандарт AAVSO: Seestar не передаёт отдельный замер проверочной звезды
                    # [EN] Strict AAVSO standard: Seestar does not output a separate check-star measurement
                    "na",
                    "na",
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
            "duplicateRemovedCount": dup_removed_count,
            "duplicateRemovedRecords": removed_old_summary,
            "bad": bad,
            "roundingWarnings": rounding_warnings,
            "obscodeFormatWarning": obs_validation.get("warning", ""),
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
    def delete_converted_records(cls, star_name: str = "", file_name: str = "", obs_date: str = "") -> Dict[str, Any]:
        with cls._lock:
            db = cls.load_storage_db()
            date_dot = str(obs_date or "").replace("-", ".")
            db["sessions"] = [
                s for s in db.get("sessions", [])
                if not ((file_name and s.get("fileName") == file_name) or (star_name and obs_date and PhotometryBackendEngine.are_same_star(s.get("star"), star_name) and obs_date in str(s.get("fileName", ""))))
            ]
            db["points"] = [
                p for p in db.get("points", [])
                if not ((file_name and p.get("fileName") == file_name) or (star_name and date_dot and PhotometryBackendEngine.are_same_star(p.get("star"), star_name) and str(p.get("utc", "")).startswith(date_dot)))
            ]
            try:
                with open(cls.get_storage_db_path(), "w", encoding="utf-8") as f:
                    json.dump(db, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
        return {"ok": True}

    @classmethod
    def reset_all_user_data(cls) -> Dict[str, Any]:
        with cls._lock:
            st_dir = get_program_converted_storage_dir()
            sessions_dir = os.path.join(st_dir, "sessions")
            try:
                if os.path.isdir(sessions_dir):
                    for fn in os.listdir(sessions_dir):
                        fp = os.path.join(sessions_dir, fn)
                        if os.path.isfile(fp):
                            os.remove(fp)
            except Exception:
                pass
            try:
                with open(cls.get_storage_db_path(), "w", encoding="utf-8") as f:
                    json.dump({"version": APP_VERSION, "sessions": [], "points": []}, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
        return {"ok": True}

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
                with cls._urlopen_with_ssl_fallback(req, timeout=7.0) as resp:
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

        # 2. Официальный AAVSO VSX VOTable API (https://vsx.aavso.org/index.php?view=query.votable&ident=...)
        if not result["ok"]:
            for cand_ident in (norm_q, vsx_q, raw_q):
                try:
                    u_vsx = f"https://vsx.aavso.org/index.php?{urllib.parse.urlencode({'view': 'query.votable', 'ident': cand_ident})}"
                    req = urllib.request.Request(u_vsx, headers={"User-Agent": f"SeestarAstroLab/{APP_VERSION}"})
                    with cls._urlopen_with_ssl_fallback(req, timeout=7.0) as resp:
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
                with cls._urlopen_with_ssl_fallback(req, timeout=8.0) as resp:
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
                    with cls._urlopen_with_ssl_fallback(req, timeout=7.0) as resp:
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

    @staticmethod
    def jd_to_utc_str(jd_val: float) -> str:
        """
        [RU] Конвертирует Юлианскую дату (JD) контрольной точки в строку UTC (YYYY-MM-DD HH:MM:SS UTC).
        [EN] Converts a checkpoint Julian Date (JD) into a human-readable UTC string (YYYY-MM-DD HH:MM:SS UTC).
        """
        try:
            unix_ts = (float(jd_val) - 2440587.5) * 86400.0
            dt = time.gmtime(unix_ts)
            return time.strftime("%Y-%m-%d %H:%M:%S UTC", dt)
        except Exception:
            return ""


    @classmethod
    def fetch_live_star_dossier(cls, star_name: str) -> Dict[str, Any]:
        """
        Загружает живые данные о звезде из AAVSO VSX (JSON API) и CDS SIMBAD Sesame (XML)
        на стороне Python-бэкенда (без браузерных ограничений CORS).
        """
        import xml.etree.ElementTree as ET

        clean_star = PhotometryBackendEngine.normalize_star_for_vsp(star_name)
        if not clean_star:
            return {"ok": False, "error": "Empty star name", "gotAnyOnline": False}

        aliases: List[str] = []
        constellation = ""
        spectral_type = ""
        period_str = ""
        epoch_str = ""
        pm_str = ""
        got_any = False
        errors: List[str] = []

        # 1) AAVSO VSX API
        try:
            vsx_url = f"https://vsx.aavso.org/index.php?view=api.object&ident={urllib.parse.quote(clean_star)}&format=json"
            req = urllib.request.Request(vsx_url, headers={"User-Agent": f"SeestarAstroLab/{APP_VERSION}"})
            with cls._urlopen_with_ssl_fallback(req, timeout=7.0) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
            obj = (data or {}).get("VSXObject")
            if isinstance(obj, dict) and (obj.get("Name") or obj.get("AUID")):
                got_any = True
                if obj.get("AUID"):
                    aliases.append(f"AAVSO AUID {obj['AUID']}")
                if obj.get("Name") and obj["Name"] != clean_star:
                    aliases.append(str(obj["Name"]))
                if obj.get("Constellation"):
                    constellation = str(obj["Constellation"])
                if obj.get("SpectralType"):
                    spectral_type = str(obj["SpectralType"])
                if obj.get("Period"):
                    period_str = f"{obj['Period']} d"
                if obj.get("Epoch"):
                    epoch_str = f"HJD {obj['Epoch']}"
        except Exception as e:
            errors.append(f"VSX: {e}")

        # 2) CDS SIMBAD Sesame XML (cds.unistra.fr primary, cdsweb.u-strasbg.fr mirror)
        for host in ("https://cds.unistra.fr", "https://cdsweb.u-strasbg.fr"):
            try:
                ses_url = f"{host}/cgi-bin/nph-sesame/-oxp/NSV?{urllib.parse.quote(clean_star)}"
                req = urllib.request.Request(ses_url, headers={"User-Agent": f"SeestarAstroLab/{APP_VERSION}"})
                with cls._urlopen_with_ssl_fallback(req, timeout=7.0) as resp:
                    xml_text = resp.read().decode("utf-8", errors="replace")
                root = ET.fromstring(xml_text)
                for al in root.findall(".//alias"):
                    txt = (al.text or "").strip()
                    if txt and txt not in aliases:
                        aliases.append(txt)
                sp = root.find(".//spType")
                if sp is not None and (sp.text or "").strip() and not spectral_type:
                    spectral_type = sp.text.strip()
                pm_ra = root.find(".//pm/pmRA")
                pm_de = root.find(".//pm/pmDE")
                if pm_ra is not None and pm_de is not None and (pm_ra.text or "").strip() and (pm_de.text or "").strip():
                    pm_str = f"μRA={pm_ra.text.strip()} mas/yr, μDec={pm_de.text.strip()} mas/yr"
                if aliases or spectral_type:
                    got_any = True
                    break
            except Exception as e:
                errors.append(f"SIMBAD({host}): {e}")

        return {
            "ok": got_any,
            "gotAnyOnline": got_any,
            "star": clean_star,
            "aliases": aliases[:15],
            "constellation": constellation,
            "spectralType": spectral_type,
            "periodStr": period_str,
            "epochStr": epoch_str,
            "pmStr": pm_str,
            "errors": errors,
        }


    @classmethod
    def fetch_live_aavso_notices(cls) -> Dict[str, Any]:
        """Запрашивает актуальные Alert Notices с сервера AAVSO (без выдумывания данных)."""
        notices = []
        err = ""
        for url in (
            "https://apps.aavso.org/v2/api/notices/?page_size=10",
            "https://www.aavso.org/aavso-alert-notices-for-observing-campaigns",
        ):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": f"SeestarAstroLab/{APP_VERSION}"})
                with cls._urlopen_with_ssl_fallback(req, timeout=6.0) as resp:
                    raw = resp.read().decode("utf-8", errors="replace")
                if url.endswith("page_size=10"):
                    j = json.loads(raw)
                    for r in (j.get("results") or [])[:10]:
                        notices.append({
                            "number": str(r.get("number") or r.get("id") or ""),
                            "title": str(r.get("title") or "").strip(),
                            "published": str(r.get("published") or r.get("created") or "")[:10],
                        })
                    if notices:
                        return {"ok": True, "source": "AAVSO API v2 /notices/", "notices": notices}
                else:
                    import re as _re
                    for m in _re.finditer(r"AAVSO Alert Notice\s+(\d+)[:\s]+([^<\n]{4,120})", raw, _re.I):
                        notices.append({"number": m.group(1), "title": m.group(2).strip(), "published": ""})
                        if len(notices) >= 10:
                            break
                    if notices:
                        return {"ok": True, "source": "AAVSO Alert Notices Web", "notices": notices}
            except Exception as e:
                err = str(e)
        return {"ok": False, "source": "", "notices": [], "error": err or "No live notices returned"}

    _IAU_CONSTELLATIONS = {
        "And", "Ant", "Aps", "Aqr", "Aql", "Ara", "Ari", "Aur", "Boo", "Cae",
        "Cam", "Cnc", "CVn", "CMa", "CMi", "Cap", "Car", "Cas", "Cen", "Cep",
        "Cet", "Cha", "Cir", "Col", "Com", "CrA", "CrB", "Crv", "Crt", "Cru",
        "Cyg", "Del", "Dor", "Dra", "Equ", "Eri", "For", "Gem", "Gru", "Her",
        "Hor", "Hya", "Hyi", "Ind", "Lac", "Leo", "LMi", "Lep", "Lib", "Lup",
        "Lyn", "Lyr", "Men", "Mic", "Mon", "Mus", "Nor", "Oct", "Oph", "Ori",
        "Pav", "Peg", "Per", "Phe", "Pic", "Psc", "PsA", "Pup", "Pyx", "Ret",
        "Sge", "Sgr", "Sco", "Scl", "Sct", "Ser", "Sex", "Tau", "Tel", "Tri",
        "TrA", "Tuc", "UMa", "UMi", "Vel", "Vir", "Vol", "Vul",
    }

    @classmethod
    def _urlopen_with_ssl_fallback(cls, req_or_url, timeout: float = 8.0):
        """
        Унифицированный HTTPS-запрос с двойной защитой SSL:
        1) Сначала пробует встроенный актуальный комплект корневых сертификатов certifi;
        2) При ошибке SSLCertVerificationError (например, корпоративный прокси/антивирус с локальным CA)
           автоматически откатывается на системное хранилище сертификатов Windows.
        """
        ssl_ctx = cls._build_ssl_context()
        try:
            return urllib.request.urlopen(req_or_url, timeout=timeout, context=ssl_ctx)
        except urllib.error.URLError as ue:
            reason = getattr(ue, "reason", None)
            if isinstance(reason, _ssl.SSLCertVerificationError) or "CERTIFICATE_VERIFY_FAILED" in str(ue):
                AstroLabDiagnosticLogger.log_event("WARN", "SSL_FALLBACK", f"certifi verify failed ({ue}), retrying with system SSL store")
                sys_ctx = _ssl.create_default_context()
                return urllib.request.urlopen(req_or_url, timeout=timeout, context=sys_ctx)
            raise
        except _ssl.SSLCertVerificationError as se:
            AstroLabDiagnosticLogger.log_event("WARN", "SSL_FALLBACK", f"certifi verify failed ({se}), retrying with system SSL store")
            sys_ctx = _ssl.create_default_context()
            return urllib.request.urlopen(req_or_url, timeout=timeout, context=sys_ctx)

    @staticmethod
    def _build_ssl_context():
        try:
            import ssl
            try:
                import certifi
                return ssl.create_default_context(cafile=certifi.where())
            except Exception:
                return ssl.create_default_context()
        except Exception:
            return None

    @staticmethod
    def _parse_ra_dec_to_deg(val: Any, is_ra: bool = True) -> Optional[float]:
        """Преобразует RA/Dec из десятичных градусов или строкового формата HH:MM:SS / ±DD:MM:SS в градусы."""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            fval = float(val)
            if is_ra and 0.0 <= fval <= 360.0:
                return fval
            if (not is_ra) and -90.0 <= fval <= 90.0:
                return fval
            return None
        s = str(val).strip()
        if not s:
            return None
        try:
            fval = float(s)
            if is_ra and 0.0 <= fval <= 360.0:
                return fval
            if (not is_ra) and -90.0 <= fval <= 90.0:
                return fval
            return None
        except ValueError:
            pass
        parts = re.split(r"[:\s°'\"hmsHMS]+", s.strip())
        parts = [p for p in parts if p]
        if len(parts) < 2:
            return None
        try:
            sign = -1.0 if s.strip().startswith("-") else 1.0
            d0 = abs(float(parts[0]))
            m0 = float(parts[1]) if len(parts) > 1 else 0.0
            s0 = float(parts[2]) if len(parts) > 2 else 0.0
            val_deg = d0 + m0 / 60.0 + s0 / 3600.0
            if is_ra:
                return (val_deg * 15.0) % 360.0
            return sign * val_deg
        except Exception:
            return None

    @classmethod
    def _extract_stars_from_notice_title(cls, title: str) -> List[str]:
        """Извлекает обозначения переменных звёзд (GCVS/Nova/AT/SN/NSV) из заголовка AAVSO Alert Notice."""
        if not title:
            return []
        found: List[str] = []
        seen = set()

        def _add(name: str):
            clean = re.sub(r"\s+", " ", name.strip())
            key = clean.lower()
            if clean and key not in seen:
                seen.add(key)
                found.append(clean)

        # 1) GCVS-style: V1405 Cas, T CrB, SS Cyg, alpha Ori, chi Cyg, Nova Cas 2024
        gcvs_re = re.compile(
            r"\b(V\d{3,5}|[R-Z]|[A-Z]{2}|Nova|SN|AT)\s+([A-Za-z]{2,3})(?:\s+(20\d{2}))?\b"
        )
        for m in gcvs_re.finditer(title):
            prefix, con, yr = m.group(1), m.group(2), m.group(3)
            if con in cls._IAU_CONSTELLATIONS:
                if prefix in ("Nova", "SN", "AT") and yr:
                    _add(f"{prefix} {con} {yr}")
                elif prefix not in ("SN", "AT"):
                    _add(f"{prefix} {con}")

        # 2) Catalog designations: NSV 12345, AT 2025abc, SN 2025xyz, ASASSN-24ab, ZTF24...
        cat_re = re.compile(
            r"\b((?:NSV|HD|HIP|BD|TYC|TOI|TIC)\s*\d{3,7}|(?:AT|SN)\s*20\d{2}[a-z]{1,4}|ASASSN-\d{2}[a-z]{2,4})\b"
        )
        for m in cat_re.finditer(title):
            _add(m.group(1))

        return found

    @classmethod
    def _resolve_stars_via_simbad_batch(cls, star_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """Пакетно разрешает J2000.0 RA/Dec и тип звёзд через SIMBAD TAP (ADQL)."""
        if not star_names:
            return {}
        safe_names = [s.replace("'", "''") for s in star_names[:30]]
        in_clause = ",".join(f"'{s}'" for s in safe_names)
        adql = (
            "SELECT ident.id, basic.main_id, basic.ra, basic.dec, basic.otype_txt, allfluxes.V "
            "FROM ident "
            "JOIN basic ON ident.oidref = basic.oid "
            "LEFT JOIN allfluxes ON allfluxes.oidref = basic.oid "
            f"WHERE ident.id IN ({in_clause})"
        )
        params = urllib.parse.urlencode({
            "request": "doQuery",
            "lang": "ADQL",
            "format": "json",
            "query": adql,
        })
        ssl_ctx = cls._build_ssl_context()
        resolved: Dict[str, Dict[str, Any]] = {}
        for endpoint in (
            "https://simbad.cds.unistra.fr/simbad/sim-tap/sync",
            "https://simbad.cfa.harvard.edu/simbad/sim-tap/sync",
        ):
            try:
                req = urllib.request.Request(
                    f"{endpoint}?{params}",
                    headers={"User-Agent": f"SeestarAstroLab/{APP_VERSION}"},
                )
                with cls._urlopen_with_ssl_fallback(req, timeout=7.0) as resp:
                    j = json.loads(resp.read().decode("utf-8", errors="replace"))
                meta = [c.get("name") for c in (j.get("metadata") or [])]
                for row in (j.get("data") or []):
                    rec = dict(zip(meta, row))
                    ra_v = cls._parse_ra_dec_to_deg(rec.get("ra"), is_ra=True)
                    dec_v = cls._parse_ra_dec_to_deg(rec.get("dec"), is_ra=False)
                    if ra_v is None or dec_v is None:
                        continue
                    ident_id = str(rec.get("id") or rec.get("main_id") or "").strip()
                    if not ident_id:
                        continue
                    v_mag = rec.get("V")
                    mag_str = f"{float(v_mag):.1f} V (SIMBAD)" if isinstance(v_mag, (int, float)) else "Campaign Live"
                    info = {
                        "ra": round(ra_v, 6),
                        "dec": round(dec_v, 6),
                        "otype": str(rec.get("otype_txt") or "Var*").strip(),
                        "magRange": mag_str,
                        "mainId": str(rec.get("main_id") or ident_id).strip(),
                    }
                    resolved[ident_id.lower()] = info
                    norm = PhotometryBackendEngine.normalize_star_for_vsp(ident_id).lower()
                    if norm:
                        resolved[norm] = info
                if resolved:
                    return resolved
            except Exception:
                continue
        return resolved

    @classmethod
    def fetch_live_aavso_campaign_targets(cls, max_stars: int = 25) -> Dict[str, Any]:
        """
        Вариант 1 (без API-ключа): загружает свежие публичные AAVSO Alert Notices,
        извлекает звёзды актуальных кампаний и разрешает их J2000.0 RA/Dec через SIMBAD TAP.
        """
        ssl_ctx = cls._build_ssl_context()
        notices: List[Dict[str, Any]] = []
        err = ""
        for url in (
            "https://apps.aavso.org/v2/api/notices/?page_size=20",
            "https://www.aavso.org/aavso-alert-notices-for-observing-campaigns",
        ):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": f"SeestarAstroLab/{APP_VERSION}"})
                with cls._urlopen_with_ssl_fallback(req, timeout=7.0) as resp:
                    raw = resp.read().decode("utf-8", errors="replace")
                if "page_size=" in url:
                    j = json.loads(raw)
                    for r in (j.get("results") or [])[:20]:
                        notices.append({
                            "number": str(r.get("number") or r.get("id") or ""),
                            "title": str(r.get("title") or "").strip(),
                            "published": str(r.get("published") or r.get("created") or "")[:10],
                        })
                    if notices:
                        break
                else:
                    for m in re.finditer(r"AAVSO Alert Notice\s+(\d+)[:\s]+([^<\n]{4,140})", raw, re.I):
                        notices.append({"number": m.group(1), "title": m.group(2).strip(), "published": ""})
                        if len(notices) >= 20:
                            break
                    if notices:
                        break
            except Exception as e:
                err = str(e)

        if not notices:
            return {
                "ok": False,
                "source": "",
                "notices": [],
                "targets": [],
                "error": err or "Could not fetch public AAVSO Alert Notices",
            }

        star_to_notice: Dict[str, Dict[str, Any]] = {}
        ordered_stars: List[str] = []
        for n in notices:
            for star in cls._extract_stars_from_notice_title(n.get("title", "")):
                key = star.lower()
                if key not in star_to_notice:
                    star_to_notice[key] = n
                    ordered_stars.append(star)
                if len(ordered_stars) >= max_stars:
                    break
            if len(ordered_stars) >= max_stars:
                break

        resolved_map = cls._resolve_stars_via_simbad_batch(ordered_stars) if ordered_stars else {}
        targets: List[Dict[str, Any]] = []
        for star in ordered_stars:
            rec = resolved_map.get(star.lower()) or resolved_map.get(
                PhotometryBackendEngine.normalize_star_for_vsp(star).lower()
            )
            if not rec:
                continue
            n = star_to_notice[star.lower()]
            num = n.get("number", "")
            pub = n.get("published", "")
            parts = star.split()
            con = parts[-1] if (len(parts) >= 2 and parts[-1] in cls._IAU_CONSTELLATIONS) else "AAVSO"
            targets.append({
                "star": star,
                "alias": f"Alert Notice #{num}" if num else "AAVSO Alert Notice",
                "type": rec.get("otype") or "AAVSO Alert",
                "auid": "",
                "con": con,
                "ra": rec["ra"],
                "dec": rec["dec"],
                "magRange": rec.get("magRange") or "Campaign Live",
                "chart": "",
                "kname": "",
                "kmag": "",
                "priority": f"🔴 LIVE Notice #{num}" if num else "🔴 LIVE Campaign",
                "desc": n.get("title", ""),
                "comment": f"Live AAVSO Alert Notice #{num} ({pub})" if pub else f"Live AAVSO Alert Notice #{num}",
                "isLiveCampaign": True,
                "noticeNumber": num,
                "published": pub,
            })

        return {
            "ok": True,
            "source": "AAVSO Alert Notices + SIMBAD TAP",
            "noticesCount": len(notices),
            "notices": notices[:15],
            "targets": targets,
            "error": "",
        }

    @classmethod
    def fetch_aavso_target_tool_targets(cls, api_key: str, obs_section: str = "all") -> Dict[str, Any]:
        """
        Вариант 2 (официальный AAVSO Target Tool API v1.0.0):
        GET https://targettool.aavso.org/TargetTool/api/v1/targets?obs_section=all
        HTTP Basic Auth: username = personal API key, password = 'api_token'.
        """
        clean_key = str(api_key or "").strip()
        if not clean_key:
            return {
                "ok": False,
                "errorCode": "missing_key",
                "error": "AAVSO Target Tool API key is empty.",
                "targets": [],
                "count": 0,
            }

        sec_param = urllib.parse.quote(str(obs_section or "all").strip() or "all")
        url = f"https://targettool.aavso.org/TargetTool/api/v1/targets?obs_section={sec_param}"
        auth_token = base64.b64encode(f"{clean_key}:api_token".encode("utf-8")).decode("ascii")
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Basic {auth_token}",
                "Accept": "application/json",
                "User-Agent": f"SeestarAstroLab/{APP_VERSION}",
            },
        )
        ssl_ctx = cls._build_ssl_context()

        try:
            with cls._urlopen_with_ssl_fallback(req, timeout=12.0) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                rate_rem = resp.headers.get("X-Rate-Limit-Remaining", "")
        except urllib.error.HTTPError as he:
            code = getattr(he, "code", 0)
            if code in (401, 403):
                return {
                    "ok": False,
                    "errorCode": "invalid_key",
                    "error": f"HTTP {code}: Invalid or unauthorized AAVSO Target Tool API key.",
                    "targets": [],
                    "count": 0,
                }
            if code == 429:
                return {
                    "ok": False,
                    "errorCode": "rate_limited",
                    "error": "HTTP 429: AAVSO Target Tool API rate limit (1000 req/hr) exceeded.",
                    "targets": [],
                    "count": 0,
                }
            return {
                "ok": False,
                "errorCode": f"http_{code}",
                "error": f"HTTP {code}: {he.reason}",
                "targets": [],
                "count": 0,
            }
        except Exception as e:
            return {
                "ok": False,
                "errorCode": "network_error",
                "error": f"Network error connecting to targettool.aavso.org: {e}",
                "targets": [],
                "count": 0,
            }

        try:
            payload = json.loads(raw)
        except Exception as e:
            return {
                "ok": False,
                "errorCode": "parse_error",
                "error": f"Invalid JSON from AAVSO Target Tool API: {e}",
                "targets": [],
                "count": 0,
            }

        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict):
            rows = payload.get("targets") or payload.get("results") or payload.get("data") or []
        else:
            rows = []

        targets: List[Dict[str, Any]] = []
        for rec in rows:
            if not isinstance(rec, dict):
                continue
            star_name = str(rec.get("star_name") or rec.get("name") or rec.get("star") or "").strip()
            if not star_name:
                continue
            ra_deg = cls._parse_ra_dec_to_deg(rec.get("ra"), is_ra=True)
            dec_deg = cls._parse_ra_dec_to_deg(rec.get("dec"), is_ra=False)
            if ra_deg is None or dec_deg is None:
                continue
            con = str(rec.get("constellation") or rec.get("con") or "").strip()
            if not con:
                parts = star_name.split()
                con = parts[-1] if (len(parts) >= 2 and parts[-1] in cls._IAU_CONSTELLATIONS) else "AAVSO"
            is_prio = bool(rec.get("priority"))
            solar_conj = bool(rec.get("solar_conjunction"))
            raw_ldp = rec.get("last_data_point")
            if isinstance(raw_ldp, (int, float)) and raw_ldp > 100000000:
                try:
                    last_dp = datetime.datetime.fromtimestamp(float(raw_ldp), tz=datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                except Exception:
                    last_dp = str(raw_ldp)
            else:
                last_dp = str(raw_ldp or "").strip()
            raw_sec = rec.get("obs_section") or rec.get("observing_section") or rec.get("section") or ""
            if isinstance(raw_sec, list):
                obs_sec = ", ".join(str(x).strip() for x in raw_sec if str(x).strip() and str(x).strip().lower() != "none")
            else:
                obs_sec = str(raw_sec).strip()
            var_type = str(rec.get("var_type") or rec.get("type") or obs_sec or "AAVSO Target Tool").strip()
            auid = str(rec.get("auid") or "").strip()
            min_m = rec.get("min_mag")
            max_m = rec.get("max_mag")
            if min_m is not None and max_m is not None:
                mag_range = f"{max_m}–{min_m} mag"
            elif rec.get("mag_range"):
                mag_range = str(rec.get("mag_range"))
            else:
                mag_range = "Target Tool Live"

            desc_bits = []
            if obs_sec:
                desc_bits.append(f"Section: {obs_sec}")
            if last_dp:
                desc_bits.append(f"Last obs: {last_dp[:16]} UTC")
            if solar_conj:
                desc_bits.append("Solar conjunction")
            desc_str = " • ".join(desc_bits) if desc_bits else "Live AAVSO Target Tool observing target"

            targets.append({
                "star": star_name,
                "alias": obs_sec or "AAVSO Target Tool",
                "type": var_type,
                "auid": auid,
                "con": con,
                "ra": round(ra_deg, 6),
                "dec": round(dec_deg, 6),
                "magRange": mag_range,
                "chart": "",
                "kname": "",
                "kmag": "",
                "priority": "🔴 LIVE PRIORITY" if is_prio else "🟢 LIVE Target Tool",
                "desc": desc_str,
                "comment": desc_str,
                "isLiveTargetTool": True,
                "isHighPriority": is_prio,
                "lastDataPoint": last_dp,
                "solarConjunction": solar_conj,
                "obsSection": obs_sec,
            })

        return {
            "ok": True,
            "source": "AAVSO Target Tool API v1.0.0",
            "count": len(targets),
            "rateLimitRemaining": rate_rem,
            "targets": targets,
            "error": "",
        }

    @classmethod
    def fetch_aavso_light_curve(
        cls,
        star_name: str,
        days_back: int = 180,
        api_token: str = "",
        user_obscode: str = "",
        max_points: int = 3000,
    ) -> Dict[str, Any]:
        """
        Загружает УЖЕ ИЗВЕСТНУЮ кривую блеска звезды из базы AAVSO AID:
        1) Официальный AAVSO REST API v2: GET https://apps.aavso.org/v2/api/observations/photometry/?target=...
        2) Официальный веб-эндпоинт кривых блеска AAVSO:
           GET https://vsx.aavso.org/index.php?view=api.delim&ident=...&fromjd=...&tojd=...&delimiter=,
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

        t0_lc = time.time()
        ssl_ctx = cls._build_ssl_context()
        eff_max = max(50, int(max_points or 3000))
        AstroLabDiagnosticLogger.log_event(
            "INFO",
            "AAVSO_CURVE",
            f"Start fetch_aavso_light_curve star={clean_star}",
            {"rawStar": star_name, "daysBack": days_back, "fromJd": round(from_jd, 3), "nowJd": round(now_jd, 3), "hasToken": bool(tok), "obscode": u_obs},
        )

        # Канал 1 (основной, быстрый, без токена): Официальный AAVSO AID api.delim (vsx.aavso.org, таймаут 18с для T CrB / SS Cyg)
        try:
            q_params = {
                "DateFormat": "Julian",
                "RequestedBands": "",
                "view": "api.delim",
                "ident": clean_star,
                "fromjd": f"{from_jd:.4f}",
                "tojd": f"{now_jd:.4f}",
                "delimiter": ",",
            }
            url = f"https://vsx.aavso.org/index.php?{urllib.parse.urlencode(q_params)}"
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0.0.0 Safari/537.36",
                    "Accept": "text/plain,text/csv,*/*",
                },
            )
            with cls._urlopen_with_ssl_fallback(req, timeout=18.0) as resp:
                csv_text = resp.read().decode("utf-8", errors="replace")
            delim_pts: List[Dict[str, Any]] = []
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
                    delim_pts.append({
                        "jd": round(jd_v, 6),
                        "mag": round(mag_v, 4),
                        "merr": round(err_v, 4),
                        "band": band_map.get(band_v, band_v),
                        "obscode": obs_v,
                        "source": "AAVSO_DELIM",
                        "utc": cls.jd_to_utc_str(jd_v),
                    })
                except Exception:
                    continue
            if delim_pts:
                delim_pts.sort(key=lambda x: x["jd"])
                raw_points = delim_pts[-eff_max:]
                source_used = f"AAVSO AID (api.delim, {len(raw_points)}/{len(delim_pts)} latest pts)"
        except Exception as e:
            network_errors.append(f"AAVSO AID api.delim: {e}")
            AstroLabDiagnosticLogger.log_event("WARN", "AAVSO_DELIM", f"Channel 1 failed for {clean_star}: {e}")

        # Канал 2 (резерв, если api.delim не ответил или задан токен): AAVSO REST API v2 с пагинацией
        if len(raw_points) < 20:
            try:
                q = urllib.parse.urlencode({"target": clean_star, "page_size": "200"})
                next_url: Optional[str] = f"https://apps.aavso.org/v2/api/observations/photometry/?{q}"
                req_headers = {"User-Agent": f"SeestarAstroLab/{APP_VERSION}", "Accept": "application/json"}
                if tok:
                    req_headers["Authorization"] = f"Token {tok}"
                api_pts: List[Dict[str, Any]] = []
                pages_fetched = 0
                while next_url and pages_fetched < 6 and len(api_pts) < eff_max:
                    req = urllib.request.Request(next_url, headers=req_headers)
                    with cls._urlopen_with_ssl_fallback(req, timeout=8.0) as resp:
                        data = json.loads(resp.read().decode("utf-8", errors="replace"))
                    pages_fetched += 1
                    for item in (data.get("results") or []):
                        if item.get("fainterthan"):
                            continue
                        try:
                            jd_v = float(item["jd_dbl"])
                            mag_v = float(str(item["magnitude"]).lstrip("<"))
                            if jd_v < from_jd:
                                continue
                            err_v = float(item.get("uncertainty") or 0.02)
                            b_raw = str(item.get("band") or "V")
                            api_pts.append({
                                "jd": round(jd_v, 6),
                                "mag": round(mag_v, 4),
                                "merr": round(err_v, 4),
                                "band": band_map.get(b_raw, b_raw),
                                "obscode": str(item.get("obscode") or "").strip().upper(),
                                "source": "AAVSO_API_V2",
                                "utc": cls.jd_to_utc_str(jd_v),
                            })
                        except Exception:
                            continue
                    next_url = data.get("next")
                if len(api_pts) > len(raw_points):
                    api_pts.sort(key=lambda x: x["jd"])
                    raw_points = api_pts[-eff_max:]
                    source_used = f"AAVSO API v2 ({len(raw_points)} pts, {pages_fetched} pages)"
            except Exception as e:
                network_errors.append(f"AAVSO API v2: {e}")
                AstroLabDiagnosticLogger.log_event("WARN", "AAVSO_API_V2", f"Channel 2 failed for {clean_star}: {e}")

        raw_points.sort(key=lambda x: x["jd"])
        other_pts = [p for p in raw_points if not u_obs or p.get("obscode") != u_obs]
        user_aavso_pts = [p for p in raw_points if u_obs and p.get("obscode") == u_obs]

        local_history = cls.get_converted_history(clean_star)
        has_aavso = len(raw_points) >= 1

        aavso_err_msg = ""
        if len(raw_points) == 0:
            detail = f" ({'; '.join(network_errors)})" if network_errors else ""
            aavso_err_msg = (
                f"В базе AAVSO (AID) не найдено наблюдений для звезды «{clean_star}» "
                f"за последние {days_back} сут.{detail}"
            )

        AstroLabDiagnosticLogger.log_event(
            "INFO" if has_aavso else "WARN",
            "AAVSO_CURVE",
            f"Done fetch_aavso_light_curve star={clean_star} hasData={has_aavso} other={len(other_pts)} user={len(user_aavso_pts)} local={local_history.get('totalPoints', 0)} source={source_used or 'none'} ms={int((time.time()-t0_lc)*1000)}",
            {"errors": network_errors} if network_errors else None,
        )
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

    @staticmethod
    def _parse_semver_tuple(ver_str: str):
        m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", str(ver_str or ""))
        if not m:
            return (0, 0, 0)
        return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))

    @classmethod
    def check_github_latest_release(cls, current_version: str = APP_VERSION) -> Dict[str, Any]:
        """
        Лёгкая однократная проверка новой версии на GitHub Releases.
        Не скачивает бинарные файлы, не запускает установщики, молча завершается при отсутствии сети.
        Сравнение строго remote > local (semver), чтобы локальные сборки не предлагали откат.
        """
        repo_releases_url = "https://github.com/CosmoBehemothych/Seestar-AstroLab-AAVSO/releases/latest"
        api_url = "https://api.github.com/repos/CosmoBehemothych/Seestar-AstroLab-AAVSO/releases/latest"
        latest_tag = ""
        release_url = repo_releases_url
        headers = {"User-Agent": f"SeestarAstroLab/{current_version}", "Accept": "application/vnd.github+json"}

        ssl_ctx = None
        try:
            import ssl
            try:
                import certifi
                ssl_ctx = ssl.create_default_context(cafile=certifi.where())
            except Exception:
                ssl_ctx = ssl.create_default_context()
        except Exception:
            ssl_ctx = None

        # Канал 1: лёгкий редирект github.com/.../releases/latest (без жёсткого лимита 60 req/hr API)
        try:
            req = urllib.request.Request(repo_releases_url, headers={"User-Agent": f"SeestarAstroLab/{current_version}"})
            with cls._urlopen_with_ssl_fallback(req, timeout=6.0) as resp:
                final_url = resp.geturl() or ""
                m = re.search(r"/releases/tag/([^/?#]+)", final_url)
                if m:
                    latest_tag = m.group(1).strip()
                    release_url = final_url
        except Exception:
            pass

        # Канал 2: fallback на GitHub REST API (если редирект не дал тег)
        if not latest_tag:
            try:
                req = urllib.request.Request(api_url, headers=headers)
                with cls._urlopen_with_ssl_fallback(req, timeout=6.0) as resp:
                    payload = json.loads(resp.read().decode("utf-8", errors="replace"))
                    latest_tag = str(payload.get("tag_name") or "").strip()
                    release_url = str(payload.get("html_url") or repo_releases_url).strip()
            except Exception:
                return {"ok": False, "updateAvailable": False, "currentVersion": current_version}

        if not latest_tag:
            return {"ok": False, "updateAvailable": False, "currentVersion": current_version}

        local_t = cls._parse_semver_tuple(current_version)
        remote_t = cls._parse_semver_tuple(latest_tag)
        update_avail = remote_t > local_t
        return {
            "ok": True,
            "updateAvailable": update_avail,
            "currentVersion": current_version,
            "latestVersion": latest_tag.lstrip("vV"),
            "latestTag": latest_tag,
            "releaseUrl": release_url,
        }


RPC_AUTH_TOKEN: str = secrets.token_hex(24)
MAX_RPC_BODY_BYTES: int = 25 * 1024 * 1024  # 25 MB safety cap


def get_rpc_auth_token() -> str:
    """Return the per-process cryptographic token required for local RPC POST requests."""
    return RPC_AUTH_TOKEN


def _is_allowed_rpc_origin(origin: str) -> bool:
    if not origin:
        return True  # Non-browser / direct local client without Origin header
    o = origin.strip().lower()
    if o == "null":
        return True  # WebView2 / Electron file:// origin
    return bool(re.match(r"^https?://(127\.0\.0\.1|localhost)(:\d{1,5})?$", o))


class _AstroLabBackendRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        origin = self.headers.get("Origin", "")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        if origin and _is_allowed_rpc_origin(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-AstroLab-Token")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self) -> None:
        origin = self.headers.get("Origin", "")
        if origin and not _is_allowed_rpc_origin(origin):
            self._send_json({"ok": False, "error": "Forbidden origin"}, 403)
            return
        self._send_json({"ok": True})

    def do_GET(self) -> None:
        origin = self.headers.get("Origin", "")
        if origin and not _is_allowed_rpc_origin(origin):
            self._send_json({"ok": False, "error": "Forbidden origin"}, 403)
            return
        if self.path.startswith("/api/health"):
            self._send_json({"ok": True, "version": APP_VERSION, "engine": "PhotometryBackendEngine"})
        else:
            self._send_json({"ok": False, "error": "Not found"}, 404)

    def do_POST(self) -> None:
        origin = self.headers.get("Origin", "")
        if origin and not _is_allowed_rpc_origin(origin):
            self._send_json({"ok": False, "error": "Forbidden origin"}, 403)
            return

        require_token = getattr(self.server, "require_token", True)
        if require_token:
            supplied = (self.headers.get("X-AstroLab-Token") or "").strip()
            if not supplied or not hmac.compare_digest(supplied, RPC_AUTH_TOKEN):
                self._send_json({"ok": False, "error": "Unauthorized RPC request"}, 401)
                return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json({"ok": False, "error": "Invalid Content-Length"}, 400)
            return

        if length < 0:
            self._send_json({"ok": False, "error": "Negative Content-Length"}, 400)
            return
        if length > MAX_RPC_BODY_BYTES:
            self._send_json({"ok": False, "error": f"Payload exceeds {MAX_RPC_BODY_BYTES} bytes limit"}, 413)
            return

        try:
            body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}
        except Exception as e:
            self._send_json({"ok": False, "error": str(e)}, 400)
            return

        action = body.get("action", "")
        try:
            self._dispatch_post_action(action, body)
        except Exception as exc:
            try:
                AstroLabDiagnosticLogger.log_exception("RPC_DISPATCH_ERR", f"RPC action '{action}' failed", exc)
            except Exception:
                pass
            self._send_json({"ok": False, "error": f"Internal RPC error: {exc}"}, 500)

    def _dispatch_post_action(self, action: str, body: Dict[str, Any]) -> None:
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
                kname="na",  # Strictly na for Seestar ensemble photometry
                kmag="na",   # Strictly na for Seestar ensemble photometry
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
        elif action == "delete_converted_records":
            res = AavsoNativeAndStorageService.delete_converted_records(
                star_name=body.get("star", ""),
                file_name=body.get("fileName", ""),
                obs_date=body.get("obsDate", ""),
            )
            self._send_json(res)
        elif action == "reset_all_user_data":
            res = AavsoNativeAndStorageService.reset_all_user_data()
            self._send_json(res)
        elif action == "get_converted_history":
            res = AavsoNativeAndStorageService.get_converted_history(body.get("star"))
            self._send_json(res)
        elif action == "fetch_live_star_dossier":
            res = AavsoNativeAndStorageService.fetch_live_star_dossier(body.get("star", ""))
            self._send_json(res)
        elif action == "query_aavso_star":
            res = AavsoNativeAndStorageService.query_aavso_star(
                star_name=body.get("star", ""),
                scope_model=body.get("scopeModel", "S50"),
                api_token=body.get("apiToken", ""),
            )
            self._send_json(res)
        elif action == "check_github_latest_release":
            res = AavsoNativeAndStorageService.check_github_latest_release(body.get("currentVersion") or APP_VERSION)
            self._send_json(res)
        elif action == "fetch_live_aavso_notices":
            res = AavsoNativeAndStorageService.fetch_live_aavso_notices()
            self._send_json(res)
        elif action == "fetch_live_aavso_campaign_targets":
            res = AavsoNativeAndStorageService.fetch_live_aavso_campaign_targets(
                max_stars=int(body.get("maxStars", 25) or 25)
            )
            self._send_json(res)
        elif action == "fetch_aavso_target_tool_targets":
            res = AavsoNativeAndStorageService.fetch_aavso_target_tool_targets(
                api_key=body.get("apiKey", ""),
                obs_section=body.get("obsSection", "all"),
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


def start_background_rpc_server(port: int = 18765, require_token: bool = True) -> Optional[ThreadingHTTPServer]:
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", port), _AstroLabBackendRequestHandler)
        srv.require_token = bool(require_token)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        return srv
    except Exception as exc:
        try:
            AstroLabDiagnosticLogger.log_exception("RPC_START_ERR", f"Failed to bind local RPC port {port}", exc)
        except Exception:
            pass
        return None
