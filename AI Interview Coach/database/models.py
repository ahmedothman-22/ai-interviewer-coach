import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    JSON
)
from sqlalchemy.orm import relationship
from database.connection import Base


# CANDIDATE
class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    name = Column(
        String,
        nullable=False
    )
    email = Column(
        String,
        nullable=True
    )
    phone = Column(
        String,
        nullable=True
    )
    location = Column(
        String,
        nullable=True
    )
    cv_file_path = Column(
        String,
        nullable=True
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )
    # Relationships
    cv_chunks = relationship(
        "CVChunk",
        back_populates="candidate",
        cascade="all, delete-orphan"
    )
    interviews = relationship(
        "Interview",
        back_populates="candidate",
        cascade="all, delete-orphan"
    )
# CV CHUNK
class CVChunk(Base):
    __tablename__ = "cv_chunks"
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    candidate_id = Column(
        Integer,
        ForeignKey(
            "candidates.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )
    content = Column(
        Text,
        nullable=False
    )
    section = Column(
        String,
        nullable=True
    )
    chunk_index = Column(
        Integer,
        nullable=True
    )
    chunk_metadata = Column(
        JSON,
        nullable=True
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # Relationship
    candidate = relationship(
        "Candidate",
        back_populates="cv_chunks"
    )


# INTERVIEW
class Interview(Base):
    __tablename__ = "interviews"
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    candidate_id = Column(
        Integer,
        ForeignKey(
            "candidates.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    # Unique secret token used in candidate interview URL

    token = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: uuid.uuid4().hex
    )

    job_title = Column(
        String,
        nullable=True
    )

    job_description = Column(
        Text,
        nullable=True
    )

    status = Column(
        String,
        default="pending"
    )

    overall_score = Column(
        String,
        nullable=True
    )

    started_at = Column(
        DateTime,
        nullable=True
    )

    finished_at = Column(
        DateTime,
        nullable=True
    )

    # Relationships

    candidate = relationship(
        "Candidate",
        back_populates="interviews"
    )

    questions = relationship(
        "InterviewQuestion",
        back_populates="interview",
        cascade="all, delete-orphan"
    )


# INTERVIEW QUESTION
class InterviewQuestion(Base):

    __tablename__ = "interview_questions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    interview_id = Column(
        Integer,
        ForeignKey(
            "interviews.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    question = Column(
        Text,
        nullable=False
    )

    question_type = Column(
        String,
        nullable=True
    )

    difficulty = Column(
        String,
        nullable=True
    )

    cv_chunk_ids = Column(
        JSON,
        nullable=True
    )

    question_order = Column(
        Integer,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # Relationships

    interview = relationship(
        "Interview",
        back_populates="questions"
    )

    answer = relationship(
        "CandidateAnswer",
        back_populates="question",
        uselist=False,
        cascade="all, delete-orphan"
    )


# CANDIDATE ANSWER
class CandidateAnswer(Base):

    __tablename__ = "candidate_answers"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    question_id = Column(
        Integer,
        ForeignKey(
            "interview_questions.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        unique=True
    )

    answer = Column(
        Text,
        nullable=False
    )

    answered_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # Relationships

    question = relationship(
        "InterviewQuestion",
        back_populates="answer"
    )

    evaluation = relationship(
        "Evaluation",
        back_populates="answer",
        uselist=False,
        cascade="all, delete-orphan"
    )


# EVALUATION
class Evaluation(Base):
    __tablename__ = "evaluations"
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    answer_id = Column(
        Integer,
        ForeignKey(
            "candidate_answers.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        unique=True
    )

    technical_score = Column(
        String,
        nullable=True
    )

    relevance_score = Column(
        String,
        nullable=True
    )

    depth_score = Column(
        String,
        nullable=True
    )

    communication_score = Column(
        String,
        nullable=True
    )

    problem_solving_score = Column(
        String,
        nullable=True
    )

    overall_score = Column(
        String,
        nullable=True
    )

    feedback = Column(
        Text,
        nullable=True
    )

    strengths = Column(
        JSON,
        nullable=True
    )

    weaknesses = Column(
        JSON,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # Relationship

    answer = relationship(
        "CandidateAnswer",
        back_populates="evaluation"
    )


# HR CONVERSATION
class HRConversation(Base):

    __tablename__ = "hr_conversations"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    messages = relationship(
        "HRMessage",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )


# HR MESSAGE

class HRMessage(Base):

    __tablename__ = "hr_messages"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    conversation_id = Column(
        Integer,
        ForeignKey(
            "hr_conversations.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    role = Column(
        String,
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # Relationship

    conversation = relationship(
        "HRConversation",
        back_populates="messages"
    )

