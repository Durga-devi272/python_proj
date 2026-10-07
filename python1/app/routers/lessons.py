from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.course import Course
from app.models.lesson import Module, Lesson
from app.models.progress import Enrollment, LessonProgress
from app.models.user import User
from app.templating import render_template
from app.services.auth_service import get_current_user, get_current_user_optional
from app.services.progress_service import (
    enroll_user,
    get_user_enrollment,
    mark_lesson_complete,
    calculate_course_progress
)

router = APIRouter(tags=["Lessons"])

@router.get("/courses/{course_id}/learn")
def enter_learning_room(course_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db=db)
    if not user:
        return RedirectResponse(url=f"/login?next=/courses/{course_id}/learn", status_code=status.HTTP_303_SEE_OTHER)

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    enrollment = get_user_enrollment(db, user.id, course_id)
    if not enrollment:
        enroll_user(db, user.id, course_id)

    # Find the first unfinished lesson or simply the first lesson
    all_lessons = []
    for mod in course.modules:
        for les in mod.lessons:
            all_lessons.append(les)

    if not all_lessons:
        raise HTTPException(status_code=400, detail="This course does not have lessons yet.")

    # Look for first unfinished lesson
    target_lesson = None
    for les in all_lessons:
        done = db.query(LessonProgress).filter(
            LessonProgress.user_id == user.id,
            LessonProgress.lesson_id == les.id,
            LessonProgress.completed == True
        ).first()
        if not done:
            target_lesson = les
            break

    if not target_lesson:
        target_lesson = all_lessons[0]

    return RedirectResponse(url=f"/courses/{course_id}/lessons/{target_lesson.id}", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/courses/{course_id}/lessons/{lesson_id}", response_class=HTMLResponse)
def view_lesson_page(
    course_id: int,
    lesson_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user_optional(request, db=db)
    if not user:
        return RedirectResponse(url=f"/login?next=/courses/{course_id}/lessons/{lesson_id}", status_code=status.HTTP_303_SEE_OTHER)

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson or lesson.module.course_id != course_id:
        raise HTTPException(status_code=404, detail="Lesson not found in this course")

    # Ensure enrollment
    enrollment = get_user_enrollment(db, user.id, course_id)
    if not enrollment:
        enrollment = enroll_user(db, user.id, course_id)

    # Flatten lessons to compute prev and next
    all_lessons = []
    for mod in course.modules:
        for l in mod.lessons:
            all_lessons.append(l)

    prev_lesson = None
    next_lesson = None
    for idx, l in enumerate(all_lessons):
        if l.id == lesson_id:
            if idx > 0:
                prev_lesson = all_lessons[idx - 1]
            if idx + 1 < len(all_lessons):
                next_lesson = all_lessons[idx + 1]
            break

    # Get set of completed lesson IDs for this user
    completed_ids = set()
    records = db.query(LessonProgress.lesson_id).filter(
        LessonProgress.user_id == user.id,
        LessonProgress.completed == True
    ).all()
    for r in records:
        completed_ids.add(r[0])

    is_current_completed = lesson.id in completed_ids

    # Calculate overall course progress
    course_progress = enrollment.progress

    return render_template(
        request,
        "lesson.html",
        {
            "user": user,
            "course": course,
            "lesson": lesson,
            "prev_lesson": prev_lesson,
            "next_lesson": next_lesson,
            "completed_ids": completed_ids,
            "is_current_completed": is_current_completed,
            "course_progress": course_progress,
            "all_lessons_count": len(all_lessons)
        }
    )

# ----------------- REST API Endpoints -----------------

@router.post("/api/lessons/{lesson_id}/complete")
def api_mark_lesson_complete(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = mark_lesson_complete(db, current_user.id, lesson_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/api/lessons/{lesson_id}")
def api_get_lesson(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    is_completed = db.query(LessonProgress).filter(
        LessonProgress.user_id == current_user.id,
        LessonProgress.lesson_id == lesson_id,
        LessonProgress.completed == True
    ).first() is not None

    return {
        "id": lesson.id,
        "module_id": lesson.module_id,
        "title": lesson.title,
        "content": lesson.content,
        "video_url": lesson.video_url,
        "resource_url": lesson.resource_url,
        "duration": lesson.duration,
        "topic": lesson.topic or "General",
        "order": lesson.order,
        "completed": is_completed
    }
