<!-- markdownlint-disable MD013 -->
# 💾 Хранение индексов и данных

## 📁 Где хранятся индексы

### Основное хранилище

Все данные приложения сохраняются в **локальной папке** на хосте:

```text
/home/homo/projects/boaai_s/data_volume/
├── global_index/           # Глобальный индекс PaperQA
│   ├── docs.pkl           # Основной индекс (pickle)
│   ├── docs.json          # Резервная копия индекса
│   │                      # (JSON)
│   ├── documents/         # Обработанные файлы
│   │   ├── test_document.pdf
│   │   ├── test_russian.pdf
│   │   ├── ADMIN_GUIDE.md
│   │   └── ...
│   └── global_index/      # Дополнительные индексы
│       └── global_index.pkl
├── uploads/               # Файлы, ожидающие
│   │                      # обработки
│   └── ...
├── sessions/              # Данные сессий
├── backup/                # Резервные копии
├── audit_log.json         # Лог аудита
├── users.json             # Пользователи
└── sessions.json          # Сессии (JSON)
```

### Docker volumes

В `docker-compose.yml` настроены следующие volumes:

```yaml
volumes:
  - ./data_volume:/app/data           # Основные данные
  - ./data_volume/global_index:/app/global_index  # Индексы PaperQA
  - ./data_volume/uploads:/app/uploads            # Загрузки
  - ollama_data:/root/.ollama          # Модели Ollama (Docker volume)
```

**Важно:**

- `./data_volume/*` — **локальные папки** на хосте
  (сохраняются при пересборке)
- `ollama_data:` — **Docker volume**
  (сохраняется при `docker-compose down`,
  удаляется при `docker-compose down -v`)

---

## ✅ Что сохраняется при пересборке

| Данные | Файл/Папка | Сохраняется? | Где |
| ------ | ---------- | ------------ | --- |
| **Индексы PaperQA** | `data_volume/global_index/docs.pkl` | ✅ Да | Локальная
  папка |
| **Обработанные файлы** | `data_volume/global_index/documents/` | ✅ Да | Локальная
  папка |
| **Файлы загрузок** | `data_volume/uploads/` | ✅ Да | Локальная
  папка |
| **Пользователи** | `data_volume/users.json` | ✅ Да | Локальная
  папка |
| **Сессии** | `data_volume/sessions/` | ✅ Да | Локальная
  папка |
| **Модели Ollama** | Docker volume `ollama_data` | ⚠️ Зависит | Docker
  volume |
| **Логи** | В контейнере | ❌ Нет | Только
  в памяти |

---

## 🔄 Безопасная пересборка

### ✅ Безопасные команды (данные сохраняются)

```bash
# Пересборка контейнеров
docker-compose up -d --build

# Пересоздание контейнеров
docker-compose up -d --force-recreate

# Остановка и запуск
docker-compose down
docker-compose up -d

# Restart отдельных сервисов
docker-compose restart backend
```

### ⚠️ Опасные команды (данные могут быть удалены)

```bash
# Удаление volumes (модели Ollama будут удалены!)
docker-compose down -v

# Удаление Docker volume Ollama
docker volume rm boaai_s_ollama_data

# Полная очистка (осторожно!)
docker system prune -a --volumes
```

---

## 🛡️ Резервное копирование

### Создание резервной копии

```bash
# Перейдите в директорию проекта
cd /home/homo/projects/boaai_s

# Создайте резервную копию data_volume
tar -czvf data_volume_backup_$(date +%Y%m%d_%H%M%S).tar.gz data_volume/

# Или скопируйте в другую папку
cp -r data_volume/ data_volume_backup_$(date +%Y%m%d_%H%M%S)/
```

### Восстановление из резервной копии

```bash
# Остановите контейнеры
docker-compose down

# Восстановите из tar
tar -xzvf data_volume_backup_20260306_120000.tar.gz

# Или скопируйте из backup папки
cp -r data_volume_backup_20260306_120000/ data_volume/

# Запустите контейнеры
docker-compose up -d
```

### Автоматическое резервное копирование

Скрипт `backup.sh` уже существует в проекте:

```bash
# Запустить резервное копирование
./backup.sh

# Настроить cron (ежедневно в 3:00)
crontab -e
# Добавить: 0 3 * * * /home/homo/projects/boaai_s/backup.sh
```

---

## 📊 Проверка целостности данных

### Проверка индекса

```bash
# Проверить наличие файлов индекса
ls -lh data_volume/global_index/docs.pkl data_volume/global_index/documents/

# Проверить содержимое индекса
docker exec berezhinskii-api python3 -c "
import pickle
with open('/app/global_index/docs.pkl', 'rb') as f:
    docs = pickle.load(f)
print(f'Текстов в индексе: {len(docs.texts)}')
for t in docs.texts:
    print(f'  - {t.name}')
"
```

### Проверка моделей Ollama

```bash
# Проверить модели
docker exec berezhinskii-ollama ollama list

# Если модели отсутствуют, загрузить
docker exec berezhinskii-ollama ollama pull llama3.1:8b
docker exec berezhinskii-ollama ollama pull nomic-embed-text
```

---

## 🔧 Перенос данных на другой сервер

### Экспорт

```bash
# 1. Остановите контейнеры
docker-compose down

# 2. Сохраните Docker volume Ollama
docker run --rm \
  -v boaai_s_ollama_data:/source \
  -v $(pwd):/backup \
  alpine tar -czf /backup/ollama_data.tar.gz -C /source .

# 3. Скопируйте data_volume
tar -czvf data_volume.tar.gz data_volume/

# 4. Скопируйте docker-compose.yml
cp docker-compose.yml docker-compose.yml.backup
```

### Импорт

```bash
# 1. Скопируйте файлы на новый сервер
scp data_volume.tar.gz ollama_data.tar.gz docker-compose.yml.backup user@server:/path/to/project/

# 2. На новом сервере
cd /path/to/project
tar -xzvf data_volume.tar.gz
docker-compose up -d  # Создаст контейнеры

# 3. Восстановите Ollama volume
docker run --rm \
  -v boaai_s_ollama_data:/target \
  -v $(pwd):/backup \
  alpine tar -xzf /backup/ollama_data.tar.gz -C /target

# 4. Запустите всё
docker-compose up -d
```

---

## 📋 Чек-лист перед пересборкой

- [ ] Проверить наличие `data_volume/global_index/docs.pkl`
- [ ] Проверить наличие файлов в `data_volume/global_index/documents/`
- [ ] Убедиться, что используется `docker-compose up -d --build` (не `down -v`)
- [ ] При необходимости создать резервную копию
- [ ] После пересборки проверить индекс через API или UI

---

## 🆘 Аварийное восстановление

### Если индекс повреждён

```bash
# 1. Остановите контейнеры
docker-compose down

# 2. Восстановите из резервной копии
cp backup/docs.pkl.backup data_volume/global_index/docs.pkl

# 3. Запустите контейнеры
docker-compose up -d
```

### Если модели Ollama утеряны

```bash
# Перезагрузите модели
docker exec berezhinskii-ollama ollama pull llama3.1:8b
docker exec berezhinskii-ollama ollama pull nomic-embed-text

# Проверьте
docker exec berezhinskii-ollama ollama list
```

### Если данные утеряны после `docker-compose down -v`

```bash
# 1. Проверьте Docker volumes
docker volume ls | grep boaai_s

# 2. Если volume удалён, восстановите из резервной копии
# (см. раздел "Резервное копирование")
```

---

## 📝 Рекомендации

1. **Регулярное резервное копирование** — настройте ежедневный backup
2. **Храните несколько копий** — минимум 3 последние резервные копии
3. **Проверяйте backup** — периодически восстанавливайте из резервных копий
4. **Мониторинг места** — следите за размером `data_volume/`
5. **Документируйте изменения** — записывайте важные изменения в индексах
