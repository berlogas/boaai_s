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
        """Инициализация PaperQA. Вызывать только внутри add_document с захваченным lock."""
        if self.docs is None:
            logger.info(f"Инициализация PaperQA для {self.index_path}")
            # Пробуем загрузить существующий индекс через pickle
            index_file = os.path.join(self.index_path, "docs.pkl")
            if os.path.exists(index_file):
                try:
                    logger.info("Загрузка существующего индекса...")
                    # Загружаем pickle в отдельном потоке чтобы не блокировать event loop
                    def load_pickle():
                        with open(index_file, 'rb') as f:
                            return pickle.load(f)
                    self.docs = await asyncio.to_thread(load_pickle)
                    logger.info("Индекс загружен")
                except Exception as e:
                    logger.error(f"Failed to load index: {e}")
                    self.docs = Docs()
            else:
                self.docs = Docs()

    async def add_document(self, file_path: str, doc_name: str, category: str = "temp_literature", project_id: Optional[str] = None) -> bool:
        async with self._lock:
            # Проверяем инициализацию внутри lock
            if self.docs is None:
                await self.initialize()
            try:
                start_time = datetime.now()
                logger.info(f"Начало добавления документа: {doc_name}")
                logger.info(f"  Шаг 1/3: Чтение файла и создание эмбеддингов...")

                # PaperQA 2026.3.3 использует async метод aadd
                # Конфигурация для Ollama
                from paperqa import Settings as PaperQASettings
                
                pqa_settings = PaperQASettings(
                    llm=f"ollama/{settings.DEFAULT_LLM_MODEL}",
                    summary_llm=f"ollama/{settings.DEFAULT_LLM_MODEL}",
                    embedding=f"ollama/{settings.DEFAULT_EMBEDDING_MODEL}",
                )

                # Используем async метод aadd напрямую
                await self.docs.aadd(
                    file_path,
                    docname=doc_name,
                    citation=category,
                    settings=pqa_settings
                )

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
        async with self._lock:
            if self.docs is None:
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
