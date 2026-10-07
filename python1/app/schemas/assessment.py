from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class QuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=5)
    option_a: str = Field(..., min_length=1)
    option_b: str = Field(..., min_length=1)
    option_c: str = Field(..., min_length=1)
    option_d: str = Field(..., min_length=1)
    correct_option: str = Field(..., pattern="^[A-Da-d]$")
    explanation: Optional[str] = None


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    option_a: Optional[str] = None
    option_b: Optional[str] = None
    option_c: Optional[str] = None
    option_d: Optional[str] = None
    correct_option: Optional[str] = Field(None, pattern="^[A-Da-d]$")
    explanation: Optional[str] = None


class QuestionResponse(BaseModel):
    id: int
    assessment_id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: Optional[str] = None  # None for students before submit
    explanation: Optional[str] = None

    class Config:
        from_attributes = True


class AssessmentCreate(BaseModel):
    course_id: int
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    topic: Optional[str] = Field("General", description="Variables, Loops, Functions, OOP, etc.")
    pass_percentage: float = 70.0


class AssessmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    topic: Optional[str] = None
    pass_percentage: Optional[float] = None


class AssessmentResponse(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str] = None
    topic: Optional[str] = "General"
    pass_percentage: float
    questions_count: Optional[int] = 0

    class Config:
        from_attributes = True


class AssessmentDetailResponse(AssessmentResponse):
    questions: List[QuestionResponse] = []


class AssessmentSubmit(BaseModel):
    answers: Dict[str, str]  # { "question_id": "A" }


class AssessmentResultResponse(BaseModel):
    id: int
    assessment_id: int
    assessment_title: Optional[str] = None
    course_title: Optional[str] = None
    topic: Optional[str] = None
    score: int
    total_questions: int
    percentage: float
    passed: bool
    completed_at: datetime
    answers_json: Optional[str] = None

    class Config:
        from_attributes = True
