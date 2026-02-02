import streamlit as st

def apply_custom_styles():
    """Aplica estilos CSS con paleta oceánica vibrante y correcciones de espaciado."""
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
            
            :root {
                --primary: #0284c7; /* Sky 600 */
                --primary-light: #e0f2fe; /* Sky 100 */
                --text-dark: #0f172a; /* Slate 900 */
                --text-gray: #64748b; /* Slate 500 */
                --bg-gradient-start: #f8fafc; /* Slate 50 */
                --bg-gradient-end: #e0f2fe; /* Sky 100 */
            }

            * { font-family: 'Inter', sans-serif; }
            
            /* Fondo con degradado sutil */
            .stApp { 
                background: linear-gradient(180deg, #f8fafc 0%, #f0f9ff 100%);
                background-attachment: fixed;
            }
            
            /* Ajuste del Bloque Principal para despegar del techo */
            .block-container { 
                padding-top: 3rem; 
                padding-bottom: 3rem; 
                max-width: 1400px; 
            }
            
            /* Botones de Navegación */
            div.stButton > button {
                width: 100%;
                border-radius: 12px;
                border: none;
                font-weight: 600;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
                transition: all 0.2s ease;
                padding: 0.75rem 1rem;
            }

            /* Estado Inactivo (Secondary) - Por Defecto */
            div.stButton > button {
                background: white;
                color: var(--text-gray);
            }

            /* Estado Activo (Primary) - Forzado */
            div.stButton > button[kind="primary"] {
                background: var(--primary) !important;
                color: white !important;
                box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
            }

            /* Hover para ambos */
            div.stButton > button:hover {
                background: var(--primary);
                color: white;
                transform: translateY(-2px);
                box-shadow: 0 10px 15px -3px rgba(2, 132, 199, 0.2);
            }
            
            /* Hover especifico para primary para que no salte */
            div.stButton > button[kind="primary"]:hover {
                background: #0369a1 !important; /* Sky 700 */
                box-shadow: 0 10px 15px -3px rgba(3, 105, 161, 0.3);
            }

            /* Métricas nativas con un toque de color */
            [data-testid="stMetricValue"] {
                font-size: 2rem !important;
                background: -webkit-linear-gradient(45deg, #0284c7, #06b6d4);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 800 !important;
            }
            [data-testid="stMetricLabel"] {
                color: var(--text-gray) !important;
                font-size: 0.85rem !important;
                font-weight: 600 !important;
            }
            
            /* Contenedores con borde azulado suave */
            [data-testid="stVerticalBlockBorderWrapper"] {
                border-radius: 16px;
                background: white;
                border: 1px solid #e0f2fe; /* Borde sutil azul */
                box-shadow: 0 4px 6px -1px rgba(224, 242, 254, 0.5);
                padding: 1.5rem;
            }
            
            /* Inputs estilizados */
            .stTextInput input, .stSelectbox div[data-baseweb="select"] {
                border-radius: 10px;
                border: 1px solid #cbd5e1;
                background-color: #f8fafc;
            }
        </style>
    """, unsafe_allow_html=True)

def render_header(connected=True):
    import base64
    from pathlib import Path
    
    # Lógica de Estado
    status_text = "Sistema Activo" if connected else "Error Conexión"
    status_color = "#4ade80" if connected else "#fb923c" # Verde vs Naranja Alerta
    
    # Cargar y codificar el logo
    logo_path = Path("assets/logo_technolab_facebook_400x400-YBg4v2E9q9H0EMnE.png")
    logo_base64 = ""
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode()
    
    # Header con degradado azul profundo y texto blanco para contraste profesional
    st.markdown(f"""
<div style="background: linear-gradient(135deg, #0e7490 0%, #0284c7 100%); padding: 2rem; border-radius: 20px; box-shadow: 0 10px 25px -5px rgba(14, 116, 144, 0.3); margin-bottom: 2.5rem; display: flex; align-items: center; justify-content: space-between; color: white;">
<div style="display: flex; align-items: center; gap: 1.5rem;">
<img src="data:image/png;base64,{logo_base64}" style="width: 56px; height: 56px; border-radius: 14px; background: white; padding: 4px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" alt="Technolab Logo"/>
<div>
<h1 style="margin: 0; font-size: 1.8rem; font-weight: 700; color: white; line-height: 1.1;">Sistema de Monitoreo</h1>
<p style="margin: 0.25rem 0 0 0; color: rgba(255,255,255,0.85); font-size: 0.95rem;">Monitoreo de Microalgas</p>
</div>
</div>
<div style="background: rgba(255,255,255,0.15); color: white; padding: 0.5rem 1rem; border-radius: 99px; font-size: 0.8rem; font-weight: 600; border: 1px solid rgba(255,255,255,0.25); display: flex; align-items: center; gap: 8px;">
<span style="display:block; width:8px; height:8px; background:{status_color}; border-radius:50%; box-shadow: 0 0 8px {status_color};"></span>
{status_text}
</div>
</div>
    """, unsafe_allow_html=True)