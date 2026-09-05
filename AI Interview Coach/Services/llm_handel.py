from models.cv_extracted import CVSchema, AnswerEvaluation
from dotenv import load_dotenv
from langchain_cohere import ChatCohere
import os
import re


# LOAD ENVIRONMENT VARIABLES
load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "command-a-03-2025")

if not COHERE_API_KEY:
    raise ValueError("COHERE_API_KEY is not set in .env")


# LLM
llm = ChatCohere(
    model=MODEL_NAME,
    temperature=0,
    cohere_api_key=COHERE_API_KEY
)


# STRUCTURED OUTPUTS
llm_structured = llm.with_structured_output(CVSchema)
llm_evaluate = llm.with_structured_output(AnswerEvaluation)


# 1. GENERATE INTERVIEW QUESTIONS
def generate_questions(details: str) -> list[str]:
    if not details:
        raise ValueError("Candidate details cannot be empty.")

    prompt = f"""
You are an experienced technical interviewer conducting
a professional technical interview.

Your task is to generate AT MOST FIVE interview questions
based on the candidate's background and experience.

Candidate information:

{details}

Instructions:

1. Focus primarily on the candidate's actual technical
   experience, projects, skills, and technologies mentioned
   in their CV.

2. Prefer questions that test whether the candidate truly
   understands the technologies and concepts they claim
   to know.

3. Do not ask generic questions such as:
   - Tell me about yourself.
   - What are your strengths?
   - Why should we hire you?

4. Ask questions that require the candidate to explain
   their reasoning, implementation decisions, trade-offs,
   or problem-solving approach.

5. If the candidate mentions a specific project, prefer
   asking about that project.

6. If the candidate mentions a technology, you may ask
   how they used it, why they chose it, or how they would
   solve a technical problem using it.

7. Adjust the difficulty to the candidate's apparent
   experience level.

8. Each question must be clear, specific, and answerable
   by the candidate.

9. Generate between ONE and FIVE questions.

10. Do not generate more than FIVE questions.

11. Avoid asking multiple questions that test exactly
    the same concept.

12. Make the questions progressively challenging when
    enough information about the candidate is available.

13. Each question MUST be on its own line.

14. Number the questions exactly like:

1. First question
2. Second question
3. Third question

15. Do NOT put multiple questions inside one numbered item.

Return ONLY the numbered interview questions.
"""

    # CALL LLM
    response = llm.invoke(prompt)
    content = response.content.strip()

    # PARSE QUESTIONS
    questions = []
    lines = content.splitlines()

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # Remove numbering:
        #
        # 1. Question
        # 2) Question
        # 3- Question
        #
        cleaned = re.sub(
            r"^\s*\d+\s*[\.\)\-:]\s*",
            "",
            line
        ).strip()

        if cleaned:
            questions.append(cleaned)

    # FALLBACK
    if not questions:
        raise ValueError("The LLM did not generate valid interview questions.")

    # MAXIMUM FIVE QUESTIONS
    questions = questions[:5]

    # VALIDATION
    if len(questions) > 5:
        questions = questions[:5]

    return questions


# 2. EVALUATE CANDIDATE ANSWER
def eval_answer(
    question: str,
    answer: str
) -> AnswerEvaluation:
    if not question:
        raise ValueError("Question cannot be empty.")

    if not answer:
        raise ValueError("Candidate answer cannot be empty.")

    prompt = f"""
You are an experienced technical interviewer evaluating
a candidate's answer during a technical interview.

Interview Question:

{question}

Candidate Answer:

{answer}

Evaluate the candidate's answer objectively.

Evaluate the following aspects:

1. Technical correctness
   - Are the technical statements correct?
   - Did the candidate demonstrate an accurate understanding?

2. Relevance
   - Does the answer directly address the question?
   - Did the candidate avoid unnecessary information?

3. Depth of understanding
   - Does the candidate understand the concept deeply?
   - Are they explaining concepts or merely repeating definitions?

4. Practical knowledge
   - Can the candidate connect the concept to real-world usage?
   - Did they provide examples when appropriate?

5. Reasoning and problem solving
   - Is the candidate's reasoning logical?
   - Can they explain why they chose a particular approach?

6. Missing information
   - Identify important concepts or points that should have
     been mentioned but were missing.

7. Mistakes
   - Identify technically incorrect statements.

8. Overall assessment
   - Give a concise assessment of the candidate's performance.

9. Score
   - Give an overall score from 0 to 10.

Important:

- Do not give credit for information that the candidate did
  not actually demonstrate.
- Do not assume knowledge that was not demonstrated.
- Be objective.
- Do not be overly generous.
- Base the evaluation ONLY on the question and answer.

Return the evaluation according to the provided
AnswerEvaluation schema.
"""

    response = llm_evaluate.invoke(prompt)
    return response


# 3. EXTRACT CV INFORMATION
def extract_cv_info(cv: str) -> CVSchema:
    if not cv:
        raise ValueError("CV text cannot be empty.")

    prompt = f"""
You are a professional CV information extraction system.

Your task is to extract structured information from the
following CV.

CV TEXT:

{cv}

Extraction rules:

1. Extract information ONLY from the provided CV.

2. Never invent, assume, or hallucinate information.

3. Preserve names, companies, job titles, degrees,
   technologies, certifications, and URLs as accurately
   as possible.

4. Extract ALL relevant work experiences.

5. Extract ALL relevant educational qualifications.

6. Extract technical and professional skills explicitly
   mentioned in the CV.

7. Extract projects and describe them using only information
   available in the CV.

8. Extract professional websites and profiles such as:
   - GitHub
   - LinkedIn
   - Kaggle
   - GitLab
   - Personal portfolio
   - Personal website

9. If a field is not present in the CV, use "Unknown"
   when the schema requires a string value.

10. Do not infer skills simply because a technology appears
    indirectly.

11. Keep dates exactly as they appear when possible.

12. If the candidate is currently working at a company and
    there is no end date, use "Present".

13. For experience descriptions, summarize the candidate's
    actual responsibilities and achievements without
    adding information.

14. Extract all projects mentioned in the CV.

15. Extract all certifications and training programs.

16. Extract all languages mentioned in the CV.

Return the information according to the provided CVSchema.
"""

    response = llm_structured.invoke(prompt)
    return response