import os
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from sqlalchemy.orm import Session
from langchain_cohere import ChatCohere

from database.models import (
    Candidate,
    CVChunk,
    Interview,
    InterviewQuestion,
    CandidateAnswer,
    Evaluation,
    HRConversation,
    HRMessage
)

from Services.fiass_service import search_faiss


# ENVIRONMENT
load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")

if not COHERE_API_KEY:
    raise ValueError("COHERE_API_KEY is not set in .env")

LLM_MODEL = os.getenv("LLM_MODEL", "command-a-03-2025")


# LLM
llm = ChatCohere(
    model=LLM_MODEL,
    temperature=0,
    cohere_api_key=COHERE_API_KEY
)


# RETRIEVE CV CHUNKS
def retrieve_cv_chunks(
    db: Session,
    question: str,
    candidate_id: Optional[int] = None,
    top_k: int = 8
):
    results = search_faiss(query=question, k=top_k * 3)

    if not results:
        return []

    retrieved = []

    for document, score in results:
        metadata = document.metadata
        chunk_id = metadata.get("chunk_id")
        document_candidate_id = metadata.get("candidate_id")

        # Candidate filtering
        if (
            candidate_id is not None
            and document_candidate_id != candidate_id
        ):
            continue

        if chunk_id is None:
            continue

        # PostgreSQL CV chunk
        chunk = (
            db.query(CVChunk)
            .filter(CVChunk.id == chunk_id)
            .first()
        )

        if not chunk:
            continue

        # Candidate
        candidate = (
            db.query(Candidate)
            .filter(Candidate.id == chunk.candidate_id)
            .first()
        )

        if not candidate:
            continue

        retrieved.append({
            "candidate_id": candidate.id,
            "candidate_name": candidate.name,
            "chunk_id": chunk.id,
            "section": chunk.section,
            "content": chunk.content,
            "score": float(score),
            "source_type": "CV"
        })

        if len(retrieved) >= top_k:
            break

    return retrieved


# INTERVIEW INFORMATION
def get_candidate_interview_info(
    db: Session,
    candidate_id: int
) -> Optional[Dict[str, Any]]:
    candidate = (
        db.query(Candidate)
        .filter(Candidate.id == candidate_id)
        .first()
    )

    if not candidate:
        return None

    # Get latest interview
    interview = (
        db.query(Interview)
        .filter(Interview.candidate_id == candidate_id)
        .order_by(Interview.id.desc())
        .first()
    )

    # Candidate has never had an interview
    if not interview:
        return {
            "candidate_id": candidate.id,
            "candidate_name": candidate.name,
            "interview_status": "Not Interviewed",
            "overall_score": None,
            "overview": None,
            "strengths": [],
            "weaknesses": [],
            "recommendation": None,
            "started_at": None,
            "finished_at": None
        }

    # Get all questions
    questions = (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.interview_id == interview.id)
        .all()
    )

    evaluations = []

    for question in questions:
        answer = (
            db.query(CandidateAnswer)
            .filter(CandidateAnswer.question_id == question.id)
            .first()
        )

        if not answer:
            continue

        evaluation = (
            db.query(Evaluation)
            .filter(Evaluation.answer_id == answer.id)
            .first()
        )

        if evaluation:
            evaluations.append(evaluation)

    # Collect strengths
    strengths = []

    for evaluation in evaluations:
        if evaluation.strengths:
            if isinstance(evaluation.strengths, list):
                strengths.extend(evaluation.strengths)

    # Remove duplicates
    strengths = list(dict.fromkeys(strengths))

    # Collect weaknesses
    weaknesses = []

    for evaluation in evaluations:
        if evaluation.weaknesses:
            if isinstance(evaluation.weaknesses, list):
                weaknesses.extend(evaluation.weaknesses)

    weaknesses = list(dict.fromkeys(weaknesses))

    # Collect feedback
    feedback = []

    for evaluation in evaluations:
        if evaluation.feedback:
            feedback.append(evaluation.feedback)

    # Build overview
    if feedback:
        overview = " ".join(feedback)

    elif interview.status == "completed":
        overview = (
            "The candidate completed the interview, "
            "but no detailed evaluation feedback was found."
        )

    else:
        overview = (
            "The candidate has an interview record, "
            "but the interview has not been completed."
        )

    # Recommendation
    recommendation = None

    if interview.overall_score:
        try:
            score = float(interview.overall_score)

            if score >= 85:
                recommendation = "Strong Hire"
            elif score >= 70:
                recommendation = "Consider"
            elif score >= 50:
                recommendation = "Weak Consideration"
            else:
                recommendation = "Reject"

        except (ValueError, TypeError):
            recommendation = None

    # Return
    return {
        "candidate_id": candidate.id,
        "candidate_name": candidate.name,
        "interview_id": interview.id,
        "interview_status": interview.status,
        "overall_score": interview.overall_score,
        "overview": overview,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendation": recommendation,
        "started_at": interview.started_at,
        "finished_at": interview.finished_at
    }


# RETRIEVE INTERVIEW INFORMATION FOR MULTIPLE CANDIDATES
def retrieve_interview_information(
    db: Session,
    sources: List[Dict[str, Any]],
    candidate_id: Optional[int] = None
):
    candidate_ids = set()

    # Explicit candidate
    if candidate_id is not None:
        candidate_ids.add(candidate_id)

    # Candidates found through FAISS
    for source in sources:
        source_candidate_id = source.get("candidate_id")

        if source_candidate_id is not None:
            candidate_ids.add(source_candidate_id)

    # No candidates found
    if not candidate_ids:
        return []

    interview_information = []

    for cid in candidate_ids:
        info = get_candidate_interview_info(
            db=db,
            candidate_id=cid
        )

        if info:
            interview_information.append(info)

    return interview_information


# CONVERSATION
def get_or_create_conversation(
    db: Session,
    conversation_id: Optional[int] = None
):
    if conversation_id is not None:
        conversation = (
            db.query(HRConversation)
            .filter(HRConversation.id == conversation_id)
            .first()
        )

        if conversation:
            return conversation

    conversation = HRConversation()
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


# HISTORY
def get_conversation_history(
    db: Session,
    conversation_id: int,
    limit: int = 10
):
    messages = (
        db.query(HRMessage)
        .filter(HRMessage.conversation_id == conversation_id)
        .order_by(HRMessage.created_at.desc())
        .limit(limit)
        .all()
    )

    messages.reverse()

    return messages


# BUILD CV CONTEXT
def build_cv_context(sources):
    if not sources:
        return "No relevant CV information was found."

    context = []

    for i, source in enumerate(sources, start=1):
        context.append(
            f"""
CV SOURCE {i}

Candidate:
{source["candidate_name"]}

Candidate ID:
{source["candidate_id"]}

Section:
{source["section"] or "Unknown"}

CV Content:
{source["content"]}
"""
        )

    return "\n".join(context)


# BUILD INTERVIEW CONTEXT
def build_interview_context(interview_information):
    if not interview_information:
        return "No interview information was found."

    context = []

    for info in interview_information:
        context.append(
            f"""
INTERVIEW INFORMATION

Candidate:
{info["candidate_name"]}

Candidate ID:
{info["candidate_id"]}

Interview Status:
{info["interview_status"]}

Overall Score:
{info["overall_score"] or "Not available"}

Interview Overview:
{info["overview"] or "Not available"}

Strengths:
{", ".join(info["strengths"]) if info["strengths"] else "Not available"}

Weaknesses:
{", ".join(info["weaknesses"]) if info["weaknesses"] else "Not available"}

Recommendation:
{info["recommendation"] or "Not available"}

Interview Started:
{info["started_at"] or "Not available"}

Interview Finished:
{info["finished_at"] or "Not available"}
"""
        )

    return "\n".join(context)


# CONVERSATION TEXT
def build_conversation(history):
    if not history:
        return "No previous conversation."

    messages = []

    for message in history:
        messages.append(
            f"{message.role.upper()}: {message.content}"
        )

    return "\n".join(messages)


# GENERATE ANSWER
def generate_answer(
    question: str,
    sources,
    interview_information,
    history
):
    cv_context = build_cv_context(sources)
    interview_context = build_interview_context(interview_information)
    conversation = build_conversation(history)

    prompt = f"""
You are an AI HR recruitment assistant.

Your task is to answer HR questions about candidates.

You have TWO sources of information:

1. Candidate CV information retrieved from FAISS.
2. Candidate interview information retrieved from PostgreSQL.

IMPORTANT RULES:

1. Use ONLY the provided CV and interview information.
2. Never invent candidate information.
3. Never assume information that is not present.
4. Do not confuse information between candidates.
5. Always mention the candidate name when appropriate.
6. Interview status, score, strengths, weaknesses,
   recommendation and interview overview MUST come
   from the interview information.
7. CV skills and experience MUST come from CV information.
8. If interview information is unavailable, say so clearly.
9. If a candidate has no interview record, say:
   "The candidate has not been interviewed yet."
10. If the score is unavailable, say:
   "The interview score is not available."
11. If the requested information is unavailable,
   say:
   "I couldn't find that information in the available
   candidate records."
12. Be concise and professional.
13. When HR asks for a candidate overview, combine
   CV information and interview information.
14. When HR asks about interview performance,
   prioritize PostgreSQL interview/evaluation data.
15. Do not treat CV chunks as interview results.

============================================================
CV INFORMATION
============================================================

{cv_context}


============================================================
INTERVIEW INFORMATION
============================================================

{interview_context}


============================================================
PREVIOUS CONVERSATION
============================================================

{conversation}


============================================================
HR QUESTION
============================================================

{question}


============================================================
ANSWER
============================================================
"""

    response = llm.invoke(prompt)

    return response.content


# HR RAG CHAT
def hr_rag_chat(
    db: Session,
    question: str,
    candidate_id: Optional[int] = None,
    conversation_id: Optional[int] = None
):
    # Conversation
    conversation = get_or_create_conversation(
        db=db,
        conversation_id=conversation_id
    )

    # History
    history = get_conversation_history(
        db=db,
        conversation_id=conversation.id
    )

    # CV Retrieval
    sources = retrieve_cv_chunks(
        db=db,
        question=question,
        candidate_id=candidate_id,
        top_k=8
    )

    # Interview Retrieval
    interview_information = retrieve_interview_information(
        db=db,
        sources=sources,
        candidate_id=candidate_id
    )

    # Generate
    answer = generate_answer(
        question=question,
        sources=sources,
        interview_information=interview_information,
        history=history
    )

    # Save user message
    user_message = HRMessage(
        conversation_id=conversation.id,
        role="user",
        content=question
    )

    db.add(user_message)

    # Save assistant message
    assistant_message = HRMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=answer
    )

    db.add(assistant_message)
    db.commit()

    return {
        "answer": answer,
        "conversation_id": conversation.id,
        "sources": sources,
        "interview_information": interview_information
    }