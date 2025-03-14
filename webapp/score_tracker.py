import psycopg2
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
from contextlib import closing
import matplotlib.dates as mdates
import plotly.express as px
import pandas as pd;
class ScoreTracker:
    def __init__(self):
        """Initialize database connection."""
        self.conn = psycopg2.connect(
            dbname=st.secrets["POSTGRES_DB"],
            user=st.secrets["POSTGRES_USER"],
            password=st.secrets["POSTGRES_PASSWORD"],
            host=st.secrets["POSTGRES_HOST"],
            port=st.secrets["POSTGRES_PORT"]
        )
        self.create_table()

    def create_table(self):
        """Create table for storing scores if it doesn't exist."""
        with closing(self.conn.cursor()) as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    id SERIAL PRIMARY KEY,
                    student_id VARCHAR(50) NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    score INTEGER NOT NULL,
                    total_questions INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()

    def save_score(self, student_id, category, score, total_questions):
        """Save student score to database with category."""
        with closing(self.conn.cursor()) as cursor:
            cursor.execute("""
                INSERT INTO scores (student_id, category, score, total_questions)
                VALUES (%s, %s, %s, %s)
            """, (student_id, category, score, total_questions))
            self.conn.commit()

    def get_scores(self, student_id):
        """Retrieve past scores along with categories for a given student."""
        with closing(self.conn.cursor()) as cursor:
            cursor.execute("""
                SELECT category, score, total_questions, timestamp 
                FROM scores 
                WHERE student_id = %s ORDER BY timestamp ASC
            """, (student_id,))
            return cursor.fetchall()

    def plot_progress(self, student_id):
        """Plot progress interactively using Plotly."""
        scores = self.get_scores(student_id)

        if not scores:
            st.warning("No previous scores found.")
            return

        # Convert data to Pandas DataFrame
        df = pd.DataFrame(scores, columns=["Category", "Marks", "Total Questions", "Timestamp"])
        df["Percentage"] = (df["Marks"] / df["Total Questions"]) * 100

        # Create interactive Plotly line chart
        fig = px.line(df, x="Timestamp", y="Percentage", text="Category",
              markers=True, title="📊 Exam Progress Over Time",
              custom_data=[df["Marks"], df["Total Questions"]])

        # Customize marker tooltips
        fig.update_traces(
            mode="markers+lines", 
            marker=dict(size=8, color="blue"),
            hovertemplate="<b>Category:</b> %{text}<br>"
                        "<b>Marks:</b> %{customdata[0]}/%{customdata[1]}<br>"
                        "<b>Percentage:</b> %{y:.1f}%<br>"
                        "<b>Time:</b> %{x}<extra></extra>"
        )

        # Show plot
        selected = st.plotly_chart(fig, use_container_width=True)

        # Display clicked data details
        click_data = st.session_state.get("click_data")
        if click_data:
            st.success(f"📌 *Category:* {click_data['Category']}\n\n"
                       f"🎯 *Marks:* {click_data['Marks']}/{click_data['Total Questions']}\n\n"
                       f"📅 *Date & Time:* {click_data['Timestamp']}\n\n"
                       f"📊 *Score Percentage:* {click_data['Percentage']:.1f}%")


if __name__ == "__main__":
    st.set_page_config(page_title="Student Score Tracker", layout="wide")
    st.title("📈 Track Student Exam Progress")

    tracker = ScoreTracker()

    # Creating a form for Student ID input
    with st.form(key="progress_form"):
        student_id = st.text_input("Enter Student ID to view progress:")
        submit_button = st.form_submit_button(label="Show Progress")

    # Plot only if the button is clicked
    if submit_button and student_id:
        tracker.plot_progress(student_id)