# 📘 Руководство разработчика BOAAI_S

Локальная научная платформа с RAG для научных учреждений.

---


## 📋 Оглавление

1. [Требования](#требования)
2. [Архитектура](#архитектура)
3. [Быстрый старт](#быстрый-старт)
4. [Локальная разработка](#локальная-разработка)
5. [Тестирование](#тестирование)
6. [Полезные команды](#полезные-команды)
7. [Структура проекта](#структура-проекта)
8. [Troubleshooting](#troubleshooting)


---

## 🔧 Требования

| Компонент | Версия | Примечание |
| --------- | ------ | ---------- |
| Python | 3.10+ | Обязательно |
| Docker | 20.0+ | Для контейнеризации |
| Docker Compose | 2.0+ | Для оркестрации |
| Git | 2.30+ | Для контроля версий |

### Опционально (для локальной разработки)

- **Ollama** — локальная LLM ([https://ollama.com](https://ollama.com))
- **VSCode** + расширения: Python, Docker, GitLens

---

## 🏗 Архитектура

```text
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend   │────▶│   Ollama    │
│ Streamlit   │     │   FastAPI   │     │     LLM     │
│   :8501     │     │    :8000    │     │   :11434    │
└─────────────┘     └─────────────┘     └─────────────┘
```

**Компоненты:**

| Сервис | Порт | Описание |
| ------ | ---- | -------- |
| Frontend | 8501 | Streamlit UI |
| Backend | 8000 | FastAPI REST API |
| Ollama | 11434 | Локальная LLM |

---

## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/berlogas/boaai_s.git
cd boaai_s
```

### 2. Инициализация проекта

```bash
chmod +x init.sh
./init.sh
```

Скрипт автоматически:

- Создаст `.env` из `.env.example`
- Сгенерирует `SECRET_KEY`
- Создаст необходимые директории
- Запустит Docker-контейнеры
- Загрузит модели Ollama (`llama3.1:8b`, `nomic-embed-text`)

### 3. Проверка работы

| Сервис | URL |
| ------ | --- |
| Frontend | <http://localhost:8501> |
| Backend API | <http://localhost:8000/docs> |
| Ollama API | <http://localhost:11434/api/tags> |

### 4. Тестовый вход

| Роль | Логин | Пароль |
| ---- | ----- | ------ |
| Администратор | `admin` | `admin123` |
| Исследователь | `researcher` | `researcher123` |

---

## 💻 Локальная разработка

### 1. Создание виртуального окружения

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Установка зависимостей

```bash
# Backend
pip install -r backend/requirements.txt

# Frontend
pip install -r frontend/requirements.txt
```

### 3. Настройка окружения

```bash
# Скопировать пример
cp .env.example .env

# Отредактировать .env при необходимости
# Особенно важно для локального запуска:
# OLLAMA_BASE_URL=http://localhost:11434
```

### 4. Запуск Ollama (если не через Docker)

```bash
# Установить: https://ollama.com
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### 5. Запуск Backend

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API документация: <http://localhost:8000/docs>

### 6. Запуск Frontend

```bash
# В отдельном терминале
cd frontend
streamlit run app/main.py --server.port 8501 --server.address localhost
```

UI: <http://localhost:8501>

---

## 🧪 Тестирование

### Запуск тестов Backend

```bash
cd backend
pytest
# или с подробным выводом
pytest -v --tb=short
```

### Запуск с покрытием

```bash
pip install pytest-cov
pytest --cov=app --cov-report=html
# Отчёт: open htmlcov/index.html
```

### Линтинг (опционально)

```bash
pip install ruff
ruff check backend/app
ruff check frontend/app
```

---

## ⚙️ Полезные команды

### Загрузка в глобальную базу знаний

```bash
# Через Python скрипт
python upload_global.py /path/to/paper1.pdf /path/to/paper2.pdf

# Через Docker (прямой доступ к индексу)
docker exec -it berezhinskii-api python << EOF
from paperqa import Docs
docs = Docs()
await docs.aadd('/app/data/documents/your_paper.pdf')
docs.save('/app/global_index')
EOF
```

### Docker

```bash
# Запуск всех сервисов
docker compose up -d

# Просмотр логов
docker compose logs -f

# Логи конкретного сервиса
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f ollama

# Остановка
docker compose down

# Остановка с удалением данных
docker compose down -v

# Пересборка
docker compose up -d --build

# Проверка состояния
docker compose ps
```

### Git

```bash
# Статус
git status

# Ветви
git branch -a

# Логи
git log --oneline -10

# Отправка изменений
git add .
git commit -m "Описание изменений"
git push origin main
```

### Утилиты

```bash
# Проверка портов
lsof -i :8000
lsof -i :8501
lsof -i :11434

# Очистка .venv
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
```

---

## 📁 Структура проекта

```text
boaai_s/
├── backend/
│   ├── app/
│   │   ├── api/          # REST endpoints
│   │   ├── core/         # Конфигурация, безопасность
│   │   ├── models/       # Pydantic модели
│   │   ├── services/     # Бизнес-логика
│   │   └── main.py       # Точка входа
│   ├── tests/            # Тесты
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── components/   # UI компоненты
│   │   ├── core/         # Конфигурация
│   │   ├── pages/        # Страницы
│   │   ├── utils/        # Утилиты
│   │   └── main.py       # Точка входа
│   ├── .streamlit/       # Настройки Streamlit
│   ├── Dockerfile
│   └── requirements.txt
│
├── data_volume/          # Локальные данные
│   ├── global_index/
│   ├── sessions/
│   └── backup/
│
├── ollama_data/          # Данные Ollama
│
├── .env.example          # Шаблон переменных окружения
├── docker-compose.yml    # Оркестрация
├── init.sh               # Скрипт инициализации
└── README.md
```

---

## 🔧 Troubleshooting

### Ошибка: "Docker not running"

```bash
# Проверка статуса
systemctl status docker

# Запуск
sudo systemctl start docker
sudo systemctl enable docker
```

### Ошибка: "Port already in use"

```bash
# Найти процесс на порту
lsof -i :8000

# Убить процесс
kill -9 <PID>
```

### Ошибка: "Ollama timeout"

```bash
# Проверить контейнер
docker ps | grep ollama

# Перезапустить
docker compose restart ollama

# Проверить логи
docker compose logs ollama
```

### Ошибка: "Module not found"

```bash
# Переустановить зависимости
source .venv/bin/activate
pip install -r backend/requirements.txt --force-reinstall
pip install -r frontend/requirements.txt --force-reinstall
```

### Сброс к чистому состоянию

```bash
# Остановить и удалить всё
docker compose down -v

# Удалить данные
rm -rf data_volume/* ollama_data/*

# Инициализировать заново
./init.sh
```

---

## 📞 Контакты

- GitHub: [https://github.com/berlogas/boaai_s](https://github.com/berlogas/boaai_s)
- Документация API: <http://localhost:8000/docs>

---

**Версия документа:** 1.0  
**Последнее обновление:** Март 2026
