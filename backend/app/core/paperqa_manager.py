import os
import asyncio
import logging
import pickle
from typing import List, Dict, Optional
from datetime import datetime

from paperqa import Docs, Settings
from core.config import settings

logger = logging.getLogger(__name__)

class PaperQAManager:
    def __init__(self, index_path: str):
        self.index_path = index_path
        self.docs = None
        self._lock = asyncio.Lock()
        os.makedirs(index_path, exist_ok=True)

    async def initialize(self):
        async with self._lock:
            if self.docs is None:
                logger.info(f"Инициализация PaperQA для {self.index_path}")
                self.docs = Docs()
                # Пробуем загрузить существующий индекс через pickle
                index_file = os.path.join(self.index_path, "docs.pkl")
                if os.path.exists(index_file):
                    try:
                        logger.info("Загрузка существующего индекса...")
                        with open(index_file, 'rb') as f:
                            self.docs = pickle.load(f)
                        logger.info("Индекс загружен")
                    except Exception as e:
                        logger.error(f"Failed to load index: {e}")

    async def add_document(self, file_path: str, doc_name: str, category: str = "temp_literature", project_id: Optional[str] = None) -> bool:
        async with self._lock:
            await self.initialize()
            try:
                start_time = datetime.now()
                logger.info(f"Начало добавления документа: {doc_name}")
                logger.info(f"  Шаг 1/3: Чтение файла и создание эмбеддингов...")

                # Конфигурация для Ollama через litellm
                ollama_llm_config = {
                    "model_list": [
                        {
                            "model_name": f"ollama/{settings.DEFAULT_LLM_MODEL}",
                            "litellm_params": {
                                "model": f"ollama/{settings.DEFAULT_LLM_MODEL}",
                                "api_base": settings.OLLAMA_BASE_URL,
                            },
                        }
                    ]
                }

                # В версии 5.29.1 используем sync метод add
                def add_sync():
                    d = Docs()
                    d.add(
                        file_path,
                        docname=doc_name,
                        citation=category,
                        disable_check=True,
                        settings=Settings(
                            llm=f"ollama/{settings.DEFAULT_LLM_MODEL}",
                            llm_config=ollama_llm_config,
                            summary_llm=f"ollama/{settings.DEFAULT_LLM_MODEL}",
                            summary_llm_config=ollama_llm_config,
                            embedding=f"ollama/{settings.DEFAULT_EMBEDDING_MODEL}",
                            embedding_config=ollama_llm_config,
                        )
                    )
                    return d
                
                # Запускаем в отдельном потоке
                loop = asyncio.get_event_loop()
                self.docs = await loop.run_in_executor(None, add_sync)
                
                logger.info(f"  Шаг 2/3: Сохранение индекса через pickle...")
                # Сохраняем через pickle
                index_file = os.path.join(self.index_path, "docs.pkl")
                os.makedirs(self.index_path, exist_ok=True)
                with open(index_file, 'wb') as f:
                    pickle.dump(self.docs, f)
                
                logger.info(f"  Шаг 3/3: Готово")

                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"Документ {doc_name} добавлен за {elapsed:.2f} сек")
                return True
            except Exception as e:
                logger.error(f"Error adding document {doc_name}: {e}")
                import traceback
                logger.error(traceback.format_exc())
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
            logger.error(f"Search error: {e}")
            return []

    async def rebuild_index(self):
        async with self._lock:
            logger.info("Пересоздание индекса...")
            self.docs = Docs()
            # Очищаем старый индекс
            index_file = os.path.join(self.index_path, "docs.pkl")
            if os.path.exists(index_file):
                os.remove(index_file)
            logger.info("Индекс пересоздан")
