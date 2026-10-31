from fastapi import APIRouter, HTTPException, Query, status
from typing import List
from app.models import RecommendedQuestion
from app.database import get_student_by_id
from app.ml.recommender import recommender_instance

router = APIRouter(tags=["recommendations"])

@router.get(
    "/next-questions/{student_id}",
    response_model=List[RecommendedQuestion],
    status_code=status.HTTP_200_OK
)
def get_next_questions(
    student_id: int,
    count: int = Query(default=4, ge=1, le=10, description="Number of questions to recommend")
):
    """
    Return personalized next questions for a student based on:
    1. Lowest mastery topic prioritization (SDG 4: targeting learning inequities)
    2. Zone of Proximal Development (ZPD) adaptive difficulty matching
    3. Filtering out recently answered correct questions
    4. Model prediction of success probability
    5. Explainable AI (XAI) rationale for each recommendation
    """
    student = get_student_by_id(student_id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found."
        )

    recommendations = recommender_instance.recommend(student_id=student_id, top_n=count)
    return recommendations
