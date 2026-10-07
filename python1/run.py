import sys
import uvicorn
from app.config import settings
from app.database import engine, Base, ensure_schema_updates
import app.models  # Register models

# Support UTF-8 in Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    print("==================================================")
    print(f"[*] Initializing {settings.APP_NAME}")
    print(f"[*] Database: {settings.DATABASE_URL}")
    print(f"[*] Server: http://{settings.HOST}:{settings.PORT}")
    print("==================================================")
    
    # Create DB tables & ensure schema migrations
    Base.metadata.create_all(bind=engine)
    ensure_schema_updates(engine)
    print("[+] Database tables verified and ready.")

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )

if __name__ == "__main__":
    main()
