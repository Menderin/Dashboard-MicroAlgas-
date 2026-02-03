import os 
import streamlit as st
from modules.styles import apply_custom_styles, render_header
from views import dashboard, graphs, history, settings

# --- LOAD SECRETS TO ENV (Compatibilidad Streamlit Cloud) ---
def load_secrets_to_env():
    """Carga st.secrets en os.environ para compatibilidad con codigo que usa os.getenv.
    En desarrollo local (sin secrets.toml), simplemente no hace nada y deja que .env funcione.
    """
    try:
        if hasattr(st, "secrets") and len(st.secrets) > 0:
            for key, value in st.secrets.items():
                # Solo cargar si no existe ya (prioridad env vars reales o .env)
                if key not in os.environ and isinstance(value, str):
                    os.environ[key] = value
    except Exception:
        # No hay secrets.toml - desarrollo local usa .env via python-dotenv
        pass

load_secrets_to_env()


def initialize_session_state():
    query_params = st.query_params
    url_page = query_params.get("page", None)
    
    if 'current_page' not in st.session_state:
        if url_page in ['inicio', 'graficas', 'datos', 'configuracion']:
            st.session_state.current_page = url_page
        else:
            st.session_state.current_page = 'inicio'


def render_navigation():
    with st.container():
        menu_options = {
            'inicio': 'Inicio',
            'graficas': 'Graficas',
            'datos': 'Datos',
            'configuracion': 'Configuracion'
        }
        
        cols = st.columns(len(menu_options))
        
        for idx, (page_key, page_label) in enumerate(menu_options.items()):
            with cols[idx]:
                is_active = st.session_state.current_page == page_key
                if st.button(
                    page_label,
                    key=f"nav_{page_key}",
                    type='primary' if is_active else 'secondary',
                    width="stretch"
                ):
                    st.session_state.current_page = page_key
                    st.query_params["page"] = page_key
                    st.rerun()


def route_to_page():
    current_page = st.session_state.current_page
    
    if current_page == 'inicio':
        dashboard.show_view()
    elif current_page == 'graficas':
        graphs.show_view()
    elif current_page == 'datos':
        history.show_view()
    elif current_page == 'configuracion':
        settings.show_view()


def show_login_page():
    """Muestra la página de login con contraseña."""
    st.markdown("""
    <style>
    /* Ocultar elementos de Streamlit */
    header[data-testid="stHeader"], #MainMenu, footer {
        display: none;
    }
    
    /* Fondo con gradiente verde */
    .stApp {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        min-height: 100vh;
    }
    
    .block-container {
        padding-top: 0 !important;
        max-width: 100% !important;
    }
    
    /* Card de login con glassmorphism */
    .login-card {
        max-width: 420px;
        margin: 120px auto 0 auto;
        padding: 50px 40px;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 24px;
        box-shadow: 0 25px 50px rgba(0,0,0,0.15);
        text-align: center;
    }
    
    .login-icon {
        font-size: 60px;
        margin-bottom: 20px;
    }
    
    .login-title {
        color: #1e293b;
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
    }
    
    .login-subtitle {
        color: #64748b;
        font-size: 16px;
        margin-bottom: 35px;
        font-weight: 400;
    }
    
    .login-divider {
        width: 60px;
        height: 4px;
        background: linear-gradient(90deg, #11998e, #38ef7d);
        margin: 0 auto 30px auto;
        border-radius: 2px;
    }
    
    /* Estilo del input */
    .stTextInput > div > div > input {
        border-radius: 12px !important;
        border: 2px solid #e2e8f0 !important;
        padding: 15px 20px !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #11998e !important;
        box-shadow: 0 0 0 3px rgba(17, 153, 142, 0.15) !important;
    }
    
    /* Botón verde que combina con fondo */
    .stFormSubmitButton > button {
        background: linear-gradient(90deg, #11998e, #38ef7d) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 15px 30px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(17, 153, 142, 0.4) !important;
    }
    
    .stFormSubmitButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(17, 153, 142, 0.5) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Card de login con emoji de alga/planta
    st.markdown('''
    <div class="login-card">
        <div class="login-icon">🌿</div>
        <div class="login-title">Sistema de Monitoreo</div>
        <div class="login-subtitle">Cultivo de Microalgas</div>
        <div class="login-divider"></div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Formulario centrado
    _, center, _ = st.columns([1.2, 1, 1.2])
    with center:
        with st.form("login_form"):
            password = st.text_input("Contraseña", type="password", label_visibility="collapsed", placeholder="🔒 Ingrese contraseña")
            st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Ingresar", use_container_width=True, type="primary")
            
            if submitted:
                site_password = os.getenv("SITE_PASSWORD", "")
                if password == site_password:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta")


def render_logout_button():
    """Botón de cerrar sesión en el sidebar."""
    with st.sidebar:
        st.divider()
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()


def main():
    st.set_page_config(
        page_title="Sistema de Monitoreo",
        page_icon="🔬",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Inicializar estado de autenticación
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    # Verificar autenticación
    if not st.session_state.authenticated:
        show_login_page()
        return
    
    # Si está autenticado, mostrar dashboard
    apply_custom_styles()
    initialize_session_state()
    
    # Verificar conexión para el indicador
    from modules.database import DatabaseConnection
    try:
        _ = DatabaseConnection()
        is_connected = True
    except:
        is_connected = False
        
    render_header(connected=is_connected)
    render_navigation()
    render_logout_button()
    
    st.divider()
    
    route_to_page()


if __name__ == "__main__":
    main()