# -*- coding: utf-8 -*-
"""
[RU] Выделенный модуль локального HTTP/RPC-сервера Seestar AstroLab AAVSO (127.0.0.1:18765).
     Обеспечивает проверку криптографического токена X-AstroLab-Token для всех POST-запросов
     и строгий контроль заголовка Origin.
[EN] Dedicated local HTTP/RPC server module for Seestar AstroLab AAVSO (127.0.0.1:18765)
     with mandatory X-AstroLab-Token authentication on POST and strict Origin checks.
"""

import hmac
import json
import re
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional

RPC_AUTH_TOKEN: str = secrets.token_hex(32)
MAX_RPC_BODY_BYTES: int = 25 * 1024 * 1024  # 25 MB safety cap


def get_rpc_auth_token() -> str:
    """Return the per-process cryptographic token required for local RPC POST requests."""
    return RPC_AUTH_TOKEN


def is_allowed_rpc_origin(origin: str) -> bool:
    if not origin:
        return True  # Non-browser / direct local client without Origin header
    o = origin.strip().lower()
    if o == "null":
        return True  # WebView2 / Electron file:// origin
    return bool(re.match(r"^https?://(127\.0\.0\.1|localhost)(:\d{1,5})?$", o))


def build_rpc_handler_class(
    app_version: str,
    photometry_engine_cls: Any,
    storage_service_cls: Any,
    diagnostic_logger_cls: Any,
):
    """[RU] Фабрика HTTP-обработчика локального RPC-сервера с привязкой к ядру."""

    class _AstroLabBackendRequestHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            return

        def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
            raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            origin = self.headers.get("Origin", "")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            if origin and is_allowed_rpc_origin(origin):
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-AstroLab-Token")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_OPTIONS(self) -> None:
            origin = self.headers.get("Origin", "")
            if origin and not is_allowed_rpc_origin(origin):
                self._send_json({"ok": False, "error": "Forbidden origin"}, 403)
                return
            self._send_json({"ok": True})

        def do_GET(self) -> None:
            origin = self.headers.get("Origin", "")
            if origin and not is_allowed_rpc_origin(origin):
                self._send_json({"ok": False, "error": "Forbidden origin"}, 403)
                return
            if self.path.startswith("/api/health"):
                # Strictly public health metadata only — never expose auth token or filesystem paths
                self._send_json({"ok": True, "version": app_version, "engine": "PhotometryBackendEngine"})
            else:
                self._send_json({"ok": False, "error": "Not found"}, 404)

        def do_POST(self) -> None:
            origin = self.headers.get("Origin", "")
            if origin and not is_allowed_rpc_origin(origin):
                self._send_json({"ok": False, "error": "Forbidden origin"}, 403)
                return

            require_token = getattr(self.server, "require_token", True)
            if require_token:
                supplied = (self.headers.get("X-AstroLab-Token") or "").strip()
                if not supplied or not hmac.compare_digest(supplied, RPC_AUTH_TOKEN):
                    self._send_json({"ok": False, "error": "Unauthorized RPC request"}, 401)
                    return

            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._send_json({"ok": False, "error": "Invalid Content-Length"}, 400)
                return

            if length < 0:
                self._send_json({"ok": False, "error": "Negative Content-Length"}, 400)
                return
            if length > MAX_RPC_BODY_BYTES:
                self._send_json({"ok": False, "error": f"Payload exceeds {MAX_RPC_BODY_BYTES} bytes limit"}, 413)
                return

            try:
                body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, 400)
                return

            action = body.get("action", "")
            try:
                self._dispatch_post_action(action, body)
            except Exception as exc:
                try:
                    diagnostic_logger_cls.log_exception("RPC_DISPATCH_ERR", f"RPC action '{action}' failed", exc)
                except Exception:
                    pass
                self._send_json({"ok": False, "error": f"Internal RPC error: {exc}"}, 500)

        def _dispatch_post_action(self, action: str, body: Dict[str, Any]) -> None:
            if action == "get_scope_profile":
                self._send_json({"ok": True, "profile": photometry_engine_cls.get_scope_profile(body.get("code", "S50"))})
            elif action == "preview_csv":
                res = photometry_engine_cls.preview_and_verify_csv(
                    csv_text=body.get("csvText", ""),
                    simbad_loaded=bool(body.get("simbadLoaded", False)),
                    catalog_star=body.get("catalogStar", ""),
                    catalog_ra=body.get("catalogRa"),
                    catalog_dec=body.get("catalogDec"),
                    catalog_kmag=body.get("catalogKmag"),
                    scope_model=body.get("scopeModel", "S50"),
                )
                self._send_json({"ok": True, "result": res})
            elif action == "convert_csv":
                res = photometry_engine_cls.convert_seestar_csv_to_aavso_extended(
                    csv_text=body.get("csvText", ""),
                    obscode=body.get("obscode", ""),
                    starid_ui=body.get("starid", ""),
                    chart=body.get("chart", "na"),
                    kname="na",  # Strictly na for Seestar ensemble photometry
                    kmag="na",   # Strictly na for Seestar ensemble photometry
                    ra_ui=body.get("ra", ""),
                    dec_ui=body.get("dec", ""),
                    scope_model=body.get("scopeModel", "S50"),
                    simbad_loaded=bool(body.get("simbadLoaded", False)),
                    catalog_star=body.get("catalogStar", ""),
                    catalog_ra=body.get("catalogRa"),
                    catalog_dec=body.get("catalogDec"),
                    calc_amass=bool(body.get("calcAmass", False)),
                    site_lat=body.get("siteLat"),
                    site_lon=body.get("siteLon"),
                    clip_outliers_3sigma=bool(body.get("clipOutliers3Sigma", False)),
                    selected_sessions=body.get("selectedSessions"),
                )
                self._send_json(res)
            elif action == "verify_file":
                res = photometry_engine_cls.verify_converted_aavso_file(body.get("content", ""))
                self._send_json({"ok": True, "result": res})
            elif action == "save_converted_session":
                res = storage_service_cls.save_converted_session(
                    star_name=body.get("star", ""),
                    obscode=body.get("obscode", ""),
                    scope_model=body.get("scopeModel", "S50"),
                    file_name=body.get("fileName", "Seestar_AAVSO.csv"),
                    aavso_csv_content=body.get("content", ""),
                    points=body.get("points"),
                )
                self._send_json(res)
            elif action == "delete_converted_records":
                res = storage_service_cls.delete_converted_records(
                    star_name=body.get("star", ""),
                    file_name=body.get("fileName", ""),
                    obs_date=body.get("obsDate", ""),
                )
                self._send_json(res)
            elif action == "reset_all_user_data":
                res = storage_service_cls.reset_all_user_data()
                self._send_json(res)
            elif action == "get_converted_history":
                res = storage_service_cls.get_converted_history(body.get("star"))
                self._send_json(res)
            elif action == "fetch_live_star_dossier":
                res = storage_service_cls.fetch_live_star_dossier(body.get("star", ""))
                self._send_json(res)
            elif action == "query_aavso_star":
                res = storage_service_cls.query_aavso_star(
                    star_name=body.get("star", ""),
                    scope_model=body.get("scopeModel", "S50"),
                    api_token=body.get("apiToken", ""),
                )
                self._send_json(res)
            elif action == "check_github_latest_release":
                res = storage_service_cls.check_github_latest_release(body.get("currentVersion") or app_version)
                self._send_json(res)
            elif action == "fetch_live_aavso_notices":
                res = storage_service_cls.fetch_live_aavso_notices()
                self._send_json(res)
            elif action == "fetch_live_aavso_campaign_targets":
                res = storage_service_cls.fetch_live_aavso_campaign_targets(
                    max_stars=int(body.get("maxStars", 25) or 25)
                )
                self._send_json(res)
            elif action == "fetch_aavso_target_tool_targets":
                res = storage_service_cls.fetch_aavso_target_tool_targets(
                    api_key=body.get("apiKey", ""),
                    obs_section=body.get("obsSection", "all"),
                )
                self._send_json(res)
            elif action == "fetch_aavso_light_curve":
                res = storage_service_cls.fetch_aavso_light_curve(
                    star_name=body.get("star", ""),
                    days_back=int(body.get("daysBack", 180) or 180),
                    api_token=body.get("apiToken", ""),
                    user_obscode=body.get("obscode", ""),
                )
                self._send_json(res)
            else:
                self._send_json({"ok": False, "error": f"Unknown action: {action}"}, 400)

    return _AstroLabBackendRequestHandler


def start_rpc_server(
    handler_cls: Any,
    diagnostic_logger_cls: Any,
    port: int = 18765,
    require_token: bool = True,
) -> Optional[ThreadingHTTPServer]:
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", port), handler_cls)
        srv.require_token = bool(require_token)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        return srv
    except Exception as exc:
        try:
            diagnostic_logger_cls.log_exception("RPC_START_ERR", f"Failed to bind local RPC port {port}", exc)
        except Exception:
            pass
        return None
