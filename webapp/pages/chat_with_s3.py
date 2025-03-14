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
import streamlit.components.v1 as components

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
groq_client = OpenAI(
    api_key=st.secrets["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)

# AWS S3 Configuration
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# System prompt for chatbot personality
system_prompt = """Dr. Max, explain [medical concept/case/exam strategy] in a way that makes sense, like you're talking to a clueless intern. Include the high-yield points, real-world relevance, and any exam tricks that will save me from failing. Also, throw in a sarcastic analogy so I actually remember it."""

# Initialize session state variables if not present
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "uploaded_summary" not in st.session_state:
    st.session_state.uploaded_summary = None  # Stores document summary

def extract_text_from_file(uploaded_file):
    """Extract text from an uploaded file based on its type."""
    if uploaded_file is None:
        return None

    file_type = uploaded_file.name.split(".")[-1]

    try:
        if file_type == "txt":
            return uploaded_file.read().decode("utf-8")

        elif file_type == "pdf":
            reader = PyPDF2.PdfReader(uploaded_file)
            text = "\n".join(
                [page.extract_text() for page in reader.pages if page.extract_text()]
            )
            return text if text else "No readable text found in this PDF."

        elif file_type == "docx":
            doc = docx.Document(uploaded_file)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text.strip() if text.strip() else "No text found in this Word document."

    except Exception as e:
        return f"Error extracting text: {str(e)}"

    return None

def generate_summary(text):
    """Generates a summary of the extracted text using OpenAI."""
    if not text:
        return "Sorry, I couldn't extract text from the uploaded file."

    messages = [
        {"role": "system", "content": "Summarize this medical document in a concise and structured manner."},
        {"role": "user", "content": text[:5000]},  # Limit to 5000 chars to avoid token overflow
    ]

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.5,
        max_tokens=1024,
    )
    return response.choices[0].message.content

def generate_response(prompt):
    """Generates a chatbot response for user questions, considering the uploaded document summary."""
    messages = [
        {"role": "system", "content": system_prompt},
    ]

    # If a summary is available, include it in the context
    if st.session_state.uploaded_summary:
        messages.append({"role": "system", "content": f"Based on the relevant document summary below, provide a clear and concise answer to the given question. Ensure that the response is accurate and aligned with medical concepts, clinical cases, or exam strategies.Relevant document summary:{st.session_state.uploaded_summary}"})

    messages.append({"role": "user", "content": prompt})

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.5,
        max_tokens=1024,
    )
    return {"role": "system", "content": response.choices[0].message.content} 

def logout():
    """Logs out the user and clears session state."""
    st.session_state.clear()
    st.success("👋 Logged out successfully!")
    time.sleep(1)
    st.rerun()

# Authentication
if not st.session_state.get("authenticated"):
    auth()
else:
    # Streamlit UI Configuration
    st.set_page_config(page_title="Dr. Max - Medical Chatbot", layout="wide")
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
    background-color: #D1C4E9 !important;            
}
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
    
    /* Footer Hide */
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

    st.sidebar.button("🚪 Logout", on_click=logout)

    st.title("🩺 Dr. Max - AI Medical Mentor")
    st.subheader("Your sarcastic study partner for medical exams")
    def chat_message(role, message):
        """Renders chat messages with a custom design for user and bot."""
        if role == "user":
            st.markdown(
                f"""
                <div style="display: flex; justify-content: flex-end; align-items: center; margin-bottom: 10px;">
                    <div style="
                        background-color: #8a2be2;
                        color: white;
                        padding: 10px 15px;
                        border-radius: 20px 20px 0px 20px;
                        max-width: 75%;
                        font-size: 16px;
                        text-align: right;">
                        {message}
                    </div>
                    <img src='https://img.icons8.com/ios-filled/50/808080/user-male-circle.png' width="40" style="margin-left:10px;"/>
                </div>
                """, unsafe_allow_html=True)
        
        else:  # Bot messages
            st.markdown(
                f"""
                <div style="display: flex; justify-content: flex-start; align-items: center; margin-bottom: 10px;">
                    <img src='https://img.icons8.com/ios-filled/50/6e00ff/robot-2.png' width="40" style="margin-right:10px;"/>
                    <div style="
                        background-color: #f3e8ff;
                        color: #000;
                        padding: 10px 15px;
                        border-radius: 20px 20px 20px 0px;
                        max-width: 75%;
                        font-size: 16px;
                        text-align: left;">
                        {message}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    # Typing animation before chatbot responds
    def typing_indicator():
        components.html("""
        <div class="typing">
            <span></span><span></span><span></span>
        </div>
        <style>
            .typing {
                display: flex;
                gap: 5px;
            }
            .typing span {
                width: 8px;
                height: 8px;
                background: #6a0dad;
                border-radius: 50%;
                animation: typing 1s infinite;
            }
            .typing span:nth-child(2) { animation-delay: 0.2s; }
            .typing span:nth-child(3) { animation-delay: 0.4s; }

            @keyframes typing {
                0% { opacity: 0.3; transform: scale(0.8); }
                50% { opacity: 1; transform: scale(1); }
                100% { opacity: 0.3; transform: scale(0.8); }
            }
        </style>
        """, height=30)
    # File Upload and Processing
    uploaded_file = st.file_uploader("Upload a medical document (optional)", type=["txt", "pdf", "docx"])

    if uploaded_file and st.session_state.uploaded_summary is None:
        st.success(f"📂 Uploaded: {uploaded_file.name}")
        extracted_text = extract_text_from_file(uploaded_file)

        if extracted_text:
            st.session_state.uploaded_summary = generate_summary(extracted_text)

    # Display Summary if available
    if st.session_state.uploaded_summary:
        with st.expander("### 📝 Summary of your document:", expanded=True):
                st.markdown(f'<div class="report-box">{st.session_state.uploaded_summary}</div>', unsafe_allow_html=True)

    # Chat Interface
    chat_container = st.container()
    input_container = st.container()

    with input_container:
        user_input = st.chat_input("💬 Ask Dr. Max about medical concepts, cases, or exam strategies:", key="input")

        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})


            # Display typing animation
            with st.spinner("Dr. Max is thinking..."):
                typing_indicator()
                time.sleep(1.5)  # Simulating typing delay

            # Generate bot response
            response = generate_response(user_input)
            st.session_state.chat_history.append(response)

    # Display chat history
    with chat_container:
        for msg in st.session_state.chat_history:
            chat_message(msg["role"], msg["content"])

    # Mobile optimization
    st.markdown(
        """
        <style>
            @media (max-width: 768px) {
                .stTextInput input {font-size: 16px;}
                .stButton button {width: 100%;} 
            }
        </style>
        """,
        unsafe_allow_html=True,
    )