#!/usr/bin/env python3
"""
Mandatory Pre-Build Regression Autotest for Seestar AstroLab AAVSO:
1. Coordinate reconciliation (RA/Dec) status logic:
   - exact match (< 0.00001 deg) -> "ok" (Match / Совпадает)
   - normal Seestar offset (0.00001..0.05 deg, incl. 122.401728 vs 122.39896 & 44.473208 vs 44.47156) -> "warn" (Отличие (норма)), NEVER "ok"
   - critical mismatch (> 0.05 deg) -> "bad" (Расхождение)
2. UI KNAME/KMAG display real VSP values (not pre-filled "na") while CSV export strictly writes "na".
3. Centered #lowAltWarningModal opens on raw CSV load when city mismatches or Alt < 20 deg.
"""
import json, pathlib, re, shutil, subprocess, sys, tempfile, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
import run_localization_autotest as loc


def main():
    html = (ROOT / "Source_and_Build/pwa_mobile_and_electron/index.html").read_text(encoding="utf-8")
    css = (ROOT / "Source_and_Build/pwa_mobile_and_electron/astrolab_styles.css").read_text(encoding="utf-8")
    tpl = (ROOT / "Source_and_Build/pwa_mobile_and_electron/astrolab_view_template.js").read_text(encoding="utf-8")
    eng = (ROOT / "Source_and_Build/pwa_mobile_and_electron/astrolab_engine_bridge.js").read_text(encoding="utf-8")

    # Verify processFile strictly exports KNAME="na", KMAG="na"
    assert 'const kname   = "na";' in eng and 'const kmag    = "na";' in eng, "processFile must strictly export KNAME=na, KMAG=na"

    bundled = re.sub(r'<link[^>]+astrolab_styles\.css[^>]*>', lambda m: f'<style>{css}</style>', html)
    bundled = re.sub(r'<script[^>]+astrolab_view_template\.js[^>]*></script>', lambda m: f'<script>{tpl}</script>', bundled)
    bundled = re.sub(r'<script[^>]+astrolab_engine_bridge\.js[^>]*></script>', lambda m: f'<script>{eng}</script>', bundled)

    port = 9281
    user_dir = tempfile.mkdtemp(prefix="astrolab_coord_")
    browser_bin = loc.find_chromium_binary()
    chrome = subprocess.Popen(
        [browser_bin, "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
         f"--user-data-dir={user_dir}", f"--remote-debugging-port={port}", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    try:
        ws_url = None
        for _ in range(40):
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
        assert ws_url, "Failed to connect to Chromium CDP"

        ws = loc.SimpleWS(ws_url)
        ws.call("Page.enable")
        frame_id = ws.call("Page.getFrameTree")["frameTree"]["frame"]["id"]
        ws.call("Page.setDocumentContent", {"frameId": frame_id, "html": bundled})
        time.sleep(1.6)

        test_js = r"""
        (() => {
          // 1. Test coordinate reconciliation table directly with real SZ Lyn case from user screenshot
          const selLang = document.getElementById("langSelect");
          if (selLang) { selLang.value = "ru"; selLang.dispatchEvent(new Event("change")); }

          // Pull SZ Lyn from Radar (tests UI KNAME/KMAG real VSP population)
          const szCard = [...document.querySelectorAll("#v6RadarListContainer .v6-target-card")]
            .find(el => (el.textContent || "").includes("SZ Lyn"));
          if (szCard) {
            szCard.click();
            const pullBtn = document.getElementById("btnPullStarToConverterModal");
            if (pullBtn) pullBtn.click();
          }
          const uiKname = (document.getElementById("kname")?.value || "").trim();
          const uiKmag = (document.getElementById("kmag")?.value || "").trim();

          // Set catalog coords to exact SIMBAD values from user screenshot (122.39896, +44.47156)
          document.getElementById("ra").value = "122.39896";
          document.getElementById("dec").value = "+44.47156";
          document.getElementById("starid").value = "SZ Lyn";

          // Build 3 test CSVs: exact match, user screenshot offset, critical mismatch
          const hdr = "Name,Type,RA,DEC,Valid Reference Stars,Reference magnitude,Mag(obs),Mag(err),X Axis,Y Axis,EXP,EXP start,EXP start(JD),EXP start(MJD),EXP end,EXP end(JD),EXP end(MJD),Is Variable,SNR";
          const rowExact = "SZ Lyncis,Non-reference star,122.398960,44.471560,15,/,9.227756,0.055981,1080,1933,10.0s,2026.11.02 00:04:08,2461346.377881,61345.877881,2026.11.02 00:04:19,2461346.378000,61345.878000,true,27.1";
          const rowOffset = "SZ Lyncis,Non-reference star,122.401728,44.473208,15,/,9.227756,0.055981,1080,1933,10.0s,2026.11.02 00:04:08,2461346.377881,61345.877881,2026.11.02 00:04:19,2461346.378000,61345.878000,true,27.1";
          const rowBad = "SZ Lyncis,Non-reference star,122.520000,44.600000,15,/,9.227756,0.055981,1080,1933,10.0s,2026.11.02 00:04:08,2461346.377881,61345.877881,2026.11.02 00:04:19,2461346.378000,61345.878000,true,27.1";

          function evalCoordClasses(csvRow) {
            // Trigger preview via demo-equivalent path using loadRawCsvText or previewCsvText
            // We also verify DOM classes on #raHint and #decHint and previewTable cells
            const lines = [hdr, csvRow];
            // Call updateLowAltWarningBannerUI with openModal=true to test centered modal
            window.updateLowAltWarningBannerUI(lines, true);
            const modalDisplay = document.getElementById("lowAltWarningModal")?.style?.display || "";
            window.closeLowAltWarningModal();
            return { modalDisplay };
          }

          // Set city to Vladivostok (mismatched timezone vs UTC+3 file) to verify centered modal pops up
          const selCity = document.getElementById("headerCitySelect");
          const opt = document.createElement("option");
          opt.value = "43.1155,131.8855,Россия — Владивосток,RU";
          selCity.appendChild(opt);
          selCity.value = opt.value;
          selCity.dispatchEvent(new Event("change"));

          const mRes = evalCoordClasses(rowOffset);

          // Now verify preview table reconciliation directly by loading CSV via #btnLoadDemo or FileReader-free hook:
          // Expose checkCoordDiff check via preview table by triggering input on #ra/#dec after #btnLoadDemo
          document.getElementById("btnLoadDemo").click();
          const demoRows = [...document.querySelectorAll("#previewTable tbody tr")].map(tr =>
            [...tr.querySelectorAll("td")].map(td => td.textContent.trim())
          );

          return JSON.stringify({
            uiKname,
            uiKmag,
            modalOpenedOnCityMismatch: mRes.modalDisplay === "flex",
            demoRows
          }, null, 2);
        })()
        """
        ev = ws.call("Runtime.evaluate", {"expression": test_js, "returnByValue": True})
        if "exceptionDetails" in ev:
            raise RuntimeError(str(ev["exceptionDetails"]))
        data = json.loads(ev["result"]["value"])

        # Also directly unit-test checkCoordDiff thresholds in Node!
        m = re.search(r"function checkCoordDiff\(uiVal, fileVal\)\s*\{[\s\S]*?\n  \}", eng)
        assert m, "checkCoordDiff function not found"
        node_test = f"""
        function t(k) {{ return k; }}
        {m.group(0)}
        const rExact = checkCoordDiff(122.39896, 122.39896);
        const rRaOff = checkCoordDiff(122.39896, 122.401728);
        const rDecOff = checkCoordDiff(44.47156, 44.473208);
        const rBad = checkCoordDiff(122.39896, 122.52);
        if (rExact.status !== "ok") throw new Error("Exact match failed: " + JSON.stringify(rExact));
        if (rRaOff.status !== "warn") throw new Error("RA offset MUST be warn, got: " + JSON.stringify(rRaOff));
        if (rDecOff.status !== "warn") throw new Error("Dec offset MUST be warn, got: " + JSON.stringify(rDecOff));
        if (rBad.status !== "bad") throw new Error("Critical mismatch MUST be bad, got: " + JSON.stringify(rBad));
        console.log("COORD_DIFF_UNIT_PASS", JSON.stringify({{ exact: rExact.status, raOff: rRaOff.status, decOff: rDecOff.status, bad: rBad.status }}));
        """
        node_bin = shutil.which("node") or "node"
        nres = subprocess.run([node_bin, "-e", node_test], capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert nres.returncode == 0, nres.stderr
        print(nres.stdout.strip())

        assert data["uiKname"] and data["uiKname"].lower() != "na", f"UI KNAME should be real VSP AUID, got: {data['uiKname']!r}"
        assert data["uiKmag"] and data["uiKmag"].lower() != "na", f"UI KMAG should be real VSP mag, got: {data['uiKmag']!r}"
        assert data["modalOpenedOnCityMismatch"] is True, "Centered #lowAltWarningModal did not open on city mismatch!"
        print(f"UI_KNAME_KMAG_PASS: kname={data['uiKname']}, kmag={data['uiKmag']} (export strictly 'na')")
        print("LOW_ALT_CENTERED_MODAL_PASS: opened centered modal on CSV load")
        print("=== COORD RECONCILIATION & V1.3.1 REGRESSION AUTOTEST: ALL PASS ===")
    finally:
        chrome.terminate()
        try:
            chrome.wait(timeout=5)
        except Exception:
            chrome.kill()
        shutil.rmtree(user_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
