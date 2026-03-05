#!/usr/bin/env python3
import requests
import logging

# Включаем логирование
logging.basicConfig(level=logging.DEBUG)

resp = requests.post('http://localhost:8000/token', data={'username': 'admin', 'password': 'admin123'})
token = resp.json().get('access_token')
print(f'Token: {token[:30]}...')

headers = {'Authorization': f'Bearer {token}'}

print('Sending POST to process-uploads...')
try:
    resp = requests.post('http://localhost:8000/admin/global-index/process-uploads', headers=headers, timeout=300)
    print(f'Status: {resp.status_code}')
    print(f'Response: {resp.json()}')
except Exception as e:
    print(f'Error: {e}')
