import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.course import Course
from app.models.lesson import Module, Lesson
from app.models.assessment import Assessment, Question, AssessmentResult
from app.models.progress import Enrollment, LessonProgress
from app.models.user import User
from app.templating import render_template
from app.services.auth_service import get_current_user_optional, get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

def verify_admin_web(request: Request, db: Session) -> Optional[User]:
    user = get_current_user_optional(request, db=db)
    if not user or user.role != "admin":
        return None
    return user

# ----------------- Admin Dashboard -----------------

@router.get("", response_class=HTMLResponse)
@router.get("/dashboard", response_class=HTMLResponse)
def admin_dashboard_page(request: Request, db: Session = Depends(get_db)):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login?next=/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    total_students = db.query(User).filter(User.role == "student").count()
    total_courses = db.query(Course).count()
    total_enrollments = db.query(Enrollment).count()
    total_lessons = db.query(Lesson).count()

    # Average course completion
    avg_completion = db.query(func.avg(Enrollment.progress)).scalar() or 0.0
    avg_completion = round(avg_completion, 1)

    # Average assessment score
    avg_score = db.query(func.avg(AssessmentResult.percentage)).scalar() or 0.0
    avg_score = round(avg_score, 1)

    # Enrollment trends / monthly data
    trend_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"]
    trend_counts = [12, 19, 28, 45, 62, 85, 110, 140, 195, max(total_enrollments, 240)]

    # Course popularity (top courses by enrollment)
    courses = db.query(Course).all()
    courses_popularity = []
    for c in courses:
        courses_popularity.append({
            "title": c.title,
            "enrollments": len(c.enrollments)
        })
    courses_popularity.sort(key=lambda x: x["enrollments"], reverse=True)
    pop_labels = [c["title"][:15] + "..." if len(c["title"]) > 15 else c["title"] for c in courses_popularity[:5]]
    pop_data = [c["enrollments"] for c in courses_popularity[:5]]

    # Recent student signups
    recent_students = db.query(User).filter(User.role == "student").order_by(User.created_at.desc()).limit(5).all()

    # Recent assessments
    recent_results = db.query(AssessmentResult).order_by(AssessmentResult.completed_at.desc()).limit(5).all()

    return render_template(
        request,
        "admin/dashboard.html",
        {
            "user": admin_user,
            "stats": {
                "total_students": total_students,
                "total_courses": total_courses,
                "total_enrollments": total_enrollments,
                "total_lessons": total_lessons,
                "avg_completion": avg_completion,
                "avg_score": avg_score
            },
            "recent_students": recent_students,
            "recent_results": recent_results,
            "trend_labels_json": json.dumps(trend_labels),
            "trend_counts_json": json.dumps(trend_counts),
            "pop_labels_json": json.dumps(pop_labels),
            "pop_data_json": json.dumps(pop_data),
        }
    )

# ----------------- Course Management -----------------

@router.get("/courses", response_class=HTMLResponse)
def admin_courses_list(request: Request, db: Session = Depends(get_db)):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    courses = db.query(Course).order_by(Course.created_at.desc()).all()
    course_items = []
    for c in courses:
        modules_count = len(c.modules)
        lessons_count = sum(len(m.lessons) for m in c.modules)
        students_count = len(c.enrollments)
        course_items.append({
            "course": c,
            "modules_count": modules_count,
            "lessons_count": lessons_count,
            "students_count": students_count
        })

    return render_template(
        request,
        "admin/courses.html",
        {"user": admin_user, "courses": course_items}
    )

@router.get("/courses/new", response_class=HTMLResponse)
def admin_course_new_page(request: Request, db: Session = Depends(get_db)):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    return render_template(
        request,
        "admin/course_form.html",
        {"user": admin_user, "course": None, "is_edit": False}
    )

@router.post("/courses/new")
def admin_course_create(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    difficulty: str = Form(...),
    duration: str = Form("6 hours"),
    instructor: str = Form(...),
    thumbnail: str = Form(""),
    learning_objectives: str = Form(""),
    published: bool = Form(False),
    db: Session = Depends(get_db)
):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    course = Course(
        title=title.strip(),
        description=description.strip(),
        category=category.strip(),
        difficulty=difficulty.strip(),
        duration=duration.strip(),
        instructor=instructor.strip(),
        thumbnail=thumbnail.strip() or "/static/images/course-default.jpg",
        learning_objectives=learning_objectives.strip(),
        published=published
    )
    db.add(course)
    db.commit()
    db.refresh(course)

    return RedirectResponse(url=f"/admin/courses/{course.id}/curriculum", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/courses/{course_id}/edit", response_class=HTMLResponse)
def admin_course_edit_page(course_id: int, request: Request, db: Session = Depends(get_db)):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return render_template(
        request,
        "admin/course_form.html",
        {"user": admin_user, "course": course, "is_edit": True}
    )

@router.post("/courses/{course_id}/edit")
def admin_course_update(
    course_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    difficulty: str = Form(...),
    duration: str = Form(...),
    instructor: str = Form(...),
    thumbnail: str = Form(""),
    learning_objectives: str = Form(""),
    published: bool = Form(False),
    db: Session = Depends(get_db)
):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    course.title = title.strip()
    course.description = description.strip()
    course.category = category.strip()
    course.difficulty = difficulty.strip()
    course.duration = duration.strip()
    course.instructor = instructor.strip()
    if thumbnail.strip():
        course.thumbnail = thumbnail.strip()
    course.learning_objectives = learning_objectives.strip()
    course.published = published

    db.commit()
    return RedirectResponse(url="/admin/courses", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/courses/{course_id}/delete")
def admin_course_delete(course_id: int, request: Request, db: Session = Depends(get_db)):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    course = db.query(Course).filter(Course.id == course_id).first()
    if course:
        db.delete(course)
        db.commit()

    return RedirectResponse(url="/admin/courses", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/courses/{course_id}/toggle-publish")
def admin_course_toggle_publish(course_id: int, request: Request, db: Session = Depends(get_db)):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    course = db.query(Course).filter(Course.id == course_id).first()
    if course:
        course.published = not course.published
        db.commit()

    return RedirectResponse(url="/admin/courses", status_code=status.HTTP_303_SEE_OTHER)

# ----------------- Curriculum / Modules & Lessons -----------------

@router.get("/courses/{course_id}/curriculum", response_class=HTMLResponse)
def admin_curriculum_page(course_id: int, request: Request, db: Session = Depends(get_db)):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return render_template(
        request,
        "admin/modules_lessons.html",
        {"user": admin_user, "course": course}
    )

@router.post("/courses/{course_id}/modules/new")
def admin_module_create(
    course_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    order: int = Form(1),
    db: Session = Depends(get_db)
):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    mod = Module(
        course_id=course_id,
        title=title.strip(),
        description=description.strip(),
        order=order
    )
    db.add(mod)
    db.commit()

    return RedirectResponse(url=f"/admin/courses/{course_id}/curriculum", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/modules/{module_id}/delete")
def admin_module_delete(module_id: int, request: Request, db: Session = Depends(get_db)):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    mod = db.query(Module).filter(Module.id == module_id).first()
    if mod:
        c_id = mod.course_id
        db.delete(mod)
        db.commit()
        return RedirectResponse(url=f"/admin/courses/{c_id}/curriculum", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/admin/courses", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/modules/{module_id}/lessons/new")
def admin_lesson_create(
    module_id: int,
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    video_url: str = Form(""),
    resource_url: str = Form(""),
    duration: str = Form("15 mins"),
    topic: str = Form("General"),
    order: int = Form(1),
    db: Session = Depends(get_db)
):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    mod = db.query(Module).filter(Module.id == module_id).first()
    if not mod:
        raise HTTPException(status_code=404, detail="Module not found")

    lesson = Lesson(
        module_id=module_id,
        title=title.strip(),
        content=content.strip(),
        video_url=video_url.strip() or None,
        resource_url=resource_url.strip() or None,
        duration=duration.strip(),
        topic=topic.strip() if topic else "General",
        order=order
    )
    db.add(lesson)
    db.commit()

    return RedirectResponse(url=f"/admin/courses/{mod.course_id}/curriculum", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/lessons/{lesson_id}/edit")
def admin_lesson_update(
    lesson_id: int,
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    video_url: str = Form(""),
    resource_url: str = Form(""),
    duration: str = Form("15 mins"),
    topic: str = Form("General"),
    order: int = Form(1),
    db: Session = Depends(get_db)
):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    course_id = lesson.module.course_id
    lesson.title = title.strip()
    lesson.content = content.strip()
    lesson.video_url = video_url.strip() or None
    lesson.resource_url = resource_url.strip() or None
    lesson.duration = duration.strip()
    lesson.topic = topic.strip() if topic else "General"
    lesson.order = order

    db.commit()
    return RedirectResponse(url=f"/admin/courses/{course_id}/curriculum", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/lessons/{lesson_id}/delete")
def admin_lesson_delete(lesson_id: int, request: Request, db: Session = Depends(get_db)):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if lesson:
        c_id = lesson.module.course_id
        db.delete(lesson)
        db.commit()
        return RedirectResponse(url=f"/admin/courses/{c_id}/curriculum", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/admin/courses", status_code=status.HTTP_303_SEE_OTHER)

# ----------------- Assessment Management -----------------

@router.get("/assessments", response_class=HTMLResponse)
def admin_assessments_page(request: Request, db: Session = Depends(get_db)):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    assessments = db.query(Assessment).all()
    courses = db.query(Course).all()

    return render_template(
        request,
        "admin/assessments.html",
        {"user": admin_user, "assessments": assessments, "courses": courses}
    )

@router.post("/courses/{course_id}/assessments/new")
def admin_assessment_create(
    course_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    topic: str = Form("General"),
    pass_percentage: float = Form(70.0),
    db: Session = Depends(get_db)
):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    assessment = Assessment(
        course_id=course_id,
        title=title.strip(),
        description=description.strip(),
        topic=topic.strip() if topic else "General",
        pass_percentage=pass_percentage
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return RedirectResponse(url=f"/admin/assessments/{assessment.id}/questions", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/assessments/{assessment_id}/questions", response_class=HTMLResponse)
def admin_questions_page(assessment_id: int, request: Request, db: Session = Depends(get_db)):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    return render_template(
        request,
        "admin/questions.html",
        {"user": admin_user, "assessment": assessment}
    )

@router.post("/assessments/{assessment_id}/questions/new")
def admin_question_create(
    assessment_id: int,
    request: Request,
    question_text: str = Form(...),
    option_a: str = Form(...),
    option_b: str = Form(...),
    option_c: str = Form(...),
    option_d: str = Form(...),
    correct_option: str = Form(...),
    explanation: str = Form(""),
    db: Session = Depends(get_db)
):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    q = Question(
        assessment_id=assessment_id,
        question_text=question_text.strip(),
        option_a=option_a.strip(),
        option_b=option_b.strip(),
        option_c=option_c.strip(),
        option_d=option_d.strip(),
        correct_option=correct_option.strip().upper(),
        explanation=explanation.strip()
    )
    db.add(q)
    db.commit()

    return RedirectResponse(url=f"/admin/assessments/{assessment_id}/questions", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/questions/{question_id}/edit")
def admin_question_update(
    question_id: int,
    request: Request,
    question_text: str = Form(...),
    option_a: str = Form(...),
    option_b: str = Form(...),
    option_c: str = Form(...),
    option_d: str = Form(...),
    correct_option: str = Form(...),
    explanation: str = Form(""),
    db: Session = Depends(get_db)
):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    q.question_text = question_text.strip()
    q.option_a = option_a.strip()
    q.option_b = option_b.strip()
    q.option_c = option_c.strip()
    q.option_d = option_d.strip()
    q.correct_option = correct_option.strip().upper()
    q.explanation = explanation.strip()

    db.commit()
    return RedirectResponse(url=f"/admin/assessments/{q.assessment_id}/questions", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/questions/{question_id}/delete")
def admin_question_delete(question_id: int, request: Request, db: Session = Depends(get_db)):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    q = db.query(Question).filter(Question.id == question_id).first()
    if q:
        a_id = q.assessment_id
        db.delete(q)
        db.commit()
        return RedirectResponse(url=f"/admin/assessments/{a_id}/questions", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/admin/assessments", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/assessments/{assessment_id}/delete")
def admin_assessment_delete(assessment_id: int, request: Request, db: Session = Depends(get_db)):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if assessment:
        db.delete(assessment)
        db.commit()

    return RedirectResponse(url="/admin/assessments", status_code=status.HTTP_303_SEE_OTHER)

# ----------------- Student Management -----------------

@router.get("/students", response_class=HTMLResponse)
def admin_students_page(request: Request, db: Session = Depends(get_db)):
    admin_user = verify_admin_web(request, db)
    if not admin_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    students = db.query(User).filter(User.role == "student").order_by(User.created_at.desc()).all()
    students_data = []

    for s in students:
        enr_count = len(s.enrollments)
        completed_courses = sum(1 for e in s.enrollments if e.progress >= 100.0)
        avg_score = round(sum(r.percentage for r in s.assessment_results) / len(s.assessment_results), 1) if s.assessment_results else 0.0
        
        # Last activity
        last_act = s.created_at
        for r in s.assessment_results:
            if r.completed_at > last_act:
                last_act = r.completed_at
        for lp in s.lesson_progress:
            if lp.completed_at and lp.completed_at > last_act:
                last_act = lp.completed_at

        students_data.append({
            "user": s,
            "enr_count": enr_count,
            "completed_courses": completed_courses,
            "avg_score": avg_score,
            "preferred_resource_type": s.preferred_resource_type or "Mixed",
            "last_activity": last_act
        })

    return render_template(
        request,
        "admin/students.html",
        {"user": admin_user, "students": students_data}
    )
