import streamlit as st
import psycopg2
import pymysql
from contextlib import closing
from score_tracker import ScoreTracker

class ScoreCalculator:
    def __init__(self):
        """Initialize database connection."""
        self.postgres_conn = psycopg2.connect(
            dbname=st.secrets["POSTGRES_DB"],
            user=st.secrets["POSTGRES_USER"],
            password=st.secrets["POSTGRES_PASSWORD"],
            host=st.secrets["POSTGRES_HOST"],
            port=st.secrets["POSTGRES_PORT"]
        )
        self.mysql_conn = pymysql.connect(
            host="13.201.239.165",
            user="ubuntu",
            password="LMS@12345",
            database="ukmed_live",
            port=3306,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
    
    
    def get_correct_answers(self, question_ids):
        """Fetch correct answers from MySQL based on question IDs."""
        if not question_ids:
            return {}

        # ✅ Ensure question_ids are correctly formatted as strings for SQL query
        formatted_ids = ", ".join(map(str, question_ids))

        query = f"""
            SELECT question_id, option_text 
            FROM question_options 
            WHERE question_id IN ({formatted_ids}) 
            AND is_correct = 1;
        """

        with closing(self.mysql_conn.cursor()) as cursor:
            cursor.execute(query)
            correct_options = cursor.fetchall()

        # ✅ Ensure the dictionary stores answers with *matching types*
        return {str(opt["question_id"]): opt["option_text"] for opt in correct_options}

    
    def calculate_score(self, student_responses):
        """Compare student responses with correct answers and calculate score."""
        question_ids = list(student_responses.keys())  # ✅ Get stored question IDs
        correct_answers = self.get_correct_answers(question_ids)  # ✅ Fetch correct answers

        score = 0
        total_questions = len(question_ids)

        for q_id, student_answer in student_responses.items():
            correct_answer = correct_answers.get(str(q_id), "N/A")  # ✅ Ensure key lookup matches type
            if student_answer == correct_answer:
                score += 1

        return score, total_questions

    
    def display_results(self):
        with st.expander("📊 Exam result", expanded=True):
                st.markdown(f'<div class="report-box"></div>', unsafe_allow_html=True)

            
                if "responses" not in st.session_state or not st.session_state.responses:
                    st.warning("⚠ No responses found! Complete the exam first.")
                    return
                
                score, total = self.calculate_score(st.session_state.responses)
                student_id = st.session_state.get("student_id", "unknown")
                st.session_state.score_tracker.save_score(student_id,score, total)
                st.success(f"✅ Your Score: {score} / {total}")
                st.progress(score / total)
                
                # Show detailed response analysis
                st.write("### Your Responses vs Correct Answers")
                correct_answers = self.get_correct_answers(st.session_state.responses.keys())
                
                for index, (q_id, student_answer) in enumerate(st.session_state.responses.items(), start=1):
                    correct = correct_answers.get(str(q_id), "N/A")
                    is_correct = "✅" if student_answer == correct else "❌"
                    st.write(f"*Q{index}:* You selected: {student_answer} | Correct Answer: {correct} {is_correct}")

                st.session_state.responses = {}

# Streamlit Execution
if __name__ == "__main__":
    st.set_page_config(page_title="Exam Score Calculator", layout="wide")
    st.title("🎯 Exam Score Calculation")
    
    calculator = ScoreCalculator()
    calculator.display_results()