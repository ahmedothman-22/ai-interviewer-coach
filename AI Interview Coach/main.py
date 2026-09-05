from fastapi import FastAPI
from database.connection import Base, engine
from database import models
from routers import candidates, hr, interview

app = FastAPI(
    title="AI Recruitment Platform",
    description="AI-powered recruitment and HR RAG system",
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)

app.include_router(
    candidates.router,
    prefix="/candidates",
    tags=["Candidates"]
)

app.include_router(
    interview.router,
    prefix="/interview",
    tags=["Interview"]
)

app.include_router(
    hr.router,
    prefix="/hr",
    tags=["HR"]
)


@app.get("/")
def root():
    return {
        "message": "AI Recruitment API is running",
        "status": "success"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }