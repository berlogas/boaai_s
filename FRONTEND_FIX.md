# 🔧 Исправление проблемы подключения frontend к backend

## ❌ Проблема

Frontend пытался подключиться к backend по жёстко заданному IP адресу:

```python
self.base_url = "http://172.18.0.3:8000"
```

**Проблема:** IP адрес контейнера меняется при пересоздании контейнера (пересборка, restart, и т.д.)

**Симптомы:**

```text
Ошибка: HTTPConnectionPool(host='172.18.0.3', port=8000): Max retries exceeded
❌ Неверные credentials
```

## ✅ Решение

Использовать **имя сервиса Docker** вместо IP адреса:

```python
# Было
self.base_url = "http://172.18.0.3:8000"

# Стало
self.base_url = "http://backend:8000"
```

### Изменения в файлах

**Файл:** `frontend/app/core/api_client.py`

1. Основной URL подключения:

```python
class APIClient:
    def __init__(self, base_url: str = None):
        # Используем имя сервиса Docker для надёжности
        # IP адрес может меняться при пересоздании контейнеров
        self.base_url = base_url or "http://backend:8000"
```

1. URL в методе `upload_to_global_index` (curl запрос):

```python
cmd = f'curl -s -w "\\nHTTP_CODE:%{{http_code}}" -X POST "http://backend:8000/admin/global-index/upload" ...'
```

### Применение исправления

```bash
# Пересобрать frontend
cd /home/homo/projects/boaai_s
docker-compose up -d --build frontend

# Проверить подключение
docker exec berezhinskii-ui python3 -c "
import requests
resp = requests.post('http://backend:8000/token', data={'username': 'admin', 'password': 'admin123'})
print(f'Статус: {resp.status_code}')
print('✅ Подключение успешно!' if resp.status_code == 200 else '❌ Ошибка')
"
```

## 📋 Проверка

### 1. Тест подключения из frontend

```bash
docker exec berezhinskii-ui python3 -c "
import requests
resp = requests.post('http://backend:8000/token', data={'username': 'admin', 'password': 'admin123'})
print(f'Статус: {resp.status_code}')
if resp.status_code == 200:
    print('✅ Подключение успешно!')
else:
    print('❌ Ошибка подключения')
"
```

### 2. Проверка через веб-интерфейс

1. Откройте <http://localhost:8501>
2. Введите:
   - **Имя пользователя:** `admin`
   - **Пароль:** `admin123`
3. Нажмите **Войти**

Если всё работает — вы успешно авторизовались! ✅

### 3. Проверка логов

```bash
# Логи frontend
docker logs berezhinskii-ui 2>&1 | tail -20

# Логи backend
docker logs berezhinskii-api 2>&1 | tail -20
```

## 🔍 Почему это работает

Docker Compose создаёт внутреннюю DNS сеть, где сервисы доступны по именам:

```yaml
services:
  backend:    # ← Доступен как "http://backend:8000"
  frontend:   # ← Доступен как "http://frontend:8501"
  ollama:     # ← Доступен как "http://ollama:11434"
```

**Преимущества:**

- ✅ IP адрес не нужен
- ✅ Работает при пересоздании контейнеров
- ✅ Не зависит от порядка запуска
- ✅ Стандартный подход Docker

## 📝 Примечания

### Если используете внешний доступ

Для доступа к API извне контейнеров (с хоста или другой машины):

```python
# Для локального доступа с хоста
self.base_url = "http://localhost:8000"

# Для доступа из внешней сети
self.base_url = "http://<IP-сервера>:8000"
```

### Переменная окружения

Для гибкости можно вынести URL в переменную окружения:

```python
import os
self.base_url = os.getenv("BACKEND_URL", "http://backend:8000")
```

В `docker-compose.yml`:

```yaml
frontend:
  environment:
    - BACKEND_URL=http://backend:8000
```

---

**Дата исправления:** 2026-03-06  
**Файл:** `frontend/app/core/api_client.py`
