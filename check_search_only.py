import asyncio
import pickle
from pathlib import Path
from paperqa import Settings

async def check_search_only():
    pkl_path = Path('/app/global_index/docs.pkl')
    with open(pkl_path, 'rb') as f:
        docs = pickle.load(f)
    
    print(f"📚 Документы в индексе: {len(docs.docnames)}")
    for name in docs.docnames:
        print(f"  • {name}")
    
    settings = Settings(
        llm="ollama/llama3.1:8b",
        summary_llm="ollama/llama3.1:8b",
        embedding="ollama/nomic-embed-text",
        temperature=0.1,
    )
    
    query = "test document"
    print(f"\n🔍 Поиск (без генерации ответа): {query}\n" + "=" * 70)
    
    # Используем get_evidence вместо query
    evidence_result = await docs.aget_evidence(query, settings=settings)
    
    print(f"\n📖 Найдено контекстов: {len(evidence_result.contexts)}")
    for i, ctx in enumerate(evidence_result.contexts, 1):
        print(f"\n{i}. Источник:")
        if ctx.text:
            print(f"    Имя: {ctx.text.name}")
            print(f"    Текст: {ctx.text.text[:150]}...")
        if hasattr(ctx, 'score'):
            print(f"    Релевантность: {ctx.score}")

if __name__ == "__main__":
    asyncio.run(check_search_only())
