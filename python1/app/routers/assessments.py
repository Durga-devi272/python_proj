import json
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.course import Course
from app.models.assessment import Assessment, Question, AssessmentResult
from app.models.user import User
from app.schemas.assessment import AssessmentSubmit
from app.templating import render_template
from app.services.auth_service import get_current_user, get_current_user_optional
from app.services.assessment_service import evaluate_assessment, get_assessment_by_id, get_assessment_result
from app.services.progress_service import is_user_enrolled, enroll_user

router = APIRouter(tags=["Assessments"])

# ----------------- HTML Views -----------------

@router.get("/courses/{course_id}/assessments/{assessment_id}", response_class=HTMLResponse)
def take_assessment_page(
    course_id: int,
    assessment_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user_optional(request, db=db)
    if not user:
        return RedirectResponse(
            url=f"/login?next=/courses/{course_id}/assessments/{assessment_id}",
            status_code=status.HTTP_303_SEE_OTHER
        )

    assessment = get_assessment_by_id(db, assessment_id)
    if not assessment or assessment.course_id != course_id:
        raise HTTPException(status_code=404, detail="Assessment not found for this course")

    # Auto enroll if not enrolled
    if not is_user_enrolled(db, user.id, course_id):
        enroll_user(db, user.id, course_id)

    # Previous attempts count
    past_results = db.query(AssessmentResult).filter(
        AssessmentResult.user_id == user.id,
        AssessmentResult.assessment_id == assessment_id
    ).order_by(AssessmentResult.completed_at.desc()).all()

    return render_template(
        request,
        "assessment.html",
        {
            "user": user,
            "course": assessment.course,
            "assessment": assessment,
            "questions": assessment.questions,
            "past_results": past_results
        }
    )

@router.post("/courses/{course_id}/assessments/{assessment_id}/submit")
async def submit_assessment_form(
    course_id: int,
    assessment_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user_optional(request, db=db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    form_data = await request.form()
    # Collect answers: keys like "q_{question_id}"
    answers = {}
    for key, val in form_data.items():
        if key.startswith("q_"):
            q_id = key.split("_")[1]
            answers[q_id] = str(val).strip().upper()

    try:
        eval_result = evaluate_assessment(db, user.id, assessment_id, answers)
        return RedirectResponse(
            url=f"/assessments/results/{eval_result['result_id']}",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/assessments/results/{result_id}", response_class=HTMLResponse)
def view_assessment_result(
    result_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user_optional(request, db=db)
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    result = get_assessment_result(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    # Authorize: only owner or admin can view
    if result.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")

    assessment = result.assessment
    course = assessment.course

    # Parse saved answers
    answers_map = {}
    if result.answers_json:
        try:
            answers_map = json.loads(result.answers_json)
        except Exception:
            answers_map = {}

    # Build question reviews
    question_reviews = []
    for q in assessment.questions:
        user_choice = answers_map.get(str(q.id), "").strip().upper()
        correct_choice = q.correct_option.strip().upper()
        is_correct = (user_choice == correct_choice)
        question_reviews.append({
            "question": q,
            "user_choice": user_choice,
            "correct_choice": correct_choice,
            "is_correct": is_correct,
            "explanation": q.explanation
        })

    # Performance tier
    if result.percentage >= 90:
        perf_tier = "Outstanding Master"
        badge_color = "emerald"
    elif result.percentage >= 70:
        perf_tier = "Proficient & Passed"
        badge_color = "indigo"
    elif result.percentage >= 50:
        perf_tier = "Needs Review"
        badge_color = "amber"
    else:
        perf_tier = "Requires Practice"
        badge_color = "rose"

    return render_template(
        request,
        "result.html",
        {
            "user": user,
            "result": result,
            "assessment": assessment,
            "course": course,
            "question_reviews": question_reviews,
            "perf_tier": perf_tier,
            "badge_color": badge_color,
            "incorrect_count": result.total_questions - result.score
        }
    )

# ----------------- REST API Endpoints -----------------

@router.get("/api/assessments/{assessment_id}")
def api_get_assessment(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    assessment = get_assessment_by_id(db, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    questions_data = []
    for q in assessment.questions:
        questions_data.append({
            "id": q.id,
            "question_text": q.question_text,
            "option_a": q.option_a,
            "option_b": q.option_b,
            "option_c": q.option_c,
            "option_d": q.option_d,
            # hide correct_option for students
            "explanation": q.explanation if current_user.role == "admin" else None
        })

    return {
        "id": assessment.id,
        "course_id": assessment.course_id,
        "course_title": assessment.course.title,
        "title": assessment.title,
        "topic": assessment.topic or "General",
        "description": assessment.description,
        "pass_percentage": assessment.pass_percentage,
        "questions": questions_data
    }

@router.post("/api/assessments/{assessment_id}/submit")
def api_submit_assessment(
    assessment_id: int,
    submit_data: AssessmentSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        eval_result = evaluate_assessment(db, current_user.id, assessment_id, submit_data.answers)
        return eval_result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
