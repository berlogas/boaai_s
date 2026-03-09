#!/usr/bin/env python3
import requests
import json
import time

# Получаем токен
resp = requests.post('http://localhost:8000/token', data={'username': 'admin', 'password': 'admin123'})
if resp.status_code != 200:
    print(f'❌ Ошибка аутентификации: {resp.status_code}')
    exit(1)

token = resp.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}
print(f'✅ Токен получен: {token[:20]}...')

# Загружаем PDF в глобальную базу
print('📤 Загрузка PDF в глобальную базу...')
start = time.time()

with open('test_document.pdf', 'rb') as f:
    files = {'file': ('test_document3.pdf', f, 'application/pdf')}
    resp = requests.post('http://localhost:8000/upload/global', headers=headers, files=files, timeout=300)

elapsed = time.time() - start
print(f'📤 Status: {resp.status_code} (за {elapsed:.1f} сек)')

try:
    result = resp.json()
    print('✅ Результат:')
    print(json.dumps(result, indent=2, ensure_ascii=False))
except Exception as e:
    print(f'❌ Ошибка парсинга ответа: {e}')
    print(f'Ответ: {resp.text[:500]}')
