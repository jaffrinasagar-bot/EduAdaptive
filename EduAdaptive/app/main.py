from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db, get_all_questions
from app.seed import seed_database
from app.ml.classifier import classifier_instance
from app.routes.attempts import router as attempts_router
from app.routes.recommendations import router as recommendations_router
from app.routes.dashboard import router as dashboard_router

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB and train ML model if not already trained
    init_db()
    existing_questions = get_all_questions()
    if len(existing_questions) == 0:
        print("[Startup] Seeding database for first-time launch...")
        seed_database(reset=True)
    classifier_instance.load_or_train()
    print("[Startup] Recommendation Engine & ML system ready.")
    yield
    # Shutdown logic if any
    pass

app = FastAPI(
    title="Personalized Practice Question Recommendation Engine",
    description="SDG 4 (Quality Education) Hackathon Prototype: Adaptive Learning Driven by Machine Learning",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(attempts_router)
app.include_router(recommendations_router)
app.include_router(dashboard_router)

# Mount Frontend Static Assets (Served at root '/')
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
