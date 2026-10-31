# EduAdaptive: Personalized Practice Question Recommendation Engine
### UN SDG 4 (Quality Education) Hackathon Prototype

EduAdaptive is a full-stack adaptive learning platform where **Machine Learning directly drives the educational experience**. It assesses student competency across core mathematical subjects, predicts question difficulty suitability, and dynamically recommends questions in the student's **Zone of Proximal Development (ZPD)** to close learning gaps and accelerate mastery.

---

## 🌟 Key Features

1. **ML Mastery Classifier (`scikit-learn`)**:
   - Calibrated `LogisticRegression` that predicts the probability \(P(\text{correct})\) a student will solve a given question.
   - Features include:
     - `topic_accuracy`: Student's historical accuracy in that topic (with Laplace smoothing).
     - `recent_streak`: Momentum tracker (-3 to +3).
     - `difficulty`: Normalized question cognitive load (1 to 5).
     - `questions_attempted`: Log-scaled cumulative practice volume.
2. **Adaptive Recommender (Vygotsky's ZPD Engine)**:
   - Identifies and prioritizes topics with the lowest mastery score to directly tackle educational inequality (SDG 4.1).
   - Targets the learning sweet spot (\(P(\text{success}) \approx 0.60 - 0.75\)) so learning is challenging without being frustrating.
   - Suppresses recently answered questions to prevent boring repetition.
   - Generates transparent, human-readable Explainable AI (XAI) rationale for each recommendation.
3. **Dynamic Online Mastery Update**:
   - Real-time Bayesian residual update after every attempt:
     $$\Delta M = \eta \cdot (\text{actual} - \text{predicted}) \cdot \text{weight}(\text{difficulty})$$
   - Solving a Level 5 problem yields significant mastery growth; failing a foundational problem prompts supportive scaffolding.
4. **Interactive Single-Page Dashboard**:
   - **Practice Mode**: Live question solving with multiple-choice buttons, instant feedback, and real-time mastery diff pill.
   - **Learner Analytics**: Topic Mastery Radar/Bar Chart (Chart.js), Adaptive Difficulty Progression Timeline, KPI cards, and attempt log table.
   - **Persona Switcher**: Seamlessly switch between 5 seeded student personas (e.g. Alice the Prodigy, Bob struggling with Probability).
   - **1-Click Reset**: Instant database reset button for live hackathon presentations.

---

## 📂 Architecture Overview

```
ML hackathon/
├── app/
│   ├── config.py              # System paths, constants, ML hyperparameters
│   ├── database.py            # SQLite schema (4 tables), indexes, helper queries
│   ├── models.py              # Pydantic schemas for requests/responses
│   ├── seed.py                # Database seeder (~40 questions, ~150 attempts, 5 students)
│   ├── ml/
│   │   ├── classifier.py      # Logistic Regression mastery classifier & feature extraction
│   │   └── recommender.py     # ZPD adaptive recommendation engine with XAI
│   ├── routes/
│   │   ├── attempts.py        # POST /attempt
│   │   ├── recommendations.py # GET /next-questions/{student_id}
│   │   └── dashboard.py       # GET /dashboard/{student_id}, GET /students, POST /reset
│   ├── static/
│   │   ├── index.html         # Modern single-page app
│   │   ├── styles.css         # Responsive styling (SDG 4 theme)
│   │   └── app.js             # Frontend API client & Chart.js logic
│   └── main.py                # FastAPI app & static file mounting
├── tests/
│   └── test_engine.py         # Automated pytest suite (Seeding, ML, Recommender, Endpoints)
├── requirements.txt           # Python dependencies
└── README.md                  # This documentation
```

---

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Seed Database (Optional - Happens Automatically on First Launch)
```bash
python -m app.seed
```

### 3. Run the Server
```bash
python -m uvicorn app.main:app --port 8000 --reload
```
Open your browser and navigate to:
👉 **[http://localhost:8000](http://localhost:8000)**

API Documentation (Swagger UI) is available at:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## 🧪 Running the Test Suite

```bash
python -m pytest tests/test_engine.py -v
```

---

## 🎤 Hackathon Pitch & Live Demo Guide

1. **Set the Stage**:
   *"Today, students drop out or lose interest because one-size-fits-all education leaves lagging students frustrated and advanced students bored. SDG 4 demands equitable, quality education for all."*
2. **Show Bob Jones (Struggling Persona)**:
   - Select **Bob Jones** from the top dropdown.
   - Go to **Learner Analytics**: Point out that Bob is strong in Algebra (78%) and Number Systems (75%), but has an acute gap in **Probability (28%)**.
3. **Show Adaptive AI Recommendation**:
   - Switch to **Adaptive Practice**: The AI has identified Probability as the focus topic and served a Level 2 question with an explainable AI rationale:
     *"Priority Focus: Your mastery in Probability is 28%. Level 2 is selected to strengthen core concepts (Predicted success rate: 71%)."*
4. **Answer the Question Live**:
   - Choose the correct answer and click **Submit Answer**.
   - Show the judges the instant feedback and the **Real-time Mastery Update** badge:
     `Probability: 28% ➔ 41% (+13%)`
   - Notice how the analytics chart and upcoming queue reflect this immediately.
5. **Show Alice Smith (High Achiever)**:
   - Switch to **Alice Smith**: The system instantly adapts, serving Level 4 and 5 problems.
6. **Reset Anytime**:
   - Click **Reset Demo** in the top bar to return to pristine seed state at any point.
