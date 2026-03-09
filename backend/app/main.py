from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import os
import logging
import asyncio
import pickle
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

    # Проверяем конфликт имён — если файл уже есть, добавляем номер
    filename = file.filename
    file_dir = os.path.join(settings.DATA_PATH, "sessions", session_id)
    os.makedirs(file_dir, exist_ok=True)
    
    file_path = os.path.join(file_dir, filename)
    
    # Если файл с таким именем уже существует — добавляем номер
    if os.path.exists(file_path):
        name_parts = os.path.splitext(filename)
        base_name = name_parts[0]
        extension = name_parts[1]
        
        counter = 1
        while True:
            new_filename = f"{base_name}_{counter}{extension}"
            file_path = os.path.join(file_dir, new_filename)
            if not os.path.exists(file_path):
                filename = new_filename
                logger.info(f"⚠️ Файл переименован: {new_filename} (конфликт имён в сессии {session_id})")
                break
            counter += 1

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    file_size_bytes = os.path.getsize(file_path)
    file_size_mb = file_size_bytes / (1024 * 1024)

    doc_meta = {
        "name": filename,
        "path": file_path,
        "category": category,
        "project_id": project_id,
        "size_mb": round(file_size_mb, 6),
        "size_bytes": file_size_bytes,
        "uploaded_at": __import__('datetime').datetime.now().isoformat()
    }

    updated_session = await session_manager.add_document(
        session_id, current_user["username"], doc_meta
    )

    session_pqa = rag_engine._get_session_pqa(session_id)
    await session_pqa.add_document(file_path, filename, category, project_id)

    return {
        "message": "Документ загружен",
        "document": doc_meta,
        "session": updated_session
    }

@app.get("/sessions/{session_id}/documents")
async def get_session_documents(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Получить список документов сессии"""
    session = await session_manager.get_session(session_id, current_user["username"])
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    documents = session.get("documents", [])
    return documents

@app.post("/upload/session/{session_id}")
async def upload_to_session(
    session_id: str,
    file: UploadFile = File(...),
    category: str = "temp_literature",
    current_user: dict = Depends(get_current_user)
):
    """Загрузить документ в сессию пользователя"""
    return await upload_document(session_id, file, category, None, current_user)

@app.post("/upload/global")
async def upload_to_global(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Загрузить документ в глобальную базу (только admin)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Только admin может загружать в глобальную базу")
    
    return await upload_to_global_index(file, current_user)

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

@app.post("/admin/global-index/upload", dependencies=[Depends(require_role("admin"))])
async def upload_to_global_index(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Загрузка документа в глобальную базу знаний"""
    import shutil
    
    logger.info(f"📥 Получен запрос на загрузку от {current_user['username']}")
    logger.info(f"📄 Файл: {file.filename}, type: {file.content_type}, size: {file.size}")
    
    file_path = os.path.join(settings.GLOBAL_INDEX_PATH, "documents", file.filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Сохраняем файл явно
    logger.info(f"💾 Сохранение в {file_path}...")
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"✅ Файл сохранён")
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения: {str(e)}")

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    logger.info(f"📊 Размер: {file_size_mb:.4f} MB")

    # Добавляем в индекс (это может занять время)
    try:
        logger.info(f"🔄 Начало индексации: {file.filename}")
        await rag_engine.global_pqa.add_document(
            file_path, 
            file.filename, 
            category="global_index"
        )
        logger.info(f"✅ Индексация завершена: {file.filename}")
        
        log_audit("global_doc_uploaded", current_user["username"], {"document": file.filename, "size_mb": round(file_size_mb, 2)})
        return {
            "message": "Документ добавлен в глобальную базу",
            "document": {
                "name": file.filename,
                "path": file_path,
                "size_mb": round(file_size_mb, 2),
                "uploaded_at": datetime.now().isoformat(),
                "uploaded_by": current_user["username"]
            }
        }
    except Exception as e:
        logger.error(f"❌ Ошибка индексации {file.filename}: {e}")
        # Не удаляем файл при ошибке — администратор может попробовать снова
        raise HTTPException(status_code=500, detail=f"Ошибка индексации: {str(e)}")

@app.get("/admin/global-index/documents", dependencies=[Depends(require_role("admin"))])
async def list_global_documents_admin(current_user: dict = Depends(get_current_user)):
    """Получить список документов в глобальной базе (admin)"""
    return await list_global_documents_public()

@app.get("/global-index/documents")
async def list_global_documents_public():
    """Получить список документов в глобальной базе (все пользователи)"""
    import glob
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
    """Удалить документ из глобальной базы"""
    file_path = os.path.join(settings.GLOBAL_INDEX_PATH, "documents", doc_name)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Документ не найден")
    
    try:
        os.remove(file_path)
        # Переиндексируем
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
    """Получить список файлов в папке uploads, ожидающих загрузки"""
    import glob
    pending_files = []

    # Поддерживаемые форматы PaperQA2:
    # https://github.com/Future-House/paper-qa#valid-extensions
    for pattern in ["*.pdf", "*.txt", "*.md", "*.html", "*.docx", "*.xlsx", "*.pptx", "*.py", "*.ts", "*.yaml", "*.json", "*.csv", "*.xml"]:
        file_pattern = os.path.join(settings.UPLOADS_PATH, pattern)
        for file_path in glob.glob(file_pattern):
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                size_bytes = stat.st_size
                size_mb = size_bytes / (1024 * 1024)
                pending_files.append({
                    "name": os.path.basename(file_path),
                    "path": file_path,
                    "size_bytes": size_bytes,
                    "size_mb": round(size_mb, 4),
                    "size_formatted": f"{size_bytes / (1024 * 1024):.2f} MB" if size_bytes >= 1024 * 1024 else f"{size_bytes / 1024:.1f} KB",
                    "added_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

    return sorted(pending_files, key=lambda x: x["added_at"])

# Глобальная переменная для хранения статуса загрузки
upload_status = {}
# Храним ссылки на фоновые задачи
background_tasks = {}

async def process_upload_task(user_id: str):
    """Фоновая задача для загрузки файлов"""
    import glob
    import shutil
    
    uploaded = []
    errors = []
    
    # Считаем общее количество файлов
    all_files = []
    for pattern in ["*.pdf", "*.txt", "*.md", "*.html", "*.docx", "*.xlsx", "*.pptx", "*.py", "*.ts", "*.yaml", "*.json", "*.csv", "*.xml"]:
        file_pattern = os.path.join(settings.UPLOADS_PATH, pattern)
        all_files.extend(glob.glob(file_pattern))
    
    total_files = len(all_files)
    logger.info(f"📊 Найдено файлов для загрузки: {total_files}")
    
    for pattern in ["*.pdf", "*.txt", "*.md", "*.html", "*.docx", "*.xlsx", "*.pptx", "*.py", "*.ts", "*.yaml", "*.json", "*.csv", "*.xml"]:
        file_pattern = os.path.join(settings.UPLOADS_PATH, pattern)
        for file_path in glob.glob(file_pattern):
            if os.path.isfile(file_path):
                filename = os.path.basename(file_path)
                current_num = len(uploaded) + len(errors) + 1
                try:
                    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    logger.info(f"🔄 [{current_num}/{total_files}] Обработка файла: {filename} ({file_size_mb:.2f} MB)")
                    logger.info(f"  📖 Шаг 1/3: Чтение и парсинг файла...")

                    # Добавляем в индекс
                    logger.info(f"  🧠 Шаг 2/3: Индексация (эмбеддинг и сохранение)...")
                    await rag_engine.global_pqa.add_document(
                        file_path,
                        filename,
                        category="global_index"
                    )

                    # Перемещаем в documents после успешной индексации
                    # Если файл с таким именем уже есть — добавляем номер
                    dest_path = os.path.join(settings.GLOBAL_INDEX_PATH, "documents", filename)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    
                    # Проверяем конфликт имён
                    if os.path.exists(dest_path):
                        # Разбиваем имя на части: file.pdf → file, .pdf
                        name_parts = os.path.splitext(filename)
                        base_name = name_parts[0]
                        extension = name_parts[1]
                        
                        # Ищем свободное имя с номером
                        counter = 1
                        while True:
                            new_filename = f"{base_name}_{counter}{extension}"
                            new_dest_path = os.path.join(settings.GLOBAL_INDEX_PATH, "documents", new_filename)
                            if not os.path.exists(new_dest_path):
                                dest_path = new_dest_path
                                filename = new_filename
                                logger.info(f"⚠️ Файл переименован: {new_filename} (конфликт имён)")
                                break
                            counter += 1
                    
                    shutil.move(file_path, dest_path)
                    logger.info(f"  ✅ Файл перемещён в хранилище: {filename}")
                    
                    logger.info(f"✅ Файл {filename} загружен успешно")

                    uploaded.append({
                        "name": filename,
                        "size_mb": round(file_size_mb, 2)
                    })

                except Exception as e:
                    error_msg = f"Ошибка при загрузке {filename}: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    errors.append({"name": filename, "error": str(e)})
    
    upload_status[user_id] = {
        "completed": True,
        "message": f"Загружено {len(uploaded)} файлов",
        "uploaded": uploaded,
        "errors": errors
    }
    
    if uploaded:
        log_audit("global_doc_uploaded", user_id, {
            "documents": [f["name"] for f in uploaded],
            "count": len(uploaded)
        })
        logger.info(f"🎉 Загрузка завершена: {len(uploaded)} файлов успешно обработано")

@app.post("/admin/global-index/process-uploads", dependencies=[Depends(require_role("admin"))])
async def process_pending_uploads(current_user: dict = Depends(get_current_user)):
    """Запустить загрузку всех файлов из папки uploads в фоновом режиме"""
    user_id = current_user["username"]
    
    # Проверяем, есть ли файлы
    import glob
    all_files = []
    for pattern in ["*.pdf", "*.txt", "*.md", "*.html", "*.docx", "*.xlsx", "*.pptx", "*.py", "*.ts", "*.yaml", "*.json", "*.csv", "*.xml"]:
        file_pattern = os.path.join(settings.UPLOADS_PATH, pattern)
        all_files.extend(glob.glob(file_pattern))
    
    if not all_files:
        return {"message": "Нет файлов для загрузки"}
    
    # Инициализируем статус
    upload_status[user_id] = {"completed": False, "message": "Загрузка...", "uploaded": [], "errors": []}
    
    # Запускаем фоновую задачу в отдельном потоке
    task = asyncio.create_task(asyncio.to_thread(process_upload_task_sync, user_id))
    background_tasks[user_id] = task
    
    return {"message": f"Начата загрузка {len(all_files)} файлов", "status": "processing"}

def process_upload_task_sync(user_id: str):
    """Синхронная обёртка для фоновой задачи"""
    import glob
    import shutil
    import asyncio
    
    uploaded = []
    errors = []
    
    # Считаем общее количество файлов
    all_files = []
    for pattern in ["*.pdf", "*.txt", "*.md", "*.html", "*.docx", "*.xlsx", "*.pptx", "*.py", "*.ts", "*.yaml", "*.json", "*.csv", "*.xml"]:
        file_pattern = os.path.join(settings.UPLOADS_PATH, pattern)
        all_files.extend(glob.glob(file_pattern))
    
    total_files = len(all_files)
    logger.info(f"📊 Найдено файлов для загрузки: {total_files}")
    
    # Запускаем асинхронную функцию в event loop
    from paperqa import Docs, Settings

    async def process_all_files():
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
        
        ollama_embedding_config = {
            "model_list": [
                {
                    "model_name": f"ollama/{settings.DEFAULT_EMBEDDING_MODEL}",
                    "litellm_params": {
                        "model": f"ollama/{settings.DEFAULT_EMBEDDING_MODEL}",
                        "api_base": settings.OLLAMA_BASE_URL,
                    },
                }
            ]
        }
        
        for idx, pattern in enumerate(["*.pdf", "*.txt", "*.md", "*.html", "*.docx", "*.xlsx", "*.pptx", "*.py", "*.ts", "*.yaml", "*.json", "*.csv", "*.xml"]):
            file_pattern = os.path.join(settings.UPLOADS_PATH, pattern)
            files_for_pattern = glob.glob(file_pattern)
            
            for file_path in files_for_pattern:
                if os.path.isfile(file_path):
                    filename = os.path.basename(file_path)
                    current_num = len(uploaded) + len(errors) + 1

                    # Обновляем прогресс
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
                        logger.info(f"🔄 [{current_num}/{total_files}] Обработка файла: {filename} ({file_size_mb:.2f} MB)")
                        logger.info(f"  📖 Шаг 1/3: Чтение и парсинг файла...")

                        # Создаем Docs и добавляем файл (sync метод в версии 5.29.1)
                        # Используем asyncio.to_thread для запуска в отдельном потоке
                        import threading
                        import fitz  # PyMuPDF
                        import tempfile
                        
                        def add_doc():
                            docs = Docs()
                            
                            # Для PDF используем PyMuPDF для извлечения текста
                            if file_path.lower().endswith('.pdf'):
                                # Извлекаем текст через PyMuPDF
                                pdf_doc = fitz.open(file_path)
                                text = ""
                                for page in pdf_doc:
                                    text += page.get_text()
                                pdf_doc.close()
                                
                                # Сохраняем текст во временный файл
                                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                                    f.write(text)
                                    temp_file = f.name
                                
                                try:
                                    # Добавляем как текст из файла с правильной конфигурацией Ollama
                                    # В новой версии используем asyncio.run для aadd
                                    async def add_async():
                                        await docs.aadd(
                                            temp_file,
                                            docname=filename,
                                            citation="global_index",
                                            settings=Settings(
                                                llm=f"ollama/{settings.DEFAULT_LLM_MODEL}",
                                                llm_config=ollama_llm_config,
                                                summary_llm=f"ollama/{settings.DEFAULT_LLM_MODEL}",
                                                summary_llm_config=ollama_llm_config,
                                                embedding=f"ollama/{settings.DEFAULT_EMBEDDING_MODEL}",
                                                embedding_config=ollama_embedding_config,
                                            )
                                        )
                                        return docs
                                    
                                    # Создаем новый event loop для запуска
                                    import asyncio
                                    new_loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(new_loop)
                                    try:
                                        new_loop.run_until_complete(add_async())
                                    finally:
                                        new_loop.close()
                                    
                                finally:
                                    # Удаляем временный файл
                                    import os
                                    os.unlink(temp_file)
                            else:
                                # Для других файлов используем стандартный метод
                                async def add_async():
                                    await docs.aadd(
                                        file_path,
                                        docname=filename,
                                        citation="global_index",
                                        settings=Settings(
                                            llm=f"ollama/{settings.DEFAULT_LLM_MODEL}",
                                            llm_config=ollama_llm_config,
                                            summary_llm=f"ollama/{settings.DEFAULT_LLM_MODEL}",
                                            summary_llm_config=ollama_llm_config,
                                            embedding=f"ollama/{settings.DEFAULT_EMBEDDING_MODEL}",
                                            embedding_config=ollama_embedding_config,
                                        )
                                    )
                                    return docs
                                
                                # Создаем новый event loop для запуска
                                import asyncio
                                new_loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(new_loop)
                                try:
                                    new_loop.run_until_complete(add_async())
                                finally:
                                    new_loop.close()
                            
                            return docs
                        
                        # Запускаем в отдельном потоке
                        loop = asyncio.get_event_loop()
                        docs = await loop.run_in_executor(None, add_doc)
                        
                        logger.info(f"  🧠 Шаг 2/3: Создание эмбеддингов и сохранение...")
                        
                        # Сохраняем индекс
                        index_path = settings.GLOBAL_INDEX_PATH
                        index_file = os.path.join(index_path, "docs.pkl")
                        os.makedirs(index_path, exist_ok=True)
                        with open(index_file, 'wb') as f:
                            pickle.dump(docs, f)

                        # Перемещаем в documents
                        dest_path = os.path.join(settings.GLOBAL_INDEX_PATH, "documents", filename)
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        shutil.move(file_path, dest_path)
                        
                        logger.info(f"  ✅ Шаг 3/3: Файл перемещён в хранилище")
                        logger.info(f"✅ Файл {filename} загружен успешно")

                        uploaded.append({
                            "name": filename,
                            "size_mb": round(file_size_mb, 2)
                        })

                    except Exception as e:
                        error_msg = f"Ошибка при загрузке {filename}: {str(e)}"
                        logger.error(f"❌ {error_msg}")
                        import traceback
                        logger.error(traceback.format_exc())
                        errors.append({"name": filename, "error": str(e)})
        
        return uploaded, errors
    
    # Запускаем асинхронную функцию
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        uploaded, errors = loop.run_until_complete(process_all_files())
    finally:
        loop.close()
    
    upload_status[user_id] = {
        "completed": True,
        "message": f"Загружено {len(uploaded)} файлов",
        "uploaded": uploaded,
        "errors": errors
    }
    
    if uploaded:
        log_audit("global_doc_uploaded", user_id, {
            "documents": [f["name"] for f in uploaded],
            "count": len(uploaded)
        })
        logger.info(f"🎉 Загрузка завершена: {len(uploaded)} файлов успешно обработано")

@app.get("/admin/global-index/process-uploads/status", dependencies=[Depends(require_role("admin"))])
async def get_upload_status(current_user: dict = Depends(get_current_user)):
    """Получить статус загрузки"""
    user_id = current_user["username"]
    return upload_status.get(user_id, {"message": "Нет активных загрузок"})

@app.delete("/admin/global-index/pending/{file_name}", dependencies=[Depends(require_role("admin"))])
async def delete_pending_upload(file_name: str, current_user: dict = Depends(get_current_user)):
    """Удалить файл из папки uploads без загрузки"""
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
    """Получить журнал аудита активности пользователей"""
    audit_file = os.path.join(settings.DATA_PATH, "audit_log.json")
    
    if not os.path.exists(audit_file):
        return []
    
    import json
    with open(audit_file, 'r') as f:
        logs = json.load(f)
    
    # Возвращаем последние 100 записей
    return logs[-100:]

def log_audit(action: str, user: str, details: dict = None):
    """Записать действие в журнал аудита"""
    audit_file = os.path.join(settings.DATA_PATH, "audit_log.json")
    os.makedirs(os.path.dirname(audit_file), exist_ok=True)
    
    import json
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
    
    # Храним только последние 1000 записей
    logs = logs[-1000:]
    
    with open(audit_file, 'w') as f:
        json.dump(logs, f, indent=2)

@app.on_event("startup")
async def startup_event():
    print("🚀 BOAAI_S запускается...")
    print(f"📁 Data path: {settings.DATA_PATH}")
    print(f"🤖 Ollama URL: {settings.OLLAMA_BASE_URL}")
    print(f"🧠 LLM Model: {settings.DEFAULT_LLM_MODEL}")
