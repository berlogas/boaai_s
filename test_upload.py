#!/usr/bin/env python3
import requests
import json
import time

resp = requests.post('http://localhost:8000/token', data={'username': 'admin', 'password': 'admin123'})
token = resp.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

print('🔄 Отправка запроса на process-uploads...')
start = time.time()

try:
    resp = requests.post('http://localhost:8000/admin/global-index/process-uploads', headers=headers, timeout=90)
    elapsed = time.time() - start
    print(f'✅ Завершено за {elapsed:.1f} сек')
    print(f'Status: {resp.status_code}')
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
except requests.Timeout:
    print('⏰ Таймаут 90 сек')
except Exception as e:
    print(f'❌ Error: {e}')
