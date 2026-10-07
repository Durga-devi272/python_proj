from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import os

from app.config import settings
from app.database import engine, Base, ensure_schema_updates
import app.models  # ensure all models are registered
from app.routers import (
    auth_router,
    courses_router,
    lessons_router,
    assessments_router,
    progress_router,
    admin_router,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables and ensure columns on startup
    Base.metadata.create_all(bind=engine)
    ensure_schema_updates(engine)
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade modern E-Learning Platform built with FastAPI, SQLAlchemy, and Jinja2",
    version="1.0.0",
    lifespan=lifespan
)

# Static files mounting
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# Register Routers
app.include_router(auth_router)
app.include_router(courses_router)
app.include_router(lessons_router)
app.include_router(assessments_router)
app.include_router(progress_router)
app.include_router(admin_router)

from app.templating import render_template
from fastapi.responses import JSONResponse

# Exception Handlers
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=404, content={"detail": "Resource not found"})
    return render_template(
        request,
        "base.html",
        {
            "user": None,
            "custom_content": """
            <div style="min-height: 70vh; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 2rem;">
                <div style="font-size: 5rem; font-weight: 800; color: #6366f1; margin-bottom: 1rem;">404</div>
                <h1 style="font-size: 1.875rem; font-weight: 700; color: #1e293b; margin-bottom: 0.5rem;">Page Not Found</h1>
                <p style="color: #64748b; max-width: 480px; margin-bottom: 2rem;">The page you are looking for doesn't exist or has been moved.</p>
                <a href="/" class="btn btn-primary" style="padding: 0.75rem 1.75rem; font-weight: 600; text-decoration: none; border-radius: 0.5rem; background: #4f46e5; color: white;">Return to Home</a>
            </div>
            """
        },
        status_code=404
    )
