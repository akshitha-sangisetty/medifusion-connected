# app/schemas/user_schema.py
from typing import Literal

from pydantic import BaseModel, constr

class UserCreate(BaseModel):
    username: constr(strip_whitespace=True, min_length=3, max_length=64, regex=r"^[A-Za-z0-9_.-]+$")
    password: constr(min_length=12, max_length=72)
    full_name: constr(strip_whitespace=True, min_length=1, max_length=120)
    role: Literal["patient", "doctor", "lab"]

class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str

    class Config:
        orm_mode = True  # Pydantic v2 replacement for orm_mode
