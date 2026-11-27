#!/usr/bin/env python3
"""
Mandatory Pre-Build Regression Autotest for v1.5.0 UI Fixes & AAVSO Chart Guide:
1. Sky Clarity & Moon widgets stay strictly inside header toolbar bounds on narrow 860px viewport.
2. #obsFilterDate allows keyboard typing (no readonly), parses DD.MM.YYYY & YYYY-MM-DD, rejects invalid dates.
3. #graphGuideModal opens in 8-slide presentation layout (matching Getting Started) and renders all 8 slides.
4. Version 1.5.0 is consistent across release files, with zero SignPath or Portable build artifacts.
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
import run_localization_autotest as loc


def test_version_and_policy_consistency():
    must_have_132 = [
        "README.md",
        ".github/workflows/build.yml",
        "Source_and_Build/Seestar_AstroLab_Installer.iss",
        "Source_and_Build/version_info.txt",
        "Source_and_Build/package.json",
        "Source_and_Build/desktop_launcher.py",
        "Source_and_Build/pwa_mobile_and_electron/astrolab_engine_bridge.js",
        "VERIFY.txt",
    ]
    for rel in must_have_132:
        txt = (ROOT / rel).read_text(encoding="utf-8")
        assert "1.5.0" in txt, f"Version 1.5.0 missing in {rel}"

    for doc in ["README.md", "SECURITY.md", "VERIFY.txt"]:
        txt = (ROOT / doc).read_text(encoding="utf-8")
        assert "signpath" not in txt.lower(), f"Forbidden SignPath mention in {doc}"

    build_yml = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
    assert "Seestar_AstroLab_Portable" not in build_yml, "Portable build must not exist in build.yml"
    assert "regression-tests:" in build_yml and "needs: regression-tests" in build_yml, "CI regression gate missing"
    print("VERSION_AND_POLICY_CONSISTENCY_PASS (v1.5.0, no Portable, no SignPath, CI gate intact)")


def test_ui_and_guides_in_browser():
    html = (ROOT / "Source_and_Build/pwa_mobile_and_electron/index.html").read_text(encoding="utf-8")
    css = (ROOT / "Source_and_Build/pwa_mobile_and_electron/astrolab_styles.css").read_text(encoding="utf-8")
    tpl = (ROOT / "Source_and_Build/pwa_mobile_and_electron/astrolab_view_template.js").read_text(encoding="utf-8")
    eng = (ROOT / "Source_and_Build/pwa_mobile_and_electron/astrolab_engine_bridge.js").read_text(encoding="utf-8")

    bundled = re.sub(r'<link[^>]+astrolab_styles\.css[^>]*>', lambda m: f'<style>{css}</style>', html)
    bundled = re.sub(r'<script[^>]+astrolab_view_template\.js[^>]*></script>', lambda m: f'<script>{tpl}</script>', bundled)
    bundled = re.sub(r'<script[^>]+astrolab_engine_bridge\.js[^>]*></script>', lambda m: f'<script>{eng}</script>', bundled)

    test_js = r"""
    (() => {
      const sp = document.getElementById("splashModal");
      if (sp) sp.remove();

      // 1. Simulate narrow 860px viewport container on #appShell to verify Sky & Moon cards never overflow
      const shell = document.getElementById("appShell");
      if (shell) { shell.style.width = "820px"; shell.style.maxWidth = "820px"; }
      const toolbar = document.getElementById("uiThemeToggleBar");
      const skyCard = document.getElementById("btnHeaderSkyClarity");
      const moonCard = document.getElementById("headerMoonPhaseChip");
      const tbRect = toolbar.getBoundingClientRect();
      const skyRect = skyCard.getBoundingClientRect();
      const moonRect = moonCard.getBoundingClientRect();
      const widgetsContained = (
        skyRect.right <= tbRect.right + 1.5 &&
        moonRect.right <= tbRect.right + 1.5 &&
        skyRect.left >= tbRect.left - 1.5 &&
        moonRect.left >= tbRect.left - 1.5
      );

      // 2. Test keyboard date input in My Observations (#obsFilterDate)
      const dateInput = document.getElementById("obsFilterDate");
      const dateEditable = Boolean(dateInput && !dateInput.hasAttribute("readonly") && !dateInput.readOnly);
      const parseOk = (
        window.parseObsUserDateToIso("16.11.2026") === "2026-11-16" &&
        window.parseObsUserDateToIso("2026-11-02") === "2026-11-02" &&
        window.parseObsUserDateToIso("31.02.2026") === null &&
        window.parseObsUserDateToIso("") === ""
      );
      dateInput.value = "16.11.2026";
      dateInput.dispatchEvent(new Event("input", { bubbles: true }));
      dateInput.dispatchEvent(new Event("change", { bubbles: true }));
      const dateValuePreserved = (dateInput.value === "16.11.2026");

      // 3. Test 8-slide "How to Read Light Curves" modal (#graphGuideModal)
      const selLang = document.getElementById("langSelect");
      if (selLang) { selLang.value = "ru"; selLang.dispatchEvent(new Event("change")); }
      window.openGraphGuideModal(0);
      const modalOpen = document.getElementById("graphGuideModal")?.classList.contains("open");
      let slidesOk = 0;
      for (let i = 0; i < 8; i++) {
        window.renderGraphGuideSlide(i);
        const counter = document.getElementById("graphGuideCounterBadge")?.textContent?.trim();
        const stageText = document.getElementById("graphGuideStageContent")?.innerText?.trim() || "";
        if (counter === `${i + 1} / 8` && stageText.length > 100) slidesOk++;
      }
      window.closeGraphGuideModal();

      return JSON.stringify({
        widgetsContained,
        tbRight: Math.round(tbRect.right),
        skyRight: Math.round(skyRect.right),
        moonRight: Math.round(moonRect.right),
        dateEditable,
        parseOk,
        dateValuePreserved,
        modalOpen,
        slidesOk
      });
    })()
    """
    raw = loc.eval_in_browser(bundled, test_js, port=9289, await_promise=False, wait_ms=1400)
    res = json.loads(raw)
    print("UI_AND_GUIDES_V132_RESULT:", json.dumps(res))
    assert res["widgetsContained"] is True, f"Sky/Moon widgets overflowed toolbar: {res}"
    assert res["dateEditable"] is True, "#obsFilterDate must NOT be readonly"
    assert res["parseOk"] is True, "parseObsUserDateToIso failed"
    assert res["dateValuePreserved"] is True, "#obsFilterDate did not preserve keyboard value"
    assert res["modalOpen"] is True and res["slidesOk"] == 8, f"8-slide Graph Guide failed: {res}"
    test_zero_overflow_all_guides_and_svgs()
    print("=== V1.5.0 UI, KEYBOARD DATE & 8-SLIDE GRAPH GUIDE AUTOTEST: ALL PASS ===")




def test_zero_overflow_all_guides_and_svgs():
    html = (ROOT / "Source_and_Build/pwa_mobile_and_electron/index.html").read_text(encoding="utf-8")
    css = (ROOT / "Source_and_Build/pwa_mobile_and_electron/astrolab_styles.css").read_text(encoding="utf-8")
    tpl = (ROOT / "Source_and_Build/pwa_mobile_and_electron/astrolab_view_template.js").read_text(encoding="utf-8")
    eng = (ROOT / "Source_and_Build/pwa_mobile_and_electron/astrolab_engine_bridge.js").read_text(encoding="utf-8")

    bundled = re.sub(r'<link[^>]+astrolab_styles\.css[^>]*>', lambda m: f'<style>{css}</style>', html)
    bundled = re.sub(r'<script[^>]+astrolab_view_template\.js[^>]*></script>', lambda m: f'<script>{tpl}</script>', bundled)
    bundled = re.sub(r'<script[^>]+astrolab_engine_bridge\.js[^>]*></script>', lambda m: f'<script>{eng}</script>', bundled)

    js = r"""
    (() => {
      const sp = document.getElementById("splashModal");
      if (sp) sp.remove();
      const issues = [];
      let slidesChecked = 0;
      function checkBox(root, scopeName, lang) {
        const rr = root.getBoundingClientRect();
        if (rr.width < 50) return;
        root.querySelectorAll("div, p, span, code, pre, td, th, h3, h4, button, li").forEach(el => {
          const r = el.getBoundingClientRect();
          if (r.width < 10 || r.height < 6) return;
          const cs = getComputedStyle(el);
          if (cs.overflowX === "auto" || cs.overflowX === "scroll") return;
          if (el.scrollWidth > el.clientWidth + 4 && el.clientWidth > 20) {
            issues.push({ kind: "SCROLL_OV", scope: scopeName, lang, text: (el.textContent || "").trim().slice(0, 60) });
          }
          if (r.right > rr.right + 4) {
            issues.push({ kind: "RIGHT_OV", scope: scopeName, lang, text: (el.textContent || "").trim().slice(0, 60) });
          }
        });
      }
      for (const lang of ["ru", "en"]) {
        const sel = document.getElementById("langSelect");
        if (sel) { sel.value = lang; sel.dispatchEvent(new Event("change")); }
        const nBeg = document.querySelectorAll("#beginnerSlideTabsBar .beginner-slide-tab").length;
        for (let i = 0; i < nBeg; i++) {
          window.openBeginnerGuideModal(i);
          slidesChecked++;
          const st = document.getElementById("beginnerSlideStageContent");
          if (st) checkBox(st, "beginner_s" + (i + 1), lang);
        }
        window.closeBeginnerGuideModal();
        const nGr = document.querySelectorAll("#graphGuideTabsBar .beginner-slide-tab").length;
        for (let i = 0; i < nGr; i++) {
          window.openGraphGuideModal(i);
          slidesChecked++;
          const st = document.getElementById("graphGuideStageContent");
          if (st) checkBox(st, "graph_s" + (i + 1), lang);
        }
        window.closeGraphGuideModal();
      }
      return { slidesChecked, issuesCount: issues.length, sample: issues.slice(0, 10) };
    })();
    """
    res = loc.eval_in_browser(bundled, js)
    assert res["slidesChecked"] >= 58, f"Expected >=58 guide slide checks, got {res}"
    assert res["issuesCount"] == 0, f"Guide slide overflow detected: {res['sample']}"

    # Also verify all inline <svg> blocks in astrolab_engine_bridge.js have 0 <text> overflows
    inline_svgs = re.findall(r"<svg\b[^>]*>.*?</svg>", eng, flags=re.DOTALL)
    blocks = [f'<div class="svg-chk" data-i="{i}">{s.replace(chr(92)+"n", chr(10)).replace(chr(92)+chr(34), chr(34))}</div>' for i, s in enumerate(inline_svgs)]
    harness = "<!doctype html><html><head><meta charset='utf-8'><style>body{margin:0;font-family:sans-serif;}.svg-chk{width:700px;}</style></head><body>" + "\n".join(blocks) + "</body></html>"
    svg_js = r"""
    (() => {
      const ovs = [];
      let checked = 0;
      document.querySelectorAll(".svg-chk svg").forEach((svg, idx) => {
        const vb = svg.getAttribute("viewBox");
        if (!vb) return;
        const p = vb.trim().split(/[\s,]+/).map(Number);
        if (p.length !== 4) return;
        const [vx, vy, vw, vh] = p;
        const rects = Array.from(svg.querySelectorAll("rect")).map(r => ({
          x: parseFloat(r.getAttribute("x") || 0), y: parseFloat(r.getAttribute("y") || 0),
          w: parseFloat(r.getAttribute("width") || 0), h: parseFloat(r.getAttribute("height") || 0)
        })).filter(r => r.w > 25 && r.h > 12);
        svg.querySelectorAll("text").forEach(t => {
          let bb; try { bb = t.getBBox(); } catch (_) { return; }
          if (!bb || bb.width <= 0) return;
          checked++;
          const x1 = bb.x, x2 = bb.x + bb.width, yc = bb.y + bb.height / 2, xc = bb.x + bb.width / 2;
          if (x1 < vx + 1 || x2 > vx + vw - 1) { ovs.push({ idx, kind: "VB", text: (t.textContent || "").trim() }); return; }
          let best = null;
          for (const r of rects) {
            if (yc >= r.y && yc <= r.y + r.h && xc >= r.x && xc <= r.x + r.w) {
              if (!best || r.w * r.h < best.w * best.h) best = r;
            }
          }
          if (best && (x1 < best.x + 1 || x2 > best.x + best.w - 1) && Math.max(best.x - x1, x2 - (best.x + best.w)) >= 2) {
            ovs.push({ idx, kind: "RECT", text: (t.textContent || "").trim() });
          }
        });
      });
      return { checked, ovCount: ovs.length, sample: ovs.slice(0, 10) };
    })();
    """
    sres = loc.eval_in_browser(harness, svg_js)
    assert sres["ovCount"] == 0, f"Inline SVG text overflow detected: {sres['sample']}"
    print(f"ZERO_OVERFLOW_GATE_PASS (slides={res['slidesChecked']}, inlineSvgTexts={sres['checked']}, overflows=0)")


if __name__ == "__main__":
    test_version_and_policy_consistency()
    test_ui_and_guides_in_browser()
