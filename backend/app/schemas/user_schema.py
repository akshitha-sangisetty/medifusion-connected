# app/schemas/user_schema.py
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str  # patient, doctor, lab

class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str

    class Config:
        orm_mode = True  # Pydantic v2 replacement for orm_mode
