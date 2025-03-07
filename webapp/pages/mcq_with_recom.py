import os
import streamlit as st
import matplotlib.pyplot as plt
import time
from openai import OpenAI
from dotenv import load_dotenv
from auth import auth
from student_form import StudentExamForm

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

# System prompt for MCQ explanations
system_prompt = """You are Dr. Max, a medical mentor specializing in exam preparation.
Provide clear, concise explanations for MCQs. When users answer incorrectly, explain their mistake and 
guide them toward the correct reasoning."""

# MCQ Question Bank
mcq_questions = [
    {"question": "What's the most common cause of hypercalcemia in hospitalized patients?",
     "options": ["Malignancy", "Primary hyperparathyroidism", "Vitamin D toxicity", "Thiazide use"],
     "answer": "Malignancy"},
    
    {"question": "Which artery is most commonly involved in an epidural hematoma?",
     "options": ["Middle meningeal artery", "Anterior cerebral artery", "Basilar artery", "Vertebral artery"],
     "answer": "Middle meningeal artery"},
    
    {"question": "What is the most common cause of community-acquired pneumonia?",
     "options": ["Streptococcus pneumoniae", "Mycoplasma pneumoniae", "Legionella pneumophila", "Klebsiella pneumoniae"],
     "answer": "Streptococcus pneumoniae"},
]



def generate_response(prompt):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7,
        max_tokens=300
    )
    return response.choices[0].message.content

def handle_mcq_answer(user_answer):
    """Handles the answer, updates progress, and generates an explanation."""
    question_data = mcq_questions[st.session_state.current_question_index]
    correct_answer = question_data["answer"]
    question_text = question_data["question"]

    if user_answer == correct_answer:
        st.session_state.mcq_progress["correct"] += 1
        st.session_state.explanation_text = "✅ Correct! " + generate_response(f"Explain why {correct_answer} is correct for: {question_text}")
    else:
        st.session_state.mcq_progress["incorrect"] += 1
        st.session_state.mcq_progress["incorrect_topics"].append(question_text)
        st.session_state.explanation_text = f"❌ Wrong! " + generate_response(f"Explain why {user_answer} is incorrect for: {question_text}. The correct answer is {correct_answer}")

    st.session_state.show_explanation = True

def next_question():
    """Moves to the next question and clears previous explanation."""
    if st.session_state.current_question_index < len(mcq_questions) - 1:
        st.session_state.current_question_index += 1
        st.session_state.show_explanation = False
        st.session_state.explanation_text = ""
    else:
        st.session_state.quiz_completed = True

def show_progress_chart():
    """Displays a bar chart of correct vs. incorrect answers."""
    labels = ['Correct', 'Incorrect']
    values = [st.session_state.mcq_progress['correct'], st.session_state.mcq_progress['incorrect']]
    colors = ['#4CAF50', '#F44336']
    
    fig, ax = plt.subplots()
    ax.bar(labels, values, color=colors)
    ax.set_ylabel("Number of Answers")
    ax.set_title("Quiz Performance")
    st.pyplot(fig)

def show_final_report():
    """Displays final exam report with recommendations."""
    st.subheader("📊 Final Exam Report")
    show_progress_chart()
    st.write(f"✅ Correct: {st.session_state.mcq_progress['correct']}")
    st.write(f"❌ Incorrect: {st.session_state.mcq_progress['incorrect']}")
    
    if st.session_state.mcq_progress["incorrect_topics"]:
        st.subheader("📚 Recommended Areas for Improvement")
        for topic in set(st.session_state.mcq_progress["incorrect_topics"]):
            st.write(f"- {topic}")
    else:
        st.write("✅ Great job! No weak areas detected.")

# Streamlit UI

if not st.session_state["authenticated"]:
    auth()
else:
    st.set_page_config(page_title="Dr. Max - MCQ Trainer", layout="wide")
    st.title("📝 MCQ Practice with Dr. Max")
    st.subheader("Test your knowledge with medical questions!")

    exam_data, start_exam = st.session_state.exam_form.display_form()