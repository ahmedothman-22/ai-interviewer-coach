from sqlalchemy import text

from .connection import engine, Base
from .models import (
    Candidate,
    CVChunk,
    Interview,
    InterviewQuestion,
    CandidateAnswer,
    Evaluation
)


def init_database():
    with engine.begin() as connection:
        # Enable pgvector
        connection.execute(
            text("CREATE EXTENSION IF NOT EXISTS vector"))

    # Create tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")


if __name__ == "__main__":
    init_database()