#!/usr/bin/env python3
"""Local HTTPS mock for Cyber Hunter patch CDN (g94na.update.easebar.com/patch_map)."""
from __future__ import annotations

import argparse
import json
import logging
import ssl
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
CERT_DIR = ROOT / "certs"
RESPONSES = ROOT / "responses"
LOG_DIR = ROOT / "logs"
HOSTNAME = "g94na.update.easebar.com"
DEFAULT_PROFILE = "ret_code_ok"


def list_profiles() -> list[str]:
    # npk_version.json is a dedicated endpoint body, not a /patch_map profile
    return sorted(p.stem for p in RESPONSES.glob("*.json") if p.stem != "npk_version")


def load_body(profile: str) -> tuple[bytes, str]:
    path = RESPONSES / f"{profile}.json"
    if not path.exists():
        raise FileNotFoundError(f"unknown profile {profile!r}; available: {', '.join(list_profiles())}")
    text = path.read_text(encoding="utf-8")
    # normalize JSON formatting for stable responses
    payload = json.dumps(json.loads(text), separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return payload, "application/json; charset=utf-8"


def load_npk_version() -> bytes:
    """VersionFetcher splits on NPK_VERSION_SEPARATOR ('##########') and uses data[1].

    Format that yields data[1] as the JSON dict:
      ##########\\n{...json...}
    """
    path = RESPONSES / "npk_version.json"
    if path.exists():
        payload = json.dumps(json.loads(path.read_text(encoding="utf-8")), separators=(",", ":"), ensure_ascii=False)
    else:
        # Match game/version so the client treats itself as up-to-date (no download).
        payload = json.dumps(
            {
                "client_version": "1.251560.230461.251560",
                "version": "1.251560.230461.251560",
                "engine_version": "1.251560.230461.251560",
                "force_update": 0,
                "review": 0,
            },
            separators=(",", ":"),
        )
    return ("##########\n" + payload).encode("utf-8")


class PatchHandler(BaseHTTPRequestHandler):
    server_version = "CyberHunterPatchMock/1.0"
    profile = DEFAULT_PROFILE
    # fetch_list splits the body on '\n' and treats the LAST line as the lvs
    # signature (dropped from the returned data). So the manifest JSON must be
    # followed by a signature line. lvs_validate is neutralized at runtime, so
    # the content of this line is irrelevant -- it just has to exist.
    sig_line = "local"

    def log_message(self, fmt: str, *args) -> None:
        logging.info("%s - %s", self.address_string(), fmt % args)

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.send_header("Server", self.server_version)
        self.end_headers()
        self.wfile.write(body)

    def _log_request(self) -> None:
        parsed = urlparse(self.path)
        sensitive = {"authorization", "cookie", "set-cookie", "x-admin-session", "x-owner-key", "x-api-key"}
        qs = {
            key: (["[REDACTED]"] if key.lower() in sensitive or "token" in key.lower() or "secret" in key.lower() else value)
            for key, value in parse_qs(parsed.query, keep_blank_values=True).items()
        }
        headers = {k: ("[REDACTED]" if k.lower() in sensitive else v) for k, v in self.headers.items()}
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "method": self.command,
            "path": parsed.path,
            "query": qs,
            "headers": headers,
            "client": self.client_address[0],
            "profile": self.profile,
        }
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOG_DIR / "requests.jsonl"
        with log_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        logging.info("REQUEST %s %s qs=%s profile=%s", self.command, parsed.path, qs, self.profile)

    def _proxy_admin(self, method: str, body: bytes = b"") -> bool:
        """Expose only the owner admin page through the existing TLS endpoint.

        The Node relay remains the authorization authority.  This small proxy
        exists because remote players already trust the patch endpoint on 443;
        it never proxies arbitrary paths or destinations.
        """
        parsed = urlparse(self.path)
        if not (parsed.path == "/admin" or parsed.path.startswith("/admin/")):
            return False
        try:
            import urllib.error
            import urllib.request
            url = "http://127.0.0.1:3000" + parsed.path
            if parsed.query:
                url += "?" + parsed.query
            headers = {
                "Content-Type": self.headers.get("Content-Type", "application/json"),
                "Authorization": self.headers.get("Authorization", ""),
                "X-Admin-Session": self.headers.get("X-Admin-Session", ""),
                "X-Owner-Key": self.headers.get("X-Owner-Key", ""),
                "X-Forwarded-Proto": "https",
                "X-Forwarded-For": str(self.client_address[0]),
            }
            req = urllib.request.Request(url, data=(body if method == "POST" else None), headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=12) as resp:
                    self._send(resp.status, resp.read(), resp.headers.get("Content-Type", "application/json"))
            except urllib.error.HTTPError as exc:
                self._send(exc.code, exc.read() or b'{"ok":false}', exc.headers.get("Content-Type", "application/json"))
            return True
        except Exception as exc:
            logging.error("admin proxy error: %s", exc)
            self._send(502, b'{"ok":false,"error":"admin unavailable"}', "application/json")
            return True

    def do_GET(self) -> None:
        self._log_request()
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path == "/admin" or path.startswith("/admin/"):
            self._proxy_admin("GET")
            return
        if path == "/patch_map":
            try:
                body, ctype = load_body(self.profile)
            except FileNotFoundError as exc:
                self._send(500, str(exc).encode("utf-8"), "text/plain; charset=utf-8")
                return
            if self.sig_line is not None:
                body = body + b"\n" + self.sig_line.encode("utf-8")
            logging.info("RESPONSE profile=%s body=%s", self.profile, body.decode("utf-8", "replace")[:500])
            self._send(200, body, ctype)
            return
        if path.startswith("/npk_version"):
            body = load_npk_version()
            logging.info("RESPONSE npk_version body=%s", body.decode("utf-8", "replace")[:500])
            self._send(200, body, "text/plain; charset=utf-8")
            return
        # server list / notice endpoints (fetch_server "Retrieving server info")
        if "serverlist" in path.lower() or path.endswith("/server.txt") or "server_list" in path.lower():
            sl = RESPONSES / "serverlist.txt"
            body = sl.read_bytes() if sl.exists() else b"127.0.0.1 10001 local\n"
            # same newline+sig convention as patch_map (fetch_list drops last line)
            if self.sig_line is not None:
                body = body.rstrip() + b"\n" + self.sig_line.encode("utf-8")
            logging.info("RESPONSE serverlist path=%s", path)
            self._send(200, body, "text/plain; charset=utf-8")
            return
        if "notice" in path.lower():
            body = b"[]\nlocal"
            self._send(200, body, "text/plain; charset=utf-8")
            return
        # UniSDK's Gas3 store query. The generic ok-body below has no
        # product_info_list at all, and the client logged
        #   [UniSDK][Error]query jf product list Failed !
        #   [UniSDK][Error]Gas3 ...product_info_list...
        # immediately before dying on a worker thread with a null read
        # (client.exe+0x6887EF, AV READ 0x000179B4) ~0.2s after lobby_ready.
        # Offline there is nothing to sell, so hand back a well-formed
        # response carrying an EMPTY list rather than no list.
        if "query_product" in path.lower():
            body = (b'{"ret_code":0,"code":0,"result":"ok","reason":"ok",'
                    b'"product_info_list":[]}')
            logging.info("RESPONSE query_product empty product_info_list")
            self._send(200, body, "application/json; charset=utf-8")
            return
        # everything else (dead SDK telemetry: drpf/applog/data-detect/mgbsdk) -> instant 200
        # so the client's blocking calls return immediately instead of hanging on a dead host.
        self._send(200, b'{"ret_code":0,"code":0,"result":"ok"}', "application/json; charset=utf-8")

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_POST(self) -> None:
        self._log_request()
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path == "/admin" or path.startswith("/admin/"):
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length) if length else b""
            except (ValueError, OSError):
                body = b""
            self._proxy_admin("POST", body)
            return
        if path == "/sync":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length) if length else b""
                import urllib.request
                req = urllib.request.Request(
                    "http://127.0.0.1:3000/sync",
                    data=body,
                    headers={
                        "Content-Type": self.headers.get("Content-Type", "application/json"),
                        "Authorization": self.headers.get("Authorization", ""),
                        "X-Forwarded-Proto": "https",
                        # Real player IP so the relay rate-limits per player,
                        # not everyone behind this proxy as 127.0.0.1.
                        "X-Forwarded-For": str(self.client_address[0]),
                    },
                    method="POST",
                )
                import urllib.error
                try:
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        resp_data = resp.read()
                        self._send(resp.status, resp_data, resp.headers.get("Content-Type", "application/json"))
                except urllib.error.HTTPError as he:
                    # Pass 403/404/429 through instead of turning them into 500s.
                    self._send(he.code, he.read() or b'{"ok":false}', "application/json")
                return
            except Exception as e:
                logging.error("patch_server sync proxy error: %s", e)
                self._send(500, json.dumps({"ok": False, "error": str(e)}).encode("utf-8"), "application/json")
                return

        try:
            length = int(self.headers.get("Content-Length", 0))
            if length:
                self.rfile.read(length)  # drain body so the socket closes cleanly
        except (ValueError, OSError):
            pass
        self._send(200, b'{"ret_code":0,"code":0,"result":"ok"}', "application/json; charset=utf-8")


def build_ssl_context() -> ssl.SSLContext:
    cert = CERT_DIR / "server.cert.pem"
    key = CERT_DIR / "server.key.pem"
    if not cert.exists() or not key.exists():
        raise FileNotFoundError(f"missing TLS files in {CERT_DIR}; run generate_certs.py first")
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(certfile=str(cert), keyfile=str(key))
    return ctx


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0", help="bind address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=443, help="bind port (default: 443, needs admin)")
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE,
        choices=list_profiles(),
        help=f"response body template (default: {DEFAULT_PROFILE})",
    )
    parser.add_argument(
        "--sig-line",
        default="local",
        help="append '<newline><value>' after the JSON so fetch_list has a signature line to drop",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    PatchHandler.profile = args.profile
    PatchHandler.sig_line = args.sig_line
    httpd = ThreadingHTTPServer((args.host, args.port), PatchHandler)
    httpd.socket = build_ssl_context().wrap_socket(httpd.socket, server_side=True)

    logging.info("serving https://%s:%s/patch_map profile=%s", HOSTNAME, args.port, args.profile)
    logging.info("profiles: %s", ", ".join(list_profiles()))
    logging.info("request log: %s", LOG_DIR / "requests.jsonl")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("stopped")
        return 0
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
