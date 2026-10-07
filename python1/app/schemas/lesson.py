from typing import Optional, List
from pydantic import BaseModel, Field

class LessonCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    content: str
    video_url: Optional[str] = None
    resource_url: Optional[str] = None
    duration: str = "15 mins"
    topic: Optional[str] = Field("General", description="Variables, Loops, Functions, OOP, etc.")
    order: int = 1


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    video_url: Optional[str] = None
    resource_url: Optional[str] = None
    duration: Optional[str] = None
    topic: Optional[str] = None
    order: Optional[int] = None


class LessonResponse(BaseModel):
    id: int
    module_id: int
    title: str
    content: str
    video_url: Optional[str] = None
    resource_url: Optional[str] = None
    duration: str
    topic: Optional[str] = "General"
    order: int
    completed: Optional[bool] = False

    class Config:
        from_attributes = True


class ModuleCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    order: int = 1


class ModuleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None


class ModuleResponse(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str] = None
    order: int
    lessons: List[LessonResponse] = []

    class Config:
        from_attributes = True
