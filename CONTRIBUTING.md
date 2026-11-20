# Contributing to Seestar AstroLab AAVSO

Thank you for your interest in improving **Seestar AstroLab AAVSO**! Contributions from amateur astronomers, professional variable-star observers, translators, and software developers are very welcome.

## Ways to Contribute

- **Scientific & Photometric Feedback:** Suggest improvements to AAVSO Extended compliance, airmass/altitude thresholds, `MERR` filtering, or observing-condition recommendations.
- **Bug Reports:** Open a [GitHub Issue](https://github.com/CosmoBehemothych/Seestar-AstroLab-AAVSO/issues) with your app version, Windows version, steps to reproduce, and (if relevant) an anonymized sample of the Seestar `Magnitude_*.csv` file.
- **Translations:** The UI currently supports 8 languages (`EN`, `RU`, `ES`, `DE`, `FR`, `ZH`, `CS`, `BER`). Improvements to existing translations or new languages are always welcome.
- **Code & Pull Requests:** Fork the repository, create a feature branch, and open a Pull Request against `main`.

## Scientific Data Integrity Rules

All pull requests touching photometry conversion or target validation must preserve these non-negotiable rules:

1. **No fabricated measurements:** Exported AAVSO Extended files must strictly set `CNAME=ENSEMBLE`, `CMAG=na`, `KNAME=na`, `KMAG=na`, and `AIRMASS=na` when those quantities are not independently measured in the raw Seestar CSV.
2. **Coordinate & catalog verification:** Keep J2000.0 `RA`/`Dec` cross-checking against SIMBAD / AAVSO VSX intact (`< 0.00001°` match, `≤ 0.05°` warning, `> 0.05°` conversion lock).
3. **Symmetric hemisphere math:** Visibility calculations must work identically for Northern and Southern Hemisphere observers (`|lat - dec| ≤ 70°`, culmination `≥ 20°`).

## Running Mandatory Regression Autotests

Before opening a Pull Request, run all three regression autotests from the repository root:

```bash
python tests/run_localization_autotest.py
python tests/run_coord_reconciliation_autotest.py
python tests/run_update_checker_autotest.py
```

All three suites must report `PASS` (the same checks run automatically in GitHub Actions CI on every push and pull request).

## Building Locally

See [`BUILD.md`](BUILD.md) for step-by-step instructions on reproducing the Windows installer from source.

## Code of Conduct

By participating in this project, you agree to abide by our [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
