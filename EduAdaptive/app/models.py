from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class StudentSchema(BaseModel):
    id: int
    name: str
    persona: str = ""

class LoginRequest(BaseModel):
    student_id: int
    name: str

class LoginResponse(BaseModel):
    student_id: int
    name: str
    persona: str
    is_new: bool
    message: str


class QuestionSchema(BaseModel):
    id: int
    topic: str
    difficulty: int = Field(ge=1, le=5)
    question_text: str
    options: List[str]
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None

class RecommendedQuestion(BaseModel):
    id: int
    topic: str
    difficulty: int
    question_text: str
    options: List[str]
    predicted_success_prob: float
    reasoning: str
    target_zpd: bool = True

class AttemptRequest(BaseModel):
    student_id: int
    question_id: int
    selected_option: str

class AttemptResponse(BaseModel):
    attempt_id: int
    student_id: int
    question_id: int
    topic: str
    difficulty: int
    is_correct: bool
    selected_option: str
    correct_answer: str
    explanation: str
    previous_mastery: float
    updated_mastery: float
    mastery_delta: float
    feedback_message: str

class TopicMastery(BaseModel):
    topic: str
    mastery_score: float
    last_difficulty: int
    questions_attempted: int
    questions_correct: int
    accuracy: float

class DashboardResponse(BaseModel):
    student_id: int
    student_name: str
    persona: str
    overall_mastery: float
    total_attempts: int
    total_correct: int
    overall_accuracy: float
    focus_topic: str
    topic_mastery: List[TopicMastery]
    difficulty_timeline: List[Dict[str, Any]]
    recent_attempts: List[Dict[str, Any]]
