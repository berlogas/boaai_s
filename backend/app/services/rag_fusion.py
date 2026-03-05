import asyncio
from typing import List, Dict, Optional
import litellm
from core.config import settings
from core.paperqa_manager import PaperQAManager
class RAGFusionEngine:
    def __init__(self):
        self.global_pqa = PaperQAManager(index_path=settings.GLOBAL_INDEX_PATH)
        self.session_pqa_cache = {}
    
    def _get_session_pqa(self, session_id: str) -> PaperQAManager:
        if session_id not in self.session_pqa_cache:
            index_path = f"{settings.DATA_PATH}/indices/{session_id}"
            self.session_pqa_cache[session_id] = PaperQAManager(index_path=index_path)
        return self.session_pqa_cache[session_id]
    
    async def query(self, query: str, session_id: Optional[str] = None, mode: str = "hybrid", project_id: Optional[str] = None) -> Dict:
        contexts = []
        sources_info = []
        
        if mode in ["hybrid", "global_only"]:
            try:
                global_results = await self.global_pqa.search(query, top_k=3)
                for res in global_results:
                    contexts.append({"source": "📚 Global", "text": res.get("text", ""), "priority": 4})
                    sources_info.append({"type": "global", "name": res.get("source", "Unknown")})
            except Exception as e:
                print(f"Global search error: {e}")
        
        if session_id and mode in ["hybrid", "session_only", "project_focus"]:
            session_pqa = self._get_session_pqa(session_id)
            try:
                session_results = await session_pqa.search(query, top_k=5)
                for res in session_results:
                    category = res.get("category", "temp_literature")
                    priority = 1 if category in ["project_draft", "project_data"] else 3
                    contexts.append({"source": "📁 Session", "text": res.get("text", ""), "priority": priority})
                    sources_info.append({"type": "session", "name": res.get("source", "Unknown")})
            except Exception as e:
                print(f"Session search error: {e}")
        
        contexts.sort(key=lambda x: x["priority"])
        contexts = contexts[:10]
        
        context_text = "\n\n".join([f"[{c['source']}] {c['text']}" for c in contexts])
        
        system_prompt = "Ты научный ассистент. Отвечай ТОЛЬКО на основе контекста. Указывай источники (📚 или 📁)."
        user_prompt = f"Контекст:\n{context_text}\n\nВопрос: {query}"
        
        try:
            response = await litellm.acompletion(
                model=f"ollama/{settings.DEFAULT_LLM_MODEL}",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                api_base=settings.OLLAMA_BASE_URL,
                temperature=0.3            )
            return {"answer": response.choices[0].message.content, "sources": sources_info, "contexts_used": len(contexts), "mode": mode}
        except Exception as e:
            return {"answer": f"Ошибка: {str(e)}", "sources": [], "contexts_used": 0, "mode": mode}
    
    async def quick_query(self, query: str) -> Dict:
        return await self.query(query, session_id=None, mode="global_only")

rag_engine = RAGFusionEngine()
