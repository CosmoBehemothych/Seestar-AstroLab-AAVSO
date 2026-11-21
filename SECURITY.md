# Security Policy

## Supported Versions

Only the latest release line receives active security and bug fixes. Starting with `v1.3.4`, the project distributes **only the Windows Installer** (`Seestar_AstroLab_Setup_v*.exe`); portable builds are no longer maintained.

| Version | Supported |
| :--- | :---: |
| `1.3.x` | ✅ Yes |
| `< 1.3.0` | ❌ No |

## Reporting a Vulnerability

If you discover a security issue, unexpected network behavior, or a data-integrity flaw:

1. **Email privately:** [CosmoBehemothych@gmail.com](mailto:CosmoBehemothych@gmail.com) with subject `[SECURITY] Seestar AstroLab AAVSO`.
2. **Or use GitHub Security Advisories:** open a private report via the repository's **Security → Advisories** tab.

Please include steps to reproduce and the affected version. You can expect an acknowledgment within **72 hours** and a coordinated fix in the next patch release.

## Verifying Release Integrity (SHA-256 & Reproducible Builds)

Every official release binary is built transparently from source on GitHub-hosted Windows runners via [`.github/workflows/build.yml`](.github/workflows/build.yml) and published alongside `SHA256SUMS.txt` and `VERIFY.txt`.

To verify a downloaded installer on Windows:

```powershell
Get-FileHash .\Seestar_AstroLab_Setup_v1.3.4.exe -Algorithm SHA256
```

Compare the output hash with the value published in `SHA256SUMS.txt` on the [GitHub Releases](https://github.com/CosmoBehemothych/Seestar-AstroLab-AAVSO/releases) page. You may also upload the installer to [VirusTotal](https://www.virustotal.com/) or build the executable yourself from source following [`BUILD.md`](BUILD.md).

## Windows SmartScreen Notice

Because the Windows installer does not carry a commercial Authenticode code-signing certificate, Windows Defender SmartScreen may display an *"Unknown publisher"* warning. This reflects the absence of a commercial Authenticode certificate rather than detected malware. Always verify the `SHA-256` checksum before proceeding.

## Privacy & Network Scope

Seestar AstroLab AAVSO collects **zero telemetry** and never uploads telescope images or personal data. All network requests are strictly read-only queries to public astronomy, weather, and release endpoints:

- **AAVSO** (`aavso.org`) — VSX, VSP comparison star charts, AID light curves, urgent target alerts
- **CDS SIMBAD** (`simbad.cds.unistra.fr`) — canonical star names and J2000.0 coordinates
- **Open-Meteo** (`open-meteo.com`) & **USNO** (`aa.usno.navy.mil`) — local sky clarity and Moon phase
- **GitHub Releases API** (`api.github.com`) — one-time startup version check (no auto-download)
