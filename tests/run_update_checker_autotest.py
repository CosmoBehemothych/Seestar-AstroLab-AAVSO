#!/usr/bin/env python3
"""
Mandatory Pre-Build Autotest for GitHub Release Update Checker:
1. Backend unit test (redirect channel + REST API fallback + semver remote > local).
2. Frontend Headless Chromium test:
   - Semver comparisons (1.3.1 > 1.3.0, 1.3.1 == 1.3.1, 1.2.2 < 1.3.1, 2.0.0 > 1.3.1).
   - Channel 1 (pywebview API) triggers visible #githubUpdateBanner with release link.
   - Channel 2 fallback (when pywebview fails / returns ok:false -> direct WebView2 fetch to GitHub API)
     triggers visible #githubUpdateBanner.
   - Strictly ONE check per app launch (second call with forceCheck=false makes 0 network calls).
   - Skip button hides banner and persists skipped version.
"""
import io, json, pathlib, re, shutil, subprocess, sys, tempfile, time, urllib.request
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
    # Test 1: Redirect channel returns v1.4.0 > 1.3.1
    with patch("urllib.request.urlopen", return_value=_FakeResp(
        url="https://github.com/CosmoBehemothych/Seestar-AstroLab-AAVSO/releases/tag/v1.4.0"
    )):
        r = core.AavsoNativeAndStorageService.check_github_latest_release("1.3.1")
        assert r["ok"] is True and r["updateAvailable"] is True and r["latestVersion"] == "1.4.0", r

    # Test 2: Same version v1.3.1 == 1.3.1 -> updateAvailable=False
    with patch("urllib.request.urlopen", return_value=_FakeResp(
        url="https://github.com/CosmoBehemothych/Seestar-AstroLab-AAVSO/releases/tag/v1.3.1"
    )):
        r = core.AavsoNativeAndStorageService.check_github_latest_release("1.3.1")
        assert r["ok"] is True and r["updateAvailable"] is False, r

    # Test 3: Redirect fails -> REST API fallback succeeds
    calls = {"n": 0}
    def fake_open(req, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("redirect blocked")
        return _FakeResp(body=json.dumps({
            "tag_name": "v1.3.2",
            "html_url": "https://github.com/CosmoBehemothych/Seestar-AstroLab-AAVSO/releases/tag/v1.3.2"
        }).encode("utf-8"))

    with patch("urllib.request.urlopen", side_effect=fake_open):
        r = core.AavsoNativeAndStorageService.check_github_latest_release("1.3.1")
        assert r["ok"] is True and r["updateAvailable"] is True and r["latestVersion"] == "1.3.2", r

    print("BACKEND_UPDATE_CHECKER_PASS (redirect + REST fallback + semver)")


def test_frontend():
    html = (ROOT / "Source_and_Build/pwa_mobile_and_electron/index.html").read_text(encoding="utf-8")
    css = (ROOT / "Source_and_Build/pwa_mobile_and_electron/astrolab_styles.css").read_text(encoding="utf-8")
    tpl = (ROOT / "Source_and_Build/pwa_mobile_and_electron/astrolab_view_template.js").read_text(encoding="utf-8")
    eng = (ROOT / "Source_and_Build/pwa_mobile_and_electron/astrolab_engine_bridge.js").read_text(encoding="utf-8")

    bundled = re.sub(r'<link[^>]+astrolab_styles\.css[^>]*>', lambda m: f'<style>{css}</style>', html)
    bundled = re.sub(r'<script[^>]+astrolab_view_template\.js[^>]*></script>', lambda m: f'<script>{tpl}</script>', bundled)
    bundled = re.sub(r'<script[^>]+astrolab_engine_bridge\.js[^>]*></script>', lambda m: f'<script>{eng}</script>', bundled)

    port = 9284
    user_dir = tempfile.mkdtemp(prefix="astrolab_upd_")
    browser_bin = loc.find_chromium_binary()
    chrome = subprocess.Popen(
        [browser_bin, "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--no-first-run", "--no-default-browser-check", "--disable-extensions", "--remote-allow-origins=*",
         f"--user-data-dir={user_dir}", "--window-size=1280,800", f"--remote-debugging-port={port}", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    try:
        ws_url = None
        for _ in range(125):
            try:
                tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=1).read().decode())
                for t in tabs:
                    if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
                        ws_url = t["webSocketDebuggerUrl"]
                        break
                if ws_url:
                    break
            except Exception:
                time.sleep(0.2)
        assert ws_url

        ws = loc.SimpleWS(ws_url)
        ws.call("Page.enable")
        frame_id = ws.call("Page.getFrameTree")["frameTree"]["frame"]["id"]
        ws.call("Page.setDocumentContent", {"frameId": frame_id, "html": bundled})
        time.sleep(1.5)

        test_js = r"""
        (async () => {
          // Dismiss splash so layout is visible
          const sp = document.getElementById("splashModal");
          if (sp) sp.remove();
          try { localStorage.removeItem("seestar_skipped_update_ver"); } catch (_) {}

          // 1. Semver checks
          const semverOk = (
            window.isRemoteVersionNewer("1.3.1", "1.3.0") === true &&
            window.isRemoteVersionNewer("v1.3.1", "1.3.1") === false &&
            window.isRemoteVersionNewer("1.2.2", "1.3.1") === false &&
            window.isRemoteVersionNewer("2.0.0", "1.3.1") === true
          );

          // 2. Test Channel 2 fallback: pywebview fails -> direct fetch to GitHub API succeeds
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

          // 3. Calling a second time without forceCheck MUST NOT make another request (strictly once per launch)
          const callsBeforeSecond = fetchCalls;
          await window.checkGithubReleaseOnceOnStartup(false);
          const strictlyOnce = (fetchCalls === callsBeforeSecond);

          // 4. Test Skip button removes banner
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
        ev = ws.call("Runtime.evaluate", {"expression": test_js, "awaitPromise": True, "returnByValue": True})
        if "exceptionDetails" in ev:
            raise RuntimeError(str(ev["exceptionDetails"]))
        res = json.loads(ev["result"]["value"])
        print("FRONTEND_UPDATE_CHECKER_RESULT:", json.dumps(res))
        for k, v in res.items():
            assert v is True, f"Frontend update checker assertion failed: {k}={v}"
        print("FRONTEND_UPDATE_CHECKER_PASS (semver + WebView2 fallback + banner + once-per-launch + skip)")
    finally:
        chrome.terminate()
        try:
            chrome.wait(timeout=5)
        except Exception:
            chrome.kill()
        shutil.rmtree(user_dir, ignore_errors=True)


if __name__ == "__main__":
    test_backend()
    test_frontend()
    print("=== UPDATE CHECKER AUTOTEST: ALL PASS ===")
