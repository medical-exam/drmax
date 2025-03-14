import streamlit as st
import psycopg2
import pymysql
from dataclasses import dataclass
from contextlib import closing
from bs4 import BeautifulSoup  # ✅ Import for HTML cleaning
from calculate_score import ScoreCalculator

@dataclass
class StudentExamForm:
    def __init__(self):
        """Initialize database connection for PostgreSQL and MySQL."""
        # PostgreSQL Connection (for storing student exam data)
        self.postgres_conn = psycopg2.connect(
            dbname=st.secrets["POSTGRES_DB"],
            user=st.secrets["POSTGRES_USER"],
            password=st.secrets["POSTGRES_PASSWORD"],
            host=st.secrets["POSTGRES_HOST"],
            port=st.secrets["POSTGRES_PORT"]
        )

        # MySQL Connection (for fetching MCQs) using pymysql
        self.mysql_conn = pymysql.connect(
            host="13.201.239.165",
            user="ubuntu",
            password="LMS@12345",
            database="ukmed_live",
            port=3306,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True  # ✅ Prevents connection timeout issues
        )

        self.create_tables()

    def create_tables(self):
        """Create student_information table if not exists in PostgreSQL."""
        with closing(self.postgres_conn.cursor()) as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS student_information (
                    id SERIAL PRIMARY KEY,
                    student_id VARCHAR(50) NOT NULL,
                    student_name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    phone VARCHAR(20),
                    main_category VARCHAR(50),
                    sub_category VARCHAR(50),
                    difficulty_level VARCHAR(20),
                    duration_minutes INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.postgres_conn.commit()

    def get_categories(self):
        """Fetch available categories from the MySQL category table."""
        with closing(self.mysql_conn.cursor()) as cursor:
            cursor.execute("SELECT id, name FROM category WHERE status = 1")  # ✅ Fetch active categories
            categories = cursor.fetchall()
        return categories if categories else []

    def save_exam_data(self, exam_data):
        """Insert student exam data into PostgreSQL with error handling."""
        try:
            insert_query = """
            INSERT INTO student_information 
            (student_id, student_name, email, phone, main_category, sub_category, difficulty_level, duration_minutes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            with closing(self.postgres_conn.cursor()) as cursor:
                cursor.execute(insert_query, (
                    exam_data["id"],
                    exam_data["name"],
                    exam_data["email"],
                    exam_data["phone"],
                    exam_data["main_category"],  # ✅ Use correct column
                    exam_data["sub_category"],  # ✅ Include sub_category
                    exam_data["difficulty"],
                    exam_data["duration"]
                ))
                self.postgres_conn.commit()
        except Exception as e:
            self.postgres_conn.rollback()  # ✅ Rollback if any error occurs
            st.error(f"Database Error: {e}")  # ✅ Show error message in Streamlit



    def fetch_mcqs_with_options(self, category_id):
        """Fetch 20 MCQs with options based on the selected category."""
        try:
            if not self.mysql_conn.open:
                self.mysql_conn.ping(reconnect=True)

            with closing(self.mysql_conn.cursor()) as cursor:
                query_questions = """
                    SELECT DISTINCT qb.id AS question_id, qb.question 
                    FROM question_bank qb
                    JOIN question_category qc ON qb.id = qc.question_id
                    WHERE qc.category_id = %s
                    ORDER BY RAND()
                    LIMIT 10;
                """

                cursor.execute(query_questions, (category_id,))
                questions = cursor.fetchall()

                if not questions:
                    st.error("❌ No questions found for this category!")
                    return []

                # Extract question IDs
                question_ids = [str(q["question_id"]) for q in questions]

                # Fetch options for selected questions
                query_options = f"""
                    SELECT question_id, option_text
                    FROM question_options
                    WHERE question_id IN ({", ".join(question_ids)});
                """
                cursor.execute(query_options)
                options = cursor.fetchall()

                # Organize data into structured MCQs
                mcqs = {}
                for q in questions:
                    q_id = q["question_id"]
                    cleaned_question = BeautifulSoup(q["question"], "html.parser").get_text()  # ✅ Clean HTML
                    mcqs[q_id] = {
                        "question_id": q_id,  # ✅ Ensure question_id is included
                        "question": cleaned_question,
                        "options": []
                    }

                for opt in options:
                    q_id = opt["question_id"]
                    if q_id in mcqs:
                        cleaned_option = BeautifulSoup(opt["option_text"], "html.parser").get_text()  # ✅ Clean HTML
                        mcqs[q_id]["options"].append(cleaned_option)

                return list(mcqs.values())  # ✅ Return structured questions with options

        except pymysql.err.OperationalError as e:
            st.error(f"Database error: {e}")
            return []

    def display_form(self):
    
        # ✅ If exam has started, skip the form and show MCQs
        if st.session_state.get("exam_started", False):
            self.display_mcqs(st.session_state.mcqs)
            return {}, True  # ✅ Return a valid tuple

        st.subheader("📝 Student Information")

        col1, col2 = st.columns(2)
        with col1:
            student_name = st.text_input("Full Name", key="name")
            student_id = st.text_input("Student ID", key="id")
        with col2:
            email = st.text_input("Email", key="email")
            phone = st.text_input("Phone Number", key="phone")

        # ✅ Fetch categories dynamically
        categories = self.get_categories()
        category_dict = {c["name"]: c["id"] for c in categories}

        if not categories:
            st.error("❌ No categories found in the database!")
            return {}, False  # ✅ Ensure a tuple is returned

        selected_category = st.selectbox("Select Category", list(category_dict.keys()))
        difficulty_level = st.select_slider("Difficulty Level", ["Beginner", "Intermediate", "Advanced"], key="difficulty")
        time_preference = st.number_input("Exam Duration (minutes)", min_value=30, max_value=180, value=60, step=30, key="duration")

        start_exam = st.button("Start Exam")

        if start_exam:
            category_id = category_dict[selected_category]
            exam_data = {
                "name": student_name,
                "id": student_id,
                "email": email,
                "phone": phone,
                "main_category": selected_category,
                "sub_category": 'sub_category',
                "difficulty": difficulty_level,
                "duration": time_preference
            }
            st.session_state.student_id = student_id
            self.save_exam_data(exam_data)

            # ✅ Fetch and store MCQs
            mcqs = self.fetch_mcqs_with_options(category_id)
            if mcqs:
                st.session_state.mcqs = mcqs
                st.session_state.exam_started = True
                st.session_state.current_question = 0  # Reset index
                st.session_state.responses = {}  # Reset responses
                st.rerun()  # ✅ Force re-run to display MCQs immediately
            else:
                st.error("❌ No MCQs found for the selected category!")

        return {}, False  # ✅ Always return a valid tuple


    


    def display_mcqs(self, mcqs):
        """Display MCQs one by one after answering the previous question."""
        st.subheader("📝 Attempt the Exam")

        if not mcqs:
            st.error("❌ No MCQs found!")
            return

        # Initialize session state for tracking the current question
        if "current_question" not in st.session_state:
            st.session_state.current_question = 0
            st.session_state.responses = {}

        total_questions = len(mcqs)
        current_index = st.session_state.current_question
        current_mcq = mcqs[current_index]

        st.write(f"Q{current_index+1}. {current_mcq['question']}")

        # Radio button for answer selection
        question_id = str(current_mcq["question_id"])  # ✅ Ensure ID is stored as string

        selected_answer = st.radio(
            "Select an answer:",
            current_mcq["options"],
            index=None,  # Ensure no default selection
            key=f"q{question_id}"
        )
        if selected_answer:
            st.session_state.responses[question_id] = selected_answer
        
        col1, col2 = st.columns(2)
        
        if current_index > 0:
            if col1.button("⬅ Previous", key="prev"):
                st.session_state.current_question -= 1
                st.rerun()

        if current_index < total_questions - 1:
            if col2.button("➡ Next", key="next"):
                st.session_state.current_question += 1
                st.rerun()
        else:
            # Last question -> Show Submit button
            if st.button("✅ Submit Exam"):
                if len(st.session_state.responses) < total_questions:
                    st.warning("⚠ Please answer all questions before submitting!")
                else:
                    st.success("✅ Exam submitted successfully!")
                    score_calculator = ScoreCalculator()
                    score_calculator.display_results()

                    # Reset session state after submission
                    st.session_state.current_question = 0
                    st.session_state.responses = {}


# Streamlit App Execution
if __name__ == "__main__":
    st.set_page_config(page_title="Student Exam Form", layout="wide")
    st.title("🎓 Student Exam Registration")
    
    form = StudentExamForm()
    form.display_form()