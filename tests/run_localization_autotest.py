#!/usr/bin/env python3
"""
Automated 8-Language Localization & Regression Test for Seestar AstroLab AAVSO.
Must pass with exit code 0 before every build/release.
"""
import os, sys, json, time, socket, struct, base64, shutil, tempfile, subprocess, urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def find_chromium_binary():
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    win_candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for p in win_candidates:
        if p and os.path.isfile(p):
            return p
    raise FileNotFoundError("No Chromium/Chrome/Edge browser found for headless regression test")

ROOT = Path(__file__).resolve().parent.parent
PWA = ROOT / "Source_and_Build" / "pwa_mobile_and_electron"

class SimpleWS:
    def __init__(self, url):
        rest = url[5:]
        host_port, path = rest.split("/", 1)
        host, port = host_port.split(":")
        self.sock = socket.create_connection((host, int(port)), timeout=15)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall(
            f"GET /{path} HTTP/1.1\r\nHost: {host_port}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n".encode()
        )
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.sock.recv(4096)
        self.extra = buf.split(b"\r\n\r\n", 1)[1]
        self.msg_id = 0

    def _recv_exact(self, n):
        out = bytearray()
        if self.extra:
            take = min(n, len(self.extra))
            out.extend(self.extra[:take])
            self.extra = self.extra[take:]
        while len(out) < n:
            out.extend(self.sock.recv(n - len(out)))
        return bytes(out)

    def send(self, obj):
        self.msg_id += 1
        obj["id"] = self.msg_id
        data = json.dumps(obj).encode("utf-8")
        mask = os.urandom(4)
        header = bytearray([0x81])
        L = len(data)
        if L < 126:
            header.append(0x80 | L)
        elif L < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", L))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", L))
        header.extend(mask)
        self.sock.sendall(bytes(header) + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))
        return self.msg_id

    def call(self, method, params=None):
        mid = self.send({"method": method, "params": params or {}})
        while True:
            b1, b2 = self._recv_exact(2)
            op = b1 & 0x0F
            L = b2 & 0x7F
            if L == 126:
                L = struct.unpack("!H", self._recv_exact(2))[0]
            elif L == 127:
                L = struct.unpack("!Q", self._recv_exact(8))[0]
            pl = self._recv_exact(L)
            if op == 1:
                m = json.loads(pl.decode("utf-8"))
                if m.get("id") == mid:
                    return m.get("result", {})

def main():
    css = (PWA / "astrolab_styles.css").read_text(encoding="utf-8")
    tmpl = (PWA / "astrolab_view_template.js").read_text(encoding="utf-8")
    bridge = (PWA / "astrolab_engine_bridge.js").read_text(encoding="utf-8")
    doc = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{css}</style></head>
<body><div id="app"></div><script>{tmpl}</script>
<script>window.__SEESTAR_DISK_STORE__={{installer_lang:"en",lang:"en"}};</script>
<script>{bridge}</script></body></html>"""

    user_dir = tempfile.mkdtemp(prefix="astrolab_loc_")
    browser_bin = find_chromium_binary()
    proc = subprocess.Popen(
        [browser_bin, "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", f"--user-data-dir={user_dir}", "--remote-debugging-port=9235", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    try:
        ws_url = None
        for _ in range(30):
            try:
                with urllib.request.urlopen("http://127.0.0.1:9235/json", timeout=1) as r:
                    pages = json.loads(r.read().decode())
                    if pages:
                        ws_url = pages[0]["webSocketDebuggerUrl"]
                        ft = pages[0]["id"]
                        break
            except Exception:
                time.sleep(0.2)
        assert ws_url, "Chromium CDP failed to start"
        ws = SimpleWS(ws_url)
        ws.call("Page.enable")
        ws.call("Runtime.enable")
        ws.call("Page.setDocumentContent", {"frameId": ft, "html": doc})
        time.sleep(1.5)

        res = ws.call("Runtime.evaluate", {
            "expression": """
            (() => {
              const langs = ["en", "ru", "es", "de", "fr", "zh", "cs", "ber"];
              const domKeys = new Set();
              document.querySelectorAll("[data-i18n]").forEach(el => domKeys.add(el.getAttribute("data-i18n")));
              document.querySelectorAll("[data-i18n-placeholder]").forEach(el => domKeys.add(el.getAttribute("data-i18n-placeholder")));
              document.querySelectorAll("[data-i18n-title]").forEach(el => domKeys.add(el.getAttribute("data-i18n-title")));
              document.querySelectorAll("[data-i18n-html]").forEach(el => domKeys.add(el.getAttribute("data-i18n-html")));

              const enDict = window.I18N.en || {};
              const out = { totalDomKeys: domKeys.size, results: {} };
              const sel = document.getElementById("langSelect");

              for (const l of langs) {
                sel.value = l;
                sel.dispatchEvent(new Event("change", { bubbles: true }));
                const d = window.I18N[l] || {};
                const missing = [...domKeys].filter(k => !(k in d) || !String(d[k] || "").trim());
                const untranslated = [];
                if (l !== "en") {
                  for (const k of domKeys) {
                    const ve = String(enDict[k] || "").trim();
                    const vl = String(d[k] || "").trim();
                    if (ve && vl && ve === vl && ve.includes(" ") && ve.length >= 8) {
                      if (!/^(AAVSO|SIMBAD|VSP|VSX|OBSCODE|STARID|CHART|KNAME|KMAG|RA|Dec|Seestar|19ʰ|\\+50°|💙 aavso|Version \d+\.\d+\.\d+)/i.test(ve)) {
                        untranslated.push([k, ve]);
                      }
                    }
                  }
                }
                out.results[l] = {
                  dictSize: Object.keys(d).length,
                  missingCount: missing.length,
                  missing,
                  untranslatedCount: untranslated.length,
                  untranslated,
                  liveGuideBtn: document.getElementById("btnOpenBeginnerGuideTop")?.innerText?.trim(),
                  liveLuckBtn: document.getElementById("btnTryUniverseLuck")?.innerText?.trim(),
                  liveSettingsBtn: document.querySelector("#btnSettingsGear [data-i18n='lblSettingsTitle']")?.innerText?.trim(),
                  liveConvertBtn: document.getElementById("btnConvert")?.innerText?.trim(),
                };
              }
              return JSON.stringify(out);
            })()
            """,
            "returnByValue": True
        })
        data = json.loads(res["result"]["value"])
        print(f"=== LOCALIZATION AUTOTEST REPORT (DOM keys: {data['totalDomKeys']}) ===")
        all_ok = True
        for l, r in data["results"].items():
            status = "PASS" if (r["missingCount"] == 0 and r["untranslatedCount"] == 0 and (l == "en" or "Try the Luck" not in (r["liveLuckBtn"] or ""))) else "FAIL"
            if status != "PASS":
                all_ok = False
            print(f"[{status}] {l.upper():3s} | dict={r['dictSize']} | missing={r['missingCount']} | untranslated={r['untranslatedCount']} | guide={r['liveGuideBtn']!r} | luck={r['liveLuckBtn']!r} | settings={r['liveSettingsBtn']!r}")
            if r["missing"]:
                print(f"   Missing keys: {r['missing']}")
            if r["untranslated"]:
                print(f"   Untranslated: {r['untranslated'][:10]}")
        sys.exit(0 if all_ok else 1)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        shutil.rmtree(user_dir, ignore_errors=True)

if __name__ == "__main__":
    main()
