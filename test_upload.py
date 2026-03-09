#!/usr/bin/env python3
"""Тестовый скрипт для загрузки PDF в глобальный индекс"""

import requests
import time

BASE_URL = "http://localhost:8000"

# Создадим простой PDF файл
def create_test_pdf():
    """Создаёт простой тестовый PDF"""
    pdf_content = b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n4 0 obj\n<< /Length 200 >>\nstream\nBT\n/F1 16 Tf\n50 700 Td\n(Test Document for PaperQA Indexation) Tj\n0 -30 Td\n(Created: ' + str(time.time()).encode() + b') Tj\n0 -30 Td\n(This is a test PDF file) Tj\nET\nendstream\nendobj\n5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000266 00000 n \n0000000517 00000 n \ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n594\n%%EOF'
    
    filepath = '/tmp/test_upload_' + str(int(time.time())) + '.pdf'
    with open(filepath, 'wb') as f:
        f.write(pdf_content)
    return filepath

def get_token(username='admin', password='admin123'):
    """Получение токена доступа"""
    response = requests.post(
        f"{BASE_URL}/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if response.status_code == 200:
        return response.json().get('access_token')
    return None

def upload_to_global(token, filepath):
    """Загрузка файла в глобальный индекс"""
    headers = {"Authorization": f"Bearer {token}"}
    with open(filepath, 'rb') as f:
        files = {"file": (filepath.split('/')[-1], f, "application/pdf")}
        response = requests.post(
            f"{BASE_URL}/admin/global-index/upload",
            headers=headers,
            files=files,
            timeout=180  # 3 минуты на загрузку
        )
    return response

def rebuild_index(token):
    """Пересборка индекса"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/admin/global-index/rebuild",
        headers=headers,
        timeout=300  # 5 минут на пересборку
    )
    return response

if __name__ == '__main__':
    print("📄 Создание тестового PDF...")
    pdf_path = create_test_pdf()
    print(f"✅ PDF создан: {pdf_path}")
    
    print("\n🔑 Получение токена...")
    token = get_token()
    
    if not token:
        print("❌ Не удалось получить токен")
    else:
        print(f"✅ Токен получен: {token[:20]}...")
        
        print("\n📤 Загрузка в глобальный индекс...")
        try:
            response = upload_to_global(token, pdf_path)
            print(f"Статус: {response.status_code}")
            print(f"Ответ: {response.json()}")
        except requests.Timeout:
            print("⏰ Таймаут загрузки файла")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        print("\n🔄 Пересборка индекса...")
        try:
            response = rebuild_index(token)
            print(f"Статус: {response.status_code}")
            print(f"Ответ: {response.json()}")
        except requests.Timeout:
            print("⏰ Таймаут пересборки индекса")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    print(f"\n📁 Файл: {pdf_path}")
