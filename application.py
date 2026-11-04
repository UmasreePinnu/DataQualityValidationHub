from html import escape

import streamlit as st
import Home, Connections, SchemaValidator, FileGenerator, FileComparator
import FactMetrics, KeysValidator, ColourFilter, ValidationReportGenerator
import MIDFileValidator
import AIIntegration
import AppStatistics
import auth

st.set_page_config(page_title="DQ Validation Hub", page_icon="📊", layout="wide")

auth.require_auth()

st.markdown(
    """
    <style>
    .st-key-user-header [data-testid="stHorizontalBlock"] {
        align-items: stretch;
        gap: 0.65rem;
    }
    .user-badge {
        min-height: 2.55rem;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 0.45rem;
        white-space: nowrap;
        color: #234357;
        font-size: 0.88rem;
    }
    .user-badge strong {
        font-weight: 700;
    }
    .user-badge-role {
        color: #718695;
        font-size: 0.8rem;
    }
    .st-key-user-header [data-testid="stButton"] {
        display: flex;
        justify-content: flex-end;
    }
    .st-key-user-header [data-testid="stBaseButton-secondary"] {
        min-height: 2.55rem;
        padding: 0.35rem 1rem;
        border: 1px solid #12636a;
        border-radius: 9px;
        color: #ffffff !important;
        background: #12636a !important;
        font-weight: 650;
        transition: background 150ms ease, box-shadow 150ms ease;
    }
    .st-key-user-header [data-testid="stBaseButton-secondary"]:hover {
        border-color: #0e5057;
        color: #ffffff !important;
        background: #0e5057 !important;
        box-shadow: 0 4px 12px rgba(18, 99, 106, 0.2);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.container(key="user-header"):
    header_spacer, user_info, logout_column = st.columns([8, 2.5, 1.3], gap="small")
    with user_info:
        username = escape(str(st.session_state.get("username", "")))
        role = escape(str(st.session_state.get("role", "")))
        st.markdown(
            f'<div class="user-badge"><strong>{username}</strong>'
            f'<span class="user-badge-role">· {role}</span></div>',
            unsafe_allow_html=True,
        )
    with logout_column:
        if st.button("Logout", use_container_width=True, key="logout"):
            auth.logout()

with st.sidebar:
    st.markdown('<div class="sidebar-logo"><span class="dot"></span>DQ Validation Hub</div>', unsafe_allow_html=True)
    nav_options = [
        "🏠  Home",
        "📈  Application Statistics",
        "🤖  AI DQ Orchestrator",
        "📋  Validation Report Generator",
        "🔍  Schema Validator",
        "📄  File Generator",
        "🔄  File Comparator",
        "📑  MID File Validator",
        "📊  Fact Metric Validator",
        "🔑  Keys Validator",
        "🎨  Colour Record Filter",
        "🔌  Connections",
    ]

    if "main_navigation" not in st.session_state:
        st.session_state["main_navigation"] = "🏠  Home"

    page = st.radio("Navigate", nav_options, label_visibility="collapsed", key="main_navigation")

pages = {
    "🏠  Home":                        Home,
    "📈  Application Statistics":       AppStatistics,
    "🤖  AI DQ Orchestrator":          AIIntegration,
    "📋  Validation Report Generator": ValidationReportGenerator,
    "🔍  Schema Validator":            SchemaValidator,
    "📄  File Generator":              FileGenerator,
    "🔄  File Comparator":             FileComparator,
    "📑  MID File Validator":          MIDFileValidator,
    "📊  Fact Metric Validator":       FactMetrics,
    "🔑  Keys Validator":              KeysValidator,
    "🎨  Colour Record Filter":        ColourFilter,
    "🔌  Connections":                 Connections,
}

pages[page].run()