import streamlit as st
from core.api_client import api_client

st.set_page_config(page_title="Вход", page_icon="🔐")
st.title("🔐 Вход в систему")

with st.form("login_form"):
    username = st.text_input("Имя пользователя")
    password = st.text_input("Пароль", type="password")
    submit = st.form_submit_button("Войти", use_container_width=True)
    if submit:
        if not username or not password:
            st.error("Введите логин и пароль")
        else:
            with st.spinner("Проверка..."):
                result = api_client.login(username, password)
                if result:
                    st.session_state["user_info"] = {"username": username, "role": result["role"]}
                    st.success("✅ Успешный вход!")
                    st.switch_page("main.py")
                else:
                    st.error("❌ Неверные credentials")
st.info("**Тест:** admin / admin123")
