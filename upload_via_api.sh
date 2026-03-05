#!/bin/bash
set -x

# Получаем токен
TOKEN=$(curl -s -X POST http://localhost:8000/token -d "username=admin" -d "password=admin123" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

echo "Token: ${TOKEN:0:30}..."

# Проверяем pending
echo "Checking pending..."
curl -s "http://localhost:8000/admin/global-index/pending" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# Загружаем файлы
echo "Uploading files..."
curl -s -X POST "http://localhost:8000/admin/global-index/process-uploads" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --max-time 120 | python3 -m json.tool
