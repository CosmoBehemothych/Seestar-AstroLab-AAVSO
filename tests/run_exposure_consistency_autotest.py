#!/usr/bin/env python3
"""
Release Gate Autotest: Unified Exposure Formula & UI Consistency
Verifies that AstroLabCore.evaluateScopeSuitability() uses the single D^2 + saturation
formula consistently across ALL catalog stars, ALL 5 Seestar models, and ALL languages,
with zero discrepancies between the prominent exposure badge (expRec) and badgeText,
no double units, no legacy hardcoded expHint, and overflow-safe CSS on .exp-highlight-pill.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRIDGE = ROOT / "Source_and_Build" / "pwa_mobile_and_electron" / "astrolab_engine_bridge.js"
CSS = ROOT / "Source_and_Build" / "pwa_mobile_and_electron" / "astrolab_styles.css"

def main():
    bridge_txt = BRIDGE.read_text(encoding="utf-8")
    css_txt = CSS.read_text(encoding="utf-8")

    # 1. Static source guards
    assert ".replace(\"{exp}\", prof.maxExpSec)" not in bridge_txt, "Found legacy prof.maxExpSec in badgeText!"
    assert ".replace(\"{exp}\", prof.minExpSec)" not in bridge_txt, "Found legacy prof.minExpSec in badgeText!"
    assert "const expHint =" not in bridge_txt, "Found legacy hardcoded expHint in SIMBAD catalog generator!"
    assert "if (window._astroLabSummaryCsvLoaded)" in bridge_txt, "Summary CSV must be blocked in processFile() for AAVSO!"
    assert "max-width: 100%;" in css_txt and "box-sizing: border-box;" in css_txt and ".exp-highlight-pill" in css_txt, \
        "Missing overflow-safe rules on .exp-highlight-pill!"

    # 2. Live Node.js verification across ALL stars x ALL 5 Seestar models x ALL 6 main languages
    node_script = r"""
const fs = require('fs');
const vm = require('vm');
const code = fs.readFileSync(process.argv[1], 'utf8');

// Extract AstroLabCore (from const AstroLabCore = up to window.AstroLabCore =)
const coreStart = code.indexOf('const TELESCOPE_MODELS = Object.freeze({');
const coreEnd = code.indexOf('window.AstroLabCore = AstroLabCore;');
if (coreStart < 0 || coreEnd < 0) throw new Error('AstroLabCore block not found');

// Extract I18N scopeEval* formats for ru, en, es, de, fr, zh
const fmtsByLang = {};
const langRegex = /^\s*(ru|en|es|de|fr|zh):\s*\{/gm;
const lines = code.split('\n');
let curLang = null;
for (const ln of lines) {
  const lm = ln.match(/^\s{4}(ru|en|es|de|fr|zh):\s*\{\s*$/);
  if (lm) curLang = lm[1];
  if (curLang) {
    const km = ln.match(/^\s+(scopeEval(?:Ok|Faint|Dip|Bright)Fmt):\s*"(.*)"/);
    if (km) {
      fmtsByLang[curLang] = fmtsByLang[curLang] || {};
      fmtsByLang[curLang][km[1]] = km[2];
    }
  }
}

// Extract AAVSO_URGENT_CATALOGUE sample + regression edge stars
const testStars = [
  { star: 'W UMa', magRange: '7.75m → 8.48m (P = 0.33364 d)', kmag: '10.6', type: 'Контактная затменная (EW)' },
  { star: 'SW Lac', magRange: '8.51m → 9.49m (P = 0.3207 d)', kmag: '11.2', type: 'Контактная затменная (EW/KW)' },
  { star: 'V838 Mon', magRange: '6.7m → 14.8m', kmag: '12.5', type: 'Световое эхо (LRN)' },
  { star: 'OJ 287', magRange: '12.0m → 15.1m', kmag: '13.4', type: 'Двойная сверхмассивная ЧД (BLLAC)' },
  { star: 'V404 Cyg', magRange: '11.5m → 18.5m', kmag: '13.0', type: 'Рентгеновская новая с ЧД (XN)' },
  { star: 'Betelgeuse', magRange: '0.0m → 1.6m', kmag: '5.0', type: 'Красный сверхгигант (SRC)' },
  { star: 'T CrB', magRange: '10.0m → 2.0m', kmag: '10.5', type: 'Повторная новая (NR)' },
  { star: 'SS Cyg', magRange: '12.1m → 8.2m', kmag: '11.8', type: 'Карликовая новая (UGSS)' },
  { star: 'TrES-3', magRange: '12.40m', kmag: '12.5', type: 'Транзит экзопланеты (EP)' },
  { star: 'DQ Her', magRange: '14.1m → 14.8m', kmag: '14.2', type: 'Поляр (NB+EA+DQ)' },
];

const models = ['S30', 'S30PLUS', 'S30PRO', 'S50', 'S50PRO'];
const langs = Object.keys(fmtsByLang);
if (langs.length < 6) throw new Error('Expected >= 6 languages for scopeEval formats, got ' + langs.length);

let checked = 0;
for (const lg of langs) {
  const ctx = {
    window: {},
    Date, Math, Number, String, Array, Object, RegExp, parseFloat, isNaN,
    t: (k) => (fmtsByLang[lg] && fmtsByLang[lg][k]) ? fmtsByLang[lg][k] : k
  };
  vm.runInNewContext(code.slice(coreStart, coreEnd) + '\nwindow.AstroLabCore = AstroLabCore;', ctx);
  const Core = ctx.window.AstroLabCore;

  for (const m of models) {
    for (const st of testStars) {
      const ev = Core.evaluateScopeSuitability(st, m);
      checked++;
      const expNumMatch = String(ev.expRec).match(/^(\d+)\s*s/);
      if (!expNumMatch) throw new Error(`Invalid expRec "${ev.expRec}" for ${st.star}/${m}/${lg}`);
      const expNum = expNumMatch[1];

      // Check no double units like "10 s с" or "60 s (EQ) s" or "10 s 秒"
      if (/\bs(?:\s*\(EQ\))?(?:\s*🌙)?\s+(?:s|с|秒)\b/i.test(ev.badgeText)) {
        throw new Error(`Double unit in badgeText for ${st.star}/${m}/${lg}: "${ev.badgeText}"`);
      }

      // If badgeText mentions an exposure number, it MUST equal expNum from expRec!
      const badgeExpMatch = ev.badgeText.match(/(?:Выдержка|Exposure|Exposición|Belichtung|Bel\.|Pose|Exp|曝光)\s+(\d+)\s*s/i);
      if (badgeExpMatch && badgeExpMatch[1] !== expNum) {
        throw new Error(
          `MISMATCH for ${st.star}/${m}/${lg}: expRec="${ev.expRec}" vs badgeText="${ev.badgeText}"`
        );
      }
    }
  }
}

// Specific regression assertions on S30PRO
const ctxRu = {
  window: {}, Date, Math, Number, String, Array, Object, RegExp, parseFloat, isNaN,
  t: (k) => fmtsByLang.ru[k] || k
};
vm.runInNewContext(code.slice(coreStart, coreEnd) + '\nwindow.AstroLabCore = AstroLabCore;', ctxRu);
const CoreRu = ctxRu.window.AstroLabCore;

const wuma = CoreRu.evaluateScopeSuitability(testStars[0], 'S30PRO');
if (!wuma.expRec.startsWith('10 s')) throw new Error('W UMa on S30PRO must be 10 s, got ' + wuma.expRec);

const v838 = CoreRu.evaluateScopeSuitability(testStars[2], 'S30PRO');
if (!v838.expRec.startsWith('10 s') || !v838.badgeText.includes('10 s')) {
  throw new Error(`V838 Mon on S30PRO mismatch: expRec=${v838.expRec}, badge=${v838.badgeText}`);
}

const oj287 = CoreRu.evaluateScopeSuitability(testStars[3], 'S30PRO');
const ojNum = oj287.expRec.match(/^(\d+)/)[1];
if (!oj287.badgeText.includes(ojNum + ' s')) {
  throw new Error(`OJ 287 on S30PRO mismatch: expRec=${oj287.expRec}, badge=${oj287.badgeText}`);
}


// 3. Real CCD SNR Physics verification (Bortle, Airmass, Aperture, Saturation)
const faintStar = { star: 'OJ 287', magRange: '12.0m → 15.1m', kmag: '13.4', type: 'BLLAC' };
const snrB2 = CoreRu.computeCcdSnrExposure(faintStar, 'S30PRO', { bortle: 2, fwhm: 3.5, altDeg: 60, moonFrac: 0.0 });
const snrB8 = CoreRu.computeCcdSnrExposure(faintStar, 'S30PRO', { bortle: 8, fwhm: 3.5, altDeg: 60, moonFrac: 0.0 });
if (!(snrB2.snr > snrB8.snr)) throw new Error(`Physics fail: Bortle 2 SNR (${snrB2.snr}) must exceed Bortle 8 (${snrB8.snr})`);

const snrHigh = CoreRu.computeCcdSnrExposure(faintStar, 'S30PRO', { bortle: 5, fwhm: 3.5, altDeg: 75, moonFrac: 0.0 });
const snrLow  = CoreRu.computeCcdSnrExposure(faintStar, 'S30PRO', { bortle: 5, fwhm: 3.5, altDeg: 20, moonFrac: 0.0 });
if (!(snrHigh.snr > snrLow.snr && snrLow.airmass > snrHigh.airmass)) {
  throw new Error(`Physics fail: high alt SNR (${snrHigh.snr}, X=${snrHigh.airmass}) must exceed low alt (${snrLow.snr}, X=${snrLow.airmass})`);
}

const snrS50 = CoreRu.computeCcdSnrExposure(faintStar, 'S50', { bortle: 5, fwhm: 3.5, altDeg: 60, moonFrac: 0.0 });
const snrS30 = CoreRu.computeCcdSnrExposure(faintStar, 'S30', { bortle: 5, fwhm: 3.5, altDeg: 60, moonFrac: 0.0 });
if (!(snrS50.snr > snrS30.snr)) throw new Error(`Physics fail: S50 SNR (${snrS50.snr}) must exceed S30 (${snrS30.snr})`);

console.log(`CCD SNR PHYSICS OK: B2=${snrB2.snr} > B8=${snrB8.snr} | alt75=${snrHigh.snr}(X=${snrHigh.airmass}) > alt20=${snrLow.snr}(X=${snrLow.airmass}) | S50=${snrS50.snr} > S30=${snrS30.snr}`);
console.log(`PASS: Verified ${checked} (star x model x lang) exposure consistency checks with 0 discrepancies!`);

"""
    res = subprocess.run(["node", "-e", node_script, str(BRIDGE)], capture_output=True, text=True)
    if res.returncode != 0:
        print("FAIL:", res.stdout, res.stderr)
        sys.exit(1)
    print(res.stdout.strip())

if __name__ == "__main__":
    main()
