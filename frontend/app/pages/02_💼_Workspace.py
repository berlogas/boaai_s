import streamlit as st
from core.api_client import api_client

st.title("💼 Рабочее пространство")

if "current_session" not in st.session_state or not st.session_state.current_session:
    sessions = api_client.get_sessions()
    if sessions:
        st.session_state["current_session"] = sessions[0]
    else:
        st.warning("📭 Нет сессий. Создайте на дашборде.")
        st.stop()

session = st.session_state.current_session
st.markdown(f"### 📁 {session['name']}")

tab1, tab2 = st.tabs(["💬 Чат", "📄 Документы"])

with tab1:
    mode = st.selectbox("Режим поиска", ["hybrid", "session_only", "global_only"], key="search_mode")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Отображение истории
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Обработка отправки
    def send_message():
        prompt = st.session_state.chat_text_input
        if prompt:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            with st.spinner("Генерация..."):
                result = api_client.query(query=prompt, session_id=session["id"], mode=mode)
                if result:
                    st.session_state.chat_history.append({"role": "assistant", "content": result["answer"]})

    # Поле ввода с кнопкой в одной строке
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([10, 1])
        with col1:
            st.text_input("Спросите...", key="chat_text_input", label_visibility="collapsed", placeholder="Введите вопрос и нажмите Enter...")
        with col2:
            st.form_submit_button("➤", on_click=send_message, help="Отправить (Enter)")

with tab2:
    uploaded_file = st.file_uploader("Загрузить", type=["pdf", "txt", "md"])
    category = st.selectbox("Категория", ["temp_literature", "project_draft", "project_data"])
    if uploaded_file and st.button("📤 Загрузить"):
        st.success(f"{uploaded_file.name} загружен!")
