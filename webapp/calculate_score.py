import streamlit as st
import psycopg2
import pymysql
from contextlib import closing
from score_tracker import ScoreTracker
from openai import OpenAI  # Ensure you have OpenAI API access

class AIExplanation:
    def __init__(self):
        self.client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])  # Ensure API key is stored in secrets

    def generate_explanation(self, question_text, correct_answer, student_answer):
        """You are Dr. Max, a medical mentor specializing in exam preparation.
            Provide clear, concise explanations for MCQs. When users answer incorrectly, explain their mistake and 
            guide them toward the correct reasoning."""
        prompt = f"""
        Question: {question_text}
        Student's Answer: {student_answer}
        Correct Answer: {correct_answer}
        
        Explain why the correct answer is right and why the student's answer might be incorrect.make sure explaination must be sort in 1-2 line maximum. 
        """

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content


class ScoreCalculator:
    def __init__(self):
        """Initialize database connections."""
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
        self.ai_explainer = AIExplanation()

    def get_correct_answers_with_questions(self, question_ids):
        """Fetch question texts and correct answers from MySQL."""
        if not question_ids:
            return {}

        formatted_ids = ", ".join(map(str, question_ids))

        query = f"""
            SELECT q.id AS question_id, q.question, o.option_text AS correct_answer
            FROM question_bank q
            JOIN question_options o ON q.id = o.question_id
            WHERE q.id IN ({formatted_ids}) AND o.is_correct = 1;
        """

        with closing(self.mysql_conn.cursor()) as cursor:
            cursor.execute(query)
            results = cursor.fetchall()

        # ✅ Store both question texts and correct answers
        return {str(row["question_id"]): {"question_text": row["question"], "correct_answer": row["correct_answer"]}
        for row in results}

    def calculate_score(self, student_responses):
        """Compare student responses with correct answers and calculate score."""
        question_ids = list(student_responses.keys())  
        correct_answers = self.get_correct_answers_with_questions(question_ids)  

        score = 0
        total_questions = len(question_ids)

        for q_id, student_answer in student_responses.items():
            correct_answer = correct_answers.get(str(q_id), {}).get("correct_answer", "N/A")
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
            category = st.session_state.get("current_category", "Unknown")  
            st.session_state.score_tracker.save_score(student_id, category, score, total)
            st.success(f"✅ Your Score: {score} / {total}")
            st.progress(score / total)

            # Fetch correct answers along with question texts
            question_data = self.get_correct_answers_with_questions(st.session_state.responses.keys())

            for index, (q_id, student_answer) in enumerate(st.session_state.responses.items(), start=1):
                data = question_data.get(str(q_id), {"question_text": "Unknown", "correct_answer": "N/A"})
                question_text = data["question_text"]
                correct = data["correct_answer"]
                is_correct = "✅" if student_answer == correct else "❌"

                
                st.write(f"Q{index} You selected: {is_correct} {student_answer}  | ✅ Correct Answer: {correct}")

                # Generate AI explanation for incorrect answers
                if student_answer != correct:
                    explanation = self.ai_explainer.generate_explanation(question_text, correct, student_answer)
                    st.warning(f"🤖 AI Explanation: {explanation}")

            st.session_state.responses = {}


# Streamlit Execution
if __name__ == "__main__":
    st.set_page_config(page_title="Exam Score Calculator", layout="wide")
    st.title("🎯 Exam Score Calculation")
    
    calculator = ScoreCalculator()
    calculator.display_results()