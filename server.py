#!/usr/bin/env python3
"""Static presentation server for the Timeweb deployment."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import os


ROOT = Path(__file__).resolve().parent


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _is_health_request(self):
        path = self.path.split("?", 1)[0].rstrip("/")
        return path == "/api/health"

    def log_message(self, format_string, *args):
        print("[%s] %s" % (self.log_date_time_string(), format_string % args))

    def do_GET(self):
        if self._is_health_request():
            payload = json.dumps({"ok": True}, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)
            return
        super().do_GET()

    def do_HEAD(self):
        if self._is_health_request():
            payload = b'{"ok":true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        super().do_HEAD()


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
