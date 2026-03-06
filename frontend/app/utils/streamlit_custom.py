"""
Кастомный CSS для полной кастомизации Streamlit
"""

CUSTOM_CSS = """
<style>
/* Полная блокировка верхней панели Streamlit */
#MainMenu {visibility: hidden !important;}
header {visibility: hidden !important;}
footer {visibility: hidden !important;}

/* Скрыть header */
.stApp > header {display: none !important;}

/* Блокировка iframe с кнопкой Deploy */
iframe[src*="streamlit"] {display: none !important;}

/* Скрыть все уведомления */
[data-testid="stAlertWrapper"] {display: none !important;}
[data-testid="stToast"] {display: none !important;}
[data-testid="stStatusContainer"] {display: none !important;}

/* Кастомный header для приложения */
.app-header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 50px;
    background: linear-gradient(90deg, #0068c9 0%, #004a99 100%);
    display: flex;
    align-items: center;
    padding: 0 20px;
    color: white;
    font-weight: bold;
    font-size: 18px;
    z-index: 9999;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Сдвиг контента вниз */
.stApp > main {
    margin-top: 60px !important;
}

/* Сайдбар */
[data-testid="stSidebar"] {
    z-index: 9998 !important;
}
</style>
"""

def render_custom_header(title: str = "🔬 BOAAI_S"):
    """Отобразить кастомный header вместо стандартного"""
    import streamlit as st
    st.markdown(f"""
        {CUSTOM_CSS}
        <div class="app-header">{title}</div>
    """, unsafe_allow_html=True)
