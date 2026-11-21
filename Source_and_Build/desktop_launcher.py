#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
==============================================================================
Seestar AstroLab by CosmoBehemothych – Native Desktop Runner (v1.3.4)
==============================================================================
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import threading
import ctypes

# [КРИТИЧЕСКИЙ ФИКС] Скрываем консольное окно, так как PyInstaller собирает в режиме --console
if sys.platform == "win32":
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass

# [ASSETS] Оригинальный фото-баннер installer_header_fullwidth.bmp и иконка Seestar_AstroLab.ico находятся в Source_and_Build/assets/

# Подключение единого серверного ядра бизнес-логики PhotometryBackendEngine
try:
    from backend.astrolab_backend_core import PhotometryBackendEngine, AavsoNativeAndStorageService, get_program_converted_storage_dir, start_background_rpc_server
except ImportError:
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from backend.astrolab_backend_core import PhotometryBackendEngine, AavsoNativeAndStorageService, get_program_converted_storage_dir, start_background_rpc_server
    except ImportError:
        PhotometryBackendEngine = None
        AavsoNativeAndStorageService = None
        get_program_converted_storage_dir = None
        start_background_rpc_server = None


APP_VERSION = "1.3.4"
APP_TITLE = "Seestar AstroLab AAVSO by CosmoBehemothych – Фотометрия и Радар целей (v1.3.4)"
APP_USER_MODEL_ID = "CosmoBehemothych.SeestarAstroLab.Desktop.1.0"


if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        pass


def get_base_dir():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    d = os.path.dirname(os.path.abspath(__file__))
    if d.lower().endswith(".exe"):
        return os.path.dirname(d)
    return d


def get_html_path():
    base_dir = get_base_dir()
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0])) if sys.argv else base_dir
    local_appdata = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
    installed_default = os.path.join(local_appdata, "Programs", "Seestar_AstroLab")

    # 1. Если рядом с .exe есть папка pwa_mobile_and_electron (установленная или распакованная Portable-версия), используем её напрямую
    for direct_p in [
        os.path.join(exe_dir, "pwa_mobile_and_electron", "index.html"),
        os.path.join(os.path.dirname(exe_dir), "pwa_mobile_and_electron", "index.html"),
        os.path.join(exe_dir, "Source_and_Build", "pwa_mobile_and_electron", "index.html"),
    ]:
        if direct_p and os.path.isfile(direct_p):
            return os.path.abspath(direct_p)

    # 2. [FIX PORTABLE --onefile] Если запущен одиночный Portable .exe из произвольной папки (файлы внутри sys._MEIPASS),
    # синхронизируем pwa_mobile_and_electron в постоянную рабочую папку %APPDATA%\Seestar_AstroLab\ui_runtime_v121,
    # чтобы WebView2 корректно открывал локальный интерфейс без блокировок %TEMP%\_MEI* и сохранял настройки!
    meipass_pwa = os.path.join(base_dir, "pwa_mobile_and_electron")
    if getattr(sys, "frozen", False) and os.path.isdir(meipass_pwa):
        try:
            runtime_pwa = os.path.join(get_persistent_data_dir(), "ui_runtime_v121", "pwa_mobile_and_electron")
            os.makedirs(runtime_pwa, exist_ok=True)
            for fn in os.listdir(meipass_pwa):
                s_item = os.path.join(meipass_pwa, fn)
                d_item = os.path.join(runtime_pwa, fn)
                if os.path.isfile(s_item):
                    if fn == "user_persistent_store.js" and os.path.isfile(d_item):
                        continue
                    shutil.copy2(s_item, d_item)
            rt_index = os.path.join(runtime_pwa, "index.html")
            if os.path.isfile(rt_index):
                return os.path.abspath(rt_index)
        except Exception:
            pass

    candidates = [
        os.path.join(base_dir, "pwa_mobile_and_electron", "index.html"),
        os.path.join(os.path.dirname(base_dir), "pwa_mobile_and_electron", "index.html"),
        os.path.join(base_dir, "Source_and_Build", "pwa_mobile_and_electron", "index.html"),
        os.path.join(os.path.dirname(base_dir), "Source_and_Build", "pwa_mobile_and_electron", "index.html"),
        os.path.join(installed_default, "pwa_mobile_and_electron", "index.html"),
        os.path.join(base_dir, "index.html"),
    ]
    for p in candidates:
        if p and os.path.isfile(p):
            return os.path.abspath(p)

    # [RU] Резервная самораспаковка UI из собственного .exe архива (для автономного Portable-запуска из любой папки)
    # [EN] Self-extract UI bundle from own .exe zip payload if index.html is not found in adjacent folders
    try:
        import zipfile as _zf
        import io as _io
        self_bin = os.path.abspath(sys.argv[0])
        if os.path.isfile(self_bin):
            with open(self_bin, "rb") as _bf:
                _raw = _bf.read()
            _pk = _raw.find(b"PK\x03\x04")
            if _pk != -1:
                _runtime_ui = os.path.join(get_persistent_data_dir(), "ui_runtime_v121")
                with _zf.ZipFile(_io.BytesIO(_raw[_pk:]), "r") as _z:
                    for _m in _z.namelist():
                        if _m.startswith("pwa_mobile_and_electron/") and not _m.endswith("/"):
                            _dst = os.path.join(_runtime_ui, _m)
                            os.makedirs(os.path.dirname(_dst), exist_ok=True)
                            with open(_dst, "wb") as _outf:
                                _outf.write(_z.read(_m))
                _extr_html = os.path.join(_runtime_ui, "pwa_mobile_and_electron", "index.html")
                if os.path.isfile(_extr_html):
                    return os.path.abspath(_extr_html)
    except Exception:
        pass

    return os.path.abspath(candidates[0])


def get_icon_path():
    base_dir = get_base_dir()
    candidates = [
        os.path.join(base_dir, "assets", "Seestar_AstroLab.ico"),
        os.path.join(os.path.dirname(base_dir), "assets", "Seestar_AstroLab.ico"),
        os.path.join(base_dir, "Source_and_Build", "assets", "Seestar_AstroLab.ico"),
        os.path.join(os.path.dirname(base_dir), "Source_and_Build", "assets", "Seestar_AstroLab.ico"),
        os.path.join(base_dir, "Seestar_AstroLab.ico"),
        os.path.join(os.path.dirname(base_dir), "Seestar_AstroLab.ico"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return os.path.abspath(p)
    return ""


def get_persistent_data_dir():
    appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    d = os.path.join(appdata, "Seestar_AstroLab")
    os.makedirs(d, exist_ok=True)
    return d


class AstroLabDiskBridge:
    r"""
    Нативный мост сохранения состояния на жёсткий диск Windows:
    сохраняет OBSCODE и базу «Мои наблюдения» в `%APPDATA%\\Seestar_AstroLab\\user_persistent_store.json`
    и обновляет `user_persistent_store.js` рядом с `index.html`.
    """
    def __init__(self, html_file_path):
        self._lock = threading.Lock()
        self.data_dir = get_persistent_data_dir()
        self.json_path = os.path.join(self.data_dir, "user_persistent_store.json")
        self.js_path = os.path.join(os.path.dirname(os.path.abspath(html_file_path)), "user_persistent_store.js")
        self._store = self._load_from_disk()
        self._increment_launch_counter()
        self._save_to_disk()

    def _increment_launch_counter(self):
        try:
            cnt = int(self._store.get("seestar_donate_launch_count", "0") or 0) + 1
        except Exception:
            cnt = 1
        self._store["seestar_donate_launch_count"] = str(cnt)
        self._store["seestar_host_counted_this_launch"] = "1" 

    def _load_from_disk(self):
        store = {}
        if os.path.isfile(self.json_path):
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    store.update(data)
            except Exception:
                pass
                # Язык, выбранный на этапе установки, применяется при первом запуске (если пользователь ещё не менял язык в настройках).
        # При всех последующих запусках сохраняется язык, выбранный пользователем в настройках приложения.
        installer_first_lang = ""
        try:
            inst_flag_p = os.path.join(self.data_dir, "installer_lang.txt")
            if os.path.isfile(inst_flag_p):
                with open(inst_flag_p, "r", encoding="utf-8") as iff:
                    installer_first_lang = iff.read().strip().lower()
                try:
                    os.remove(inst_flag_p)
                except Exception:
                    pass
            if not installer_first_lang and not store.get("seestar_user_lang"):
                base_d = get_base_dir()
                exe_d = os.path.dirname(os.path.abspath(sys.argv[0])) if sys.argv else base_d
                for cand_s in [
                    os.path.join(exe_d, "user_settings.json"),
                    os.path.join(base_d, "user_settings.json"),
                    os.path.join(self.data_dir, "user_settings.json"),
                ]:
                    if os.path.isfile(cand_s):
                        with open(cand_s, "r", encoding="utf-8") as sf:
                            s_obj = json.load(sf)
                        cand_l = (s_obj.get("installer_lang") or s_obj.get("lang") or "").strip().lower()
                        if cand_l:
                            installer_first_lang = cand_l
                            break
        except Exception:
            pass

        user_chosen_lang = (
            store.get("seestar_user_lang")
            or installer_first_lang
            or store.get("seestar_lang")
            or store.get("lang")
            or ""
        ).strip().lower()

        if user_chosen_lang:
            store["lang"] = user_chosen_lang
            store["seestar_lang"] = user_chosen_lang
            store["seestar_user_lang"] = user_chosen_lang
            store.pop("installer_lang", None)
        else:
            store["lang"] = "en"
            store["seestar_lang"] = "en"
            store.pop("installer_lang", None)
        try:
            if AavsoNativeAndStorageService:
                conv_db = AavsoNativeAndStorageService.load_storage_db()
                store["seestar_converted_photometry_db_v1"] = json.dumps(conv_db, ensure_ascii=False)
                store["seestar_converted_storage_dir"] = get_program_converted_storage_dir()
        except Exception:
            pass
        return store

    def _save_to_disk(self):
        try:
            os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(self._store, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        self._write_sync_js()

    def _write_sync_js(self):
        try:
            payload = json.dumps(self._store, ensure_ascii=False)
            js_code = f"window.__SEESTAR_DISK_STORE__ = {payload};\n"
            with open(self.js_path, "w", encoding="utf-8") as f:
                f.write(js_code)
        except Exception:
            pass

    def save_store_item(self, key, val):
        with self._lock:
            k_str = str(key)
            v_str = str(val)
            self._store[k_str] = v_str
            if k_str in ("lang", "seestar_lang", "seestar_user_lang"):
                self._store["lang"] = v_str
                self._store["seestar_lang"] = v_str
                self._store["seestar_user_lang"] = v_str
                self._store.pop("installer_lang", None)
            self._save_to_disk()
        return True

    def remove_store_item(self, key):
        with self._lock:
            self._store.pop(str(key), None)
            self._save_to_disk()
        return True


    def get_all_store(self):
        with self._lock:
            return dict(self._store)

    def backend_get_scope_profile(self, code="S50"):
        if PhotometryBackendEngine:
            return PhotometryBackendEngine.get_scope_profile(code)
        return {}

    def backend_preview_csv(self, payload):
        if PhotometryBackendEngine and isinstance(payload, dict):
            return PhotometryBackendEngine.preview_and_verify_csv(
                csv_text=payload.get("csvText", ""),
                simbad_loaded=bool(payload.get("simbadLoaded", False)),
                catalog_star=payload.get("catalogStar", ""),
                catalog_ra=payload.get("catalogRa"),
                catalog_dec=payload.get("catalogDec"),
                catalog_kmag=payload.get("catalogKmag"),
            )
        return {}

    def backend_convert_csv(self, payload):
        if PhotometryBackendEngine and isinstance(payload, dict):
            return PhotometryBackendEngine.convert_seestar_csv_to_aavso_extended(
                csv_text=payload.get("csvText", ""),
                obscode=payload.get("obscode", ""),
                starid_ui=payload.get("starid", ""),
                chart=payload.get("chart", "na"),
                kname=payload.get("kname", "na"),
                kmag=payload.get("kmag", "na"),
                ra_ui=payload.get("ra", ""),
                dec_ui=payload.get("dec", ""),
                scope_model=payload.get("scopeModel", "S50"),
                simbad_loaded=bool(payload.get("simbadLoaded", False)),
                catalog_star=payload.get("catalogStar", ""),
                catalog_ra=payload.get("catalogRa"),
                catalog_dec=payload.get("catalogDec"),
            )
        return {}

    def backend_verify_file(self, content):
        if PhotometryBackendEngine:
            return PhotometryBackendEngine.verify_converted_aavso_file(content)
        return {}

    def backend_save_converted_session(self, payload):
        if AavsoNativeAndStorageService and isinstance(payload, dict):
            res = AavsoNativeAndStorageService.save_converted_session(
                star_name=payload.get("star", ""),
                obscode=payload.get("obscode", ""),
                scope_model=payload.get("scopeModel", "S50"),
                file_name=payload.get("fileName", "Seestar_AAVSO.csv"),
                aavso_csv_content=payload.get("content", ""),
                points=payload.get("points"),
            )
            try:
                db_data = AavsoNativeAndStorageService.load_storage_db()
                with self._lock:
                    self._store["seestar_converted_photometry_db_v1"] = json.dumps(db_data, ensure_ascii=False)
                    self._save_to_disk()
            except Exception:
                pass
            return res
        return {"ok": False, "error": "Backend storage service unavailable"}

    def backend_get_converted_history(self, star=""):
        if AavsoNativeAndStorageService:
            return AavsoNativeAndStorageService.get_converted_history(star)
        return {"ok": False, "hasData": False, "points": [], "error": "Сервис истории недоступен"}

    def backend_query_aavso_star(self, payload):
        if AavsoNativeAndStorageService and isinstance(payload, dict):
            return AavsoNativeAndStorageService.query_aavso_star(
                star_name=payload.get("star", ""),
                scope_model=payload.get("scopeModel", "S50"),
                api_token=payload.get("apiToken", ""),
            )
        return {"ok": False, "error": "Backend AAVSO resolver unavailable"}

    def backend_check_github_latest_release(self, payload=None):
        p = payload if isinstance(payload, dict) else {}
        return AavsoNativeAndStorageService.check_github_latest_release(p.get("currentVersion") or APP_VERSION)

    def backend_fetch_live_aavso_campaign_targets(self, payload=None):
        if AavsoNativeAndStorageService:
            p = payload if isinstance(payload, dict) else {}
            return AavsoNativeAndStorageService.fetch_live_aavso_campaign_targets(
                max_stars=int(p.get("maxStars", 25) or 25)
            )
        return {"ok": False, "notices": [], "targets": [], "error": "Backend unavailable"}

    def backend_fetch_aavso_target_tool_targets(self, payload=None):
        if AavsoNativeAndStorageService:
            p = payload if isinstance(payload, dict) else {}
            return AavsoNativeAndStorageService.fetch_aavso_target_tool_targets(
                api_key=p.get("apiKey", ""),
                obs_section=p.get("obsSection", "all"),
            )
        return {"ok": False, "targets": [], "count": 0, "error": "Backend unavailable"}

    def backend_fetch_aavso_light_curve(self, payload):
        if AavsoNativeAndStorageService and isinstance(payload, dict):
            return AavsoNativeAndStorageService.fetch_aavso_light_curve(
                star_name=payload.get("star", ""),
                days_back=int(payload.get("daysBack", 180) or 180),
                api_token=payload.get("apiToken", ""),
                user_obscode=payload.get("obscode", ""),
            )
        return {"ok": False, "hasAavsoData": False, "otherObserversPoints": [], "userAavsoPoints": []}

    def backend_open_converted_storage_folder(self):
        try:
            folder = get_program_converted_storage_dir() if get_program_converted_storage_dir else self.data_dir
            os.makedirs(folder, exist_ok=True)
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
            return {"ok": True, "path": folder}
        except Exception as e:
            return {"ok": False, "error": str(e)}


def apply_win32_window_icon(window_title, icon_path):
    if sys.platform != "win32" or not icon_path or not os.path.isfile(icon_path):
        return

    import time
    import ctypes

    def _worker():
        WM_SETICON = 0x0080
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x0010
        ICON_SMALL = 0
        ICON_BIG = 1
        GCLP_HICON = -14

        for _ in range(80):
            time.sleep(0.1)
            hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
            if hwnd:
                try:
                    hBig = ctypes.windll.user32.LoadImageW(None, icon_path, IMAGE_ICON, 48, 48, LR_LOADFROMFILE)
                    hSmall = ctypes.windll.user32.LoadImageW(None, icon_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
                    if hBig:
                        ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hBig)
                        try:
                            ctypes.windll.user32.SetClassLongPtrW(hwnd, GCLP_HICON, hBig)
                        except Exception:
                            pass
                    if hSmall:
                        ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hSmall)
                except Exception:
                    pass
                break

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def try_install_pywebview():
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        ans = messagebox.askyesno(
            "Seestar AstroLab Desktop",
            "Для запуска в собственном изолированном окне (Microsoft Edge WebView2) "
            "требуется библиотека pywebview.\n\n"
            "Установить её автоматически прямо сейчас?"
        )
        root.destroy()
        if not ans:
            return False

        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if sys.platform == "win32" else 0
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "install", "pywebview"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=flags
        )
        return proc.returncode == 0
    except Exception:
        return False



_APP_MUTEX_HANDLE = None

def _acquire_running_app_mutex():
    """Создаёт именованный мьютекс Windows и lock-файл на время работы окна приложения (Пункт 7)."""
    global _APP_MUTEX_HANDLE
    lock_file = os.path.join(get_persistent_data_dir(), "running_instance.lock")
    try:
        with open(lock_file, "w", encoding="utf-8") as lf:
            json.dump({"pid": os.getpid(), "version": APP_VERSION}, lf)
    except Exception:
        pass

    if sys.platform == "win32":
        try:
            import ctypes
            _APP_MUTEX_HANDLE = ctypes.windll.kernel32.CreateMutexW(
                None, False, "Local\\SeestarAstroLabAAVSO_Running_Mutex"
            )
        except Exception:
            pass

    import atexit
    def _cleanup_running_lock():
        global _APP_MUTEX_HANDLE
        try:
            if os.path.exists(lock_file):
                os.remove(lock_file)
        except Exception:
            pass
        if sys.platform == "win32" and _APP_MUTEX_HANDLE:
            try:
                import ctypes
                ctypes.windll.kernel32.CloseHandle(_APP_MUTEX_HANDLE)
            except Exception:
                pass
            _APP_MUTEX_HANDLE = None
    atexit.register(_cleanup_running_lock)


def main():
    _acquire_running_app_mutex()
    if start_background_rpc_server:
        start_background_rpc_server(18765)
    html_file = get_html_path()
    icon_file = get_icon_path()

    if not os.path.isfile(html_file):
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Ошибка Seestar AstroLab", f"Файл интерфейса не найден:\n{html_file}")
            root.destroy()
        except Exception:
            pass
        sys.exit(1)

    # Инициализируем постоянное файловое хранилище ДО создания окна WebView2
    disk_bridge = AstroLabDiskBridge(html_file)

    try:
        import webview
    except ImportError:
        if try_install_pywebview():
            try:
                import webview
            except ImportError:
                webview = None
        else:
            webview = None

    if not webview:
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo(
                "Требуется pywebview",
                "Для запуска десктопного окна выполните в командной строке:\n\n"
                "pip install pywebview"
            )
            root.destroy()
        except Exception:
            pass
        sys.exit(1)

    apply_win32_window_icon(APP_TITLE, icon_file)

    # [RU] Очищаем дисковый HTTP/JS-кэш WebView2 перед открытием окна, чтобы обновления интерфейса
    #      (astrolab_view_template.js, astrolab_engine_bridge.js, astrolab_styles.css) всегда загружались свежими!
    # [EN] Purge WebView2 disk cache before creating the window so updated JS/CSS bundles always load fresh.
    try:
        import shutil as _shutil
        _wv_root = os.path.join(get_persistent_data_dir(), "WebView2_Storage", "EBWebView", "Default")
        for _cache_sub in ("Cache", "Code Cache", "GPUCache", "Service Worker", "DawnCache"):
            _cp = os.path.join(_wv_root, _cache_sub)
            if os.path.isdir(_cp):
                _shutil.rmtree(_cp, ignore_errors=True)
    except Exception:
        pass

    window = webview.create_window(
        title=APP_TITLE,
        url=pathlib.Path(html_file).as_uri(),
        js_api=disk_bridge,
        width=1380,
        height=920,
        min_size=(640, 480),
        confirm_close=False,
        text_select=True,
        zoomable=True
    )

    def _on_loaded():
        try:
            saved_data = disk_bridge.get_all_store()
            if saved_data:
                payload = json.dumps(saved_data, ensure_ascii=False)
                window.evaluate_js(f"if (window.__restoreFromDiskStore) window.__restoreFromDiskStore({payload});")
        except Exception:
            pass

    try:
        window.events.loaded += _on_loaded
    except Exception:
        pass

    wv_storage_dir = os.path.join(get_persistent_data_dir(), "WebView2_Storage")
    os.makedirs(wv_storage_dir, exist_ok=True)

    # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ ПУНКТОВ 2 и 3: private_mode=False и постоянный storage_path!
    def _on_closed():
        try:
            lock_file = os.path.join(get_persistent_data_dir(), "running_instance.lock")
            if os.path.exists(lock_file):
                os.remove(lock_file)
        except Exception:
            pass
        os._exit(0)

    try:
        window.events.closed += _on_closed
    except Exception:
        pass

    try:
        webview.start(gui="edgechromium", debug=False, private_mode=False, storage_path=wv_storage_dir)
    except TypeError:
        try:
            webview.start(gui="edgechromium", debug=False, private_mode=False)
        except TypeError:
            webview.start(gui="edgechromium", debug=False)

    _on_closed()




# =============================================================================
# КРИПТОГРАФИЧЕСКАЯ МЕТКА АВТОРСТВА (COSMOBEHEMOTHYCH ANTI-PLAGIARISM SEAL)
# =============================================================================
_CBH_AUTHOR_FINGERPRINT = "CBH-ASTROLAB-AAVSO-2026-9F8E4A21-7C3D-B601"
_CBH_ENC_SEAL_B64 = "eorFisSKzorBisKKx4rHisKKwHqK+orKis2K+orKisuKxIr4isCKwnpyFQgTHRMUGxZ6Gw8OEhUICRITCnoKCBUVHHNQisWL2oriiuGK5Irsiu+K54riiu9gegk/PykuOyh6GykuKDUWOzh6GxsMCRV6cixrdGp0anq42s56isWK74vaiuiK6ovVeoroiu+L2ovbiuKL1XNQisqK6IvYiuSL2nqK4nqK5YvaiuqK6IrkiuSK64rhiuqK7orqi9iK74rhi9Zgehk1KTc1GD8yPzc1LjIjOTJQHTMuEi84YHoyLi4qKWB1dT0zLjIvOHQ5NTd1GTUpNzUYPzI/NzUuMiM5MlAYNTUpLiNgejIuLiopYHV1ODU1KS4jdC41dTk1KTc1OD8yPzc1LjIjOTJQivyK4ovei9qK5IroiuSK43qK5IvYiuWK74vdiuqL2IrkiuB6chsvLjI1KHocMzQ9PygqKDM0LnNgehkYEncbCQ4IFRYbGHcbGwwJFXdoamhsd2McYh9uG2hrd20ZaR53GGxqa1CKyovai9+K4ovYiu+K4IvYi9mL2orqYHqKyIrqi9qK4orqiueL2HpsenKK+orqiu6K6ovaeovciu+K4YrviuN6GxsMCRV6cXqK/IrviueL2IvaiuqK4YvWiueK6ovVeoveiuSL2IrkiuaK74vYi9qK4ovdiu+L24rgiuqL1XqK4YrqiuuK5IvaiuqL2Irki9qK4ovVegk/PykuOyh6CWlqdQlpagoIFXUJb2p1CW9qCggVcw=="
_CBH_SEAL_SHA256 = "b53bea58d23a07b1b2f1f3cb184915ec0bc2894fddf779c3e9582b5a1fb90dcc"


def verify_cosmobehemothych_authorship() -> dict:
    """Декодирует скрытую XOR+Base64 цифровую подпись автора разработки (CosmoBehemothych)."""
    import base64 as _b64
    raw = bytes(b ^ 90 for b in _b64.b64decode(_CBH_ENC_SEAL_B64))
    return {
        "author": "CosmoBehemothych",
        "github": "https://github.com/CosmoBehemothych",
        "boosty": "https://boosty.to/cosmobehemothych",
        "fingerprint": _CBH_AUTHOR_FINGERPRINT,
        "sha256": _CBH_SEAL_SHA256,
        "certificate": raw.decode("utf-8", errors="replace"),
    }


if __name__ == "__main__":
    main()
