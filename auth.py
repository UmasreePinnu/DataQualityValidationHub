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
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            min-height: 100vh;
            background:
                radial-gradient(ellipse at 12% 8%, rgba(35, 112, 145, 0.18), transparent 34%),
                linear-gradient(135deg, #f3f7fb 0%, #e8f0f7 55%, #eef4f7 100%);
        }
        [data-testid="stHeader"], [data-testid="stToolbar"] {
            background: transparent;
        }
        [data-testid="stMainBlockContainer"] {
            max-width: 1120px;
            padding: clamp(1.5rem, 5vh, 3.75rem) 1.5rem 2rem;
        }
        .st-key-login-page [data-testid="stHorizontalBlock"] {
            align-items: stretch;
            gap: clamp(1.25rem, 4vw, 3.5rem);
        }
        .login-intro {
            min-height: 500px;
            height: 100%;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: clamp(2rem, 4vw, 3.5rem);
            overflow: hidden;
            position: relative;
            border-radius: 24px;
            color: #f4fbff;
            background:
                radial-gradient(ellipse at 90% 8%, rgba(73, 190, 185, 0.28), transparent 38%),
                linear-gradient(145deg, #102d43 0%, #123d51 54%, #12636a 100%);
            box-shadow: 0 24px 60px rgba(19, 53, 72, 0.17);
        }
        .login-brand {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 0.95rem;
            font-weight: 700;
            letter-spacing: 0.015em;
        }
        .login-brand-mark {
            width: 42px;
            height: 42px;
            display: grid;
            place-items: center;
            border: 1px solid rgba(198, 246, 239, 0.35);
            border-radius: 13px;
            color: #b6f2e7;
            background: rgba(235, 255, 251, 0.1);
            font-size: 1rem;
            font-weight: 800;
        }
        .login-copy {
            max-width: 470px;
            margin: 3rem 0;
        }
        .login-eyebrow {
            margin: 0 0 1rem;
            color: #9de8d9;
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }
        .login-copy h1 {
            margin: 0;
            color: #f7fbff;
            font-size: clamp(2rem, 4vw, 3.15rem);
            line-height: 1.08;
            letter-spacing: -0.045em;
        }
        .login-copy > p:last-child {
            max-width: 400px;
            margin: 1.1rem 0 0;
            color: rgba(230, 243, 249, 0.76);
            font-size: 1rem;
            line-height: 1.7;
        }
        .login-feature-list {
            display: grid;
            gap: 0.9rem;
        }
        .login-feature {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            color: rgba(240, 250, 252, 0.9);
            font-size: 0.91rem;
        }
        .login-feature-icon {
            width: 29px;
            height: 29px;
            display: grid;
            place-items: center;
            flex: 0 0 29px;
            border-radius: 9px;
            color: #adf1e4;
            background: rgba(222, 255, 250, 0.11);
            font-size: 0.8rem;
        }
        .st-key-login-card {
            min-height: 500px;
            height: 100%;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: clamp(1.75rem, 4vw, 3.25rem);
            border: 1px solid #e5ebf0;
            border-radius: 24px;
            background: #ffffff;
            box-shadow: 0 24px 60px rgba(32, 57, 78, 0.09);
        }
        .login-card-heading {
            margin-bottom: 1.6rem;
        }
        .login-card-heading h2 {
            margin: 0;
            color: #183347;
            font-size: clamp(1.7rem, 3vw, 2.15rem);
            letter-spacing: -0.035em;
        }
        .login-card-heading p {
            margin: 0.55rem 0 0;
            color: #718191;
            font-size: 0.96rem;
        }
        .st-key-login-card [data-testid="stForm"] {
            padding: 0;
            border: 0;
            background: transparent;
        }
        .st-key-login-card [data-testid="stTextInput"] label {
            color: #30495c;
            font-size: 0.88rem;
            font-weight: 650;
        }
        .st-key-login-card [data-testid="stTextInput"] input {
            min-height: 3rem;
            border: 1px solid #d6e0e7;
            border-radius: 10px;
            color: #183347;
            background: #fbfdfe;
            font-size: 0.96rem;
            transition: border-color 150ms ease, box-shadow 150ms ease;
        }
        .st-key-login-card [data-testid="stTextInput"] input:focus {
            border-color: #178a83;
            box-shadow: 0 0 0 3px rgba(23, 138, 131, 0.13);
        }
        .st-key-login-card [data-testid="stFormSubmitButton"] button {
            min-height: 3rem;
            margin-top: 0.55rem;
            border: 0;
            border-radius: 10px;
            color: #ffffff;
            background: linear-gradient(100deg, #147c79, #146477);
            font-size: 0.96rem;
            font-weight: 700;
            transition: transform 150ms ease, box-shadow 150ms ease, filter 150ms ease;
        }
        .st-key-login-card [data-testid="stFormSubmitButton"] button:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 18px rgba(20, 124, 121, 0.22);
            filter: brightness(1.06);
        }
        .login-help {
            margin: 1.1rem 0 0;
            color: #82909b;
            font-size: 0.82rem;
            line-height: 1.6;
        }
        @media (max-width: 760px) {
            [data-testid="stMainBlockContainer"] {
                padding: 1rem 0.85rem 1.5rem;
            }
            .login-intro {
                min-height: auto;
                padding: 1.6rem;
            }
            .login-copy {
                margin: 2rem 0 1.5rem;
            }
            .login-copy h1 {
                font-size: 2rem;
            }
            .login-feature-list {
                grid-template-columns: repeat(auto-fit, minmax(155px, 1fr));
                gap: 0.65rem;
            }
            .st-key-login-card {
                min-height: auto;
                padding: 1.6rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(key="login-page"):
        intro, login = st.columns([1.08, 0.92], gap="large")
        with intro:
            st.markdown(
                """
                <section class="login-intro">
                    <div class="login-brand">
                        <span class="login-brand-mark">DQ</span>
                        <span>Data Quality Validation Hub</span>
                    </div>
                    <div class="login-copy">
                        <p class="login-eyebrow">Reliable data starts here</p>
                        <h1>Confidence in every dataset.</h1>
                        <p>Bring your validation workflows together and spot data issues before they reach production.</p>
                    </div>
                    <div class="login-feature-list">
                        <div class="login-feature"><span class="login-feature-icon">✓</span>Schema and key validation</div>
                        <div class="login-feature"><span class="login-feature-icon">↔</span>File and data comparison</div>
                        <div class="login-feature"><span class="login-feature-icon">▤</span>Metrics and clear reports</div>
                    </div>
                </section>
                """,
                unsafe_allow_html=True,
            )

        with login:
            with st.container(key="login-card"):
                st.markdown(
                    """
                    <div class="login-card-heading">
                        <h2>Welcome back</h2>
                        <p>Sign in to continue to your workspace.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                with st.form("login_form", clear_on_submit=False):
                    username = st.text_input("Username", placeholder="Enter your username")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    submitted = st.form_submit_button("Sign in", use_container_width=True)

                if submitted:
                    config = load_auth_config()
                    users = config.get("users", {})
                    user = users.get(username.strip())
                    if user and user.get("password") == password:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = username.strip()
                        st.session_state["role"] = user.get("role", "user")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")

                st.markdown(
                    '<p class="login-help">Use your assigned workspace credentials. Contact your administrator if you need access.</p>',
                    unsafe_allow_html=True,
                )


def require_auth():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if not st.session_state["authenticated"]:
        login_form()
        st.stop()


def logout():
    for key in ["authenticated", "username", "role"]:
        st.session_state.pop(key, None)
    st.rerun()
