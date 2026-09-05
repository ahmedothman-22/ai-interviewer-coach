# Ai interviewer coach

An AI-powered recruitment platform that automates CV screening, technical interviews, and candidate evaluation using **LLMs and RAG**.
[Ai interviewer coach.pdf](https://github.com/user-attachments/files/31804585/Ai.interviewer.coach.pdf)

## Overview

The platform helps companies simplify the recruitment process by:

* Extracting information from candidate CVs
* Generating personalized technical interview questions
* Conducting AI-powered interviews
* Evaluating candidate answers
* Helping HR search and analyze candidate data using RAG

## Key Features

### Candidate Portal

* Upload CV as PDF
* Automatic CV processing
* Personalized technical interview
* AI-based evaluation and scoring

### HR Dashboard

* View and search candidates
* Review interview scores and feedback
* Ask questions about candidates using an AI assistant
* Retrieve information from CVs and interview data

## Tech Stack

* **Backend:** FastAPI
* **Frontend:** Streamlit
* **Database:** PostgreSQL 
* **Vector Search:** FAISS
* **AI:** LangChain + Cohere
* **PDF Processing:** PyPDF

## Project Structure

```text
ai-recruitment-platform/
├── main.py
├── ui.py
├── requirements.txt
├── database/
├── models/
├── routers/
└── Services/
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
FASTAPI_URL=http://127.0.0.1:8000
COHERE_API_KEY=your_cohere_api_key
```

### 3. Run the Backend
```bash
uvicorn main:app --reload
```

### 4. Run the Frontend
```bash
streamlit run ui.py
```

The application will be available at:

* Frontend: `http://localhost:8501`
* API Docs: `http://127.0.0.1:8000/docs`

## How It Works
**Candidate → CV Upload → CV Processing → Personalized Interview → AI Evaluation → HR Dashboard**

HR can then search candidate information and use the AI assistant to get insights from CVs and interview results.
## Requirements
* Python 3.8+
* PostgreSQL
* Cohere API Key
