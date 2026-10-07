from app.routers.auth import router as auth_router
from app.routers.courses import router as courses_router
from app.routers.lessons import router as lessons_router
from app.routers.assessments import router as assessments_router
from app.routers.progress import router as progress_router
from app.routers.admin import router as admin_router

__all__ = [
    "auth_router",
    "courses_router",
    "lessons_router",
    "assessments_router",
    "progress_router",
    "admin_router"
]
