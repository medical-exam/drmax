import openai
import os
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
from bson import ObjectId

# Load environment variables
load_dotenv()

# Initialize MongoDB client
client = MongoClient(os.getenv("MONGO_URI"))
db = client["mental_health_db"]  # Replace with your actual database name
chat_history_collection = db["chat_history"]  # Replace with your actual collection name

class MentalHealthAssistant:
    def _init_(self):
        self.client = MongoClient(os.getenv("MONGO_URI"))
        self.db = self.client["mental_health_db"]
        self.chat_history_collection = self.db["chat_history"]

    def fetch_user_conversation(self, user_id):
        """
        Fetches the chat history of a specific user from MongoDB.
        """
        try:
            user_id = ObjectId(user_id)  
        except:
            pass  

        user_conversations = list(self.chat_history_collection.find({"user_id": user_id}).sort("timestamp", -1))

        if not user_conversations:
            return "No chat history found."

        conversation_text = "\n".join([f"User: {entry.get('user_input', 'N/A')}\nAI: {entry.get('ai_response', 'N/A')}" for entry in user_conversations])

        return conversation_text

def generate_report(conversation_text):
    """5
    Generates a highly structured and supportive mental health report.
    """

    # Define the AI prompt
    prompt = f''' "You are a psychologist AI. Analyze the user's conversation and detect their mental health status.\n\n"
    "conversation_text: "{conversation_text}
    '**Current Mental Health:** [Emoji + Status]\n\n\n'
    "**Summary:**\n[Brief description of user's emotional state and key concerns]\n\n"
    "**Recommendations:**\n"
    "- [Actionable Tip 1]\n"
    "- [Actionable Tip 2]\n"
    "- [Actionable Tip 3]\n\n"
    "Make sure each section appears on a new line for clarity.\n"
    "Use an appropriate emoji to represent the user's mental state (e.g., 😊 Happy, 😟 Stressed, 😔 Sad, 😢 Depressed, 😌 Relaxed, 😵‍💫 Overwhelmed, etc.)."
    "Make sure your analysis is concise, clear, and supportive."
    "Base your assessment on the conversation context."
    
    '''
    groq_client = openai.OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1"
    )
    # Call OpenAI API
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # Use a strong model for detailed responses
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,  # Adjust for more natural responses
        max_tokens=1024
    )

    # Extract AI-generated report
    ai_generated_report = format_report(response.choices[0].message.content.strip())

    return ai_generated_report

def format_report(report_text):
    """
    Formats the AI-generated report into a structured format.
    """
    formatted_report = f'''{report_text}
    
    📌 This is an AI-generated assessment. Please consult a professional for clinical advice.
    '''
    return formatted_report