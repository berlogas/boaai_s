import asyncio
import json
import os
from paperqa import Docs, Settings

async def test():
    print('Testing PaperQA with Ollama URL...')
    docs = Docs()
    
    # Используем llm_config для указания URL
    settings = Settings(
        llm='ollama/llama3.1:8b',
        llm_config={
            'api_base': 'http://ollama:11434'
        },
        summary_llm='ollama/llama/llama3.1:8b',
        summary_llm_config={
            'api_base': 'http://ollama:11434'
        },
        embedding='ollama/nomic-embed-text',
        embedding_config={
            'api_base': 'http://ollama:11434'
        },
    )
    
    print('Adding file...')
    await docs.aadd(
        '/app/uploads/ADMIN_GUIDE.md',
        docname='ADMIN_GUIDE.md',
        citation='test',
        settings=settings
    )
    
    # Сохраняем через model_dump
    print('Saving...')
    index_path = '/app/global_index'
    os.makedirs(index_path, exist_ok=True)
    
    # Сериализуем и сохраняем
    docs_data = docs.model_dump_json()
    with open(os.path.join(index_path, 'docs.json'), 'w') as f:
        f.write(docs_data)
    
    print('✅ Done!')

asyncio.run(test())
