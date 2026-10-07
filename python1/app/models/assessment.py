from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    topic = Column(String(100), default="General", nullable=True)  # Variables, Loops, Functions, OOP, etc.
    pass_percentage = Column(Float, default=70.0, nullable=False)

    # Relationships
    course = relationship("Course", back_populates="assessments")
    questions = relationship("Question", back_populates="assessment", cascade="all, delete-orphan", order_by="Question.id")
    results = relationship("AssessmentResult", back_populates="assessment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Assessment {self.title}>"


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    option_a = Column(String(255), nullable=False)
    option_b = Column(String(255), nullable=False)
    option_c = Column(String(255), nullable=False)
    option_d = Column(String(255), nullable=False)
    correct_option = Column(String(10), nullable=False)  # A, B, C, D
    explanation = Column(Text, nullable=True)

    # Relationships
    assessment = relationship("Assessment", back_populates="questions")

    def __repr__(self):
        return f"<Question id={self.id} correct={self.correct_option}>"


class AssessmentResult(Base):
    __tablename__ = "assessment_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    score = Column(Integer, nullable=False)  # number of correct answers
    total_questions = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
    passed = Column(Boolean, default=False, nullable=False)
    answers_json = Column(Text, nullable=True)  # JSON string of selected answers
    completed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="assessment_results")
    assessment = relationship("Assessment", back_populates="results")

    def __repr__(self):
        return f"<AssessmentResult user_id={self.user_id} assessment_id={self.assessment_id} score={self.score}/{self.total_questions}>"
