# Python API Handler

Pattern: keep HTTP routing thin. AppHandler should parse the request, delegate business logic to postovaya.* functions, and translate known exceptions into JSON responses.

~~~python
class AppHandler(SimpleHTTPRequestHandler):
    def send_json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

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
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            self.send_json(200, handler(payload))
        except ValueError as error:
            self.send_json(400, {"error": str(error)})
~~~

Use this shape for new JSON endpoints: route table, bounded input parsing, delegated handler, localized user-facing errors.
