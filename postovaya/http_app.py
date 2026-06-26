import base64
import io
import json
import os
import zipfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .openai_service import generate_post, generation_provider, research_venue
from .prompts import get_editable_prompt_templates, update_editable_prompt_template


ROOT = Path(__file__).resolve().parent.parent


def load_vpn_config():
    encoded = os.environ.get("VPN_BOX_OVPN_B64", "").strip()
    if encoded:
        try:
            return base64.b64decode(encoded).decode("utf-8")
        except Exception as error:
            raise RuntimeError("VPN_BOX_OVPN_B64 is invalid.") from error

    config_path = os.environ.get("VPN_BOX_OVPN_PATH", "").strip()
    if config_path:
        path = Path(config_path).expanduser()
        if not path.exists():
            raise RuntimeError(f"VPN config path not found: {path}")
        return path.read_text(encoding="utf-8")

    fallback = Path("/Users/kaban/codex/Sources/client1.ovpn")
    if fallback.exists():
        return fallback.read_text(encoding="utf-8")

    raise RuntimeError(
        "VPN config is not configured. Set VPN_BOX_OVPN_B64 or VPN_BOX_OVPN_PATH."
    )


def build_box_archive(platform):
    config = load_vpn_config()
    archive_name = f"vpn-box-{platform}.zip"
    script_name = "install.bat" if platform == "windows" else "install.command"
    script_body = (
        "@echo off\r\n"
        "setlocal\r\n"
        "set \"BOX_DIR=%~dp0\"\r\n"
        "if not exist \"%BOX_DIR%vpn-box\" mkdir \"%BOX_DIR%vpn-box\"\r\n"
        "copy /Y \"%BOX_DIR%vpn-box.ovpn\" \"%BOX_DIR%vpn-box\\vpn-box.ovpn\" >nul\r\n"
        "start \"\" \"%BOX_DIR%vpn-box\\vpn-box.ovpn\"\r\n"
    ) if platform == "windows" else (
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "DIR=\"$(cd \"$(dirname \"$0\")\" && pwd)\"\n"
        "mkdir -p \"$DIR/vpn-box\"\n"
        "cp \"$DIR/vpn-box.ovpn\" \"$DIR/vpn-box/vpn-box.ovpn\"\n"
        "open \"$DIR/vpn-box/vpn-box.ovpn\"\n"
    )

    readme = (
        "VPN Box\n\n"
        "1. Unzip this archive.\n"
        "2. Open install.bat / install.command.\n"
        "3. The VPN profile will be opened in your default client.\n"
        "4. If the system has no VPN client yet, install OpenVPN Connect once and run the script again.\n"
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        readme_info = zipfile.ZipInfo("README.txt")
        readme_info.external_attr = 0o644 << 16
        archive.writestr(readme_info, readme)

        config_info = zipfile.ZipInfo("vpn-box.ovpn")
        config_info.external_attr = 0o600 << 16
        archive.writestr(config_info, config)

        script_info = zipfile.ZipInfo(script_name)
        script_info.external_attr = (0o755 if platform != "windows" else 0o644) << 16
        archive.writestr(script_info, script_body)
    buffer.seek(0)
    return archive_name, buffer.read()


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

    def _send_download_headers(self, platform):
        try:
            archive_name, payload = build_box_archive(platform)
        except RuntimeError as error:
            self.send_json(503, {"error": str(error)})
            return None
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Disposition", f'attachment; filename="{archive_name}"')
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        return payload

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
        if self.path in ("/download/windows", "/download/mac"):
            platform = "windows" if self.path.endswith("windows") else "mac"
            payload = self._send_download_headers(platform)
            if payload is None:
                return
            self.wfile.write(payload)
            return
        if self.path == "/api/prompts":
            self.send_json(200, get_editable_prompt_templates())
            return
        super().do_GET()

    def do_HEAD(self):
        if self.path in ("/download/windows", "/download/mac"):
            platform = "windows" if self.path.endswith("windows") else "mac"
            if self._send_download_headers(platform) is None:
                return
            return
        super().do_HEAD()

    def do_POST(self):
        handlers = {
            "/api/generate": generate_post,
            "/api/prompts": update_editable_prompt_template,
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
