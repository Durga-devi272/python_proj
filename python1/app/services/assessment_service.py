import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.assessment import Assessment, Question, AssessmentResult

def get_assessment_by_id(db: Session, assessment_id: int) -> Optional[Assessment]:
    return db.query(Assessment).filter(Assessment.id == assessment_id).first()

def evaluate_assessment(
    db: Session,
    user_id: int,
    assessment_id: int,
    user_answers: Dict[str, str] # e.g. {"1": "A", "2": "C"}
) -> Dict[str, Any]:
    assessment = get_assessment_by_id(db, assessment_id)
    if not assessment:
        raise ValueError("Assessment not found")

    questions = assessment.questions
    total_questions = len(questions)
    if total_questions == 0:
        raise ValueError("Assessment has no questions")

    correct_count = 0
    question_reviews = []

    for q in questions:
        # Key could be str(q.id) or int(q.id)
        selected_option = user_answers.get(str(q.id), "").strip().upper()
        correct_option = q.correct_option.strip().upper()
        is_correct = (selected_option == correct_option)

        if is_correct:
            correct_count += 1

        question_reviews.append({
            "question_id": q.id,
            "question_text": q.question_text,
            "option_a": q.option_a,
            "option_b": q.option_b,
            "option_c": q.option_c,
            "option_d": q.option_d,
            "selected_option": selected_option,
            "correct_option": correct_option,
            "is_correct": is_correct,
            "explanation": q.explanation
        })

    incorrect_count = total_questions - correct_count
    percentage = round((correct_count / total_questions) * 100, 1)
    passed = percentage >= assessment.pass_percentage

    # Record result in database
    result = AssessmentResult(
        user_id=user_id,
        assessment_id=assessment_id,
        score=correct_count,
        total_questions=total_questions,
        percentage=percentage,
        passed=passed,
        answers_json=json.dumps(user_answers),
        completed_at=datetime.utcnow()
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    return {
        "result_id": result.id,
        "assessment_id": assessment.id,
        "assessment_title": assessment.title,
        "course_id": assessment.course_id,
        "course_title": assessment.course.title,
        "topic": assessment.topic or "General",
        "score": correct_count,
        "incorrect": incorrect_count,
        "total_questions": total_questions,
        "percentage": percentage,
        "pass_percentage": assessment.pass_percentage,
        "passed": passed,
        "question_reviews": question_reviews,
        "completed_at": result.completed_at
    }

def get_assessment_result(db: Session, result_id: int) -> Optional[AssessmentResult]:
    return db.query(AssessmentResult).filter(AssessmentResult.id == result_id).first()
