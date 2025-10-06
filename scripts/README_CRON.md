# Автоматическая публикация новостей через Cron

Этот скрипт обеспечивает автоматическую публикацию запланированных новостей каждую минуту.

## Компоненты

1. **publish_scheduled_news.py** - Python скрипт, который обрабатывает запланированные публикации
2. **cron_publish_news.sh** - Bash обёртка для запуска в Docker контейнере
3. **medical-news-publisher.service** - Systemd service
4. **medical-news-publisher.timer** - Systemd timer (запускается каждую минуту)

## Установка на сервере

### Вариант 1: Через systemd timer (рекомендуется)

```bash
# 1. Создать директорию для скриптов
mkdir -p /root/scripts
mkdir -p /root/logs

# 2. Скопировать скрипт на сервер
scp scripts/cron_publish_news.sh root@176.124.219.201:/root/scripts/
scp scripts/publish_scheduled_news.py root@176.124.219.201:/root/scripts/

# 3. Дать права на выполнение
ssh root@176.124.219.201 "chmod +x /root/scripts/cron_publish_news.sh"

# 4. Установить systemd service и timer
scp scripts/medical-news-publisher.service root@176.124.219.201:/etc/systemd/system/
scp scripts/medical-news-publisher.timer root@176.124.219.201:/etc/systemd/system/

# 5. Включить и запустить timer
ssh root@176.124.219.201 "systemctl daemon-reload && \
    systemctl enable medical-news-publisher.timer && \
    systemctl start medical-news-publisher.timer"

# 6. Проверить статус
ssh root@176.124.219.201 "systemctl status medical-news-publisher.timer"
ssh root@176.124.219.201 "systemctl list-timers medical-news-publisher.timer"
```

### Вариант 2: Через crontab (альтернатива)

```bash
# 1. Создать директорию для скриптов
mkdir -p /root/scripts
mkdir -p /root/logs

# 2. Скопировать скрипт
scp scripts/cron_publish_news.sh root@176.124.219.201:/root/scripts/
scp scripts/publish_scheduled_news.py root@176.124.219.201:/root/scripts/

# 3. Дать права на выполнение
chmod +x /root/scripts/cron_publish_news.sh

# 4. Добавить в crontab
crontab -e

# Добавить строку:
* * * * * /root/scripts/cron_publish_news.sh
```

## Скрипт должен быть скопирован в контейнер

Скрипт `publish_scheduled_news.py` должен быть доступен внутри backend контейнера по пути `/app/scripts/publish_scheduled_news.py`.

Это делается автоматически при сборке образа, так как `scripts/` директория копируется в Dockerfile.

## Проверка работы

```bash
# Проверить логи
tail -f /root/logs/publication_cron.log

# Проверить последний запуск (для systemd)
journalctl -u medical-news-publisher.service -n 50

# Ручной запуск для теста
/root/scripts/cron_publish_news.sh

# Или прямо в контейнере
docker exec medical-news-backend python3 /app/scripts/publish_scheduled_news.py
```

## Отладка

Если публикация не работает:

1. Проверьте что контейнер запущен:
   ```bash
   docker ps | grep medical-news-backend
   ```

2. Проверьте наличие скрипта в контейнере:
   ```bash
   docker exec medical-news-backend ls -la /app/scripts/
   ```

3. Проверьте логи:
   ```bash
   tail -100 /root/logs/publication_cron.log
   ```

4. Запустите вручную для отладки:
   ```bash
   docker exec -it medical-news-backend python3 /app/scripts/publish_scheduled_news.py
   ```

## Остановка

### Для systemd:
```bash
systemctl stop medical-news-publisher.timer
systemctl disable medical-news-publisher.timer
```

### Для cron:
```bash
crontab -e
# Удалить или закомментировать строку с /root/scripts/cron_publish_news.sh
```
