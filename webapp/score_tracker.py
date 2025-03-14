import psycopg2
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
from contextlib import closing
import matplotlib.dates as mdates

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
                CREATE TABLE IF NOT EXISTS exam_scores (
                    id SERIAL PRIMARY KEY,
                    student_id VARCHAR(50) NOT NULL,
                    score INTEGER NOT NULL,
                    total_questions INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()

    def save_score(self, student_id, score, total_questions):
        """Save student score to database."""
        with closing(self.conn.cursor()) as cursor:
            cursor.execute("""
                INSERT INTO exam_scores (student_id, score, total_questions)
                VALUES (%s, %s, %s)
            """, (student_id, score, total_questions))
            self.conn.commit()

    def get_scores(self, student_id):
        """Retrieve past scores for a given student."""
        with closing(self.conn.cursor()) as cursor:
            cursor.execute("""
                SELECT score, total_questions, timestamp FROM exam_scores 
                WHERE student_id = %s ORDER BY timestamp ASC
            """, (student_id,))
            return cursor.fetchall()

    def plot_progress(self, student_id):
        """Plot a graph of scores over time with correct date formatting."""
        scores = self.get_scores(student_id)

        if not scores:
            st.warning("No previous scores found.")
            return

        # Convert timestamps explicitly
        timestamps = [row[2] for row in scores]  # Ensure timestamps are in correct datetime format
        score_percentages = [(row[0] / row[1]) * 100 for row in scores]

        col1, col2, col3 = st.columns([1, 4, 1])  # Center the plot

        with col2:  
            fig, ax = plt.subplots(figsize=(4, 3), dpi=150)
            ax.plot(timestamps, score_percentages, marker='o', linestyle='-', color='b', label="Score %")

            ax.set_xlabel("Date & Time", fontsize=8)
            ax.set_ylabel("Score (%)", fontsize=8)
            ax.set_title("📊 Exam Progress Over Time", fontsize=10)
            ax.set_ylim(0, 100)
            ax.grid(True, linestyle="--", alpha=0.7)

            # Fix x-axis formatting
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            plt.xticks(rotation=45, fontsize=6)
            plt.yticks(fontsize=6)

            ax.legend(loc="upper left", fontsize=6)
            st.pyplot(fig)

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
