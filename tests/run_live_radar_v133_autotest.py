#!/usr/bin/env python3
"""
Mandatory v1.5.0-alpha Regression Autotest:
  1. Backend Option 1 (Public Live AAVSO Alert Notices -> star extraction + SIMBAD TAP resolution)
  2. Backend Option 2 (Official AAVSO Target Tool API v1.0.0 with HTTP Basic Auth api_key:api_token,
     rate-limit header, 401/429 error handling)
  3. Frontend Settings API Key UI (#settingsAavsoApiKeyInput, #btnSaveAavsoApiKey, #btnClearAavsoApiKey,
     #btnOpenApiKeyGuideModal) + localized #aavsoApiKeyGuideModal (RU & EN)
  4. Dynamic Target Radar catalog merge beyond 246 baseline + dynamic header/filter counters + LIVE badges
  5. v1.5.0-alpha version & Trust Infrastructure consistency (Zenodo Concept DOI, no Portable/SignPath)
"""

import base64
import io
import json
import os
import sys
import urllib.error
from unittest.mock import patch

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(REPO_ROOT, "Source_and_Build", "backend")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.dirname(__file__))

import astrolab_backend_core as core
import run_localization_autotest as loc

Svc = core.AavsoNativeAndStorageService


class _FakeHttpResponse:
    def __init__(self, body_str: str, headers=None):
        self._data = body_str.encode("utf-8")
        self.headers = headers or {}

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_backend_live_campaign_parser_and_simbad():
    print("[1/5] Backend Option 1: Public AAVSO Alert Notices + SIMBAD TAP...")
    stars = Svc._extract_stars_from_notice_title(
        "AAVSO Alert Notice 891: Multi-wavelength campaign on T CrB and V1405 Cas (plus SN 2026abc)"
    )
    assert "T CrB" in stars, f"Expected T CrB in {stars}"
    assert "V1405 Cas" in stars, f"Expected V1405 Cas in {stars}"
    assert "SN 2026abc" in stars, f"Expected SN 2026abc in {stars}"

    assert abs(Svc._parse_ra_dec_to_deg("15:59:30.16", is_ra=True) - 239.875667) < 0.001
    assert abs(Svc._parse_ra_dec_to_deg("+25:55:12.6", is_ra=False) - 25.920167) < 0.001
    assert abs(Svc._parse_ra_dec_to_deg("-12:30:00", is_ra=False) - (-12.5)) < 0.001

    fake_notices_json = json.dumps({
        "results": [
            {
                "number": 891,
                "title": "Urgent outburst campaign on V9999 Cyg and AT 2026xyz",
                "published": "2026-11-20T08:00:00Z",
            }
        ]
    })
    fake_simbad_json = json.dumps({
        "metadata": [{"name": "id"}, {"name": "main_id"}, {"name": "ra"}, {"name": "dec"}, {"name": "otype_txt"}, {"name": "V"}],
        "data": [
            ["V9999 Cyg", "V* V9999 Cyg", 310.1234, 42.5678, "Nova", 11.4],
            ["AT 2026xyz", "AT 2026xyz", 180.5, -15.25, "Transient", 13.2],
        ],
    })

    def _fake_urlopen(req, timeout=7.0, context=None):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if "apps.aavso.org/v2/api/notices" in url:
            return _FakeHttpResponse(fake_notices_json)
        if "sim-tap/sync" in url:
            return _FakeHttpResponse(fake_simbad_json)
        raise AssertionError(f"Unexpected URL: {url}")

    with patch("urllib.request.urlopen", side_effect=_fake_urlopen):
        res = Svc.fetch_live_aavso_campaign_targets(max_stars=10)

    assert res["ok"] is True, f"Expected ok=True, got {res}"
    assert len(res["targets"]) == 2, f"Expected 2 targets, got {res}"
    assert res["targets"][0]["star"] == "V9999 Cyg"
    assert res["targets"][0]["isLiveCampaign"] is True
    assert res["targets"][0]["con"] == "Cyg"
    assert abs(res["targets"][0]["ra"] - 310.1234) < 1e-4
    print("  PASS: Public Alert Notice extraction & SIMBAD TAP resolution")


def test_backend_target_tool_api_v1():
    print("[2/5] Backend Option 2: Official AAVSO Target Tool API v1.0.0...")
    empty_res = Svc.fetch_aavso_target_tool_targets("")
    assert empty_res["ok"] is False and empty_res["errorCode"] == "missing_key"

    captured_headers = {}
    fake_tt_payload = json.dumps({
        "targets": [
            {
                "star_name": "TT LIVE STAR",
                "ra": "20:15:00.0",
                "dec": "+38:00:00",
                "constellation": "Cyg",
                "priority": True,
                "last_data_point": 1700000000,
                "solar_conjunction": False,
                "obs_section": ["CV", "AC"],
                "min_mag": 14.1,
                "max_mag": 10.2,
            },
            {
                "star_name": "TT SECOND STAR",
                "ra": 125.25,
                "dec": 18.75,
                "constellation": "Cnc",
                "priority": False,
                "last_data_point": "2026-11-19T22:10:00Z",
                "solar_conjunction": True,
                "obs_section": "LPV",
            },
        ]
    })

    def _fake_tt_ok(req, timeout=12.0, context=None):
        captured_headers.update(dict(req.header_items()))
        assert "targettool.aavso.org/TargetTool/api/v1/targets?obs_section=all" in req.full_url
        return _FakeHttpResponse(fake_tt_payload, headers={"X-Rate-Limit-Remaining": "998"})

    with patch("urllib.request.urlopen", side_effect=_fake_tt_ok):
        res = Svc.fetch_aavso_target_tool_targets("MY_TEST_KEY_123", "all")

    assert res["ok"] is True, f"Expected ok=True, got {res}"
    assert res["count"] == 2
    assert res["rateLimitRemaining"] == "998"
    expected_auth = "Basic " + base64.b64encode(b"MY_TEST_KEY_123:api_token").decode("ascii")
    assert captured_headers.get("Authorization") == expected_auth, f"Bad auth header: {captured_headers}"
    assert res["targets"][0]["isLiveTargetTool"] is True
    assert res["targets"][0]["isHighPriority"] is True
    assert res["targets"][0]["lastDataPoint"] == "2023-11-14 22:13 UTC" and res["targets"][0]["obsSection"] == "CV, AC"
    assert "S30PLUS" in core.SCOPE_PROFILES and core.SCOPE_PROFILES["S30PLUS"]["fovStr"] == "2.66°×1.50°"
    assert res["targets"][1]["solarConjunction"] is True

    # Test 401 unauthorized handling
    def _fake_401(req, timeout=12.0, context=None):
        raise urllib.error.HTTPError(req.full_url, 401, "Unauthorized", {}, io.BytesIO(b""))

    with patch("urllib.request.urlopen", side_effect=_fake_401):
        r401 = Svc.fetch_aavso_target_tool_targets("BAD_KEY")
    assert r401["ok"] is False and r401["errorCode"] == "invalid_key"

    # Test 429 rate-limit handling
    def _fake_429(req, timeout=12.0, context=None):
        raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", {}, io.BytesIO(b""))

    with patch("urllib.request.urlopen", side_effect=_fake_429):
        r429 = Svc.fetch_aavso_target_tool_targets("VALID_KEY")
    assert r429["ok"] is False and r429["errorCode"] == "rate_limited"
    print("  PASS: Target Tool API Basic Auth, schema mapping, 401 & 429 handling")


def test_frontend_settings_modal_and_dynamic_radar():
    print("[3/5] Frontend Settings API Key UI, Guide Modal & Dynamic Radar merge...")
    js_eval = r"""
    (() => {
      const langSel = document.getElementById("langSelect");
      const setLang = (code) => {
        if (langSel) {
          langSel.value = code;
          langSel.dispatchEvent(new Event("change", { bubbles: true }));
        }
      };

      // Check Settings API Key controls exist
      const inputEl = document.getElementById("settingsAavsoApiKeyInput");
      const saveBtn = document.getElementById("btnSaveAavsoApiKey");
      const clearBtn = document.getElementById("btnClearAavsoApiKey");
      const guideBtn = document.getElementById("btnOpenApiKeyGuideModal");
      const modal = document.getElementById("aavsoApiKeyGuideModal");
      if (!inputEl || !saveBtn || !clearBtn || !guideBtn || !modal) {
        return { ok: false, error: "Missing API key UI elements in DOM" };
      }

      // Open Guide modal in RU and verify content + link
      setLang("ru");
      guideBtn.click();
      const ruOpen = modal.classList.contains("open");
      const ruText = (modal.innerText || "").trim();
      const apiLink = modal.querySelector('a[href="https://targettool.aavso.org/TargetTool/api"]');

      // Switch to EN and verify translation updates
      setLang("en");
      const enText = (modal.innerText || "").trim();
      window.closeAavsoApiKeyGuideModal();
      const closedOk = !modal.classList.contains("open");

      // Test dynamic merge into Target Radar beyond 246 baseline
      const headerEl = document.getElementById("v6RadarHeaderTitle");
      const filterAllEl = document.getElementById("radarFilterAllBtn");
      const listEl = document.getElementById("v6RadarListContainer");
      const beforeHeader = headerEl ? headerEl.textContent : "";

      const mergeRes = window.mergeLiveAavsoTargetsIntoCatalog([
        {
          star: "LIVE TEST ALPHA",
          con: "Cyg",
          ra: 305.1234,
          dec: 40.25,
          type: "CV",
          magRange: "11.0-14.0 mag",
          priority: "🔴 LIVE PRIORITY",
          isLiveTargetTool: true,
          isHighPriority: true,
          lastDataPoint: "2026-11-20T12:00:00Z"
        },
        {
          star: "LIVE TEST BETA",
          con: "Lyr",
          ra: 282.5,
          dec: 33.1,
          type: "Nova",
          magRange: "10.5 V",
          priority: "🔴 LIVE Notice #891",
          isLiveCampaign: true
        }
      ], "target_tool");

      const afterHeader = headerEl ? headerEl.textContent : "";
      const afterAllBtn = filterAllEl ? filterAllEl.textContent : "";
      const hasLiveBadge = Boolean(listEl && listEl.querySelector(".v6-live-badge"));

      // Reset to baseline and verify
      window.resetLiveAavsoTargetsToBaseline();
      const resetHeader = headerEl ? headerEl.textContent : "";
      // v1.5.0-alpha: verify S30PLUS tab & specs
      const s30PlusTab = document.querySelector('.v6-scope-tab[data-scope-tab="S30PLUS"]');
      if (s30PlusTab) s30PlusTab.click();
      const s30PlusSpecs = (document.getElementById("v6ScopeSpecsLine")?.textContent || "");

      return {
        ok: true,
        inputType: inputEl.type,
        ruOpen,
        ruHasKeyWord: ruText.includes("API-ключ") && ruText.includes("targettool.aavso.org"),
        enHasKeyWord: enText.includes("API Key") && enText.includes("targettool.aavso.org"),
        hasApiLink: Boolean(apiLink),
        closedOk,
        beforeHeader,
        mergeRes,
        afterHeader,
        afterAllBtn,
        hasLiveBadge,
        resetHeader,
        hasS30PlusTab: Boolean(s30PlusTab),
        s30PlusSpecs
      };
    })()
    """
    import re as _re
    pwa = os.path.join(REPO_ROOT, "Source_and_Build", "pwa_mobile_and_electron")
    html = open(os.path.join(pwa, "index.html"), encoding="utf-8").read()
    css = open(os.path.join(pwa, "astrolab_styles.css"), encoding="utf-8").read()
    tpl = open(os.path.join(pwa, "astrolab_view_template.js"), encoding="utf-8").read()
    eng = open(os.path.join(pwa, "astrolab_engine_bridge.js"), encoding="utf-8").read()
    bundled = _re.sub(r'<link[^>]+astrolab_styles\.css[^>]*>', lambda m: f'<style>{css}</style>', html)
    bundled = _re.sub(r'<script[^>]+astrolab_view_template\.js[^>]*></script>', lambda m: f'<script>{tpl}</script>', bundled)
    bundled = _re.sub(r'<script[^>]+astrolab_engine_bridge\.js[^>]*></script>', lambda m: f'<script>{eng}</script>', bundled)
    raw = loc.eval_in_browser(bundled, f"JSON.stringify(({js_eval}))", port=9291, await_promise=False, wait_ms=1400)
    res = json.loads(raw) if isinstance(raw, str) else raw
    assert res and res.get("ok"), f"Browser eval failed: {res}"
    assert res["inputType"] == "password", f"API key input must be password-masked: {res}"
    assert res["ruOpen"] is True, "Guide modal failed to open"
    assert res["ruHasKeyWord"] is True, "RU guide modal missing localized instructions"
    assert res["enHasKeyWord"] is True, "EN guide modal missing localized instructions"
    assert res["hasApiLink"] is True, "Guide modal missing targettool.aavso.org/TargetTool/api link"
    assert res["closedOk"] is True, "Guide modal failed to close"
    assert res["mergeRes"]["added"] == 2, f"Expected 2 added stars: {res['mergeRes']}"
    assert res["mergeRes"]["total"] >= 248, f"Expected total >= 248: {res['mergeRes']}"
    assert str(res["mergeRes"]["total"]) in res["afterHeader"], f"Header not updated: {res['afterHeader']}"
    assert str(res["mergeRes"]["total"]) in res["afterAllBtn"], f"Filter All btn not updated: {res['afterAllBtn']}"
    assert res["hasLiveBadge"] is True, "LIVE badge not rendered in Radar cards"
    assert "(246)" in res["resetHeader"], f"Reset did not restore 246 baseline: {res['resetHeader']}"
    assert res["hasS30PlusTab"] is True and "2.66" in res["s30PlusSpecs"], f"S30PLUS UI check failed: {res}"
    print(f"  PASS: UI modal (RU/EN), dynamic merge ({res['beforeHeader']} -> {res['afterHeader']} -> {res['resetHeader']}), LIVE badge")


def test_version_and_policy_consistency():
    print("[4/5] Version 1.5.0-alpha & Trust Infrastructure policy consistency...")
    files_must_have_133 = [
        "README.md",
        "Source_and_Build/desktop_launcher.py",
        "Source_and_Build/backend/astrolab_backend_core.py",
        "Source_and_Build/Seestar_AstroLab_Installer.iss",
        "Source_and_Build/package.json",
        "Source_and_Build/version_info.txt",
        ".github/workflows/build.yml",
        "VERIFY.txt",
    ]
    for rel in files_must_have_133:
        txt = open(os.path.join(REPO_ROOT, rel), "r", encoding="utf-8").read()
        assert "1.5.0-alpha" in txt, f"Version 1.5.0-alpha missing in {rel}"

    readme = open(os.path.join(REPO_ROOT, "README.md"), "r", encoding="utf-8").read()
    assert "10.5281/zenodo.24402803" in readme, "Zenodo Concept DOI missing in README.md"
    assert "signpath" not in readme.lower(), "SignPath mention must not appear in README.md"
    assert "portable.zip" not in readme.lower(), "Portable ZIP download must not appear in README.md"


    # Permanent YAML, JSON, PyInstaller & Inno Setup pre-flight validation
    import py_compile as _pyc
    import yaml as _yaml
    for _yf in (".github/workflows/build.yml", ".github/dependabot.yml"):
        _yp = os.path.join(REPO_ROOT, _yf)
        _parsed_y = _yaml.safe_load(open(_yp, "r", encoding="utf-8"))
        assert isinstance(_parsed_y, dict), f"Invalid YAML in {_yf}"
    _wf_obj = _yaml.safe_load(open(os.path.join(REPO_ROOT, ".github/workflows/build.yml"), "r", encoding="utf-8"))
    assert "regression-tests" in _wf_obj["jobs"] and "build-windows" in _wf_obj["jobs"]
    assert _wf_obj["jobs"]["build-windows"]["needs"] == "regression-tests"
    for _jf in (".zenodo.json", "Source_and_Build/package.json"):
        json.load(open(os.path.join(REPO_ROOT, _jf), "r", encoding="utf-8"))
    for _pyf in ("Source_and_Build/desktop_launcher.py", "Source_and_Build/backend/astrolab_backend_core.py"):
        _pyc.compile(os.path.join(REPO_ROOT, _pyf), doraise=True)
    for _req in (
        "Source_and_Build/Seestar_AstroLab_Installer.iss",
        "Source_and_Build/version_info.txt",
        "Source_and_Build/assets/Seestar_AstroLab.ico",
        "Source_and_Build/assets/installer_header_fullwidth.bmp",
        "Converted_Photometry_Storage/README_STORAGE.txt",
        "Converted_Photometry_Storage/user_converted_photometry_db.json",
        "VERIFY.txt",
    ):
        assert os.path.isfile(os.path.join(REPO_ROOT, _req)), f"Missing required build/installer file: {_req}"

    # Permanent CI-to-Repo test script parity check: every tests/*.py invoked by build.yml MUST exist
    import re as _re_ci
    wf_txt = open(os.path.join(REPO_ROOT, ".github/workflows/build.yml"), "r", encoding="utf-8").read()
    ci_tests = _re_ci.findall(r"python3?\s+(tests/[\w.-]+\.py)", wf_txt)
    assert len(ci_tests) >= 5, f"Expected >=5 CI autotests in build.yml, found {ci_tests}"
    for t_rel in ci_tests:
        assert os.path.isfile(os.path.join(REPO_ROOT, t_rel)), f"CI workflow references missing test file: {t_rel}"
    print(f"  PASS: All core files at v1.5.0-alpha, Zenodo DOI preserved, CI-to-Repo parity OK ({len(ci_tests)} CI tests)")


def main():
    print("=== Seestar AstroLab AAVSO v1.5.0-alpha Live Radar & API Key Autotest ===")
    test_backend_live_campaign_parser_and_simbad()
    test_backend_target_tool_api_v1()
    test_frontend_settings_modal_and_dynamic_radar()
    test_version_and_policy_consistency()
    print("[5/5] ALL v1.5.0-alpha LIVE RADAR & API KEY CHECKS PASSED!")


if __name__ == "__main__":
    main()
