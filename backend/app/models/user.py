from pydantic import BaseModel
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
