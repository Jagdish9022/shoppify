from app.db.database import engine
from app.db.models import Base

# Create tables
Base.metadata.create_all(bind=engine)

def init_db():
    print("Database tables created successfully.")

if __name__ == "__main__":
    init_db()
