import streamlit as st
import psycopg2
import bcrypt

# Database Connection
def auth():
    st.markdown("""
    <style>
        .form-box {
            width: 70%;
            max-width: 400px;
            padding: 30px;
            border-radius: 10px;
            background: white;
            box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        .stTextInput>div>div>input {
            border-radius: 8px;
            padding: 10px;
            font-size: 14px;
            width: 50%;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            font-size: 16px;
            padding: 10px;
            border-radius: 8px;
            width: 50%;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
    </style>
    """, unsafe_allow_html=True)

    def get_db_connection():
        return psycopg2.connect(
            dbname=st.secrets["POSTGRES_DB"],
            user=st.secrets["POSTGRES_USER"],
            password=st.secrets["POSTGRES_PASSWORD"],
            host=st.secrets["POSTGRES_HOST"],
            port=st.secrets["POSTGRES_PORT"]
        )

    def create_users_table():
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()

    create_users_table()

    def hash_password(password):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def check_password(password, hashed):
        return bcrypt.checkpw(password.encode(), hashed.encode())

    def signup(email, password):
        conn = get_db_connection()
        cur = conn.cursor()
        hashed_pw = hash_password(password)
        try:
            cur.execute("INSERT INTO users (email, password_hash) VALUES (%s, %s)", (email, hashed_pw))
            conn.commit()
            st.success("✅ Account created successfully! Please log in.")
            st.session_state["selected_tab"] = "Login"
            st.rerun()
        except psycopg2.errors.UniqueViolation:
            st.error("⚠ Email already registered. Please log in.")
        finally:
            cur.close()
            conn.close()

    def login(email, password):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user and check_password(password, user[0]):
            st.session_state["logged_in"] = True
            st.session_state["email"] = email
            st.success("✅ Login successful!")
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("⚠ Invalid email or password.")

    def logout():
        st.session_state.clear()
        st.success("👋 Logged out successfully!")
        st.rerun()

    # Session state for login
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "selected_tab" not in st.session_state:
        st.session_state["selected_tab"] = "Login"

    # Sidebar logout button (Visible when logged in)
    if st.session_state["logged_in"]:
        with st.sidebar:
            st.subheader(f"👤 {st.session_state['email']}")
            if st.button("🚪 Logout"):
                logout()

    col1, col2, col3 = st.columns([1, 2, 1])  # Middle column is wider

    with col2:
        st.markdown('<div class="form-box">', unsafe_allow_html=True)

        if not st.session_state["logged_in"]:
            if st.session_state["selected_tab"] == "Login":
                st.subheader("🔑 Login")
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                if st.button("Login"):
                    login(email, password)
                if st.button("Don't have an account? Sign up"):
                    st.session_state["selected_tab"] = "Signup"
                    st.rerun()

            elif st.session_state["selected_tab"] == "Signup":
                st.subheader("📝 Signup")
                new_email = st.text_input("Email", key="signup_email")
                new_password = st.text_input("Password", type="password", key="signup_password")
                if st.button("Signup"):
                    signup(new_email, new_password)
                if st.button("Already have an account? Login"):
                    st.session_state["selected_tab"] = "Login"
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # If logged in, display welcome message
    if st.session_state["logged_in"]:
        st.subheader(f"Welcome, {st.session_state['email']}! 🎉")
