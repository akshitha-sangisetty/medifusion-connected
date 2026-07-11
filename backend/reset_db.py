# reset_db.py
from app.core.database import Base, engine

# Drop all tables
print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)

# Recreate all tables
print("Creating tables...")
Base.metadata.create_all(bind=engine)

print("Database has been reset successfully!")
