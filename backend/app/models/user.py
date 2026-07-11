from sqlalchemy import Column, String, Boolean
from app.models.base import Base, IdMixin  # Corrected import

class User(Base, IdMixin):
    __tablename__ = "users"

    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="patient")
    is_doctor = Column(Boolean, default=False)
    is_lab = Column(Boolean, default=False)
