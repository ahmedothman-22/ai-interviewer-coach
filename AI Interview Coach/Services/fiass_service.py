import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_cohere import CohereEmbeddings
from langchain_core.documents import Document

load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")

if not COHERE_API_KEY:
    raise ValueError("COHERE_API_KEY is not set in .env")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "embed-v4.0")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAISS_PATH = os.path.join(BASE_DIR, "faiss_store")

os.makedirs(FAISS_PATH, exist_ok=True)

embeddings = CohereEmbeddings(
    model=EMBEDDING_MODEL,
    cohere_api_key=COHERE_API_KEY
)


def faiss_exists():
    return os.path.exists(os.path.join(FAISS_PATH, "index.faiss"))


def add_documents_to_faiss(documents: list[Document]):
    if not documents:
        return

    # Existing index
    if faiss_exists():
        vector_store = FAISS.load_local(
            FAISS_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )

        vector_store.add_documents(documents)

    # New index
    else:
        vector_store = FAISS.from_documents(
            documents,
            embeddings
        )

    # Save
    vector_store.save_local(FAISS_PATH)


def search_faiss(query: str, k: int = 8):
    if not faiss_exists():
        return []

    vector_store = FAISS.load_local(
        FAISS_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )

    results = (
        vector_store
        .similarity_search_with_score(query, k=k)
    )

    return results

