# -*- coding: utf-8 -*-
"""
[RU] Автотест №8: Регрессионная проверка всех 10 пунктов аудита конвертера,
     безопасности RPC, парсера CSV по заголовкам, скользящего 3σ MAD,
     многоночных CSV, защиты от насыщения (p05 + модель + EXP) и проверки времени.
[EN] Autotest #8: Regression suite covering all 10 code-review findings:
     header-based CSV parsing, rolling 3-sigma MAD, multi-night preservation,
     storage error reporting, model/exposure p05 saturation, frame timing checks,
     repo hygiene, methodology docs, and local RPC auth security.
"""

import json
import os
import sys
import tempfile
import urllib.error
import urllib.request

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_ROOT = os.path.join(REPO_ROOT, "Source_and_Build")
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from backend.astrolab_backend_core import (
    PhotometryBackendEngine,
    AavsoNativeAndStorageService,
    get_rpc_auth_token,
    start_background_rpc_server,
)
from backend.csv_schema import compute_saturation_threshold

STD_HEADER = (
    "Name,Type,RA,DEC,Valid Reference Stars,Reference magnitude,Mag(obs),Mag(err),"
    "X Axis,Y Axis,EXP,EXP start,EXP start(JD),EXP start(MJD),EXP end,EXP end(JD),EXP end(MJD),Is Variable,SNR"
)


def _make_row(star="SZ Lyncis", mag=9.15, merr=0.05, exp="10.0s", utc="2026.11.01 23:48:35", jd_s=2461346.367077, jd_e=2461346.367196, snr=30.0):
    jd_e_str = "" if jd_e is None else f"{jd_e:.6f}"
    return (
        f"{star},Non-reference star,122.401880,44.473356,15,/,{mag:.6f},{merr:.6f},"
        f"1096.2,1923.2,{exp},{utc},{jd_s:.6f},{jd_s-2400000.5:.6f},{utc},{jd_e_str},{jd_s-2400000.5:.6f},true,{snr:.2f}"
    )


def _with_isolated_storage(fn):
    with tempfile.TemporaryDirectory() as tmp:
        orig_get = AavsoNativeAndStorageService.get_storage_db_path
        db_file = os.path.join(tmp, "user_converted_photometry_db.json")
        AavsoNativeAndStorageService.get_storage_db_path = classmethod(lambda cls: db_file)
        try:
            return fn(tmp)
        finally:
            AavsoNativeAndStorageService.get_storage_db_path = orig_get


def test_1_header_based_csv_and_unknown_schema():
    # Shuffled columns + future ZWO firmware columns (Stack Frames, LP Filter)
    shuffled_header = (
        "SNR,Mag(obs),EXP start(JD),Type,Name,Mag(err),EXP end(JD),EXP,EXP start,RA,DEC,Valid Reference Stars,X Axis,Y Axis,Stack Frames,LP Filter"
    )
    row = "45.2,9.123456,2461346.367077,Non-reference star,SZ Lyncis,0.041200,2461346.367196,10.0s,2026.11.01 23:48:35,122.40188,44.47336,15,1096,1923,3,OFF"
    csv_text = shuffled_header + "\n" + row + "\n"

    def _run(_tmp):
        res = PhotometryBackendEngine.convert_seestar_csv_to_aavso_extended(
            csv_text=csv_text, obscode="TEST1", starid_ui="SZ Lyn"
        )
        assert res["ok"] is True, f"Shuffled header conversion failed: {res}"
        assert res["count"] == 1
        assert "9.1235,0.0412" in res["content"]
        assert "Stack=3" in res["content"] and "LP=OFF" in res["content"]

        # Unknown schema must return explicit errorCode
        bad_csv = "ColA,ColB,ColC,ColD,ColE\n1,2,3,4,5\n"
        res_bad = PhotometryBackendEngine.convert_seestar_csv_to_aavso_extended(
            csv_text=bad_csv, obscode="TEST1", starid_ui="SZ Lyn"
        )
        assert res_bad["ok"] is False and res_bad.get("errorCode") == "UNKNOWN_CSV_SCHEMA", f"Expected UNKNOWN_CSV_SCHEMA, got: {res_bad}"

    _with_isolated_storage(_run)
    print("  [PASS] 1. Header-based CSV parser (shuffled columns + future fields + explicit schema error)")


def test_2_rolling_mad_preserves_eclipse_and_ui_default_off():
    # Algol-type narrow deep eclipse (0.85 mag drop over 7 points) + 1 isolated satellite spike (+1.6 mag)
    mags = (
        [9.00, 9.01, 8.99, 9.00, 9.02, 9.00, 8.99, 9.01, 9.00, 9.00]  # baseline (0..9)
        + [9.25, 9.55, 9.80, 9.85, 9.80, 9.55, 9.25]                  # genuine narrow eclipse (10..16)
        + [9.01, 9.00, 8.99, 10.65, 9.00, 9.01, 8.99, 9.00, 9.01]     # single-frame spike at idx 20
    )
    res = PhotometryBackendEngine.detect_mad_3sigma_outliers(mags)
    assert res["method"] == "rolling_mad_3sigma"
    assert 20 in res["indices"], f"Expected single-frame spike (idx 20) to be caught: {res}"
    eclipse_cut = [i for i in range(10, 17) if i in res["indices"]]
    assert len(eclipse_cut) == 0, f"Rolling MAD must NOT cut genuine eclipse points, cut={eclipse_cut}"

    # Verify UI template checkbox is OFF by default
    tpl = open(os.path.join(BACKEND_ROOT, "pwa_mobile_and_electron/astrolab_view_template.js"), encoding="utf-8").read()
    assert '<input type="checkbox" id="chkExportClipOutliers3Sigma">' in tpl, "3-sigma export checkbox must be unchecked by default!"
    assert '<input type="checkbox" id="chkExportClipOutliers3Sigma" checked>' not in tpl
    print("  [PASS] 2. Rolling 3σ MAD preserves eclipses, catches spikes, and UI default is OFF")


def test_3_no_silent_old_night_drop():
    # Two observing nights 15 days apart (gap > 0.35d), empty storage -> ALL rows must be kept!
    rows = [STD_HEADER]
    for i in range(5):
        rows.append(_make_row(utc=f"2026.11.01 23:48:{10+i*10:02d}", jd_s=2461346.367000 + i * 0.0002, jd_e=2461346.367116 + i * 0.0002))
    for i in range(6):
        rows.append(_make_row(utc=f"2026.11.16 01:39:{10+i*10:02d}", jd_s=2461360.443800 + i * 0.0002, jd_e=2461360.443916 + i * 0.0002))
    csv_text = "\n".join(rows) + "\n"

    def _run(_tmp):
        res = PhotometryBackendEngine.convert_seestar_csv_to_aavso_extended(
            csv_text=csv_text, obscode="TEST1", starid_ui="SZ Lyn"
        )
        assert res["ok"] is True
        assert res["count"] == 11, f"Expected all 11 rows from BOTH nights, got {res['count']} (dupRemoved={res['duplicateRemovedCount']})"
        assert res["duplicateRemovedCount"] == 0
        assert len(res["sessions"]) == 2

        # Second conversion of the exact same file SHOULD deduplicate via Converted_Photometry_Storage
        res2 = PhotometryBackendEngine.convert_seestar_csv_to_aavso_extended(
            csv_text=csv_text, obscode="TEST1", starid_ui="SZ Lyn"
        )
        assert res2["ok"] is False and res2["errorCode"] == "NO_DATA_ROWS"

    _with_isolated_storage(_run)
    print("  [PASS] 3. Multi-night CSV preserves all nights on first conversion & deduplicates strictly via DB")


def test_4_storage_save_error_surfaced():
    csv_text = STD_HEADER + "\n" + _make_row() + "\n"
    orig_save = AavsoNativeAndStorageService.save_converted_session

    def _boom(*args, **kwargs):
        raise PermissionError("Simulated disk write failure")

    def _run(_tmp):
        AavsoNativeAndStorageService.save_converted_session = classmethod(lambda cls, *a, **kw: _boom())
        try:
            res = PhotometryBackendEngine.convert_seestar_csv_to_aavso_extended(
                csv_text=csv_text, obscode="TEST1", starid_ui="SZ Lyn"
            )
            assert res["ok"] is True
            assert res["storageSaved"] is False
            assert "Simulated disk write failure" in res["storageSaveWarning"]
        finally:
            AavsoNativeAndStorageService.save_converted_session = orig_save

    _with_isolated_storage(_run)
    print("  [PASS] 4. Storage save errors are logged and surfaced via storageSaveWarning (never silently swallowed)")


def test_5_saturation_p05_and_model_exposure_formula():
    # Session with median 9.2m but bright maximum at 6.5m (10s) -> p05 catches saturation!
    mags = [6.4, 6.6] + [9.2] * 18
    rows = [STD_HEADER] + [_make_row(mag=m, exp="10.0s", jd_s=2461346.367 + i * 0.0002, jd_e=2461346.367116 + i * 0.0002) for i, m in enumerate(mags)]
    csv_text = "\n".join(rows) + "\n"

    m_s50 = PhotometryBackendEngine.compute_calibration_guard_metrics(csv_text, scope_model="S50")
    assert m_s50["medianMag"] == 9.2
    assert m_s50["brightestP05Mag"] < 7.0
    assert m_s50["saturationThresholdMag"] == 7.0
    assert m_s50["saturationRisk"] is True, f"p05 should catch bright maximum saturation: {m_s50}"

    # Model-aware: S30PRO base_10s = 6.0m -> p05 ~6.59m should NOT saturate S30PRO at 10s
    m_s30p = PhotometryBackendEngine.compute_calibration_guard_metrics(csv_text, scope_model="S30PRO")
    assert m_s30p["saturationThresholdMag"] == 6.0
    assert m_s30p["saturationRisk"] is False

    # Exposure scaling: S50 at 30s -> 7.0 + 2.5*log10(3) = 8.19m
    assert compute_saturation_threshold("S50", 30.0) == 8.19
    print("  [PASS] 5. Saturation check uses 5th brightest percentile + model & 2.5*log10(EXP/10) formula")


def test_6_frame_timing_validation():
    rows = [
        STD_HEADER,
        _make_row(jd_s=2461346.367000, jd_e=2461346.367116, exp="10.0s"),      # valid (~10s)
        _make_row(jd_s=2461346.367500, jd_e=None, exp="10.0s"),                # empty jd_end -> warning
        _make_row(jd_s=2461346.368000, jd_e=2461346.367900, exp="10.0s"),      # jd_end < jd_start -> rejected
        _make_row(jd_s=2461346.369000, jd_e=2461346.370000, exp="10.0s"),      # 86.4s vs 10s -> exp mismatch warning
    ]
    csv_text = "\n".join(rows) + "\n"

    def _run(_tmp):
        res = PhotometryBackendEngine.convert_seestar_csv_to_aavso_extended(
            csv_text=csv_text, obscode="TEST1", starid_ui="SZ Lyn"
        )
        assert res["ok"] is True
        assert res["count"] == 3, f"Expected 3 valid rows (1 rejected for jd_end < jd_start), got {res['count']}"
        assert res["emptyJdEndWarnings"] == 1
        assert res["invalidTimeOrderCount"] == 1
        assert res["expDurationMismatchCount"] == 1
        assert len(res["timingWarnings"]) == 3

    _with_isolated_storage(_run)
    print("  [PASS] 6. Frame timing checks validate jd_end >= jd_start, empty jd_end, and EXP duration")


def test_7_8_docs_and_repo_hygiene():
    readme = open(os.path.join(REPO_ROOT, "README.md"), encoding="utf-8").read()
    for token in ("FILT=TG", "ENSEMBLE", "TRANS=NO", "AstroImageJ", "VPhot", "jackpot_track.mp3", "2.5·log10(EXP / 10)"):
        assert token in readme, f"README.md missing methodology/audio documentation token: {token}"
    assert os.path.isfile(os.path.join(REPO_ROOT, ".gitignore")), ".gitignore missing in repo root"
    assert not os.path.exists(os.path.join(BACKEND_ROOT, "README.md")), "Duplicate Source_and_Build/README.md must not exist"
    assert not os.path.exists(os.path.join(BACKEND_ROOT, "publish_github_hotfix_only.py")), "Old 5MB hotfix script must not exist"
    print("  [PASS] 7-8. README methodology, audio license, .gitignore, and repo hygiene verified")


def test_10_rpc_security():
    launcher = open(os.path.join(BACKEND_ROOT, "desktop_launcher.py"), encoding="utf-8").read()
    assert "require_token=False" not in launcher, "desktop_launcher.py must never disable RPC token!"

    srv = start_background_rpc_server(port=0, require_token=True)
    assert srv is not None, "Failed to start local RPC server on ephemeral port"
    port = srv.server_address[1]
    token = get_rpc_auth_token()
    try:
        # 1. GET /api/health returns 200 and does NOT leak token
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=3) as resp:
            body = resp.read().decode("utf-8")
            assert resp.status == 200
            assert token not in body

        # 2. POST without token -> 401
        req_no_tok = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/rpc",
            data=json.dumps({"action": "get_scope_profile", "code": "S50"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(req_no_tok, timeout=3)
            raise AssertionError("POST without token must return 401")
        except urllib.error.HTTPError as e:
            assert e.code == 401, f"Expected 401, got {e.code}"

        # 3. POST with untrusted Origin -> 403
        req_evil = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/rpc",
            data=json.dumps({"action": "get_scope_profile", "code": "S50"}).encode("utf-8"),
            headers={"Content-Type": "application/json", "Origin": "https://evil.example", "X-AstroLab-Token": token},
            method="POST",
        )
        try:
            urllib.request.urlopen(req_evil, timeout=3)
            raise AssertionError("POST with untrusted Origin must return 403")
        except urllib.error.HTTPError as e:
            assert e.code == 403, f"Expected 403, got {e.code}"

        # 4. POST with valid token -> 200
        req_ok = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/rpc",
            data=json.dumps({"action": "get_scope_profile", "code": "S50"}).encode("utf-8"),
            headers={"Content-Type": "application/json", "X-AstroLab-Token": token},
            method="POST",
        )
        with urllib.request.urlopen(req_ok, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert resp.status == 200 and data.get("ok") is True
    finally:
        srv.shutdown()
        srv.server_close()
    print("  [PASS] 10. Local RPC server enforces X-AstroLab-Token (401) and Origin (403), health does not leak token")


if __name__ == "__main__":
    print("=== RUNNING AUTOTEST #8: CONVERTER EDGE CASES, HYGIENE & RPC SECURITY ===")
    test_1_header_based_csv_and_unknown_schema()
    test_2_rolling_mad_preserves_eclipse_and_ui_default_off()
    test_3_no_silent_old_night_drop()
    test_4_storage_save_error_surfaced()
    test_5_saturation_p05_and_model_exposure_formula()
    test_6_frame_timing_validation()
    test_7_8_docs_and_repo_hygiene()
    test_10_rpc_security()
    print("=== CONVERTER EDGE CASES, HYGIENE & RPC SECURITY AUTOTEST: ALL PASS ===")
