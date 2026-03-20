#!/usr/bin/env python3
"""
Тестовый запрос к RAG Fusion с проверкой источников.
"""

import asyncio
import sys
sys.path.insert(0, '/app')

from app.services.rag_fusion import rag_engine


async def test_query():
    query = "Какие архитектуры нейронных сетей подходят для последовательных данных?"
    
    print(f"\n🔍 Запрос: {query}")
    print("=" * 70)
    
    result = await rag_engine.query(
        query=query,
        session_id=None,  # Только глобальная база
        mode="global_only"
    )
    
    print(f"\n💬 Ответ:\n{result['answer']}")
    print(f"\n📚 Источники:")
    for src in result.get('sources', []):
        print(f"  • {src['type']}: {src['name']}")
    
    print(f"\n📄 Использовано контекстов: {result.get('contexts_used', 0)}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_query())
