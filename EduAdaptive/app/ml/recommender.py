"""
ML COMPONENT 2: Adaptive Practice Question Recommender
------------------------------------------------------
Pitch Context for Judges (SDG 4: Quality Education):
Education research shows that students drop out or lose confidence when learning
is either boringly repetitive or overwhelming (frustration zone).

This Recommender engine implements Vygotsky's "Zone of Proximal Development" (ZPD):
1. Prioritizes topics with the lowest mastery score to eliminate knowledge gaps.
2. Selects questions with difficulty tuned to the student's current proficiency:
   - Does not repeat questions already answered correctly recently.
   - Smoothly steps up difficulty once proficiency is demonstrated.
   - Adjusts downwards if recent struggles are detected to restore confidence.
3. Generates transparent, human-readable Explainable AI (XAI) rationale for every recommendation.
"""

from typing import List, Dict, Any, Optional
from app.config import TOPICS, MIN_DIFFICULTY, MAX_DIFFICULTY, RECENT_CORRECT_EXCLUDE_LIMIT
from app.database import (
    get_all_questions,
    get_learner_profile,
    get_recent_correct_question_ids,
    get_recent_streak_in_topic,
    get_student_by_id
)
from app.ml.classifier import classifier_instance

class RecommenderEngine:
    def __init__(self):
        self.classifier = classifier_instance

    @staticmethod
    def calculate_target_difficulty(mastery: float, streak: int, last_diff: int) -> int:
        """
        Determine the ideal target difficulty level (1-5) based on mastery and momentum.
        Adaptive step-up / step-down logic:
        - Low mastery (<0.35) -> Level 1 (or 2 if on positive streak)
        - Medium mastery (0.35-0.65) -> Level 2-3
        - Proficient (0.65-0.82) -> Level 3-4
        - Advanced (>0.82) -> Level 4-5
        """
        if mastery < 0.35:
            base_diff = 1
            if streak >= 2:
                base_diff = 2
        elif mastery < 0.60:
            base_diff = 2
            if streak >= 2:
                base_diff = 3
            elif streak <= -2:
                base_diff = 1
        elif mastery < 0.82:
            base_diff = 3
            if streak >= 2:
                base_diff = 4
            elif streak <= -2:
                base_diff = 2
        else:
            base_diff = 4
            if streak >= 1 or mastery >= 0.88:
                base_diff = 5
            elif streak <= -2:
                base_diff = 3

        return max(MIN_DIFFICULTY, min(MAX_DIFFICULTY, base_diff))

    @staticmethod
    def generate_explanation(
        topic: str,
        difficulty: int,
        mastery: float,
        predicted_prob: float,
        is_lowest_topic: bool,
        streak: int
    ) -> str:
        """
        Construct a transparent, encouraging pedagogical explanation (XAI).
        """
        mastery_pct = int(round(mastery * 100))
        prob_pct = int(round(predicted_prob * 100))

        if is_lowest_topic:
            return (
                f"Priority Focus: Your mastery in {topic} is {mastery_pct}%. "
                f"Level {difficulty} is selected to strengthen core concepts "
                f"(Predicted success rate: {prob_pct}%)."
            )
        elif streak >= 2:
            return (
                f"Momentum Builder: On a hot streak (+{streak}) in {topic}! "
                f"Stepping up to Level {difficulty} to challenge your skills "
                f"(Predicted success rate: {prob_pct}%)."
            )
        elif mastery >= 0.80:
            return (
                f"Mastery Challenge: Strong proficiency in {topic} ({mastery_pct}%). "
                f"Level {difficulty} problem to test advanced synthesis "
                f"(Predicted success rate: {prob_pct}%)."
            )
        else:
            return (
                f"Adaptive Practice: Reinforcing {topic} (Mastery: {mastery_pct}%). "
                f"Level {difficulty} fits your current learning zone "
                f"(Predicted success rate: {prob_pct}%)."
            )

    def recommend(self, student_id: int, top_n: int = 4) -> List[Dict[str, Any]]:
        """
        Generate top N personalized question recommendations for the student.
        """
        # 1. Fetch student profiles and recent history
        profiles = get_learner_profile(student_id)
        profile_map = {p["topic"]: p for p in profiles}

        # Ensure all topics have a profile entry
        for t in TOPICS:
            if t not in profile_map:
                profile_map[t] = {
                    "student_id": student_id,
                    "topic": t,
                    "mastery_score": 0.20,
                    "last_difficulty": 1,
                    "questions_attempted": 0,
                    "questions_correct": 0
                }

        # Rank topics by lowest mastery score (SDG 4: focus on the most in-need areas)
        sorted_topics = sorted(TOPICS, key=lambda t: profile_map[t]["mastery_score"])
        lowest_topic = sorted_topics[0]

        # 2. Exclude recently correctly answered questions
        recent_correct_ids = set(get_recent_correct_question_ids(student_id, limit=RECENT_CORRECT_EXCLUDE_LIMIT))

        # 3. Retrieve and score all eligible questions
        all_questions = get_all_questions()

        scored_candidates: List[Dict[str, Any]] = []

        for q in all_questions:
            qid = q["id"]
            topic = q["topic"]
            q_diff = q["difficulty"]

            # Repetition prevention
            if qid in recent_correct_ids:
                continue

            t_prof = profile_map.get(topic, {})
            mastery = t_prof.get("mastery_score", 0.20)
            attempted = t_prof.get("questions_attempted", 0)
            correct = t_prof.get("questions_correct", 0)
            last_diff = t_prof.get("last_difficulty", 1)

            streak = get_recent_streak_in_topic(student_id, topic, limit=4)
            target_diff = self.calculate_target_difficulty(mastery, streak, last_diff)

            # ML prediction: P(success)
            p_success = self.classifier.predict_success_probability(
                questions_attempted=attempted,
                questions_correct=correct,
                recent_streak=streak,
                difficulty=q_diff
            )

            # --- Multi-Objective Recommendation Scoring ---
            # 1. Topic Gap Priority: Lower mastery = higher urgency (up to 40 pts)
            topic_urgency = (1.0 - mastery) * 40.0
            if topic == lowest_topic:
                topic_urgency += 15.0  # Extra focus boost for student's weakest area

            # 2. Zone of Proximal Development (ZPD) optimality: Target P(success) ~ 0.70
            # Sweet spot: 0.60 to 0.80. Heavily penalize extremes (<0.35 frustrating, >0.90 boring)
            zpd_score = 30.0 * max(0.0, 1.0 - (abs(p_success - 0.70) / 0.40))

            # 3. Difficulty match bonus
            diff_delta = abs(q_diff - target_diff)
            if diff_delta == 0:
                diff_bonus = 20.0
            elif diff_delta == 1:
                diff_bonus = 8.0
            else:
                diff_bonus = -25.0

            total_score = topic_urgency + zpd_score + diff_bonus

            reasoning = self.generate_explanation(
                topic=topic,
                difficulty=q_diff,
                mastery=mastery,
                predicted_prob=p_success,
                is_lowest_topic=(topic == lowest_topic),
                streak=streak
            )

            scored_candidates.append({
                "id": qid,
                "topic": topic,
                "difficulty": q_diff,
                "question_text": q["question_text"],
                "options": q["options"],
                "predicted_success_prob": p_success,
                "reasoning": reasoning,
                "target_zpd": (0.50 <= p_success <= 0.85),
                "score": total_score
            })

        # Sort all candidates by composite recommendation score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)

        # Diverse Selection Strategy:
        # Guarantee representation of weakest topic first, then best candidates
        selected: List[Dict[str, Any]] = []
        selected_ids = set()

        # Top 1-2 from lowest topic
        lowest_candidates = [c for c in scored_candidates if c["topic"] == lowest_topic]
        for c in lowest_candidates[:2]:
            selected.append(c)
            selected_ids.add(c["id"])

        # Fill remaining slots with the highest-scoring questions across other topics
        for c in scored_candidates:
            if c["id"] not in selected_ids:
                selected.append(c)
                selected_ids.add(c["id"])
            if len(selected) >= top_n:
                break

        # Fallback if catalog was small or heavily filtered
        if len(selected) < top_n:
            for q in all_questions:
                if q["id"] not in selected_ids:
                    selected.append({
                        "id": q["id"],
                        "topic": q["topic"],
                        "difficulty": q["difficulty"],
                        "question_text": q["question_text"],
                        "options": q["options"],
                        "predicted_success_prob": 0.70,
                        "reasoning": f"General practice in {q['topic']}.",
                        "target_zpd": True,
                        "score": 0.0
                    })
                    selected_ids.add(q["id"])
                if len(selected) >= top_n:
                    break

        # Clean output schema (remove internal sorting score)
        return [
            {
                "id": s["id"],
                "topic": s["topic"],
                "difficulty": s["difficulty"],
                "question_text": s["question_text"],
                "options": s["options"],
                "predicted_success_prob": s["predicted_success_prob"],
                "reasoning": s["reasoning"],
                "target_zpd": s["target_zpd"]
            }
            for s in selected
        ]

recommender_instance = RecommenderEngine()
