import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.progress import Enrollment, LessonProgress
from app.models.assessment import AssessmentResult
from app.models.user import User
from app.templating import render_template
from app.services.auth_service import get_current_user, get_current_user_optional, verify_password, get_password_hash
from app.services.progress_service import (
    get_student_dashboard_data,
    get_student_detailed_progress,
    get_student_learning_context,
    calculate_course_progress
)
from app.schemas.user import UserUpdate, UserResponse

router = APIRouter(tags=["Progress & Student Dashboard"])

@router.get("/dashboard", response_class=HTMLResponse)
def student_dashboard_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db=db)
    if not user:
        return RedirectResponse(url="/login?next=/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    if user.role == "admin":
        return RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_303_SEE_OTHER)

    dash_data = get_student_dashboard_data(db, user.id)

    return render_template(
        request,
        "dashboard.html",
        {
            "user": user,
            "stats": {
                "enrolled_count": dash_data["enrolled_count"],
                "completed_courses_count": dash_data["completed_courses_count"],
                "completed_lessons_count": dash_data["completed_lessons_count"],
                "avg_score": dash_data["avg_score"]
            },
            "active_courses": dash_data["active_courses"],
            "recent_activities": dash_data["recent_activities"],
            "chart_labels_json": json.dumps(dash_data["chart_labels"]),
            "chart_scores_json": json.dumps(dash_data["chart_scores"]),
        }
    )

@router.get("/progress", response_class=HTMLResponse)
def student_progress_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db=db)
    if not user:
        return RedirectResponse(url="/login?next=/progress", status_code=status.HTTP_303_SEE_OTHER)

    prog_data = get_student_detailed_progress(db, user.id)

    # Prepare chart dates and percentages
    chart_dates = []
    chart_percentages = []
    for r in reversed(prog_data["all_results"][:12]):
        chart_dates.append(r.completed_at.strftime("%b %d"))
        chart_percentages.append(r.percentage)

    if not chart_dates:
        chart_dates = ["Module 1", "Module 2", "Module 3", "Final Exam"]
        chart_percentages = [0, 0, 0, 0]

    lessons_remaining = max(0, prog_data["total_lessons_overall"] - prog_data["completed_lessons_overall"])

    return render_template(
        request,
        "progress.html",
        {
            "user": user,
            "overall_percent": prog_data["overall_percent"],
            "courses_data": prog_data["courses_data"],
            "completed_lessons": prog_data["completed_lessons_overall"],
            "lessons_remaining": lessons_remaining,
            "total_lessons": prog_data["total_lessons_overall"],
            "streak": prog_data["streak"],
            "avg_score": prog_data["avg_score"],
            "all_results": prog_data["all_results"],
            "topic_summary": prog_data.get("topic_summary", []),
            "learning_context": prog_data.get("learning_context", []),
            "struggling_topics": prog_data.get("struggling_topics", []),
            "chart_dates_json": json.dumps(chart_dates),
            "chart_percentages_json": json.dumps(chart_percentages),
        }
    )

@router.get("/profile", response_class=HTMLResponse)
def student_profile_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db=db)
    if not user:
        return RedirectResponse(url="/login?next=/profile", status_code=status.HTTP_303_SEE_OTHER)

    enrollments_count = db.query(Enrollment).filter(Enrollment.user_id == user.id).count()
    completed_count = db.query(Enrollment).filter(
        Enrollment.user_id == user.id,
        Enrollment.progress >= 100.0
    ).count()

    results = db.query(AssessmentResult).filter(AssessmentResult.user_id == user.id).all()
    avg_score = round(sum(r.percentage for r in results) / len(results), 1) if results else 0.0

    return render_template(
        request,
        "profile.html",
        {
            "user": user,
            "enrollments_count": enrollments_count,
            "completed_count": completed_count,
            "avg_score": avg_score,
            "success_msg": None,
            "error_msg": None
        }
    )

@router.post("/profile/update")
def student_profile_update(
    request: Request,
    name: str = Form(...),
    bio: str = Form(""),
    preferred_resource_type: str = Form("Mixed"),
    old_password: str = Form(""),
    new_password: str = Form(""),
    db: Session = Depends(get_db)
):
    user = get_current_user_optional(request, db=db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    user.name = name.strip()
    user.bio = bio.strip()

    # Preferred Resource Type update
    valid_preferences = ["Video", "Article", "Practice", "Mixed"]
    clean_pref = preferred_resource_type.strip().capitalize()
    if clean_pref in valid_preferences:
        user.preferred_resource_type = clean_pref
    else:
        user.preferred_resource_type = "Mixed"

    # Password update if requested
    error_msg = None
    success_msg = "Profile updated successfully."

    if new_password.strip():
        if not old_password.strip():
            error_msg = "Current password is required to set a new password."
        elif not verify_password(old_password, user.password_hash):
            error_msg = "Current password was incorrect."
        elif len(new_password) < 6:
            error_msg = "New password must be at least 6 characters."
        else:
            user.password_hash = get_password_hash(new_password)
            success_msg = "Profile and password updated successfully."

    if not error_msg:
        db.commit()
        db.refresh(user)

    enrollments_count = db.query(Enrollment).filter(Enrollment.user_id == user.id).count()
    completed_count = db.query(Enrollment).filter(
        Enrollment.user_id == user.id,
        Enrollment.progress >= 100.0
    ).count()
    results = db.query(AssessmentResult).filter(AssessmentResult.user_id == user.id).all()
    avg_score = round(sum(r.percentage for r in results) / len(results), 1) if results else 0.0

    return render_template(
        request,
        "profile.html",
        {
            "user": user,
            "enrollments_count": enrollments_count,
            "completed_count": completed_count,
            "avg_score": avg_score,
            "success_msg": success_msg if not error_msg else None,
            "error_msg": error_msg
        }
    )

# ----------------- REST API Endpoints -----------------

@router.get("/api/progress")
def api_get_progress_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_student_dashboard_data(db, current_user.id)

@router.get("/api/progress/learning-context")
def api_get_student_learning_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns student-learning context:
    Student ID + Course + Topic/Skill + Difficulty + Quiz Score + Progress + Preferred Resource Type.
    """
    return get_student_learning_context(db, current_user.id)

@router.get("/api/students/{user_id}/learning-context")
def api_get_specific_student_learning_context(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Admin or student themselves can view learning context."""
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return get_student_learning_context(db, user_id)

@router.patch("/api/users/preferences", response_model=UserResponse)
@router.put("/api/users/profile", response_model=UserResponse)
def api_update_user_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.name:
        current_user.name = data.name.strip()
    if data.bio is not None:
        current_user.bio = data.bio.strip()
    if data.preferred_resource_type is not None:
        valid_preferences = ["Video", "Article", "Practice", "Mixed"]
        clean_pref = data.preferred_resource_type.strip().capitalize()
        if clean_pref in valid_preferences:
            current_user.preferred_resource_type = clean_pref
        else:
            raise HTTPException(status_code=400, detail="Invalid preference. Options: Video, Article, Practice, Mixed")

    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/api/courses/{course_id}/progress")
def api_get_course_progress(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    enrollment = db.query(Enrollment).filter(
        Enrollment.user_id == current_user.id,
        Enrollment.course_id == course_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Not enrolled in this course")

    return {
        "course_id": course_id,
        "progress": enrollment.progress,
        "enrolled_at": enrollment.enrolled_at,
        "completed_at": enrollment.completed_at
    }
