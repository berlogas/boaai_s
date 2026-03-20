#!/usr/bin/env python3
"""
Проверка содержимого индексов PaperQA.
Показывает все документы в глобальном индексе и индексах сессий.
"""

import pickle
from pathlib import Path

DATA_VOLUME = Path("/app/data")
GLOBAL_INDEX = Path("/app/global_index")


def check_index(index_path: Path, name: str):
    """Проверка индекса."""
    print(f"\n{'=' * 70}")
    print(f"📚 {name}: {index_path}")
    print('=' * 70)
    
    pkl_path = index_path / "docs.pkl"
    if not pkl_path.exists():
        print(f"❌ Индекс не найден: {pkl_path}")
        return
    
    with open(pkl_path, 'rb') as f:
        docs = pickle.load(f)
    
    docnames = docs.docnames if docs.docnames else []
    print(f"✅ Документов в индексе: {len(docnames)}")
    
    if docnames:
        print("\nСписок документов:")
        for i, name in enumerate(docnames, 1):
            print(f"  {i}. 📄 {name}")
    
    # Проверяем текстовые фрагменты
    texts = docs.texts if docs.texts else []
    print(f"\n📝 Текстовых фрагментов: {len(texts)}")
    
    if texts:
        print("\nПримеры фрагментов:")
        for i, text in enumerate(texts[:3], 1):
            doc_name = text.name if hasattr(text, 'name') else 'N/A'
            text_content = text.text if hasattr(text, 'text') else 'N/A'
            print(f"\n  {i}. 📄 {doc_name}")
            print(f"     Текст: {text_content[:150]}...")


def main():
    print("\n" + "🔍" * 35)
    print("ПРОВЕРКА ИНДЕКСОВ PAPERQA")
    print("🔍" * 35)
    
    # Глобальный индекс
    check_index(GLOBAL_INDEX, "ГЛОБАЛЬНЫЙ ИНДЕКС")
    
    # Индексы сессий
    indices_path = DATA_VOLUME / "indices"
    if indices_path.exists():
        session_indices = list(indices_path.iterdir())
        if session_indices:
            for session_dir in session_indices:
                check_index(session_dir, f"ИНДЕКС СЕССИИ: {session_dir.name}")
        else:
            print("\n⚠️ Индексы сессий не найдены")
    
    print("\n" + "=" * 70)
    print("✅ ПРОВЕРКА ЗАВЕРШЕНА")
    print("=" * 70)
    
    # Инструкция
    print("\n📋 КАК УБЕДИТЬСЯ, ЧТО ОТВЕТЫ ИЗ ВАШИХ PDF:")
    print("=" * 70)
    print("""
1. Найдите ваш документ в списке выше
   - Если документ есть в списке → он проиндексирован
   
2. Задайте вопрос через веб-интерфейс (http://localhost:8501)
   - В ответе должны быть указаны источники
   - Имя источника должно совпадать с именем из списка выше
   
3. Проверьте логи backend:
   docker-compose logs -f backend | grep "📄"
   
4. Если документ НЕ в списке:
   - Загрузите его через веб-интерфейс
   - Или используйте скрипт upload_global.py
   
5. Для проверки конкретного запроса:
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
       result = await docs.aquery("ВАШ ВОПРОС", settings=settings)
       print("Ответ:", result.answer)
       print("Источники:", [c.text.name for c in result.contexts if c.text])
   
   asyncio.run(test())
   EOF
    """)


if __name__ == "__main__":
    main()
