#!/usr/bin/env python3
"""Static presentation server for the Timeweb deployment."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import mimetypes
import os


ROOT = Path(__file__).resolve().parent


class AppHandler(BaseHTTPRequestHandler):
    server_version = "VibeCodingTalk/1.0"

    def _is_health_request(self):
        path = self.path.split("?", 1)[0].rstrip("/")
        return path == "/api/health"

    def _resolve_path(self):
        path = self.path.split("?", 1)[0]
        if path in ("", "/"):
            path = "/index.html"
        if path.endswith("/"):
            path = path + "index.html"
        resolved = (ROOT / path.lstrip("/")).resolve()
        if ROOT not in resolved.parents and resolved != ROOT:
            return None
        return resolved

    def _send_bytes(self, status, content_type, payload):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def _send_file(self, path):
        if path is None or not path.exists() or not path.is_file():
            return False
        payload = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self._send_bytes(200, content_type, payload)
        return True

    def log_message(self, format_string, *args):
        print("[%s] %s" % (self.log_date_time_string(), format_string % args))

    def do_GET(self):
        if self._is_health_request():
            payload = json.dumps({"ok": True}, ensure_ascii=False).encode("utf-8")
            self._send_bytes(200, "application/json; charset=utf-8", payload)
            return
        if self.path.split("?", 1)[0] in ("/", "/index.html"):
            if self._send_file(ROOT / "index.html"):
                return
        resolved = self._resolve_path()
        if resolved and self._send_file(resolved):
            return
        self._send_file(ROOT / "index.html")

    def do_HEAD(self):
        if self._is_health_request():
            payload = b'{"ok":true}'
            self._send_bytes(200, "application/json; charset=utf-8", payload)
            return
        if self.path.split("?", 1)[0] in ("/", "/index.html"):
            if self._send_file(ROOT / "index.html"):
                return
        resolved = self._resolve_path()
        if resolved and self._send_file(resolved):
            return
        self._send_file(ROOT / "index.html")


def run():
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer((host, port), AppHandler)
    print("Presentation: http://%s:%s" % (host, port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
