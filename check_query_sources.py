import asyncio
import pickle
from pathlib import Path
from paperqa import Settings

async def check_query_sources():
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
    print(f"\n🔍 Запрос: {query}\n" + "=" * 70)
    
    result = await docs.aquery(query, settings=settings)
    
    print(f"\n💬 Ответ:\n{result.answer[:300]}...\n")
    
    print(f"📖 Контексты ({len(result.contexts)}):")
    for i, ctx in enumerate(result.contexts, 1):
        print(f"\n{i}. Атрибуты context:")
        for attr in dir(ctx):
            if not attr.startswith('_'):
                val = getattr(ctx, attr, 'N/A')
                if not callable(val) and isinstance(val, (str, int, float)):
                    print(f"    {attr}: {val}")
        
        print(f"    text.name: {getattr(ctx, 'text', None)}")
        if ctx.text:
            print(f"    text.name.value: {ctx.text.name}")
            print(f"    text.text: {ctx.text.text[:100]}...")

if __name__ == "__main__":
    asyncio.run(check_query_sources())
