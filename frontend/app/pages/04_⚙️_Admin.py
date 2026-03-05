import streamlit as st
from core.api_client import api_client
import requests

st.title("⚙️ Админ-панель")

if st.session_state.get("user_info", {}).get("role") != "admin":
    st.error("🔒 Доступ запрещён")
    st.stop()

# Инициализация состояния редактирования и удаления
if "editing_user" not in st.session_state:
    st.session_state.editing_user = None
if "deleting_user" not in st.session_state:
    st.session_state.deleting_user = None

tab1, tab2 = st.tabs(["👥 Пользователи", "📁 Сессии"])

with tab1:
    st.markdown("### ➕ Создать пользователя")
    col1, col2, col3 = st.columns(3)
    with col1:
        new_username = st.text_input("Имя", key="create_username")
    with col2:
        new_password = st.text_input("Пароль", type="password", key="create_password")
    with col3:
        new_role = st.selectbox("Роль", ["researcher", "admin"], key="create_role")
    
    col_btn1, col_btn2 = st.columns([1, 2])
    with col_btn1:
        if st.button("➕ Создать", use_container_width=True):
            if not new_username or not new_password:
                st.error("Введите имя и пароль")
            else:
                result = api_client.create_user(new_username, new_password, new_role)
                if result:
                    st.success(f"Пользователь '{new_username}' создан!")
                    st.rerun()

    st.markdown("---")
    st.markdown("### 📋 Список пользователей")
    
    # Загружаем список пользователей
    try:
        headers = api_client.get_headers()
        response = requests.get(f"{api_client.base_url}/admin/users", headers=headers)
        if response.status_code == 200:
            users = response.json()
            current_username = st.session_state.user_info['username']
            
            # Фильтруем текущего пользователя
            users_to_show = [u for u in users if u['username'] != current_username]
            
            if not users_to_show:
                st.info("📭 Нет других пользователей")
            
            for user in users_to_show:
                is_editing = st.session_state.editing_user == user['username']
                is_deleting = st.session_state.deleting_user == user['username']
                
                if is_deleting:
                    # Режим подтверждения удаления
                    with st.expander(f"👤 **{user['username']}** ({user['role']})", expanded=True):
                        st.warning(f"⚠️ Вы уверены, что хотите удалить пользователя **{user['username']}**?")
                        col_yes, col_no = st.columns(2)
                        with col_yes:
                            if st.button("✅ Да, удалить", key=f"yes_del_{user['username']}", use_container_width=True, type="primary"):
                                result = api_client.delete_user(user['username'])
                                if result:
                                    st.success(f"Пользователь '{user['username']}' удалён")
                                    st.session_state.deleting_user = None
                                    st.rerun()
                                else:
                                    st.error("Ошибка при удалении")
                        with col_no:
                            if st.button("❌ Отмена", key=f"no_del_{user['username']}", use_container_width=True):
                                st.session_state.deleting_user = None
                                st.rerun()
                
                elif is_editing:
                    # Режим редактирования
                    with st.expander(f"👤 **{user['username']}** ({user['role']})", expanded=True):
                        st.caption(f"Создан: {user.get('created_at', 'N/A')} | Активен: {user.get('active', True)}")
                        
                        st.markdown("**✏️ Редактировать**")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.text_input("Имя", value=user['username'], disabled=True, key=f"edit_un_{user['username']}")
                        with col2:
                            edit_password = st.text_input("Пароль", type="password", value="", placeholder="Новый пароль", key=f"edit_pw_{user['username']}")
                        with col3:
                            edit_role = st.selectbox("Роль", ["researcher", "admin"], index=0 if user['role']=="researcher" else 1, key=f"edit_rl_{user['username']}")
                        
                        # Кнопки действия
                        col_cancel, col_save = st.columns([1, 1])
                        with col_cancel:
                            if st.button("❌ Отмена", key=f"cancel_{user['username']}", use_container_width=True):
                                st.session_state.editing_user = None
                                st.rerun()
                        
                        with col_save:
                            if st.button("💾 Сохранить", key=f"save_{user['username']}", use_container_width=True, type="primary"):
                                if not edit_password:
                                    st.error("Введите новый пароль")
                                else:
                                    result = api_client.update_user(user['username'], edit_password, edit_role)
                                    if result:
                                        st.success("Пользователь обновлён!")
                                        st.session_state.editing_user = None
                                        st.rerun()
                                    else:
                                        st.error("Ошибка при обновлении")
                else:
                    # Обычный режим просмотра
                    with st.expander(f"👤 **{user['username']}** ({user['role']})"):
                        st.caption(f"Создан: {user.get('created_at', 'N/A')} | Активен: {user.get('active', True)}")
                        
                        col_edit, col_del = st.columns(2)
                        with col_edit:
                            if st.button("✏️ Редактировать", key=f"edit_btn_{user['username']}"):
                                if user['username'] == st.session_state.user_info['username']:
                                    st.error("Нельзя редактировать себя")
                                else:
                                    st.session_state.editing_user = user['username']
                                    st.rerun()
                        
                        with col_del:
                            if st.button("🗑️ Удалить", key=f"del_btn_{user['username']}", type="secondary"):
                                if user['username'] == st.session_state.user_info['username']:
                                    st.error("Нельзя удалить себя")
                                else:
                                    st.session_state.deleting_user = user['username']
                                    st.rerun()
        else:
            st.error(f"Ошибка загрузки: {response.status_code}")
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")

with tab2:
    st.markdown("### 📁 Все сессии")
    st.info("Список сессий всех пользователей")
    
    try:
        headers = api_client.get_headers()
        response = requests.get(f"{api_client.base_url}/admin/sessions", headers=headers)
        if response.status_code == 200:
            sessions = response.json()
            if sessions:
                for session in sessions:
                    with st.expander(f"📁 {session.get('name', 'N/A')} (user: {session.get('user_id', 'N/A')})"):
                        st.caption(f"ID: {session.get('id', 'N/A')}")
                        st.caption(f"Документов: {len(session.get('documents', []))}")
                        st.caption(f"Последнее действие: {session.get('last_action', 'N/A')}")
            else:
                st.info("Нет активных сессий")
        else:
            st.error(f"Ошибка загрузки: {response.status_code}")
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")
