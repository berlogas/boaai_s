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
if "deleting_doc" not in st.session_state:
    st.session_state.deleting_doc = None

tab1, tab2, tab3, tab4 = st.tabs(["👥 Пользователи", "📁 Сессии", "📚 Глобальная база", "📊 Аудит"])

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

with tab3:
    st.markdown("### 📚 Глобальная база знаний")
    st.caption("Пополняйте базу, добавляя файлы в папку uploads")

    # Инструкция для пользователя
    st.info("📁 **Папка для загрузки:** `data_volume/uploads/`")
    st.markdown(f"""
    **Как загрузить файлы:**
    1. Скопируйте файлы (PDF, TXT, MD, DOCX и др.) в папку `/home/homo/projects/boaai_s/data_volume/uploads/`
    2. Нажмите кнопку **"🔄 Загрузить файлы из папки uploads"** ниже
    3. Файлы будут обработаны и добавлены в глобальную базу (это может занять несколько минут)
    
    **Поддерживаемые форматы:** `.pdf`, `.txt`, `.md`, `.html`, `.docx`, `.xlsx`, `.pptx`, `.py`, `.ts`, `.yaml`, `.json`, `.csv`, `.xml`
    """)

    # Кнопка загрузки всех файлов из uploads
    st.markdown("#### 🚀 Загрузка файлов")
    
    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        if st.button("🔄 Загрузить файлы", use_container_width=True, type="primary"):
            # Запускаем загрузку
            result = api_client.process_pending_uploads()
            
            if result:
                st.info(f"🔄 {result['message']}")
                
                # Показываем прогресс с обновлением
                progress_bar = st.progress(0)
                status_text = st.empty()
                log_container = st.empty()
                
                # Ждём завершения с обновлением прогресса
                import time
                max_wait = 600  # 10 минут максимум
                start_time = time.time()
                
                while time.time() - start_time < max_wait:
                    time.sleep(2)
                    status = api_client.get_upload_status()
                    
                    if status.get('completed'):
                        progress_bar.progress(100)
                        status_text.success(f"✅ {status.get('message', 'Загрузка завершена!')}")
                        
                        if status.get('uploaded'):
                            st.success("📊 **Загруженные файлы:**")
                            for i, doc in enumerate(status['uploaded'], 1):
                                st.write(f"  {i}. 📄 {doc['name']} ({doc['size_mb']} MB)")
                            st.success("✅ Индексация завершена! Файлы доступны для поиска.")
                        
                        if status.get('errors'):
                            st.error("❌ **Ошибки при загрузке:**")
                            for err in status['errors']:
                                st.error(f"  • {err['name']}: {err['error']}")
                        
                        st.rerun()
                    else:
                        # Показываем текущий статус с прогрессом
                        elapsed = int(time.time() - start_time)
                        
                        # Получаем детальный прогресс
                        progress = status.get('progress', 0)
                        current_file = status.get('current_file', '')
                        
                        if current_file:
                            status_text.info(f"⏳ Обработка: {current_file} ({elapsed} сек)")
                            progress_bar.progress(progress)
                            log_container.caption(f"🔄 [{status.get('message', 'Обработка...')}]")
                        else:
                            status_text.info(f"⏳ Обработка... ({elapsed} сек)")
                            progress_bar.progress(min(50 + (elapsed // 10), 90))
                            log_container.caption("Идёт индексация файлов. Это может занять несколько минут.")
                        
                        time.sleep(1)  # Небольшая пауза перед следующим обновлением
                        
                status_text.error("⏰ Таймаут ожидания. Проверьте логи.")
                st.rerun()

    # Список файлов в uploads
    st.markdown("#### 📥 Ожидают загрузки")
    pending_docs = api_client.get_pending_uploads()

    if not pending_docs:
        st.info("📭 Нет файлов, ожидающих загрузки")
    else:
        st.caption(f"Файлов в очереди: {len(pending_docs)}")
        
        # Показываем суммарный размер
        total_size = sum(doc['size_mb'] for doc in pending_docs)
        st.caption(f"Общий размер: {total_size:.2f} MB")
        
        for doc in pending_docs:
            with st.expander(f"📄 **{doc['name']}** ({doc['size_mb']} MB)"):
                st.caption(f"Добавлен: {doc['added_at']}")
                st.caption(f"Путь: {doc['path']}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info("ℹ️ Файл готов к загрузке")
                with col2:
                    if st.button("🗑️ Удалить из очереди", key=f"del_pending_{doc['name']}"):
                        result = api_client.delete_pending_upload(doc['name'])
                        if result:
                            st.success(result['message'])
                            st.rerun()

    st.markdown("---")

    # Список документов в базе
    st.markdown("#### 📄 Документы в базе")

    # Кнопка переиндексации
    col_rebuild1, col_rebuild2 = st.columns([1, 4])
    with col_rebuild1:
        if st.button("🔄 Переиндексировать", use_container_width=True, help="Пересоздать индекс всех документов"):
            with st.spinner("Переиндексация..."):
                result = api_client.rebuild_global_index()
                if result:
                    st.success("✅ Индекс переиндексирован!")
                else:
                    st.error("Ошибка при переиндексации")

    # Список документов
    global_docs = api_client.get_global_documents()

    if not global_docs:
        st.info("📭 В глобальной базе нет документов")
    else:
        st.caption(f"Всего документов: {len(global_docs)}")

        for doc in global_docs:
            is_deleting = st.session_state.deleting_doc == doc['name']

            if is_deleting:
                with st.expander(f"📄 **{doc['name']}**", expanded=True):
                    st.warning(f"⚠️ Удалить документ **{doc['name']}** из глобальной базы?")
                    st.caption(f"Путь: {doc['path']} | Размер: {doc['size_mb']} МБ")

                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("✅ Да, удалить", key=f"yes_del_doc_{doc['name']}", use_container_width=True, type="primary"):
                            result = api_client.delete_global_document(doc['name'])
                            if result:
                                st.success(f"✅ {result['message']}")
                                st.session_state.deleting_doc = None
                                st.rerun()
                    with col_no:
                        if st.button("❌ Отмена", key=f"no_del_doc_{doc['name']}", use_container_width=True):
                            st.session_state.deleting_doc = None
                            st.rerun()
            else:
                with st.expander(f"📄 **{doc['name']}**"):
                    st.caption(f"Путь: {doc['path']} | Размер: {doc['size_mb']} МБ | Загружен: {doc['uploaded_at']}")

                    if st.button("🗑️ Удалить", key=f"del_btn_doc_{doc['name']}"):
                        st.session_state.deleting_doc = doc['name']
                        st.rerun()

with tab4:
    st.markdown("### 📊 Журнал аудита активности")
    st.caption("Последние действия пользователей в системе")
    
    audit_logs = api_client.get_audit_log()
    
    if not audit_logs:
        st.info("📭 Нет записей в журнале аудита")
    else:
        # Отображаем в обратном порядке (новые сверху)
        for log in reversed(audit_logs):
            timestamp = log.get('timestamp', 'N/A')[:19].replace('T', ' ')
            action = log.get('action', 'unknown')
            user = log.get('user', 'unknown')
            details = log.get('details', {})
            
            # Иконка для действия
            icon_map = {
                "user_created": "➕",
                "user_updated": "✏️",
                "user_deleted": "🗑️",
                "global_doc_uploaded": "📤",
                "global_doc_deleted": "📥",
                "index_rebuilt": "🔄"
            }
            icon = icon_map.get(action, "📝")
            
            with st.expander(f"{icon} [{timestamp}] {user}: {action}", expanded=False):
                if details:
                    for key, value in details.items():
                        st.caption(f"**{key}**: {value}")
                else:
                    st.caption("Без дополнительных деталей")
