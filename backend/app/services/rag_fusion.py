import asyncio
import logging
from typing import List, Dict, Optional

from core.config import settings
from core.paperqa_manager import PaperQAManager

logger = logging.getLogger(__name__)


class RAGFusionEngine:
    """
    RAG Fusion движок для PaperQA 2026.03.03.
    Полностью асинхронный, без блокировок.
    """
    
    def __init__(self):
        self.global_pqa = PaperQAManager(index_path=settings.GLOBAL_INDEX_PATH)
        self.session_pqa_cache: Dict[str, PaperQAManager] = {}
        self._cache_lock = asyncio.Lock()
    
    async def _get_session_pqa(self, session_id: str) -> PaperQAManager:
        """Получение или создание менеджера для сессии."""
        async with self._cache_lock:
            if session_id not in self.session_pqa_cache:
                index_path = f"{settings.DATA_PATH}/indices/{session_id}"
                self.session_pqa_cache[session_id] = PaperQAManager(index_path=index_path)
                # Инициализируем сразу
                await self.session_pqa_cache[session_id].initialize()
            return self.session_pqa_cache[session_id]
    
    async def query(
        self, 
        query: str, 
        session_id: Optional[str] = None, 
        mode: str = "hybrid", 
        project_id: Optional[str] = None
    ) -> Dict:
        """
        Гибридный запрос к глобальной и сессионной базам.
        """
        contexts = []
        sources_info = []
        
        # Параллельный поиск в обоих источниках
        tasks = []
        
        if mode in ["hybrid", "global_only"]:
            tasks.append(self._search_global(query))
        else:
            tasks.append(asyncio.sleep(0, result=[]))
        
        if session_id and mode in ["hybrid", "session_only", "project_focus"]:
            tasks.append(self._search_session(query, session_id))
        else:
            tasks.append(asyncio.sleep(0, result=[]))
        
        # Запускаем параллельно
        global_results, session_results = await asyncio.gather(*tasks)
        
        # Обрабатываем результаты глобального поиска
        for res in global_results:
            contexts.append({
                "source": "📚",
                "text": res.get("text", ""),
                "priority": 4,
                "doc_name": res.get("source", "Unknown")
            })
            sources_info.append({
                "type": "global",
                "name": res.get("source", "Unknown")
            })

        # Обрабатываем результаты сессионного поиска
        for res in session_results:
            category = res.get("category", "temp_literature")
            priority = 1 if category in ["project_draft", "project_data"] else 3
            contexts.append({
                "source": "📁",
                "text": res.get("text", ""),
                "priority": priority,
                "doc_name": res.get("source", "Unknown")
            })
            sources_info.append({
                "type": "session",
                "name": res.get("source", "Unknown")
            })
        
        # Сортируем и ограничиваем контекст
        contexts.sort(key=lambda x: x["priority"])
        contexts = contexts[:10]

        # Формируем промпт с явным указанием источников
        context_text = "\n\n".join([
            f"[{c['source']} {c['doc_name']}] {c['text']}" for c in contexts
        ])

        system_prompt = (
            "Ты научный ассистент. Отвечай ТОЛЬКО на основе предоставленного контекста. "
            "В конце ответа укажи источники, которые ты использовал, в формате: "
            "Источники: 📚 [имя документа] или 📁 [имя документа]. "
            "Если информация из нескольких источников, перечисли их все."
        )
        user_prompt = f"Контекст:\n{context_text}\n\nВопрос: {query}"
        
        # Генерируем ответ через LLM
        try:
            import litellm
            
            # Логируем контекст для отладки
            logger.info(f"RAG Fusion: найдено {len(contexts)} контекстов")
            for i, ctx in enumerate(contexts[:3], 1):
                logger.info(f"  Контекст {i}: {ctx['source']} {ctx['doc_name']}")

            response = await litellm.acompletion(
                model=f"ollama/{settings.DEFAULT_LLM_MODEL}",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                api_base=settings.OLLAMA_BASE_URL,
                temperature=0.3,
                timeout=settings.OLLAMA_TIMEOUT
            )
            
            return {
                "answer": response.choices[0].message.content,
                "sources": sources_info,
                "contexts_used": len(contexts),
                "mode": mode
            }
            
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return {
                "answer": f"Ошибка генерации ответа: {str(e)}",
                "sources": sources_info,
                "contexts_used": len(contexts),
                "mode": mode
            }
    
    async def _search_global(self, query: str) -> List[Dict]:
        """Поиск в глобальной базе."""
        try:
            return await self.global_pqa.search(query, top_k=3)
        except Exception as e:
            logger.error(f"Global search error: {e}")
            return []
    
    async def _search_session(self, query: str, session_id: str) -> List[Dict]:
        """Поиск в сессионной базе."""
        try:
            session_pqa = await self._get_session_pqa(session_id)
            return await session_pqa.search(query, top_k=5)
        except Exception as e:
            logger.error(f"Session search error: {e}")
            return []
    
    async def quick_query(self, query: str) -> Dict:
        """Быстрый запрос только к глобальной базе."""
        return await self.query(query, session_id=None, mode="global_only")

    async def close(self):
        """Закрытие всех ресурсов."""
        await self.global_pqa.close()
        for pqa in self.session_pqa_cache.values():
            await pqa.close()


# ✅ Создаём экземпляр для импорта в main.py
rag_engine = RAGFusionEngine()