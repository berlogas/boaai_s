#!/usr/bin/env python3
"""
Скрипт для загрузки файлов в глобальную базу знаний BOAAI_S
Запускается внутри Docker контейнера
"""

import sys
import os
import asyncio
import pickle
from pathlib import Path
from datetime import datetime

from paperqa import Docs, Settings

# Конфигурация Ollama
OLLAMA_BASE_URL = "http://ollama:11434"
DEFAULT_LLM_MODEL = "llama3.1:8b"
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"

async def upload_to_global_index(file_paths: list[str], index_path: str = "/app/global_index"):
    """Загрузить файлы в глобальный индекс PaperQA"""

    print(f"📚 Инициализация PaperQA Docs...")

    # Конфигурация для Ollama через litellm
    ollama_llm_config = {
        "model_list": [
            {
                "model_name": f"ollama/{DEFAULT_LLM_MODEL}",
                "litellm_params": {
                    "model": f"ollama/{DEFAULT_LLM_MODEL}",
                    "api_base": OLLAMA_BASE_URL,
                },
            }
        ]
    }

    settings = Settings(
        llm=f"ollama/{DEFAULT_LLM_MODEL}",
        llm_config=ollama_llm_config,
        summary_llm=f"ollama/{DEFAULT_LLM_MODEL}",
        summary_llm_config=ollama_llm_config,
        embedding=f"ollama/{DEFAULT_EMBEDDING_MODEL}",
        embedding_config=ollama_llm_config,
    )

    docs = Docs()

    # Путь к индексу
    pkl_path = os.path.join(index_path, "docs.pkl")

    # Пробуем загрузить существующий индекс
    if os.path.exists(pkl_path):
        print(f"📂 Загрузка существующего индекса из {pkl_path}")
        try:
            with open(pkl_path, 'rb') as f:
                docs = pickle.load(f)
            print(f"✅ Индекс загружен (текстов: {len(docs.texts)})")
        except Exception as e:
            print(f"⚠️ Не удалось загрузить индекс: {e}")
            docs = Docs()

    print(f"📄 Загрузка {len(file_paths)} файлов...")

    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"❌ Файл не найден: {file_path}")
            continue

        # Проверка типа файла
        ext = Path(file_path).suffix.lower()
        if ext not in ['.pdf', '.txt', '.md', '.html', '.docx']:
            print(f"  ⚠️ Неподдерживаемый формат: {ext}. Пропускаем...")
            continue

        print(f"  📖 Обработка: {os.path.basename(file_path)} ({ext})")
        start_time = datetime.now()
        try:
            # Для PDF используем sync метод add (в отдельном потоке)
            def add_sync():
                d = Docs()
                d.add(
                    file_path,
                    docname=os.path.basename(file_path),
                    citation="global_index",
                    disable_check=True,
                    settings=settings
                )
                #Merge с существующими docs
                if hasattr(docs, 'texts') and docs.texts:
                    for t in docs.texts:
                        d.texts.append(t)
                return d

            # Запускаем в отдельном потоке
            import asyncio
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(None, add_sync)

            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"  ✅ Успешно за {elapsed:.1f} сек")

        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()

    # Сохраняем индекс через pickle
    print(f"\n💾 Сохранение индекса...")
    os.makedirs(index_path, exist_ok=True)
    with open(pkl_path, 'wb') as f:
        pickle.dump(docs, f)

    print(f"✅ Готово! Индекс сохранён в {pkl_path}")
    print(f"📊 Всего текстов в индексе: {len(docs.texts)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print(f"  python {sys.argv[0]} <файл1> [файл2] ...")
        print(f"  python {sys.argv[0]} /app/uploads/paper1.pdf /app/uploads/paper2.pdf")
        sys.exit(1)

    files = sys.argv[1:]
    asyncio.run(upload_to_global_index(files))
