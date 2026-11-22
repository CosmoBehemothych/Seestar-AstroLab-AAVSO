#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seestar AstroLab AAVSO — Standalone Error Monitor & AAVSO Network Diagnostics
Zero-dependency Python 3 (tkinter + stdlib) desktop monitoring tool.
"""

import datetime
import json
import os
import platform
import queue
import re
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

APP_MONITOR_VERSION = "1.4.0"

SECRET_PATTERNS = [
    (re.compile(r"(ghp_[A-Za-z0-9_]{16,}|github_pat_[A-Za-z0-9_]{20,})"), "***GITHUB_TOKEN_REDACTED***"),
    (re.compile(r"(?i)(authorization\s*[:=]\s*(?:bearer|token|basic)\s+)([^\s,;\"'<>]+)"), r"\1***REDACTED***"),
    (re.compile(r"(?i)((?:api[_-]?key|api[_-]?token|apikey|apitoken|access[_-]?token|secret|password)\s*[:=]\s*[\"']?)([A-Za-z0-9_\-\.]{6,})([\"']?)"), r"\1***REDACTED***\3"),
]


def sanitize_text(text: str) -> str:
    s = "" if text is None else str(text)
    for pat, repl in SECRET_PATTERNS:
        s = pat.sub(repl, s)
    return s


def get_log_dir() -> str:
    env_dir = os.environ.get("ASTROLAB_LOG_DIR", "").strip()
    if env_dir:
        os.makedirs(env_dir, exist_ok=True)
        return env_dir
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        d = os.path.join(base, "SeestarAstroLab", "logs")
    else:
        d = os.path.join(os.path.expanduser("~"), ".local", "share", "SeestarAstroLab", "logs")
    os.makedirs(d, exist_ok=True)
    return d


def get_log_file_path() -> str:
    return os.path.join(get_log_dir(), "astrolab_debug.log")


def build_ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def find_installed_converter_exe() -> str:
    candidates = []
    if os.name == "nt":
        local_app = os.environ.get("LOCALAPPDATA", "")
        prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        prog_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        candidates.extend([
            os.path.join(local_app, "Programs", "Seestar AstroLab AAVSO", "Seestar_AstroLab.exe"),
            os.path.join(prog_files, "Seestar AstroLab AAVSO", "Seestar_AstroLab.exe"),
            os.path.join(prog_x86, "Seestar AstroLab AAVSO", "Seestar_AstroLab.exe"),
            os.path.join(os.getcwd(), "Seestar_AstroLab.exe"),
        ])
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return ""


def is_converter_running() -> bool:
    if os.name != "nt":
        return False
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq Seestar_AstroLab.exe", "/NH"],
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            timeout=3,
        ).decode("utf-8", errors="replace")
        return "Seestar_AstroLab.exe" in out
    except Exception:
        return False


def run_aavso_network_probes(test_star: str = "SZ Lyn") -> list:
    """Tests live connectivity to all AAVSO & SIMBAD endpoints from the user's PC."""
    ssl_ctx = build_ssl_context()
    q_star = urllib.parse.quote(test_star)
    probes = [
        (
            "AAVSO Data Search v2 (Канал 1 — публичные кривые)",
            f"https://apps.aavso.org/v2/data/search/photometry/?target={q_star}&page=1",
            {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0.0.0 Safari/537.36", "Accept": "text/html,application/xhtml+xml"},
            "webobs_html",
        ),
        (
            "AAVSO REST API v2 (Канал 2 — JSON фотометрия)",
            f"https://apps.aavso.org/v2/api/observations/photometry/?target={q_star}&page_size=5",
            {"User-Agent": f"SeestarAstroLab/{APP_MONITOR_VERSION}", "Accept": "application/json"},
            "json",
        ),
        (
            "AAVSO VSX API (Паспорт звезды)",
            f"https://vsx.aavso.org/index.php?view=api.object&ident={q_star}&format=json",
            {"User-Agent": f"SeestarAstroLab/{APP_MONITOR_VERSION}", "Accept": "application/json"},
            "json",
        ),
        (
            "AAVSO Target Tool API (Проверка доступности)",
            "https://targettool.aavso.org/TargetTool/api/v1/targets?obs_section=all",
            {"User-Agent": f"SeestarAstroLab/{APP_MONITOR_VERSION}"},
            "status_only",
        ),
        (
            "SIMBAD TAP (Координаты и каталог)",
            "https://simbad.u-strasbg.fr/simbad/sim-tap/sync?request=doQuery&lang=adql&format=json&query=SELECT+TOP+1+main_id+FROM+basic",
            {"User-Agent": f"SeestarAstroLab/{APP_MONITOR_VERSION}"},
            "json",
        ),
    ]
    results = []
    for label, url, headers, mode in probes:
        t0 = time.time()
        entry = {
            "name": label,
            "url": url,
            "ok": False,
            "status": None,
            "ms": 0,
            "bytes": 0,
            "summary": "",
        }
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10, context=ssl_ctx) as resp:
                raw = resp.read()
                ms = int((time.time() - t0) * 1000)
                text = raw.decode("utf-8", errors="replace")
                entry["status"] = getattr(resp, "status", 200)
                entry["ms"] = ms
                entry["bytes"] = len(raw)
                entry["ok"] = True
                if mode == "webobs_html":
                    tr_cnt = len(re.findall(r"<tr[^>]*>", text, re.I))
                    jd_hits = len(re.findall(r"24[56]\d{4}\.\d+", text))
                    preview = re.sub(r"\s+", " ", text[:240])
                    entry["summary"] = f"HTTP {entry['status']} | {len(raw)} B | <tr>={tr_cnt} | JD_matches={jd_hits}"
                    if jd_hits == 0:
                        entry["summary"] += f" | preview={preview}"
                else:
                    preview = re.sub(r"\s+", " ", text[:180])
                    entry["summary"] = f"HTTP {entry['status']} | {len(raw)} B | preview={preview}"
        except urllib.error.HTTPError as he:
            ms = int((time.time() - t0) * 1000)
            body = ""
            try:
                body = he.read().decode("utf-8", errors="replace")[:180]
            except Exception:
                pass
            entry["status"] = he.code
            entry["ms"] = ms
            entry["ok"] = (mode == "status_only" and he.code in (401, 403))
            clean_body = re.sub(r"\s+", " ", body)
            entry["summary"] = f"HTTP {he.code} {he.reason} | {clean_body}"
        except Exception as e:
            entry["ms"] = int((time.time() - t0) * 1000)
            entry["summary"] = f"ERROR: {type(e).__name__}: {e}"
        results.append(entry)
    return results


def export_full_error_report(probe_results=None, captured_lines=None, out_dir=None) -> str:
    log_path = get_log_file_path()
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"AstroLab_Full_Error_Report_{stamp}.txt"

    if out_dir and os.path.isdir(out_dir):
        target_path = os.path.join(out_dir, filename)
    else:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        target_path = os.path.join(desktop if os.path.isdir(desktop) else get_log_dir(), filename)

    log_lines = []
    if os.path.isfile(log_path):
        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as lf:
                log_lines = lf.readlines()[-1200:]
        except Exception as e:
            log_lines = [f"[Ошибка чтения лога: {e}]\n"]
    else:
        log_lines = [f"[Файл лога пока не создан: {log_path} — запустите конвертор v1.4.0 Hotfix3+]\n"]

    certifi_info = "not-installed"
    try:
        import certifi
        certifi_info = certifi.where()
    except Exception:
        pass

    proxy_keys = [k for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy") if os.environ.get(k)]

    parts = [
        "==============================================================================",
        f"  SEESTAR ASTROLAB AAVSO — ПОЛНЫЙ ОТЧЁТ МОНИТОРИНГА ОШИБОК (v{APP_MONITOR_VERSION})",
        f"  Сформирован: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (локальное время)",
        "==============================================================================",
        f"ОС:              {platform.system()} {platform.release()} ({platform.version()})",
        f"Архитектура:     {platform.machine()}",
        f"Python:          {platform.python_version()}",
        f"OpenSSL:         {getattr(ssl, 'OPENSSL_VERSION', 'unknown')}",
        f"Certifi CA:      {certifi_info}",
        f"Proxy env keys:  {proxy_keys}",
        f"Путь к логу:     {log_path}",
        f"Конвертор EXE:   {find_installed_converter_exe() or 'не найден автоматически'}",
        "Безопасность:    API-ключи, GitHub-токены и пароли автоматически замаскированы.",
        "",
    ]

    if probe_results:
        parts.append("--- РЕЗУЛЬТАТЫ ПРОВЕРКИ СЕТИ И AAVSO ---")
        for pr in probe_results:
            flag = "OK" if pr.get("ok") else "FAIL"
            parts.append(f"[{flag}] {pr.get('name')} ({pr.get('ms')} ms)")
            parts.append(f"      URL: {pr.get('url')}")
            parts.append(f"      ->   {sanitize_text(pr.get('summary', ''))}")
        parts.append("")

    if captured_lines:
        parts.append(f"--- ПЕРЕХВАТ STDOUT/STDERR ПРОЦЕССА ({len(captured_lines)} строк) ---")
        parts.extend(sanitize_text(x).rstrip("\r\n") for x in captured_lines[-400:])
        parts.append("")

    parts.append(f"--- ЖУРНАЛ КОНВЕРТОРА astrolab_debug.log (последние {len(log_lines)} строк) ---")
    parts.append(sanitize_text("".join(log_lines)))

    with open(target_path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))

    return target_path


def run_self_test() -> int:
    tmp_dir = tempfile.mkdtemp(prefix="astrolab_mon_test_")
    os.environ["ASTROLAB_LOG_DIR"] = tmp_dir
    try:
        # 1. Secret masking test
        sample = "Authorization: Bearer ghp_1234567890abcdefghij api_key=mySecretKey99999"
        masked = sanitize_text(sample)
        assert "ghp_1234567890" not in masked, f"GitHub token leaked: {masked}"
        assert "mySecretKey99999" not in masked, f"API key leaked: {masked}"

        # 2. Log file & full report export test
        lp = get_log_file_path()
        with open(lp, "w", encoding="utf-8") as f:
            f.write("[2026-11-21 15:00:00.000] [ERROR] [AAVSO_WEBOBS] Test error api_key=SECRET123456\n")

        rep = export_full_error_report(
            probe_results=[{"name": "Test Probe", "url": "https://example.org", "ok": True, "ms": 42, "summary": "HTTP 200"}],
            captured_lines=["[STDOUT] Sample line"],
            out_dir=tmp_dir,
        )
        assert os.path.isfile(rep), "Report file not created"
        content = open(rep, "r", encoding="utf-8").read()
        assert "SECRET123456" not in content, "Secret leaked in exported report!"
        assert "AAVSO_WEBOBS" in content, "Log line missing in exported report!"
        assert "Test Probe" in content, "Probe result missing in exported report!"
        print(f"[MONITOR SELF-TEST OK] Sanitization + report export verified ({len(content)} bytes)")
        return 0
    finally:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)


def launch_gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext

    root = tk.Tk()
    root.title(f"Seestar AstroLab AAVSO — Монитор ошибок и диагностика (v{APP_MONITOR_VERSION})")
    root.geometry("1080x700")
    root.minsize(860, 540)
    root.configure(bg="#0d1117")

    ui_queue = queue.Queue()
    state = {
        "all_lines": [],
        "captured_stdout": [],
        "probe_results": [],
        "filter_mode": "ALL",
        "err_count": 0,
        "warn_count": 0,
        "log_pos": 0,
        "proc": None,
    }

    # --- Header & Status Bar ---
    top_frame = tk.Frame(root, bg="#161b22", padx=12, pady=10)
    top_frame.pack(fill=tk.X)

    tk.Label(
        top_frame,
        text="🛰️ Seestar AstroLab AAVSO — Монитор ошибок и логов",
        bg="#161b22",
        fg="#f0f6fc",
        font=("Segoe UI", 13, "bold"),
    ).pack(side=tk.LEFT)

    status_var = tk.StringVar(value="● Ожидание лога...")
    status_lbl = tk.Label(
        top_frame,
        textvariable=status_var,
        bg="#161b22",
        fg="#7ae582",
        font=("Segoe UI", 10, "bold"),
    )
    status_lbl.pack(side=tk.RIGHT)

    # --- Info Strip ---
    info_frame = tk.Frame(root, bg="#0d1117", padx=12, pady=4)
    info_frame.pack(fill=tk.X)
    log_path_var = tk.StringVar(value=f"Файл лога: {get_log_file_path()}")
    tk.Label(info_frame, textvariable=log_path_var, bg="#0d1117", fg="#8b949e", font=("Consolas", 9)).pack(side=tk.LEFT)
    counters_var = tk.StringVar(value="Ошибок: 0  |  Предупреждений: 0")
    tk.Label(info_frame, textvariable=counters_var, bg="#0d1117", fg="#ffd166", font=("Segoe UI", 9, "bold")).pack(side=tk.RIGHT)

    # --- Action Toolbar ---
    btn_frame = tk.Frame(root, bg="#0d1117", padx=12, pady=6)
    btn_frame.pack(fill=tk.X)

    def make_btn(parent, text, cmd, bg="#21262d", fg="#f0f6fc"):
        b = tk.Button(
            parent,
            text=text,
            command=cmd,
            bg=bg,
            fg=fg,
            activebackground="#30363d",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=12,
            pady=6,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        )
        b.pack(side=tk.LEFT, padx=(0, 8))
        return b

    # --- Filter Bar ---
    flt_frame = tk.Frame(root, bg="#161b22", padx=12, pady=6)
    flt_frame.pack(fill=tk.X)
    tk.Label(flt_frame, text="Фильтр:", bg="#161b22", fg="#8b949e", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 6))

    search_var = tk.StringVar()

    # --- Log Viewer ---
    log_box = scrolledtext.ScrolledText(
        root,
        bg="#0b0f14",
        fg="#c9d1d9",
        insertbackground="#ffffff",
        font=("Consolas", 9),
        wrap=tk.WORD,
        state=tk.DISABLED,
        borderwidth=0,
        padx=10,
        pady=8,
    )
    log_box.pack(fill=tk.BOTH, expand=True, padx=12, pady=(4, 12))
    log_box.tag_config("ERR", foreground="#ff6b6b")
    log_box.tag_config("WARN", foreground="#ffd166")
    log_box.tag_config("AAVSO", foreground="#4cc9f0")
    log_box.tag_config("OK", foreground="#7ae582")
    log_box.tag_config("INFO", foreground="#c9d1d9")

    def classify_line(line: str) -> str:
        u = line.upper()
        if any(k in u for k in ("[ERROR]", "[CRITICAL]", "JS_ERROR", "JS_PROMISE", "TRACEBACK", "[FAIL]", "UNCAUGHT")):
            return "ERR"
        if any(k in u for k in ("[WARN]", "[WARNING]")):
            return "WARN"
        if any(k in u for k in ("AAVSO", "WEBOBS", "SIMBAD", "PROBE", "TARGET_TOOL")):
            return "AAVSO"
        if "[OK]" in u or "СОХРАНЁН" in u:
            return "OK"
        return "INFO"

    def line_matches_filter(line: str) -> bool:
        mode = state["filter_mode"]
        u = line.upper()
        if mode == "ERR" and classify_line(line) != "ERR":
            return False
        if mode == "AAVSO" and not any(k in u for k in ("AAVSO", "WEBOBS", "SIMBAD", "PROBE", "CURVE", "TARGET")):
            return False
        if mode == "JS" and not any(k in u for k in ("FRONTEND", "JS_ERROR", "JS_PROMISE", "CONSOLE_ERROR", "FE_")):
            return False
        q = search_var.get().strip().lower()
        if q and q not in line.lower():
            return False
        return True

    def append_line_to_ui(line: str):
        safe = sanitize_text(line).rstrip("\r\n")
        if not safe:
            return
        state["all_lines"].append(safe)
        tag = classify_line(safe)
        if tag == "ERR":
            state["err_count"] += 1
        elif tag == "WARN":
            state["warn_count"] += 1
        counters_var.set(f"Ошибок: {state['err_count']}  |  Предупреждений: {state['warn_count']}")
        if line_matches_filter(safe):
            log_box.configure(state=tk.NORMAL)
            log_box.insert(tk.END, safe + "\n", tag)
            log_box.see(tk.END)
            log_box.configure(state=tk.DISABLED)

    def rerender_log():
        log_box.configure(state=tk.NORMAL)
        log_box.delete("1.0", tk.END)
        for ln in state["all_lines"]:
            if line_matches_filter(ln):
                log_box.insert(tk.END, ln + "\n", classify_line(ln))
        log_box.see(tk.END)
        log_box.configure(state=tk.DISABLED)

    def set_filter(mode: str):
        state["filter_mode"] = mode
        rerender_log()

    for label, mode in [("Все события", "ALL"), ("Только ошибки", "ERR"), ("AAVSO / Сеть", "AAVSO"), ("Фронтенд JS", "JS")]:
        make_btn(flt_frame, label, lambda m=mode: set_filter(m), bg="#21262d")

    tk.Label(flt_frame, text="Поиск:", bg="#161b22", fg="#8b949e", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(12, 4))
    search_entry = tk.Entry(flt_frame, textvariable=search_var, bg="#0d1117", fg="#f0f6fc", insertbackground="#ffffff", width=26, relief=tk.FLAT)
    search_entry.pack(side=tk.LEFT, ipady=3)
    search_var.trace_add("write", lambda *_: rerender_log())

    # --- Actions ---
    def action_launch_converter():
        exe = find_installed_converter_exe()
        if not exe:
            exe = filedialog.askopenfilename(
                title="Выберите Seestar_AstroLab.exe",
                filetypes=[("Executable", "*.exe"), ("All files", "*.*")],
            )
        if not exe:
            return
        ui_queue.put(f"[OK] Запуск конвертора с перехватом лога: {exe}")

        def _runner():
            env = os.environ.copy()
            env["ASTROLAB_DEBUG"] = "1"
            try:
                proc = subprocess.Popen(
                    [exe],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    env=env,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                state["proc"] = proc
                for line in proc.stdout:
                    state["captured_stdout"].append(line)
                    ui_queue.put(f"[PROC] {line.rstrip()}")
                rc = proc.wait()
                ui_queue.put(f"[INFO] Процесс Seestar_AstroLab.exe завершился с кодом {rc}")
            except Exception as e:
                ui_queue.put(f"[ERROR] Не удалось запустить конвертор: {e}")

        threading.Thread(target=_runner, daemon=True).start()

    def action_run_probes():
        ui_queue.put("[PROBE] Запуск диагностики сети и каналов AAVSO (тестовая звезда: SZ Lyn)...")

        def _worker():
            res = run_aavso_network_probes("SZ Lyn")
            state["probe_results"] = res
            for pr in res:
                tag = "OK" if pr["ok"] else "FAIL"
                ui_queue.put(f"[{tag}] [PROBE] {pr['name']} ({pr['ms']} ms) -> {pr['summary']}")
            ui_queue.put("[OK] Проверка сети и AAVSO завершена. Теперь можно сохранить полный отчёт.")

        threading.Thread(target=_worker, daemon=True).start()

    def action_export_report():
        try:
            out_path = export_full_error_report(
                probe_results=state["probe_results"],
                captured_lines=state["captured_stdout"],
            )
            ui_queue.put(f"[OK] Полный отчёт сохранён: {out_path}")
            try:
                root.clipboard_clear()
                root.clipboard_append(out_path)
            except Exception:
                pass
            if os.name == "nt":
                try:
                    subprocess.Popen(["explorer", "/select,", os.path.normpath(out_path)])
                except Exception:
                    pass
            messagebox.showinfo(
                "Отчёт сохранён",
                f"Полный диагностический отчёт сохранён:\n\n{out_path}\n\n"
                "Отправьте этот .txt файл в чат — все API-ключи и токены автоматически скрыты.",
            )
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", str(e))

    def action_open_logs():
        d = get_log_dir()
        if os.name == "nt":
            os.startfile(d)
        else:
            subprocess.Popen(["xdg-open", d])

    def action_clear():
        state["all_lines"].clear()
        state["err_count"] = 0
        state["warn_count"] = 0
        counters_var.set("Ошибок: 0  |  Предупреждений: 0")
        rerender_log()

    make_btn(btn_frame, "▶ Запустить конвертор (с логом)", action_launch_converter, bg="#238636")
    make_btn(btn_frame, "🌐 Проверить сеть и AAVSO", action_run_probes, bg="#1f6feb")
    make_btn(btn_frame, "💾 Сохранить полный отчёт (.txt)", action_export_report, bg="#8957e5")
    make_btn(btn_frame, "📂 Папка логов", action_open_logs, bg="#21262d")
    make_btn(btn_frame, "🧹 Очистить окно", action_clear, bg="#21262d")

    # Initial load of existing log tail
    lp = get_log_file_path()
    if os.path.isfile(lp):
        try:
            with open(lp, "r", encoding="utf-8", errors="replace") as f:
                existing = f.readlines()
                state["log_pos"] = f.tell()
            for ln in existing[-250:]:
                append_line_to_ui(ln)
        except Exception as e:
            append_line_to_ui(f"[WARN] Не удалось прочитать существующий лог: {e}")
    else:
        append_line_to_ui("[INFO] Монитор готов. Запустите Seestar AstroLab или нажмите «🌐 Проверить сеть и AAVSO».")

    # Background tailing + process polling
    def poll_loop():
        try:
            while True:
                line = ui_queue.get_nowait()
                append_line_to_ui(line)
        except queue.Empty:
            pass

        lp_now = get_log_file_path()
        if os.path.isfile(lp_now):
            try:
                sz = os.path.getsize(lp_now)
                if sz < state["log_pos"]:
                    state["log_pos"] = 0
                if sz > state["log_pos"]:
                    with open(lp_now, "r", encoding="utf-8", errors="replace") as f:
                        f.seek(state["log_pos"])
                        chunk = f.read()
                        state["log_pos"] = f.tell()
                    for ln in chunk.splitlines():
                        append_line_to_ui(ln)
            except Exception:
                pass

        root.after(400, poll_loop)

    def poll_process_status():
        running = is_converter_running()
        if running:
            status_var.set("● Seestar_AstroLab.exe запущен")
            status_lbl.configure(fg="#7ae582")
        else:
            status_var.set("○ Seestar_AstroLab.exe не запущен")
            status_lbl.configure(fg="#8b949e")
        root.after(4000, poll_process_status)

    root.after(400, poll_loop)
    root.after(500, poll_process_status)
    root.mainloop()


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(run_self_test())
    launch_gui()
