from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "recommendation_engine.db"
MODEL_PATH = DATA_DIR / "mastery_classifier.joblib"

# Topics configuration
TOPICS = ["Algebra", "Geometry", "Probability", "Number Systems"]

# Difficulty scale
MIN_DIFFICULTY = 1
MAX_DIFFICULTY = 5

# ML & Recommender Parameters
# Zone of Proximal Development (ZPD) target probability window
ZPD_TARGET_PROB = 0.70
ZPD_PROB_WINDOW = 0.15  # Acceptable range: 0.55 to 0.85

# Bayesian / Exponential moving average update learning rate
MASTERY_LEARNING_RATE = 0.25

# Question history exclusion limit (avoid repeating recently mastered questions)
RECENT_CORRECT_EXCLUDE_LIMIT = 8
