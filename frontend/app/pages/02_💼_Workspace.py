import streamlit as st
from core.api_client import api_client
import requests

st.title("💼 Рабочее пространство")

# Проверка авторизации
if not st.session_state.get("auth_token"):
    st.warning("🔒 Пожалуйста, войдите в систему")
    st.stop()

user_info = st.session_state.get("user_info", {})
user_role = user_info.get("role", "researcher")
username = user_info.get("username", "user")

if "current_session" not in st.session_state or not st.session_state.current_session:
    sessions = api_client.get_sessions()
    if sessions:
        st.session_state["current_session"] = sessions[0]
    else:
        st.warning("📭 Нет сессий. Создайте на дашборде.")
        st.stop()

session = st.session_state.current_session
st.markdown(f"### 📁 {session['name']}")

tab1, tab2, tab3 = st.tabs(["💬 Чат", "📄 Мои документы", "📚 Глобальная база"])

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
    st.markdown("### 📤 Загрузить документ")
    st.caption("Документы будут доступны только в вашей сессии")
    
    # Ключ для принудительного обновления загрузчика
    upload_key_suffix = st.session_state.get(f"upload_key_{session['id']}", 0)
    upload_key = f"upload_{session['id']}_{upload_key_suffix}"

    uploaded_file = st.file_uploader(
        "Выберите файл",
        type=["pdf", "txt", "md", "docx"],
        key=upload_key,
        help="Поддерживаются: PDF, TXT, MD, DOCX"
    )
    
    if uploaded_file:
        st.info(f"📄 Файл: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")

        if st.button("📤 Загрузить в сессию", type="primary"):
            try:
                # Загружаем файл через API
                headers = {"Authorization": f"Bearer {api_client.token}"}

                # Читаем файл в байты
                file_bytes = uploaded_file.getvalue()
                file_size_mb = len(file_bytes) / (1024 * 1024)

                # Предупреждение для больших файлов
                if file_size_mb > 5:
                    st.warning(f"⚠️ Файл большой ({file_size_mb:.1f} MB). Обработка может занять время...")

                with st.spinner("⏳ Загрузка файла... Это может занять несколько минут"):
                    # Отправляем файл как multipart/form-data
                    files = {"file": (uploaded_file.name, file_bytes, "application/octet-stream")}

                    response = requests.post(
                        f"{api_client.base_url}/upload/session/{session['id']}",
                        headers=headers,
                        files=files,
                        timeout=300  # 5 минут на обработку
                    )

                if response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ Файл '{uploaded_file.name}' загружен в сессию!")
                    st.info(f"📊 Категория: {result.get('document', {}).get('category', 'N/A')}")
                    # Обновляем ключ для сброса состояния загрузчика
                    st.session_state[f"upload_key_{session['id']}"] = st.session_state.get(f"upload_key_{session['id']}", 0) + 1
                    # Перезагружаем страницу для обновления списка
                    st.rerun()
                else:
                    st.error(f"❌ Ошибка: {response.status_code}")
                    try:
                        error_detail = response.json()
                        st.error(f"Детали: {error_detail}")
                    except:
                        st.error(f"Детали: {response.text[:500]}")
            except requests.exceptions.Timeout:
                st.error("⏰ Таймаут загрузки (5 минут). Попробуйте файл меньшего размера.")
            except requests.exceptions.ConnectionError as e:
                st.error("❌ Ошибка подключения к серверу. Проверьте, что backend запущен.")
            except Exception as e:
                st.error(f"❌ Ошибка загрузки: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    st.markdown("---")
    st.markdown("### 📋 Документы сессии")
    
    # Получаем документы сессии
    try:
        headers = {"Authorization": f"Bearer {api_client.token}"}
        response = requests.get(
            f"{api_client.base_url}/sessions/{session['id']}/documents",
            headers=headers
        )
        
        if response.status_code == 200:
            docs = response.json()
            if docs:
                st.caption(f"Всего документов: {len(docs)}")
                for i, doc in enumerate(docs):
                    with st.expander(f"📄 {doc.get('name', 'Unknown')}"):
                        st.caption(f"📁 Категория: {doc.get('category', 'N/A')}")
                        st.caption(f"📅 Загружен: {doc.get('uploaded_at', 'N/A')}")
                        # Показываем размер в удобном формате
                        size_bytes = doc.get('size_bytes', 0)
                        if size_bytes:
                            if size_bytes < 1024:
                                st.caption(f"📊 Размер: {size_bytes} Б")
                            elif size_bytes < 1024 * 1024:
                                st.caption(f"📊 Размер: {size_bytes / 1024:.1f} KB")
                            else:
                                st.caption(f"📊 Размер: {size_bytes / (1024 * 1024):.2f} MB")
                        else:
                            # Для старых записей без size_bytes
                            size_mb = doc.get('size_mb', 0)
                            if size_mb < 0.01:
                                st.caption(f"📊 Размер: {size_mb * 1024:.1f} KB")
                            else:
                                st.caption(f"📊 Размер: {size_mb:.2f} MB")
                        # Кнопка удаления
                        if st.button("🗑️ Удалить", key=f"del_doc_{i}_{doc.get('name', '')}"):
                            st.info("ℹ️ Функционал удаления в разработке")
            else:
                st.info("📭 В сессии нет документов")
        else:
            st.info("📭 В сессии нет документов")
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")

with tab3:
    st.markdown("### 📚 Глобальная база знаний")
    st.caption("Документы доступны всем пользователям")
    
    # Для admin - загрузка в глобальную базу
    if user_role == "admin":
        st.info("🔑 Режим администратора: вы можете загружать файлы в глобальную базу")

        # Ключ для принудительного обновления загрузчика
        upload_key_global_suffix = st.session_state.get("upload_key_global", 0)
        upload_key_global = f"global_upload_{upload_key_global_suffix}"

        uploaded_file_global = st.file_uploader(
            "Загрузить в глобальную базу",
            type=["pdf", "txt", "md", "docx"],
            key=upload_key_global,
            help="Файл будет доступен всем пользователям"
        )

        if uploaded_file_global:
            st.info(f"📄 Файл: **{uploaded_file_global.name}** ({uploaded_file_global.size / 1024:.1f} KB)")

            if st.button("📤 Загрузить в глобальную базу", type="primary"):
                try:
                    headers = api_client.get_headers()
                    files = {"file": (uploaded_file_global.name, uploaded_file_global.getvalue(), uploaded_file_global.type)}

                    with st.spinner("⏳ Загрузка в глобальную базу... Это может занять несколько минут"):
                        response = requests.post(
                            f"{api_client.base_url}/upload/global",
                            headers=headers,
                            files=files,
                            timeout=300  # 5 минут на обработку
                        )

                    if response.status_code == 200:
                        st.success(f"✅ Файл '{uploaded_file_global.name}' загружен в глобальную базу!")
                        # Обновляем ключ для сброса состояния загрузчика
                        st.session_state["upload_key_global"] = st.session_state.get("upload_key_global", 0) + 1
                        st.rerun()
                    else:
                        st.error(f"❌ Ошибка: {response.status_code}")
                        try:
                            error_detail = response.json()
                            st.error(f"Детали: {error_detail}")
                        except:
                            st.error(f"Детали: {response.text[:200]}")
                except requests.exceptions.Timeout:
                    st.error("⏰ Таймаут загрузки (5 минут). Попробуйте файл меньшего размера.")
                except Exception as e:
                    st.error(f"❌ Ошибка загрузки: {str(e)}")
        
        st.markdown("---")
    
    # Список документов глобальной базы
    st.markdown("### 📄 Документы в глобальной базе")
    
    global_docs = api_client.get_global_documents()

    if not global_docs:
        st.info("📭 В глобальной базе нет документов")
    else:
        st.caption(f"Всего документов: {len(global_docs)}")

        for doc in global_docs:
            with st.expander(f"📄 **{doc['name']}**"):
                st.caption(f"📁 Путь: {doc['path']}")
                # Вычисляем размер из size_mb или из файла
                size_mb = doc.get('size_mb', 0)
                size_bytes = doc.get('size_bytes', int(size_mb * 1024 * 1024))
                
                if size_bytes:
                    if size_bytes < 1024:
                        st.caption(f"📊 Размер: {size_bytes} Б")
                    elif size_bytes < 1024 * 1024:
                        st.caption(f"📊 Размер: {size_bytes / 1024:.1f} KB")
                    else:
                        st.caption(f"📊 Размер: {size_bytes / (1024 * 1024):.2f} MB")
                else:
                    st.caption(f"📊 Размер: {size_mb:.2f} MB")
                st.caption(f"📅 Загружен: {doc.get('uploaded_at', 'N/A')}")
