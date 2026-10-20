# Образ приложения «Генератор случайных чисел» (FastAPI + PostgreSQL)
FROM python:3.13-alpine

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    APP_ENV=docker

# Сначала только зависимости: этот слой кешируется и пересобирается, лишь когда меняется requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Приложение работает не от root
RUN adduser -D -H -u 10001 appuser
USER 10001

EXPOSE 8000
CMD ["python", "-m", "app"]
