#!/bin/bash
set -euo pipefail  # Строгий режим

echo "🚀 Инициализация BOAAI_S..."

if ! python3 -c "import yaml; yaml.safe_load(open('docker-compose.yml'))" 2>/dev/null; then
    echo "❌ Ошибка в docker-compose.yml"
    exit 1
fi

# Проверка Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Ошибка: нет доступа к Docker"
    exit 1
fi

# 1. Создание .env
if [ ! -f .env ]; then
    [ -f .env.example ] && cp .env.example .env || echo "⚠️ .env.example не найден"
    echo "✅ Создан файл .env"
fi

# 2. Генерация SECRET_KEY (безопасная замена)
if grep -q "your_super_secret_key_change_in_prod" .env; then
    NEW_KEY=$(openssl rand -hex 32)
    sed -i "s|your_super_secret_key_change_in_prod|$NEW_KEY|" .env
    echo "✅ Сгенерирован SECRET_KEY"
fi

# 3. Создание директорий
mkdir -p data_volume/{global_index,sessions,backup,uploads} ollama_data

# 4. Запуск контейнеров
echo "🐳 Запуск контейнеров..."
docker compose up -d  # Обратите внимание: без дефиса!

# 5. Ожидание Ollama с retry
echo "⏳ Ожидание готовности Ollama..."
for i in {1..30}; do
    if docker exec berezhinskii-ollama curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama готова!"
        break
    fi
    [ $i -eq 30 ] && { echo "❌ Таймаут ожидания Ollama"; exit 1; }
    echo "  Попытка $i/30..."
    sleep 2
done

# 6. Загрузка моделей
echo "📥 Загрузка моделей (это может занять время)..."
docker exec berezhinskii-ollama ollama pull llama3.1:8b
docker exec berezhinskii-ollama ollama pull nomic-embed-text

echo "✅ BOAAI_S готов к работе!"
echo "🌐 Frontend: http://localhost:8501"
echo "🔧 Backend:  http://localhost:8000/docs"