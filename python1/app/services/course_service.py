from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.models.course import Course
from app.models.lesson import Module, Lesson
from app.models.progress import Enrollment, LessonProgress
from app.models.assessment import Assessment
from app.schemas.course import CourseCreate, CourseUpdate

def get_courses(
    db: Session,
    search: Optional[str] = None,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    sort_by: Optional[str] = "popular",
    published_only: bool = True
) -> List[dict]:
    query = db.query(Course)
    if published_only:
        query = query.filter(Course.published == True)

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Course.title.ilike(search_pattern),
                Course.description.ilike(search_pattern),
                Course.instructor.ilike(search_pattern),
                Course.category.ilike(search_pattern),
            )
        )

    if category and category.lower() != "all":
        query = query.filter(Course.category.ilike(category.strip()))

    if difficulty and difficulty.lower() != "all":
        query = query.filter(Course.difficulty.ilike(difficulty.strip()))

    courses = query.all()
    
    # Enrich course items with counts and stats
    course_list = []
    for c in courses:
        modules_count = len(c.modules)
        lessons_count = sum(len(m.lessons) for m in c.modules)
        students_count = len(c.enrollments)
        course_list.append({
            "course": c,
            "modules_count": modules_count,
            "lessons_count": lessons_count,
            "students_count": students_count,
            "rating": c.rating
        })

    # Sort
    if sort_by == "popular":
        course_list.sort(key=lambda x: x["students_count"], reverse=True)
    elif sort_by == "rating":
        course_list.sort(key=lambda x: x["rating"], reverse=True)
    elif sort_by == "newest":
        course_list.sort(key=lambda x: x["course"].created_at, reverse=True)

    return course_list

def get_course_by_id(db: Session, course_id: int) -> Optional[Course]:
    return db.query(Course).filter(Course.id == course_id).first()

def create_course(db: Session, course_in: CourseCreate) -> Course:
    course = Course(
        title=course_in.title,
        description=course_in.description,
        category=course_in.category,
        difficulty=course_in.difficulty,
        duration=course_in.duration,
        instructor=course_in.instructor,
        thumbnail=course_in.thumbnail,
        learning_objectives=course_in.learning_objectives,
        published=course_in.published
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course

def update_course(db: Session, course: Course, course_in: CourseUpdate) -> Course:
    data = course_in.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return course

def delete_course(db: Session, course: Course) -> None:
    db.delete(course)
    db.commit()
