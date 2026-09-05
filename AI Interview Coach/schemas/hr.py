from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class HRChatRequest(BaseModel):
    message: str
    candidate_id: Optional[int] = None
    conversation_id: Optional[int] = None


class HRSource(BaseModel):
    candidate_id: int
    candidate_name: str
    section: Optional[str] = None
    content: str
    chunk_id: int
    score: Optional[float] = None


class HRInterviewInfo(BaseModel):
    candidate_id: int
    candidate_name: str
    interview_status: str
    overall_score: Optional[str] = None
    overview: Optional[str] = None
    strengths: List[str] = []
    weaknesses: List[str] = []
    recommendation: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class HRChatResponse(BaseModel):
    answer: str
    conversation_id: int
    sources: List[HRSource]
    interview_information: List[HRInterviewInfo] = []