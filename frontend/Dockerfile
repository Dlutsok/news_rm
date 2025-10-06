# =============================================================================
# Оптимизированный Dockerfile для Next.js (multi-stage build)
# Ожидаемый размер: ~100-200MB вместо 1.77GB
# =============================================================================

# ============================
# STAGE 1: Dependencies
# ============================
FROM node:18-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Копируем только package files (теперь из frontend/)
COPY frontend/package*.json ./
RUN npm ci

# ============================
# STAGE 2: Builder
# ============================
FROM node:18-alpine AS builder
WORKDIR /app

# Копируем зависимости из предыдущего stage
COPY --from=deps /app/node_modules ./node_modules

# Копируем исходный код из frontend/ (включая public)
COPY frontend/ .

# Настройка для standalone сборки
ENV NEXT_TELEMETRY_DISABLED 1

# Build-time аргументы для встраивания в код
ARG NEXT_PUBLIC_API_URL=https://admin.news.rmevent.ru
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Собираем приложение
RUN npm run build

# ============================
# STAGE 3: Runner (финальный образ)
# ============================
FROM node:18-alpine AS runner
WORKDIR /app

# Добавляем curl для healthcheck
RUN apk add --no-cache curl

# Создаем пользователя для безопасности
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Копируем standalone сборку
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Копируем public файлы из корня context (теперь context = корень репо)
COPY --chown=nextjs:nodejs frontend/public ./public

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Запуск
CMD ["node", "server.js"]
