from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class EnrollmentResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    course_title: str
    course_thumbnail: Optional[str] = None
    course_instructor: str
    progress: float
    enrolled_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LessonProgressResponse(BaseModel):
    lesson_id: int
    lesson_title: str
    completed: bool
    completed_at: Optional[datetime] = None


class ProgressStatsResponse(BaseModel):
    enrolled_courses_count: int
    completed_courses_count: int
    completed_lessons_count: int
    total_lessons_count: int
    average_assessment_score: float
    streak_days: int
