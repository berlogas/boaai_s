# Тестирование загрузки PDF

## ✅ Результаты тестирования

### 1. PDF на английском языке

- **Файл:** `test_document.pdf`
- **Статус:** ✅ Успешно загружен и проиндексирован
- **Текста:** 1024 символа
- **Время обработки:** ~2-4 минуты

### 2. PDF с русским текстом (Unicode)

- **Файл:** `test_russian.pdf`
- **Статус:** ✅ Успешно загружен и проиндексирован
- **Текста:** 233 символа
- **Unicode:** ✅ Кириллица обрабатывается корректно

### 3. Unicode исправление

Функция `hexdigest()` в `paper-qa/utils.py` исправлена:

```python
# Было
data = data.encode("utf-8")

# Стало
data = data.encode("utf-8", errors="replace")
```

### Тест Unicode

```text
✅ "Привет мир!" -> 9c89906aaed6dd46dc640bcbc15beadd
✅ "Тест Unicode с кириллицей" -> 4163789dbd74bc09d1b0e0f40916fe27
✅ "Смешанный текст: Hello мир 123" -> 8be84b752249b592a4a52c3792ba480f
```

---

## 📝 Как тестировать загрузку PDF

### Способ 1: Через веб-интерфейс

1. Откройте <http://localhost:8501>
2. Перейдите на страницу **Admin**
3. Скопируйте PDF файл в папку `data_volume/uploads/`
4. Нажмите **Process Uploads**
5. Дождитесь завершения обработки

### Способ 2: Через API

```bash
# 1. Получите токен
TOKEN=$(curl -s -X POST http://localhost:8000/token \
  -d 'username=admin&password=admin123' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

# 2. Скопируйте файл в uploads
cp your_file.pdf data_volume/uploads/

# 3. Запустите обработку
curl -X POST http://localhost:8000/admin/global-index/process-uploads \
  -H "Authorization: Bearer $TOKEN"
```

### Способ 3: Через скрипт в контейнере

```bash
# 1. Скопируйте файл в контейнер
docker cp your_file.pdf berezhinskii-api:/app/uploads/

# 2. Запустите скрипт загрузки
docker exec berezhinskii-api python3 /app/app/upload_to_global.py /app/uploads/your_file.pdf
```

### Способ 4: Через Python скрипт (локально)

```bash
# Требует установки paper-qa локально
python3 upload_global.py data_volume/uploads/your_file.pdf
```

---

## 🔍 Проверка результатов

### 1. Проверка индекса

```bash
docker exec berezhinskii-api python3 -c "
import pickle
with open('/app/global_index/docs.pkl', 'rb') as f:
    docs = pickle.load(f)
print(f'Текстов в индексе: {len(docs.texts)}')
for t in docs.texts:
    print(f'  - {t.name}: {len(t.text)} символов')
"
```

### 2. Проверка файлов

```bash
# Обработанные файлы
docker exec berezhinskii-api ls -la /app/global_index/documents/

# Ожидающие файлы
docker exec berezhinskii-api ls -la /app/uploads/
```

### 3. Проверка логов

```bash
docker logs berezhinskii-api 2>&1 | grep -i -E "pdf|upload|index|error"
```

---

## 🐛 Возможные проблемы

### 1. Файл не обрабатывается

**Причина:** Ollama не отвечает или медленно работает

**Решение:**

```bash
# Проверьте доступность Ollama
docker exec berezhinskii-api curl http://ollama:11434/api/tags

# Проверьте модели
docker exec berezhinskii-ollama ollama list

# Если нужно, загрузите модели
docker exec berezhinskii-ollama ollama pull llama3.1:8b
docker exec berezhinskii-ollama ollama pull nomic-embed-text
```

### 2. Ошибка Unicode

**Причина:** Не применено исправление в `paper-qa/utils.py`

**Проверка:**

```bash
docker exec berezhinskii-api grep "errors=\"replace\"" /usr/local/lib/python3.11/site-packages/paperqa/utils.py
```

**Решение:** Пересоберите контейнер:

```bash
docker-compose up -d --build backend
```

### 3. Таймаут при обработке

**Причина:** Большие файлы или медленная Ollama

**Решение:** Увеличьте таймаут в API запросе или используйте фоновую обработку через веб-интерфейс.

---

## 📊 Поддерживаемые форматы

- **PDF** (.pdf) - через PyMuPDF
- **Текст** (.txt, .md) - напрямую
- **HTML** (.html) - через BeautifulSoup
- **Word** (.docx) - через python-docx
- **Excel** (.xlsx) - через openpyxl
- **PowerPoint** (.pptx) - через python-pptx

---

## 📈 Производительность

| Размер PDF | Страниц | Время обработки |
| ---------- | ------- | --------------- |
| 100 KB     | 1-2     | ~30 сек         |
| 1 MB       | 10-15   | ~2-3 мин        |
| 5 MB       | 50+     | ~10-15 мин      |

Время зависит от скорости Ollama и доступных ресурсов CPU/RAM.
