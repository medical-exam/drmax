import streamlit as st
import time
from main import MentalHealthAssistant 
import uuid
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from io import BytesIO
from journal import journaling_page
import re
from podcast import display_podcasts
from PIL import Image

st.set_page_config(
    page_title="Dr. Max",
    page_icon=Image.open("logo.jpg"),
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state variables
if "assistant" not in st.session_state:
    st.session_state.assistant = MentalHealthAssistant()
if "listening" not in st.session_state:
    st.session_state.listening = False
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = ""
if "show_history" not in st.session_state:
    st.session_state.show_history = False
if "show_report" not in st.session_state:
    st.session_state.show_report = False
if "last_processed_input" not in st.session_state:
    st.session_state.last_processed_input = ""
if "show_info" not in st.session_state:
    st.session_state.show_info = False

# Custom CSS styling
st.markdown("""
        <style>
            body { background-color: #121212; color: white; margin-right:100px}
        
            .stTextInput > div > div > input {
                background-color: rgb(220, 214, 238) !important;
                color: black !important;
                border: 2px solid transparent !important;  /* Removes the red border */
                border-radius: 8px !important;
                padding: 10px !important;
                transition: border-color 0.3s ease-in-out !important;
            }

            .stTextInput > div > div > input:focus {
                border: 2px solid rgb(173, 149, 213) !important; /* Adds a soft purple focus border */
                outline: none !important;
                text-color:black;
            }

            .stButton > button {
                background-color: #9575CD !important;
                color: white !important;
                font-size: 19px !important; 
                width:85%;
                transform: scale(1.05); /* Slightly enlarge active tab */
                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.2); /* More depth */
            }

            .stButton > button:hover {
                background-color: #D1C4E9 !important;            
            }
    
            .stChatMessage {
                border-radius: 12px; 
                padding: 12px; 
                margin-bottom: 12px;
            }

            .stChatMessage-user {
                background-color: #333333; 
                color: white;
            }

            .stChatMessage-assistant {
                background-color: #2d2d2d; 
                color:rgb(217, 205, 235);
            }
            div[data-testid="stHorizontalBlock"] {
            display: flex;
            justify-content: center;
            margin-bottom: 15px !important;
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
            .stMarkdown { font-size: 16px; }
        </style>
    """, unsafe_allow_html=True)

# Navigation bar using horizontal radio buttons
page = st.radio("Navigation", ["🏠 Home", "📖 Journal", "🎙 Podcast"], horizontal=True)

if page == "🏠 Home":
    # Sidebar for chat history (only relevant to the Home page)
    with st.sidebar:
        st.button("📜 Show History", on_click=lambda: st.session_state.update(show_history=not st.session_state.show_history))
        if st.session_state.show_history:
            chat_history = st.session_state.assistant.get_chat_history()
            for entry in chat_history:
                with st.chat_message("user"):
                    st.markdown(entry['user_input'])
                with st.chat_message("assistant"):
                    st.markdown(entry['ai_response'])
        else:
            st.info("History is currently hidden. Please Click on **Show History** in the main view.")

    # Main content area for Home (chat interface)
    st.title("🎤 Dr. Max, Your Virtual Assistance in Exam.")
    st.markdown("💬 Talk to your AI companion for exam support")

    # Info and history controls
    col1, col2 = st.columns([0.85, 0.15])
    with col1:
        if st.session_state.show_info:
            with st.expander("ℹ️ About Dr. Max", expanded=True):
                st.markdown("""
                    🎤 **Voice activated mental health companion**  
                    🧠 Detects mental wellness and emotional state  
                    🔊 Speaks responses aloud for natural interaction  
                    💬 Chat interface for text-based communication  
                    📊 Generates detailed mental health reports  
                    📥 Export your session history as PDF  
                """)
    with col2:
        st.button("ℹ️ About Bot", on_click=lambda: st.session_state.update(show_info=not st.session_state.show_info))
    # Display chat messages
    for message in st.session_state.assistant.messages:
        if message["role"] == "system":
            continue
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input and processing
    if prompt := st.chat_input("Type your message or click microphone to speak..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                response = st.session_state.assistant.process_user_input(prompt)
                st.markdown(response)

    # Voice controls at bottom
    st.markdown("---")
    cols = st.columns(3)
    with cols[0]:
        if st.button("🎙️ Start Listening" if not st.session_state.listening else "🔴 Stop Listening"):
            st.session_state.listening = not st.session_state.listening
            if st.session_state.listening:
                st.info("Listening... Speak now.")
                user_input = st.session_state.assistant.recognize_speech()
                if user_input:
                    with st.chat_message("user"):
                        st.markdown(user_input)
                    with st.chat_message("assistant"):
                        with st.spinner("Analyzing..."):
                            response = st.session_state.assistant.process_user_input(user_input, is_voice=True)
                            st.markdown(response)
                    st.session_state.listening = False
                    st.rerun()
    with cols[1]:
        if st.button("⏹️ Stop Speaking"):
            st.session_state.assistant.stop_speech()
    with cols[2]:
        if st.button("📊 Generate Report"):
            if "user_id" not in st.session_state:
                st.session_state.user_id = str(uuid.uuid4())
            report = st.session_state.assistant.generate_report_for_user(st.session_state.user_id)
            if report:
                st.session_state.show_report = True
                st.session_state.analysis_result = report
                st.rerun()

    # Report generation section
    if st.session_state.show_report:
        with st.expander("📊 Dr. Max Report", expanded=True):
            st.markdown(f'<div class="report-box">{st.session_state.analysis_result}</div>', unsafe_allow_html=True)

            # Generate PDF Report
            def generate_pdf(report_text):
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter)
                story = []
                styles = getSampleStyleSheet()
                normal_style = ParagraphStyle(
                    "Normal",
                    parent=styles['Normal'],
                    fontName="Helvetica",
                    fontSize=12,
                    leading=14,
                    spaceAfter=12,
                    spaceBefore=6
                )
                bullet_style = ParagraphStyle(
                    "Bullet",
                    parent=styles['Normal'],
                    fontName="Helvetica",
                    fontSize=12,
                    leading=14,
                    spaceAfter=12,
                    spaceBefore=6,
                    leftIndent=20,
                    bulletIndent=10
                )

                # Compile a regex pattern for common emoji characters.
                emoji_pattern = re.compile(
                    "["                    
                    u"\U0001F600-\U0001F64F"  # emoticons
                    u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                    u"\U0001F680-\U0001F6FF"  # transport & map symbols
                    u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                    "]+", 
                    flags=re.UNICODE
                )

                for line in report_text.split('\n'):
                    # Remove markdown bold markers "**"
                    line = line.replace("**", "")
                    # Remove emojis using the compiled pattern.
                    line = emoji_pattern.sub(r'', line)
                    line = line.strip()
                    # Choose bullet_style if line starts with a bullet character, otherwise normal_style.
                    paragraph = Paragraph(line, bullet_style if line.startswith("•") else normal_style)
                    story.append(paragraph)

                doc.build(story)
                buffer.seek(0)
                return buffer

        
        pdf_buffer = generate_pdf(st.session_state.analysis_result)
        st.download_button("📥 Download PDF", data=pdf_buffer,file_name="Mental_health_report.pdf",mime="application/pdf")
            
elif page == "📖 Journal":
    journaling_page()
    with st.sidebar:
        st.button("📜 Show History", on_click=lambda: st.session_state.update(show_history=not st.session_state.show_history))
        if st.session_state.show_history:
            chat_history = st.session_state.assistant.get_chat_history()
            for entry in chat_history:
                with st.chat_message("user"):
                    st.markdown(entry['user_input'])
                with st.chat_message("assistant"):
                    st.markdown(entry['ai_response'])
        else:
            st.info("History is currently hidden. Please Click on **Show History** in the main view.")

elif page == "🎙 Podcast":
    display_podcasts()
    with st.sidebar:
        st.button("📜 Show History", on_click=lambda: st.session_state.update(show_history=not st.session_state.show_history))
        if st.session_state.show_history:
            chat_history = st.session_state.assistant.get_chat_history()
            for entry in chat_history:
                with st.chat_message("user"):
                    st.markdown(entry['user_input'])
                with st.chat_message("assistant"):
                    st.markdown(entry['ai_response'])
        else:
            st.info("History is currently hidden. Please Click on **Show History** in the main view.")



