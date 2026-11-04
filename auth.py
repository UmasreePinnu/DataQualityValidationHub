import json
import os
import streamlit as st


AUTH_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "auth_config.json")


def load_auth_config():
    try:
        with open(AUTH_CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"users": {}}


def login_form():
    st.markdown("### 🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        config = load_auth_config()
        users = config.get("users", {})
        user = users.get(username)
        if user and user.get("password") == password:
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.session_state["role"] = user.get("role", "user")
            st.rerun()
        else:
            st.error("Invalid username or password")
    st.info("Sample users: admin/admin123, demo/demo123, qa/qa123, analyst/analyst123, viewer/viewer123")


def require_auth():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if not st.session_state["authenticated"]:
        login_form()
        st.stop()
    with st.sidebar:
        st.write(f"👤 {st.session_state.get('username')} ({st.session_state.get('role')})")
        if st.button("Logout"):
            for key in ["authenticated", "username", "role"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
