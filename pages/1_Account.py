import streamlit as st
import json
import hashlib
import os
from pathlib import Path

st.set_page_config(page_title="Account", page_icon="👤")

# File to store user data
USER_DATA_FILE = Path(__file__).parent.parent / "users.json"

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load users from JSON file."""
    if USER_DATA_FILE.exists():
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Save users to JSON file."""
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def create_account(username, password, email):
    """Create a new user account."""
    users = load_users()
    if username in users:
        return False, "Username already exists"
    
    users[username] = {
        "password": hash_password(password),
        "email": email,
        "account_type": "free"
    }
    save_users(users)
    return True, "Account created successfully"

def login(username, password):
    """Authenticate a user."""
    users = load_users()
    if username not in users:
        return False, "Username not found"
    
    if users[username]["password"] == hash_password(password):
        return True, "Login successful"
    return False, "Incorrect password"

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

# Display account page
if st.session_state.logged_in:
    st.title(f"👤 Account: {st.session_state.username}")
    
    users = load_users()
    user_data = users.get(st.session_state.username, {})
    
    st.subheader("Account Information")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Username", st.session_state.username)
        st.metric("Email", user_data.get("email", "N/A"))
    with col2:
        account_type = user_data.get("account_type", "free").upper()
        st.metric("Account Type", account_type)
        if account_type == "FREE":
            st.info("💎 Upgrade to Premium for exclusive features!")
    
    st.divider()
    
    if st.button("🚪 Logout", type="secondary"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()
else:
    st.title("👤 Account")
    
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
        st.subheader("Login")
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", type="primary"):
            if login_username and login_password:
                success, message = login(login_username, login_password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = login_username
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("Please enter both username and password")
    
    with tab2:
        st.subheader("Create New Account")
        new_username = st.text_input("Username", key="new_username")
        new_email = st.text_input("Email", key="new_email")
        new_password = st.text_input("Password", type="password", key="new_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        
        if st.button("Create Account", type="primary"):
            if new_username and new_email and new_password and confirm_password:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    success, message = create_account(new_username, new_password, new_email)
                    if success:
                        st.success(message)
                        st.info("You can now login with your credentials")
                    else:
                        st.error(message)
            else:
                st.warning("Please fill in all fields")
