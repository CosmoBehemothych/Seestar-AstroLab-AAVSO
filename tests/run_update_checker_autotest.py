#!/usr/bin/env python3
"""
Mandatory Pre-Build Autotest for GitHub Release Update Checker:
1. Backend unit test (redirect channel + REST API fallback + semver remote > local).
2. Frontend Headless Chromium test (Playwright on CI / local CDP fallback).
"""
import json, pathlib, re, sys
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "Source_and_Build/backend"))
sys.path.insert(0, str(ROOT / "tests"))

import astrolab_backend_core as core
import run_localization_autotest as loc


class _FakeResp:
    def __init__(self, url="", body=b"{}"):
        self._url = url
        self._body = body
    def geturl(self):
        return self._url
    def read(self):
        return self._body
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False


def test_backend():
    with patch("urllib.request.urlopen", return_value=_FakeResp(
        url="https://github.com/CosmoBehemothych/Seestar-AstroLab-AAVSO/releases/tag/v1.5.0"
    )):
        r = core.AavsoNativeAndStorageService.check_github_latest_release("1.3.1")
        assert r["ok"] is True and r["updateAvailable"] is True and r["latestVersion"] == "1.5.0", r

    with patch("urllib.request.urlopen", return_value=_FakeResp(
        url="https://github.com/CosmoBehemothych/Seestar-AstroLab-AAVSO/releases/tag/v1.3.1"
    )):
        r = core.AavsoNativeAndStorageService.check_github_latest_release("1.3.1")
        assert r["ok"] is True and r["updateAvailable"] is False, r

    calls = {"n": 0}
    def fake_open(req, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("redirect blocked")
        return _FakeResp(body=json.dumps({
            "tag_name": "v1.5.0",
            "html_url": "https://github.com/CosmoBehemothych/Seestar-AstroLab-AAVSO/releases/tag/v1.5.0"
        }).encode("utf-8"))

    with patch("urllib.request.urlopen", side_effect=fake_open):
        r = core.AavsoNativeAndStorageService.check_github_latest_release("1.3.1")
        assert r["ok"] is True and r["updateAvailable"] is True and r["latestVersion"] == "1.5.0", r

    print("BACKEND_UPDATE_CHECKER_PASS (redirect + REST fallback + semver)")


def test_frontend():
    html = (ROOT / "Source_and_Build/pwa_mobile_and_electron/index.html").read_text(encoding="utf-8")
    css = (ROOT / "Source_and_Build/pwa_mobile_and_electron/astrolab_styles.css").read_text(encoding="utf-8")
    tpl = (ROOT / "Source_and_Build/pwa_mobile_and_electron/astrolab_view_template.js").read_text(encoding="utf-8")
    eng = (ROOT / "Source_and_Build/pwa_mobile_and_electron/astrolab_engine_bridge.js").read_text(encoding="utf-8")

    bundled = re.sub(r'<link[^>]+astrolab_styles\.css[^>]*>', lambda m: f'<style>{css}</style>', html)
    bundled = re.sub(r'<script[^>]+astrolab_view_template\.js[^>]*></script>', lambda m: f'<script>{tpl}</script>', bundled)
    bundled = re.sub(r'<script[^>]+astrolab_engine_bridge\.js[^>]*></script>', lambda m: f'<script>{eng}</script>', bundled)

    test_js = r"""
    (async () => {
      const sp = document.getElementById("splashModal");
      if (sp) sp.remove();
      try { localStorage.removeItem("seestar_skipped_update_ver"); } catch (_) {}

      const semverOk = (
        window.isRemoteVersionNewer("1.3.1", "1.3.0") === true &&
        window.isRemoteVersionNewer("v1.3.1", "1.3.1") === false &&
        window.isRemoteVersionNewer("1.2.2", "1.3.1") === false &&
        window.isRemoteVersionNewer("2.0.0", "1.3.1") === true
      );

      let fetchCalls = 0;
      window.pywebview = {
        api: {
          backend_check_github_latest_release: async () => ({ ok: false })
        }
      };
      window.fetch = async (url) => {
        fetchCalls++;
        if (String(url).includes("api.github.com")) {
          return {
            ok: true,
            json: async () => ({
              tag_name: "v9.9.9",
              html_url: "https://github.com/CosmoBehemothych/Seestar-AstroLab-AAVSO/releases/tag/v9.9.9"
            })
          };
        }
        return { ok: false };
      };

      window._githubUpdateCheckedThisSession = false;
      await window.checkGithubReleaseOnceOnStartup(false);

      const banner = document.getElementById("githubUpdateBanner");
      const rect = banner ? banner.getBoundingClientRect() : { height: 0 };
      const bannerText = banner ? banner.innerText : "";
      const bannerHref = banner ? (banner.querySelector("a")?.getAttribute("href") || "") : "";

      const callsBeforeSecond = fetchCalls;
      await window.checkGithubReleaseOnceOnStartup(false);
      const strictlyOnce = (fetchCalls === callsBeforeSecond);

      const skipBtn = document.getElementById("btnSkipGithubUpdate");
      if (skipBtn) skipBtn.click();
      const removedAfterSkip = !document.getElementById("githubUpdateBanner");

      return JSON.stringify({
        semverOk,
        bannerVisible: Boolean(banner && rect.height >= 30),
        hasVer: bannerText.includes("9.9.9"),
        hasHref: bannerHref.includes("releases/tag/v9.9.9"),
        strictlyOnce,
        removedAfterSkip
      });
    })()
    """
    raw_val = loc.eval_in_browser(bundled, test_js, port=9284, await_promise=True, wait_ms=1500)
    res = json.loads(raw_val)
    print("FRONTEND_UPDATE_CHECKER_RESULT:", json.dumps(res))
    for k, v in res.items():
        assert v is True, f"Frontend update checker assertion failed: {k}={v}"
    print("FRONTEND_UPDATE_CHECKER_PASS (semver + WebView2 fallback + banner + once-per-launch + skip)")


if __name__ == "__main__":
    test_backend()
    test_frontend()
    print("=== UPDATE CHECKER AUTOTEST: ALL PASS ===")
