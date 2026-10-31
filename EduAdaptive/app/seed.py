import json
from datetime import datetime, timedelta, timezone
import random
from app.config import TOPICS
from app.database import get_db_connection, init_db

# Curated high-quality curriculum questions across 4 topics and 5 difficulty tiers
SAMPLE_QUESTIONS = [
    # --- ALGEBRA (11 questions) ---
    {
        "topic": "Algebra",
        "difficulty": 1,
        "question_text": "Solve for x: x + 7 = 15",
        "options": ["x = 6", "x = 8", "x = 9", "x = 22"],
        "correct_answer": "x = 8",
        "explanation": "Subtract 7 from both sides: x = 15 - 7 = 8."
    },
    {
        "topic": "Algebra",
        "difficulty": 1,
        "question_text": "What is the value of 3y when y = 4?",
        "options": ["7", "12", "14", "1"],
        "correct_answer": "12",
        "explanation": "Multiply 3 by 4: 3 * 4 = 12."
    },
    {
        "topic": "Algebra",
        "difficulty": 2,
        "question_text": "Solve the linear equation: 2x - 5 = 11",
        "options": ["x = 3", "x = 6", "x = 8", "x = 16"],
        "correct_answer": "x = 8",
        "explanation": "Add 5 to both sides: 2x = 16, then divide by 2: x = 8."
    },
    {
        "topic": "Algebra",
        "difficulty": 2,
        "question_text": "Simplify the expression: 4(2a + 3) - 5a",
        "options": ["3a + 12", "3a + 3", "13a + 12", "3a - 12"],
        "correct_answer": "3a + 12",
        "explanation": "Expand: 8a + 12 - 5a = (8a - 5a) + 12 = 3a + 12."
    },
    {
        "topic": "Algebra",
        "difficulty": 3,
        "question_text": "Factor the quadratic expression: x^2 - 9",
        "options": ["(x - 3)(x - 3)", "(x + 3)(x - 3)", "(x + 9)(x - 1)", "(x + 3)(x + 3)"],
        "correct_answer": "(x + 3)(x - 3)",
        "explanation": "Difference of two squares: a^2 - b^2 = (a + b)(a - b). Here a = x, b = 3."
    },
    {
        "topic": "Algebra",
        "difficulty": 3,
        "question_text": "Solve for x: 3(x - 2) = 2(x + 4)",
        "options": ["x = 10", "x = 14", "x = 6", "x = 2"],
        "correct_answer": "x = 14",
        "explanation": "Expand both sides: 3x - 6 = 2x + 8. Subtract 2x and add 6: x = 14."
    },
    {
        "topic": "Algebra",
        "difficulty": 4,
        "question_text": "Find the roots of the quadratic equation: x^2 - 5x + 6 = 0",
        "options": ["x = -2, -3", "x = 2, 3", "x = 1, 6", "x = -1, -6"],
        "correct_answer": "x = 2, 3",
        "explanation": "Factor: (x - 2)(x - 3) = 0, giving roots x = 2 and x = 3."
    },
    {
        "topic": "Algebra",
        "difficulty": 4,
        "question_text": "If f(x) = 2x^2 - 3x + 1, find f(-2).",
        "options": ["3", "7", "15", "19"],
        "correct_answer": "15",
        "explanation": "Substitute x = -2: 2(-2)^2 - 3(-2) + 1 = 2(4) + 6 + 1 = 8 + 6 + 1 = 15."
    },
    {
        "topic": "Algebra",
        "difficulty": 5,
        "question_text": "Find the discriminant and nature of roots for 2x^2 - 4x + 5 = 0.",
        "options": [
            "D = 24, Two real distinct roots",
            "D = -24, Two complex conjugate roots",
            "D = 0, One repeated real root",
            "D = -56, Two complex conjugate roots"
        ],
        "correct_answer": "D = -24, Two complex conjugate roots",
        "explanation": "D = b^2 - 4ac = (-4)^2 - 4(2)(5) = 16 - 40 = -24 < 0, yielding complex conjugate roots."
    },
    {
        "topic": "Algebra",
        "difficulty": 5,
        "question_text": "If log_2(x) + log_2(x - 2) = 3, what is the valid real value of x?",
        "options": ["x = 4", "x = -2", "x = 2", "x = 8"],
        "correct_answer": "x = 4",
        "explanation": "Combine: log_2(x(x - 2)) = 3 => x^2 - 2x = 8 => x^2 - 2x - 8 = 0 => (x - 4)(x + 2) = 0. Since x > 2, x = 4."
    },

    # --- GEOMETRY (11 questions) ---
    {
        "topic": "Geometry",
        "difficulty": 1,
        "question_text": "What is the perimeter of a rectangle with length 8 cm and width 5 cm?",
        "options": ["13 cm", "26 cm", "40 cm", "20 cm"],
        "correct_answer": "26 cm",
        "explanation": "Perimeter = 2 * (length + width) = 2 * (8 + 5) = 2 * 13 = 26 cm."
    },
    {
        "topic": "Geometry",
        "difficulty": 1,
        "question_text": "What is the sum of interior angles in any triangle?",
        "options": ["90°", "180°", "270°", "360°"],
        "correct_answer": "180°",
        "explanation": "The sum of interior angles in any Euclidean triangle is always 180°."
    },
    {
        "topic": "Geometry",
        "difficulty": 2,
        "question_text": "In a right triangle, legs are 6 cm and 8 cm. What is the length of the hypotenuse?",
        "options": ["10 cm", "14 cm", "12 cm", "7 cm"],
        "correct_answer": "10 cm",
        "explanation": "By the Pythagorean theorem: c = sqrt(6^2 + 8^2) = sqrt(36 + 64) = sqrt(100) = 10 cm."
    },
    {
        "topic": "Geometry",
        "difficulty": 2,
        "question_text": "Find the area of a triangle with base 10 m and height 7 m.",
        "options": ["70 m²", "35 m²", "17 m²", "45 m²"],
        "correct_answer": "35 m²",
        "explanation": "Area = 0.5 * base * height = 0.5 * 10 * 7 = 35 m²."
    },
    {
        "topic": "Geometry",
        "difficulty": 3,
        "question_text": "What is the area of a circle with radius 7 cm? (Use π ≈ 22/7)",
        "options": ["44 cm²", "154 cm²", "88 cm²", "147 cm²"],
        "correct_answer": "154 cm²",
        "explanation": "Area = π * r^2 = (22/7) * 7 * 7 = 154 cm²."
    },
    {
        "topic": "Geometry",
        "difficulty": 3,
        "question_text": "What is the measure of each interior angle in a regular pentagon?",
        "options": ["72°", "108°", "120°", "90°"],
        "correct_answer": "108°",
        "explanation": "Interior angle formula: ((n - 2) * 180) / n = ((5 - 2) * 180) / 5 = 540 / 5 = 108°."
    },
    {
        "topic": "Geometry",
        "difficulty": 4,
        "question_text": "A cylinder has radius 3 cm and height 10 cm. Find its total surface area in terms of π.",
        "options": ["60π cm²", "78π cm²", "90π cm²", "54π cm²"],
        "correct_answer": "78π cm²",
        "explanation": "Total surface area = 2πr^2 + 2πrh = 2π(9) + 2π(3)(10) = 18π + 60π = 78π cm²."
    },
    {
        "topic": "Geometry",
        "difficulty": 4,
        "question_text": "Two similar triangles have areas in ratio 16:49. What is the ratio of their corresponding sides?",
        "options": ["4:7", "16:49", "2:sqrt(7)", "8:24.5"],
        "correct_answer": "4:7",
        "explanation": "The ratio of linear dimensions is the square root of the ratio of areas: sqrt(16/49) = 4/7."
    },
    {
        "topic": "Geometry",
        "difficulty": 5,
        "question_text": "In triangle ABC, side a = 7, b = 8, and angle C = 60°. Find side c using the Law of Cosines.",
        "options": ["sqrt(57)", "sqrt(113)", "sqrt(65)", "sqrt(97)"],
        "correct_answer": "sqrt(57)",
        "explanation": "c^2 = a^2 + b^2 - 2ab*cos(C) = 49 + 64 - 2(7)(8)(0.5) = 113 - 56 = 57. Thus c = sqrt(57) ≈ 7.55."
    },
    {
        "topic": "Geometry",
        "difficulty": 5,
        "question_text": "What is the volume of a regular tetrahedron with edge length 6 cm?",
        "options": ["18*sqrt(2) cm³", "36 cm³", "12*sqrt(3) cm³", "24*sqrt(2) cm³"],
        "correct_answer": "18*sqrt(2) cm³",
        "explanation": "Formula: V = (a^3) / (6 * sqrt(2)) = 216 / (6 * sqrt(2)) = 36 / sqrt(2) = 18*sqrt(2) cm³."
    },

    # --- PROBABILITY (11 questions) ---
    {
        "topic": "Probability",
        "difficulty": 1,
        "question_text": "A standard six-sided die is rolled. What is the probability of rolling a 4?",
        "options": ["1/6", "1/2", "1/3", "4/6"],
        "correct_answer": "1/6",
        "explanation": "There is 1 favorable outcome out of 6 equally likely outcomes: P(4) = 1/6."
    },
    {
        "topic": "Probability",
        "difficulty": 1,
        "question_text": "A coin is tossed once. What is the probability of getting heads?",
        "options": ["0.25", "0.50", "0.75", "1.00"],
        "correct_answer": "0.50",
        "explanation": "A fair coin has 2 outcomes: heads or tails. P(Heads) = 1/2 = 0.50."
    },
    {
        "topic": "Probability",
        "difficulty": 2,
        "question_text": "A bag contains 3 red, 4 blue, and 5 green marbles. What is the probability of drawing a blue marble?",
        "options": ["1/4", "1/3", "4/15", "5/12"],
        "correct_answer": "1/3",
        "explanation": "Total marbles = 3 + 4 + 5 = 12. P(Blue) = 4 / 12 = 1/3."
    },
    {
        "topic": "Probability",
        "difficulty": 2,
        "question_text": "What is the probability of rolling an even number on a standard die?",
        "options": ["1/6", "1/3", "1/2", "2/3"],
        "correct_answer": "1/2",
        "explanation": "Even numbers are 2, 4, 6 (3 outcomes). P(Even) = 3/6 = 1/2."
    },
    {
        "topic": "Probability",
        "difficulty": 3,
        "question_text": "Two independent coins are flipped. What is the probability of getting at least one head?",
        "options": ["1/4", "1/2", "3/4", "1/3"],
        "correct_answer": "3/4",
        "explanation": "Sample space: {HH, HT, TH, TT}. Outcomes with at least one head = 3, so P = 3/4."
    },
    {
        "topic": "Probability",
        "difficulty": 3,
        "question_text": "A card is drawn from a standard deck of 52 cards. What is the probability of drawing a Queen or a Heart?",
        "options": ["17/52", "16/52", "4/13", "1/4"],
        "correct_answer": "16/52",
        "explanation": "P(Queen) = 4/52, P(Heart) = 13/52, P(Queen of Hearts) = 1/52. P = 4/52 + 13/52 - 1/52 = 16/52 = 4/13."
    },
    {
        "topic": "Probability",
        "difficulty": 4,
        "question_text": "Two dice are rolled. What is the probability that the sum of the numbers is 9?",
        "options": ["1/9", "1/6", "5/36", "1/12"],
        "correct_answer": "1/9",
        "explanation": "Pairs summing to 9: (3,6), (4,5), (5,4), (6,3) = 4 pairs out of 36. P = 4/36 = 1/9."
    },
    {
        "topic": "Probability",
        "difficulty": 4,
        "question_text": "In a group of 30 students, 18 take Physics, 15 take Chemistry, and 8 take both. Find the probability a random student takes neither.",
        "options": ["5/30", "7/30", "8/30", "1/6"],
        "correct_answer": "5/30",
        "explanation": "P(Physics or Chem) = 18 + 15 - 8 = 25. Neither = 30 - 25 = 5. P = 5/30 = 1/6."
    },
    {
        "topic": "Probability",
        "difficulty": 5,
        "question_text": "A test has 95% sensitivity and 90% specificity. If disease prevalence is 1%, what is P(Disease | Positive Test)?",
        "options": ["~8.8%", "~95%", "~50%", "~19.2%"],
        "correct_answer": "~8.8%",
        "explanation": "Bayes' Theorem: (0.95 * 0.01) / [0.95 * 0.01 + 0.10 * 0.99] = 0.0095 / (0.0095 + 0.099) ≈ 0.0876 (8.8%)."
    },
    {
        "topic": "Probability",
        "difficulty": 5,
        "question_text": "A biased coin lands on heads with probability p = 0.6. In 5 independent flips, what is the probability of exactly 3 heads?",
        "options": ["0.3456", "0.2304", "0.1980", "0.5120"],
        "correct_answer": "0.3456",
        "explanation": "Binomial: C(5, 3) * (0.6)^3 * (0.4)^2 = 10 * 0.216 * 0.16 = 0.3456."
    },

    # --- NUMBER SYSTEMS (11 questions) ---
    {
        "topic": "Number Systems",
        "difficulty": 1,
        "question_text": "Which of the following numbers is a prime number?",
        "options": ["9", "15", "17", "21"],
        "correct_answer": "17",
        "explanation": "17 has only two factors: 1 and 17, so it is a prime number."
    },
    {
        "topic": "Number Systems",
        "difficulty": 1,
        "question_text": "What is the Greatest Common Divisor (GCD) of 12 and 18?",
        "options": ["2", "3", "6", "12"],
        "correct_answer": "6",
        "explanation": "Divisors of 12: 1, 2, 3, 4, 6, 12. Divisors of 18: 1, 2, 3, 6, 9, 18. Greatest common is 6."
    },
    {
        "topic": "Number Systems",
        "difficulty": 2,
        "question_text": "Convert the binary number 1011_2 into base 10.",
        "options": ["9", "11", "13", "15"],
        "correct_answer": "11",
        "explanation": "1011_2 = 1*(2^3) + 0*(2^2) + 1*(2^1) + 1*(2^0) = 8 + 0 + 2 + 1 = 11."
    },
    {
        "topic": "Number Systems",
        "difficulty": 2,
        "question_text": "What is the Least Common Multiple (LCM) of 6 and 8?",
        "options": ["12", "18", "24", "48"],
        "correct_answer": "24",
        "explanation": "Multiples of 6: 6, 12, 18, 24... Multiples of 8: 8, 16, 24... LCM = 24."
    },
    {
        "topic": "Number Systems",
        "difficulty": 3,
        "question_text": "What is the value of 5! (5 factorial)?",
        "options": ["60", "100", "120", "720"],
        "correct_answer": "120",
        "explanation": "5! = 5 * 4 * 3 * 2 * 1 = 120."
    },
    {
        "topic": "Number Systems",
        "difficulty": 3,
        "question_text": "What is the remainder when 47 is divided by 5?",
        "options": ["1", "2", "3", "4"],
        "correct_answer": "2",
        "explanation": "47 = 5 * 9 + 2, so the remainder is 2."
    },
    {
        "topic": "Number Systems",
        "difficulty": 4,
        "question_text": "Evaluate: 7^3 mod 5.",
        "options": ["1", "2", "3", "4"],
        "correct_answer": "3",
        "explanation": "7 ≡ 2 mod 5. Therefore, 7^3 ≡ 2^3 = 8 ≡ 3 mod 5."
    },
    {
        "topic": "Number Systems",
        "difficulty": 4,
        "question_text": "How many positive integer factors does 72 have?",
        "options": ["8", "10", "12", "16"],
        "correct_answer": "12",
        "explanation": "Prime factorization: 72 = 2^3 * 3^2. Number of factors = (3 + 1)(2 + 1) = 4 * 3 = 12."
    },
    {
        "topic": "Number Systems",
        "difficulty": 5,
        "question_text": "Find the last two digits of 3^100.",
        "options": ["01", "07", "09", "81"],
        "correct_answer": "01",
        "explanation": "By Euler's Totient Theorem, phi(100) = 40. Or note 3^4 = 81, 3^20 ≡ 1 mod 100. (3^20)^5 ≡ 1 mod 100, last digits are 01."
    },
    {
        "topic": "Number Systems",
        "difficulty": 5,
        "question_text": "If x ≡ 2 mod 3 and x ≡ 3 mod 5, what is the smallest positive integer x?",
        "options": ["8", "11", "13", "17"],
        "correct_answer": "8",
        "explanation": "By Chinese Remainder Theorem: Numbers ≡ 3 mod 5 are 3, 8, 13... Check: 8 mod 3 = 2. So x = 8."
    }
]

# 5 Defined Student Personas
STUDENT_PERSONAS = [
    {
        "id": 1,
        "name": "Alice Smith",
        "persona": "High Achiever (Excels across all topics, exploring Lv 4-5)",
        # Target mastery per topic:
        "target_masteries": {"Algebra": 0.88, "Geometry": 0.84, "Probability": 0.80, "Number Systems": 0.86},
        "target_attempts": 38
    },
    {
        "id": 2,
        "name": "Bob Jones",
        "persona": "Struggling with Probability (Strong in Algebra/Numbers, gaps in Probability)",
        "target_masteries": {"Algebra": 0.78, "Geometry": 0.52, "Probability": 0.28, "Number Systems": 0.75},
        "target_attempts": 36
    },
    {
        "id": 3,
        "name": "Charlie Brown",
        "persona": "Balanced Beginner (Building foundations across Lv 1-2)",
        "target_masteries": {"Algebra": 0.45, "Geometry": 0.42, "Probability": 0.40, "Number Systems": 0.48},
        "target_attempts": 32
    },
    {
        "id": 4,
        "name": "Diana Prince",
        "persona": "Geometry Specialist (Ace in spatial topics, developing in Numbers)",
        "target_masteries": {"Algebra": 0.52, "Geometry": 0.90, "Probability": 0.55, "Number Systems": 0.32},
        "target_attempts": 34
    },
    {
        "id": 5,
        "name": "Ethan Hunt",
        "persona": "New Student (Fresh onboarding, early exploration)",
        "target_masteries": {"Algebra": 0.30, "Geometry": 0.25, "Probability": 0.22, "Number Systems": 0.35},
        "target_attempts": 12
    }
]

def seed_database(reset: bool = True):
    """Seed the database with questions, students, and ~150 synthetic attempts."""
    init_db()
    conn = get_db_connection()

    with conn:
        if reset:
            conn.execute("DELETE FROM attempts;")
            conn.execute("DELETE FROM learner_profile;")
            conn.execute("DELETE FROM questions;")
            conn.execute("DELETE FROM students;")

        # Insert Questions
        for q in SAMPLE_QUESTIONS:
            conn.execute("""
                INSERT INTO questions (topic, difficulty, question_text, options, correct_answer, explanation)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                q["topic"],
                q["difficulty"],
                q["question_text"],
                json.dumps(q["options"]),
                q["correct_answer"],
                q["explanation"]
            ))

        # Insert Students
        for s in STUDENT_PERSONAS:
            conn.execute("""
                INSERT INTO students (id, name, persona)
                VALUES (?, ?, ?)
            """, (s["id"], s["name"], s["persona"]))

    conn.close()

    # Fetch inserted questions by topic and difficulty
    all_questions = []
    conn = get_db_connection()
    q_rows = conn.execute("SELECT id, topic, difficulty FROM questions").fetchall()
    for row in q_rows:
        all_questions.append(dict(row))
    conn.close()

    # Generate synthetic attempts
    random.seed(42)  # Deterministic seed for reproducible pitch demos
    now = datetime.now(timezone.utc)

    total_attempts_count = 0

    for s in STUDENT_PERSONAS:
        student_id = s["id"]
        target_attempts = s["target_attempts"]
        target_masteries = s["target_masteries"]

        # Track rolling counts per topic
        topic_counts = {t: {"attempted": 0, "correct": 0, "last_diff": 1, "mastery": 0.20} for t in TOPICS}

        # Generate timestamps spaced over past 10 days
        for i in range(target_attempts):
            days_ago = (target_attempts - i) * 0.25
            attempt_time = (now - timedelta(days=days_ago)).isoformat()

            # Choose topic based on target profile
            topic = random.choice(TOPICS)
            t_mastery = target_masteries[topic]

            # Choose difficulty consistent with student level for that topic
            if t_mastery >= 0.75:
                diff_weights = [0.05, 0.15, 0.30, 0.35, 0.15]
            elif t_mastery >= 0.50:
                diff_weights = [0.15, 0.35, 0.35, 0.10, 0.05]
            else:
                diff_weights = [0.45, 0.40, 0.15, 0.00, 0.00]

            chosen_diff = random.choices([1, 2, 3, 4, 5], weights=diff_weights)[0]

            # Pick a question with this topic and difficulty
            candidate_qs = [q for q in all_questions if q["topic"] == topic and q["difficulty"] == chosen_diff]
            if not candidate_qs:
                candidate_qs = [q for q in all_questions if q["topic"] == topic]
            question = random.choice(candidate_qs)

            # Determine correctness based on student ability vs question difficulty
            # Logistic-style probability:
            # Base logit = 3.5 * t_mastery - 0.7 * difficulty
            ability_delta = (t_mastery * 5.0) - chosen_diff
            p_correct = 1.0 / (1.0 + (2.71828 ** (-1.2 * ability_delta)))
            p_correct = max(0.10, min(0.95, p_correct))

            is_correct = 1 if random.random() < p_correct else 0

            # Record attempt in DB
            conn = get_db_connection()
            with conn:
                conn.execute("""
                    INSERT INTO attempts (student_id, question_id, topic, difficulty, is_correct, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (student_id, question["id"], topic, chosen_diff, is_correct, attempt_time))
            conn.close()

            # Update topic tracker
            topic_counts[topic]["attempted"] += 1
            if is_correct:
                topic_counts[topic]["correct"] += 1
            topic_counts[topic]["last_diff"] = chosen_diff

            # Dynamic mastery update: moving average towards empirical performance
            curr_acc = topic_counts[topic]["correct"] / topic_counts[topic]["attempted"]
            # Blend accuracy with difficulty scaling
            diff_factor = (chosen_diff / 5.0) if is_correct else 0.0
            new_est = 0.7 * curr_acc + 0.3 * (topic_counts[topic]["last_diff"] / 5.0)
            topic_counts[topic]["mastery"] = round(max(0.15, min(0.98, new_est)), 3)

            total_attempts_count += 1

        # Populate learner_profile table for this student
        conn = get_db_connection()
        with conn:
            for t in TOPICS:
                tc = topic_counts[t]
                # If topic was never attempted in random pick, give baseline
                if tc["attempted"] == 0:
                    tc["mastery"] = round(target_masteries[t], 2)
                    tc["last_diff"] = 1
                conn.execute("""
                    INSERT INTO learner_profile (
                        student_id, topic, mastery_score, last_difficulty, questions_attempted, questions_correct
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (student_id, t, tc["mastery"], tc["last_diff"], tc["attempted"], tc["correct"]))
        conn.close()

    print(f"Database seeded successfully with {len(SAMPLE_QUESTIONS)} questions, "
          f"{len(STUDENT_PERSONAS)} students, and {total_attempts_count} attempts.")

def seed_single_student(student_id: int):
    """Reset attempts and restore profile for a single student."""
    conn = get_db_connection()
    with conn:
        conn.execute("DELETE FROM attempts WHERE student_id = ?;", (student_id,))
        conn.execute("DELETE FROM learner_profile WHERE student_id = ?;", (student_id,))
    conn.close()

    # Check if this student is one of the predefined personas
    persona = next((s for s in STUDENT_PERSONAS if s["id"] == student_id), None)
    if not persona:
        # Custom/new student: initialize with clean default profile (0.35 mastery across topics)
        conn = get_db_connection()
        with conn:
            for t in TOPICS:
                conn.execute("""
                    INSERT INTO learner_profile (
                        student_id, topic, mastery_score, last_difficulty, questions_attempted, questions_correct
                    ) VALUES (?, ?, 0.35, 1, 0, 0)
                """, (student_id, t))
        conn.close()
        print(f"[Seed] Reset data for custom student {student_id} to clean baseline.")
        return

    # Seed attempts and profile for this persona
    conn = get_db_connection()
    q_rows = conn.execute("SELECT id, topic, difficulty FROM questions").fetchall()
    all_questions = [dict(r) for r in q_rows]
    conn.close()

    random.seed(42 + student_id)
    now = datetime.now(timezone.utc)
    target_attempts = persona["target_attempts"]
    target_masteries = persona["target_masteries"]
    topic_counts = {t: {"attempted": 0, "correct": 0, "last_diff": 1, "mastery": 0.20} for t in TOPICS}

    for i in range(target_attempts):
        days_ago = (target_attempts - i) * 0.25
        attempt_time = (now - timedelta(days=days_ago)).isoformat()
        topic = random.choice(TOPICS)
        t_mastery = target_masteries[topic]

        if t_mastery >= 0.75:
            diff_weights = [0.05, 0.15, 0.30, 0.35, 0.15]
        elif t_mastery >= 0.50:
            diff_weights = [0.15, 0.35, 0.35, 0.10, 0.05]
        else:
            diff_weights = [0.45, 0.40, 0.15, 0.00, 0.00]

        chosen_diff = random.choices([1, 2, 3, 4, 5], weights=diff_weights)[0]
        candidate_qs = [q for q in all_questions if q["topic"] == topic and q["difficulty"] == chosen_diff]
        if not candidate_qs:
            candidate_qs = [q for q in all_questions if q["topic"] == topic]
        question = random.choice(candidate_qs)

        ability_delta = (t_mastery * 5.0) - chosen_diff
        p_correct = 1.0 / (1.0 + (2.71828 ** (-1.2 * ability_delta)))
        p_correct = max(0.10, min(0.95, p_correct))
        is_correct = 1 if random.random() < p_correct else 0

        conn = get_db_connection()
        with conn:
            conn.execute("""
                INSERT INTO attempts (student_id, question_id, topic, difficulty, is_correct, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (student_id, question["id"], topic, chosen_diff, is_correct, attempt_time))
        conn.close()

        topic_counts[topic]["attempted"] += 1
        if is_correct:
            topic_counts[topic]["correct"] += 1
        topic_counts[topic]["last_diff"] = chosen_diff

        curr_acc = topic_counts[topic]["correct"] / topic_counts[topic]["attempted"]
        new_est = 0.7 * curr_acc + 0.3 * (topic_counts[topic]["last_diff"] / 5.0)
        topic_counts[topic]["mastery"] = round(max(0.15, min(0.98, new_est)), 3)

    conn = get_db_connection()
    with conn:
        for t in TOPICS:
            tc = topic_counts[t]
            if tc["attempted"] == 0:
                tc["mastery"] = round(target_masteries[t], 2)
                tc["last_diff"] = 1
            conn.execute("""
                INSERT INTO learner_profile (
                    student_id, topic, mastery_score, last_difficulty, questions_attempted, questions_correct
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (student_id, t, tc["mastery"], tc["last_diff"], tc["attempted"], tc["correct"]))
    conn.close()
    print(f"[Seed] Scoped reset complete for student {student_id} ({persona['name']}).")

if __name__ == "__main__":
    seed_database(reset=True)

