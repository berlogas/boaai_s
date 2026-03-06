# Руководство по запуску приложения

Приложение развёртывается в Docker-контейнерах и состоит из трёх компонентов:
- **Backend** (FastAPI) — API сервер на порту 8000
- **Frontend** (Streamlit) — веб-интерфейс на порту 8501
- **Ollama** — локальная LLM на порту 11434

---

## 📋 Требования

- Docker (версия 20.10+)
- Docker Compose (версия 2.0+)
- Минимум 8 ГБ ОЗУ (рекомендуется 16 ГБ)
- Минимум 20 ГБ свободного места на диске

### Проверка установки Docker

```bash
docker --version
docker-compose --version
```

---

## 🚀 Быстрый старт

### 1. Перейдите в директорию проекта

```bash
cd /home/homo/projects/boaai_s
```

### 2. Запустите все контейнеры

```bash
docker-compose up -d
```

Флаг `-d` запускает контейнеры в фоновом режиме.

### 3. Проверьте статус

```bash
docker-compose ps
```

Все контейнеры должны быть в статусе `Up`:
- `berezhinskii-ollama`
- `berezhinskii-api`
- `berezhinskii-ui`

### 4. Откройте приложение в браузере

- **Веб-интерфейс:** http://localhost:8501
- **API документация:** http://localhost:8000/docs

---

## 🔧 Управление приложением

### Просмотр логов

```bash
# Все логи
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f ollama
```

### Остановка приложения

```bash
# Остановить все контейнеры
docker-compose down

# Остановить с удалением volumes (данные будут удалены!)
docker-compose down -v
```

### Перезапуск

```bash
# Быстрый перезапуск
docker-compose restart

# Перезапуск конкретного сервиса
docker-compose restart backend
```

### Пересборка контейнеров

После изменений в коде:

```bash
docker-compose up -d --build
```

---

## 📦 Управление моделями Ollama

### Проверка доступных моделей

```bash
docker exec berezhinskii-ollama ollama list
```

### Загрузка модели

```bash
docker exec berezhinskii-ollama ollama pull llama3.1:8b
```

### Удаление модели

```bash
docker exec berezhinskii-ollama ollama rm llama3.1:8b
```

---

## 🗂️ Структура данных

Данные приложения сохраняются в следующих директориях:

```
/home/homo/projects/boaai_s/
├── data_volume/          # Данные приложения
│   ├── global_index/     # Индексы документов
│   └── uploads/          # Загруженные файлы
└── ...
```

---

## 🔐 Авторизация

По умолчанию:
- **Логин:** `admin`
- **Пароль:** `admin123`

Для смены пароля измените переменные окружения в `.env` файле.

---

## ⚙️ Конфигурация

### Переменные окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Основные переменные:

```env
SECRET_KEY=your_secret_key_here
OLLAMA_BASE_URL=http://ollama:11434
DEFAULT_LLM_MODEL=llama3.1:8b
DEFAULT_EMBEDDING_MODEL=nomic-embed-text
```

### Применение изменений

После изменения `.env`:

```bash
docker-compose down
docker-compose up -d
```

---

## 🐛 Диагностика проблем

### Контейнер не запускается

```bash
# Проверить логи
docker-compose logs backend

# Проверить статус
docker-compose ps

# Пересоздать контейнер
docker-compose up -d --force-recreate backend
```

### Ошибки подключения к Ollama

```bash
# Проверить доступность Ollama
docker exec berezhinskii-ollama ollama list

# Перезапустить Ollama
docker-compose restart ollama
```

### Ошибки при обработке PDF

Убедитесь, что применено исправление Unicode (автоматически применяется при сборке):

```bash
docker exec berezhinskii-api grep "errors=\"replace\"" /usr/local/lib/python3.11/site-packages/paperqa/utils.py
```

### Полная очистка и перезапуск

```bash
# Остановить и удалить всё
docker-compose down -v

# Удалить образы (опционально)
docker rmi boaai_s-backend

# Пересобрать и запустить
docker-compose up -d --build
```

---

## 📊 Мониторинг ресурсов

### Использование памяти

```bash
docker stats
```

### Место на диске

```bash
docker system df
```

### Очистка неиспользуемых данных

```bash
# Очистить остановленные контейнеры
docker container prune

# Очистить неиспользуемые образы
docker image prune

# Полная очистка (осторожно!)
docker system prune -a
```

---

## 🔌 API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/health` | Проверка здоровья |
| POST | `/token` | Получение токена |
| POST | `/upload/` | Загрузка файла |
| POST | `/search/` | Поиск по индексам |
| POST | `/chat/` | Запрос к RAG |

Полная документация: http://localhost:8000/docs

---

## 📝 Часто используемые команды

```bash
# Запуск
cd /home/homo/projects/boaai_s && docker-compose up -d

# Остановка
docker-compose down

# Логи
docker-compose logs -f backend

# Пересборка
docker-compose up -d --build

# Статус
docker-compose ps
```

---

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs -f`
2. Убедитесь, что порты не заняты: `lsof -i :8000 -i :8501 -i :11434`
3. Проверьте доступность Ollama: `curl http://localhost:11434/api/tags`
