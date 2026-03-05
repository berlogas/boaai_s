import os
import asyncio
from typing import List, Dict, Optional

from paperqa import Docs, Settings
from core.config import settings

class PaperQAManager:
    def __init__(self, index_path: str):
        self.index_path = index_path
        self.docs = None
        self._lock = asyncio.Lock()
        os.makedirs(index_path, exist_ok=True)
    
    async def initialize(self):
        async with self._lock:
            if self.docs is None:
                self.docs = Docs()
                index_file = os.path.join(self.index_path, "index.json")
                if os.path.exists(index_file):
                    try:
                        self.docs.load(self.index_path)
                    except Exception as e:
                        print(f"Failed to load index: {e}")
    
    async def add_document(self, file_path: str, doc_name: str, category: str = "temp_literature", project_id: Optional[str] = None) -> bool:
        async with self._lock:
            await self.initialize()
            try:
                self.docs.add(file_path, docname=doc_name, citation=category)
                self.docs.save(self.index_path)
                return True
            except Exception as e:
                print(f"Error adding document: {e}")
                return False
    
    async def search(self, query: str, top_k: int = 5) -> List[Dict]:
        await self.initialize()
        try:
            results = await self.docs.query(query, settings=Settings(answer=False, k=top_k))
            contexts = []            
            if hasattr(results, 'contexts') and results.contexts:
                for ctx in results.contexts:
                    contexts.append({
                        "text": ctx.text,
                        "source": ctx.docname,
                        "citation": ctx.citation,
                        "category": ctx.citation
                    })
            return contexts
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    async def rebuild_index(self):
        async with self._lock:
            self.docs = Docs()
