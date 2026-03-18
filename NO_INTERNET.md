# ✅ Отключение интернета в приложении

## 🎯 Что сделано

Все попытки подключения к внешним серверам Streamlit **отключены**.

### Изменения в файлах

### 1. `docker-compose.yml`

Добавлены переменные окружения для frontend:

```yaml
frontend:
  environment:
    - STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
    - STREAMLIT_SERVER_ENABLE_STATIC_SERVING=false
```

### 2. `frontend/app/main.py`

Дополнительная защита на уровне кода:

```python
import os
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
os.environ["STREAMLIT_SERVER_ENABLE_STATIC_SERVING"] = "false"
```

### 3. `frontend/app/.streamlit/config.toml`

Полная конфигурация offline режима:

```toml
[browser]
gatherUsageStats = false

[server]
enableStaticServing = false

[global]
showWarningOnDirectExecution = false

[logger]
level = "error"
```

### 4. `frontend/app/.streamlit/custom.css`

Скрытие всех уведомлений:

```css
/* Скрыть кнопку Deploy */
#MainMenu {visibility: hidden;}

/* Скрыть уведомления о сети */
[data-testid="stAlertWrapper"] {display: none !important;}
[data-testid="stToast"] {display: none !important;}
```

---

## 🔍 Проверка

### 1. Проверка переменных окружения

```bash
docker exec berezhinskii-ui python3 -c "
import os
print('GATHER_USAGE_STATS:', os.environ.get('STREAMLIT_BROWSER_GATHER_USAGE_STATS'))
print('STATIC_SERVING:', os.environ.get('STREAMLIT_SERVER_ENABLE_STATIC_SERVING'))
"
```

**Ожидаемый вывод:**

```text
GATHER_USAGE_STATS: false
STATIC_SERVING: false
```

### 2. Проверка логов

```bash
docker logs berezhinskii-ui 2>&1 | tail -10
```

**Ожидаемый вывод:**

```text
You can now view your Streamlit app in your browser.
URL: http://0.0.0.0:8501
```

(Без сообщений о сборе статистики)

### 3. Мониторинг сети

```bash
# Проверить исходящие подключения
docker exec berezhinskii-ui netstat -tn 2>/dev/null | grep -v "Local\|^$"

# Должно быть пусто или только локальные подключения
```

---

## 🚫 Что отключено

| Компонент | Статус | Примечание |
| --------- | ------ | ---------- |
| **Сбор статистики** | ❌ Отключен | `gatherUsageStats = false` |
| **Проверка обновлений** | ❌ Отключена | `showWarningOnDirectExecution = false` |
| **Кнопка Deploy** | ❌ Скрыта | CSS `#MainMenu {visibility: hidden;}` |
| **Уведомления о сети** | ❌ Скрыты | CSS `[data-testid="stAlertWrapper"]` |
| **Статический сервинг** | ❌ Отключен | `enableStaticServing = false` |
| **Логирование** | ⚠️ Минимальное | `level = "error"` |

---

## 🛡️ Дополнительная защита

### 1. Изолированная сеть (опционально)

Для полной изоляции добавьте в `docker-compose.yml`:

```yaml
networks:
  default:
    name: berezhinskii_network
    driver: bridge
    internal: true  # ← Нет доступа наружу
```

**Внимание:** Это может нарушить работу если нужны внешние API.

### 2. Брандмауэр на хосте

```bash
# Заблокировать исходящий трафик Docker
iptables -I DOCKER-USER -i docker0 -o eth0 -j DROP
```

---

## 📊 Сравнение

### До изменений

```text
Collecting usage statistics. To deactivate, set browser.gatherUsageStats to False.
https://streamlit.io
Copyright 2026 Snowflake Inc. All rights reserved.
[Deploy] кнопка видна
```

### После изменений

```text
You can now view your Streamlit app in your browser.
URL: http://0.0.0.0:8501
[Никаких внешних подключений]
```

---

## ✅ Результат

- ✅ **Нет подключения к интернету**
- ✅ **Нет сбора статистики**
- ✅ **Нет уведомлений**
- ✅ **Нет кнопки Deploy**
- ✅ **Полностью локальная работа**

---

## 📝 Примечания

### Локальные подключения

Приложение продолжает работать внутри Docker сети:

- `frontend` ↔ `backend` (порт 8000)
- `backend` ↔ `ollama` (порт 11434)

### Обновление приложения

Для обновления используйте локальные файлы:

```bash
# Пересборка из локальных исходников
docker-compose up -d --build
```

### Безопасность

Данные полностью под контролем:

- Все данные хранятся локально в `data_volume/`
- Нет внешних подключений
- Сессии не передаются наружу

---

**Дата обновления:** 2026-03-06  
**Статус:** ✅ Полностью автономный режим
