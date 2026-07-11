import sys
import os

# Add /app to Python path



# app/test_setup.py

from sqlalchemy import text
from core.database import Base, engine, SessionLocal
from workers.tasks import process_case_task
from models.user import User
from app.models.patient_case import PatientCase
from models.reports import Report

# 1️⃣ Create all tables
print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")

# 2️⃣ Test database connection
print("Testing database connection...")
db = SessionLocal()
try:
    result = db.execute(text("SELECT 1")).fetchall()
    print("Database connection test result:", result)
finally:
    db.close()

# 3️⃣ Test Celery task
print("Sending test Celery task...")
task = process_case_task.delay(1)  # replace 1 with an actual case ID if exists
print("Task sent! Task ID:", task.id)
print("Check your worker logs to see if the task was executed.")
