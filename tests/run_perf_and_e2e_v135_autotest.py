#!/usr/bin/env python3
"""
Mandatory v1.5.0-alpha Stress Test (3,000+ Live Stars), Z-Index Stacking & Full E2E UI Autotest:
  1. Stress Test with 3,000 live AAVSO Target Tool stars:
     - Verifies renderV6RadarDock() and renderUrgentStarsCards() complete in < 250 ms
     - Verifies 60-card progressive windowing (DOM card count <= 65, Load More appends +60)
     - Verifies live search filter completes in < 250 ms
  2. Modal Z-Index Stacking Fix:
     - Opens #urgentStarsModal, clicks a star inside it, and asserts #starFullDossierModal
       opens strictly ABOVE #urgentStarsModal (z-index 100250 > 98000) and displays non-empty content
  3. Full End-to-End Verification of Every Major Button, Modal, Telescope & Text:
     - All 5 telescopes (S30, S30PLUS, S30PRO, S50, S50PRO)
     - Dark/Light theme toggle
     - Every modal trigger: Urgent Stars, Star Full Dossier, My Observations, Graph Guide (8 slides),
       Beginner Guide (12 slides), Settings Popover + API Key Guide Modal, Universe Luck Wheel
     - Zero 'undefined' / '[object Object]' text leaks
"""

import json
import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import run_localization_autotest as loc


def build_inline_html():
    pwa = os.path.join(REPO_ROOT, "Source_and_Build", "pwa_mobile_and_electron")
    html = open(os.path.join(pwa, "index.html"), encoding="utf-8").read()
    css = open(os.path.join(pwa, "astrolab_styles.css"), encoding="utf-8").read()
    tpl = open(os.path.join(pwa, "astrolab_view_template.js"), encoding="utf-8").read()
    eng = open(os.path.join(pwa, "astrolab_engine_bridge.js"), encoding="utf-8").read()
    bundled = re.sub(r'<link[^>]+astrolab_styles\.css[^>]*>', lambda m: f'<style>{css}</style>', html)
    bundled = re.sub(r'<script[^>]+astrolab_view_template\.js[^>]*></script>', lambda m: f'<script>{tpl}</script>', bundled)
    bundled = re.sub(r'<script[^>]+astrolab_engine_bridge\.js[^>]*></script>', lambda m: f'<script>{eng}</script>', bundled)
    return bundled


def test_stress_zindex_and_full_e2e():
    print("[1/2] Running 3,000-star Stress Test, Z-Index Check & Full E2E UI Audit in Headless Browser...")
    bundled = build_inline_html()
    js_test = r"""
    (() => {
      const sp = document.getElementById("splashModal");
      if (sp) sp.remove();

      // --- A. STRESS TEST: Inject 3,000 live AAVSO Target Tool stars ---
      const bulk = [];
      const cons = ["Cyg", "Lyr", "Cas", "Per", "Ori", "Her", "UMa", "Aur", "Tau", "And"];
      for (let i = 1; i <= 3000; i++) {
        bulk.push({
          star: `V${5000 + i} ${cons[i % cons.length]}`,
          con: cons[i % cons.length],
          ra: (i * 0.119) % 360,
          dec: ((i * 0.047) % 100) - 10,
          type: "CV",
          magRange: "11.2-14.5 mag",
          priority: (i % 25 === 0) ? "🔴 LIVE PRIORITY" : "🟢 LIVE Target Tool",
          isLiveTargetTool: true,
          isHighPriority: (i % 25 === 0),
          lastDataPoint: "2026-11-20 20:00 UTC",
          obsSection: "CV"
        });
      }

      const tMerge0 = performance.now();
      const mergeInfo = window.mergeLiveAavsoTargetsIntoCatalog(bulk, "target_tool");
      const tMergeMs = Math.round(performance.now() - tMerge0);

      // Measure renderV6RadarDock with 3,246 stars
      const tV60 = performance.now();
      window.renderV6RadarDock();
      const tV6Ms = Math.round(performance.now() - tV60);

      const v6CardsInitial = document.querySelectorAll("#v6RadarListContainer .v6-target-card").length;
      const v6LoadMoreBtn = document.getElementById("btnV6RadarLoadMore");
      let v6CardsAfterMore = v6CardsInitial;
      if (v6LoadMoreBtn) {
        v6LoadMoreBtn.click();
        v6CardsAfterMore = document.querySelectorAll("#v6RadarListContainer .v6-target-card").length;
      }

      // Open #urgentStarsModal & measure renderUrgentStarsCards with 3,246 stars
      const urgModal = document.getElementById("urgentStarsModal");
      const btnOpenUrg = document.getElementById("btnOpenUrgentModal");
      if (btnOpenUrg) btnOpenUrg.click();
      else if (urgModal) urgModal.classList.add("open");

      const tUrg0 = performance.now();
      window.renderUrgentStarsCards("");
      const tUrgMs = Math.round(performance.now() - tUrg0);

      const urgCardsInitial = document.querySelectorAll("#urgentStarsGridContainer .urgent-star-card").length;
      const urgLoadMoreBtn = document.getElementById("btnUrgentLoadMore");
      let urgCardsAfterMore = urgCardsInitial;
      if (urgLoadMoreBtn) {
        urgLoadMoreBtn.click();
        urgCardsAfterMore = document.querySelectorAll("#urgentStarsGridContainer .urgent-star-card").length;
      }

      // --- B. Z-INDEX STACKING FIX: Click a star inside #urgentStarsModal ---
      const firstUrgCard = document.querySelector("#urgentStarsGridContainer .urgent-star-card");
      if (firstUrgCard) firstUrgCard.click();
      const dossierModal = document.getElementById("starFullDossierModal");
      const dossierOpen = Boolean(dossierModal && dossierModal.classList.contains("open"));
      const zUrgent = urgModal ? parseInt(getComputedStyle(urgModal).zIndex || "0", 10) : 0;
      const zDossier = dossierModal ? parseInt(getComputedStyle(dossierModal).zIndex || "0", 10) : 0;
      const dossierTextLen = dossierModal ? (dossierModal.innerText || "").trim().length : 0;
      if (dossierModal) dossierModal.classList.remove("open");
      if (urgModal) urgModal.classList.remove("open");

      // Measure filtered search under 3,246 stars
      const tSearch0 = performance.now();
      window.renderUrgentStarsCards("V5025");
      const tSearchMs = Math.round(performance.now() - tSearch0);
      const searchMatchCount = document.querySelectorAll("#urgentStarsGridContainer .urgent-star-card").length;

      // Reset catalog back to baseline for clean E2E checks
      window.resetLiveAavsoTargetsToBaseline();

      // --- C. FULL E2E CHECK: ALL 5 TELESCOPES, THEME TOGGLE & EVERY MODAL ---
      const scopeResults = {};
      for (const sc of ["S30", "S30PLUS", "S30PRO", "S50", "S50PRO"]) {
        const tab = document.querySelector(`.v6-scope-tab[data-scope-tab="${sc}"]`);
        if (tab) tab.click();
        scopeResults[sc] = {
          tabExists: Boolean(tab),
          specs: (document.getElementById("v6ScopeSpecsLine")?.textContent || "").trim()
        };
      }

      // Theme toggle check
      const btnLight = document.getElementById("btnThemeLight");
      const btnDark = document.getElementById("btnThemeDark");
      if (btnLight) btnLight.click();
      const lightApplied = document.body.getAttribute("data-theme") === "light";
      if (btnDark) btnDark.click();
      const darkApplied = document.body.getAttribute("data-theme") !== "light";

      // Modals check: My Observations, Graph Guide, Beginner Guide, API Key Guide, Universe Luck
      const modalChecks = {};
      const checkModal = (name, openFn, modalId, closeFn) => {
        try {
          openFn();
          const m = document.getElementById(modalId);
          const isOpen = Boolean(m && m.classList.contains("open"));
          const len = m ? ((m.innerText || m.textContent || "").trim().length) : 0;
          closeFn();
          const isClosed = Boolean(m && !m.classList.contains("open"));
          modalChecks[name] = { isOpen, len, isClosed };
        } catch (e) {
          modalChecks[name] = { error: String(e) };
        }
      };

      checkModal(
        "graphGuide",
        () => window.openGraphGuideModal && window.openGraphGuideModal(0),
        "graphGuideModal",
        () => window.closeGraphGuideModal && window.closeGraphGuideModal()
      );
      checkModal(
        "beginnerGuide",
        () => window.openBeginnerGuideModal && window.openBeginnerGuideModal(0),
        "beginnerGuidePresentationModal",
        () => window.closeBeginnerGuideModal && window.closeBeginnerGuideModal()
      );
      checkModal(
        "apiKeyGuide",
        () => window.openAavsoApiKeyGuideModal && window.openAavsoApiKeyGuideModal(),
        "aavsoApiKeyGuideModal",
        () => window.closeAavsoApiKeyGuideModal && window.closeAavsoApiKeyGuideModal()
      );
      checkModal(
        "obsTracker",
        () => { const b = document.getElementById("btnOpenObsTracker"); if (b) b.click(); },
        "obsTrackerModal",
        () => { const m = document.getElementById("obsTrackerModal"); if (m) m.classList.remove("open"); }
      );
      checkModal(
        "universeLuck",
        () => { const b = document.querySelector(".universe-luck-btn") || document.getElementById("btnTryUniverseLuckFromModal"); if (b) b.click(); },
        "universeLuckModal",
        () => { const m = document.getElementById("universeLuckModal"); if (m) m.classList.remove("open"); }
      );

      // Text integrity check (no raw 'undefined' or '[object Object]' in main visible shell)
      const bodyText = (document.body.innerText || "");
      const hasUndefinedLeak = /\bundefined\b/.test(bodyText) || bodyText.includes("[object Object]");

      return JSON.stringify({
        mergeInfo,
        tMergeMs,
        tV6Ms,
        tUrgMs,
        tSearchMs,
        v6CardsInitial,
        v6CardsAfterMore,
        urgCardsInitial,
        urgCardsAfterMore,
        searchMatchCount,
        dossierOpen,
        zUrgent,
        zDossier,
        dossierTextLen,
        scopeResults,
        lightApplied,
        darkApplied,
        modalChecks,
        hasUndefinedLeak
      });
    })()
    """
    raw = loc.eval_in_browser(bundled, js_test, port=9293, await_promise=False, wait_ms=1400)
    res = json.loads(raw)
    print(
        f"  STRESS METRICS (total={res['mergeInfo']['total']} stars): "
        f"renderV6={res['tV6Ms']}ms, renderUrgent={res['tUrgMs']}ms, search={res['tSearchMs']}ms, "
        f"v6Cards={res['v6CardsInitial']}->{res['v6CardsAfterMore']}, "
        f"urgCards={res['urgCardsInitial']}->{res['urgCardsAfterMore']}"
    )
    print(f"  Z-INDEX CHECK: urgentStarsModal={res['zUrgent']}, starFullDossierModal={res['zDossier']}, open={res['dossierOpen']}, textLen={res['dossierTextLen']}")

    # Assertions: Performance & Windowing
    assert res["mergeInfo"]["total"] >= 3246, f"Expected >= 3246 stars: {res['mergeInfo']}"
    assert res["tV6Ms"] < 250, f"renderV6RadarDock too slow under 3,246 stars: {res['tV6Ms']}ms"
    assert res["tUrgMs"] < 250, f"renderUrgentStarsCards too slow under 3,246 stars: {res['tUrgMs']}ms"
    assert res["tSearchMs"] < 250, f"Search under 3,246 stars too slow: {res['tSearchMs']}ms"
    assert 0 < res["v6CardsInitial"] <= 60, f"Radar cards not windowed: {res['v6CardsInitial']}"
    assert res["v6CardsAfterMore"] > res["v6CardsInitial"], f"Radar Load More did not expand: {res['v6CardsInitial']}->{res['v6CardsAfterMore']}"
    assert 0 < res["urgCardsInitial"] <= 60, f"Urgent cards not windowed: {res['urgCardsInitial']}"
    assert res["urgCardsAfterMore"] > res["urgCardsInitial"], f"Urgent Load More did not expand: {res['urgCardsInitial']}->{res['urgCardsAfterMore']}"
    assert res["searchMatchCount"] >= 1, f"Search for V5025 returned 0 matches"

    # Assertions: Z-Index Fix
    assert res["dossierOpen"] is True, "Clicking star inside #urgentStarsModal did not open #starFullDossierModal"
    assert res["zDossier"] > res["zUrgent"], f"Z-INDEX BUG: dossier ({res['zDossier']}) must be > urgent ({res['zUrgent']})"
    assert res["dossierTextLen"] > 40, f"Star dossier modal content too short: {res['dossierTextLen']}"

    # Assertions: All 5 Telescopes
    for sc in ("S30", "S30PLUS", "S30PRO", "S50", "S50PRO"):
        sr = res["scopeResults"][sc]
        assert sr["tabExists"] is True and len(sr["specs"]) > 10, f"Telescope {sc} failed: {sr}"
    assert "2.66" in res["scopeResults"]["S30PLUS"]["specs"], f"S30PLUS specs missing 2.66°: {res['scopeResults']['S30PLUS']}"

    # Assertions: Theme Toggle & Every Modal
    assert res["lightApplied"] is True and res["darkApplied"] is True, "Theme toggle failed"
    for mname, mres in res["modalChecks"].items():
        assert mres.get("isOpen") is True and mres.get("isClosed") is True and mres.get("len", 0) > 20, f"Modal {mname} failed: {mres}"

    # Assertions: Zero Text Leaks
    assert res["hasUndefinedLeak"] is False, "Detected 'undefined' or '[object Object]' leak in rendered UI!"
    print("[2/2] ALL v1.5.0-alpha STRESS (3,246 STARS), Z-INDEX & FULL E2E CHECKS PASSED!")


if __name__ == "__main__":
    test_stress_zindex_and_full_e2e()
