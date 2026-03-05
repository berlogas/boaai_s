import streamlit as st
from core.api_client import api_client

st.set_page_config(page_title="BOAAI_S", page_icon="🔬", layout="wide")

if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "current_session" not in st.session_state:
    st.session_state.current_session = None

if st.session_state.auth_token:
    api_client.token = st.session_state.auth_token
    api_client.role = st.session_state.user_info.get("role") if st.session_state.user_info else None

if not st.session_state.auth_token:
    st.switch_page("pages/05_🔐_Login.py")
else:
    with st.sidebar:
        st.title("🔬 BOAAI_S")
        st.markdown("---")
        if st.session_state.user_info:            
            st.write(f"👤 **{st.session_state.user_info.get('username')}**")
            st.write(f"🎭 Роль: `{st.session_state.user_info.get('role')}`")
        st.markdown("---")
        page = st.radio("Навигация", ["🏠 Дашборд", "💼 Рабочее пространство", "📊 Проекты"])
        if st.session_state.user_info.get("role") == "admin":
            page = st.radio("Навигация", ["🏠 Дашборд", "💼 Рабочее пространство", "📊 Проекты", "⚙️ Админ-панель"])
        st.markdown("---")
        if st.button("🚪 Выйти", use_container_width=True):
            st.session_state.auth_token = None
            st.session_state.user_info = None
            st.session_state.current_session = None
            st.rerun()
    
    if page == "🏠 Дашборд":
        st.switch_page("pages/01_🏠_Dashboard.py")
    elif page == "💼 Рабочее пространство":
        st.switch_page("pages/02_💼_Workspace.py")
    elif page == "📊 Проекты":
        st.switch_page("pages/03_📊_Projects.py")
    elif page == "⚙️ Админ-панель":
        st.switch_page("pages/04_⚙️_Admin.py")
