from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.course import Course
from app.models.lesson import Module, Lesson
from app.models.progress import Enrollment, LessonProgress
from app.models.assessment import Assessment, AssessmentResult
from app.models.user import User

def is_user_enrolled(db: Session, user_id: int, course_id: int) -> bool:
    return db.query(Enrollment).filter(
        Enrollment.user_id == user_id,
        Enrollment.course_id == course_id
    ).first() is not None

def get_user_enrollment(db: Session, user_id: int, course_id: int) -> Optional[Enrollment]:
    return db.query(Enrollment).filter(
        Enrollment.user_id == user_id,
        Enrollment.course_id == course_id
    ).first()

def enroll_user(db: Session, user_id: int, course_id: int) -> Enrollment:
    existing = get_user_enrollment(db, user_id, course_id)
    if existing:
        return existing

    enrollment = Enrollment(
        user_id=user_id,
        course_id=course_id,
        progress=0.0
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment

def calculate_course_progress(db: Session, user_id: int, course_id: int) -> float:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        return 0.0

    all_lesson_ids = []
    for module in course.modules:
        for lesson in module.lessons:
            all_lesson_ids.append(lesson.id)

    total_lessons = len(all_lesson_ids)
    if total_lessons == 0:
        return 0.0

    completed_count = db.query(LessonProgress).filter(
        LessonProgress.user_id == user_id,
        LessonProgress.lesson_id.in_(all_lesson_ids),
        LessonProgress.completed == True
    ).count()

    progress = round((completed_count / total_lessons) * 100, 1)
    
    # Update enrollment record
    enrollment = get_user_enrollment(db, user_id, course_id)
    if enrollment:
        enrollment.progress = progress
        if progress >= 100.0 and not enrollment.completed_at:
            enrollment.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(enrollment)

    return progress

def mark_lesson_complete(db: Session, user_id: int, lesson_id: int) -> Dict[str, Any]:
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise ValueError("Lesson not found")

    course_id = lesson.module.course_id
    
    # Ensure enrollment exists
    enrollment = get_user_enrollment(db, user_id, course_id)
    if not enrollment:
        enrollment = enroll_user(db, user_id, course_id)

    # Record lesson progress
    progress_rec = db.query(LessonProgress).filter(
        LessonProgress.user_id == user_id,
        LessonProgress.lesson_id == lesson_id
    ).first()

    if not progress_rec:
        progress_rec = LessonProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            completed=True,
            completed_at=datetime.utcnow()
        )
        db.add(progress_rec)
    else:
        progress_rec.completed = True
        progress_rec.completed_at = datetime.utcnow()

    db.commit()

    # Recalculate progress
    new_progress = calculate_course_progress(db, user_id, course_id)

    # Find next lesson if available
    course = db.query(Course).filter(Course.id == course_id).first()
    all_lessons = []
    for m in course.modules:
        for l in m.lessons:
            all_lessons.append(l)

    next_lesson_id = None
    for i, l in enumerate(all_lessons):
        if l.id == lesson_id and i + 1 < len(all_lessons):
            next_lesson_id = all_lessons[i + 1].id
            break

    return {
        "status": "success",
        "lesson_id": lesson_id,
        "completed": True,
        "course_progress": new_progress,
        "next_lesson_id": next_lesson_id
    }

def get_student_dashboard_data(db: Session, user_id: int) -> Dict[str, Any]:
    # 1. Enrolled courses
    enrollments = db.query(Enrollment).filter(Enrollment.user_id == user_id).all()
    enrolled_count = len(enrollments)
    completed_courses_count = sum(1 for e in enrollments if e.progress >= 100.0)

    # 2. Completed lessons count
    completed_lessons_count = db.query(LessonProgress).filter(
        LessonProgress.user_id == user_id,
        LessonProgress.completed == True
    ).count()

    # 3. Assessment results
    results = db.query(AssessmentResult).filter(
        AssessmentResult.user_id == user_id
    ).order_by(AssessmentResult.completed_at.desc()).all()

    avg_score = 0.0
    if results:
        avg_score = round(sum(r.percentage for r in results) / len(results), 1)

    # 4. Active courses list with next lesson
    active_courses = []
    for enr in enrollments:
        course = enr.course
        # Find next uncompleted lesson
        next_lesson = None
        first_lesson = None
        for m in course.modules:
            for l in m.lessons:
                if not first_lesson:
                    first_lesson = l
                # check if completed
                is_done = db.query(LessonProgress).filter(
                    LessonProgress.user_id == user_id,
                    LessonProgress.lesson_id == l.id,
                    LessonProgress.completed == True
                ).first()
                if not is_done and not next_lesson:
                    next_lesson = l

        active_courses.append({
            "course": course,
            "enrollment": enr,
            "next_lesson": next_lesson or first_lesson,
            "progress": enr.progress
        })

    # Sort active courses by recent enrollment or uncompleted first
    active_courses.sort(key=lambda x: (x["progress"] >= 100.0, -x["enrollment"].enrolled_at.timestamp()))

    # 5. Recent activities
    recent_activities = []
    # Latest completed lessons
    recent_lessons = db.query(LessonProgress).filter(
        LessonProgress.user_id == user_id,
        LessonProgress.completed == True
    ).order_by(LessonProgress.completed_at.desc()).limit(3).all()

    for lp in recent_lessons:
        if lp.completed_at:
            recent_activities.append({
                "type": "lesson_completed",
                "title": f"Completed lesson '{lp.lesson.title}'",
                "course": lp.lesson.module.course.title,
                "timestamp": lp.completed_at,
                "icon": "fa-check-circle",
                "color": "emerald"
            })

    # Latest assessment results
    for res in results[:3]:
        recent_activities.append({
            "type": "assessment",
            "title": f"Scored {res.percentage}% in '{res.assessment.title}'",
            "course": res.assessment.course.title,
            "timestamp": res.completed_at,
            "icon": "fa-award",
            "color": "indigo" if res.passed else "amber"
        })

    # Sort recent activities by timestamp
    recent_activities.sort(key=lambda x: x["timestamp"], reverse=True)
    recent_activities = recent_activities[:6]

    # 6. Chart data (scores over time)
    chart_labels = []
    chart_scores = []
    # reverse order for chronological display
    for res in reversed(results[:10]):
        chart_labels.append(res.completed_at.strftime("%b %d"))
        chart_scores.append(res.percentage)

    if not chart_labels:
        # Default placeholder trend for empty states
        chart_labels = ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5"]
        chart_scores = [0, 0, 0, 0, 0]

    return {
        "enrolled_count": enrolled_count,
        "completed_courses_count": completed_courses_count,
        "completed_lessons_count": completed_lessons_count,
        "avg_score": avg_score,
        "active_courses": active_courses,
        "recent_activities": recent_activities,
        "chart_labels": chart_labels,
        "chart_scores": chart_scores,
    }

def get_student_detailed_progress(db: Session, user_id: int) -> Dict[str, Any]:
    enrollments = db.query(Enrollment).filter(Enrollment.user_id == user_id).all()
    courses_data = []
    total_lessons_overall = 0
    completed_lessons_overall = 0

    for enr in enrollments:
        course = enr.course
        all_lessons = []
        for m in course.modules:
            for l in m.lessons:
                all_lessons.append(l)

        c_total = len(all_lessons)
        c_completed = db.query(LessonProgress).filter(
            LessonProgress.user_id == user_id,
            LessonProgress.lesson_id.in_([l.id for l in all_lessons]),
            LessonProgress.completed == True
        ).count() if c_total > 0 else 0

        total_lessons_overall += c_total
        completed_lessons_overall += c_completed

        courses_data.append({
            "course": course,
            "progress": enr.progress,
            "completed_lessons": c_completed,
            "total_lessons": c_total,
            "enrolled_at": enr.enrolled_at,
            "completed_at": enr.completed_at
        })

    overall_percent = 0.0
    if total_lessons_overall > 0:
        overall_percent = round((completed_lessons_overall / total_lessons_overall) * 100, 1)

    # Learning streak calculation (consecutive days with completed lessons or assessments)
    activity_dates = set()
    lps = db.query(LessonProgress.completed_at).filter(
        LessonProgress.user_id == user_id,
        LessonProgress.completed == True
    ).all()
    for lp in lps:
        if lp[0]:
            activity_dates.add(lp[0].date())

    results = db.query(AssessmentResult.completed_at).filter(
        AssessmentResult.user_id == user_id
    ).all()
    for r in results:
        if r[0]:
            activity_dates.add(r[0].date())

    streak = 0
    today = datetime.utcnow().date()
    check_date = today
    if check_date not in activity_dates:
        check_date = today - timedelta(days=1)
    
    while check_date in activity_dates:
        streak += 1
        check_date -= timedelta(days=1)

    if streak == 0 and activity_dates:
        streak = 1  # Recent activity

    # All assessment results
    all_results = db.query(AssessmentResult).filter(
        AssessmentResult.user_id == user_id
    ).order_by(AssessmentResult.completed_at.desc()).all()

    avg_score = 0.0
    if all_results:
        avg_score = round(sum(r.percentage for r in all_results) / len(all_results), 1)

    # Learning Context & Topic Breakdown
    learning_context = get_student_learning_context(db, user_id)

    return {
        "overall_percent": overall_percent,
        "courses_data": courses_data,
        "total_lessons_overall": total_lessons_overall,
        "completed_lessons_overall": completed_lessons_overall,
        "streak": max(streak, 1) if (completed_lessons_overall > 0 or all_results) else 0,
        "avg_score": avg_score,
        "all_results": all_results,
        "learning_context": learning_context.get("records", []),
        "topic_summary": learning_context.get("topic_summary", []),
        "struggling_topics": learning_context.get("struggling_topics", []),
    }


def get_student_learning_context(db: Session, user_id: int) -> Dict[str, Any]:
    """Collects comprehensive student-learning context:
    Student ID + Course + Topic/Skill + Difficulty + Quiz Score + Progress + Preferred Resource Type.
    Identifies topics the student is currently learning or struggling with.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"records": [], "topic_summary": [], "struggling_topics": []}

    pref_type = user.preferred_resource_type or "Mixed"
    enrollments = db.query(Enrollment).filter(Enrollment.user_id == user_id).all()

    records = []
    topic_data: Dict[str, Dict[str, Any]] = {}
    struggling_topics = []

    # Map all assessment results by assessment_id
    all_results = db.query(AssessmentResult).filter(
        AssessmentResult.user_id == user_id
    ).order_by(AssessmentResult.completed_at.desc()).all()

    results_by_assessment: Dict[int, List[AssessmentResult]] = {}
    for r in all_results:
        results_by_assessment.setdefault(r.assessment_id, []).append(r)

    # Completed lesson ids
    completed_lesson_ids = set(
        r[0] for r in db.query(LessonProgress.lesson_id).filter(
            LessonProgress.user_id == user_id,
            LessonProgress.completed == True
        ).all()
    )

    for enr in enrollments:
        course = enr.course
        course_diff = course.difficulty or "Beginner"
        course_prog = enr.progress

        # Track topics in this course from lessons
        for mod in course.modules:
            for les in mod.lessons:
                t_name = les.topic.strip() if les.topic else "General"
                key = f"{course.id}_{t_name}"
                if key not in topic_data:
                    topic_data[key] = {
                        "course_id": course.id,
                        "course_title": course.title,
                        "difficulty": course_diff,
                        "progress": course_prog,
                        "topic": t_name,
                        "total_lessons": 0,
                        "completed_lessons": 0,
                        "quiz_scores": [],
                        "passed_flags": [],
                    }
                topic_data[key]["total_lessons"] += 1
                if les.id in completed_lesson_ids:
                    topic_data[key]["completed_lessons"] += 1

        # Track assessments and build discrete student-learning context records
        for asm in course.assessments:
            t_name = asm.topic.strip() if asm.topic else "General"
            key = f"{course.id}_{t_name}"
            if key not in topic_data:
                topic_data[key] = {
                    "course_id": course.id,
                    "course_title": course.title,
                    "difficulty": course_diff,
                    "progress": course_prog,
                    "topic": t_name,
                    "total_lessons": 0,
                    "completed_lessons": 0,
                    "quiz_scores": [],
                    "passed_flags": [],
                }

            asm_results = results_by_assessment.get(asm.id, [])
            for res in asm_results:
                topic_data[key]["quiz_scores"].append(res.percentage)
                topic_data[key]["passed_flags"].append(res.passed)

                # Discrete 7-tuple learning context record
                records.append({
                    "student_id": user.id,
                    "student_name": user.name,
                    "course": course.title,
                    "course_id": course.id,
                    "topic_skill": t_name,
                    "difficulty": course_diff,
                    "quiz_score": res.percentage,
                    "score_raw": f"{res.score}/{res.total_questions}",
                    "passed": res.passed,
                    "progress": course_prog,
                    "preferred_resource_type": pref_type,
                    "completed_at": res.completed_at.strftime("%Y-%m-%d %H:%M:%S") if res.completed_at else None,
                    "status": "Mastered" if res.passed else "Struggling",
                })

    # Build topic summaries and struggling topics list
    topic_summary = []
    for key, data in topic_data.items():
        scores = data["quiz_scores"]
        latest_score = scores[0] if scores else None
        avg_score = round(sum(scores) / len(scores), 1) if scores else None
        has_failed = any(not p for p in data["passed_flags"])
        all_passed = bool(data["passed_flags"] and all(data["passed_flags"]))

        if scores and (latest_score < 70.0 or has_failed):
            status = "Struggling"
            if data["topic"] not in struggling_topics:
                struggling_topics.append(data["topic"])
        elif all_passed:
            status = "Mastered"
        elif data["completed_lessons"] > 0:
            status = "Learning"
        else:
            status = "Not Started"

        topic_summary.append({
            "course_id": data["course_id"],
            "course_title": data["course_title"],
            "topic": data["topic"],
            "difficulty": data["difficulty"],
            "progress": data["progress"],
            "preferred_resource_type": pref_type,
            "completed_lessons": data["completed_lessons"],
            "total_lessons": data["total_lessons"],
            "latest_score": latest_score,
            "avg_score": avg_score,
            "status": status,
            "is_struggling": (status == "Struggling"),
        })

        # If no quiz was taken yet for this topic but user is enrolled, also create a baseline context entry
        if not scores and data["completed_lessons"] > 0:
            records.append({
                "student_id": user.id,
                "student_name": user.name,
                "course": data["course_title"],
                "course_id": data["course_id"],
                "topic_skill": data["topic"],
                "difficulty": data["difficulty"],
                "quiz_score": None,
                "score_raw": "In Progress",
                "passed": None,
                "progress": data["progress"],
                "preferred_resource_type": pref_type,
                "completed_at": None,
                "status": "Learning",
            })

    return {
        "student_id": user.id,
        "student_name": user.name,
        "preferred_resource_type": pref_type,
        "records": records,
        "topic_summary": topic_summary,
        "struggling_topics": struggling_topics,
    }
