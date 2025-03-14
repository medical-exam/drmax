import streamlit as st
import os
import psycopg2
import bcrypt

# Database Connection
def auth():
    st.markdown("""
<style>
              
        

        [data-testid="stSidebar"] {
        background: #f3e8ff !important;;
        
        }

            body { background-color: #121212; color: white; margin-right:100px}
        
            .stTextInput > div > div > input {
                background-color: rgb(220, 214, 238) !important;
                color: black !important;
                border: 2px solid transparent !important;  /* Removes the red border */
                border-radius: 8px !important;
                padding: 10px !important;
                transition: border-color 0.3s ease-in-out !important;
            }

            .stTextInput > div > div > input:focus {
                border: 2px solid rgb(173, 149, 213) !important; /* Adds a soft purple focus border */
                outline: none !important;
                text-color:black;
            }

            .stButton > button {
                background-color: #9575CD !important;
                color: white !important;
                font-size: 19px !important; 
                width:85%;
                transform: scale(1.05); /* Slightly enlarge active tab */
                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.2); /* More depth */
            }

            .stButton > button:hover {
                background-color: #D1C4E9 !important;            
            }
    
            .stChatMessage {
                border-radius: 12px; 
                padding: 12px; 
                margin-bottom: 12px;
            }

            .stChatMessage-user {
                background-color: #333333; 
                color: white;
            }

            .stChatMessage-assistant {
                background-color: #2d2d2d; 
                color:rgb(217, 205, 235);
            }
            div[data-testid="stHorizontalBlock"] {
            display: flex;
            justify-content: center;
            margin-bottom: 15px !important;
        }

        /* Style the individual radio buttons */
        div[data-testid="stRadio"] label {
            font-size: 18px !important;
            font-weight: bold !important;
            color: #6B52AE !important;  /* Purple */
            background-color: #EDE7F6 !important;
            border-radius: 25px !important; /* More rounded */
            padding: 14px 22px !important; /* Increased padding */
            margin: 8px !important; /* Adds spacing between options */
            transition: all 0.3s ease-in-out;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1); /* Soft shadow */
            cursor: pointer;
        }

        /* Hover effect */
        div[data-testid="stRadio"] label:hover {
            background-color: #D1C4E9 !important;
        }

        /* Active (selected) button */
        div[data-testid="stRadio"] label[data-testid="stMarkdownContainer"] {
            background-color: #9575CD !important;
            color: white !important;
            font-size: 19px !important;
            transform: scale(1.05); /* Slightly enlarge active tab */
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.2); /* More depth */
        }
            .stMarkdown { font-size: 16px; }
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

    
    
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "selected_tab" not in st.session_state:
        st.session_state["selected_tab"] = "Login"

    with st.container():
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown('<div class="left-panel">', unsafe_allow_html=True)
            
            
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            if not st.session_state["logged_in"]:
                if st.session_state["selected_tab"] == "Login":
                    st.header("Welcome back 👋")
                    st.write("Please enter your details")
                    st.subheader("🔑 Login")

                    email = st.text_input("Email", key="login_email")
                    password = st.text_input("Password", type="password", key="login_password")
                    if st.button("Login"):
                        login(email, password)
                    if st.button("Don't have an account? Sign up"):
                        st.session_state["selected_tab"] = "Signup"
                        st.rerun()

                elif st.session_state["selected_tab"] == "Signup":
                    st.header("Welcome Back!")
                    st.write("Create your account to get started.")

                    new_email = st.text_input("Email", key="signup_email")
                    new_password = st.text_input("Password", type="password", key="signup_password")
                    if st.button("Signup"):
                        signup(new_email, new_password)
                    if st.button("Already have an account? Login"):
                        st.session_state["selected_tab"] = "Login"
                        st.rerun()

        

            
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="right-panel">', unsafe_allow_html=True)
            st.image("s1.jpg", width=600)  # Illustration might be missing
            st.markdown('</div>', unsafe_allow_html=True)

    
    # If logged in, display welcome message
    if st.session_state["logged_in"]:
        st.subheader(f"Welcome, {st.session_state['email']}! 🎉")
        if st.button("Logout"):
            logout()