import streamlit as st
from datetime import datetime

def init_session_state():
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None
    if "user_info" not in st.session_state:
        st.session_state.user_info = None

def check_auth() -> bool:
    return st.session_state.get("auth_token") is not None

def format_date(iso_string: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return iso_string
