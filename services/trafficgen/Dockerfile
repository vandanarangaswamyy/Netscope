FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir fastapi httpx prometheus-client pydantic-settings "uvicorn[standard]"

COPY services/trafficgen/trafficgen ./trafficgen

EXPOSE 9000

CMD ["uvicorn", "trafficgen.main:app", "--host", "0.0.0.0", "--port", "9000"]
