#!/usr/bin/env python3
"""
Скрипт для загрузки файлов в глобальную базу знаний BOAAI_S

Использование:
    python upload_to_global.py <файл> <логин> <пароль>

Пример:
    python upload_to_global.py document.pdf admin admin123
"""

import sys
import os
import requests
import json

BASE_URL = "http://localhost:8000"

def login(username, password):
    """Получить токен авторизации"""
    response = requests.post(
        f"{BASE_URL}/token",
        data={"username": username, "password": password}
    )
    if response.status_code == 200:
        data = response.json()
        return data["access_token"]
    else:
        print(f"❌ Ошибка авторизации: {response.status_code}")
        print(response.text)
        return None

def upload_file(file_path, token):
    """Загрузить файл в глобальную базу"""
    if not os.path.exists(file_path):
        print(f"❌ Файл не найден: {file_path}")
        return False
    
    filename = os.path.basename(file_path)
    print(f"📤 Загрузка {filename}...")
    
    with open(file_path, 'rb') as f:
        response = requests.post(
            f"{BASE_URL}/admin/global-index/upload",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": (filename, f)},
            timeout=120
        )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Успех: {result.get('message', 'OK')}")
        print(f"📄 {result.get('document', {})}")
        return True
    else:
        print(f"❌ Ошибка: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    
    file_path = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]
    
    # Авторизация
    print(f"🔐 Авторизация как {username}...")
    token = login(username, password)
    if not token:
        sys.exit(1)
    
    print(f"✅ Токен получен")
    
    # Загрузка файла
    if upload_file(file_path, token):
        print("✅ Готово!")
        sys.exit(0)
    else:
        print("❌ Ошибка загрузки")
        sys.exit(1)
