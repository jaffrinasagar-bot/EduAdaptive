from fastapi import APIRouter, HTTPException, status
from app.models import AttemptRequest, AttemptResponse
from app.database import (
    get_question_by_id,
    get_student_by_id,
    get_topic_mastery,
    upsert_learner_profile,
    record_attempt,
    get_recent_streak_in_topic
)
from app.ml.classifier import classifier_instance

router = APIRouter(tags=["attempts"])

@router.post("/attempt", response_model=AttemptResponse, status_code=status.HTTP_200_OK)
def log_attempt(payload: AttemptRequest):
    """
    Log a student's answer attempt:
    1. Validates the student and question.
    2. Checks correctness of the chosen answer.
    3. Uses ML to compute predicted probability and dynamic online mastery update.
    4. Persists the attempt and updates the learner_profile in the database.
    5. Returns instant educational feedback, explanation, and mastery score change.
    """
    # 1. Verify student and question
    student = get_student_by_id(payload.student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {payload.student_id} not found."
        )

    question = get_question_by_id(payload.question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with ID {payload.question_id} not found."
        )

    # 2. Check correctness
    topic = question["topic"]
    difficulty = question["difficulty"]
    correct_answer = question["correct_answer"]
    explanation = question.get("explanation", "")

    # Clean comparison (stripping whitespace, lower-case fallback if needed)
    is_correct = (payload.selected_option.strip() == correct_answer.strip())

    # 3. Retrieve student's current mastery for this topic
    profile = get_topic_mastery(payload.student_id, topic)
    if profile:
        prev_mastery = profile["mastery_score"]
        attempted = profile["questions_attempted"]
        correct = profile["questions_correct"]
    else:
        prev_mastery = 0.20
        attempted = 0
        correct = 0

    streak = get_recent_streak_in_topic(payload.student_id, topic, limit=4)

    # 4. Predict probability and compute online mastery update
    predicted_prob = classifier_instance.predict_success_probability(
        questions_attempted=attempted,
        questions_correct=correct,
        recent_streak=streak,
        difficulty=difficulty
    )

    new_mastery, delta = classifier_instance.update_mastery_score(
        current_mastery=prev_mastery,
        is_correct=is_correct,
        difficulty=difficulty,
        predicted_prob=predicted_prob
    )

    # 5. Persist attempt
    attempt_id = record_attempt(
        student_id=payload.student_id,
        question_id=payload.question_id,
        topic=topic,
        difficulty=difficulty,
        is_correct=1 if is_correct else 0
    )

    # 6. Update learner profile
    new_attempted = attempted + 1
    new_correct = correct + (1 if is_correct else 0)
    upsert_learner_profile(
        student_id=payload.student_id,
        topic=topic,
        mastery_score=new_mastery,
        last_difficulty=difficulty,
        questions_attempted=new_attempted,
        questions_correct=new_correct
    )

    # 7. Formulate encouraging feedback message
    if is_correct:
        if delta > 0.05:
            feedback = f"Outstanding! Solved a challenging Level {difficulty} problem. Mastery in {topic} surged by +{int(round(delta*100))}%."
        else:
            feedback = f"Correct! Good solid grasp on this {topic} question. Mastery increased."
    else:
        feedback = f"Not quite. Review the explanation above to close the gap. Keep going!"

    return AttemptResponse(
        attempt_id=attempt_id,
        student_id=payload.student_id,
        question_id=payload.question_id,
        topic=topic,
        difficulty=difficulty,
        is_correct=is_correct,
        selected_option=payload.selected_option,
        correct_answer=correct_answer,
        explanation=explanation,
        previous_mastery=round(prev_mastery, 3),
        updated_mastery=round(new_mastery, 3),
        mastery_delta=round(delta, 3),
        feedback_message=feedback
    )
