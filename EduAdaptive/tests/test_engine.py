import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db_connection, init_db, get_student_by_id, get_topic_mastery
from app.seed import seed_database
from app.ml.classifier import classifier_instance
from app.ml.recommender import recommender_instance

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Ensure database is seeded before running tests."""
    seed_database(reset=True)
    classifier_instance.train_from_database()
    yield

def test_database_seeding():
    """Test that all tables are populated with seed data."""
    conn = get_db_connection()
    q_count = conn.execute("SELECT COUNT(*) FROM questions;").fetchone()[0]
    s_count = conn.execute("SELECT COUNT(*) FROM students;").fetchone()[0]
    a_count = conn.execute("SELECT COUNT(*) FROM attempts;").fetchone()[0]
    p_count = conn.execute("SELECT COUNT(*) FROM learner_profile;").fetchone()[0]
    conn.close()

    assert q_count >= 40, f"Expected at least 40 questions, got {q_count}"
    assert s_count == 5, f"Expected 5 students, got {s_count}"
    assert a_count >= 100, f"Expected >=100 attempts, got {a_count}"
    assert p_count == 20, f"Expected 20 profile rows (5 students * 4 topics), got {p_count}"

def test_ml_classifier_predictions():
    """Test the mastery classifier produces valid calibrated probabilities."""
    # Test high ability student on easy question
    p_high = classifier_instance.predict_success_probability(
        questions_attempted=20,
        questions_correct=18,
        recent_streak=3,
        difficulty=1
    )
    # Test low ability student on hard question
    p_low = classifier_instance.predict_success_probability(
        questions_attempted=10,
        questions_correct=2,
        recent_streak=-3,
        difficulty=5
    )

    assert 0.05 <= p_high <= 0.95
    assert 0.05 <= p_low <= 0.95
    assert p_high > p_low, f"High ability ({p_high}) should predict higher probability than low ability ({p_low})"

def test_online_mastery_update():
    """Test dynamic Bayesian mastery update logic."""
    initial_mastery = 0.50

    # Correct answer on difficult question (difficulty 5) -> large boost
    new_m1, delta1 = classifier_instance.update_mastery_score(
        current_mastery=initial_mastery,
        is_correct=True,
        difficulty=5,
        predicted_prob=0.30
    )
    assert delta1 > 0
    assert new_m1 > initial_mastery

    # Incorrect answer on easy question (difficulty 1) -> drop
    new_m2, delta2 = classifier_instance.update_mastery_score(
        current_mastery=initial_mastery,
        is_correct=False,
        difficulty=1,
        predicted_prob=0.85
    )
    assert delta2 < 0
    assert new_m2 < initial_mastery

def test_recommender_prioritizes_weakest_topic():
    """Test that student 2 (Bob, weak in Probability) gets Probability recommended first."""
    # Bob Jones has lowest mastery in Probability
    recs = recommender_instance.recommend(student_id=2, top_n=4)
    assert len(recs) == 4
    # First recommendation should target Bob's weakest topic: Probability
    assert recs[0]["topic"] == "Probability"
    assert "reasoning" in recs[0]
    assert len(recs[0]["options"]) == 4

def test_api_endpoints():
    """Test all FastAPI endpoints end-to-end using TestClient."""
    with TestClient(app) as client:
        # 1. GET /students
        res = client.get("/students")
        assert res.status_code == 200
        students = res.json()
        assert len(students) == 5

        # 2. GET /next-questions/{student_id}
        res = client.get("/next-questions/2?count=3")
        assert res.status_code == 200
        recs = res.json()
        assert len(recs) == 3
        q = recs[0]
        assert "predicted_success_prob" in q

        # 3. POST /attempt
        # Pick the recommended question and submit the correct answer
        question_id = q["id"]
        # Fetch question details from DB to know correct answer
        from app.database import get_question_by_id
        q_db = get_question_by_id(question_id)
        assert q_db is not None

        attempt_payload = {
            "student_id": 2,
            "question_id": question_id,
            "selected_option": q_db["correct_answer"]
        }
        res = client.post("/attempt", json=attempt_payload)
        assert res.status_code == 200
        att_resp = res.json()
        assert att_resp["is_correct"] is True
        assert att_resp["updated_mastery"] >= att_resp["previous_mastery"]

        # 4. GET /dashboard/{student_id}
        res = client.get("/dashboard/2")
        assert res.status_code == 200
        dash = res.json()
        assert dash["student_id"] == 2
        assert len(dash["topic_mastery"]) == 4
        assert len(dash["difficulty_timeline"]) > 0
        assert len(dash["recent_attempts"]) > 0

        # 5. POST /reset
        res = client.post("/reset")
        assert res.status_code == 200
        assert res.json()["status"] == "success"
