import os
import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path

from paperqa import Docs, Settings
from paperqa.settings import AgentSettings, IndexSettings

from core.config import settings

logger = logging.getLogger(__name__)


class PaperQAManager:
    """
    Менеджер для PaperQA 2026.03.03.
    Использует pickle для сохранения индекса Docs (единственный способ в 2026.03.03).
    """
    
    def __init__(self, index_path: str):
        self.index_path = Path(index_path)
        self.docs: Optional[Docs] = None
        self._lock = asyncio.Lock()
        self._initialized = False
        
        # Создаем директории
        self.index_path.mkdir(parents=True, exist_ok=True)
        (self.index_path / "papers").mkdir(exist_ok=True)
        
        # Настройки PaperQA 2026.03.03
        self.settings = self._create_settings()
    
    def _create_settings(self) -> Settings:
        """Создание настроек для PaperQA 2026.03.03."""

        # Конфигурация для Ollama через litellm
        ollama_llm_config = {
            "model_list": [
                {
                    "model_name": f"ollama/{settings.DEFAULT_LLM_MODEL}",
                    "litellm_params": {
                        "model": f"ollama/{settings.DEFAULT_LLM_MODEL}",
                        "api_base": settings.OLLAMA_BASE_URL,
                        "timeout": settings.OLLAMA_TIMEOUT,
                        "temperature": 0.1,
                        "max_tokens": 4096,
                    },
                }
            ]
        }

        ollama_embedding_config = {
            "model_list": [
                {
                    "model_name": f"ollama/{settings.DEFAULT_EMBEDDING_MODEL}",
                    "litellm_params": {
                        "model": f"ollama/{settings.DEFAULT_EMBEDDING_MODEL}",
                        "api_base": settings.OLLAMA_BASE_URL,
                        "timeout": settings.OLLAMA_TIMEOUT,
                    },
                }
            ]
        }

        # ✅ PaperQA 2026.03.03: используем IndexSettings для автоматического управления индексом
        return Settings(
            llm=f"ollama/{settings.DEFAULT_LLM_MODEL}",
            llm_config=ollama_llm_config,
            summary_llm=f"ollama/{settings.DEFAULT_LLM_MODEL}",
            summary_llm_config=ollama_llm_config,
            embedding=f"ollama/{settings.DEFAULT_EMBEDDING_MODEL}",
            embedding_config=ollama_embedding_config,
            temperature=0.1,
            batch_size=1,
            verbosity=1,

            # AgentSettings с IndexSettings — PaperQA сама управляет индексом
            agent=AgentSettings(
                agent_llm=f"ollama/{settings.DEFAULT_LLM_MODEL}",
                agent_llm_config=ollama_llm_config,
                search_count=8,
                index=IndexSettings(
                    paper_directory=self.index_path / "papers",
                    index_directory=self.index_path / "index",
                    manifest_file=None,
                    sync_with_paper_directory=True,  # ✅ Авто-синхронизация
                ),
            ),
        )
    
    async def initialize(self):
        """Асинхронная инициализация Docs."""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            print(f"🔧 Инициализация PaperQA 2026.03.03 для {self.index_path}")
            logger.info(f"Инициализация PaperQA 2026.03.03 для {self.index_path}")

            # Создаем Docs
            self.docs = Docs()

            # ✅ Загружаем индекс из pickle (если существует)
            await self._load_index()

            self._initialized = True
            print(f"✅ Инициализация завершена")
            logger.info("Инициализация завершена")

    async def _load_index(self):
        """Загрузка индекса из pickle файла."""
        pkl_path = self.index_path / "docs.pkl"
        if pkl_path.exists():
            try:
                import pickle
                with open(pkl_path, 'rb') as f:
                    self.docs = pickle.load(f)
                # ✅ В PaperQA 2026.03.03 клиент восстанавливается автоматически
                print(f"✅ Индекс загружен из {pkl_path}")
                logger.info(f"✅ Индекс загружен из {pkl_path}")
            except Exception as e:
                print(f"⚠️ Не удалось загрузить индекс: {e}")
                logger.warning(f"Не удалось загрузить индекс: {e}")

    async def _save_index(self):
        """Сохранение индекса в pickle файл."""
        if not self.docs:
            return
        
        import pickle
        pkl_path = self.index_path / "docs.pkl"
        
        try:
            with open(pkl_path, 'wb') as f:
                pickle.dump(self.docs, f)
            logger.info(f"Индекс сохранён в {pkl_path}")
        except Exception as e:
            logger.error(f"Ошибка сохранения индекса: {e}")
    
    async def add_document(
        self, 
        file_path: str, 
        doc_name: str, 
        category: str = "temp_literature", 
        project_id: Optional[str] = None
    ) -> bool:
        """
        Добавление документа в индекс.
        PaperQA 2026.03.03 сама выбирает ридер (PyPDF, PyMuPDF, etc.).
        """
        await self.initialize()
        
        async with self._lock:
            try:
                start_time = datetime.now()
                logger.info(f"Начало добавления документа: {doc_name}")
                
                # Проверяем существование файла
                if not os.path.exists(file_path):
                    logger.error(f"Файл не найден: {file_path}")
                    return False
                
                # ✅ PaperQA 2026.03.03: полностью асинхронный метод aadd
                await self.docs.aadd(
                    file_path,
                    docname=doc_name,
                    citation=category,
                    settings=self.settings,
                )

                # ✅ Сохраняем индекс через pickle (единственный способ в 2026.03.03)
                await self._save_index()

                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"Документ {doc_name} добавлен за {elapsed:.2f} сек")
                return True
                
            except Exception as e:
                logger.error(f"Error adding document {doc_name}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return False
    
    async def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Поиск по индексу без генерации ответа.
        Возвращает только контексты.
        """
        await self.initialize()
        
        try:
            # ✅ PaperQA 2026.03.03: используем aquery с answer=False
            # или используем search (если доступен)
            results: Any = await self.docs.aquery(
                query,
                settings=self.settings,
            )
            
            contexts = []
            if results.contexts:
                for ctx in results.contexts[:top_k]:
                    contexts.append({
                        "text": ctx.text,
                        "source": ctx.docname,
                        "citation": ctx.citation,
                        "category": ctx.citation,
                        "score": getattr(ctx, 'score', None),
                    })
            return contexts
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    async def query_with_answer(self, query: str) -> Dict:
        """
        Полный запрос с генерацией ответа.
        """
        await self.initialize()
        
        try:
            results: Any = await self.docs.aquery(
                query,
                settings=self.settings,
            )
            
            return {
                "answer": results.answer or "Нет ответа",
                "contexts": [
                    {
                        "text": ctx.text,
                        "source": ctx.docname,
                        "citation": ctx.citation,
                    }
                    for ctx in results.contexts
                ],
                "references": results.references or [],
            }
            
        except Exception as e:
            logger.error(f"Query error: {e}")
            return {"answer": f"Ошибка: {str(e)}", "contexts": [], "references": []}
    
    async def rebuild_index(self):
        """Пересоздание индекса с нуля."""
        async with self._lock:
            logger.info("Пересоздание индекса...")

            # Пересоздаем Docs
            self.docs = Docs()
            self._initialized = True

            # Сохраняем пустой индекс
            await self._save_index()

            logger.info("Индекс пересоздан")

    async def close(self):
        """Закрытие ресурсов."""
        # В PaperQA 2026.03.03 Docs не требует закрытия ресурсов
        logger.info(f"PaperQA менеджер для {self.index_path} закрыт")