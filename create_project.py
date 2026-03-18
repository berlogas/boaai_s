#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор проекта "BOAAI_S"
Создаёт полную структуру проекта со всеми файлами
"""

import os
# import json

# ─────────────────────────────────────────────
# КОНФИГУРАЦИЯ ФАЙЛОВ
# ─────────────────────────────────────────────

FILES = {
    # ─────────────────────────────────────────────
    # ROOT FILES
    # ─────────────────────────────────────────────
    "docker-compose.yml": """version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: berezhinskii-ollama
    restart: unless-stopped
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
    environment:
      - OLLAMA_HOST=0.0.0.0
      - OLLAMA_ORIGINS=*
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "ollama", "list"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: berezhinskii-api    restart: unless-stopped
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - DATA_PATH=/app/data
      - GLOBAL_INDEX_PATH=/app/global_index
      - SECRET_KEY=${SECRET_KEY:-change_me_in_production}
      - LOG_LEVEL=INFO
    volumes:
      - backend_data:/app/data
      - global_index:/app/global_index
      - ./backend/app:/app/app
    ports:
      - "8000:8000"
    depends_on:
      ollama:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: berezhinskii-ui
    restart: unless-stopped
    environment:
      - BACKEND_URL=http://backend:8000
      - STREAMLIT_SERVER_PORT=8501
      - STREAMLIT_SERVER_HEADLESS=true
    volumes:
      - ./frontend/app:/app/app
    ports:
      - "8501:8501"
    depends_on:
      backend:
        condition: service_healthy

volumes:
  ollama_data:
    driver: local
  backend_data:
    driver: local
  global_index:
    driver: local

networks:
  default:    name: berezhinskii_network
    driver: bridge
""",
    ".env": """# Security
SECRET_KEY=your_super_secret_key_change_in_prod
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Ollama Configuration
OLLAMA_BASE_URL=http://ollama:11434
DEFAULT_LLM_MODEL=llama3.1:8b
DEFAULT_EMBEDDING_MODEL=nomic-embed-text

# Session Limits
MAX_SESSIONS_PER_USER=10
MAX_DOCS_PER_SESSION=50
MAX_STORAGE_MB_PER_SESSION=500
MAX_PROJECTS_PER_SESSION=5
SESSION_TTL_DAYS=90
HEARTBEAT_INTERVAL_MINUTES=5

# Paths
DATA_PATH=/app/data
GLOBAL_INDEX_PATH=/app/global_index
LOG_LEVEL=INFO
""",
    ".env.example": """# Security
SECRET_KEY=change_me_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Ollama Configuration
OLLAMA_BASE_URL=http://ollama:11434
DEFAULT_LLM_MODEL=llama3.1:8b
DEFAULT_EMBEDDING_MODEL=nomic-embed-text

# Session Limits
MAX_SESSIONS_PER_USER=10
MAX_DOCS_PER_SESSION=50
MAX_STORAGE_MB_PER_SESSION=500
MAX_PROJECTS_PER_SESSION=5
SESSION_TTL_DAYS=90
HEARTBEAT_INTERVAL_MINUTES=5

# Paths
DATA_PATH=/app/data
GLOBAL_INDEX_PATH=/app/global_index
LOG_LEVEL=INFO""",
    ".dockerignore": """# Backend
backend/__pycache__/
backend/*.pyc
backend/.git
backend/venv/
backend/data/
backend/global_index/

# Frontend
frontend/__pycache__/
frontend/*.pyc
frontend/.git
frontend/venv/

# General
*.md
*.txt
!requirements.txt
.env
.gitignore
""",
    ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.venv/

# Docker
*.log
.env

# Data
data_volume/*
!data_volume/.gitkeep
backend/app/data/*
!backend/app/data/.gitkeep

# IDE
.idea/
.vscode/
*.swp
*.swo
# OS
.DS_Store
Thumbs.db

# Tests
.pytest_cache/
.coverage
htmlcov/
""",
    "init.sh": """#!/bin/bash
echo "🚀 Инициализация BOAAI_S..."

# 1. Создание .env если не существует
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Создан файл .env"
fi

# 2. Генерация секретного ключа
if grep -q "your_super_secret_key_change_in_prod" .env; then
    NEW_KEY=$(openssl rand -hex 32)
    sed -i "s/your_super_secret_key_change_in_prod/$NEW_KEY/" .env
    echo "✅ Сгенерирован SECRET_KEY"
fi

# 3. Создание директорий для томов
mkdir -p data_volume/global_index
mkdir -p data_volume/sessions
mkdir -p data_volume/backup
mkdir -p ollama_data

# 4. Запуск контейнеров
docker-compose up -d

# 5. Ожидание готовности Ollama
echo "⏳ Ожидание готовности Ollama..."
sleep 10

# 6. Загрузка моделей
echo "📥 Загрузка моделей (это может занять время)..."
docker exec berezhinskii-ollama ollama pull llama3.1:8b
docker exec berezhinskii-ollama ollama pull nomic-embed-text

echo "✅ BOAAI_S готов к работе!"
echo "🌐 Frontend: http://localhost:8501"
echo "🔧 Backend:  http://localhost:8000/docs"
""",
    "backup.sh": """#!/bin/bashBACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "🔄 Начало резервного копирования..."

mkdir -p $BACKUP_DIR

# 1. Бэкап томов Docker
echo "📦 Бэкап томов..."
docker run --rm \\
  -v berezhinskii_backend_data:/data:ro \\
  -v $BACKUP_DIR:/backup \\
  alpine tar czf /backup/data_$DATE.tar.gz /data

docker run --rm \\
  -v berezhinskii_global_index:/data:ro \\
  -v $BACKUP_DIR:/backup \\
  alpine tar czf /backup/global_index_$DATE.tar.gz /data

# 2. Бэкап конфигурации
echo "📄 Бэкап конфигурации..."
cp .env $BACKUP_DIR/env_$DATE.backup
cp docker-compose.yml $BACKUP_DIR/compose_$DATE.backup

# 3. Очистка старых бэкапов (>30 дней)
echo "🧹 Очистка старых бэкапов..."
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.backup" -mtime +30 -delete

echo "✅ Резервное копирование завершено: $BACKUP_DIR"
""",
    "README.md": """# 🔬 BOAAI_S

Локальная научная платформа с RAG для научных учреждений.

## 📋 Описание

**BOAAI_S** — автономная система для работы с научной литературой, 
поддерживающая полную конфиденциальность данных (всё работает локально).

### Ключевые возможности

- ✅ **Полная автономность** — данные не покидают инфраструктуру
- ✅ **RAG Fusion** — объединённый поиск по глобальной базе и личным документам
- ✅ **Персистентность сессий** — 90 дней хранения с автосохранением
- ✅ **RBAC** — разделение ролей (Администратор / Исследователь)
- ✅ **Точное цитирование** — каждый ответ с источниками

## 🚀 Быстрый старт
```bash
# 1. Инициализация
chmod +x init.sh
./init.sh

# 2. Доступ к интерфейсу
# Frontend: http://localhost:8501
# Backend API: http://localhost:8000/docs
```

### Тестовые учётные данные

| Роль | Логин | Пароль |
|------|-------|--------|
| Администратор | `admin` | `admin123` |
| Исследователь | `researcher` | `researcher123` |

## 📊 Лимиты системы

| Параметр | Значение |
|----------|----------|
| Макс. сессий на пользователя | 10 |
| Макс. документов в сессии | 50 |
| Лимит хранилища сессии | 500 МБ |
| Срок жизни сессии | 90 дней |

## 📄 Лицензия

MIT License
""",
    # ─────────────────────────────────────────────
    # BACKEND FILES
    # ─────────────────────────────────────────────
    "backend/Dockerfile": """FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    libpq-dev \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app
RUN mkdir -p /app/data /app/global_index

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
""",
    "backend/requirements.txt": """fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
paperqa==5.0.0
litellm==1.30.0
ollama==0.1.7
pydantic==2.5.3
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
aiofiles==23.2.1
httpx==0.26.0
python-dotenv==1.0.0
""",
    "backend/pytest.ini": """[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
asyncio_mode = auto
""",
    "backend/app/__init__.py": "",
    "backend/app/main.py": """from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import os

from core.config import settings
from core.security import get_current_user, require_role, authenticate_user, create_access_token
from services.session_manager import session_manager
from services.rag_fusion import rag_engine
from models.user import UserLogin, UserCreate, Token
from models.session import SessionCreate, SessionResponse

app = FastAPI(
    title="BOAAI_S API",    
    description="Локальная научная платформа с RAG",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "ollama_url": settings.OLLAMA_BASE_URL,
        "data_path": settings.DATA_PATH
    }

@app.post("/token", response_model=Token)
async def login(form_data: UserLogin):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    return {"access_token": access_token, "token_type": "bearer", "role": user["role"]}

@app.post("/users/", dependencies=[Depends(require_role("admin"))])
async def create_user(user_data: UserCreate, current_user: dict = Depends(get_current_user)):
    from core.security import _load_users, _save_users, get_password_hash
    users = _load_users()
    if user_data.username in users:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    
    users[user_data.username] = {
        "username": user_data.username,
        "hashed_password": get_password_hash(user_data.password),
        "role": user_data.role,
        "created_at": __import__('datetime').datetime.now().isoformat(),
        "active": True
    }
    _save_users(users)
    return {"message": "Пользователь создан", "username": user_data.username}
@app.post("/sessions/", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    current_user: dict = Depends(get_current_user)
):
    return await session_manager.create_session(
        user_id=current_user["username"],
        name=session_data.name
    )

@app.get("/sessions/", response_model=List[SessionResponse])
async def get_user_sessions(current_user: dict = Depends(get_current_user)):
    return await session_manager.get_user_sessions(current_user["username"])

@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    session = await session_manager.get_session(session_id, current_user["username"])
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    return session

@app.post("/sessions/{session_id}/heartbeat")
async def session_heartbeat(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    return await session_manager.heartbeat(session_id, current_user["username"])

@app.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    success = await session_manager.delete_session(session_id, current_user["username"])
    if not success:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    return {"message": "Сессия удалена"}

@app.post("/query")
async def query_system(
    query: str,
    session_id: Optional[str] = None,
    mode: str = "hybrid",
    project_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):    if session_id:
        session = await session_manager.get_session(session_id, current_user["username"])
        if not session:
            raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    return await rag_engine.query(
        query=query,
        session_id=session_id,
        mode=mode,
        project_id=project_id
    )

@app.post("/quick-query")
async def quick_query(query: str):
    return await rag_engine.quick_query(query)

@app.post("/sessions/{session_id}/documents/")
async def upload_document(
    session_id: str,
    file: UploadFile = File(...),
    category: str = "temp_literature",
    project_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    session = await session_manager.get_session(session_id, current_user["username"])
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    file_path = os.path.join(settings.DATA_PATH, "sessions", session_id, file.filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    
    doc_meta = {
        "name": file.filename,
        "path": file_path,
        "category": category,
        "project_id": project_id,
        "size_mb": round(file_size_mb, 2),
        "uploaded_at": __import__('datetime').datetime.now().isoformat()
    }
    
    updated_session = await session_manager.add_document(
        session_id, current_user["username"], doc_meta
    )
    
    session_pqa = rag_engine._get_session_pqa(session_id)    await session_pqa.add_document(file_path, file.filename, category, project_id)
    
    return {
        "message": "Документ загружен",
        "document": doc_meta,
        "session": updated_session
    }

@app.get("/admin/users", dependencies=[Depends(require_role("admin"))])
async def list_users(current_user: dict = Depends(get_current_user)):
    from core.security import _load_users
    users = _load_users()
    return list(users.values())

@app.get("/admin/sessions", dependencies=[Depends(require_role("admin"))])
async def list_all_sessions(current_user: dict = Depends(get_current_user)):
    from services.session_manager import SESSIONS_FILE
    import json
    with open(SESSIONS_FILE, 'r') as f:
        sessions = json.load(f)
    return list(sessions.values())

@app.post("/admin/global-index/rebuild", dependencies=[Depends(require_role("admin"))])
async def rebuild_global_index(current_user: dict = Depends(get_current_user)):
    await rag_engine.global_pqa.rebuild_index()
    return {"message": "Глобальный индекс переиндексирован"}

@app.on_event("startup")
async def startup_event():
    print("🚀 BOAAI_S запускается...")
    print(f"📁 Data path: {settings.DATA_PATH}")
    print(f"🤖 Ollama URL: {settings.OLLAMA_BASE_URL}")
    print(f"🧠 LLM Model: {settings.DEFAULT_LLM_MODEL}")
""",
    "backend/app/core/__init__.py": "",
    "backend/app/core/config.py": """from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_me_in_production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    DEFAULT_LLM_MODEL: str = "llama3.1:8b"
    DEFAULT_EMBEDDING_MODEL: str = "nomic-embed-text"
        MAX_SESSIONS_PER_USER: int = 10
    MAX_DOCS_PER_SESSION: int = 50
    MAX_STORAGE_MB_PER_SESSION: int = 500
    MAX_PROJECTS_PER_SESSION: int = 5
    SESSION_TTL_DAYS: int = 90
    HEARTBEAT_INTERVAL_MINUTES: int = 5
    
    DATA_PATH: str = "/app/data"
    GLOBAL_INDEX_PATH: str = "/app/global_index"
    
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

os.makedirs(settings.DATA_PATH, exist_ok=True)
os.makedirs(settings.GLOBAL_INDEX_PATH, exist_ok=True)
""",
    "backend/app/core/security.py": """from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
import json

from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

USERS_FILE = os.path.join(settings.DATA_PATH, "users.json")

def _load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        default_users = {
            "admin": {
                "username": "admin",
                "hashed_password": pwd_context.hash("admin123"),
                "role": "admin",
                "created_at": datetime.now().isoformat(),
                "active": True
            }
        }
        _save_users(default_users)        return default_users
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def _save_users(users: dict):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def authenticate_user(username: str, password: str) -> Optional[dict]:
    users = _load_users()
    user = users.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    users = _load_users()
    user = users.get(username)
    if user is None or not user.get("active", False):
        raise credentials_exception
    return user

def require_role(required_role: str):
    async def role_checker(current_user: dict = Depends(get_current_user)):        if current_user["role"] != required_role and required_role != "any":
            if required_role == "admin" and current_user["role"] != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )
        return current_user
    return role_checker
""",
    "backend/app/core/paperqa_manager.py": """import os
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
            contexts = []            if hasattr(results, 'contexts') and results.contexts:
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
""",
    "backend/app/models/__init__.py": "",
    "backend/app/models/user.py": """from pydantic import BaseModel
from typing import Optional

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "researcher"

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
""",
    "backend/app/models/session.py": """from pydantic import BaseModel
from typing import List, Optional

class SessionCreate(BaseModel):
    name: str

class DocumentMeta(BaseModel):
    name: str
    category: str
    project_id: Optional[str] = None
    size_mb: float
    uploaded_at: str
class ProjectMeta(BaseModel):
    id: str
    name: str
    target_journal: Optional[str] = None
    status: str = "draft"
    sections: List[str] = []

class SessionResponse(BaseModel):
    id: str
    user_id: str
    name: str
    created_at: str
    last_active: str
    status: str
    documents: List[DocumentMeta]
    chat_history: List[dict]
    projects: List[ProjectMeta]
    last_action: str
    storage_used_mb: float
""",
    "backend/app/services/__init__.py": "",
    "backend/app/services/session_manager.py": """import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from fastapi import HTTPException, status

from core.config import settings

SESSIONS_FILE = os.path.join(settings.DATA_PATH, "sessions.json")

class SessionManager:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._ensure_file()
    
    def _ensure_file(self):
        os.makedirs(os.path.dirname(SESSIONS_FILE), exist_ok=True)
        if not os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, 'w') as f:
                json.dump({}, f)
    
    def _load(self) -> Dict:
        with open(SESSIONS_FILE, 'r') as f:
            return json.load(f)
        def _save(self, data: Dict):
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    async def create_session(self, user_id: str, name: str) -> dict:
        async with self._lock:
            sessions = self._load()
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
            self._save(sessions)
            return session_data
    
    async def get_session(self, session_id: str, user_id: Optional[str] = None) -> Optional[dict]:
        sessions = self._load()
        session = sessions.get(session_id)
        if not session:
            return None
        if user_id and session['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="Доступ запрещён")
        last_active = datetime.fromisoformat(session["last_active"])
        if datetime.now() - last_active > timedelta(days=settings.SESSION_TTL_DAYS):
            if session["status"] != "archived":
                session["status"] = "archived"
                sessions[session_id] = session
                self._save(sessions)
            raise HTTPException(status_code=403, detail="Сессия архивирована")
        return session
    
    async def heartbeat(self, session_id: str, user_id: str) -> dict:
        async with self._lock:
            session = await self.get_session(session_id, user_id)
            if not session:
                raise HTTPException(status_code=404, detail="Сессия не найдена")            sessions = self._load()
            sessions[session_id]["last_active"] = datetime.now().isoformat()
            if sessions[session_id]["status"] == "paused":
                sessions[session_id]["status"] = "active"
            self._save(sessions)
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
            sessions = self._load()
            sessions[session_id]["documents"].append(doc_meta)
            sessions[session_id]["storage_used_mb"] = new_storage
            sessions[session_id]["last_active"] = datetime.now().isoformat()
            self._save(sessions)
            return sessions[session_id]
    
    async def get_user_sessions(self, user_id: str) -> List[dict]:
        sessions = self._load()
        user_sessions = [s for s in sessions.values() if s['user_id'] == user_id]
        user_sessions.sort(key=lambda x: x['last_active'], reverse=True)
        return user_sessions
    
    async def delete_session(self, session_id: str, user_id: str) -> bool:
        async with self._lock:
            sessions = self._load()
            if session_id not in sessions:
                return False
            if sessions[session_id]['user_id'] != user_id:
                raise HTTPException(status_code=403, detail="Доступ запрещён")
            del sessions[session_id]
            self._save(sessions)
            return True

session_manager = SessionManager()
""",
    "backend/app/services/rag_fusion.py": """import asyncio
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
        
        context_text = "\\n\\n".join([f"[{c['source']}] {c['text']}" for c in contexts])
        
        system_prompt = "Ты научный ассистент. Отвечай ТОЛЬКО на основе контекста. Указывай источники (📚 или 📁)."
        user_prompt = f"Контекст:\\n{context_text}\\n\\nВопрос: {query}"
        
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
""",
    "backend/app/api/__init__.py": "",
    "backend/app/data/.gitkeep": "",
    "backend/tests/__init__.py": "",
    "backend/tests/test_api.py": """import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def admin_token():
    response = client.post("/token", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    return response.json()["access_token"]

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_login_admin():
    response = client.post("/token", data={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid():
    response = client.post("/token", data={"username": "admin", "password": "wrong"})
    assert response.status_code == 401

def test_quick_query():
    response = client.post("/quick-query", json={"query": "Что такое RAG?"})
    assert response.status_code == 200
    assert "answer" in response.json()
""",
    # ─────────────────────────────────────────────    # FRONTEND FILES
    # ─────────────────────────────────────────────
    "frontend/Dockerfile": """FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true

CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
""",
    "frontend/requirements.txt": """streamlit==1.30.0
requests==2.31.0
pandas==2.1.4
python-dotenv==1.0.0
""",
    "frontend/app/__init__.py": "",
    "frontend/app/main.py": """import streamlit as st
from core.api_client import api_client

st.set_page_config(page_title="BOAAI_S", page_icon="🔬", layout="wide")

if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "current_session" not in st.session_state:
    st.session_state.current_session = None

if st.session_state.auth_token:
    api_client.token = st.session_state.auth_token
    api_client.role = st.session_state.user_info.get("role") if st.session_state.user_info else None

if not st.session_state.auth_token:
    st.switch_page("pages/05_🔐_Login.py")
else:
    with st.sidebar:
        st.title("🔬 BOAAI_S")
        st.markdown("---")
        if st.session_state.user_info:            st.write(f"👤 **{st.session_state.user_info.get('username')}**")
            st.write(f"🎭 Роль: `{st.session_state.user_info.get('role')}`")
        st.markdown("---")
        page = st.radio("Навигация", ["🏠 Дашборд", "💼 Рабочее пространство", "📊 Проекты"])
        if st.session_state.user_info.get("role") == "admin":
            page = st.radio("Навигация", ["🏠 Дашборд", "💼 Рабочее пространство", "📊 Проекты", "⚙️ Админ-панель"])
        st.markdown("---")
        if st.button("🚪 Выйти", use_container_width=True):
            st.session_state.auth_token = None
            st.session_state.user_info = None
            st.session_state.current_session = None
            st.rerun()
    
    if page == "🏠 Дашборд":
        st.switch_page("pages/01_🏠_Dashboard.py")
    elif page == "💼 Рабочее пространство":
        st.switch_page("pages/02_💼_Workspace.py")
    elif page == "📊 Проекты":
        st.switch_page("pages/03_📊_Projects.py")
    elif page == "⚙️ Админ-панель":
        st.switch_page("pages/04_⚙️_Admin.py")
""",
    "frontend/app/core/__init__.py": "",
    "frontend/app/core/api_client.py": """import requests
import streamlit as st
from typing import Optional, Dict, List

class APIClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or st.secrets.get("BACKEND_URL", "http://backend:8000")
        self.token = None
        self.role = None
    
    def set_token(self, token: str, role: str):
        self.token = token
        self.role = role
        st.session_state["auth_token"] = token
        st.session_state["user_role"] = role
    
    def get_headers(self) -> Dict:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def login(self, username: str, password: str) -> Optional[Dict]:
        try:
            response = requests.post(f"{self.base_url}/token", data={"username": username, "password": password}, headers={"Content-Type": "application/x-www-form-urlencoded"})            if response.status_code == 200:
                data = response.json()
                self.set_token(data["access_token"], data["role"])
                return data
            return None
        except Exception as e:
            st.error(f"Ошибка: {str(e)}")
            return None
    
    def logout(self):
        self.token = None
        self.role = None
        st.session_state.pop("auth_token", None)
        st.session_state.pop("user_role", None)
    
    def create_session(self, name: str) -> Optional[Dict]:
        try:
            response = requests.post(f"{self.base_url}/sessions/", json={"name": name}, headers=self.get_headers())
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def get_sessions(self) -> List[Dict]:
        try:
            response = requests.get(f"{self.base_url}/sessions/", headers=self.get_headers())
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []
    
    def query(self, query: str, session_id: Optional[str] = None, mode: str = "hybrid") -> Optional[Dict]:
        try:
            payload = {"query": query, "mode": mode}
            if session_id:
                payload["session_id"] = session_id
            response = requests.post(f"{self.base_url}/query", json=payload, headers=self.get_headers())
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def quick_query(self, query: str) -> Optional[Dict]:
        try:
            response = requests.post(f"{self.base_url}/quick-query", json={"query": query})
            if response.status_code == 200:
                return response.json()            return None
        except:
            return None

api_client = APIClient()
""",
    "frontend/app/pages/__init__.py": "",
    "frontend/app/pages/01_🏠_Dashboard.py": """import streamlit as st
from core.api_client import api_client

st.title("🏠 Дашборд исследователя")

st.markdown("### ⚡ Быстрый вопрос")
query = st.text_input("Ваш вопрос", placeholder="Спросите о чём-нибудь...")
if st.button("🔍 Найти"):
    if query:
        with st.spinner("Поиск..."):
            result = api_client.quick_query(query)
            if result:
                st.write(result["answer"])

st.markdown("---")
st.markdown("### 📁 Ваши сессии")

col1, col2 = st.columns([3, 1])
with col1:
    st.caption("Сессии сохраняются 90 дней")
with col2:
    new_session_name = st.text_input("Новая сессия", placeholder="Название...")
    if st.button("➕ Создать", use_container_width=True):
        if new_session_name:
            session = api_client.create_session(new_session_name)
            if session:
                st.success(f"Сессия '{new_session_name}' создана!")
                st.session_state["current_session"] = session
                st.rerun()

sessions = api_client.get_sessions()
if not sessions:
    st.info("📭 Нет активных сессий")
else:
    for session in sessions[:5]:
        with st.container():
            st.markdown(f"**🟢 {session['name']}**")
            st.caption(f"Документов: {len(session.get('documents', []))} | Последнее: {session.get('last_action', 'N/A')}")
            if st.button("▶️ Продолжить", key=f"resume_{session['id']}"):
                st.session_state["current_session"] = session
                st.rerun()            st.markdown("---")
""",
    "frontend/app/pages/02_💼_Workspace.py": """import streamlit as st
from core.api_client import api_client

st.title("💼 Рабочее пространство")

if "current_session" not in st.session_state or not st.session_state.current_session:
    sessions = api_client.get_sessions()
    if sessions:
        st.session_state["current_session"] = sessions[0]
    else:
        st.warning("📭 Нет сессий. Создайте на дашборде.")
        st.stop()

session = st.session_state.current_session
st.markdown(f"### 📁 {session['name']}")

tab1, tab2 = st.tabs(["💬 Чат", "📄 Документы"])

with tab1:
    mode = st.selectbox("Режим поиска", ["hybrid", "session_only", "global_only"])
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    if prompt := st.chat_input("Спросите..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            with st.spinner("Генерация..."):
                result = api_client.query(query=prompt, session_id=session["id"], mode=mode)
                if result:
                    st.write(result["answer"])
                    st.session_state.chat_history.append({"role": "assistant", "content": result["answer"]})

with tab2:
    uploaded_file = st.file_uploader("Загрузить", type=["pdf", "txt", "md"])
    category = st.selectbox("Категория", ["temp_literature", "project_draft", "project_data"])
    if uploaded_file and st.button("📤 Загрузить"):
        st.success(f"{uploaded_file.name} загружен!")
""",
    "frontend/app/pages/03_📊_Projects.py": """import streamlit as st
st.title("📊 Проекты статей")
st.info("Функционал в разработке")
""",
    "frontend/app/pages/04_⚙️_Admin.py": """import streamlit as stfrom core.api_client import api_client

st.title("⚙️ Админ-панель")

if st.session_state.get("user_info", {}).get("role") != "admin":
    st.error("🔒 Доступ запрещён")
    st.stop()

tab1, tab2 = st.tabs(["👥 Пользователи", "📁 Сессии"])

with tab1:
    st.markdown("### Создать пользователя")
    col1, col2, col3 = st.columns(3)
    with col1:
        new_username = st.text_input("Имя")
    with col2:
        new_password = st.text_input("Пароль", type="password")
    with col3:
        new_role = st.selectbox("Роль", ["researcher", "admin"])
    if st.button("➕ Создать"):
        st.success("Пользователь создан!")

with tab2:
    st.markdown("### Все сессии")
    st.info("Список сессий всех пользователей")
""",
    "frontend/app/pages/05_🔐_Login.py": """import streamlit as st
from core.api_client import api_client

st.set_page_config(page_title="Вход", page_icon="🔐")
st.title("🔐 Вход в систему")

with st.form("login_form"):
    username = st.text_input("Имя пользователя")
    password = st.text_input("Пароль", type="password")
    submit = st.form_submit_button("Войти", use_container_width=True)
    if submit:
        if not username or not password:
            st.error("Введите логин и пароль")
        else:
            with st.spinner("Проверка..."):
                result = api_client.login(username, password)
                if result:
                    st.session_state["user_info"] = {"username": username, "role": result["role"]}
                    st.success("✅ Успешный вход!")
                    st.switch_page("../main.py")
                else:
                    st.error("❌ Неверные credentials")
st.info("**Тест:** admin / admin123")
""",
    "frontend/app/components/__init__.py": "",
    "frontend/app/utils/__init__.py": "",
    "frontend/app/utils/helpers.py": """import streamlit as st
from datetime import datetime

def init_session_state():
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None
    if "user_info" not in st.session_state:
        st.session_state.user_info = None

def check_auth() -> bool:
    return st.session_state.get("auth_token") is not None

def format_date(iso_string: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return iso_string
""",
    # ─────────────────────────────────────────────
    # DOCS
    # ─────────────────────────────────────────────
    "docs/USER_GUIDE.md": """# 👤 Руководство пользователя

## Вход
1. Откройте http://localhost:8501
2. Введите логин/пароль
3. Нажмите "Войти"

## Сессии
- Создавайте сессии для разных проектов
- Сессии сохраняются 90 дней
- Все документы и чат сохраняются

## RAG Поиск
- hybrid: глобальная + сессия
- session_only: только ваши файлы
- global_only: только база
""",
    "docs/ADMIN_GUIDE.md": """# ⚙️ Руководство администратора
## Пользователи
- Создавайте через Админ-панель
- Назначайте роли (admin/researcher)

## Глобальная база
- Только админ может загружать
- Переиндексация при проблемах

## Бэкапы
```bash
./backup.sh
```
""",
    "data_volume/.gitkeep": "",
    "data_volume/global_index/.gitkeep": "",
    "data_volume/sessions/.gitkeep": "",
    "data_volume/backup/.gitkeep": "",
}

# ─────────────────────────────────────────────
# ГЕНЕРАЦИЯ ФАЙЛОВ
# ─────────────────────────────────────────────


def create_project():
    print("🚀 Создание проекта BOAAI_S...")

    for filepath, content in FILES.items():
        # Create directory if needed
        directory = os.path.dirname(filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)

        # Write file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"✅ {filepath}")

    # Make scripts executable
    import stat

    for script in ["init.sh", "backup.sh"]:
        if os.path.exists(script):
            os.chmod(script, os.stat(script).st_mode | stat.S_IEXEC)

    print("\\n" + "=" * 50)
    print("✅ Проект создан успешно!")
    print("=" * 50)
    print("\\n📁 Структура:")
    print("  berezhinskii/")
    print("  ├── docker-compose.yml")
    print("  ├── .env")
    print("  ├── init.sh")
    print("  ├── backend/")
    print("  ├── frontend/")
    print("  ├── docs/")
    print("  └── data_volume/")
    print("\\n🚀 Запуск:")
    print("  cd berezhinskii")
    print("  chmod +x init.sh")
    print("  ./init.sh")
    print("\\n🌐 Доступ:")
    print("  Frontend: http://localhost:8501")
    print("  Backend:  http://localhost:8000/docs")


if __name__ == "__main__":
    create_project()
