from pydantic import BaseModel
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