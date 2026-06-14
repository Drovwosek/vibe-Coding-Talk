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

CMD ["python", "server.py"]
