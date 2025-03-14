import streamlit as st
import os
from datetime import datetime
from pymongo import MongoClient
# MongoDB connection
client = MongoClient(os.getenv("MONGO_URI"))  # Update with your MongoDB URI if needed
db = client["mental_health_app"]  # Database name
collection = db["journal_entries"]  # Collection name

def save_entry(text):
    entry = {"timestamp": datetime.now(), "text": text}
    collection.insert_one(entry)

def get_recent_entries(limit=5):
    return list(collection.find().sort("timestamp", -1).limit(limit))

def journaling_page():
    # Custom CSS for styling
    
    st.markdown("""
        <style>
            body { background-color: #121212; color: white; }
            .stTextArea textarea { 
                background-color: #2d2d2d; 
                color: white; 
                border-radius: 8px; 
                padding: 10px; 
            }
            .stButton > button {
                border-radius: 12px; 
                font-size: 16px; 
                padding: 12px; 
                transition: 0.3s;
                background-color: rgb(173, 149, 213);
                color: white;
                border: none;
            }
            .stButton > button:hover {
                background-color: rgb(140, 110, 190) !important;
            }
            .custom-toggle {
                background-color: rgb(173, 149, 213) !important;
                color: white !important;
                border-radius: 12px;
                padding: 5px 15px;
                cursor: pointer;
            }
        </style>
    """, unsafe_allow_html=True)

    # Initialize session state for journal entries
    if "journal_entries" not in st.session_state:
        st.session_state.journal_entries = []

    # App Title
    st.title("📔 Journaling ")
    st.markdown("""
        Writing down your thoughts and feelings can help you process emotions, reduce stress, and gain clarity. 
        Take a few minutes to journal whenever you feel overwhelmed or low.
    """)

    # Journaling Section
    with st.form("journal_form"):
        st.subheader("✍ Write Your Journal Entry")
        journal_text = st.text_area(
            "How are you feeling today? Write about your thoughts, emotions, or anything on your mind...",
            height=200,
            placeholder="Start writing here..."
        )
        submit_button = st.form_submit_button("Save Entry")

        if submit_button and journal_text:
            save_entry(journal_text)
            st.success("Your journal entry has been saved! 🎉")
            st.rerun()

    st.subheader("📜 Recent Journal Entries")
    entries = get_recent_entries()
    if entries:
        for entry in entries:
            st.markdown(f"🗓 *{entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}*")
            st.markdown(f"> {entry['text'].splitlines()[0]} ... ")
            show_more = st.toggle(f"Read More", key=entry["timestamp"])

            if show_more:
                st.markdown(f"> {entry['text']}")
        
    else:
        st.info("No journal entries yet. Start writing to see your entries here!")
    # Optional: Add a button to clear all journal entries
    if st.session_state.journal_entries:
        if st.button("🧹 Clear All Entries"):
            st.session_state.journal_entries = []
            st.success("All journal entries have been cleared!")