#!/bin/bash
#
# Setup Git Hook for Auto-Deploy
# Настройка git hook на продакшн сервере
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Git Auto-Deploy Hook Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Проверка что мы на сервере
if [ ! -d ".git" ]; then
    echo -e "${RED}Ошибка: Не найдена .git директория${NC}"
    echo "Запустите этот скрипт из корня git репозитория на продакшн сервере"
    exit 1
fi

# Метод 1: Git Hook (post-receive для bare repo или post-merge для обычного)
echo -e "${YELLOW}[1/3] Настройка Git Hook...${NC}"

# Определяем тип репозитория
if [ -f ".git/config" ]; then
    # Обычный репозиторий - используем post-merge
    HOOK_FILE=".git/hooks/post-merge"

    cat > "$HOOK_FILE" << 'EOF'
#!/bin/bash
# Auto-deploy on git pull/merge

PROJECT_DIR="$(git rev-parse --show-toplevel)"
cd "$PROJECT_DIR"

echo "Git changes detected - triggering auto-deploy..."
./deployed/git-deploy.sh

EOF

    chmod +x "$HOOK_FILE"
    echo -e "${GREEN}✓ Post-merge hook установлен${NC}"
    echo "  Деплой будет запускаться после каждого git pull"
else
    echo -e "${YELLOW}⚠ Bare репозиторий не обнаружен${NC}"
fi

# Метод 2: Cron job для периодической проверки
echo ""
echo -e "${YELLOW}[2/3] Настройка Cron Job (опционально)...${NC}"
echo "Добавить автоматическую проверку обновлений каждые 5 минут? (y/n)"
read -r response

if [ "$response" = "y" ]; then
    PROJECT_DIR=$(pwd)
    CRON_JOB="*/5 * * * * cd $PROJECT_DIR && git fetch && git diff --quiet HEAD origin/main || ./deployed/git-deploy.sh >> $PROJECT_DIR/logs/cron-deploy.log 2>&1"

    # Добавляем в crontab
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo -e "${GREEN}✓ Cron job добавлен${NC}"
    echo "  Проверка обновлений каждые 5 минут"
else
    echo "  Пропущено"
fi

# Метод 3: Webhook endpoint (через GitHub/GitLab)
echo ""
echo -e "${YELLOW}[3/3] Webhook Endpoint (опционально)...${NC}"
echo "Создать webhook endpoint для GitHub/GitLab? (y/n)"
read -r response

if [ "$response" = "y" ]; then
    WEBHOOK_PORT=9000
    WEBHOOK_SECRET=$(openssl rand -hex 32)

    # Создаем простой webhook сервер
    cat > deployed/webhook-server.js << EOF
const http = require('http');
const { exec } = require('child_process');
const crypto = require('crypto');

const PORT = ${WEBHOOK_PORT};
const SECRET = '${WEBHOOK_SECRET}';
const DEPLOY_SCRIPT = '${PROJECT_DIR}/deployed/git-deploy.sh';

const server = http.createServer((req, res) => {
    if (req.method === 'POST' && req.url === '/deploy') {
        let body = '';

        req.on('data', chunk => {
            body += chunk.toString();
        });

        req.on('end', () => {
            // Проверка подписи (для GitHub)
            const signature = req.headers['x-hub-signature-256'];
            if (signature) {
                const hash = 'sha256=' + crypto
                    .createHmac('sha256', SECRET)
                    .update(body)
                    .digest('hex');

                if (signature !== hash) {
                    res.writeHead(401);
                    res.end('Invalid signature');
                    return;
                }
            }

            console.log('[' + new Date().toISOString() + '] Deploy triggered');

            // Запускаем деплой
            exec(DEPLOY_SCRIPT, (error, stdout, stderr) => {
                if (error) {
                    console.error('Deploy error:', error);
                }
                console.log(stdout);
                if (stderr) console.error(stderr);
            });

            res.writeHead(200);
            res.end('Deploy started');
        });
    } else {
        res.writeHead(404);
        res.end('Not found');
    }
});

server.listen(PORT, () => {
    console.log(\`Webhook server listening on port \${PORT}\`);
    console.log(\`Webhook URL: http://YOUR_SERVER_IP:\${PORT}/deploy\`);
    console.log(\`Secret: \${SECRET}\`);
});
EOF

    # Создаем systemd сервис для webhook
    cat > /tmp/webhook-deploy.service << EOF
[Unit]
Description=Git Deploy Webhook
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/node $PROJECT_DIR/deployed/webhook-server.js
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    sudo mv /tmp/webhook-deploy.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable webhook-deploy
    sudo systemctl start webhook-deploy

    echo -e "${GREEN}✓ Webhook сервер запущен${NC}"
    echo ""
    echo "  Webhook URL: http://$(hostname -I | awk '{print $1}'):${WEBHOOK_PORT}/deploy"
    echo "  Secret: ${WEBHOOK_SECRET}"
    echo ""
    echo "Добавьте webhook в GitHub/GitLab:"
    echo "  1. Зайдите в Settings → Webhooks"
    echo "  2. Payload URL: http://YOUR_SERVER_IP:${WEBHOOK_PORT}/deploy"
    echo "  3. Secret: ${WEBHOOK_SECRET}"
    echo "  4. Events: Just the push event"
else
    echo "  Пропущено"
fi

# Создание директорий
echo ""
echo -e "${YELLOW}Создание необходимых директорий...${NC}"
mkdir -p logs backups
echo -e "${GREEN}✓ Директории созданы${NC}"

# Финальные инструкции
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Настройка завершена!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Автоматический деплой настроен следующими способами:"
echo ""

if [ -f ".git/hooks/post-merge" ]; then
    echo "✓ Git Hook (post-merge)"
    echo "  Деплой запускается после git pull"
fi

if crontab -l 2>/dev/null | grep -q "git-deploy.sh"; then
    echo "✓ Cron Job"
    echo "  Проверка обновлений каждые 5 минут"
fi

if systemctl is-active --quiet webhook-deploy; then
    echo "✓ Webhook Server"
    echo "  Деплой по HTTP запросу от GitHub/GitLab"
fi

echo ""
echo "Теперь при изменениях в коде:"
echo "  1. На локальной машине: git push"
echo "  2. На сервере: автоматический деплой"
echo ""
echo "Логи деплоя:"
echo "  tail -f logs/deploy.log"
echo ""
echo "Ручной запуск деплоя:"
echo "  ./deployed/git-deploy.sh"
echo ""
