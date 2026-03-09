from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import os
import logging
import asyncio
import shutil
import json
import glob
from datetime import datetime

from core.config import settings
from core.security import get_current_user, require_role, authenticate_user, create_access_token
from services.session_manager import session_manager
from services.rag_fusion import rag_engine
from models.user import UserLogin, UserCreate, Token
from models.session import SessionCreate, SessionResponse

logger = logging.getLogger(__name__)

app = FastAPI(
    title="BOAAI_S API",
    description="Локальная научная платформа с RAG (PaperQA 2026.03.03)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

upload_status = {}
background_tasks_store = {}


@app.on_event("startup")
async def startup_event():
    print("🚀 BOAAI_S запускается...")
    print(f"📁 Data path: {settings.DATA_PATH}")
    print(f"🤖 Ollama URL: {settings.OLLAMA_BASE_URL}")
    print(f"🧠 LLM Model: {settings.DEFAULT_LLM_MODEL}")
    print(f"📚 PaperQA версия: 2026.03.03")
    await rag_engine.global_pqa.initialize()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Завершение работы...")
    await rag_engine.close()
    await session_manager.close()


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "paperqa_version": "2026.03.03",
        "ollama_url": settings.OLLAMA_BASE_URL,
        "data_path": settings.DATA_PATH
    }


@app.post("/token", response_model=Token)
async def login(username: str = Form(...), password: str = Form(...)):
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
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
        "created_at": datetime.now().isoformat(),
        "active": True
    }
    _save_users(users)
    log_audit("user_created", current_user["username"], {"target_user": user_data.username, "role": user_data.role})
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
    log_audit("user_updated", current_user["username"], {"target_user": username, "new_role": user_data.role})
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
    log_audit("user_deleted", current_user["username"], {"target_user": username})
    return {"message": "Пользователь удалён", "username": username}


@app.post("/sessions/", response_model=SessionResponse)
async def create_session(session_data: SessionCreate, current_user: dict = Depends(get_current_user)):
    return await session_manager.create_session(user_id=current_user["username"], name=session_data.name)


@app.get("/sessions/", response_model=List[SessionResponse])
async def get_user_sessions(current_user: dict = Depends(get_current_user)):
    return await session_manager.get_user_sessions(current_user["username"])


@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, current_user: dict = Depends(get_current_user)):
    session = await session_manager.get_session(session_id, current_user["username"])
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    return session


@app.post("/sessions/{session_id}/heartbeat")
async def session_heartbeat(session_id: str, current_user: dict = Depends(get_current_user)):
    return await session_manager.heartbeat(session_id, current_user["username"])


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str, current_user: dict = Depends(get_current_user)):
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
    
    return await rag_engine.query(query=query, session_id=session_id, mode=mode, project_id=project_id)


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

    file_size_bytes = os.path.getsize(file_path)
    file_size_mb = file_size_bytes / (1024 * 1024)

    doc_meta = {
        "name": file.filename,
        "path": file_path,
        "category": category,
        "project_id": project_id,
        "size_mb": round(file_size_mb, 6),
        "size_bytes": file_size_bytes,
        "uploaded_at": datetime.now().isoformat()
    }

    updated_session = await session_manager.add_document(session_id, current_user["username"], doc_meta)

    session_pqa = await rag_engine._get_session_pqa(session_id)
    await session_pqa.add_document(file_path, file.filename, category, project_id)

    return {
        "message": "Документ загружен",
        "document": doc_meta,
        "session": updated_session
    }


@app.get("/sessions/{session_id}/documents")
async def get_session_documents(session_id: str, current_user: dict = Depends(get_current_user)):
    session = await session_manager.get_session(session_id, current_user["username"])
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    return session.get("documents", [])


@app.post("/upload/session/{session_id}")
async def upload_to_session(
    session_id: str,
    file: UploadFile = File(...),
    category: str = "temp_literature",
    current_user: dict = Depends(get_current_user)
):
    return await upload_document(session_id, file, category, None, current_user)


@app.post("/upload/global")
async def upload_to_global(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Только admin может загружать в глобальную базу")
    
    file_path = os.path.join(settings.GLOBAL_INDEX_PATH, "documents", file.filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    await rag_engine.global_pqa.add_document(file_path, file.filename, "global_index")

    log_audit("global_doc_uploaded", current_user["username"], {
        "document": file.filename,
        "size_mb": round(file_size_mb, 2)
    })

    return {
        "message": "Документ добавлен в глобальную базу",
        "document": {
            "name": file.filename,
            "path": file_path,
            "size_mb": round(file_size_mb, 2),
            "uploaded_at": datetime.now().isoformat()
        }
    }


@app.get("/admin/users", dependencies=[Depends(require_role("admin"))])
async def list_users(current_user: dict = Depends(get_current_user)):
    from core.security import _load_users
    users = _load_users()
    return list(users.values())


@app.get("/admin/sessions", dependencies=[Depends(require_role("admin"))])
async def list_all_sessions(current_user: dict = Depends(get_current_user)):
    from services.session_manager import SESSIONS_FILE
    with open(SESSIONS_FILE, 'r') as f:
        sessions = json.load(f)
    return list(sessions.values())


@app.post("/admin/global-index/upload", dependencies=[Depends(require_role("admin"))])
async def admin_upload_to_global(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    return await upload_to_global(file, current_user)


@app.get("/admin/global-index/documents", dependencies=[Depends(require_role("admin"))])
async def list_global_documents_admin(current_user: dict = Depends(get_current_user)):
    return await list_global_documents_public()


@app.get("/global-index/documents")
async def list_global_documents_public():
    doc_pattern = os.path.join(settings.GLOBAL_INDEX_PATH, "documents", "*")
    documents = []

    for file_path in glob.glob(doc_pattern):
        if os.path.isfile(file_path):
            stat = os.stat(file_path)
            size_bytes = stat.st_size
            documents.append({
                "name": os.path.basename(file_path),
                "path": file_path,
                "size_mb": round(size_bytes / (1024 * 1024), 6),
                "size_bytes": size_bytes,
                "uploaded_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

    return documents


@app.delete("/admin/global-index/documents/{doc_name}", dependencies=[Depends(require_role("admin"))])
async def delete_global_document(doc_name: str, current_user: dict = Depends(get_current_user)):
    file_path = os.path.join(settings.GLOBAL_INDEX_PATH, "documents", doc_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Документ не найден")
    
    try:
        os.remove(file_path)
        await rag_engine.global_pqa.rebuild_index()
        log_audit("global_doc_deleted", current_user["username"], {"document": doc_name})
        return {"message": f"Документ '{doc_name}' удалён", "rebuild_required": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка удаления: {str(e)}")


@app.post("/admin/global-index/rebuild", dependencies=[Depends(require_role("admin"))])
async def rebuild_global_index(current_user: dict = Depends(get_current_user)):
    await rag_engine.global_pqa.rebuild_index()
    log_audit("index_rebuilt", current_user["username"], {})
    return {"message": "Глобальный индекс переиндексирован"}


@app.get("/admin/global-index/pending", dependencies=[Depends(require_role("admin"))])
async def list_pending_uploads(current_user: dict = Depends(get_current_user)):
    pending_files = []
    
    for pattern in ["*.pdf", "*.txt", "*.md", "*.html", "*.docx", "*.xlsx", "*.pptx", "*.py", "*.ts", "*.yaml", "*.json", "*.csv", "*.xml"]:
        file_pattern = os.path.join(settings.UPLOADS_PATH, pattern)
        for file_path in glob.glob(file_pattern):
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                pending_files.append({
                    "name": os.path.basename(file_path),
                    "path": file_path,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "added_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
    
    return sorted(pending_files, key=lambda x: x["added_at"])


async def process_upload_task(user_id: str):
    """Фоновая загрузка для PaperQA 2026.03.03 (полностью асинхронная)"""
    uploaded = []
    errors = []
    
    all_files = []
    for pattern in ["*.pdf", "*.txt", "*.md", "*.html", "*.docx", "*.xlsx", "*.pptx", "*.py", "*.ts", "*.yaml", "*.json", "*.csv", "*.xml"]:
        file_pattern = os.path.join(settings.UPLOADS_PATH, pattern)
        all_files.extend(glob.glob(file_pattern))
    
    total_files = len(all_files)
    if total_files == 0:
        upload_status[user_id] = {
            "completed": True,
            "message": "Нет файлов для загрузки",
            "uploaded": [],
            "errors": []
        }
        return
    
    logger.info(f"📊 Найдено файлов для загрузки: {total_files}")
    
    for idx, file_path in enumerate(all_files):
        if not os.path.isfile(file_path):
            continue
        
        filename = os.path.basename(file_path)
        current_num = idx + 1
        
        upload_status[user_id] = {
            "completed": False,
            "message": f"Обработка {current_num}/{total_files}: {filename}",
            "progress": int((current_num / total_files) * 100),
            "current_file": filename,
            "uploaded": uploaded,
            "errors": errors
        }
        
        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            logger.info(f"🔄 [{current_num}/{total_files}] Обработка: {filename}")
            
            success = await rag_engine.global_pqa.add_document(
                file_path=file_path,
                doc_name=filename,
                category="global_index"
            )
            
            if success:
                dest_path = os.path.join(settings.GLOBAL_INDEX_PATH, "documents", filename)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.move(file_path, dest_path)
                
                uploaded.append({
                    "name": filename,
                    "size_mb": round(file_size_mb, 2)
                })
                logger.info(f"✅ Файл {filename} загружен успешно")
            else:
                errors.append({"name": filename, "error": "Processing failed"})
                
        except Exception as e:
            error_msg = f"Ошибка при загрузке {filename}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            import traceback
            logger.error(traceback.format_exc())
            errors.append({"name": filename, "error": str(e)})
    
    upload_status[user_id] = {
        "completed": True,
        "message": f"Загружено {len(uploaded)} из {total_files} файлов",
        "progress": 100,
        "uploaded": uploaded,
        "errors": errors
    }
    
    if uploaded:
        log_audit("global_doc_uploaded", user_id, {
            "documents": [f["name"] for f in uploaded],
            "count": len(uploaded)
        })
        logger.info(f"🎉 Загрузка завершена: {len(uploaded)} файлов")


@app.post("/admin/global-index/process-uploads", dependencies=[Depends(require_role("admin"))])
async def process_pending_uploads(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["username"]
    
    all_files = []
    for pattern in ["*.pdf", "*.txt", "*.md", "*.html", "*.docx", "*.xlsx", "*.pptx", "*.py", "*.ts", "*.yaml", "*.json", "*.csv", "*.xml"]:
        file_pattern = os.path.join(settings.UPLOADS_PATH, pattern)
        all_files.extend(glob.glob(file_pattern))
    
    if not all_files:
        return {"message": "Нет файлов для загрузки"}
    
    if user_id in upload_status and not upload_status[user_id].get("completed", True):
        return {"message": "Загрузка уже выполняется", "status": "running"}
    
    upload_status[user_id] = {
        "completed": False,
        "message": f"Начало загрузки {len(all_files)} файлов...",
        "progress": 0,
        "uploaded": [],
        "errors": []
    }
    
    background_tasks.add_task(process_upload_task, user_id)
    
    return {
        "message": f"Начата загрузка {len(all_files)} файлов",
        "status": "processing",
        "files_count": len(all_files)
    }


@app.get("/admin/global-index/process-uploads/status", dependencies=[Depends(require_role("admin"))])
async def get_upload_status(current_user: dict = Depends(get_current_user)):
    user_id = current_user["username"]
    return upload_status.get(user_id, {"message": "Нет активных загрузок"})


@app.delete("/admin/global-index/pending/{file_name}", dependencies=[Depends(require_role("admin"))])
async def delete_pending_upload(file_name: str, current_user: dict = Depends(get_current_user)):
    file_path = os.path.join(settings.UPLOADS_PATH, file_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    try:
        os.remove(file_path)
        return {"message": f"Файл '{file_name}' удалён из очереди"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка удаления: {str(e)}")


@app.get("/admin/audit-log", dependencies=[Depends(require_role("admin"))])
async def get_audit_log(current_user: dict = Depends(get_current_user)):
    audit_file = os.path.join(settings.DATA_PATH, "audit_log.json")
    
    if not os.path.exists(audit_file):
        return []
    
    with open(audit_file, 'r') as f:
        logs = json.load(f)
    
    return logs[-100:]


def log_audit(action: str, user: str, details: dict = None):
    audit_file = os.path.join(settings.DATA_PATH, "audit_log.json")
    os.makedirs(os.path.dirname(audit_file), exist_ok=True)
    
    logs = []
    if os.path.exists(audit_file):
        with open(audit_file, 'r') as f:
            logs = json.load(f)
    
    logs.append({
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "user": user,
        "details": details or {}
    })
    
    logs = logs[-1000:]
    
    with open(audit_file, 'w') as f:
        json.dump(logs, f, indent=2)