# Import Checks

- Backend code uses only the Python standard library unless a dependency is explicitly introduced and documented.
- Keep server.py as a compatibility entry point; do not move application logic into it.
- Use relative imports inside postovaya: from .prompts import ...
- Avoid importing http_app from service modules. Routing depends on services, services should not depend on routing.
- Frontend modules should be loaded through web/index.html and attach exports to window.Postovaya.
- Do not mix ES module imports with the current IIFE browser modules unless the whole frontend module strategy is changed deliberately.
