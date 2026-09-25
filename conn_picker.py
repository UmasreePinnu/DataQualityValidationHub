import streamlit as st
from connection_manager import load_profiles

def render_picker(label: str, key: str) -> dict:
    profiles = load_profiles()
    if not profiles:
        st.warning("No profiles saved. Go to Connections.", icon="🔌")
        return {}

    options = ["— select a profile —"] + list(profiles.keys())
    col1, col2 = st.columns([4, 1])
    with col1:
        selected = st.selectbox(label, options, key=f"picker_{key}")
    with col2:
        st.markdown("<div style='padding-top:28px'></div>", unsafe_allow_html=True)
        if st.button("＋ New", key=f"picker_new_{key}"):
            st.session_state["goto_connections"] = True
            st.rerun()

    if selected == "— select a profile —":
        return {}

    p = profiles[selected]
    st.caption(f"🔵 **{p.get('type')}** · {p.get('server', p.get('dsn'))}")
    return p