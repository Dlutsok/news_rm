#!/bin/bash

# Medical News Automation System - Quick Start Script

echo "🚀 Запуск Medical News Automation System..."

# Проверка зависимостей
check_dependencies() {
    echo "📋 Проверка зависимостей..."
    
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 не найден. Установите Python 3.8+"
        exit 1
    fi
    
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js не найден. Установите Node.js 16+"
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        echo "❌ npm не найден. Установите npm"
        exit 1
    fi
    
    echo "✅ Все зависимости найдены"
}

# Установка backend
setup_backend() {
    echo "🔧 Настройка backend..."
    cd backend
    
    # Проверяем наличие .env файла в корне проекта
    if [ ! -f "../.env" ]; then
        echo "📝 Создание .env файла из примера..."
        cp ../.env.example ../.env
        echo "⚠️  Не забудьте настроить переменные в .env файле!"
    else
        echo "✅ .env файл найден в корне проекта"
    fi
    
    echo "📦 Установка Python зависимостей..."
    pip3 install -r requirements.txt
    
    cd ..
    echo "✅ Backend настроен"
}

# Установка frontend
setup_frontend() {
    echo "🔧 Настройка frontend..."
    cd frontend
    
    echo "📦 Установка npm зависимостей..."
    npm install
    
    cd ..
    echo "✅ Frontend настроен"
}



# Запуск backend
start_backend() {
    echo "🚀 Запуск backend сервера..."
    cd backend
    uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
    echo "✅ Backend запущен на http://localhost:8000 (PID: $BACKEND_PID)"
}

# Запуск frontend
start_frontend() {
    echo "🚀 Запуск frontend сервера..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    echo "✅ Frontend запущен на http://localhost:3000 (PID: $FRONTEND_PID)"
}



# Функция остановки
cleanup() {
    echo "🛑 Остановка серверов..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "✅ Backend остановлен"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "✅ Frontend остановлен"
    fi
    exit 0
}

# Обработка сигналов
trap cleanup SIGINT SIGTERM

# Основная логика
case "$1" in
    "install")
        check_dependencies
        setup_backend
        setup_frontend
        echo "🎉 Установка завершена! Запустите: ./start.sh run"
        ;;
    "run")
        echo "🚀 Запуск системы..."
        start_backend
        sleep 2
        start_frontend
        
        echo ""
        echo "🌐 Система запущена!"
        echo "   Frontend:     http://localhost:3000"
        echo "   Backend:      http://localhost:8000"
        echo "   API Docs:     http://localhost:8000/docs"
        echo ""
        echo "Нажмите Ctrl+C для остановки"
        
        # Ожидание
        wait
        ;;
    "test")
        echo "🧪 Тестирование парсера..."
        curl -s http://localhost:8000/api/news/sources/test | python3 -m json.tool
        ;;
    "stop")
        cleanup
        ;;
    *)
        echo "Использование: $0 {install|run|test|stop}"
        echo ""
        echo "Команды:"
        echo "  install  - Установка зависимостей"
        echo "  run      - Запуск системы"
        echo "  test     - Тест парсера"
        echo "  stop     - Остановка системы"
        exit 1
        ;;
esac