from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.connection import get_db
from database.models import Interview, InterviewQuestion, CandidateAnswer, Evaluation
from Services.llm_handel import eval_answer


router = APIRouter()


class AnswerRequest(BaseModel):
    answer: str


def get_next_unanswered_question(
    interview_id: int,
    db: Session
):
    """
    Return the first interview question that does not
    have a candidate answer yet.
    """

    questions = (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.interview_id == interview_id)
        .order_by(InterviewQuestion.question_order)
        .all()
    )

    for question in questions:
        existing_answer = (
            db.query(CandidateAnswer)
            .filter(CandidateAnswer.question_id == question.id)
            .first()
        )

        if existing_answer is None:
            return question

    return None


@router.get("/{token}")
def get_interview(
    token: str,
    db: Session = Depends(get_db)
):
    interview = (
        db.query(Interview)
        .filter(Interview.token == token)
        .first()
    )

    if not interview:
        raise HTTPException(
            status_code=404,
            detail="Interview not found."
        )

    # Already completed
    if interview.status == "completed":
        raise HTTPException(
            status_code=400,
            detail="This interview has already been completed."
        )

    # Find next unanswered question
    question = get_next_unanswered_question(
        interview_id=interview.id,
        db=db
    )

    if not question:
        # No questions remain.
        # This should normally only happen if the interview
        # was completed previously.

        interview.status = "completed"

        if interview.finished_at is None:
            interview.finished_at = datetime.utcnow()

        db.commit()

        raise HTTPException(
            status_code=400,
            detail="All interview questions have been answered."
        )

    # Mark interview as started
    if interview.started_at is None:
        interview.started_at = datetime.utcnow()
        interview.status = "in_progress"

        db.commit()
        db.refresh(interview)

    # Count questions
    total_questions = (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.interview_id == interview.id)
        .count()
    )

    answered_questions = (
        db.query(CandidateAnswer)
        .join(
            InterviewQuestion,
            CandidateAnswer.question_id == InterviewQuestion.id
        )
        .filter(InterviewQuestion.interview_id == interview.id)
        .count()
    )

    # Current question number
    question_number = question.question_order

    # Response
    return {
        "candidate_id": interview.candidate.id,
        "candidate_name": interview.candidate.name,
        "interview_id": interview.id,
        "question_id": question.id,
        "question": question.question,
        "question_number": question_number,
        "answered_questions": answered_questions,
        "total_questions": total_questions,
        "status": interview.status
    }


@router.post("/{token}/answer")
def submit_answer(
    token: str,
    request: AnswerRequest,
    db: Session = Depends(get_db)
):
    # Validate answer
    if not request.answer.strip():
        raise HTTPException(
            status_code=400,
            detail="Answer cannot be empty."
        )

    # Find interview
    interview = (
        db.query(Interview)
        .filter(Interview.token == token)
        .first()
    )

    if not interview:
        raise HTTPException(
            status_code=404,
            detail="Interview not found."
        )

    if interview.status == "completed":
        raise HTTPException(
            status_code=400,
            detail="This interview has already been completed."
        )

    # Find CURRENT unanswered question
    question = get_next_unanswered_question(
        interview_id=interview.id,
        db=db
    )

    if not question:
        raise HTTPException(
            status_code=400,
            detail="No unanswered questions remain."
        )

    # Evaluate answer
    try:
        evaluation = eval_answer(
            question=question.question,
            answer=request.answer
        )

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Answer evaluation failed: {str(e)}"
        )

    # Save candidate answer
    candidate_answer = CandidateAnswer(
        question_id=question.id,
        answer=request.answer,
        answered_at=datetime.utcnow()
    )

    db.add(candidate_answer)
    db.flush()

    # Save evaluation
    missing_points = (
        evaluation.missing_points
        if evaluation.missing_points
        else []
    )

    mistakes = (
        evaluation.mistakes
        if evaluation.mistakes
        else []
    )

    weaknesses = missing_points + mistakes

    evaluation_record = Evaluation(
        answer_id=candidate_answer.id,
        technical_score=str(evaluation.technical_correctness),
        relevance_score=str(evaluation.relevance),
        depth_score=str(evaluation.depth),
        overall_score=str(evaluation.score),
        feedback=evaluation.overall_feedback,
        strengths=evaluation.strengths if evaluation.strengths else [],
        weaknesses=weaknesses
    )

    db.add(evaluation_record)
    db.flush()

    # Find next question
    next_question = get_next_unanswered_question(
        interview_id=interview.id,
        db=db
    )

    # Current evaluation response
    current_evaluation = {
        "score": evaluation.score,
        "technical_correctness": evaluation.technical_correctness,
        "relevance": evaluation.relevance,
        "depth": evaluation.depth,
        "strengths": evaluation.strengths,
        "missing_points": evaluation.missing_points,
        "mistakes": evaluation.mistakes,
        "overall_feedback": evaluation.overall_feedback
    }

    # MORE QUESTIONS REMAIN
    if next_question:
        interview.status = "in_progress"
        db.commit()

        # Count answered questions
        answered_questions = (
            db.query(CandidateAnswer)
            .join(
                InterviewQuestion,
                CandidateAnswer.question_id == InterviewQuestion.id
            )
            .filter(InterviewQuestion.interview_id == interview.id)
            .count()
        )

        total_questions = (
            db.query(InterviewQuestion)
            .filter(InterviewQuestion.interview_id == interview.id)
            .count()
        )

        return {
            "message": "Answer submitted successfully.",
            "completed": False,
            "current_question_id": question.id,
            "current_question_number": question.question_order,
            "evaluation": current_evaluation,
            "next_question_id": next_question.id,
            "next_question": next_question.question,
            "next_question_number": next_question.question_order,
            "answered_questions": answered_questions,
            "total_questions": total_questions,
            "status": interview.status
        }

    # ALL QUESTIONS COMPLETED
    evaluations = (
        db.query(Evaluation)
        .join(
            CandidateAnswer,
            Evaluation.answer_id == CandidateAnswer.id
        )
        .join(
            InterviewQuestion,
            CandidateAnswer.question_id == InterviewQuestion.id
        )
        .filter(InterviewQuestion.interview_id == interview.id)
        .all()
    )

    # Calculate final score
    scores = []

    for item in evaluations:
        try:
            score = float(item.overall_score)
            scores.append(score)

        except (ValueError, TypeError):
            continue

    if scores:
        final_score = sum(scores) / len(scores)
        final_score = round(final_score, 2)

    else:
        final_score = float(evaluation.score)

    # Complete interview
    interview.status = "completed"
    interview.finished_at = datetime.utcnow()
    interview.overall_score = str(final_score)

    db.commit()

    # FINAL RESPONSE
    return {
        "message": "Interview completed successfully.",
        "completed": True,
        "current_question_id": question.id,
        "current_question_number": question.question_order,
        "total_questions": len(evaluations),
        "final_score": final_score,
        "evaluation": current_evaluation,
        "status": "completed"
    }