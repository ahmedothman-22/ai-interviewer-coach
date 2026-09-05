from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Candidate, Interview, InterviewQuestion
from Services.pdf_service import extract_pdf_text
from Services.llm_handel import extract_cv_info, generate_questions
from Services.email_service import send_interview_email
from Services.cv_service import save_cv_chunks
from langchain_text_splitters import RecursiveCharacterTextSplitter


router = APIRouter()


# GET ALL CANDIDATES
@router.get("/")
def get_candidates(
    db: Session = Depends(get_db)
):
    candidates = (
        db.query(Candidate)
        .order_by(Candidate.id.desc())
        .all()
    )

    result = []

    for candidate in candidates:
        # Get latest interview
        interview = (
            db.query(Interview)
            .filter(Interview.candidate_id == candidate.id)
            .order_by(Interview.id.desc())
            .first()
        )

        # Default values
        interview_status = "not_started"
        overall_score = None
        interview_id = None
        started_at = None
        finished_at = None

        # Interview exists
        if interview:
            interview_id = interview.id
            interview_status = interview.status or "pending"
            overall_score = interview.overall_score
            started_at = interview.started_at
            finished_at = interview.finished_at

        # Candidate response
        result.append({
            "id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "phone": candidate.phone,
            "location": candidate.location,
            "cv_file_path": candidate.cv_file_path,
            "interview_id": interview_id,
            "interview_status": interview_status,
            "overall_score": overall_score,
            "started_at": started_at,
            "finished_at": finished_at,
            "created_at": candidate.created_at
        })

    return result


# UPLOAD CV
@router.post("/upload-cv")
async def upload_cv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file was provided."
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    try:
        # 1. READ PDF
        pdf_bytes = await file.read()

        if not pdf_bytes:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty."
            )

        # 2. EXTRACT TEXT FROM PDF
        cv_text = extract_pdf_text(pdf_bytes)

        if not cv_text or not cv_text.strip():
            raise HTTPException(
                status_code=400,
                detail=(
                    "Could not extract text from the CV. "
                    "The PDF may be scanned or image-based."
                )
            )

        print(f"Extracted CV text: {len(cv_text)} characters")

        # 3. EXTRACT STRUCTURED CV INFORMATION
        cv_data = extract_cv_info(cv_text)

        if not cv_data.email or cv_data.email == "Unknown":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Could not find a valid email address "
                    "in the CV."
                )
            )

        # 4. CREATE CANDIDATE
        candidate = Candidate(
            name=cv_data.name,
            email=cv_data.email,
            phone=cv_data.phone,
            location=cv_data.location,
            cv_file_path=file.filename
        )

        db.add(candidate)

        # Flush gives us candidate.id
        # without committing yet.
        db.flush()

        print(f"Candidate created: {candidate.id} - {candidate.name}")

        # 5. CHUNK CV
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        chunks = text_splitter.create_documents(
            [cv_text],
            metadatas=[{
                "candidate_id": candidate.id,
                "candidate_name": candidate.name,
                "source": file.filename
            }]
        )

        print(
            f"Created {len(chunks)} CV chunks "
            f"for candidate {candidate.id}"
        )

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="Could not create CV chunks."
            )

        # 6. SAVE CHUNKS TO POSTGRESQL + FAISS
        save_cv_chunks(
            db=db,
            candidate=candidate,
            chunks=chunks
        )

        print(
            f"CV chunks indexed successfully "
            f"for candidate {candidate.id}"
        )

        # 7. BUILD CANDIDATE DETAILS
        skills = ", ".join(cv_data.skills) if cv_data.skills else "None"
        projects = ", ".join(cv_data.projects) if cv_data.projects else "None"
        certifications = ", ".join(cv_data.certifications) if cv_data.certifications else "None"
        languages = ", ".join(cv_data.languages) if cv_data.languages else "None"

        details = f"""
Candidate Name:
{cv_data.name}

Professional Summary:
{cv_data.summary}

Skills:
{skills}

Projects:
{projects}

Experience:
{cv_data.experience}

Education:
{cv_data.education}

Certifications:
{certifications}

Languages:
{languages}
"""

        # 8. GENERATE INTERVIEW QUESTIONS
        questions = generate_questions(details)

        if not questions:
            raise ValueError(
                "Failed to generate interview questions."
            )

        # Make sure the result is a list
        if isinstance(questions, str):
            questions = [questions]

        # Maximum 5 questions
        questions = questions[:5]

        print(
            f"Generated {len(questions)} interview questions "
            f"for candidate {candidate.id}"
        )

        # 9. CREATE INTERVIEW
        interview = Interview(
            candidate_id=candidate.id,
            job_title="Technical Interview",
            status="pending"
        )

        db.add(interview)

        # Flush so interview.id and interview.token
        # are available.
        db.flush()

        print(f"Interview created: {interview.id}")

        # 10. CREATE INTERVIEW QUESTIONS
        for index, question in enumerate(questions, start=1):
            # Safety check
            if not question:
                continue

            question = str(question).strip()

            if not question:
                continue

            # Create database row
            interview_question = InterviewQuestion(
                interview_id=interview.id,
                question=question,
                question_type="technical",
                difficulty="adaptive",
                question_order=index
            )

            db.add(interview_question)

            print(
                f"Question {index} created: "
                f"{question}"
            )

        # 11. BUILD INTERVIEW URL
        interview_url = (
            "http://localhost:8501/"
            f"?token={interview.token}"
        )

        print(f"Interview URL generated: {interview_url}")

        # 12. COMMIT DATABASE
        db.commit()

        # 13. SEND EMAIL
        try:
            send_interview_email(
                candidate_email=cv_data.email,
                candidate_name=cv_data.name,
                interview_url=interview_url
            )

            email_status = "sent"

            print(f"Interview email sent to {cv_data.email}")

        except Exception as email_error:
            # Candidate + interview are already stored.
            email_status = "failed"

            print(
                f"WARNING: Could not send email: "
                f"{email_error}"
            )

        # 14. RETURN RESPONSE
        return {
            "message": (
                "CV processed successfully. "
                "Interview invitation created."
            ),
            "candidate_id": candidate.id,
            "candidate_name": candidate.name,
            "email": candidate.email,
            "interview_id": interview.id,
            "questions_generated": len(questions),
            "questions": questions,
            "email_status": email_status,
            "indexed_chunks": len(chunks)
        }

    # HTTP EXCEPTION
    except HTTPException:
        db.rollback()
        raise

    # GENERAL EXCEPTION
    except Exception as e:
        db.rollback()

        print(f"ERROR while processing CV: {e}")

        raise HTTPException(
            status_code=500,
            detail=f"Error while processing CV: {str(e)}"
        )


# GET CANDIDATE INTERVIEW
@router.get("/{candidate_id}/interview/{interview_id}")
def get_candidate_interview(
    candidate_id: int,
    interview_id: int,
    db: Session = Depends(get_db)
):
    interview = (
        db.query(Interview)
        .filter(
            Interview.id == interview_id,
            Interview.candidate_id == candidate_id
        )
        .first()
    )

    if not interview:
        raise HTTPException(
            status_code=404,
            detail="Interview not found."
        )

    return {
        "interview_id": interview.id,
        "candidate_id": interview.candidate_id,
        "token": interview.token,
        "status": interview.status
    }