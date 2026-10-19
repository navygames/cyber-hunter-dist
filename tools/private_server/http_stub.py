#!/usr/bin/env python3
"""Plain HTTP stub on :80 for NeoX dials that hit hardcoded NetEase IPs (not hostnames)."""
from __future__ import annotations

import argparse
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class OkHandler(BaseHTTPRequestHandler):
    server_version = "CyberHunterHttpStub/1.0"

    def log_message(self, fmt: str, *args) -> None:
        logging.info("%s - %s", self.address_string(), fmt % args)

    def _ok(self) -> None:
        body = b'{"ret_code":0,"code":0,"result":"ok"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        logging.info("GET %s", self.path)
        self._ok()

    def do_POST(self) -> None:
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n:
                self.rfile.read(n)
        except (ValueError, OSError):
            pass
        logging.info("POST %s", self.path)
        self._ok()

    def do_HEAD(self) -> None:
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=80)
    p.add_argument("-v", action="store_true")
    args = p.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.v else logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    httpd = ThreadingHTTPServer((args.host, args.port), OkHandler)
    logging.info("HTTP stub listening on %s:%s", args.host, args.port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
