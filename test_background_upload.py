#!/usr/bin/env python3
import requests
import time

resp = requests.post('http://localhost:8000/token', data={'username': 'admin', 'password': 'admin123'})
token = resp.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

print('🔄 Запуск загрузки...')
resp = requests.post('http://localhost:8000/admin/global-index/process-uploads', headers=headers, timeout=30)
print(f'Status: {resp.status_code}')
print(f'Response: {resp.json()}')

print('\\n⏳ Ожидание завершения...')
for i in range(60):  # Ждём до 60 секунд
    time.sleep(2)
    resp = requests.get('http://localhost:8000/admin/global-index/process-uploads/status', headers=headers, timeout=10)
    status = resp.json()
    print(f'  [{i*2}с] {status.get("message", "N/A")}')
    if status.get('completed'):
        print('\\n✅ Загрузка завершена!')
        print(f'Uploaded: {status.get("uploaded", [])}')
        if status.get('errors'):
            print(f'Errors: {status.get("errors")}')
        break
else:
    print('\\n⏰ Таймаут ожидания')
