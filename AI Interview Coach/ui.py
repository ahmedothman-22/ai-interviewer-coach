import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# CONFIGURATION

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="AI Recruitment Platform",
    page_icon="",
    layout="wide"
)

# SESSION STATE

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "selected_candidate" not in st.session_state:
    st.session_state.selected_candidate = None

if "interview_data" not in st.session_state:
    st.session_state.interview_data = None

if "answer_submitted" not in st.session_state:
    st.session_state.answer_submitted = False

if "evaluation" not in st.session_state:
    st.session_state.evaluation = None

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

if "interview_history" not in st.session_state:
    st.session_state.interview_history = []

# API FUNCTIONS

def get_candidates():
    try:
        response = requests.get(
            f"{FASTAPI_URL}/candidates",
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to FastAPI: {e}")
        return []


# UPLOAD CV

def upload_cv(uploaded_file):
    try:
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                "application/pdf"
            )
        }

        response = requests.post(
            f"{FASTAPI_URL}/candidates/upload-cv",
            files=files,
            timeout=180
        )

        if response.status_code >= 400:
            try:
                detail = response.json().get(
                    "detail",
                    "CV upload failed."
                )
            except Exception:
                detail = response.text

            st.error(detail)
            return None

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to FastAPI: {e}")
        return None


# GET INTERVIEW

def get_interview(token):
    try:
        response = requests.get(
            f"{FASTAPI_URL}/interview/{token}",
            timeout=30
        )

        if response.status_code == 404:
            st.error("❌ Interview not found.")
            return None

        if response.status_code == 400:
            try:
                detail = response.json().get(
                    "detail",
                    "This interview is no longer available."
                )
            except Exception:
                detail = response.text

            st.error(detail)
            return None

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to interview server: {e}")
        return None


# SUBMIT ANSWER

def submit_answer(token, answer):
    try:
        response = requests.post(
            f"{FASTAPI_URL}/interview/{token}/answer",
            json={"answer": answer},
            timeout=180
        )

        if response.status_code == 400:
            try:
                detail = response.json().get(
                    "detail",
                    "Could not submit answer."
                )
            except Exception:
                detail = response.text

            st.error(detail)
            return None

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        st.error(f"Could not submit answer: {e}")
        return None


# HR CHAT

def send_hr_message(message, candidate_id=None):
    payload = {
        "message": message,
        "candidate_id": candidate_id,
        "conversation_id": st.session_state.conversation_id
    }

    try:
        response = requests.post(
            f"{FASTAPI_URL}/hr/chat",
            json=payload,
            timeout=120
        )

        if response.status_code >= 400:
            try:
                detail = response.json().get(
                    "detail",
                    "HR API request failed."
                )
            except Exception:
                detail = response.text

            st.error(
                f"HR API Error {response.status_code}: {detail}"
            )
            return None

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to HR API: {e}")
        return None


# CANDIDATE UPLOAD PAGE

def candidate_upload_page():
    st.title("Candidate Portal")
    st.write("Upload your CV to start the technical interview.")
    st.divider()

    st.subheader("📄 Upload Your CV")

    uploaded_file = st.file_uploader(
        "Choose your CV",
        type=["pdf"],
        help="Only PDF files are supported."
    )

    if uploaded_file:
        st.success(f"Selected file: {uploaded_file.name}")
        st.caption(f"File size: {uploaded_file.size / 1024:.1f} KB")

    st.divider()

    if st.button(
        "🚀 Submit CV",
        type="primary",
        use_container_width=True
    ):
        if uploaded_file is None:
            st.warning("Please upload your CV first.")
            return

        with st.spinner("Processing your CV..."):
            result = upload_cv(uploaded_file)

        if result:
            st.success("✅ Your CV was processed successfully!")

            candidate_name = result.get(
                "candidate_name",
                "Candidate"
            )
            candidate_email = result.get("email", "")
            questions_generated = result.get(
                "questions_generated",
                0
            )

            st.markdown(f"### Hello {candidate_name} 👋")

            if candidate_email:
                st.write(
                    f"📧 Interview invitation sent to: "
                    f"**{candidate_email}**"
                )

            if questions_generated:
                st.info(
                    f"🧠 Your interview contains "
                    f"**{questions_generated} technical questions**."
                )

            st.info(
                """
📬 **Please check your email.**

Your technical interview link has been
sent to your email address.

Click the link inside the email to start
your interview.
"""
            )


# DISPLAY EVALUATION

def display_evaluation(evaluation, title=" Question Evaluation"):
    if not evaluation:
        return

    st.divider()
    st.markdown(f"## {title}")

    # Score
    score = evaluation.get("score")

    if score is not None:
        st.metric("Score", f"{score}/10")

    # Technical correctness
    technical = evaluation.get("technical_correctness")

    if technical:
        st.markdown("### Technical Correctness")
        st.write(technical)

    # Relevance
    relevance = evaluation.get("relevance")

    if relevance:
        st.markdown("### 🎯 Relevance")
        st.write(relevance)

    # Depth
    depth = evaluation.get("depth")

    if depth:
        st.markdown("### 📚 Depth")
        st.write(depth)

    # Strengths
    strengths = evaluation.get("strengths", [])

    if strengths:
        st.markdown("### 💪 Strengths")

        for item in strengths:
            st.write(f"• {item}")

    # Missing points
    missing_points = evaluation.get("missing_points", [])

    if missing_points:
        st.markdown("### ⚠️ Missing Points")

        for item in missing_points:
            st.write(f"• {item}")

    # Mistakes
    mistakes = evaluation.get("mistakes", [])

    if mistakes:
        st.markdown("### ❌ Mistakes")

        for item in mistakes:
            st.write(f"• {item}")

    # Feedback
    feedback = evaluation.get("overall_feedback")

    if feedback:
        st.markdown("### 📝 Feedback")
        st.write(feedback)


# CANDIDATE INTERVIEW PAGE

def candidate_interview_page(token):
    st.title("Technical Interview")
    st.write("Welcome to your technical interview.")
    st.divider()

    # LOAD INTERVIEW

    if st.session_state.interview_data is None:
        with st.spinner("Loading your interview..."):
            interview = get_interview(token)

        if interview is None:
            return

        st.session_state.interview_data = interview
    else:
        interview = st.session_state.interview_data

    # CANDIDATE INFORMATION

    candidate_name = interview.get(
        "candidate_name",
        "Candidate"
    )
    question = interview.get("question", "")
    question_number = interview.get("question_number", 1)
    total_questions = interview.get("total_questions", 1)

    # Protect against invalid values
    try:
        question_number = int(question_number)
    except (ValueError, TypeError):
        question_number = 1

    try:
        total_questions = int(total_questions)
    except (ValueError, TypeError):
        total_questions = 1

    if total_questions <= 0:
        total_questions = 1

    st.success(f"Hello {candidate_name} 👋")

    # FINAL INTERVIEW RESULT

    if st.session_state.answer_submitted:
        st.success("🎉 Your technical interview is complete!")
        st.info("Thank you for completing the interview.")

        final_result = st.session_state.evaluation

        if final_result:
            # Final score
            final_score = final_result.get("final_score")

            if final_score is not None:
                st.markdown("## 🏆 Final Interview Score")
                st.metric("Overall Score", f"{final_score}/10")

            # Questions completed
            completed_questions = final_result.get("total_questions")

            if completed_questions is not None:
                st.write(
                    f"✅ Questions answered: "
                    f"**{completed_questions}**"
                )

            # Show all previous evaluations
            if st.session_state.interview_history:
                st.divider()
                st.markdown("## 📋 Interview Summary")

                for item in st.session_state.interview_history:
                    question_num = item.get("question_number")
                    score = item.get("score")

                    with st.expander(
                        f"Question {question_num} — Score: {score}/10"
                        if score is not None
                        else f"Question {question_num}"
                    ):
                        st.write(
                            f"**Question:** "
                            f"{item.get('question', '')}"
                        )

                        if item.get("answer"):
                            st.write(
                                f"**Your Answer:** "
                                f"{item.get('answer')}"
                            )

                        if score is not None:
                            st.metric("Score", f"{score}/10")

                        feedback = item.get("overall_feedback")

                        if feedback:
                            st.markdown("### 📝 Feedback")
                            st.write(feedback)

            # Last question evaluation
            last_evaluation = final_result.get(
                "evaluation",
                {}
            )

            if last_evaluation:
                display_evaluation(
                    last_evaluation,
                    title="📊 Final Question Evaluation"
                )

        return

    # PROGRESS

    st.markdown(
        f"### Question {question_number} of {total_questions}"
    )

    progress = question_number / total_questions
    progress = min(max(progress, 0.0), 1.0)

    st.progress(progress)
    st.caption(f"Progress: {int(progress * 100)}%")
    st.divider()

    # QUESTION

    st.markdown("## 🧠 Technical Question")
    st.info(question)
    st.divider()

    # PREVIOUS EVALUATIONS

    if st.session_state.interview_history:
        with st.expander("📋 Previous Question Results"):
            for item in st.session_state.interview_history:
                question_num = item.get("question_number")
                score = item.get("score")

                st.markdown(f"### Question {question_num}")

                if item.get("question"):
                    st.write(
                        f"**Question:** "
                        f"{item.get('question')}"
                    )

                if score is not None:
                    st.write(f"⭐ **Score:** {score}/10")

                feedback = item.get("overall_feedback")

                if feedback:
                    st.write(feedback)

                st.divider()

    # ANSWER

    st.markdown("## ✍️ Your Answer")

    answer = st.text_area(
        "Write your answer:",
        height=300,
        placeholder="Explain your answer clearly...",
        key=f"candidate_answer_{question_number}"
    )

    # SUBMIT ANSWER

    if st.button(
        "🚀 Submit Answer",
        type="primary",
        use_container_width=True
    ):
        if not answer.strip():
            st.warning("Please write an answer first.")
            return

        with st.spinner("🤖 AI is evaluating your answer..."):
            result = submit_answer(token, answer)

        if result:
            # INTERVIEW COMPLETED

            if result.get("completed", False):
                # Save the final question evaluation
                final_evaluation = result.get(
                    "evaluation",
                    {}
                )

                st.session_state.interview_history.append(
                    {
                        "question_number": result.get(
                            "current_question_number",
                            question_number
                        ),
                        "question": question,
                        "answer": answer,
                        "score": final_evaluation.get("score"),
                        "technical_correctness": final_evaluation.get(
                            "technical_correctness"
                        ),
                        "relevance": final_evaluation.get("relevance"),
                        "depth": final_evaluation.get("depth"),
                        "overall_feedback": final_evaluation.get(
                            "overall_feedback"
                        )
                    }
                )

                # Save final result
                st.session_state.answer_submitted = True
                st.session_state.evaluation = result
                st.rerun()

            # MORE QUESTIONS REMAIN

            else:
                current_evaluation = result.get(
                    "evaluation",
                    {}
                )

                # Save current question result
                st.session_state.interview_history.append(
                    {
                        "question_number": result.get(
                            "current_question_number",
                            question_number
                        ),
                        "question": question,
                        "answer": answer,
                        "score": current_evaluation.get("score"),
                        "technical_correctness": current_evaluation.get(
                            "technical_correctness"
                        ),
                        "relevance": current_evaluation.get("relevance"),
                        "depth": current_evaluation.get("depth"),
                        "overall_feedback": current_evaluation.get(
                            "overall_feedback"
                        )
                    }
                )

                # Update interview data
                st.session_state.interview_data = {
                    "candidate_name": candidate_name,
                    "candidate_id": interview.get("candidate_id"),
                    "interview_id": interview.get("interview_id"),
                    "question_id": result.get("next_question_id"),
                    "question": result.get("next_question", ""),
                    "question_number": result.get(
                        "next_question_number",
                        question_number + 1
                    ),
                    "total_questions": result.get(
                        "total_questions",
                        total_questions
                    ),
                    "answered_questions": result.get(
                        "answered_questions"
                    ),
                    "status": result.get("status")
                }

                # Move to next question
                st.rerun()


# STATUS HELPERS

def get_interview_status_display(status):
    if status is None:
        return "⚪", "Not Started"

    status = str(status).lower().strip()

    if status in ["completed", "complete", "finished"]:
        return "🟢", "Completed"

    if status in ["in_progress", "in progress", "started", "active"]:
        return "🟡", "In Progress"

    if status in ["pending", "not_started", "not started"]:
        return "⚪", "Not Started"

    if status in ["expired"]:
        return "🔴", "Expired"

    if status in ["cancelled", "canceled"]:
        return "🔴", "Cancelled"

    return "⚪", status.title()


# FORMAT SCORE

def format_score(score):
    if score is None:
        return "⭐ No score"

    score_string = str(score).strip()

    if not score_string:
        return "⭐ No score"

    # Backend already sends something like 85/100
    if "/" in score_string:
        return f"⭐ {score_string}"

    return f"⭐ {score_string}/10"


# HR SIDEBAR

def render_hr_sidebar():
    with st.sidebar:
        st.header("Candidates")
        candidates = get_candidates()

        # No candidates
        if not candidates:
            st.info("No candidates found.")

        # All candidates
        all_selected = st.session_state.selected_candidate is None

        if st.button(
            "🌎 All Candidates",
            key="all_candidates_button",
            use_container_width=True,
            type="primary" if all_selected else "secondary"
        ):
            st.session_state.selected_candidate = None
            st.session_state.messages = []
            st.session_state.conversation_id = None
            st.rerun()

        st.divider()

        # Candidate cards
        for candidate in candidates:
            candidate_id = candidate.get("id")
            candidate_name = candidate.get(
                "name",
                "Unknown Candidate"
            )
            interview_status = candidate.get(
                "interview_status",
                "not_started"
            )
            score = candidate.get("overall_score")

            status_icon, status_text = get_interview_status_display(
                interview_status
            )
            score_text = format_score(score)
            is_selected = (
                st.session_state.selected_candidate == candidate_id
            )

            # Candidate button
            if st.button(
                f"👤 {candidate_name}",
                key=f"candidate_{candidate_id}",
                use_container_width=True,
                type="primary" if is_selected else "secondary"
            ):
                st.session_state.selected_candidate = candidate_id
                st.session_state.messages = []
                st.session_state.conversation_id = None
                st.rerun()

            # Status
            st.caption(f"{status_icon} {status_text}")

            # Score
            st.caption(score_text)

            st.markdown(
                "<div style='height: 5px'></div>",
                unsafe_allow_html=True
            )

        st.divider()

        # Selected candidate information
        selected_id = st.session_state.selected_candidate

        if selected_id is not None:
            selected_candidate = next(
                (
                    candidate
                    for candidate in candidates
                    if candidate.get("id") == selected_id
                ),
                None
            )

            if selected_candidate:
                st.markdown("### 🎯 Selected Candidate")
                st.write(f"**{selected_candidate.get('name')}**")

                status_icon, status_text = get_interview_status_display(
                    selected_candidate.get("interview_status")
                )

                st.write(f"{status_icon} **{status_text}**")

                st.write(
                    format_score(
                        selected_candidate.get("overall_score")
                    )
                )

        st.divider()

        # New conversation
        if st.button(
            "➕ New Conversation",
            key="new_conversation",
            use_container_width=True
        ):
            st.session_state.messages = []
            st.session_state.conversation_id = None
            st.rerun()

        st.divider()

        # Example questions
        st.markdown("### 💡 Example Questions")

        examples = [
            "Which candidates have experience with Python?",
            "Which candidates have experience with FastAPI?",
            "What projects did this candidate work on?",
            "Which candidate has the strongest machine learning experience?",
            "Does this candidate have experience with PostgreSQL?",
            "Compare candidates based on Python experience.",
            "Show me this candidate's interview score.",
            "What are this candidate's strengths?",
            "What are this candidate's weaknesses?",
            "Should we hire this candidate?"
        ]

        for index, example in enumerate(examples):
            if st.button(
                example,
                key=f"example_{index}",
                use_container_width=True
            ):
                st.session_state.pending_question = example
                st.rerun()


# HR DASHBOARD

def hr_dashboard():
    st.title("👔 HR Dashboard")
    st.caption(
        "AI-powered candidate search and recruitment assistant"
    )

    # SIDEBAR
    render_hr_sidebar()

    # CURRENT SELECTION
    selected_candidate_id = st.session_state.selected_candidate

    # MAIN HEADER
    if selected_candidate_id is None:
        st.subheader("💬 HR Assistant")
        st.caption("Searching across all candidates")
    else:
        st.subheader("💬 HR Assistant")
        st.caption(
            f"Searching candidate ID: {selected_candidate_id}"
        )

    # PREVIOUS MESSAGES
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # CV Sources
            if (
                message["role"] == "assistant"
                and message.get("sources")
            ):
                with st.expander("📚 Retrieved CV Sources"):
                    for i, source in enumerate(
                        message["sources"],
                        start=1
                    ):
                        st.markdown(f"### Source {i}")

                        st.write(
                            f"**Candidate:** "
                            f"{source.get('candidate_name')}"
                        )

                        st.write(
                            f"**Section:** "
                            f"{source.get('section')}"
                        )

                        st.write(
                            f"**Chunk ID:** "
                            f"{source.get('chunk_id')}"
                        )

                        score = source.get("score")

                        if score is not None:
                            st.write(
                                f"**Retrieval Score:** "
                                f"{score:.4f}"
                            )

                        st.write(
                            source.get(
                                "content",
                                ""
                            )
                        )

                        st.divider()

            # Interview Information
            if (
                message["role"] == "assistant"
                and message.get("interview_information")
            ):
                interview_information = message[
                    "interview_information"
                ]

                with st.expander("📊 Interview Information"):
                    for info in interview_information:
                        st.markdown(
                            f"### 👤 "
                            f"{info.get('candidate_name')}"
                        )

                        status = info.get("interview_status")

                        status_icon, status_text = (
                            get_interview_status_display(status)
                        )

                        st.write(
                            f"{status_icon} "
                            f"**Status:** {status_text}"
                        )

                        score = info.get("overall_score")

                        if score:
                            st.write(
                                f"⭐ **Score:** {score}/10"
                            )

                        recommendation = info.get("recommendation")

                        if recommendation:
                            st.write(
                                f"🎯 **Recommendation:** "
                                f"{recommendation}"
                            )

                        overview = info.get("overview")

                        if overview:
                            st.markdown("#### 📝 Overview")
                            st.write(overview)

                        strengths = info.get("strengths", [])

                        if strengths:
                            st.markdown("#### 💪 Strengths")

                            for strength in strengths:
                                st.write(f"• {strength}")

                        weaknesses = info.get("weaknesses", [])

                        if weaknesses:
                            st.markdown("#### ⚠️ Weaknesses")

                            for weakness in weaknesses:
                                st.write(f"• {weakness}")

                        st.divider()

    # CHAT INPUT
    pending_question = st.session_state.pop(
        "pending_question",
        None
    )

    prompt = st.chat_input("Ask about candidates...")

    if pending_question:
        prompt = pending_question

    # SEND MESSAGE
    if prompt:
        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt
            }
        )

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner(
                "🔎 Searching CVs and interview information..."
            ):
                result = send_hr_message(
                    message=prompt,
                    candidate_id=st.session_state.selected_candidate
                )

            if result:
                answer = result.get(
                    "answer",
                    "No answer returned."
                )
                sources = result.get("sources", [])
                interview_information = result.get(
                    "interview_information",
                    []
                )

                st.session_state.conversation_id = result.get(
                    "conversation_id"
                )

                # Answer
                st.markdown(answer)

                # CV sources
                if sources:
                    with st.expander("📚 Retrieved CV Sources"):
                        for i, source in enumerate(
                            sources,
                            start=1
                        ):
                            st.markdown(f"### Source {i}")

                            st.write(
                                f"**Candidate:** "
                                f"{source.get('candidate_name')}"
                            )

                            st.write(
                                f"**Section:** "
                                f"{source.get('section')}"
                            )

                            st.write(
                                f"**Chunk ID:** "
                                f"{source.get('chunk_id')}"
                            )

                            score = source.get("score")

                            if score is not None:
                                st.write(
                                    f"**Retrieval Score:** "
                                    f"{score:.4f}"
                                )

                            st.write(
                                source.get(
                                    "content",
                                    ""
                                )
                            )

                            st.divider()

                # Interview information
                if interview_information:
                    with st.expander("📊 Interview Information"):
                        for info in interview_information:
                            st.markdown(
                                f"### 👤 "
                                f"{info.get('candidate_name')}"
                            )

                            status_icon, status_text = (
                                get_interview_status_display(
                                    info.get("interview_status")
                                )
                            )

                            st.write(
                                f"{status_icon} "
                                f"**Status:** {status_text}"
                            )

                            score = info.get("overall_score")

                            if score:
                                st.write(
                                    f"⭐ **Score:** {score}/10"
                                )

                            recommendation = info.get("recommendation")

                            if recommendation:
                                st.write(
                                    f"🎯 **Recommendation:** "
                                    f"{recommendation}"
                                )

                            overview = info.get("overview")

                            if overview:
                                st.markdown("#### 📝 Overview")
                                st.write(overview)

                            strengths = info.get("strengths", [])

                            if strengths:
                                st.markdown("#### 💪 Strengths")

                                for strength in strengths:
                                    st.write(f"• {strength}")

                            weaknesses = info.get("weaknesses", [])

                            if weaknesses:
                                st.markdown("#### ⚠️ Weaknesses")

                                for weakness in weaknesses:
                                    st.write(f"• {weakness}")

                # Save message
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "interview_information": interview_information
                    }
                )

            else:
                st.error("Could not get an answer from the API.")


# MAIN ROUTER

query_params = st.query_params
token = query_params.get("token")
page = query_params.get("page")

# INTERVIEW

if token:
    candidate_interview_page(token)

# CANDIDATE PORTAL

elif page == "candidate":
    candidate_upload_page()

# HR DASHBOARD

elif page == "hr":
    hr_dashboard()

# HOME

else:
    st.title(" AI Recruitment Platform")
    st.write("Choose how you want to use the platform.")
    st.divider()

    col1, col2 = st.columns(2)

    # Candidate
    with col1:
        st.markdown("## Candidate")
        st.write(
            "Upload your CV and complete "
            "your technical interview."
        )

        if st.button(
            " Candidate Portal",
            type="primary",
            use_container_width=True
        ):
            st.query_params["page"] = "candidate"
            st.rerun()

    # HR
    with col2:
        st.markdown("## HR")
        st.write(
            "Search candidates and use AI "
            "to analyze their CVs and interviews."
        )

        if st.button(
            " HR Dashboard",
            use_container_width=True
        ):
            st.query_params["page"] = "hr"
            st.rerun()