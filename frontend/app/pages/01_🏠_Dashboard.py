import streamlit as st
from core.api_client import api_client

user_info = st.session_state.get("user_info", {})
username = user_info.get("username", "Исследователь")
st.title(f"🔬 Исследователь {username}")

st.markdown("### ⚡ Быстрый вопрос")
query = st.text_input("Ваш вопрос", placeholder="Спросите о чём-нибудь...")
if st.button("🔍 Найти"):
    if query:
        with st.spinner("Поиск..."):
            result = api_client.quick_query(query)
            if result:
                st.write(result.get("answer", "Нет ответа"))
            else:
                st.error("Ошибка при получении ответа")

st.markdown("---")
st.markdown("### 📁 Ваши сессии")

col1, col2 = st.columns([3, 1])
with col1:
    st.caption("Сессии сохраняются 90 дней")
with col2:
    new_session_name = st.text_input("Новая сессия", placeholder="Название...")
    if st.button("➕ Создать", use_container_width=True):
        if new_session_name:
            session = api_client.create_session(new_session_name)
            if session:
                st.success(f"Сессия '{new_session_name}' создана!")
                st.session_state["current_session"] = session
                st.rerun()

sessions = api_client.get_sessions()
if not sessions:
    st.info("📭 Нет активных сессий")
else:
    for session in sessions[:5]:
        with st.container():
            st.markdown(f"**🟢 {session['name']}**")
            st.caption(f"Документов: {len(session.get('documents', []))} | Последнее: {session.get('last_action', 'N/A')}")
            if st.button("▶️ Продолжить", key=f"resume_{session['id']}"):
                st.session_state["current_session"] = session
                st.rerun()            
                st.markdown("---")
