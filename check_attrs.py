import asyncio
import pickle
from pathlib import Path

async def check_context_attrs():
    pkl_path = Path('/app/global_index/docs.pkl')
    with open(pkl_path, 'rb') as f:
        docs = pickle.load(f)
    
    if docs.texts:
        text_obj = docs.texts[0]
        print("Атрибуты text объекта:")
        for attr in dir(text_obj):
            if not attr.startswith('_'):
                print(f"  {attr}")
        
        print("\n\nЗначения:")
        print(f"  text.text: {getattr(text_obj, 'text', 'N/A')[:100]}")
        print(f"  text.name: {getattr(text_obj, 'name', 'N/A')}")
        print(f"  text.docname: {getattr(text_obj, 'docname', 'N/A')}")
        print(f"  text.doc_id: {getattr(text_obj, 'doc_id', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(check_context_attrs())
