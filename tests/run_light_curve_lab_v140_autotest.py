#!/usr/bin/env python3
"""
Mandatory v1.4.0 Autotest:
  1. Backend AAVSO AID Light Curve Upgrade:
     - Mocked 3,500-row api.delim CSV -> asserts 3,000 NEWEST points (tail) returned, not oldest 400
     - Mocked 2-row api.delim CSV -> asserts 1..4 real points are preserved (hasAavsoData=True)
  2. Frontend Radar Exact Filtered Counter & Target Tool API Filter Button:
     - Exact filtered match count displayed (> 60) even with 60-card DOM windowing
     - #btnRadarFetchTargetToolApi disabled when no API key, enabled when API key saved
  3. Frontend Scientific Light Curve Analysis Lab (Lomb-Scargle, BLS, Phase Plot, Auto-Triggers):
     - Pulsating Variable (P=0.1205d, Δm=0.80 mag) -> recovers period within 3% & fires PULSATING
     - Eclipsing Binary (EA, 1.2 mag dip from plateau) -> fires ECLIPSING_BINARY
     - Nova / Dwarf Nova Outburst (2.8 mag bright jump) -> fires OUTBURST_NOVA
     - Exoplanet Transit (0.025 mag box dip) -> fires EXOPLANET_TRANSIT
     - Phase Plot rendering & #lcAnalysisResultPanel UI check
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


def test_backend_aavso_aid_newest_tail_and_small_counts():
    print("[1/3] Backend AAVSO AID: 3,500-row newest-tail retention & 2-point preservation...")
    # Build 3,500 chronological rows (JD 2461000.0001 .. 2461000.3500)
    rows = ["JD,Magnitude,Uncertainty,Band,Observer Code"]
    for i in range(1, 3501):
        rows.append(f"{2461000.0 + i * 0.0001:.6f},9.123,0.015,TG,OBS1")
    big_csv = "\n".join(rows)

    with patch("urllib.request.urlopen", return_value=_FakeResp(big_csv)):
        res = Svc.fetch_aavso_light_curve("SZ Lyn", days_back=180, max_points=3000)

    assert res["ok"] is True and res["hasAavsoData"] is True
    assert res["totalAavsoPoints"] == 3000, f"Expected 3000 points, got {res['totalAavsoPoints']}"
    # Verify NEWEST tail was kept (first kept point should be row 501, last should be row 3500)
    first_jd = res["otherObserversPoints"][0]["jd"]
    last_jd = res["otherObserversPoints"][-1]["jd"]
    assert abs(last_jd - 2461000.3500) < 1e-4, f"Did not keep newest point! last_jd={last_jd}"
    assert abs(first_jd - 2461000.0501) < 1e-4, f"Did not slice newest tail! first_jd={first_jd}"

    # Small count (2 observations) must be preserved, not wiped to 0
    small_csv = "JD,Magnitude,Uncertainty,Band,Observer Code\n2461300.1,11.2,0.02,V,ABC\n2461301.2,11.4,0.02,V,DEF\n"
    with patch("urllib.request.urlopen", return_value=_FakeResp(small_csv)):
        res2 = Svc.fetch_aavso_light_curve("V999 Cas", days_back=180)
    assert res2["hasAavsoData"] is True and res2["totalAavsoPoints"] == 2
    print(f"  PASS: Kept newest 3,000/{3500} pts (JD {first_jd:.4f}..{last_jd:.4f}) & preserved 2-pt sparse curve")


def test_frontend_radar_counter_api_btn_and_scientific_lab():
    print("[2/3] Frontend: Radar exact counter, API filter button & Scientific Light Curve Analysis Lab...")
    pwa = os.path.join(REPO_ROOT, "Source_and_Build", "pwa_mobile_and_electron")
    html = open(os.path.join(pwa, "index.html"), encoding="utf-8").read()
    css = open(os.path.join(pwa, "astrolab_styles.css"), encoding="utf-8").read()
    tpl = open(os.path.join(pwa, "astrolab_view_template.js"), encoding="utf-8").read()
    eng = open(os.path.join(pwa, "astrolab_engine_bridge.js"), encoding="utf-8").read()
    bundled = re.sub(r'<link[^>]+astrolab_styles\.css[^>]*>', lambda m: f'<style>{css}</style>', html)
    bundled = re.sub(r'<script[^>]+astrolab_view_template\.js[^>]*></script>', lambda m: f'<script>{tpl}</script>', bundled)
    bundled = re.sub(r'<script[^>]+astrolab_engine_bridge\.js[^>]*></script>', lambda m: f'<script>{eng}</script>', bundled)

    js = r"""
    (() => {
      const sp = document.getElementById("splashModal");
      if (sp) sp.remove();

      // 1. Check Radar API Filter Button disabled when no key, enabled when key set
      window._syncRadarApiFetchButton(false);
      const apiBtn = document.getElementById("btnRadarFetchTargetToolApi");
      const disabledNoKey = Boolean(apiBtn && apiBtn.disabled === true);

      window._syncRadarApiFetchButton(true);
      const enabledWithKey = Boolean(apiBtn && apiBtn.disabled === false);

      window._syncRadarApiFetchButton(false);
      const disabledAfterClear = Boolean(apiBtn && apiBtn.disabled === true);

      // 2. Check Radar exact filtered counter (> 60) even with 60-card DOM windowing
      const extra = [];
      for (let i = 1; i <= 400; i++) {
        extra.push({
          star: `V7${String(i).padStart(3, "0")} Cyg`,
          con: "Cyg",
          ra: 300 + (i % 20) * 0.1,
          dec: 45 + (i % 15) * 0.1,
          type: "CV",
          magRange: "11-13 mag",
          isLiveTargetTool: true
        });
      }
      window.mergeLiveAavsoTargetsIntoCatalog(extra, "target_tool");
      window.renderV6RadarDock();
      const cntTxt = (document.getElementById("v6RadarCountText")?.textContent || "").trim();
      const domCards = document.querySelectorAll("#v6RadarListContainer .v6-target-card").length;
      window.resetLiveAavsoTargetsToBaseline();

      // 3. Scientific Light Curve Analysis Lab Tests
      const Lab = window.AstroLabLightCurveLab;
      const jd0 = 2461360.0;

      // 3a. Synthetic Pulsating Variable (P = 0.1205 d, Δm = 0.80 mag, 90 pts over 0.65 d)
      const pulsPts = [];
      const trueP = 0.1205;
      for (let i = 0; i < 90; i++) {
        const t = jd0 + i * 0.0072;
        const mag = 9.0 + 0.40 * Math.sin(2 * Math.PI * (t - jd0) / trueP);
        pulsPts.push({ jd: t, mag, merr: 0.012, band: "TG", source: "LOCAL" });
      }
      const resPuls = Lab.analyze(pulsPts);

      // 3b. Synthetic Eclipsing Binary (EA: 10.0m plateau + sharp 1.2 mag dip)
      const ebPts = [];
      for (let i = 0; i < 60; i++) {
        const t = jd0 + i * 0.004;
        const dist = Math.abs(i - 30);
        const dip = dist < 6 ? 1.2 * (1 - dist / 6) : 0;
        ebPts.push({ jd: t, mag: 10.0 + dip, merr: 0.015, band: "V", source: "AAVSO_AID_DELIM" });
      }
      const resEb = Lab.analyze(ebPts);

      // 3c. Synthetic Nova / Dwarf Nova Outburst (14.0m quiescence + 2.8 mag bright jump to 11.2m)
      const novaPts = [];
      for (let i = 0; i < 40; i++) {
        const t = jd0 + i * 0.5;
        const mag = (i >= 34) ? (11.2 + (i - 34) * 0.15) : (14.0 + ((i % 3) - 1) * 0.04);
        novaPts.push({ jd: t, mag, merr: 0.03, band: "V", source: "AAVSO_AID_DELIM" });
      }
      const resNova = Lab.analyze(novaPts);

      // 3d. Synthetic Exoplanet Transit (11.0m flat baseline + 0.025 mag box dip)
      const epPts = [];
      for (let i = 0; i < 60; i++) {
        const t = jd0 + i * 0.003;
        const inTransit = (i >= 24 && i <= 34);
        const mag = 11.0 + (inTransit ? 0.025 : 0) + ((i % 2 === 0) ? 0.001 : -0.001);
        epPts.push({ jd: t, mag, merr: 0.003, band: "TG", source: "LOCAL" });
      }
      const resEp = Lab.analyze(epPts);

      // 3e. UI Panel + Phase Plot rendering check
      const fpModal = document.getElementById("fullPageLightCurveModal");
      if (fpModal) fpModal.classList.add("open");
      window.runFullPageLightCurveAnalysis(pulsPts);
      const panelEl = document.getElementById("lcAnalysisResultPanel");
      const panelVisible = Boolean(panelEl && panelEl.style.display !== "none" && panelEl.textContent.length > 50);
      const fpCanvas = document.getElementById("fullPageLightCurveCanvas");
      Lab.renderPhasePlotCanvas(fpCanvas, pulsPts, resPuls.ls.bestPeriodDays || trueP, jd0, 800, 420);
      const phaseDrawn = Boolean(fpCanvas && fpCanvas.width >= 800);
      if (fpModal) fpModal.classList.remove("open");

      return JSON.stringify({
        disabledNoKey,
        enabledWithKey,
        disabledAfterClear,
        cntTxt,
        domCards,
        pulsPeriod: resPuls.ls.bestPeriodDays,
        pulsCodes: resPuls.triggers.map(t => t.code),
        ebCodes: resEb.triggers.map(t => t.code),
        novaCodes: resNova.triggers.map(t => t.code),
        epCodes: resEp.triggers.map(t => t.code),
        panelVisible,
        phaseDrawn
      });
    })()
    """
    raw = loc.eval_in_browser(bundled, js, port=9295, await_promise=False, wait_ms=1400)
    res = json.loads(raw)
    print(f"  API BTN: noKeyDisabled={res['disabledNoKey']}, withKeyEnabled={res['enabledWithKey']}, clearedDisabled={res['disabledAfterClear']}")
    print(f"  RADAR COUNT: '{res['cntTxt']}' (DOM cards={res['domCards']})")
    print(
        f"  SCIENTIFIC TRIGGERS: Pulsating P={res['pulsPeriod']:.5f}d {res['pulsCodes']}, "
        f"EB={res['ebCodes']}, Nova={res['novaCodes']}, Transit={res['epCodes']}"
    )

    assert res["disabledNoKey"] is True and res["enabledWithKey"] is True and res["disabledAfterClear"] is True
    assert res["domCards"] <= 60 and "(60↓)" in res["cntTxt"], f"Radar counter/window check failed: {res}"
    # Verify exact filtered count in text is > 60 (not capped at 60!)
    nums = [int(x) for x in re.findall(r"\d+", res["cntTxt"])]
    assert nums and nums[0] > 60, f"Radar counter still capped at 60: {res['cntTxt']}"

    assert abs(res["pulsPeriod"] - 0.1205) / 0.1205 < 0.03, f"Lomb-Scargle period off: {res['pulsPeriod']}"
    assert "PULSATING" in res["pulsCodes"], f"PULSATING trigger missed: {res['pulsCodes']}"
    assert "ECLIPSING_BINARY" in res["ebCodes"], f"ECLIPSING_BINARY trigger missed: {res['ebCodes']}"
    assert "OUTBURST_NOVA" in res["novaCodes"], f"OUTBURST_NOVA trigger missed: {res['novaCodes']}"
    assert "EXOPLANET_TRANSIT" in res["epCodes"], f"EXOPLANET_TRANSIT trigger missed: {res['epCodes']}"
    assert res["panelVisible"] is True and res["phaseDrawn"] is True
    print("[3/3] ALL v1.4.0 SCIENTIFIC LIGHT CURVE LAB, AAVSO AID & RADAR CHECKS PASSED!")


if __name__ == "__main__":
    test_backend_aavso_aid_newest_tail_and_small_counts()
    test_frontend_radar_counter_api_btn_and_scientific_lab()
