# 🔍 Как проверить, что ответы используют ваши документы

## Проблема

Ранее ответы не показывали ссылки на ваши документы, потому что:
1. Неправильно извлекались имена документов из PaperQA Context
2. Источники не отображались в ответе

## Что исправлено

1. **paperqa_manager.py**:
   - `search()` теперь использует `ctx.text.name` вместо `ctx.docname`
   - `query_with_answer()` также исправлен
   - Имена документов очищаются от "pages X-Y"

2. **rag_fusion.py**:
   - Контексты теперь включают `doc_name` для каждого источника
   - Промпт явно требует указывать источники в формате: `📚 [имя документа]`
   - Добавлено логирование используемых контекстов

## Как проверить

### Способ 1: Через веб-интерфейс

1. Откройте http://localhost:8501
2. Задайте вопрос по вашим документам
3. В ответе должны быть источники:
   ```
   Источники: 📚 01_transformer_attention.pdf
   ```

### Способ 2: Через логи

```bash
# В одном терминале следите за логами
docker-compose logs -f backend

# В другом терминале задайте вопрос через API
curl -X POST "http://localhost:8000/quick-query" \
  -H "Content-Type: application/json" \
  -d '{"query": "transformer attention mechanism"}'
```

В логах увидите:
```
RAG Fusion: найдено N контекстов
  Контекст 1: 📚 01_transformer_attention.pdf
  Контекст 2: 📚 05_bert_nlp_embeddings.pdf
```

### Способ 3: Проверка индекса

```bash
# Скопируйте скрипт в контейнер
docker cp /home/homo/projects/boaai_s/check_indices.py berezhinskii-api:/app/check_indices.py

# Запустите проверку
docker exec berezhinskii-api python /app/check_indices.py
```

Вы увидите все документы в индексе. Если ваш документ есть в списке → он будет использоваться.

## Ваши документы в индексе

**Глобальный индекс (7 документов):**
- 01_transformer_attention.pdf
- 02_cnn_image_recognition.pdf
- 03_reinforcement_learning.pdf
- 04_gan_generative_models.pdf
- 05_bert_nlp_embeddings.pdf
- 06_optimizers_comparison.pdf
- test_document copy14.pdf

**Индекс сессии user1_1772794803 (1 документ):**
- test_document copy7.pdf

## Пример правильного ответа

**Вопрос:** Какие архитектуры подходят для обработки последовательных данных?

**Правильный ответ:**
```
Для обработки последовательных данных лучше всего подходят:

1. Трансформеры с механизмом внимания...
2. RNN и LSTM...

Источники:
📚 01_transformer_attention.pdf
📚 05_bert_nlp_embeddings.pdf
```

## Если источники не отображаются

1. Проверьте логи:
   ```bash
   docker-compose logs backend | grep "RAG Fusion"
   ```

2. Убедитесь, что документ в индексе:
   ```bash
   docker exec berezhinskii-api python /app/check_indices.py
   ```

3. Перезапустите backend:
   ```bash
   docker-compose restart backend
   ```

4. Если проблема остаётся, проверьте, что код обновился:
   ```bash
   docker exec berezhinskii-api grep "ctx.text.name" /app/app/core/paperqa_manager.py
   ```

## Примечание

Модель llama3.1:8b может иногда игнорировать инструкцию указывать источники. 
Если это произошло:
- Попробуйте задать вопрос иначе
- Используйте более явную формулировку: "Перечисли источники..."
- Рассмотрите возможность использования более мощной модели
