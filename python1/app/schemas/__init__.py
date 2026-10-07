from app.schemas.user import UserRegister, UserLogin, UserUpdate, UserResponse, Token
from app.schemas.course import CourseCreate, CourseUpdate, CourseResponse, CourseDetailResponse
from app.schemas.lesson import LessonCreate, LessonUpdate, LessonResponse, ModuleCreate, ModuleUpdate, ModuleResponse
from app.schemas.assessment import (
    QuestionCreate, QuestionUpdate, QuestionResponse,
    AssessmentCreate, AssessmentUpdate, AssessmentResponse, AssessmentDetailResponse,
    AssessmentSubmit, AssessmentResultResponse
)
from app.schemas.progress import EnrollmentResponse, LessonProgressResponse, ProgressStatsResponse

__all__ = [
    "UserRegister", "UserLogin", "UserUpdate", "UserResponse", "Token",
    "CourseCreate", "CourseUpdate", "CourseResponse", "CourseDetailResponse",
    "LessonCreate", "LessonUpdate", "LessonResponse", "ModuleCreate", "ModuleUpdate", "ModuleResponse",
    "QuestionCreate", "QuestionUpdate", "QuestionResponse",
    "AssessmentCreate", "AssessmentUpdate", "AssessmentResponse", "AssessmentDetailResponse",
    "AssessmentSubmit", "AssessmentResultResponse",
    "EnrollmentResponse", "LessonProgressResponse", "ProgressStatsResponse"
]
