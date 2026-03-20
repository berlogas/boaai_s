#!/usr/bin/env python3
"""
Скрипт для проверки источников в ответах PaperQA.
Показывает, из каких документов взяты цитаты.
"""

import asyncio
import sys
from pathlib import Path

# Добавляем backend в path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from paperqa import Docs, Settings
import pickle


async def test_query_with_sources(query: str, index_path: str = "/app/global_index"):
    """Тестовый запрос с показом источников."""
    
    # Загружаем индекс
    pkl_path = Path(index_path) / "docs.pkl"
    if not pkl_path.exists():
        print(f"❌ Индекс не найден: {pkl_path}")
        return
    
    with open(pkl_path, 'rb') as f:
        docs = pickle.load(f)
    
    print(f"\n📚 Индекс: {index_path}")
    print(f"📄 Документов в индексе: {len(docs.docnames) if docs.docnames else 0}")
    if docs.docnames:
        print("\nДоступные документы:")
        for name in docs.docnames:
            print(f"  • {name}")
    
    # Настройки для Ollama
    settings = Settings(
        llm="ollama/llama3.1:8b",
        summary_llm="ollama/llama3.1:8b",
        embedding="ollama/nomic-embed-text",
        temperature=0.1,
    )
    
    print(f"\n🔍 Запрос: {query}")
    print("=" * 70)
    
    # Выполняем запрос
    result = await docs.aquery(query, settings=settings)
    
    print(f"\n💬 Ответ:\n{result.answer}")
    
    print(f"\n📖 Источники ({len(result.contexts)}):")
    print("=" * 70)
    
    for i, ctx in enumerate(result.contexts, 1):
        print(f"\n{i}. 📄 Документ: {ctx.docname}")
        print(f"   Цитата: {ctx.citation}")
        print(f"   Текст: {ctx.text[:300]}...")
        print(f"   Релевантность: {getattr(ctx, 'score', 'N/A')}")
    
    print("\n" + "=" * 70)
    print("✅ Проверка завершена")
    
    # Возвращаем имена использованных документов
    used_docs = list(set(ctx.docname for ctx in result.contexts))
    print(f"\n📋 Использовано документов: {len(used_docs)}")
    for doc in used_docs:
        print(f"  ✓ {doc}")
    
    return used_docs


async def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "What is attention mechanism in transformers?"
    
    await test_query_with_sources(query)


if __name__ == "__main__":
    asyncio.run(main())
