import os
import speech_recognition as sr
import streamlit as st
import pyttsx3
import threading
from openai import OpenAI
from dotenv import load_dotenv
import re  # Import regex for text cleaning
from report_generator import generate_report
from pymongo import MongoClient
import uuid
import datetime
from bson import ObjectId
import psycopg2 # postgresql



load_dotenv()

class MentalHealthAssistant:
    def __init__(self):

        self.client = MongoClient(st.secrets["MONGO_URI"]) 
        self.db = self.client["mental_health_db"]
        self.chat_history_collection = self.db["chat_history"]

        self.conn = psycopg2.connect(
            dbname=st.secrets["POSTGRES_DB"],
            user=st.secrets["POSTGRES_USER"],
            password=st.secrets["POSTGRES_PASSWORD"],
            host=st.secrets["POSTGRES_HOST"],
            port=st.secrets["POSTGRES_PORT"]
        )
        self.cursor = self.conn.cursor()

        self.create_chat_table()

        self.openai_client = OpenAI(
            api_key=st.secrets["OPENAI_API_KEY"],
            )
        self.messages = [{"role": "system", "content": ''' You are "ElevateMind" - a friendly mental health companion that keeps conversations flowing with ultra-short responses. Always:
1. Respond in 1-2 sentences max
2. Use casual language (ok→"ok", college→"clg")
3. End with a ❓ unless user shares a problem
4. Add 1 relevant emoji per message

**Response Rules:**
- Happy updates → Celebrate + ask follow-up 🎉
- Neutral updates → Show interest + ask follow-up ❓
- Negative feelings → Validate + 1 mini-strategy 💡
- Crisis words → Immediate resources 🆘

**Examples:**
:User   "today im going to clg"
Bot: "Oh good! First class? 👀" 

:User   "had fight with bf"
Bot: "Ugh fights suck 😮💨 Try texting him this: 'Can we talk later?'"

:User   "i failed exam"
Bot: "Oof that stings 💔 Wanna rant or get tips?" 

:User   "i wanna die"
Bot: "🚨 Please call 1-800-273-8255 now. I'm here too."
Example Start-Up Message:

"Hello! I’m Mental Health Assistant. I’m here to listen and support you. How was your day?"
'''}]

        self.speech_engine = None
        self.speech_thread = None
        self.current_response = ""
        self._stop_speaking = False

    def create_chat_table(self):
        """Create chat history table if it does not exist"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS chat_history (
            id SERIAL PRIMARY KEY,
            user_id UUID NOT NULL,
            user_input TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        self.cursor.execute(create_table_query)
        self.conn.commit()

    def recognize_speech(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            try:
                audio = recognizer.listen(source, timeout=20)
                text = recognizer.recognize_google(audio, language="en-US")
                return text
            except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
                return None
            
    def process_user_input(self, user_input, is_voice=False):
        self.messages.append({"role": "user", "content": user_input})
        if "user_id" not in st.session_state:
            st.session_state.user_id = str(uuid.uuid4())
        user_id = st.session_state.user_id
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=self.messages,
            temperature=0.5,
            max_tokens=1024,
        )        
        ai_response = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": ai_response})
        self.current_response = ai_response
        self.store_chat_history(user_input, ai_response, user_id)
        
        if is_voice:
            self.speak(ai_response)
        
        return ai_response

    def _speak(self, text):
        """Handle text-to-speech with engine reinitialization"""
        self._stop_speaking = False
        self.speech_engine = pyttsx3.init()
        self.speech_engine.setProperty("rate", 150)
        
        # Clean the text to remove emojis and symbols
        clean_text = self.clean_text(text)

        #Get Female Voice
        voices = self.speech_engine.getProperty('voices')
        for voice in voices:
            if "zira" in voice.name.lower():
                self.speech_engine.setProperty('voice', voice.id)
                break

        # Add event callbacks for proper cleanup
        def on_start(name):
            if self._stop_speaking:
                self.speech_engine.stop()

        def on_word(name, location, length):
            if self._stop_speaking:
                self.speech_engine.stop()

        self.speech_engine.connect('started-utterance', on_start)
        self.speech_engine.connect('started-word', on_word)
        
        self.speech_engine.say(clean_text)
        self.speech_engine.runAndWait()
        self.speech_engine = None  # Clean up engine after use

    def clean_text(self, text):
        """Remove emojis and non-alphanumeric characters from the text"""
        # Regex to remove emojis and special characters
        return re.sub(r'[^\w\s,.!?]', '', text)

    def speak(self, text):
        """Start speaking response directly"""
        if self.is_speaking():
            return False
        
        self._stop_speaking = False
        self.speech_thread = threading.Thread(
            target=self._speak, 
            args=(text,),
            daemon=True
        )
        self.speech_thread.start()
        return True

    def stop_speech(self):
        """Stop current speech"""
        self._stop_speaking = True
        if self.speech_engine:
            self.speech_engine.stop()
        if self.speech_thread and self.speech_thread.is_alive():
            self.speech_thread.join(timeout=1)

    def is_speaking(self):
        """Check if currently speaking"""
        return self.speech_thread and self.speech_thread.is_alive()
    
    def get_chat_history(self):
        """Retrieve past conversations from PostgreSQL"""
        query = """
        SELECT user_input, ai_response, timestamp FROM chat_history
        ORDER BY timestamp DESC;
        """
        self.cursor.execute(query)
        history = self.cursor.fetchall()
        print("Chat History:", history)
        conversation = []
        for entry in history:
            conversation.append({"user_input": entry[0], "ai_response": entry[1], "timestamp": entry[2]})

        return conversation  # Returns a list of dictionaries
    
    def store_chat_history(self, user_input, ai_response, user_id):
        """Store user conversation in PostgreSQL"""
        insert_query = """
        INSERT INTO chat_history (user_id, user_input, ai_response)
        VALUES (%s, %s, %s);
        """
        self.cursor.execute(insert_query, (user_id, user_input, ai_response))
        self.conn.commit()

    def generate_report_for_user(self, user_id):
        """Generate a mental health report based on the user's chat history"""
        query = """
        SELECT user_input, ai_response FROM chat_history
        WHERE user_id = %s
        ORDER BY timestamp DESC;
        """
        self.cursor.execute(query, (user_id,))
        user_conversations = self.cursor.fetchall()

        if not user_conversations:
            return "No chat history found for this user!"

        conversation_text = "\n".join([
            f"User: {entry[0]}\nAI: {entry[1]}" for entry in user_conversations
        ])

        report = generate_report(conversation_text)
        return report

    def close_connection(self):
            """Close PostgreSQL connection"""
            self.cursor.close()
            self.conn.close()
 

    