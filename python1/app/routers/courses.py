from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.course import Course
from app.models.lesson import Module, Lesson
from app.models.progress import Enrollment, LessonProgress
from app.models.user import User
from app.schemas.course import CourseCreate, CourseUpdate, CourseResponse, CourseDetailResponse
from app.templating import render_template
from app.services.auth_service import get_current_user, get_current_user_optional, get_current_admin
from app.services.course_service import (
    get_courses,
    get_course_by_id,
    create_course,
    update_course,
    delete_course
)
from app.services.progress_service import enroll_user, is_user_enrolled, get_user_enrollment

router = APIRouter(tags=["Courses"])

# ----------------- HTML Views -----------------

@router.get("/", response_class=HTMLResponse)
def home_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db=db)
    # Popular courses
    all_courses_enriched = get_courses(db, sort_by="popular", published_only=True)
    popular_courses = all_courses_enriched[:4]

    # Platform statistics
    total_students = db.query(User).filter(User.role == "student").count()
    total_courses = db.query(Course).filter(Course.published == True).count()
    total_enrollments = db.query(Enrollment).count()
    avg_rating = 4.9

    categories = [
        {"name": "Python Programming", "icon": "fa-brands fa-python", "count": 12},
        {"name": "Data Structures & Algorithms", "icon": "fa-solid fa-network-wired", "count": 8},
        {"name": "Database Management", "icon": "fa-solid fa-database", "count": 6},
        {"name": "Web Development", "icon": "fa-solid fa-code", "count": 15},
        {"name": "System Design & DevOps", "icon": "fa-solid fa-server", "count": 9},
        {"name": "Machine Learning & AI", "icon": "fa-solid fa-brain", "count": 11},
    ]

    return render_template(
        request,
        "home.html",
        {
            "user": user,
            "popular_courses": popular_courses,
            "categories": categories,
            "total_students": max(total_students, 1250),
            "total_courses": total_courses,
            "total_enrollments": max(total_enrollments, 3420),
            "avg_rating": avg_rating
        }
    )

@router.get("/courses", response_class=HTMLResponse)
def courses_page(
    request: Request,
    q: Optional[str] = None,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    sort: Optional[str] = "popular",
    db: Session = Depends(get_db)
):
    user = get_current_user_optional(request, db=db)
    course_items = get_courses(
        db,
        search=q,
        category=category,
        difficulty=difficulty,
        sort_by=sort,
        published_only=True
    )

    # Attach enrollment data if user is logged in
    user_enrolled_map = {}
    if user:
        enrollments = db.query(Enrollment).filter(Enrollment.user_id == user.id).all()
        for enr in enrollments:
            user_enrolled_map[enr.course_id] = enr.progress

    for item in course_items:
        c_id = item["course"].id
        item["is_enrolled"] = c_id in user_enrolled_map
        item["user_progress"] = user_enrolled_map.get(c_id, 0.0)

    # All unique categories for filter pills
    all_categories = [
        "All Categories",
        "Python Programming",
        "Data Structures",
        "Database Management",
        "Web Development"
    ]

    return render_template(
        request,
        "courses.html",
        {
            "user": user,
            "courses": course_items,
            "search_query": q or "",
            "selected_category": category or "All Categories",
            "selected_difficulty": difficulty or "All",
            "selected_sort": sort or "popular",
            "categories": all_categories
        }
    )

@router.get("/courses/{course_id}", response_class=HTMLResponse)
def course_detail_page(course_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db=db)
    course = get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    is_enrolled = False
    user_progress = 0.0
    first_lesson_id = None

    if user:
        enrollment = get_user_enrollment(db, user.id, course_id)
        if enrollment:
            is_enrolled = True
            user_progress = enrollment.progress

    # Total lessons and first lesson id
    total_lessons = 0
    for mod in course.modules:
        for lesson in mod.lessons:
            total_lessons += 1
            if not first_lesson_id:
                first_lesson_id = lesson.id

    # Parse learning objectives
    objectives = []
    if course.learning_objectives:
        objectives = [obj.strip() for obj in course.learning_objectives.split("\n") if obj.strip()]

    return render_template(
        request,
        "course_detail.html",
        {
            "user": user,
            "course": course,
            "is_enrolled": is_enrolled,
            "user_progress": user_progress,
            "total_lessons": total_lessons,
            "first_lesson_id": first_lesson_id,
            "objectives": objectives,
            "students_count": len(course.enrollments)
        }
    )

@router.post("/courses/{course_id}/enroll")
def enroll_course_action(course_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db=db)
    if not user:
        return RedirectResponse(url=f"/login?next=/courses/{course_id}", status_code=status.HTTP_303_SEE_OTHER)

    course = get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    enroll_user(db, user.id, course_id)

    # Redirect directly into the learning room
    return RedirectResponse(url=f"/courses/{course_id}/learn", status_code=status.HTTP_303_SEE_OTHER)

# ----------------- REST API Endpoints -----------------

@router.get("/api/courses")
def api_get_courses(
    search: Optional[str] = None,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    sort_by: Optional[str] = "popular",
    db: Session = Depends(get_db)
):
    items = get_courses(db, search, category, difficulty, sort_by, published_only=True)
    results = []
    for it in items:
        c = it["course"]
        results.append({
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "category": c.category,
            "difficulty": c.difficulty,
            "duration": c.duration,
            "instructor": c.instructor,
            "thumbnail": c.thumbnail,
            "rating": c.rating,
            "learning_objectives": c.learning_objectives,
            "published": c.published,
            "created_at": c.created_at,
            "modules_count": it["modules_count"],
            "lessons_count": it["lessons_count"],
            "students_count": it["students_count"],
        })
    return results

@router.get("/api/courses/{course_id}")
def api_get_course(course_id: int, db: Session = Depends(get_db)):
    course = get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    modules_data = []
    for m in course.modules:
        lessons_data = []
        for l in m.lessons:
            lessons_data.append({
                "id": l.id,
                "module_id": l.module_id,
                "title": l.title,
                "duration": l.duration,
                "topic": l.topic or "General",
                "order": l.order,
                "video_url": l.video_url,
                "resource_url": l.resource_url
            })
        modules_data.append({
            "id": m.id,
            "course_id": m.course_id,
            "title": m.title,
            "description": m.description,
            "order": m.order,
            "lessons": lessons_data
        })

    assessments_data = [
        {
            "id": a.id,
            "title": a.title,
            "topic": a.topic or "General",
            "description": a.description,
            "pass_percentage": a.pass_percentage,
            "questions_count": len(a.questions)
        } for a in course.assessments
    ]

    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "category": course.category,
        "difficulty": course.difficulty,
        "duration": course.duration,
        "instructor": course.instructor,
        "thumbnail": course.thumbnail,
        "rating": course.rating,
        "learning_objectives": course.learning_objectives,
        "published": course.published,
        "created_at": course.created_at,
        "modules": modules_data,
        "assessments": assessments_data,
        "students_count": len(course.enrollments)
    }

@router.post("/api/courses/{course_id}/enroll")
def api_enroll_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    course = get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    enrollment = enroll_user(db, current_user.id, course_id)
    return {
        "message": "Enrolled successfully",
        "course_id": course.id,
        "course_title": course.title,
        "progress": enrollment.progress,
        "enrolled_at": enrollment.enrolled_at
    }

@router.get("/api/my-courses")
def api_my_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    enrollments = db.query(Enrollment).filter(Enrollment.user_id == current_user.id).all()
    results = []
    for enr in enrollments:
        c = enr.course
        results.append({
            "enrollment_id": enr.id,
            "course_id": c.id,
            "title": c.title,
            "instructor": c.instructor,
            "thumbnail": c.thumbnail,
            "progress": enr.progress,
            "enrolled_at": enr.enrolled_at,
            "completed_at": enr.completed_at
        })
    return results

@router.post("/api/courses", status_code=status.HTTP_201_CREATED)
def api_create_course(
    course_in: CourseCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    new_course = create_course(db, course_in)
    return new_course

@router.put("/api/courses/{course_id}")
def api_update_course(
    course_id: int,
    course_in: CourseUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    course = get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    updated = update_course(db, course, course_in)
    return updated

@router.delete("/api/courses/{course_id}")
def api_delete_course(
    course_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    course = get_course_by_id(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    delete_course(db, course)
    return {"message": "Course deleted successfully"}
