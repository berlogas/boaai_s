# 🔘 Кнопка "Deploy" в Streamlit

## ❓ Что это такое

Кнопка **"Deploy"** в верхнем правом углу — это **стандартный элемент интерфейса Streamlit**, а не часть вашего приложения.

Она предлагает развернуть приложение в облачном сервисе **Streamlit Cloud**.

```text
┌─────────────────────────────────────────────────────┐
│  🔬 BOAAI_S                              [Deploy] ▼ │  ← Стандартный Streamlit
│  ─────────────────────────────────────────────────  │
│                                                     │
│  Ваше приложение...                                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## ✅ Как скрыть кнопку "Deploy"

Кнопка скрыта автоматически через CSS в файле `frontend/app/main.py`:

```python
# Скрыть стандартные элементы Streamlit (Deploy, footer, header)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp > header {display: none !important;}
    </style>
""", unsafe_allow_html=True)
```

## 📁 Файлы конфигурации Streamlit

### 1. `frontend/app/.streamlit/config.toml`

Основная конфигурация:

```toml
[theme]
primaryColor = "#0068c9"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
```

### 2. `frontend/app/.streamlit/custom.css`

Дополнительные стили:

```css
/* Скрыть кнопку "Deploy" в верхнем правом углу */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
```

## 🔍 Другие элементы Streamlit

### В приложении также скрыты

- **Header** — заголовок страницы
- **Footer** — подвал страницы
- **MainMenu** — меню (три точки)

### Отображается

- **Sidebar** — боковая панель с навигацией
- **Контент** — основное содержимое приложения

## 📊 Информация о Streamlit

Внизу sidebar может отображаться:

```text
Made with
Streamlit v1.30.0
https://streamlit.io
Copyright 2026 Snowflake Inc. All rights reserved.
```

Это **стандартная подпись Streamlit**, которую нельзя удалить (только скрыть CSS).

## 🛠️ Применение изменений

После изменения конфигурации:

```bash
# Пересобрать frontend
cd /home/homo/projects/boaai_s
docker-compose up -d --build frontend

# Проверить
docker logs berezhinskii-ui 2>&1 | tail -10
```

## 📝 Примечания

### Почему нельзя полностью удалить?

Кнопка "Deploy" — часть **фреймворка Streamlit**, а не вашего кода. Она добавляется автоматически на уровне библиотеки.

### Альтернативы

1. **Оставить как есть** — не мешает работе
2. **Скрыть CSS** — как сделано сейчас
3. **Использовать кастомную тему** — через `config.toml`

### Для production

В production-среде можно полностью кастомизировать интерфейс через:

- CSS стили
- Кастомные компоненты
- Прокси-сервер с модификацией контента

---

**Дата обновления:** 2026-03-06  
**Файлы:** `frontend/app/main.py`, `frontend/app/.streamlit/config.toml`
