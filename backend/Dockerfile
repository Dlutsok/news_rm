# =============================================================================
# Оптимизированный Dockerfile для FastAPI Backend
# Ожидаемый размер: ~300-400MB вместо 724MB
# =============================================================================

# ============================
# STAGE 1: Builder
# ============================
FROM python:3.11-slim as builder

WORKDIR /app

# Устанавливаем только необходимые системные зависимости для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements и устанавливаем зависимости в отдельную директорию
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================
# STAGE 2: Runtime (финальный образ)
# ============================
FROM python:3.11-slim

WORKDIR /app

# Устанавливаем только runtime зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Копируем установленные Python пакеты из builder stage
COPY --from=builder /root/.local /root/.local

# Добавляем локальные пакеты в PATH
ENV PATH=/root/.local/bin:$PATH

# Копируем код приложения (без ненужных файлов)
COPY --chown=root:root . .

# Создаем директории для логов и storage
RUN mkdir -p /app/logs /app/storage/images /app/chat_service/data

# Копируем и делаем исполнимыми скрипты
COPY entrypoint.sh /entrypoint.sh
COPY wait-for-db.sh /wait-for-db.sh
RUN chmod +x /entrypoint.sh /wait-for-db.sh

# Очищаем ненужные файлы
RUN find . -type f -name "*.pyc" -delete \
    && find . -type d -name "__pycache__" -delete \
    && rm -rf /tmp/* /var/tmp/*

# Открываем порт
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Точка входа
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
