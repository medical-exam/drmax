import os
import streamlit as st
import matplotlib.pyplot as plt
import time
from openai import OpenAI
from dotenv import load_dotenv
from auth import auth
from student_form import StudentExamForm
from score_tracker import ScoreTracker


# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize session states
if 'mcq_progress' not in st.session_state:
    st.session_state.mcq_progress = {"correct": 0, "incorrect": 0, "incorrect_topics": []}
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
if 'show_explanation' not in st.session_state:
    st.session_state.show_explanation = False
if 'explanation_text' not in st.session_state:
    st.session_state.explanation_text = ""
if 'quiz_completed' not in st.session_state:
    st.session_state.quiz_completed = False
if 'retake_exam' not in st.session_state:
    st.session_state.retake_exam = False
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "exam_form" not in st.session_state:
    st.session_state.exam_form = StudentExamForm()
if "score_tracker" not in st.session_state:
    st.session_state.score_tracker = ScoreTracker()
if 'student_id' not in st.session_state:
    st.session_state.student_id = False

def logout():
    st.session_state.clear()
    st.success("👋 Logged out successfully!")
    time.sleep(1)
    st.rerun()


# Streamlit UI

if not st.session_state["authenticated"]:
    auth()
else:
    st.set_page_config(page_title="Dr. Max - MCQ Trainer", layout="wide")
    st.title("📝 MCQ Practice with Dr. Max")
    st.subheader("Test your knowledge with medical questions!")
    st.markdown(
        """
        <style>
        

        [data-testid="stSidebar"] {
        background: #f3e8ff !important;;
        
        }

    .stButton button {
        border-radius: 12px !important;
        font-size: 16px !important;
        background-color: #8a2be2 !important; /* Bright purple */
        color: white !important;
        padding: 10px;
    }
    .stButton > button:hover {
        backgrouSnd-color: #D1C4E9 !important;            
    }
    /* Improve chat input box */
    .stTextInput input {
        border: 2px solid #8a2be2 !important;
        background-color: #ffffff !important;
        border-radius: 8px;
        padding: 10px;
        font-size: 16px;
        transition: all 0.3s ease-in-out;
    }

    /* Glow effect when user focuses */
    .stTextInput input:focus {
        border-color: #6a0dad !important;
        box-shadow: 0px 0px 8px rgba(138, 43, 226, 0.5);
    }

    /* Send button next to input */
    .stChatInput button {
        background: #8a2be2 !important;
        color: white !important;
        border-radius: 50%;
        font-size: 20px;
        padding: 10px;
        transition: all 0.3s ease-in-out;
    }

    /* Hover effect for send button */
    .stChatInput button:hover {
        background-color: #6a0dad !important;
        transform: scale(1.1);
    }



        h1, h2 {
        font-size: 24px; /* Larger for headings */
        font-weight: 700; /* Bold for emphasis */
        font-family: 'Roboto', sans-serif; 
    }
    p {
        font-size: 16px; /* Readable body text */
        font-family: 'Roboto', sans-serif; 
    }

    
        /* Text Input */
        .stTextInput input {
            background-color: #ffffff !important;
            border: 2px solid #8a2be2 !important;
            border-radius: 8px;
        }
        .stFileUploader {
        
        background-color: #f3e8ff !important;
        border-radius: 10px;
        padding: 10px;
    }

        .stChatMessage {
        background-color: #8a2be2 !important;
        color: white !important;
    }


        /* Style for bot messages specifically */
        [data-testid="StChatMessage"] {
        background-color: #8a2be2 !important; /* Bright purple */
        color: white !important;
    }

        /* Style for user messages */
        [data-testid="UserChatMessage"] {
            background-color: #8a2be2 !important;
            border: 1px solid #8a2be2 !important;
        }
        /* Style the individual radio buttons */
        div[data-testid="stRadio"] label {
            font-size: 18px !important;
            font-weight: bold !important;
            color: #6B52AE !important;  /* Purple */
            background-color: #EDE7F6 !important;
            border-radius: 25px !important; /* More rounded */
            padding: 14px 22px !important; /* Increased padding */
            margin: 8px !important; /* Adds spacing between options */
            transition: all 0.3s ease-in-out;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1); /* Soft shadow */
            cursor: pointer;
        }

        /* Hover effect */
        div[data-testid="stRadio"] label:hover {
            background-color: #D1C4E9 !important;
        }

        /* Active (selected) button */
        div[data-testid="stRadio"] label[data-testid="stMarkdownContainer"] {
            background-color: #9575CD !important;
            color: white !important;
            font-size: 19px !important;
            transform: scale(1.05); /* Slightly enlarge active tab */
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.2); /* More depth */
        }
        
        /* Footer Hide */
        footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True
    )
    st.sidebar.button("🚪 Logout", on_click=logout)

    # Create tabs for Exam and Progress Tracking
    page = st.radio("Navigation", ["Exam", "Progress tracking"], horizontal=True)

    if page == "Exam":
        st.subheader("MCQ Exam")
        exam_data, start_exam = st.session_state.exam_form.display_form()
    elif page == "Progress tracking":
        st.subheader("Progress Tracking")
        student_id = st.session_state.student_id  # Get student ID
        if not student_id:
            st.warning("⚠ No student ID found. Please log in and attempt the exam to track progress.")
        else:
            st.session_state.score_tracker.plot_progress(student_id)