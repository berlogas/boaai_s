# 🔬 BOAAI_S

Локальная научная платформа с RAG для научных учреждений.

## 📋 Описание

**BOAAI_S** — автономная система для работы с научной литературой,
поддерживающая полную конфиденциальность данных (всё работает локально).

### Ключевые возможности

- ✅ **Полная автономность** — данные не покидают инфраструктуру
- ✅ **RAG Fusion** — объединённый поиск по глобальной базе и личным документам
- ✅ **Персистентность сессий** — 90 дней хранения с автосохранением
- ✅ **RBAC** — разделение ролей (Администратор / Исследователь)
- ✅ **Точное цитирование** — каждый ответ с источниками

## 🚀 Быстрый старт

```bash
# 1. Инициализация
chmod +x init.sh
./init.sh

# 2. Доступ к интерфейсу
# Frontend: http://localhost:8501
# Backend API: http://localhost:8000/docs
```

## 🛠 Настройка окружения

```bash
# 1. Создать venv:
python3 -m venv .venv
source .venv/bin/activate

# 2. Установить зависимости:
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt

# 3. Запустить через Docker:
docker compose up -d
```

### Выбор интерпретатора в VS Code

1. Нажмите **Ctrl+Shift+P** (или **Cmd+Shift+P** на macOS)
2. Введите и выберите: **Python: Select Interpreter**
3. Выберите из списка: `.venv/bin/python`

Или укажите путь вручную в настройках (уже настроено в `.vscode/settings.json`):

```json
"python.defaultInterpreterPath": ".venv/bin/python"
```

### Тестовые учётные данные

| Роль          | Логин        | Пароль            |
| ------------- | ------------ | ----------------- |
| Администратор | `admin`      | `admin123`        |
| Исследователь | `researcher` | `researcher123`   |

## 📊 Лимиты системы

| Параметр                      | Значение    |
| ----------------------------- | ----------- |
| Макс. сессий на пользователя  | 10          |
| Макс. документов в сессии     | 50          |
| Лимит хранилища сессии        | 500 МБ      |
| Срок жизни сессии             | 90 дней     |

## 📤 Загрузка файлов в глобальную базу

**Только администратор может загружать файлы.**

1. Скопируйте файлы в папку: `data_volume/uploads/`
2. Откройте <http://localhost:8501> → Админ-панель → Глобальная база
3. Нажмите кнопку "🔄 Загрузить файлы из папки uploads"

**Поддерживаемые форматы:**

- `.pdf` — научные статьи
- `.txt`, `.md` — текст и Markdown
- `.html` — веб-страницы
- `.docx`, `.xlsx`, `.pptx` — документы Office
- `.py`, `.ts`, `.yaml`, `.json`, `.csv`, `.xml` — файлы кода и данных

## 📄 Лицензия
3 тестовых запроса для PaperQA2
# Запрос 1: Преимущества self-attention
pqa -i test_papers ask "Какие преимущества имеет механизм self-attention перед RNN?"

# Запрос 2: Сравнение оптимизаторов
pqa -i test_papers ask "Сравните оптимизаторы Adam и SGD: когда лучше использовать каждый?"

# Запрос 3: Архитектуры для последовательностей
pqa -i test_papers ask "Какие архитектуры нейронных сетей лучше подходят для обработки последовательных данных?"
Ожидаемые ответы:

Запрос 1 → должен использовать 01_transformer_attention.pdf: параллелизация, работа с длинными зависимостями, 10x ускорение vs LSTM

Запрос 2 → должен использовать 06_optimizers_comparison.pdf: Adam быстрее, SGD лучше обобщает, AdamW рекомендуется для трансформеров

Запрос 3 → должен объединить 01_transformer_attention.pdf + 05_bert_nlp_embeddings.pdf: Transformers и BERT для последовательностей

Для проверки конкретного запроса:
   docker exec berezhinskii-api python << 'EOF'
   import asyncio, pickle
   from pathlib import Path
   from paperqa import Settings
   
   async def test():
       with open('/app/global_index/docs.pkl', 'rb') as f:
           docs = pickle.load(f)
       settings = Settings(
           llm="ollama/llama3.1:8b",
           summary_llm="ollama/llama3.1:8b",
           embedding="ollama/nomic-embed-text",
       )
       result = await docs.aquery("Какие архитектуры нейронных сетей лучше подходят для обработки последовательных данных?", settings=settings)
       print("Ответ:", result.answer)
       print("Источники:", [c.text.name for c in result.contexts if c.text])
   
   asyncio.run(test())
   EOF