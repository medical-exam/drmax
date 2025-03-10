import os
import streamlit as st
import boto3
import time
import docx
import PyPDF2
from openai import OpenAI
from dotenv import load_dotenv
from streamlit_chat import message
from auth import auth

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# AWS S3 Configuration
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# System prompt for personality
system_prompt = """You are Dr. Max, a witty medical mentor with the sarcastic humor of Dr. House. 
Provide expert guidance for medical exams (USMLE/PLAB/MCCQE). Be concise, add occasional humor, 
and prioritize clinical reasoning. When users make mistakes, offer sharp but constructive feedback."""

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def extract_text_from_file(uploaded_file):
    """Extract text from uploaded file based on its type."""
    if uploaded_file is None:
        return None
    
    file_type = uploaded_file.name.split(".")[-1]
    
    try:
        if file_type == "txt":
            return uploaded_file.read().decode("utf-8")
        
        elif file_type == "pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            return text if text else "No readable text found in this PDF."
        
        elif file_type == "docx":
            doc = docx.Document(uploaded_file)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text if text.strip() else "No text found in this Word document."
        
    except Exception as e:
        return f"Error extracting text: {str(e)}"
    
    return None

def generate_summary(text):
    """Generates a summary of the extracted text using OpenAI."""
    if not text:
        return "Sorry, I couldn't extract text from the uploaded file."
    
    messages = [
        {"role": "system", "content": "Summarize this medical document in a concise and structured manner."},
        {"role": "user", "content": text[:5000]}  # Limit to 5000 chars to avoid token overflow
    ]
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.5,
        max_tokens=300
    )
    return response.choices[0].message.content

def generate_response(prompt):
    """Generates a chatbot response for user questions."""
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

def logout():
    st.session_state.clear()
    st.success("👋 Logged out successfully!")
    time.sleep(1)
    st.rerun()

if not st.session_state.get("authenticated"):
    auth()
else:
    # Streamlit UI
    st.set_page_config(page_title="Dr. Max - Medical Chatbot", layout="wide")
    st.sidebar.button("🚪 Logout", on_click=logout)

    st.title("🤖 Dr. Max - AI Medical Mentor")
    st.subheader("Your sarcastic study partner for medical exams")

    # Chat interface
    chat_container = st.container()
    input_container = st.container()

    with input_container:
        uploaded_file = st.file_uploader("Upload a medical document (optional)", type=["txt", "pdf", "docx"])

        if uploaded_file:
            st.success(f"📂 Uploaded: {uploaded_file.name}")
            extracted_text = extract_text_from_file(uploaded_file)
            if extracted_text:
                summary = generate_summary(extracted_text)
                st.write("### 📝 Summary of your document:")
                st.info(summary)

        user_input = st.text_input("💬 Ask Dr. Max about medical concepts, cases, or exam strategies:", key="input")

        if user_input:
            response = generate_response(user_input)
            st.session_state.chat_history.append(("user", user_input))
            st.session_state.chat_history.append(("system", response))

    # Display chat history
    with chat_container:
        for i, (role, msg) in enumerate(st.session_state.chat_history):
            if role == "user":
                message(msg, is_user=True, key=f"{i}_user")
            else:
                message(msg, key=f"{i}")

    # Mobile optimization
    st.markdown("""
    <style>
        @media (max-width: 768px) {
            .stTextInput input {font-size: 16px;}
            .stButton button {width: 100%;} 
        }
    </style>
    """, unsafe_allow_html=True)
