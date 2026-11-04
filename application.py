import streamlit as st
import Home, Connections, SchemaValidator, FileGenerator, FileComparator
import FactMetrics, KeysValidator, ColourFilter, ValidationReportGenerator
import MIDFileValidator
import AIIntegration
import AppStatistics
import auth

st.set_page_config(page_title="DQ Validation Hub", page_icon="📊", layout="wide")

auth.require_auth()

header_spacer, user_info, logout_column = st.columns([8, 2, 1.3])
with user_info:
    st.caption(
        f"Signed in as **{st.session_state.get('username')}** · "
        f"{st.session_state.get('role')}"
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