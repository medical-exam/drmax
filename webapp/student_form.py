import streamlit as st
import psycopg2
from dataclasses import dataclass

@dataclass 
class StudentExamForm:
    def __init__(self):
        # Connect using existing credentials from secrets.toml
        self.conn = psycopg2.connect(
            dbname=st.secrets["POSTGRES_DB"],
            user=st.secrets["POSTGRES_USER"],
            password=st.secrets["POSTGRES_PASSWORD"],
            host=st.secrets["POSTGRES_HOST"],
            port=st.secrets["POSTGRES_PORT"]
        )
        self.cursor = self.conn.cursor()
        self.create_exam_tables()
        
        # Category definitions
        self.categories = {
            "Mathematics": ["Algebra", "Calculus", "Geometry", "Statistics"],
            "Physics": ["Mechanics", "Thermodynamics", "Electromagnetism", "Quantum Physics"],
            "Chemistry": ["Organic", "Inorganic", "Physical Chemistry", "Biochemistry"],
            "Biology": ["Anatomy", "Genetics", "Ecology", "Microbiology"],
            "Computer Science": ["Programming", "Data Structures", "Algorithms", "Database"]
        }

    def create_exam_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_exams (
                id SERIAL PRIMARY KEY,
                student_id VARCHAR(50) NOT NULL,
                student_name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                phone VARCHAR(20),
                grade_level VARCHAR(20),
                main_category VARCHAR(50),
                sub_category VARCHAR(50),
                difficulty_level VARCHAR(20),
                duration_minutes INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def save_exam_data(self, exam_data):
        insert_query = """
        INSERT INTO student_exams 
        (student_id, student_name, email, phone, grade_level, 
         main_category, sub_category, difficulty_level, duration_minutes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        self.cursor.execute(insert_query, (
            exam_data["id"],
            exam_data["name"],
            exam_data["email"],
            exam_data["phone"],
            exam_data["grade"],
            exam_data["main_category"],
            exam_data["sub_category"],
            exam_data["difficulty"],
            exam_data["duration"]
        ))
        self.conn.commit()

        
    def display_form(self):
        with st.form("student_exam_form"):
            st.subheader("📝 Student Information")
            
            # Personal Details Section
            col1, col2 = st.columns(2)
            with col1:
                student_name = st.text_input("Full Name")
                student_id = st.text_input("Student ID")
            with col2:
                email = st.text_input("Email")
                phone = st.text_input("Phone Number")
            
            # Academic Details
            col3, col4 = st.columns(2)
            with col3:
                grade_level = st.selectbox("Grade Level", 
                    ["Freshman", "Sophomore", "Junior", "Senior"])
                main_category = st.selectbox("Select Main Category", 
                    options=list(self.categories.keys()))
            with col4:
                sub_category = st.selectbox("Select Sub Category",
                    options=self.categories[main_category])
                difficulty_level = st.select_slider("Difficulty Level",
                    options=["Beginner", "Intermediate", "Advanced"])
            
            # Exam Preferences
            time_preference = st.number_input("Exam Duration (minutes)",
                min_value=30, max_value=180, value=60, step=30)
            
            submitted = st.form_submit_button("Start Exam")
            
            if submitted:
                if student_name and student_id and email:
                    exam_data = {
                        "name": student_name,
                        "id": student_id,
                        "email": email,
                        "phone": phone,
                        "grade": grade_level,
                        "main_category": main_category,
                        "sub_category": sub_category,
                        "difficulty": difficulty_level,
                        "duration": time_preference
                    }
                    self.save_exam_data(exam_data)
                    return exam_data, True
                st.warning("Please fill all required fields")
            return None, False
