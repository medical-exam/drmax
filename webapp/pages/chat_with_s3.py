import os
import streamlit as st
import boto3
import time
from openai import OpenAI
from dotenv import load_dotenv
from streamlit_chat import message

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

def search_s3_for_content(user_query):
    """Searches S3 bucket for relevant content matching the user query."""
    try:
        response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME)
        if 'Contents' in response:
            for obj in response['Contents']:
                file_key = obj['Key']
                if user_query.lower() in file_key.lower():  # Basic search by filename
                    s3_object = s3.get_object(Bucket=S3_BUCKET_NAME, Key=file_key)
                    return s3_object['Body'].read().decode('utf-8')  # Assume text content
    except Exception as e:
        st.error(f"Error accessing S3: {e}")
    return None

def generate_response(prompt):
    """Generates a response from OpenAI if S3 has no matching content."""
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

# Streamlit UI
st.set_page_config(page_title="Dr. Max - Medical Chatbot", layout="wide")

st.title("🤖 Dr. Max - AI Medical Mentor")
st.subheader("Your sarcastic study partner for medical exams")

# Chat interface
chat_container = st.container()
input_container = st.container()

with input_container:
    user_input = st.text_input("Ask Dr. Max about medical concepts, cases, or exam strategies:", key="input")
    if user_input:
        s3_content = search_s3_for_content(user_input)
        if s3_content:
            response = s3_content  # Use content from S3 if found
        else:
            response = generate_response(user_input)  # Otherwise, use OpenAI
        
        st.session_state.chat_history.append(("user", user_input))
        st.session_state.chat_history.append(("system", ""))  # Placeholder for streamed response
        
        response_container = st.empty()
        displayed_response = ""
        
        for word in response.split():
            displayed_response += word + " "
            response_container.markdown(f"**Dr. Max:** {displayed_response}")
            time.sleep(0.1)  # Simulate streaming effect
        
        st.session_state.chat_history[-1] = ("system", displayed_response)

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