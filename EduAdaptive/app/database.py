import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.config import DB_PATH, TOPICS

def get_db_connection() -> sqlite3.Connection:
    """Return an SQLite connection configured for dictionary-style row access."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initialize database tables and indexes."""
    conn = get_db_connection()
    with conn:
        # 1. Questions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY,
                topic TEXT NOT NULL,
                difficulty INTEGER NOT NULL CHECK (difficulty BETWEEN 1 AND 5),
                question_text TEXT NOT NULL,
                options TEXT NOT NULL,          -- JSON encoded list of options e.g. ["A", "B", "C", "D"]
                correct_answer TEXT NOT NULL,
                explanation TEXT NOT NULL DEFAULT ''
            );
        """)

        # 2. Students table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                persona TEXT DEFAULT ''
            );
        """)

        # 3. Attempts table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                difficulty INTEGER NOT NULL,
                is_correct INTEGER NOT NULL CHECK (is_correct IN (0, 1)),
                timestamp TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
            );
        """)

        # 4. Learner Profile table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS learner_profile (
                student_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                mastery_score REAL NOT NULL DEFAULT 0.20 CHECK (mastery_score BETWEEN 0.0 AND 1.0),
                last_difficulty INTEGER NOT NULL DEFAULT 1,
                questions_attempted INTEGER NOT NULL DEFAULT 0,
                questions_correct INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (student_id, topic),
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );
        """)

        # Indexes for fast querying during dashboard and recommendation lookups
        conn.execute("CREATE INDEX IF NOT EXISTS idx_attempts_student ON attempts(student_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_attempts_topic ON attempts(topic);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_questions_topic_diff ON questions(topic, difficulty);")
    conn.close()

# --- Query & Persistence Helpers ---

def get_all_students() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    rows = conn.execute("SELECT id, name, persona FROM students ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_student_by_id(student_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    row = conn.execute("SELECT id, name, persona FROM students WHERE id = ?", (student_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def create_student(student_id: int, name: str, persona: str = "Self-Registered Learner") -> Dict[str, Any]:
    """Create or update a student record with name and persona."""
    conn = get_db_connection()
    with conn:
        conn.execute("""
            INSERT INTO students (id, name, persona)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET name = excluded.name;
        """, (student_id, name, persona))
    conn.close()
    return {"id": student_id, "name": name, "persona": persona}

def init_student_profile(student_id: int, default_mastery: float = 0.35):
    """Initialize default learner profile for a new student across all 4 topics."""
    conn = get_db_connection()
    with conn:
        for topic in TOPICS:
            conn.execute("""
                INSERT INTO learner_profile (
                    student_id, topic, mastery_score, last_difficulty, questions_attempted, questions_correct
                ) VALUES (?, ?, ?, 1, 0, 0)
                ON CONFLICT(student_id, topic) DO NOTHING;
            """, (student_id, topic, default_mastery))
    conn.close()

def reset_student_data(student_id: int):
    """Scoped reset: clear attempts for only this student and restore baseline/seed profile."""
    from app.seed import seed_single_student
    seed_single_student(student_id)


def get_question_by_id(question_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    if isinstance(d["options"], str):
        try:
            d["options"] = json.loads(d["options"])
        except Exception:
            pass
    return d

def get_all_questions() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM questions ORDER BY topic, difficulty, id").fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        if isinstance(d["options"], str):
            try:
                d["options"] = json.loads(d["options"])
            except Exception:
                pass
        result.append(d)
    return result

def get_learner_profile(student_id: int) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT student_id, topic, mastery_score, last_difficulty, questions_attempted, questions_correct
        FROM learner_profile
        WHERE student_id = ?
        ORDER BY topic ASC
    """, (student_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_topic_mastery(student_id: int, topic: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    row = conn.execute("""
        SELECT student_id, topic, mastery_score, last_difficulty, questions_attempted, questions_correct
        FROM learner_profile
        WHERE student_id = ? AND topic = ?
    """, (student_id, topic)).fetchone()
    conn.close()
    return dict(row) if row else None

def upsert_learner_profile(
    student_id: int,
    topic: str,
    mastery_score: float,
    last_difficulty: int,
    questions_attempted: int,
    questions_correct: int
):
    mastery_score = max(0.0, min(1.0, float(mastery_score)))
    conn = get_db_connection()
    with conn:
        conn.execute("""
            INSERT INTO learner_profile (
                student_id, topic, mastery_score, last_difficulty, questions_attempted, questions_correct
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(student_id, topic) DO UPDATE SET
                mastery_score = excluded.mastery_score,
                last_difficulty = excluded.last_difficulty,
                questions_attempted = excluded.questions_attempted,
                questions_correct = excluded.questions_correct;
        """, (student_id, topic, mastery_score, last_difficulty, questions_attempted, questions_correct))
    conn.close()

def record_attempt(
    student_id: int,
    question_id: int,
    topic: str,
    difficulty: int,
    is_correct: int,
    timestamp: Optional[str] = None
) -> int:
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    conn = get_db_connection()
    with conn:
        cursor = conn.execute("""
            INSERT INTO attempts (student_id, question_id, topic, difficulty, is_correct, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, question_id, topic, difficulty, is_correct, timestamp))
        attempt_id = cursor.lastrowid
    conn.close()
    return attempt_id

def get_student_attempts(student_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    query = """
        SELECT a.id, a.student_id, a.question_id, a.topic, a.difficulty, a.is_correct, a.timestamp,
               q.question_text
        FROM attempts a
        LEFT JOIN questions q ON a.question_id = q.id
        WHERE a.student_id = ?
        ORDER BY a.id DESC
    """
    if limit:
        query += f" LIMIT {limit}"
    rows = conn.execute(query, (student_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_recent_correct_question_ids(student_id: int, limit: int = 8) -> List[int]:
    """Retrieve IDs of questions the student successfully answered recently to prevent repetition."""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT question_id FROM attempts
        WHERE student_id = ? AND is_correct = 1
        ORDER BY id DESC
        LIMIT ?
    """, (student_id, limit)).fetchall()
    conn.close()
    return [r["question_id"] for r in rows]

def get_recent_streak_in_topic(student_id: int, topic: str, limit: int = 4) -> int:
    """Calculate the recent directional streak in a given topic: + for consecutive correct, - for wrong."""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT is_correct FROM attempts
        WHERE student_id = ? AND topic = ?
        ORDER BY id DESC
        LIMIT ?
    """, (student_id, topic, limit)).fetchall()
    conn.close()
    if not rows:
        return 0

    first_val = rows[0]["is_correct"]
    streak = 0
    for r in rows:
        if r["is_correct"] == first_val:
            streak += 1
        else:
            break
    return streak if first_val == 1 else -streak

def get_all_attempts_for_training() -> List[Dict[str, Any]]:
    """Fetch all historical attempts joined with profile metrics for model training."""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT a.id, a.student_id, a.question_id, a.topic, a.difficulty, a.is_correct, a.timestamp
        FROM attempts a
        ORDER BY a.id ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
