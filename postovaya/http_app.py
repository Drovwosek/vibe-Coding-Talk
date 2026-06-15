import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .openai_service import generate_post, generation_provider, research_venue


ROOT = Path(__file__).resolve().parent.parent


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "web"), **kwargs)

    def log_message(self, format_string, *args):
        print("[%s] %s" % (self.log_date_time_string(), format_string % args))

    def send_json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/api/health":
            provider = generation_provider()
            self.send_json(200, {
                "ok": True,
                "aiConfigured": bool(provider["key"]),
                "provider": provider["name"] if provider["key"] else None,
                "model": provider["model"] if provider["key"] else None,
                "researchConfigured": bool(os.environ.get("OPENAI_API_KEY", "").strip()),
            })
            return
        super().do_GET()

    def do_POST(self):
        handlers = {
            "/api/generate": generate_post,
            "/api/research-venue": research_venue,
        }
        handler = handlers.get(self.path)
        if not handler:
            self.send_json(404, {"error": "Маршрут не найден."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 100_000:
                raise ValueError("Некорректный размер запроса.")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            self.send_json(200, handler(payload))
        except (ValueError, json.JSONDecodeError) as error:
            self.send_json(400, {"error": str(error)})
        except RuntimeError as error:
            self.send_json(502, {"error": str(error)})
        except Exception:
            self.send_json(500, {"error": "Внутренняя ошибка сервера."})


def run():
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8765"))
    provider = generation_provider()
    server = ThreadingHTTPServer((host, port), AppHandler)
    print("Telegram Post Studio: http://%s:%s" % (host, port))
    print("AI mode: %s" % (provider["name"].title() if provider["key"] else "demo"))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
