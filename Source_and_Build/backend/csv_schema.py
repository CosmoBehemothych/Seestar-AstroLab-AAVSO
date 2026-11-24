# -*- coding: utf-8 -*-
"""
[RU] Модуль схемы и валидации сырых CSV-файлов ZWO Seestar.
     Реализует чтение строго по заголовкам колонок (header -> index),
     скользящий детектор выбросов >3σ MAD, расчёт порога насыщения матрицы
     по модели телескопа и выдержке (5-й процентиль блеска) и проверку времени кадров.
[EN] ZWO Seestar raw CSV schema resolver, rolling 3-sigma MAD outlier detector,
     model-aware exposure saturation model (5th brightest percentile), and frame timing validator.
"""

import math
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple


# [RU] Канонические ключи колонок Seestar CSV и допустимые варианты заголовков ZWO
# [EN] Canonical Seestar CSV column keys and accepted ZWO header aliases
SEESTAR_COLUMN_ALIASES: Dict[str, Tuple[str, ...]] = {
    "name": ("name", "star", "starid", "object", "target"),
    "type": ("type", "star type", "role"),
    "ra": ("ra", "ra(deg)", "ra_deg", "ra (j2000)"),
    "dec": ("dec", "dec(deg)", "dec_deg", "dec (j2000)"),
    "ref_stars": ("valid reference stars", "ref stars", "refstars", "comparison stars"),
    "ref_mag": ("reference magnitude", "ref mag", "ref_mag"),
    "mag": ("mag(obs)", "mag", "magnitude", "obs mag"),
    "merr": ("mag(err)", "merr", "mag err", "error", "mag_err"),
    "x": ("x axis", "x", "x_pos", "x(px)"),
    "y": ("y axis", "y", "y_pos", "y(px)"),
    "exp": ("exp", "exposure", "exptime", "exp(s)"),
    "utc": ("exp start", "utc", "start time", "date-obs"),
    "jd_start": ("exp start(jd)", "jd start", "jd_start", "jd"),
    "mjd_start": ("exp start(mjd)", "mjd start", "mjd_start", "mjd"),
    "utc_end": ("exp end", "end time"),
    "jd_end": ("exp end(jd)", "jd end", "jd_end"),
    "mjd_end": ("exp end(mjd)", "mjd end", "mjd_end"),
    "is_var": ("is variable", "variable", "is_variable"),
    "snr": ("snr", "s/n", "signal_to_noise"),
    # [RU] Опциональные колонки будущих прошивок ZWO (стэкинг и LP-фильтр)
    # [EN] Optional future ZWO firmware columns (stack frame count & LP filter state)
    "stack_frames": ("stack frames", "stack count", "stacked frames", "frames", "nstack"),
    "lp_filter": ("lp filter", "lp_filter", "filter", "dual band", "ircut"),
}

# [RU] Обязательные колонки для корректной фотометрической конвертации
# [EN] Mandatory columns required for valid photometric conversion
REQUIRED_SEESTAR_COLUMNS: Tuple[str, ...] = ("name", "type", "mag", "merr", "jd_start")

# [RU] Индексы классической 19-колоночной схемы ZWO Seestar (используются только для беззаголовочных фрагментов)
# [EN] Legacy 19-column positional map (used ONLY if raw headerless data rows are supplied)
LEGACY_19COL_MAP: Dict[str, int] = {
    "name": 0,
    "type": 1,
    "ra": 2,
    "dec": 3,
    "ref_stars": 4,
    "ref_mag": 5,
    "mag": 6,
    "merr": 7,
    "x": 8,
    "y": 9,
    "exp": 10,
    "utc": 11,
    "jd_start": 12,
    "mjd_start": 13,
    "utc_end": 14,
    "jd_end": 15,
    "mjd_end": 16,
    "is_var": 17,
    "snr": 18,
}

# [RU] Базовый порог насыщения матрицы при выдержке 10 с для каждой модели Seestar
#      (масштабируется формулой: threshold = base_10s + 2.5 * log10(EXP / 10))
# [EN] Baseline 10s saturation threshold (mag) per Seestar model
#      (scaled continuously via: threshold = base_10s + 2.5 * log10(EXP / 10))
SCOPE_SATURATION_BASE_10S: Dict[str, float] = {
    "S30": 6.4,
    "S30PLUS": 6.2,
    "S30PRO": 6.0,
    "S50": 7.0,
    "S50PRO": 6.8,
}


class SeestarCsvSchemaError(ValueError):
    """[RU] Ошибка неизвестной или неполной схемы заголовков CSV Seestar."""

    def __init__(self, message: str, missing_columns: Optional[List[str]] = None, header_cols: Optional[List[str]] = None):
        super().__init__(message)
        self.missing_columns = list(missing_columns or [])
        self.header_cols = list(header_cols or [])


def _norm_header_token(raw: str) -> str:
    s = str(raw or "").strip().lstrip("\ufeff").lower()
    s = re.sub(r"\s+", " ", s)
    return s


def is_seestar_header_row(cols: Sequence[str]) -> bool:
    """[RU] Определяет, является ли строка заголовком таблицы Seestar CSV."""
    if not cols or len(cols) < 5:
        return False
    normed = [_norm_header_token(c) for c in cols]
    # Header never contains 'non-reference star' or 'reference star' as col 1
    if len(normed) > 1 and normed[1] in ("non-reference star", "reference star"):
        return False
    hits = 0
    all_aliases = {a for aliases in SEESTAR_COLUMN_ALIASES.values() for a in aliases}
    for tok in normed:
        if tok in all_aliases:
            hits += 1
    return hits >= 3


def resolve_seestar_csv_columns(header_cols: Sequence[str]) -> Dict[str, int]:
    """
    [RU] Преобразует строку заголовков CSV в словарь {canonical_key: col_index}.
         Выбрасывает SeestarCsvSchemaError, если обязательные колонки отсутствуют.
    [EN] Maps CSV header column names to canonical indices; raises SeestarCsvSchemaError if required columns are missing.
    """
    normed = [_norm_header_token(c) for c in header_cols]
    col_map: Dict[str, int] = {}
    for canonical_key, aliases in SEESTAR_COLUMN_ALIASES.items():
        for idx, tok in enumerate(normed):
            if tok in aliases:
                col_map[canonical_key] = idx
                break

    missing = [k for k in REQUIRED_SEESTAR_COLUMNS if k not in col_map]
    if missing:
        raise SeestarCsvSchemaError(
            f"Неизвестная схема CSV Seestar: отсутствуют обязательные колонки {', '.join(missing)}. "
            f"Найдены заголовки: {', '.join(str(c).strip() for c in header_cols[:20])}",
            missing_columns=missing,
            header_cols=[str(c).strip() for c in header_cols],
        )
    return col_map


def parse_seestar_csv_header_and_rows(
    csv_text: str,
    split_fn,
) -> Tuple[Dict[str, int], List[Tuple[int, List[str]]], bool]:
    """
    [RU] Единая точка разбора заголовка и строк Seestar CSV.
         Возвращает (col_map, data_rows[(1-based_line_no, cols)], has_header).
         Если в файле есть заголовок, но обязательных колонок нет — выбрасывает SeestarCsvSchemaError.
    [EN] Unified Seestar CSV header + row parser returning (col_map, data_rows, has_header).
    """
    raw_lines = (csv_text or "").splitlines()
    col_map: Optional[Dict[str, int]] = None
    has_header = False
    data_rows: List[Tuple[int, List[str]]] = []

    for idx, raw_line in enumerate(raw_lines):
        s = raw_line.strip()
        if not s or s.startswith("#"):
            continue
        cols = split_fn(s)
        if not cols:
            continue
        if col_map is None:
            if is_seestar_header_row(cols):
                col_map = resolve_seestar_csv_columns(cols)
                has_header = True
                continue
            # Check if first non-empty line is already a legacy 19-col data row
            if len(cols) >= 19 and cols[1].strip().lower() in ("non-reference star", "reference star"):
                col_map = dict(LEGACY_19COL_MAP)
                has_header = False
                data_rows.append((idx + 1, cols))
                continue
            # Unknown header format -> raise explicit schema error
            resolve_seestar_csv_columns(cols)
        else:
            data_rows.append((idx + 1, cols))

    if col_map is None:
        col_map = dict(LEGACY_19COL_MAP)
    return col_map, data_rows, has_header


def get_col(cols: Sequence[str], col_map: Dict[str, int], key: str, default: str = "") -> str:
    idx = col_map.get(key)
    if idx is None or idx < 0 or idx >= len(cols):
        return default
    return str(cols[idx]).strip()


def _median(vals: Sequence[float]) -> float:
    s = sorted(vals)
    n = len(s)
    return s[n // 2] if n % 2 == 1 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def compute_percentile(vals: Sequence[float], pct: float = 5.0) -> Optional[float]:
    """[RU] Линейно-интерполированный процентиль (например, 5-й процентиль = ярчайшие точки сессии)."""
    clean = sorted(v for v in vals if math.isfinite(v))
    if not clean:
        return None
    if len(clean) == 1:
        return clean[0]
    p = max(0.0, min(100.0, float(pct))) / 100.0
    pos = p * (len(clean) - 1)
    lo = int(math.floor(pos))
    hi = min(len(clean) - 1, lo + 1)
    frac = pos - lo
    return clean[lo] * (1.0 - frac) + clean[hi] * frac


def compute_saturation_threshold(scope_model: str = "S50", exp_sec: Optional[float] = 10.0) -> float:
    """
    [RU] Порог риска перенасыщения матрицы Seestar (mag) с учётом модели телескопа и выдержки:
         threshold = base_10s(model) + 2.5 * log10(EXP / 10.0)
         (эквивалентно критерию из README: mag + 2.5*log10(EXP) < C_model).
    [EN] Model- and exposure-aware Seestar saturation threshold (mag):
         threshold = base_10s(model) + 2.5 * log10(EXP / 10.0).
    """
    code = str(scope_model or "S50").strip().upper().replace(" ", "").replace("_", "")
    base_10s = SCOPE_SATURATION_BASE_10S.get(code, 7.0)
    ev = float(exp_sec) if (exp_sec is not None and math.isfinite(float(exp_sec)) and float(exp_sec) > 0) else 10.0
    return round(base_10s + 2.5 * math.log10(ev / 10.0), 2)


def detect_rolling_mad_3sigma_outliers(mags: Sequence[float], window: int = 9) -> Dict[str, Any]:
    """
    [RU] Определяет статистические выбросы относительно СКОЛЬЗЯЩЕЙ медианы (> max(0.06, 3 * 1.4826 * local_MAD)).
         В отличие от глобальной медианы всей сессии, скользящее окно отслеживает реальные
         узкие минимумы затменных двойных (EA), вспышки и быстрый рост карликовых новых,
         отсекая только одиночные артефакты (спутники, облака, космические лучи).
    [EN] Rolling-window 3-sigma MAD outlier detector that preserves genuine eclipses/flares
         while flagging isolated single-frame spikes.
    """
    n = len(mags)
    if n < 6:
        return {
            "count": 0,
            "indices": set(),
            "median": round(_median(mags), 4) if n else None,
            "limit": None,
            "method": "rolling_mad_3sigma",
            "window": window,
        }

    # Global stats retained for backward-compatible summary reporting
    global_med = _median(mags)
    global_abs = [abs(m - global_med) for m in mags]
    global_mad = _median(global_abs) * 1.4826
    global_limit = max(0.06, 3.0 * (global_mad if global_mad > 0 else 0.05))

    half_w = max(2, int(window) // 2)
    bad_idx = set()
    for i in range(n):
        lo = max(0, i - half_w)
        hi = min(n, i + half_w + 1)
        # Ensure at least 5 points in the local window (including edges)
        if hi - lo < min(5, n):
            if lo == 0:
                hi = min(n, 5)
            else:
                lo = max(0, n - 5)
        # Leave-one-out local neighbors so a huge single-frame spike doesn't inflate its own local MAD
        neighbors = [mags[j] for j in range(lo, hi) if j != i]
        if len(neighbors) < 4:
            continue
        loc_med = _median(neighbors)
        loc_mad = _median([abs(x - loc_med) for x in neighbors]) * 1.4826
        loc_limit = max(0.06, 3.0 * (loc_mad if loc_mad > 0 else 0.02))
        if abs(mags[i] - loc_med) > loc_limit:
            bad_idx.add(i)

    return {
        "count": len(bad_idx),
        "indices": bad_idx,
        "median": round(global_med, 4),
        "limit": round(global_limit, 4),
        "method": "rolling_mad_3sigma",
        "window": window,
    }


def validate_frame_timing(
    jd_start: float,
    jd_end: Optional[float],
    exp_sec: Optional[float] = None,
) -> Dict[str, Any]:
    """
    [RU] Проверяет корректность временного интервала кадра:
         - наличие jd_end (предупреждение, если пусто — без тихой подстановки);
         - порядок времени jd_end >= jd_start (иначе строка бракуется);
         - согласие длительности (jd_end - jd_start) * 86400 с заявленной выдержкой EXP.
    """
    empty_end = jd_end is None
    eff_end = jd_start if empty_end else float(jd_end)
    if not (math.isfinite(jd_start) and math.isfinite(eff_end)):
        return {"valid": False, "reason": "non_finite_jd", "emptyEnd": empty_end, "expMismatch": False}
    if eff_end < jd_start:
        return {"valid": False, "reason": "jd_end_before_jd_start", "emptyEnd": empty_end, "expMismatch": False}

    actual_sec = (eff_end - jd_start) * 86400.0
    exp_mismatch = False
    if not empty_end and exp_sec is not None and math.isfinite(exp_sec) and exp_sec > 0:
        # Allow realistic Seestar readout/stacking overhead (±max(5s, 50% of EXP))
        tol = max(5.0, 0.5 * exp_sec)
        if abs(actual_sec - exp_sec) > tol:
            exp_mismatch = True

    return {
        "valid": True,
        "reason": "",
        "emptyEnd": empty_end,
        "expMismatch": exp_mismatch,
        "actualSec": round(actual_sec, 2),
        "jdEndEffective": eff_end,
    }
