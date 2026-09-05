from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Candidate
from schemas.hr import HRChatRequest, HRChatResponse, HRSource, HRInterviewInfo
from Services.hr_rag import hr_rag_chat


router = APIRouter()


# HR CHAT
@router.post("/chat", response_model=HRChatResponse)
def chat(
    request: HRChatRequest,
    db: Session = Depends(get_db)
):
    # Validate message
    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    # Candidate validation
    if request.candidate_id is not None:
        candidate = (
            db.query(Candidate)
            .filter(Candidate.id == request.candidate_id)
            .first()
        )

        if not candidate:
            raise HTTPException(
                status_code=404,
                detail="Candidate not found."
            )

    # RAG
    try:
        result = hr_rag_chat(
            db=db,
            question=request.message,
            candidate_id=request.candidate_id,
            conversation_id=request.conversation_id
        )

        # CV Sources
        sources = [
            HRSource(
                candidate_id=source["candidate_id"],
                candidate_name=source["candidate_name"],
                section=source["section"],
                content=source["content"],
                chunk_id=source["chunk_id"],
                score=source["score"]
            )
            for source in result["sources"]
        ]

        # Interview information
        interview_information = [
            HRInterviewInfo(
                candidate_id=info["candidate_id"],
                candidate_name=info["candidate_name"],
                interview_status=info["interview_status"],
                overall_score=info["overall_score"],
                overview=info["overview"],
                strengths=info["strengths"],
                weaknesses=info["weaknesses"],
                recommendation=info["recommendation"],
                started_at=info["started_at"],
                finished_at=info["finished_at"]
            )
            for info in result["interview_information"]
        ]

        return HRChatResponse(
            answer=result["answer"],
            conversation_id=result["conversation_id"],
            sources=sources,
            interview_information=interview_information
        )

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"RAG error: {str(e)}"
        )