# Руководство по обслуживанию системы

## Обзор

Данное руководство содержит процедуры для ежедневного, еженедельного и ежемесячного обслуживания системы медицинских новостей, а также инструкции по устранению неполадок и аварийному восстановлению.

## Ежедневные задачи

### 1. Проверка состояния системы
Выполняется автоматически через мониторинг, но рекомендуется ручная проверка:

```bash
# Проверка статуса всех сервисов
sudo systemctl status medapp-backend medapp-frontend nginx postgresql

# Проверка использования ресурсов
htop
df -h
free -h

# Проверка логов за последний час
sudo journalctl --since "1 hour ago" | grep -E "(ERROR|CRITICAL|Failed)"
```

### 2. Проверка парсинга новостей
```bash
# Проверка последних сессий парсинга
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/news/parse-sessions?limit=5

# Проверка статистики источников
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/news/stats
```

### 3. Мониторинг расходов AI
```bash
# Проверка расходов за сегодня
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/expenses/summary?period=day

# Проверка использования AI
grep "OpenAI" /var/log/medapp/backend.log | tail -20
```

### 4. Проверка размера базы данных
```bash
# Размер PostgreSQL БД
sudo -u postgres psql -c "
SELECT pg_size_pretty(pg_database_size('medapp_db')) as size;
"

# Количество записей в основных таблицах
sudo -u postgres psql medapp_db -c "
SELECT
    'articles' as table_name, COUNT(*) as count FROM articles
UNION ALL
SELECT
    'news_generation_drafts', COUNT(*) FROM news_generation_drafts
UNION ALL
SELECT
    'expenses', COUNT(*) FROM expenses;
"
```

## Еженедельные задачи

### 1. Проверка и очистка логов
```bash
# Размер логов
sudo du -sh /var/log/nginx/
sudo du -sh /var/log/medapp/
sudo journalctl --disk-usage

# Очистка старых логов (старше 30 дней)
sudo find /var/log/nginx/ -name "*.log.*" -mtime +30 -delete
sudo find /var/log/medapp/ -name "*.log.*" -mtime +30 -delete

# Очистка journal логов (оставить последние 7 дней)
sudo journalctl --vacuum-time=7d
```

### 2. Анализ производительности
```bash
# Проверка медленных запросов PostgreSQL
sudo -u postgres psql medapp_db -c "
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
"

# Анализ логов Nginx для медленных запросов
sudo awk '$10 > 5.0 {print $0}' /var/log/nginx/medapp_access.log | tail -20

# Проверка размера таблиц БД
sudo -u postgres psql medapp_db -c "
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::regclass) DESC;
"
```

### 3. Обновление зависимостей
```bash
cd /opt/medapp

# Проверка обновлений Python пакетов
cd backend
source venv/bin/activate
pip list --outdated

# Проверка обновлений Node.js пакетов
cd ../frontend
npm outdated

# Обновление системных пакетов
sudo apt update
sudo apt list --upgradable
```

### 4. Проверка SSL сертификатов
```bash
# Проверка срока действия
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates

# Автоматическое обновление (тест)
sudo certbot renew --dry-run
```

## Ежемесячные задачи

### 1. Глубокий анализ производительности
```bash
#!/bin/bash
# monthly_performance_check.sh

echo "=== Monthly Performance Report $(date) ===" > /tmp/performance_report.txt

# Статистика использования ресурсов
echo "CPU and Memory usage:" >> /tmp/performance_report.txt
top -bn1 | grep -E "(Cpu|Mem)" >> /tmp/performance_report.txt

# Статистика БД
echo -e "\nDatabase statistics:" >> /tmp/performance_report.txt
sudo -u postgres psql medapp_db -c "
SELECT
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size
FROM pg_stat_user_tables
ORDER BY n_tup_ins DESC;
" >> /tmp/performance_report.txt

# Статистика парсинга
echo -e "\nParsing statistics (last 30 days):" >> /tmp/performance_report.txt
sudo -u postgres psql medapp_db -c "
SELECT
    source_site,
    COUNT(*) as sessions,
    AVG(parsed_articles) as avg_parsed,
    AVG(duration_seconds) as avg_duration
FROM parse_sessions
WHERE started_at > NOW() - INTERVAL '30 days'
GROUP BY source_site;
" >> /tmp/performance_report.txt

# Отправка отчета (настроить email)
# mail -s "Monthly Performance Report" admin@yourdomain.com < /tmp/performance_report.txt
```

### 2. Архивирование старых данных
```bash
#!/bin/bash
# archive_old_data.sh

# Архивирование статей старше 6 месяцев
ARCHIVE_DATE=$(date -d "6 months ago" +%Y-%m-%d)

echo "Archiving articles older than $ARCHIVE_DATE"

# Экспорт старых статей
sudo -u postgres pg_dump medapp_db \
    --table=articles \
    --where="created_at < '$ARCHIVE_DATE'" \
    --data-only > /opt/backups/medapp/archived_articles_$(date +%Y%m).sql

# Подсчет записей для архивирования
OLD_ARTICLES=$(sudo -u postgres psql medapp_db -t -c "
SELECT COUNT(*) FROM articles WHERE created_at < '$ARCHIVE_DATE';
")

echo "Found $OLD_ARTICLES articles to archive"

# Удаление старых записей (раскомментировать после проверки)
# sudo -u postgres psql medapp_db -c "
# DELETE FROM articles WHERE created_at < '$ARCHIVE_DATE';
# "

# Очистка старых логов генерации (старше 3 месяцев)
sudo -u postgres psql medapp_db -c "
DELETE FROM generation_logs
WHERE created_at < NOW() - INTERVAL '3 months';
"

# Вакуум таблиц после удаления
sudo -u postgres psql medapp_db -c "VACUUM ANALYZE;"
```

### 3. Проверка безопасности
```bash
#!/bin/bash
# security_check.sh

echo "=== Security Check $(date) ===" > /tmp/security_report.txt

# Проверка открытых портов
echo "Open ports:" >> /tmp/security_report.txt
sudo netstat -tlnp | grep LISTEN >> /tmp/security_report.txt

# Проверка неудачных попыток входа
echo -e "\nFailed login attempts:" >> /tmp/security_report.txt
sudo grep "Failed password" /var/log/auth.log | tail -10 >> /tmp/security_report.txt

# Проверка активности fail2ban
echo -e "\nFail2ban status:" >> /tmp/security_report.txt
sudo fail2ban-client status >> /tmp/security_report.txt

# Проверка SSL сертификата
echo -e "\nSSL certificate expiry:" >> /tmp/security_report.txt
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates >> /tmp/security_report.txt

# Проверка обновлений безопасности
echo -e "\nSecurity updates available:" >> /tmp/security_report.txt
sudo apt list --upgradable | grep -i security >> /tmp/security_report.txt
```

## Процедуры восстановления

### 1. Восстановление из резервной копии

#### Восстановление базы данных
```bash
# Остановка приложения
sudo systemctl stop medapp-backend medapp-frontend

# Создание текущего бэкапа (на всякий случай)
sudo -u postgres pg_dump medapp_db > /tmp/current_backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление из бэкапа
sudo -u postgres dropdb medapp_db
sudo -u postgres createdb medapp_db -O medapp_user
sudo -u postgres psql medapp_db < /opt/backups/medapp/db_backup_YYYYMMDD_HHMMSS.sql

# Проверка восстановления
sudo -u postgres psql medapp_db -c "SELECT COUNT(*) FROM articles;"

# Запуск приложения
sudo systemctl start medapp-backend medapp-frontend
```

#### Восстановление файлов приложения
```bash
# Остановка сервисов
sudo systemctl stop medapp-backend medapp-frontend

# Создание резервной копии текущего состояния
sudo mv /opt/medapp /opt/medapp_broken_$(date +%Y%m%d_%H%M%S)

# Восстановление из архива
cd /opt
sudo tar -xzf /opt/backups/medapp/app_backup_YYYYMMDD_HHMMSS.tar.gz

# Восстановление прав доступа
sudo chown -R medapp:medapp /opt/medapp

# Запуск сервисов
sudo systemctl start medapp-backend medapp-frontend

# Проверка работоспособности
curl http://localhost:8000/health
curl http://localhost:3000
```

### 2. Аварийный перезапуск системы

#### Полный перезапуск всех компонентов
```bash
#!/bin/bash
# emergency_restart.sh

echo "Emergency restart initiated at $(date)"

# Остановка всех сервисов
sudo systemctl stop medapp-frontend
sudo systemctl stop medapp-backend
sudo systemctl stop nginx

# Проверка и очистка процессов
sudo pkill -f "uvicorn"
sudo pkill -f "node.*next"

# Проверка портов
while sudo netstat -tlnp | grep -E ":8000|:3000" > /dev/null; do
    echo "Waiting for ports to be released..."
    sleep 2
done

# Запуск сервисов
sudo systemctl start postgresql
sleep 5
sudo systemctl start medapp-backend
sleep 10
sudo systemctl start medapp-frontend
sleep 5
sudo systemctl start nginx

# Проверка статуса
echo "Service status:"
sudo systemctl status postgresql medapp-backend medapp-frontend nginx

# Проверка доступности
echo "Health checks:"
curl -f http://localhost:8000/health && echo "Backend: OK" || echo "Backend: FAILED"
curl -f http://localhost:3000 && echo "Frontend: OK" || echo "Frontend: FAILED"
```

#### Восстановление после сбоя диска
```bash
# 1. Проверка файловой системы
sudo fsck /dev/sda1

# 2. Монтирование и проверка
sudo mount /dev/sda1 /mnt/recovery
ls -la /mnt/recovery/opt/medapp

# 3. Восстановление критических данных
sudo rsync -av /mnt/recovery/opt/medapp/ /opt/medapp/

# 4. Восстановление БД из последнего бэкапа
# (см. раздел восстановления БД выше)
```

## Процедуры обновления

### 1. Минорное обновление приложения
```bash
#!/bin/bash
# minor_update.sh

echo "Starting minor update at $(date)"

# Создание точки восстановления
cd /opt/medapp
git stash
sudo systemctl stop medapp-backend medapp-frontend

# Создание бэкапа БД
sudo -u postgres pg_dump medapp_db > /tmp/pre_update_backup_$(date +%Y%m%d_%H%M%S).sql

# Получение обновлений
git pull origin main

# Обновление Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Применение миграций БД (если есть)
# python migrate.py

# Обновление Frontend
cd ../frontend
npm ci --only=production
npm run build

# Запуск сервисов
sudo systemctl start medapp-backend
sleep 10
sudo systemctl start medapp-frontend

# Проверка работоспособности
if curl -f http://localhost:8000/health && curl -f http://localhost:3000; then
    echo "Update completed successfully"
    git stash drop
else
    echo "Update failed, rolling back..."
    git stash pop
    sudo systemctl restart medapp-backend medapp-frontend
fi
```

### 2. Мажорное обновление с даунтаймом
```bash
#!/bin/bash
# major_update.sh

echo "Starting major update with planned downtime"

# Настройка страницы обслуживания
sudo cp /opt/medapp/maintenance.html /var/www/html/
sudo systemctl stop medapp-frontend

# Полный бэкап системы
sudo -u postgres pg_dump medapp_db > /opt/backups/medapp/major_update_backup_$(date +%Y%m%d_%H%M%S).sql
sudo tar -czf /opt/backups/medapp/app_major_backup_$(date +%Y%m%d_%H%M%S).tar.gz /opt/medapp

# Остановка Backend
sudo systemctl stop medapp-backend

# Обновление системных зависимостей
sudo apt update && sudo apt upgrade -y

# Обновление приложения
cd /opt/medapp
git checkout main
git pull origin main

# Обновление Backend зависимостей
cd backend
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Применение миграций
python migrate.py

# Обновление Frontend
cd ../frontend
rm -rf node_modules
npm install
npm run build

# Запуск и проверка
sudo systemctl start medapp-backend
sleep 15
sudo systemctl start medapp-frontend
sleep 10

# Проверка и восстановление трафика
if curl -f http://localhost:8000/health && curl -f http://localhost:3000; then
    echo "Major update completed successfully"
    sudo rm /var/www/html/maintenance.html
else
    echo "Major update failed, manual intervention required"
fi
```

## Мониторинг и алерты

### 1. Настройка системного мониторинга
```bash
# Установка и настройка монитора дискового пространства
cat > /opt/medapp/scripts/disk_monitor.sh << 'EOF'
#!/bin/bash

THRESHOLD=80
USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')

if [ $USAGE -gt $THRESHOLD ]; then
    echo "ALERT: Disk usage is ${USAGE}% - exceeds threshold of ${THRESHOLD}%"
    # Отправка уведомления
    # curl -X POST "your-webhook-url" -d "Disk usage alert: ${USAGE}%"
fi
EOF

chmod +x /opt/medapp/scripts/disk_monitor.sh

# Добавление в cron (каждые 15 минут)
echo "*/15 * * * * /opt/medapp/scripts/disk_monitor.sh" | crontab -
```

### 2. Мониторинг производительности API
```bash
# Скрипт проверки времени ответа API
cat > /opt/medapp/scripts/api_monitor.sh << 'EOF'
#!/bin/bash

API_URL="http://localhost:8000/health"
THRESHOLD=5  # секунды

RESPONSE_TIME=$(curl -w "%{time_total}" -s -o /dev/null $API_URL)

if (( $(echo "$RESPONSE_TIME > $THRESHOLD" | bc -l) )); then
    echo "ALERT: API response time is ${RESPONSE_TIME}s - exceeds threshold of ${THRESHOLD}s"
    # Отправка уведомления
fi
EOF

chmod +x /opt/medapp/scripts/api_monitor.sh

# Добавление в cron (каждые 5 минут)
echo "*/5 * * * * /opt/medapp/scripts/api_monitor.sh" | crontab -
```

### 3. Мониторинг ошибок в логах
```bash
# Скрипт мониторинга ошибок
cat > /opt/medapp/scripts/error_monitor.sh << 'EOF'
#!/bin/bash

ERROR_COUNT=$(sudo journalctl -u medapp-backend --since "5 minutes ago" | grep -c ERROR)

if [ $ERROR_COUNT -gt 5 ]; then
    echo "ALERT: ${ERROR_COUNT} errors detected in backend logs in last 5 minutes"
    # Отправка детальной информации
    sudo journalctl -u medapp-backend --since "5 minutes ago" | grep ERROR | tail -5
fi
EOF

chmod +x /opt/medapp/scripts/error_monitor.sh
```

## Процедуры очистки

### 1. Очистка временных файлов
```bash
#!/bin/bash
# cleanup_temp_files.sh

# Очистка временных файлов Python
find /opt/medapp/backend -name "*.pyc" -delete
find /opt/medapp/backend -name "__pycache__" -type d -exec rm -rf {} +

# Очистка кэша npm
cd /opt/medapp/frontend
npm cache clean --force

# Очистка логов развертывания
find /tmp -name "*medapp*" -mtime +7 -delete

# Очистка старых архивов
find /opt/backups/medapp -name "*.tar.gz" -mtime +30 -delete
find /opt/backups/medapp -name "*.sql" -mtime +30 -delete

echo "Cleanup completed at $(date)"
```

### 2. Оптимизация базы данных
```bash
#!/bin/bash
# optimize_database.sh

echo "Starting database optimization at $(date)"

# Анализ и вакуум всех таблиц
sudo -u postgres psql medapp_db -c "VACUUM ANALYZE;"

# Переиндексация для оптимизации
sudo -u postgres psql medapp_db -c "REINDEX DATABASE medapp_db;"

# Обновление статистики планировщика
sudo -u postgres psql medapp_db -c "ANALYZE;"

# Проверка фрагментации
sudo -u postgres psql medapp_db -c "
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size,
    n_dead_tup,
    n_live_tup,
    CASE
        WHEN n_live_tup > 0
        THEN round((n_dead_tup::float / n_live_tup::float) * 100, 2)
        ELSE 0
    END as dead_ratio
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY dead_ratio DESC;
"

echo "Database optimization completed at $(date)"
```

## Контрольные списки

### Еженедельный чек-лист
- [ ] Проверить статус всех сервисов
- [ ] Проверить использование диска (< 80%)
- [ ] Проверить размер логов
- [ ] Очистить старые логи
- [ ] Проверить SSL сертификат (срок действия)
- [ ] Проверить бэкапы (последний успешный)
- [ ] Проверить статистику парсинга
- [ ] Проверить расходы AI
- [ ] Проверить производительность БД
- [ ] Обновить системные пакеты (security updates)

### Ежемесячный чек-лист
- [ ] Создать отчет производительности
- [ ] Архивировать старые данные
- [ ] Провести security audit
- [ ] Обновить зависимости приложения
- [ ] Проверить планы бэкапа
- [ ] Оптимизировать базу данных
- [ ] Проверить мониторинг и алерты
- [ ] Обновить документацию
- [ ] Провести disaster recovery тест
- [ ] Проанализировать capacity planning

### Чек-лист перед обновлением
- [ ] Создать полный бэкап системы
- [ ] Создать бэкап БД
- [ ] Проверить статус всех сервисов
- [ ] Протестировать обновление в staging
- [ ] Запланировать окно обслуживания
- [ ] Подготовить план отката
- [ ] Уведомить пользователей
- [ ] Подготовить процедуры проверки
- [ ] Иметь контакты для экстренной связи

Это руководство должно регулярно обновляться на основе опыта эксплуатации системы и новых требований.