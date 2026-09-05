from sqlalchemy.orm import Session
from langchain_core.documents import Document
from database.models import Candidate, CVChunk
from Services.fiass_service import add_documents_to_faiss


def save_cv_chunks(
    db: Session,
    candidate: Candidate,
    chunks
):
    """
    Save CV chunks to PostgreSQL and index them in FAISS.
    """

    if not chunks:
        return []

    faiss_documents = []

    for i, chunk in enumerate(chunks):
        metadata = chunk.metadata if chunk.metadata else {}

        # Save chunk in PostgreSQL
        chunk_record = CVChunk(
            candidate_id=candidate.id,
            content=chunk.page_content,
            section=metadata.get("section", "CV"),
            chunk_index=i,
            chunk_metadata=metadata
        )

        db.add(chunk_record)

        # We need chunk_record.id for FAISS metadata.
        db.flush()

        # Create LangChain Document
        document = Document(
            page_content=chunk.page_content,
            metadata={
                "candidate_id": candidate.id,
                "candidate_name": candidate.name,
                "chunk_id": chunk_record.id,
                "section": chunk_record.section,
                "chunk_index": i
            }
        )

        faiss_documents.append(document)

    # Add documents to FAISS
    add_documents_to_faiss(faiss_documents)

    print(
        f"Added {len(faiss_documents)} "
        f"documents to FAISS."
    )

    # IMPORTANT:
    # No db.commit() here.
    #
    # The caller controls the transaction.

    return faiss_documents