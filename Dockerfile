FROM python:3.12-slim

ENV HOST=0.0.0.0 \
    PORT=8080 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY postovaya ./postovaya
COPY web ./web
COPY server.py ./server.py

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import json, urllib.request; assert json.load(urllib.request.urlopen('http://127.0.0.1:8080/api/health'))['ok']"

CMD ["python", "server.py"]
