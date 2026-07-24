FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY netprobe ./netprobe

RUN pip install --no-cache-dir .

ENTRYPOINT ["netprobe"]
CMD ["diagnose", "--target", "http://nginx:8080", "--prometheus-url", "http://prometheus:9090"]
