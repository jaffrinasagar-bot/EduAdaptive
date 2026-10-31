from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Dict, Any, Optional
from app.models import DashboardResponse, TopicMastery, StudentSchema, LoginRequest, LoginResponse
from app.database import (
    get_student_by_id,
    get_all_students,
    get_learner_profile,
    get_student_attempts,
    create_student,
    init_student_profile,
    reset_student_data
)
from app.config import TOPICS
from app.seed import seed_database
from app.ml.classifier import classifier_instance

router = APIRouter(tags=["dashboard"])

@router.post("/login", response_model=LoginResponse)
def login_student(payload: LoginRequest):
    """
    Authenticate or register a student:
    - If Student ID exists, log them in and return existing record.
    - If Student ID does not exist, create the student and initialize a fresh learner_profile.
    """
    if payload.student_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student ID must be a positive integer."
        )

    student = get_student_by_id(payload.student_id)
    if student:
        # Existing student
        return LoginResponse(
            student_id=student["id"],
            name=student["name"],
            persona=student.get("persona", "Enrolled Student"),
            is_new=False,
            message=f"Welcome back, {student['name']}!"
        )
    else:
        # New student registration
        new_name = payload.name.strip() if payload.name.strip() else f"Student #{payload.student_id}"
        persona = "Self-Registered Learner"
        created = create_student(payload.student_id, new_name, persona)
        init_student_profile(payload.student_id, default_mastery=0.35)
        return LoginResponse(
            student_id=created["id"],
            name=created["name"],
            persona=persona,
            is_new=True,
            message=f"Account created! Welcome, {created['name']}."
        )

@router.get("/students", response_model=List[StudentSchema])

def list_students():
    """List all student personas for switching demo accounts."""
    students = get_all_students()
    return students

@router.get("/dashboard/{student_id}", response_model=DashboardResponse)
def get_dashboard(student_id: int):
    """
    Return comprehensive analytics for the student:
    - Topic mastery breakdown (Radar / Bar chart)
    - Difficulty progression and accuracy over time (Timeline chart)
    - KPI cards: Total attempts, accuracy, overall mastery, focus topic
    - Recent attempt history
    """
    student = get_student_by_id(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found."
        )

    # 1. Fetch learner profiles
    profiles = get_learner_profile(student_id)
    profile_map = {p["topic"]: p for p in profiles}

    topic_masteries: List[TopicMastery] = []
    total_attempts = 0
    total_correct = 0
    mastery_sum = 0.0

    for topic in TOPICS:
        p = profile_map.get(topic)
        if p:
            attempted = p["questions_attempted"]
            correct = p["questions_correct"]
            mastery = p["mastery_score"]
            last_diff = p["last_difficulty"]
        else:
            attempted = 0
            correct = 0
            mastery = 0.20
            last_diff = 1

        acc = round(correct / attempted, 3) if attempted > 0 else 0.0

        total_attempts += attempted
        total_correct += correct
        mastery_sum += mastery

        topic_masteries.append(TopicMastery(
            topic=topic,
            mastery_score=round(mastery, 3),
            last_difficulty=last_diff,
            questions_attempted=attempted,
            questions_correct=correct,
            accuracy=acc
        ))

    overall_mastery = round(mastery_sum / len(TOPICS), 3) if TOPICS else 0.0
    overall_accuracy = round(total_correct / total_attempts, 3) if total_attempts > 0 else 0.0

    # Weakest topic is focus topic
    focus_topic = min(topic_masteries, key=lambda tm: tm.mastery_score).topic

    # 2. Difficulty and Accuracy Progression Timeline
    # Fetch all attempts in chronological order (oldest to newest)
    raw_attempts = get_student_attempts(student_id, limit=None)
    chronological_attempts = list(reversed(raw_attempts))

    difficulty_timeline: List[Dict[str, Any]] = []
    cumulative_correct = 0

    for idx, att in enumerate(chronological_attempts, start=1):
        if att["is_correct"]:
            cumulative_correct += 1
        rolling_acc = round(cumulative_correct / idx, 3)

        difficulty_timeline.append({
            "attempt_number": idx,
            "topic": att["topic"],
            "difficulty": att["difficulty"],
            "is_correct": bool(att["is_correct"]),
            "timestamp": att["timestamp"],
            "rolling_accuracy": rolling_acc,
            "question_text": att.get("question_text", "")
        })

    # 3. Recent 10 attempts for the tabular log
    recent_attempts: List[Dict[str, Any]] = [
        {
            "id": a["id"],
            "topic": a["topic"],
            "difficulty": a["difficulty"],
            "is_correct": bool(a["is_correct"]),
            "timestamp": a["timestamp"],
            "question_text": a.get("question_text", "")
        }
        for a in raw_attempts[:10]
    ]

    return DashboardResponse(
        student_id=student["id"],
        student_name=student["name"],
        persona=student.get("persona", ""),
        overall_mastery=overall_mastery,
        total_attempts=total_attempts,
        total_correct=total_correct,
        overall_accuracy=overall_accuracy,
        focus_topic=focus_topic,
        topic_mastery=topic_masteries,
        difficulty_timeline=difficulty_timeline,
        recent_attempts=recent_attempts
    )

@router.post("/reset")
def reset_database(student_id: Optional[int] = Query(default=None, description="Optional student ID for scoped reset")):
    """
    Reset demo data:
    - If student_id is provided, reset only that student's attempts and profile.
    - If student_id is omitted, perform full reset to initial seed state.
    """
    if student_id is not None:
        reset_student_data(student_id)
        classifier_instance.train_from_database()
        return {
            "status": "success",
            "message": f"Demo data for student {student_id} has been reset.",
            "student_id": student_id
        }
    else:
        seed_database(reset=True)
        classifier_instance.train_from_database()
        return {
            "status": "success",
            "message": "Database and ML model reset to seed state.",
            "student_id": None
        }

