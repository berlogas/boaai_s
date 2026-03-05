#!/usr/bin/env python3
"""
Скрипт для загрузки файлов в глобальную базу знаний BOAAI_S
Использует PaperQA напрямую для индексации
"""

import sys
import os
import asyncio
import pickle
from pathlib import Path

# Добавляем backend в path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from paperqa import Docs, Settings

async def upload_to_global_index(file_paths: list[str], index_name: str = "global_index"):
    """Загрузить файлы в глобальный индекс PaperQA"""
    
    print(f"📚 Инициализация PaperQA Docs...")
    
    # Настройки для использования с локальной Ollama
    settings = Settings(
        llm="ollama/llama3.1:8b",
        summary_llm="ollama/llama3.1:8b",
        embedding="ollama/nomic-embed-text",
    )
    
    docs = Docs()
    
    # Путь к индексу
    index_path = Path(__file__).parent / "data_volume" / "global_index"
    index_path.mkdir(parents=True, exist_ok=True)
    
    pkl_path = index_path / f"{index_name}.pkl"
    
    print(f"📂 Индекс будет сохранён в: {pkl_path}")
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
        try:
            # Используем правильный reader для разных типов файлов
            if ext == '.pdf':
                await docs.aadd(file_path, settings=settings)
            elif ext in ['.txt', '.md']:
                # Для текстовых файлов используем простой reader
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                await docs.aadd_text(content, docname=os.path.basename(file_path))
            elif ext == '.html':
                await docs.aadd(file_path, settings=settings)
            elif ext == '.docx':
                await docs.aadd(file_path, settings=settings)
            print(f"  ✅ Успешно")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
    
    # Сохраняем индекс через pickle
    print(f"\n💾 Сохранение индекса...")
    with open(pkl_path, 'wb') as f:
        pickle.dump(docs, f)
    
    print(f"✅ Готово! Индекс сохранён в {pkl_path}")
    print(f"📊 Всего текстов в индексе: {len(docs.texts)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print(f"  python {sys.argv[0]} <файл1> [файл2] ...")
        print(f"  python {sys.argv[0]} /path/to/paper1.pdf /path/to/paper2.pdf")
        sys.exit(1)
    
    files = sys.argv[1:]
    asyncio.run(upload_to_global_index(files))
