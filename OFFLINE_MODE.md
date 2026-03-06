# 🔒 Работа без интернета (Offline режим)

## 🚫 Отключённые внешние соединения

Streamlit по умолчанию пытается подключаться к своим серверам. В локальной среде это не нужно.

### Что отключено:

1. **Сбор статистики использования**
2. **Проверка обновлений**
3. **Уведомления о сети**
4. **Кнопка "Deploy"**
5. **Внешние CSS/шрифты**

---

## ⚙️ Конфигурация offline режима

### 1. Переменные окружения

В `frontend/app/main.py`:

```python
# Отключение всех внешних соединений Streamlit
import os
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
os.environ["STREAMLIT_SERVER_ENABLE_STATIC_SERVING"] = "false"
```

### 2. Файл config.toml

`frontend/app/.streamlit/config.toml`:

```toml
[server]
headless = true
enableCORS = false
enableXsrfProtection = true
enableStaticServing = false

[browser]
gatherUsageStats = false

[global]
showWarningOnDirectExecution = false

[logger]
level = "error"
```

### 3. CSS для скрытия уведомлений

`frontend/app/.streamlit/custom.css`:

```css
/* Скрыть кнопку "Deploy" */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* Скрыть уведомления о сети */
[data-testid="stAlertWrapper"] {display: none !important;}
[data-testid="stToast"] {display: none !important;}
[data-testid="stStatusContainer"] {display: none !important;}
```

---

## 🔍 Проверка отсутствия соединений

### Логи контейнера

```bash
docker logs berezhinskii-ui 2>&1 | grep -i -E "connect|http|network|error"
```

### Мониторинг сетевой активности

```bash
# Проверить активные подключения из контейнера
docker exec berezhinskii-ui netstat -tn 2>/dev/null || ss -tn

# Или через tcpdump (если установлен)
docker exec berezhinskii-ui tcpdump -i any -n 2>&1 | head -20
```

### Блокировка на уровне сети

Для полной уверенности можно заблокировать исходящий трафик:

```bash
# Запретить исходящие подключения из контейнера (iptables)
docker network inspect -f '{{range .IPAM.Config}}{{.Subnet}}{{end}}' bridge
```

---

## 🛡️ Дополнительная изоляция

### 1. Отключить сеть для контейнера

Если приложение полностью локальное, можно отключить сеть:

```yaml
# В docker-compose.yml
frontend:
  network_mode: "none"
```

**Внимание:** Это отключит ВСЮ сеть, включая подключение к backend!

### 2. Использовать внутренний network

```yaml
# В docker-compose.yml
services:
  frontend:
    networks:
      - internal
    # Нет доступа к внешнему миру
  
  backend:
    networks:
      - internal
  
  ollama:
    networks:
      - internal

networks:
  internal:
    driver: bridge
    internal: true  # ← Нет доступа наружу
```

### 3. Брандмауэр

На уровне хоста:

```bash
# Заблокировать исходящий трафик для Docker
iptables -A OUTPUT -o eth0 -p tcp --dport 80 -j DROP
iptables -A OUTPUT -o eth0 -p tcp --dport 443 -j DROP
```

---

## 📊 Сравнение режимов

| Режим | Интернет | Статистика | Обновления | Deploy |
|-------|----------|------------|------------|--------|
| **По умолчанию** | ✅ Да | ✅ Да | ✅ Да | ✅ Да |
| **Offline (сейчас)** | ❌ Нет | ❌ Нет | ❌ Нет | ❌ Скрыта |

---

## 🐛 Возможные проблемы

### 1. Ошибки подключения к backend

Если frontend не может подключиться к backend:

```bash
# Проверить подключение
docker exec berezhinskii-ui curl -I http://backend:8000/health

# Проверить логи
docker logs berezhinskii-ui 2>&1 | tail -50
```

### 2. Streamlit пытается загрузить шрифты

Шрифты загружаются из Google Fonts. Для полной автономности:

```toml
# В config.toml
[theme]
font = "sans serif"  # Использовать системные шрифты
```

### 3. Уведомления всё равно появляются

Проверьте CSS:

```bash
docker exec berezhinskii-ui cat /app/app/.streamlit/custom.css
```

---

## ✅ Чек-лист offline настройки

- [x] `gatherUsageStats = false` в config.toml
- [x] Переменные окружения установлены
- [x] CSS скрывает уведомления
- [x] Кнопка Deploy скрыта
- [x] Логирование минимально
- [ ] (Опционально) Network internal mode
- [ ] (Опционально) Брандмауэр на хосте

---

## 📝 Примечания

### Безопасность

Даже без интернета данные защищены:
- **XSRF защита** включена
- **CORS** отключён (только локальный доступ)
- **Сессии** хранятся локально

### Производительность

Offline режим работает быстрее:
- Нет задержек на сетевые запросы
- Нет фоновых проверок
- Меньше логов

### Обновления

Для обновления приложения:
1. Скачайте обновления на хосте
2. Скопируйте в проект
3. Пересоберите контейнеры

```bash
docker-compose up -d --build
```

---

**Дата обновления:** 2026-03-06  
**Режим:** Полностью автономный (offline)
