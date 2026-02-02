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


def main():
    st.set_page_config(
        page_title="Sistema de Monitoreo",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
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
    
    st.divider()
    
    route_to_page()


if __name__ == "__main__":
    main()