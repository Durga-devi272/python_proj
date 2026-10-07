from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Handle SQLite specific parameters
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

from sqlalchemy import inspect

def ensure_schema_updates(bind_engine=engine):
    """Safely migrate and add new columns to existing tables if missing."""
    try:
        inspector = inspect(bind_engine)
        existing_tables = inspector.get_table_names()

        with bind_engine.connect() as conn:
            # 1. users.preferred_resource_type
            if "users" in existing_tables:
                user_cols = [c["name"] for c in inspector.get_columns("users")]
                if "preferred_resource_type" not in user_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN preferred_resource_type VARCHAR(50) DEFAULT 'Mixed'"))
                    conn.commit()

            # 2. lessons.topic
            if "lessons" in existing_tables:
                lesson_cols = [c["name"] for c in inspector.get_columns("lessons")]
                if "topic" not in lesson_cols:
                    conn.execute(text("ALTER TABLE lessons ADD COLUMN topic VARCHAR(100) DEFAULT 'General'"))
                    conn.commit()

            # 3. assessments.topic
            if "assessments" in existing_tables:
                asm_cols = [c["name"] for c in inspector.get_columns("assessments")]
                if "topic" not in asm_cols:
                    conn.execute(text("ALTER TABLE assessments ADD COLUMN topic VARCHAR(100) DEFAULT 'General'"))
                    conn.commit()
    except Exception as e:
        print(f"[!] Warning during ensure_schema_updates: {e}")

# Ensure schema consistency on module load
try:
    Base.metadata.create_all(bind=engine)
    ensure_schema_updates(engine)
except Exception:
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
