from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Body
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
async def login(
    username: str = Form(...),
    password: str = Form(...)
):
    user = authenticate_user(username, password)
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

@app.put("/users/{username}", dependencies=[Depends(require_role("admin"))])
async def update_user(username: str, user_data: UserCreate, current_user: dict = Depends(get_current_user)):
    from core.security import _load_users, _save_users, get_password_hash
    users = _load_users()
    if username not in users:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if username == current_user["username"]:
        raise HTTPException(status_code=400, detail="Нельзя редактировать себя")

    users[username]["hashed_password"] = get_password_hash(user_data.password)
    users[username]["role"] = user_data.role
    users[username]["active"] = True
    _save_users(users)
    return {"message": "Пользователь обновлён", "username": username}

@app.delete("/users/{username}", dependencies=[Depends(require_role("admin"))])
async def delete_user(username: str, current_user: dict = Depends(get_current_user)):
    from core.security import _load_users, _save_users
    users = _load_users()
    if username not in users:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if username == current_user["username"]:
        raise HTTPException(status_code=400, detail="Нельзя удалить себя")

    del users[username]
    _save_users(users)
    return {"message": "Пользователь удалён", "username": username}
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
    query: str = Body(..., embed=True),
    session_id: Optional[str] = Body(None, embed=True),
    mode: str = Body("hybrid", embed=True),
    project_id: Optional[str] = Body(None, embed=True),
    current_user: dict = Depends(get_current_user)
):    
    if session_id:
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
async def quick_query(query: str = Body(..., embed=True)):
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
    
    session_pqa = rag_engine._get_session_pqa(session_id)    
    await session_pqa.add_document(file_path, file.filename, category, project_id)
    
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
