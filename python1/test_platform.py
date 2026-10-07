import sys
import requests
from app.config import settings

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_tests():
    # Use FastAPI TestClient to test synchronously in memory without launching external background process
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    print("=" * 60)
    print("[*] Running EduPulse Platform Functional Verification Suite")
    print("=" * 60)

    # 1. Landing Page
    print("[1] Testing Public Landing Page (GET /)...")
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert "Learn. Practice." in res.text, "Hero section text missing"
    assert "Popular Courses" in res.text, "Popular courses section missing"
    print("    [PASS] Landing page renders properly.")

    # 2. Courses Marketplace
    print("[2] Testing Course Discovery (GET /courses)...")
    res = client.get("/courses")
    assert res.status_code == 200
    assert "Python Programming" in res.text
    assert "Data Structures" in res.text
    print("    [PASS] Course marketplace renders courses.")

    # 2b. Course Search & Filters
    print("[2b] Testing Course Search (GET /courses?q=Python)...")
    res = client.get("/courses?q=Python")
    assert res.status_code == 200
    assert "Python Programming" in res.text
    print("    [PASS] Search filters work correctly.")

    # 3. Course Details
    print("[3] Testing Course Details (GET /courses/1)...")
    res = client.get("/courses/1")
    assert res.status_code == 200
    assert "Course Curriculum" in res.text
    assert "Module 1" in res.text
    print("    [PASS] Course details and curriculum render properly.")

    # 4. Authentication API
    print("[4] Testing Student Login API (POST /api/auth/login)...")
    res = client.post("/api/auth/login", json={
        "email": "student@elearning.com",
        "password": "student123"
    })
    assert res.status_code == 200, f"Login failed: {res.text}"
    token_data = res.json()
    assert "access_token" in token_data
    assert token_data["user"]["role"] == "student"
    student_token = token_data["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}
    student_cookies = {"access_token": student_token}
    print("    [PASS] Student authentication successful.")

    # 4b. Invalid Login
    print("[4b] Testing Invalid Login Rejection...")
    res = client.post("/api/auth/login", json={
        "email": "student@elearning.com",
        "password": "wrongpassword"
    })
    assert res.status_code == 401
    print("    [PASS] Invalid password rejected with HTTP 401.")

    # 4c. Admin Login API
    print("[4c] Testing Admin Login API...")
    res = client.post("/api/auth/login", json={
        "email": "admin@elearning.com",
        "password": "admin123"
    })
    assert res.status_code == 200
    admin_token = res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    admin_cookies = {"access_token": admin_token}
    print("    [PASS] Admin authentication successful.")

    # 5. Protected Student Dashboard
    print("[5] Testing Student Dashboard (GET /dashboard)...")
    res = client.get("/dashboard", cookies=student_cookies)
    assert res.status_code == 200
    assert "Welcome back" in res.text
    assert "Enrolled Courses" in res.text
    print("    [PASS] Student dashboard loads with statistics.")

    # 6. Student Progress Analytics
    print("[6] Testing Student Progress Page (GET /progress)...")
    res = client.get("/progress", cookies=student_cookies)
    assert res.status_code == 200
    assert "Learning Progress" in res.text
    assert "Day Streak" in res.text
    print("    [PASS] Progress page renders with analytics.")

    # 7. Student Profile Page
    print("[7] Testing Student Profile (GET /profile)...")
    res = client.get("/profile", cookies=student_cookies)
    assert res.status_code == 200
    assert "Account Settings" in res.text
    print("    [PASS] Profile settings render properly.")

    # 8. Learning Room & Lesson Progression
    print("[8] Testing Lesson View & Completion API...")
    res = client.get("/courses/1/lessons/1", cookies=student_cookies)
    assert res.status_code == 200
    assert "Introduction to Python" in res.text

    # Mark Lesson Complete API
    res = client.post("/api/lessons/1/complete", headers=student_headers)
    assert res.status_code == 200
    comp_data = res.json()
    assert comp_data["completed"] is True
    assert "course_progress" in comp_data
    print(f"    [PASS] Lesson completed successfully (course progress: {comp_data['course_progress']}%).")

    # 9. Assessment Submission & Grading
    print("[9] Testing Assessment Submission (POST /api/assessments/1/submit)...")
    res = client.post("/api/assessments/1/submit", headers=student_headers, json={
        "answers": {
            "1": "B",  # Correct
            "2": "B",  # Correct
            "3": "A",  # Correct
            "4": "B",  # Correct
            "5": "B"   # Correct
        }
    })
    assert res.status_code == 200, f"Submit failed: {res.text}"
    eval_res = res.json()
    assert eval_res["score"] == 5
    assert eval_res["percentage"] == 100.0
    assert eval_res["passed"] is True
    print(f"    [PASS] Assessment graded: {eval_res['score']}/{eval_res['total_questions']} ({eval_res['percentage']}%, Passed: {eval_res['passed']}).")

    # 10. Result Review Page
    result_id = eval_res["result_id"]
    res = client.get(f"/assessments/results/{result_id}", cookies=student_cookies)
    assert res.status_code == 200
    assert "Assessment Completed" in res.text
    assert "100.0%" in res.text
    print("    [PASS] Result review page renders score and explanations.")

    # 11. Admin Protected Dashboard
    print("[11] Testing Admin Dashboard (GET /admin/dashboard)...")
    res = client.get("/admin/dashboard", cookies=admin_cookies)
    assert res.status_code == 200
    assert "Platform Analytics Overview" in res.text
    assert "Total Students" in res.text
    print("    [PASS] Admin dashboard loads with full management telemetry.")

    # 11b. Student Blocked from Admin
    print("[11b] Verifying Student is blocked from Admin Portal...")
    res = client.get("/admin/dashboard", cookies=student_cookies, follow_redirects=False)
    # Student should be redirected to login or denied
    assert res.status_code in [302, 303, 403]
    print("    [PASS] Role-based access control successfully blocks student from admin routes.")

    # 12. Admin Course Management
    print("[12] Testing Admin Course Management (GET /admin/courses)...")
    res = client.get("/admin/courses", cookies=admin_cookies)
    assert res.status_code == 200
    assert "Course Management" in res.text

    # 13. Admin Student Directory
    print("[13] Testing Admin Student Directory (GET /admin/students)...")
    res = client.get("/admin/students", cookies=admin_cookies)
    assert res.status_code == 200
    assert "Student Directory" in res.text
    assert "Demo Student" in res.text
    print("    [PASS] Admin student directory lists active learners.")

    # 14. Feature 1: Topic/Skill on Lessons & Assessments
    print("[14] Testing Topic/Skill integration on Lessons & Assessments...")
    # Check Lesson API
    res = client.get("/api/lessons/1", headers=student_headers)
    assert res.status_code == 200
    lesson_data = res.json()
    assert "topic" in lesson_data
    assert lesson_data["topic"] in ["Variables", "General", "Loops", "Functions", "OOP"]
    print(f"    [PASS] Lesson 1 has topic: '{lesson_data['topic']}'.")

    # Check Assessment API
    res = client.get("/api/assessments/1", headers=student_headers)
    assert res.status_code == 200
    asm_data = res.json()
    assert "topic" in asm_data
    assert asm_data["topic"] is not None
    print(f"    [PASS] Assessment 1 has topic: '{asm_data['topic']}'.")

    # Check Assessment Web View
    res = client.get("/courses/1/assessments/1", cookies=student_cookies)
    assert res.status_code == 200
    assert "Topic / Skill:" in res.text

    # 15. Feature 2: Preferred Resource Type on Student Profile
    print("[15] Testing Preferred Resource Type (Video, Article, Practice, Mixed)...")
    # Verify Profile HTML has preference selector
    res = client.get("/profile", cookies=student_cookies)
    assert res.status_code == 200
    assert "Preferred Learning Resource Type" in res.text
    assert "Video" in res.text and "Article" in res.text and "Practice" in res.text and "Mixed" in res.text

    # Update Preference via Form POST
    res = client.post("/profile/update", cookies=student_cookies, data={
        "name": "Demo Student",
        "bio": "Updated bio with video preference.",
        "preferred_resource_type": "Video",
        "old_password": "",
        "new_password": ""
    })
    assert res.status_code == 200
    assert "Profile updated successfully." in res.text

    # Verify user object reflected preference
    res = client.get("/api/auth/me", headers=student_headers)
    assert res.status_code == 200
    user_me = res.json()
    assert user_me["preferred_resource_type"] == "Video"
    print("    [PASS] Student preferred resource type successfully updated to 'Video'.")

    # Update Preference via REST API PATCH
    res = client.patch("/api/users/preferences", headers=student_headers, json={
        "preferred_resource_type": "Practice"
    })
    assert res.status_code == 200
    assert res.json()["preferred_resource_type"] == "Practice"
    print("    [PASS] REST API updated preference to 'Practice'.")

    # 16. Student Learning Context: 7-dimension collection
    print("[16] Testing Student-Learning Context Collection (7 dimensions)...")
    res = client.get("/api/progress/learning-context", headers=student_headers)
    assert res.status_code == 200
    ctx_data = res.json()
    assert ctx_data["student_id"] == 2
    assert ctx_data["preferred_resource_type"] == "Practice"
    assert "records" in ctx_data
    assert len(ctx_data["records"]) > 0

    first_record = ctx_data["records"][0]
    required_fields = [
        "student_id",
        "course",
        "topic_skill",
        "difficulty",
        "quiz_score",
        "progress",
        "preferred_resource_type"
    ]
    for field in required_fields:
        assert field in first_record, f"Missing context field '{field}' in record: {first_record}"

    print(f"    [PASS] Collected Context Tuple -> Student ID: #{first_record['student_id']} | Course: '{first_record['course']}' | Topic: '{first_record['topic_skill']}' | Difficulty: '{first_record['difficulty']}' | Quiz: {first_record['quiz_score']}% | Progress: {first_record['progress']}% | Pref: '{first_record['preferred_resource_type']}'")

    # Verify Progress Page UI renders Topic Mastery and Learning Context
    res = client.get("/progress", cookies=student_cookies)
    assert res.status_code == 200
    assert "Topic & Skill Mastery Breakdown" in res.text
    assert "Collected Student-Learning Context Records" in res.text
    print("    [PASS] Student Progress UI displays topic mastery and context table.")

    # 17. Failing Assessment Identifies Struggling Topic
    print("[17] Verifying assessment failure identifies struggling topic...")
    fail_res = client.post("/api/assessments/1/submit", headers=student_headers, json={
        "answers": {
            "1": "A",  # Wrong
            "2": "A",  # Wrong
            "3": "C",  # Wrong
            "4": "C",  # Wrong
            "5": "C"   # Wrong
        }
    })
    assert fail_res.status_code == 200
    f_data = fail_res.json()
    assert f_data["passed"] is False
    assert f_data["topic"] is not None

    # Check Result Page explicitly highlights struggling topic
    result_page_res = client.get(f"/assessments/results/{f_data['result_id']}", cookies=student_cookies)
    assert result_page_res.status_code == 200
    assert "struggling with the topic" in result_page_res.text
    print(f"    [PASS] System detected struggling topic '{f_data['topic']}' on failed assessment.")

    print("=" * 60)
    print("[+] ALL 17 TEST SUITES PASSED FLAWLESSLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
