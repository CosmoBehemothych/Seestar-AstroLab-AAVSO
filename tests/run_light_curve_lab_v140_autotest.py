#!/usr/bin/env python3
"""
Mandatory v1.4.0 Autotest (Zero-JS-Error Real-Click E2E + Backend API v2/delim + Scientific Light Curve Lab):
  1. Backend AAVSO AID Light Curve:
     - Verifies Channel 1 (AAVSO API v2) does NOT pass invalid fromjd/tojd params & paginates via `next`
     - Verifies Channel 2 fallback (api.delim) keeps NEWEST 3,000 tail from 3,500 rows & preserves 2-pt sparse curves
  2. Frontend Real-Click E2E (strictly ZERO uncaught JS errors / ReferenceErrors):
     - Radar exact filtered counter (> 60) + #btnRadarFetchTargetToolApi disabled/enabled state
     - Real DOM click on #btnRunLightCurveAnalysis (zero custom args!) reading window._STATE_CURVES
     - Real DOM click on #btnFpTogglePhaseMode verifying canvas.toDataURL() ACTUALLY CHANGES
     - Real change events on #fpBandFilterSelect, #fpBinningSelect, #chkFpSigmaClip
  3. Scientific Classifier Accuracy:
     - Pulsating (P=0.1205d), Eclipsing Binary (EA), Nova Outburst (2.8 mag), Exoplanet Transit (0.025 mag)
"""

import json
import os
import re
import sys
from unittest.mock import patch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "Source_and_Build", "backend"))
sys.path.insert(0, os.path.dirname(__file__))

import astrolab_backend_core as core
import run_localization_autotest as loc

Svc = core.AavsoNativeAndStorageService


class _FakeResp:
    def __init__(self, text: str):
        self._b = text.encode("utf-8")

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_backend_aavso_aid_api_v2_and_delim_tail():
    print("[1/3] Backend AAVSO AID: API v2 valid params + pagination & api.delim 3,500-row newest-tail...")
    import time
    now_jd = (time.time() / 86400.0) + 2440587.5

    # 1a. Channel 1 (API v2): verify NO invalid fromjd/tojd query params & multi-page pagination
    seen_urls = []

    # 1d. Channel 1 (Primary fast vsx.aavso.org api.delim, no token): verify real column extraction
    wo_csv = "JD,Magnitude,Uncertainty,Band,Observer Code\n2461360.4150,9.142,0.014,TG,APPA\n2461360.4250,9.085,0.012,V,HMB\n"
    with patch("urllib.request.urlopen", return_value=_FakeResp(wo_csv)):
        res_wo = Svc.fetch_aavso_light_curve("SZ Lyn", days_back=3650)
    assert res_wo["ok"] is True and res_wo["totalAavsoPoints"] == 2, f"Primary api.delim parser failed: {res_wo}"
    assert res_wo["otherObserversPoints"][0]["band"] == "TG" and res_wo["otherObserversPoints"][1]["band"] == "V"

    def _fake_api_v2(req, timeout=6.0, context=None):
        u = req.full_url if hasattr(req, "full_url") else str(req)
        seen_urls.append(u)
        if "vsx.aavso.org" in u:
            return _FakeResp("<html></html>")
        assert "fromjd=" not in u and "tojd=" not in u, f"API v2 must NOT pass invalid fromjd/tojd params: {u}"
        if "page=2" not in u:
            results = [{"jd_dbl": now_jd - 2.0 + i * 0.01, "magnitude": "9.10", "uncertainty": 0.015, "band": "22", "obscode": "OBS1", "fainterthan": False} for i in range(60)]
            return _FakeResp(json.dumps({"results": results, "next": "https://apps.aavso.org/v2/api/observations/photometry/?target=SZ+Lyn&page_size=200&page=2"}))
        results = [{"jd_dbl": now_jd - 1.0 + i * 0.01, "magnitude": "9.25", "uncertainty": 0.015, "band": "22", "obscode": "OBS2", "fainterthan": False} for i in range(60)]
        return _FakeResp(json.dumps({"results": results, "next": None}))

    with patch("urllib.request.urlopen", side_effect=_fake_api_v2):
        res_v2 = Svc.fetch_aavso_light_curve("SZ Lyn", days_back=180, max_points=3000)
    assert res_v2["ok"] is True and res_v2["totalAavsoPoints"] == 120, f"API v2 pagination failed: {res_v2}"
    assert len([u for u in seen_urls if "apps.aavso.org/v2/api/observations" in u]) == 2, f"Expected 2 paginated API v2 requests, got {seen_urls}"

    # 1b. Channel 2 fallback (api.delim): 3,500 chronological rows -> keep newest 3,000 tail
    rows = ["JD,Magnitude,Uncertainty,Band,Observer Code"]
    for i in range(1, 3501):
        rows.append(f"{2461000.0 + i * 0.0001:.6f},9.123,0.015,TG,OBS1")
    big_csv = "\n".join(rows)

    def _fake_fallback(req, timeout=9.0, context=None):
        u = req.full_url if hasattr(req, "full_url") else str(req)
        if "view=api.delim" in u:
            return _FakeResp(big_csv)
        if "apps.aavso.org/v2/api/observations" in u:
            return _FakeResp(json.dumps({"results": [], "next": None}))
        return _FakeResp(big_csv)

    with patch("urllib.request.urlopen", side_effect=_fake_fallback):
        res = Svc.fetch_aavso_light_curve("SZ Lyn", days_back=180, max_points=3000)

    assert res["ok"] is True and res["hasAavsoData"] is True
    assert res["totalAavsoPoints"] == 3000, f"Expected 3000 points, got {res['totalAavsoPoints']}"
    first_jd = res["otherObserversPoints"][0]["jd"]
    last_jd = res["otherObserversPoints"][-1]["jd"]
    assert abs(last_jd - 2461000.3500) < 1e-4 and abs(first_jd - 2461000.0501) < 1e-4

    # 1c. Preserve sparse 2-point curve
    small_csv = "JD,Magnitude,Uncertainty,Band,Observer Code\n2461300.1,11.2,0.02,V,ABC\n2461301.2,11.4,0.02,V,DEF\n"
    def _fake_small(req, timeout=9.0, context=None):
        u = req.full_url if hasattr(req, "full_url") else str(req)
        if "view=api.delim" in u:
            return _FakeResp(small_csv)
        if "apps.aavso.org/v2/api/observations" in u:
            return _FakeResp(json.dumps({"results": [], "next": None}))
        return _FakeResp(small_csv)
    with patch("urllib.request.urlopen", side_effect=_fake_small):
        res2 = Svc.fetch_aavso_light_curve("V999 Cas", days_back=180)
    assert res2["hasAavsoData"] is True and res2["totalAavsoPoints"] == 2
    print("  PASS: API v2 pagination (120 pts, valid params) + api.delim newest tail (3,000/3,500) + 2-pt sparse curve")


def test_frontend_real_clicks_zero_errors_and_scientific_lab():
    print("[2/3] Frontend Real-Click E2E (zero JS errors) + Radar API Button + Scientific Lab...")
    pwa = os.path.join(REPO_ROOT, "Source_and_Build", "pwa_mobile_and_electron")
    html = open(os.path.join(pwa, "index.html"), encoding="utf-8").read()
    css = open(os.path.join(pwa, "astrolab_styles.css"), encoding="utf-8").read()
    tpl = open(os.path.join(pwa, "astrolab_view_template.js"), encoding="utf-8").read()
    eng = open(os.path.join(pwa, "astrolab_engine_bridge.js"), encoding="utf-8").read()
    bundled = re.sub(r'<link[^>]+astrolab_styles\.css[^>]*>', lambda m: f'<style>{css}</style>', html)
    bundled = re.sub(r'<script[^>]+astrolab_view_template\.js[^>]*></script>', lambda m: f'<script>{tpl}</script>', bundled)
    bundled = re.sub(r'<script[^>]+astrolab_engine_bridge\.js[^>]*></script>', lambda m: f'<script>{eng}</script>', bundled)

    js = r"""
    (async () => {
      const jsErrors = [];
      window.addEventListener("error", (e) => jsErrors.push(String(e.message || e)));
      window.addEventListener("unhandledrejection", (e) => jsErrors.push(String(e.reason || e)));

      const sp = document.getElementById("splashModal");
      if (sp) sp.remove();

      // 1. Radar API button disabled/enabled toggle
      window._syncRadarApiFetchButton(false);
      const apiBtn = document.getElementById("btnRadarFetchTargetToolApi");
      const disabledNoKey = Boolean(apiBtn && apiBtn.disabled === true);
      window._syncRadarApiFetchButton(true);
      const enabledWithKey = Boolean(apiBtn && apiBtn.disabled === false);
      window._syncRadarApiFetchButton(false);
      const disabledAfterClear = Boolean(apiBtn && apiBtn.disabled === true);

      // 2. Radar exact filtered counter (> 60) under 60-card windowing
      const extra = [];
      for (let i = 1; i <= 400; i++) {
        extra.push({ star: `V7${String(i).padStart(3, "0")} Cyg`, con: "Cyg", ra: 300 + (i % 20) * 0.1, dec: 45 + (i % 15) * 0.1, type: "CV", magRange: "11-13 mag", isLiveTargetTool: true });
      }
      window.mergeLiveAavsoTargetsIntoCatalog(extra, "target_tool");
      window.renderV6RadarDock();
      const cntTxt = (document.getElementById("v6RadarCountText")?.textContent || "").trim();
      const domCards = document.querySelectorAll("#v6RadarListContainer .v6-target-card").length;
      window.resetLiveAavsoTargetsToBaseline();

      // 2b. DIRECT E2E TEST of fetchAavsoCurveSeriesForStar() with mocked pywebview backend (prevents silent empty return!)
      const mockBackendPts = [];
      for (let i = 0; i < 150; i++) {
        mockBackendPts.push({ jd: 2461350.0 + i * 0.01, mag: 9.1 + 0.3 * Math.sin(i * 0.2), merr: 0.015, band: "TG", obscode: "OTHER1" });
      }
      window.pywebview = {
        api: {
          backend_fetch_aavso_light_curve: async () => ({
            ok: true,
            hasAavsoData: true,
            otherObserversPoints: mockBackendPts,
            userAavsoPoints: []
          })
        }
      };
      const fetchBridgeRes = await window.fetchAavsoCurveSeriesForStar("SZ Lyn", "APPA");

      // 3. REAL-USER CLICK TEST inside #fullPageLightCurveModal (ZERO custom args!)
      const jd0 = 2461360.0;
      const trueP = 0.1205;
      const pulsPts = [];
      for (let i = 0; i < 90; i++) {
        const t = jd0 + i * 0.0072;
        const mag = 9.0 + 0.40 * Math.sin(2 * Math.PI * (t - jd0) / trueP);
        pulsPts.push({ jd: t, mag, merr: 0.012, band: "TG", source: "AAVSO_AID_DELIM", obscode: "OBS1" });
      }
      const starInp = document.getElementById("starid"); if (starInp) starInp.value = "SZ Lyn";
      window._STATE_CURVES.star = "SZ Lyn";
      window._STATE_CURVES.aavsoLoadedForStar = "sz lyn";
      window._STATE_CURVES.fullPageMode = "aavso_combined";
      window._STATE_CURVES.aavsoOtherPoints = pulsPts;
      window._STATE_CURVES.aavsoHasEnoughData = true;

      const fpModal = document.getElementById("fullPageLightCurveModal");
      fpModal.classList.add("open");
      if (typeof window.renderFullPageScrollableChart === "function") window.renderFullPageScrollableChart();

      const fpCanvas = document.getElementById("fullPageLightCurveCanvas");
      const beforeUrl = fpCanvas.toDataURL();

      // Real DOM click on "Analyze Curve & Auto-Triggers" (NO custom args!)
      document.getElementById("btnRunLightCurveAnalysis").click();
      const panelEl = document.getElementById("lcAnalysisResultPanel");
      const panelVisible = Boolean(panelEl && panelEl.style.display !== "none" && panelEl.textContent.length > 60);
      const panelHasPeriod = Boolean(panelEl && (panelEl.textContent.includes("2.8") || panelEl.textContent.includes("2.9") || panelEl.textContent.includes("0.12")));

      // Real DOM click on "Phase Plot" button -> verify canvas pixels ACTUALLY CHANGE!
      const btnPhase = document.getElementById("btnFpTogglePhaseMode");
      const phaseLabelBefore = btnPhase.textContent;
      btnPhase.click();
      const phaseActiveAfterClick = Boolean(window._fpPhaseModeActive);
      const phaseLabelAfter = btnPhase.textContent;
      const afterPhaseUrl = fpCanvas.toDataURL();
      const canvasChangedOnPhase = (afterPhaseUrl !== beforeUrl);

      // Real change events on Band, Binning, and 3σ Clip
      const bandSel = document.getElementById("fpBandFilterSelect");
      bandSel.value = "TG";
      bandSel.dispatchEvent(new Event("change", { bubbles: true }));
      const binSel = document.getElementById("fpBinningSelect");
      binSel.value = "10";
      binSel.dispatchEvent(new Event("change", { bubbles: true }));
      const clipChk = document.getElementById("chkFpSigmaClip");
      clipChk.checked = true;
      clipChk.dispatchEvent(new Event("change", { bubbles: true }));

      // Toggle back to Time Series mode & verify filtered Time Series visually changes canvas!
      btnPhase.click();
      const backToTimeMode = (window._fpPhaseModeActive === false);
      const afterFilteredTimeUrl = fpCanvas.toDataURL();
      const timeSeriesChangedOnFilter = (afterFilteredTimeUrl !== beforeUrl);

      // Click Pro Help button -> verify #lcProHelpPanel opens with guide text
      document.getElementById("btnOpenLcHelpModal").click();
      const helpModal = document.getElementById("lcLabHelpModal");
      const helpBody = document.getElementById("lcLabHelpModalBody");
      const helpVisible = Boolean(helpModal && helpModal.classList.contains("open") && helpBody && helpBody.textContent.length > 100);
      fpModal.classList.remove("open");

      // 4. Verify all 4 scientific triggers
      const Lab = window.AstroLabLightCurveLab;
      const resPuls = Lab.analyze(pulsPts);
      const ebPts = [];
      for (let i = 0; i < 60; i++) {
        const dist = Math.abs(i - 30);
        ebPts.push({ jd: jd0 + i * 0.004, mag: 10.0 + (dist < 6 ? 1.2 * (1 - dist / 6) : 0), merr: 0.015, band: "V", source: "AAVSO_AID_DELIM" });
      }
      const resEb = Lab.analyze(ebPts);
      const novaPts = [];
      for (let i = 0; i < 40; i++) {
        novaPts.push({ jd: jd0 + i * 0.5, mag: (i >= 34) ? (11.2 + (i - 34) * 0.15) : (14.0 + ((i % 3) - 1) * 0.04), merr: 0.03, band: "V", source: "AAVSO_AID_DELIM" });
      }
      const resNova = Lab.analyze(novaPts);
      const epPts = [];
      for (let i = 0; i < 60; i++) {
        epPts.push({ jd: jd0 + i * 0.003, mag: 11.0 + ((i >= 24 && i <= 34) ? 0.025 : 0) + ((i % 2 === 0) ? 0.001 : -0.001), merr: 0.003, band: "TG", source: "LOCAL" });
      }
      const resEp = Lab.analyze(epPts);

      return JSON.stringify({
        jsErrors,
        fetchBridgeOk: Boolean(fetchBridgeRes && fetchBridgeRes.ok && fetchBridgeRes.hasEnoughData),
        fetchBridgeCount: (fetchBridgeRes && Array.isArray(fetchBridgeRes.points)) ? fetchBridgeRes.points.length : 0,
        disabledNoKey,
        enabledWithKey,
        disabledAfterClear,
        cntTxt,
        domCards,
        panelVisible,
        panelHasPeriod,
        phaseActiveAfterClick,
        phaseLabelChanged: phaseLabelBefore !== phaseLabelAfter,
        canvasChangedOnPhase,
        backToTimeMode,
        timeSeriesChangedOnFilter,
        helpVisible,
        pulsPeriod: resPuls.ls.bestPeriodDays,
        pulsCodes: resPuls.triggers.map(t => t.code),
        ebCodes: resEb.triggers.map(t => t.code),
        novaCodes: resNova.triggers.map(t => t.code),
        epCodes: resEp.triggers.map(t => t.code)
      });
    })()
    """
    raw = loc.eval_in_browser(bundled, js, port=9295, await_promise=True, wait_ms=1400)
    res = json.loads(raw)
    print(f"  ZERO JS ERRORS: {res['jsErrors']}")
    print(f"  REAL CLICKS: panelVisible={res['panelVisible']}, panelHasPeriod={res['panelHasPeriod']}, phaseActive={res['phaseActiveAfterClick']}, canvasChanged={res['canvasChangedOnPhase']}, backToTime={res['backToTimeMode']}")
    print(f"  SCIENTIFIC TRIGGERS: Pulsating P={res['pulsPeriod']:.5f}d {res['pulsCodes']}, EB={res['ebCodes']}, Nova={res['novaCodes']}, Transit={res['epCodes']}")

    assert len(res["jsErrors"]) == 0, f"UNCAUGHT JS ERRORS DETECTED: {res['jsErrors']}"
    assert res["fetchBridgeOk"] is True and res["fetchBridgeCount"] == 150, f"fetchAavsoCurveSeriesForStar dropped points: {res}"
    assert res["disabledNoKey"] is True and res["enabledWithKey"] is True and res["disabledAfterClear"] is True
    assert res["domCards"] <= 60 and "(60↓)" in res["cntTxt"]
    nums = [int(x) for x in re.findall(r"\d+", res["cntTxt"])]
    assert nums and nums[0] > 60, f"Radar counter capped at 60: {res['cntTxt']}"

    assert res["panelVisible"] is True and res["panelHasPeriod"] is True, f"Real Analyze button click failed: {res}"
    assert res["phaseActiveAfterClick"] is True and res["phaseLabelChanged"] is True and res["canvasChangedOnPhase"] is True, f"Real Phase Plot button click did not update canvas: {res}"
    assert res["backToTimeMode"] is True and res["timeSeriesChangedOnFilter"] is True, f"Time Series filter did not visually update canvas: {res}"
    assert res["helpVisible"] is True, "Pro Help guide panel did not open"

    assert abs(res["pulsPeriod"] - 0.1205) / 0.1205 < 0.03
    assert "PULSATING" in res["pulsCodes"]
    assert "ECLIPSING_BINARY" in res["ebCodes"]
    assert "OUTBURST_NOVA" in res["novaCodes"]
    assert "EXOPLANET_TRANSIT" in res["epCodes"]
    print("[3/3] ALL v1.4.0 ZERO-ERROR REAL-CLICK E2E & SCIENTIFIC LAB CHECKS PASSED!")


if __name__ == "__main__":
    test_backend_aavso_aid_api_v2_and_delim_tail()
    test_frontend_real_clicks_zero_errors_and_scientific_lab()
