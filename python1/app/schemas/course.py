from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.lesson import ModuleResponse
from app.schemas.assessment import AssessmentResponse

class CourseBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str
    category: str = Field(..., min_length=2, max_length=50)
    difficulty: str = Field("Beginner", min_length=2, max_length=20)
    duration: str = "6 hours"
    instructor: str = Field(..., min_length=2, max_length=100)
    thumbnail: Optional[str] = None
    learning_objectives: Optional[str] = None
    published: bool = True


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    duration: Optional[str] = None
    instructor: Optional[str] = None
    thumbnail: Optional[str] = None
    learning_objectives: Optional[str] = None
    published: Optional[bool] = None


class CourseResponse(CourseBase):
    id: int
    rating: float
    created_at: datetime
    modules_count: int = 0
    lessons_count: int = 0
    students_count: int = 0
    is_enrolled: Optional[bool] = False
    user_progress: Optional[float] = 0.0

    class Config:
        from_attributes = True


class CourseDetailResponse(CourseResponse):
    modules: List[ModuleResponse] = []
    assessments: List[AssessmentResponse] = []
