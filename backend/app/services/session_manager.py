import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from fastapi import HTTPException, status

import aiofiles
import aiofiles.os

from core.config import settings

SESSIONS_FILE = os.path.join(settings.DATA_PATH, "sessions.json")


class SessionManager:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._ensure_file()

    def _ensure_file(self):
        """Синхронная инициализация файла (только при старте)."""
        os.makedirs(os.path.dirname(SESSIONS_FILE), exist_ok=True)
        if not os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, 'w') as f:
                json.dump({}, f)

    async def _load(self) -> Dict:
        """Асинхронное чтение сессий."""
        async with aiofiles.open(SESSIONS_FILE, 'r', encoding='utf-8') as f:
            content = await f.read()
            return json.loads(content)

    async def _save(self, data: Dict):
        """Атомарная асинхронная запись."""
        temp_file = f"{SESSIONS_FILE}.tmp"
        async with aiofiles.open(temp_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, indent=2, ensure_ascii=False))
        await aiofiles.os.rename(temp_file, SESSIONS_FILE)

    async def create_session(self, user_id: str, name: str) -> dict:
        async with self._lock:
            sessions = await self._load()
            user_sessions = [s for s in sessions.values() if s['user_id'] == user_id and s['status'] != 'archived']
            if len(user_sessions) >= settings.MAX_SESSIONS_PER_USER:
                raise HTTPException(status_code=400, detail=f"Максимум {settings.MAX_SESSIONS_PER_USER} сессий")

            session_id = f"{user_id}_{int(datetime.now().timestamp())}"
            session_data = {
                "id": session_id,
                "user_id": user_id,
                "name": name,
                "created_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
                "status": "active",
                "documents": [],
                "chat_history": [],
                "projects": [],
                "last_action": "Сессия создана",
                "storage_used_mb": 0
            }
            sessions[session_id] = session_data
            await self._save(sessions)
            return session_data

    async def get_session(self, session_id: str, user_id: Optional[str] = None) -> Optional[dict]:
        sessions = await self._load()
        session = sessions.get(session_id)
        if not session:
            return None
        if user_id and session['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Доступ запрещён")
        
        # Проверка TTL
        last_active = datetime.fromisoformat(session["last_active"])
        if datetime.now() - last_active > timedelta(days=settings.SESSION_TTL_DAYS):
            if session["status"] != "archived":
                session["status"] = "archived"
                sessions[session_id] = session
                await self._save(sessions)
            raise HTTPException(status_code=403, detail="Сессия архивирована")
        
        return session

    async def heartbeat(self, session_id: str, user_id: str) -> dict:
        async with self._lock:
            session = await self.get_session(session_id, user_id)
            if not session:
                raise HTTPException(status_code=404, detail="Сессия не найдена")
            
            sessions = await self._load()
            sessions[session_id]["last_active"] = datetime.now().isoformat()
            if sessions[session_id]["status"] == "paused":
                sessions[session_id]["status"] = "active"
            
            await self._save(sessions)
            return sessions[session_id]

    async def add_document(self, session_id: str, user_id: str, doc_meta: dict) -> dict:
        async with self._lock:
            session = await self.get_session(session_id, user_id)
            if not session:
                raise HTTPException(status_code=404, detail="Сессия не найдена")
            
            if len(session["documents"]) >= settings.MAX_DOCS_PER_SESSION:
                raise HTTPException(status_code=400, detail=f"Максимум {settings.MAX_DOCS_PER_SESSION} документов")
            
            new_storage = session["storage_used_mb"] + doc_meta.get("size_mb", 0)
            if new_storage > settings.MAX_STORAGE_MB_PER_SESSION:
                raise HTTPException(status_code=400, detail=f"Превышен лимит хранилища")
            
            sessions = await self._load()
            sessions[session_id]["documents"].append(doc_meta)
            sessions[session_id]["storage_used_mb"] = new_storage
            sessions[session_id]["last_active"] = datetime.now().isoformat()
            
            await self._save(sessions)
            return sessions[session_id]

    async def get_user_sessions(self, user_id: str) -> List[dict]:
        sessions = await self._load()
        user_sessions = [s for s in sessions.values() if s['user_id'] == user_id]
        user_sessions.sort(key=lambda x: x['last_active'], reverse=True)
        return user_sessions

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        async with self._lock:
            sessions = await self._load()
            if session_id not in sessions:
                return False
            if sessions[session_id]['user_id'] != user_id:
                raise HTTPException(status_code=403, detail="Доступ запрещён")
            
            del sessions[session_id]
            await self._save(sessions)
            return True
    
    async def close(self):
        """Заглушка для совместимости."""
        pass


session_manager = SessionManager()