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
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_ROOT = os.path.join(REPO_ROOT, "Source_and_Build")
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from backend.astrolab_backend_core import (
    AstroLabDiagnosticLogger,
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
    import backend.astrolab_backend_core as _bc
    with tempfile.TemporaryDirectory() as tmp:
        orig_get = AavsoNativeAndStorageService.get_storage_db_path
        orig_dir = _bc.get_program_converted_storage_dir
        db_file = os.path.join(tmp, "user_converted_photometry_db.json")
        os.makedirs(os.path.join(tmp, "sessions"), exist_ok=True)
        AavsoNativeAndStorageService.get_storage_db_path = classmethod(lambda cls: db_file)
        _bc.get_program_converted_storage_dir = lambda: tmp
        try:
            return fn(tmp)
        finally:
            AavsoNativeAndStorageService.get_storage_db_path = orig_get
            _bc.get_program_converted_storage_dir = orig_dir


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

    # Model-aware: S30PRO empirically calibrated base_10s = 7.7m -> p05 ~6.59m saturates S30PRO at 10s
    m_s30p = PhotometryBackendEngine.compute_calibration_guard_metrics(csv_text, scope_model="S30PRO")
    assert m_s30p["saturationThresholdMag"] == 7.7
    assert m_s30p["saturationRisk"] is True

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
    sess_dir = os.path.join(BACKEND_ROOT, "Converted_Photometry_Storage", "sessions")
    leaked_csvs = [f for f in os.listdir(sess_dir) if f.lower().endswith(".csv")] if os.path.isdir(sess_dir) else []
    assert not leaked_csvs, f"User/test session CSVs must NOT exist in repo storage: {leaked_csvs}"
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




def test_11_raw_seestar_tg_band_and_lab_only_obstracker():
    """
    [RU] Обязательный регрессионный автотест (v1.5.0 Hotfix):
         1) Сырые (неконвертированные) точки Seestar CSV, где колонка 5 = Reference magnitude ("/"),
            должны всегда получать band="TG" и полностью отображаться в полосе TG на графике AID + Ваш вклад
            (кол-во точек в TG === кол-во точек в ALL, никогда не теряются из-за "/").
         2) Режим «🔬 Загрузить в Лабораторию и проанализировать» (#btnAnalyzeInLabOnly) обязан сохранять
            сессию в «📓 Мои наблюдения» через window.getObsTrackerRecords() + window.saveObsTrackerDb()
            с filter="TG" и статусом "lab_unsubmitted", а Quality Gate должен выдавать aavsoEligible=true
            для качественных замеров (SNR >= 10, нет насыщения) и aavsoEligible=false для шумных/насыщенных.
    [EN] Mandatory regression autotest: raw Seestar CSV points must map to band="TG" (never "/") and
         Lab-Only analysis must persist sessions to My Observations via window.saveObsTrackerDb.
    """
    bridge_path = os.path.join(BACKEND_ROOT, "pwa_mobile_and_electron", "astrolab_engine_bridge.js")
    js_src = open(bridge_path, encoding="utf-8").read()

    # 1. Static structural invariants in astrolab_engine_bridge.js
    assert "window.saveObsTrackerDb = saveObsTrackerDb;" in js_src, (
        "window.saveObsTrackerDb must be exported outside the main IIFE so Lab-Only can persist sessions!"
    )
    assert "window.getObsTrackerRecords()" in js_src, (
        "btnAnalyzeInLabOnly must read obsTrackerRecords via window.getObsTrackerRecords()!"
    )
    assert "window.saveObsTrackerDb(trackerArr)" in js_src, (
        "btnAnalyzeInLabOnly must save lab_unsubmitted records via window.saveObsTrackerDb(trackerArr)!"
    )
    assert "window.refreshLabUnsubmittedReminderBar(starName)" in js_src, (
        "btnAnalyzeInLabOnly must refresh #labUnsubmittedReminderBar after saving labRec!"
    )
    assert 'band: "TG"' in js_src and 'rawBand: "TG"' in js_src, (
        "parseCurrentCsvPoints must assign band='TG' for raw Seestar CSV rows (col 5 is Reference magnitude='/')!"
    )

    # 2. Live Node.js execution against the actual functions in astrolab_engine_bridge.js
    node_bin = shutil.which("node")
    assert node_bin, "Node.js is required to run live JS regression checks for TG band and Lab-Only Quality Gate"

    node_script = r"""
const fs = require('fs');
const vm = require('vm');
const jsPath = process.argv[1];
const src = fs.readFileSync(jsPath, 'utf8');

function extractFn(source, signature) {
  const lines = source.split(/\r?\n/);
  const startIdx = lines.findIndex(l => l.includes(signature));
  if (startIdx < 0) throw new Error('Signature not found: ' + signature);
  const indent = (lines[startIdx].match(/^(\s*)/) || ['', ''])[1];
  const closeRe = new RegExp('^' + indent + '\\};?$');
  for (let i = startIdx + 1; i < lines.length; i++) {
    if (closeRe.test(lines[i])) {
      return lines.slice(startIdx, i + 1).join('\n');
    }
  }
  throw new Error('Closing brace not found for: ' + signature);
}

const fnSplit = extractFn(src, 'function splitSeestarCsvRow(');
const fnSchema = extractFn(src, 'window.resolveSeestarCsvSchema = function(');
const fnParse = extractFn(src, 'function parseCurrentCsvPoints(');
const fnPreprocess = extractFn(src, 'function preprocessPoints(');
const fnMetrics = extractFn(src, 'function computePhotometryMetrics(');
const fnElig = extractFn(src, 'function evaluateSessionAavsoEligibility(');

const sandbox = {
  console,
  Math,
  Number,
  String,
  Array,
  Object,
  Map,
  Set,
  Date,
  isNaN,
  isFinite,
  parseFloat,
  parseInt,
  _cachedCsvPtsKey: '',
  _cachedCsvPtsResult: null,
  document: { getElementById: () => null },
  window: {},
  _median: (arr) => {
    const a = arr.filter(Number.isFinite).slice().sort((x, y) => x - y);
    if (!a.length) return 0;
    const m = Math.floor(a.length / 2);
    return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
  },
  _mean: (arr) => {
    const a = arr.filter(Number.isFinite);
    return a.length ? a.reduce((s, v) => s + v, 0) / a.length : 0;
  }
};
sandbox.window = sandbox;
vm.createContext(sandbox);
vm.runInContext(
  [fnSplit, fnSchema + ';', fnParse, fnPreprocess, fnMetrics, fnElig].join('\n'),
  sandbox
);

const header = 'Name,Type,RA,DEC,Valid Reference Stars,Reference magnitude,Mag(obs),Mag(err),X Axis,Y Axis,EXP,EXP start,EXP start(JD),EXP start(MJD),EXP end,EXP end(JD),EXP end(MJD),Is Variable,SNR';

// Case A: High-SNR raw Seestar CSV (SZ Lyncis, col 5 = "/", merr = 0.045 -> SNR ~ 24)
const goodLines = [header];
for (let i = 0; i < 12; i++) {
  const jd1 = (2461360.4438 + i * 0.0002).toFixed(6);
  const jd2 = (2461360.443916 + i * 0.0002).toFixed(6);
  goodLines.push(`SZ Lyncis,Non-reference star,122.40188,44.47336,15,/,9.1200,0.0450,1096,1923,10.0s,2026.11.16 01:39:10,${jd1},61359.9438,2026.11.16 01:39:20,${jd2},61359.9439,true,24.1`);
}

const parsedGood = sandbox.parseCurrentCsvPoints(goodLines);
if (parsedGood.length !== 12) throw new Error('Expected 12 raw points, got ' + parsedGood.length);
if (parsedGood.some(p => p.band !== 'TG')) {
  throw new Error('Raw Seestar points must ALL have band=TG, got: ' + JSON.stringify(parsedGood.map(p => p.band)));
}

const inTg = sandbox.preprocessPoints(parsedGood, { band: 'TG' });
const inAll = sandbox.preprocessPoints(parsedGood, { band: 'ALL' });
if (inTg.length !== 12 || inTg.length !== inAll.length) {
  throw new Error(`TG band dropped unconverted Seestar points! TG=${inTg.length}, ALL=${inAll.length}`);
}

// Legacy/malformed "/" or "IR-CUT" band normalization in preprocessPoints
const legacyPts = [
  { jd: 2461360.5, mag: 9.1, merr: 0.04, band: '/' },
  { jd: 2461360.51, mag: 9.12, merr: 0.04, band: 'IR-CUT' },
  { jd: 2461360.52, mag: 9.11, merr: 0.04, band: '' }
];
const normTg = sandbox.preprocessPoints(legacyPts, { band: 'TG' });
if (normTg.length !== 3 || normTg.some(p => p.band !== 'TG')) {
  throw new Error('preprocessPoints failed to normalize legacy "/" or "IR-CUT" to TG: ' + JSON.stringify(normTg));
}

// Quality Gate for high-SNR good session -> aavsoEligible = true
const qgGood = sandbox.evaluateSessionAavsoEligibility(parsedGood, { calibrationBlocked: false });
if (!qgGood.eligible) {
  throw new Error('Good high-SNR session should be aavsoEligible=true, got: ' + JSON.stringify(qgGood));
}

// Case B: Noisy/saturated raw Seestar CSV (W UMa 30s, col 5 = "/", merr = 0.197 -> SNR ~ 5.5 < 10)
const noisyLines = [header];
for (let i = 0; i < 8; i++) {
  const jd1 = (2461361.4000 + i * 0.0004).toFixed(6);
  const jd2 = (2461361.400347 + i * 0.0004).toFixed(6);
  noisyLines.push(`W Ursae Majoris,Non-reference star,145.941,55.954,12,/,7.6400,0.1970,800,900,30.0s,2026.11.17 01:00:00,${jd1},61360.9000,2026.11.17 01:00:30,${jd2},61360.9003,true,5.5`);
}
const parsedNoisy = sandbox.parseCurrentCsvPoints(noisyLines);
if (parsedNoisy.length !== 8 || parsedNoisy.some(p => p.band !== 'TG')) {
  throw new Error('Noisy raw Seestar points must still map to band=TG');
}
const noisyInTg = sandbox.preprocessPoints(parsedNoisy, { band: 'TG' });
if (noisyInTg.length !== 8) {
  throw new Error('Noisy raw Seestar points must still be visible in TG band, got ' + noisyInTg.length);
}
const qgNoisy = sandbox.evaluateSessionAavsoEligibility(parsedNoisy, { calibrationBlocked: true });
if (qgNoisy.eligible) {
  throw new Error('Noisy/saturated session (SNR~5.5, calibrationBlocked) must be aavsoEligible=false');
}

console.log('NODE_TG_AND_LAB_ONLY_OK');
"""
    proc = subprocess.run([node_bin, "-e", node_script, bridge_path], capture_output=True, text=True, timeout=20)
    assert proc.returncode == 0 and "NODE_TG_AND_LAB_ONLY_OK" in proc.stdout, (
        f"Node.js TG-band / Lab-Only regression test failed!\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )
    print("  [PASS] 11. Raw Seestar CSV points map to TG band (never '/') & Lab-Only persists to My Observations with Quality Gate")




def test_12_diagnostic_logging_opt_in_clear_and_custom_dir():
    """
    [RU] Обязательный автотест управления диагностическим логом:
         1) По умолчанию запись выключена (не создаёт файл astrolab_debug.log).
         2) После включения события пишутся; clear_log() удаляет старый лог и ротированные копии.
         3) set_export_dir() сохраняет выбранную папку, и export_diagnostic_report() пишет отчёт туда.
         4) После выключения запись прекращается.
    """
    orig_env_dir = os.environ.get("ASTROLAB_LOG_DIR")
    orig_force = os.environ.get("ASTROLAB_FORCE_DIAG_LOG")
    try:
        os.environ.pop("ASTROLAB_FORCE_DIAG_LOG", None)
        with tempfile.TemporaryDirectory() as tmp_log_dir, tempfile.TemporaryDirectory() as tmp_export_dir:
            os.environ["ASTROLAB_LOG_DIR"] = tmp_log_dir
            AstroLabDiagnosticLogger._close_handlers_unlocked()

            # 1. Disabled by default -> must NOT create astrolab_debug.log
            assert AstroLabDiagnosticLogger.is_enabled() is False
            AstroLabDiagnosticLogger.init_session("autotest_disabled")
            AstroLabDiagnosticLogger.log_event("INFO", "TEST", "should_not_be_written")
            log_file = AstroLabDiagnosticLogger.get_log_file_path()
            assert not os.path.exists(log_file), "Log file must NOT be created while logging is OFF!"

            # 2. Enable -> writes events
            r_en = AstroLabDiagnosticLogger.set_enabled(True)
            assert r_en["ok"] is True and AstroLabDiagnosticLogger.is_enabled() is True
            AstroLabDiagnosticLogger.log_event("INFO", "TEST", "old_session_marker_12345")
            assert os.path.isfile(log_file)
            assert "old_session_marker_12345" in open(log_file, encoding="utf-8").read()

            # Create a fake rotated backup .1 and clear_log() -> both old log and backup wiped!
            backup_file = log_file + ".1"
            open(backup_file, "w", encoding="utf-8").write("ancient_v121_error\n")
            r_clr = AstroLabDiagnosticLogger.clear_log()
            assert r_clr["ok"] is True and r_clr["deletedCount"] >= 2, f"Expected >=2 deleted, got {r_clr}"
            assert not os.path.exists(backup_file), "Rotated backup .log.1 must be deleted on clear_log()"
            fresh_txt = open(log_file, encoding="utf-8").read()
            assert "old_session_marker_12345" not in fresh_txt, "Old log content must be wiped!"
            assert "log_cleared" in fresh_txt, "Fresh log session header must start after clear_log()"

            # 3. Custom export folder persists and receives exported report
            r_dir = AstroLabDiagnosticLogger.set_export_dir(tmp_export_dir)
            assert r_dir["ok"] is True and os.path.abspath(r_dir["exportDir"]) == os.path.abspath(tmp_export_dir)
            assert AstroLabDiagnosticLogger.is_enabled() is True, "set_export_dir must preserve enabled flag"
            r_exp = AstroLabDiagnosticLogger.export_diagnostic_report({"test": True})
            assert r_exp["ok"] is True
            assert os.path.dirname(os.path.abspath(r_exp["path"])) == os.path.abspath(tmp_export_dir)
            assert os.path.isfile(r_exp["path"])

            # 4. Disable -> stops writing immediately
            r_dis = AstroLabDiagnosticLogger.set_enabled(False)
            assert r_dis["ok"] is True and AstroLabDiagnosticLogger.is_enabled() is False
            size_before = os.path.getsize(log_file)
            AstroLabDiagnosticLogger.log_event("ERROR", "TEST", "must_not_append_when_off")
            assert os.path.getsize(log_file) == size_before, "No bytes may be appended when logging is OFF!"

            AstroLabDiagnosticLogger._close_handlers_unlocked()

        # 5. UI & DesktopApi wiring checks
        tpl = open(os.path.join(BACKEND_ROOT, "pwa_mobile_and_electron/astrolab_view_template.js"), encoding="utf-8").read()
        assert 'id="btnChooseDiagLogDir"' in tpl and 'id="btnClearDiagnosticLog"' in tpl
        dl = open(os.path.join(BACKEND_ROOT, "desktop_launcher.py"), encoding="utf-8").read()
        assert "def backend_clear_diagnostic_log(" in dl and "def backend_choose_diagnostic_log_dir(" in dl
    finally:
        AstroLabDiagnosticLogger._close_handlers_unlocked()
        if orig_env_dir is None:
            os.environ.pop("ASTROLAB_LOG_DIR", None)
        else:
            os.environ["ASTROLAB_LOG_DIR"] = orig_env_dir
        if orig_force is not None:
            os.environ["ASTROLAB_FORCE_DIAG_LOG"] = orig_force
    print("  [PASS] 12. Diagnostic log is strictly opt-in, clearable (with backups), and supports custom export folder")




def test_13_offline_catalog_guard_and_network_timeouts():
    """
    [RU] Обязательный автотест офлайн-защиты и отсутствия зависаний/зацикливаний в сетевых вызовах:
         1) btnFetchAll проверяет simbadOk / vspOk / localMatched и при офлайне + отсутствии звезды
            в локальном каталоге НЕ ставит data-source="catalog" и НЕ сворачивает Раздел 1.
         2) Все вызовы Open-Meteo Geocoding имеют явный AbortController-таймаут (6s).
         3) Все вызовы urlopen в бэкенде имеют конечный timeout=, а пагинация AAVSO AID ограничена лимитом страниц.
    """
    bridge_path = os.path.join(BACKEND_ROOT, "pwa_mobile_and_electron", "astrolab_engine_bridge.js")
    js_src = open(bridge_path, encoding="utf-8").read()

    # 1. Offline guard in btnFetchAll
    assert "const catalogConfirmed = Boolean(simbadOk || vspOk || localMatched || (finalCatRec && finalCatRec.matched));" in js_src
    assert 'staridEl.removeAttribute("data-source");' in js_src
    assert "errOfflineStarNotFound" in js_src

    # 2. Zero bare unbounded geocoding fetch(url) calls
    for line in js_src.splitlines():
        if "geocoding-api.open-meteo.com" in line and "fetch(" in line:
            assert "signal:" in line, f"Geocoding fetch missing AbortController signal: {line.strip()}"
    assert "geoCtrl1.abort(), 6000" in js_src
    assert "geoCtrl2.abort(), 6000" in js_src
    assert "geoCtrl3.abort(), 6000" in js_src

    # 3. Backend urlopen timeouts & bounded pagination
    core_src = open(os.path.join(BACKEND_ROOT, "backend", "astrolab_backend_core.py"), encoding="utf-8").read()
    for line in core_src.splitlines():
        if "_urlopen_with_ssl_fallback(" in line and "def " not in line:
            assert "timeout=" in line, f"Backend network call missing timeout=: {line.strip()}"
    assert "while next_url and pages_fetched < 6" in core_src, "AAVSO AID pagination loop must have a strict page cap!"
    print("  [PASS] 13. Offline catalog guard (no false OK/collapse), geocoder timeouts (6s), and bounded backend network loops verified")




def test_14_csv_verification_aavso_guard_badges_and_3sigma_default():
    """
    [RU] Обязательный браузерный E2E-автотест (реальный Chromium) проверки CSV и формул сверки:
         1) Галочка >3σ при экспорте реально ВЫКЛЮЧЕНА по умолчанию после загрузки JS.
         2) Загрузка уже сконвертированного AAVSO Extended файла (#TYPE=EXTENDED) вместо сырого
            Seestar Magnitude_*.csv: блокирует Шаг 3, открывает модалку ошибки с явным пояснением,
            убирает зелёный статус pill-ready с Шага 2 и Шага 3.
         3) Загрузка сырого CSV другой звезды (W UMa против SZ Lyn): строит таблицу сверки (6 строк),
            выявляет критические расхождения STARID + RA + DEC, блокирует экспорт и убирает pill-ready.
         4) Загрузка сырого CSV совпадающей звезды (SZ Lyn против SZ Lyn): строит таблицу (6 строк),
            снимает блокировку, открывает кнопку конвертации и ставит зелёный pill-ready.
    """
    import re
    sys.path.insert(0, os.path.dirname(__file__))
    import run_localization_autotest as loc

    html_src = (loc.PWA / "index.html").read_text(encoding="utf-8")
    tpl_js = (loc.PWA / "astrolab_view_template.js").read_text(encoding="utf-8")
    eng_js = (loc.PWA / "astrolab_engine_bridge.js").read_text(encoding="utf-8")
    bundled = re.sub(r'<script src="astrolab_view_template\.js[^"]*"></script>', lambda _: f"<script>{tpl_js}</script>", html_src)
    bundled = re.sub(r'<script src="astrolab_engine_bridge\.js[^"]*"></script>', lambda _: f"<script>{eng_js}</script>", bundled)

    aavso_converted = (
        "#TYPE=EXTENDED\n#OBSCODE=APPA\n#SOFTWARE=Seestar\n#DELIM=,\n#DATE=JD\n#OBSTYPE=CMOS\n"
        "#NAME,DATE,MAG,MERR,FILT,TRANS,MTYPE,CNAME,CMAG,KNAME,KMAG,AMASS,GROUP,CHART,NOTES\n"
        "W UMa,2461360.500000,7.4818,0.0450,TG,NO,STD,ENSEMBLE,na,na,na,na,na,X42562V,Seestar\n"
    )
    raw_wuma = STD_HEADER + "\n" + (
        "W Ursae Majoris,Non-reference star,145.943086,55.954105,12,/,7.4818,0.0450,"
        "800,900,20.0s,2026.11.16 02:56:21,2461360.497465,61359.997465,2026.11.16 02:56:41,2461360.497697,61359.997697,true,22.0\n"
    )
    raw_szlyn = STD_HEADER + "\n" + _make_row(star="SZ Lyncis", mag=9.15, merr=0.045, exp="10.0s") + "\n"

    js = f"""
    (async () => {{
      const aavsoTxt = {json.dumps(aavso_converted)};
      const rawWuma = {json.dumps(raw_wuma)};
      const rawSzlyn = {json.dumps(raw_szlyn)};
      const out = {{}};

      document.getElementById('obscode').value = 'APPA';
      document.getElementById('starid').value = 'SZ Lyn';
      document.getElementById('ra').value = '122.40188';
      document.getElementById('dec').value = '+44.47336';
      document.getElementById('chart').value = 'X42562V';
      window.STATE.catalogStarName = 'SZ Lyn';
      window.STATE.catalogRa = 122.40188;
      window.STATE.catalogDec = 44.47336;
      window.STATE.simbadCatalogLoaded = true;
      out.default_chk3s = document.getElementById('chkExportClipOutliers3Sigma')?.checked;

      async function loadCsv(name, txt) {{
        const dt = new DataTransfer();
        dt.items.add(new File([txt], name, {{ type: 'text/csv' }}));
        const inp = document.getElementById('csvFile');
        inp.files = dt.files;
        inp.dispatchEvent(new Event('change', {{ bubbles: true }}));
        await new Promise(r => setTimeout(r, 450));
        return {{
          tableDisplay: document.getElementById('previewTable')?.style.display,
          rowsCount: document.querySelectorAll('#previewTable tbody tr').length,
          blocked: window.STATE.isConversionBlockedByMismatch,
          reasons: window.STATE.lastMismatchReasons,
          btnConvertDisabled: document.getElementById('btnConvert')?.disabled,
          btnLabDisabled: document.getElementById('btnAnalyzeInLabOnly')?.disabled,
          modalDisplay: document.getElementById('criticalMismatchModal')?.style.display,
          filePillReady: document.getElementById('accFileSummaryPill')?.classList.contains('pill-ready'),
          convPillReady: document.getElementById('accConvertSummaryPill')?.classList.contains('pill-ready'),
        }};
      }}

      out.c_aavso = await loadCsv('W_UMa_2026-11-16_02-56-21_105pts_Seestar.csv', aavsoTxt);
      // In AAVSO Export mode, summary CSV (without reference stars) MUST be blocked
      out.c_summary_aavso_blocked = await loadCsv('Magnitude_08h 09m 36s +44° 28′ 23″.csv', rawSzlyn);
      // In Lab-Only mode, summary CSV is allowed for inspection and still runs full mismatch verification
      if (window.setAstrolabWorkflowMode) window.setAstrolabWorkflowMode('lab');
      out.c_mismatch = await loadCsv('Magnitude_09h 43m 46s +55° 57′ 14″.csv', rawWuma);
      // Back to AAVSO Export mode: per-frame CSV (with reference stars) passes full verification & unlocks conversion
      if (window.setAstrolabWorkflowMode) window.setAstrolabWorkflowMode('aavso');
      const perFrameSzlyn = rawSzlyn.trim() + String.fromCharCode(10) +
        ',reference star,122.50,44.50,15,9.500,9.500,0.015,100,100,10.0s,2026.11.16 01:00:00,2461360.5000,61360.0000,2026.11.16 01:00:10,2461360.5001,61360.0001,false,150.0' + String.fromCharCode(10) +
        ',reference star,122.60,44.55,15,9.800,9.800,0.015,200,200,10.0s,2026.11.16 01:00:00,2461360.5000,61360.0000,2026.11.16 01:00:10,2461360.5001,61360.0001,false,140.0' + String.fromCharCode(10) +
        ',reference star,122.30,44.40,15,10.100,10.100,0.015,300,300,10.0s,2026.11.16 01:00:00,2461360.5000,61360.0000,2026.11.16 01:00:10,2461360.5001,61360.0001,false,130.0';
      out.c_match = await loadCsv('Magnitude_08h 09m 36s +44° 28′ 23″_010000.csv', perFrameSzlyn);
      return JSON.stringify(out);
    }})()
    """
    raw = loc.eval_in_browser(bundled, js, port=9297, await_promise=True, wait_ms=1400)
    res = json.loads(raw)

    assert res["default_chk3s"] is False, f"3-sigma checkbox MUST be OFF by default at runtime! Got: {res['default_chk3s']}"

    c1 = res["c_aavso"]
    assert c1["blocked"] is True and c1["btnConvertDisabled"] is True and c1["btnLabDisabled"] is True, f"Already-converted AAVSO CSV must lock conversion: {c1}"
    assert c1["modalDisplay"] == "flex", f"Already-converted AAVSO CSV must show alert modal: {c1}"
    assert any("AAVSO Extended" in r for r in c1["reasons"]), f"Reason must identify AAVSO Extended file: {c1}"
    assert c1["filePillReady"] is False and c1["convPillReady"] is False, f"Step 2 & 3 badges must NOT be green on invalid CSV: {c1}"

    csum = res["c_summary_aavso_blocked"]
    assert csum["blocked"] is True and csum["btnConvertDisabled"] is True, f"Summary CSV MUST be blocked in AAVSO Export mode: {csum}"

    c2 = res["c_mismatch"]
    assert c2["tableDisplay"] == "table" and c2["rowsCount"] >= 6, f"Raw mismatched CSV must render comparison table: {c2}"
    assert c2["blocked"] is True and c2["btnConvertDisabled"] is True and len(c2["reasons"]) >= 3, f"Raw W UMa vs SZ Lyn must trigger STARID+RA+DEC mismatch: {c2}"
    assert c2["filePillReady"] is False and c2["convPillReady"] is False, f"Step 2 & 3 badges must NOT be green on mismatch: {c2}"

    c3 = res["c_match"]
    assert c3["tableDisplay"] == "table" and c3["rowsCount"] >= 6, f"Raw matching CSV must render comparison table: {c3}"
    assert c3["blocked"] is False and c3["btnConvertDisabled"] is False, f"Raw SZ Lyn vs SZ Lyn must unlock conversion: {c3}"
    assert c3["filePillReady"] is True and c3["convPillReady"] is True, f"Step 2 & 3 badges must be green on valid matching CSV: {c3}"

    print("  [PASS] 14. Real-Chromium E2E: >3σ default OFF, AAVSO Extended guard, raw mismatch/match verification & accordion badges")




def test_15_offline_notifications_all_four_buttons():
    """
    [RU] Обязательный автотест офлайн-уведомлений для всех 4 кнопок из живого лога Windows:
         #btnHeaderSkyClarity, #btnRadarFetchTargetToolApi, #btnReloadAavsoCurve и #btnFetchAll (локальный фолбэк).
    """
    bridge_path = os.path.join(BACKEND_ROOT, "pwa_mobile_and_electron", "astrolab_engine_bridge.js")
    js_src = open(bridge_path, encoding="utf-8").read()
    for key in (
        "errOfflineSkyClarity",
        "errOfflineRadarApi",
        "errOfflineAavsoCurve",
        "offlineLocalFallbackTitle",
        "offlineLocalFallbackMsg",
    ):
        assert key in js_src, f"Missing offline notification key/usage: {key}"
    assert "if (!simbadOk && !vspOk && (localMatched || (finalCatRec && finalCatRec.matched)))" in js_src
    assert 'if (OBSERVER_GEO_STATE.skyClarityPct === null && typeof showIosNotification === "function")' in js_src
    print("  [PASS] 15. Offline notifications verified for Sky Clarity, Target Radar API, AAVSO Curve reload & local catalog fallback")




def test_per_frame_recalibration_and_zp_inflation():
    from csv_schema import recalibrate_per_frame_seestar_csvs, is_per_frame_seestar_csv
    per_frame_csv = (
        "Name,Type,RA,DEC,Valid Reference Stars,Reference magnitude,Mag(obs),Mag(err),X Axis,Y Axis,EXP,EXP start,EXP start(JD),EXP start(MJD),EXP end,EXP end(JD),EXP end(MJD),Is Variable,SNR\n"
        ",reference star,146.63,57.12,15,4.028,6.271,0.181,564,905,20.0s,2026.11.16 03:31:54,2461360.522160,61360.022160,2026.11.16 03:32:14,2461360.522395,61360.022395,false,389.0\n"
        ",reference star,145.62,56.18,15,8.615,8.195,0.181,1102,1834,20.0s,2026.11.16 03:31:54,2461360.522160,61360.022160,2026.11.16 03:32:14,2461360.522395,61360.022395,false,79.3\n"
        ",reference star,143.96,54.69,15,8.629,8.209,0.181,2035,3290,20.0s,2026.11.16 03:31:54,2461360.522160,61360.022160,2026.11.16 03:32:14,2461360.522395,61360.022395,false,100.0\n"
        ",reference star,145.67,55.66,15,8.645,8.225,0.181,1070,2347,20.0s,2026.11.16 03:31:54,2461360.522160,61360.022160,2026.11.16 03:32:14,2461360.522395,61360.022395,false,107.7\n"
        "W Ursae Majoris,Non-reference star,145.943,55.954,15,/,7.580,0.181,926,2063,20.0s,2026.11.16 03:31:54,2461360.522160,61360.022160,2026.11.16 03:32:14,2461360.522395,61360.022395,true,157.0\n"
    )
    assert is_per_frame_seestar_csv(per_frame_csv) is True
    rec = recalibrate_per_frame_seestar_csvs([per_frame_csv], target_name_hint="W Ursae Majoris")
    assert rec["framesProcessed"] == 1
    assert abs(rec["medianZpShiftMag"] - (-0.42)) < 0.02, f"Unexpected shift: {rec}"
    assert rec["avgSaturatedRefs"] == 1.0
    assert "8.000" in rec["csvText"], f"Expected recalibrated mag ~8.000 in {rec['csvText']}"

    summary_csv = (
        "Name,Type,RA,DEC,Valid Reference Stars,Reference magnitude,Mag(obs),Mag(err),X Axis,Y Axis,EXP,EXP start,EXP start(JD),EXP start(MJD),EXP end,EXP end(JD),EXP end(MJD),Is Variable,SNR\n"
        "W Ursae Majoris,Non-reference star,145.943,55.954,15,/,7.58,0.183,926,2063,20.0s,2026.11.16 03:31:54,2461360.522160,61360.022160,2026.11.16 03:32:14,2461360.522395,61360.022395,true,180.0\n"
    )
    cg = PhotometryBackendEngine.compute_calibration_guard_metrics(summary_csv, scope_model="S30PRO")
    assert cg["zpInflationRisk"] is True, f"Expected zpInflationRisk=True: {cg}"
    assert cg["zpInflationRatio"] > 20.0
    print("PER_FRAME_RECALIBRATION_AND_ZP_INFLATION_PASS")


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
    test_11_raw_seestar_tg_band_and_lab_only_obstracker()
    test_12_diagnostic_logging_opt_in_clear_and_custom_dir()
    test_13_offline_catalog_guard_and_network_timeouts()
    test_14_csv_verification_aavso_guard_badges_and_3sigma_default()
    test_15_offline_notifications_all_four_buttons()
    print("=== CONVERTER EDGE CASES, HYGIENE & RPC SECURITY AUTOTEST: ALL PASS ===")
