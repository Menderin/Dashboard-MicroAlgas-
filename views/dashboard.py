import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Dict
import re

from modules.database import DatabaseConnection
from modules.config_manager import ConfigManager
from modules.sensor_registry import SensorRegistry
from modules.device_manager import DeviceManager, ConnectionStatus, HealthStatus, DeviceInfo

# --- SVGs CONSTANTS ---
ICON_LOC = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: text-bottom; margin-right: 2px;"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>'
ICON_ALERT = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: sub;"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>'
ICON_CLOCK = '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>'
ICON_WIFI_OFF = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="2" x2="22" y1="2" y2="22"/><path d="M8.5 8.5A6 6 0 0 1 12 8c.7 0 1.4.11 2.06.31"/><path d="M5 5A10 10 0 0 1 12 2c1.7 0 3.33.42 4.8 1.16"/><path d="M2.5 13.5a10 10 0 0 1 .63-1.07"/><path d="M2 2l20 20"/><path d="M12 22a2 2 0 0 1-2-2"/></svg>'
ICON_GRAPH_BTN = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2" /><line x1="8" y1="12" x2="8" y2="16" /><line x1="12" y1="8" x2="12" y2="16" /><line x1="16" y1="10" x2="16" y2="16" /></svg>'
ICON_REFRESH = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" /><path d="M21 3v5h-5" /><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" /><path d="M3 21v-5h5" /></svg>'

def initialize_dashboard_state():
    if 'dashboard_page' not in st.session_state:
        st.session_state.dashboard_page = 0

def clean_html(html_str):
    return re.sub(r'\n\s+', ' ', html_str).strip()

def show_view():
    initialize_dashboard_state()
    
    # --- CSS Global para tarjetas ---
    st.markdown("""
    <style>
    /* TARJETA: Contenedor principal con altura fija */
    .device-card {
        background: white;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
        margin-bottom: 1rem;
        min-height: 320px;
        display: flex;
        flex-direction: column;
    }
    
    /* TARJETA: Header */
    .device-card-header {
        padding: 0.875rem 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* TARJETA: Cuerpo con altura fija */
    .device-card-body {
        padding: 1rem;
        flex: 1;
        display: flex;
        flex-direction: column;
    }
    
    /* TARJETA: Grid de sensores con altura fija */
    .sensor-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.625rem;
        min-height: 145px;
    }
    
    /* TARJETA: Celda de sensor */
    .sensor-cell {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.625rem 0.5rem;
        text-align: center;
    }
    
    /* TARJETA: Footer */
    .device-card-footer {
        margin-top: auto;
        padding-top: 0.5rem;
        border-top: 1px solid #f1f5f9;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #94a3b8;
        font-size: 0.65rem;
    }
    
    /* BOTON: Estilos base para todos los botones de tarjeta */
    div[data-testid="stColumn"] > div > div > div > div[data-testid="stButton"] button {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        color: #64748b !important;
        font-weight: 600 !important;
        padding: 10px 16px !important;
        margin-top: 0.5rem !important;
        transition: all 0.15s ease !important;
    }
    
    div[data-testid="stColumn"] > div > div > div > div[data-testid="stButton"] button:hover {
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%) !important;
        color: #0284c7 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # --- Database Connection ---
    db = None
    config_manager = None
    thresholds = {}
    
    try:
        db = DatabaseConnection()
        config_manager = ConfigManager(db)
        thresholds = config_manager.get_all_configured_sensors()
    except Exception as e:
        st.error(f"Error Database Connection: {e}")
        return

    # --- Toolbar ---
    c1, c2 = st.columns([6, 1])
    with c1:
        st.subheader("Vista General de Dispositivos")
    with c2:
        if st.button("Actualizar Todo", type="primary"):
            # Limpiar caches para forzar recarga completa
            keys_to_delete = [k for k in st.session_state.keys() if k.startswith('live_data_')]
            for k in keys_to_delete:
                del st.session_state[k]
            st.rerun()
    
    # --- Data Loading ---
    all_devices = []
    
    try:
        df = db.get_latest_by_device()
        prev_states = st.session_state.get('device_health_states', {})
        
        if df is None or df.empty:
            all_devices = []
        else:
            try:
                detected = SensorRegistry.discover_sensors_from_dataframe(df)
                config_manager.sync_with_detected_sensors(detected)
                global_thresholds = config_manager.get_all_configured_sensors() 
                thresholds = global_thresholds
                
                all_meta = config_manager.get_device_metadata()
                dev_specifics = {k: v.get('thresholds', {}) for k, v in all_meta.items()}
                device_manager = DeviceManager(global_thresholds, prev_states, dev_specifics)
            except: 
                device_manager = DeviceManager(thresholds, prev_states)
            
            all_devices = device_manager.get_all_devices_info(df)
            st.session_state['device_health_states'] = device_manager.get_health_states()

    except Exception as e:
        st.error(f"Error fetching devices: {str(e)}")
        return
    
    # Solo necesitamos pasar config_manager, el fragment cargará los datos
    render_dashboard_content(all_devices, thresholds, config_manager)


@st.fragment(run_every=30)
def refresh_dashboard_data(all_devices, thresholds, config_manager):
    """Fragment que se auto-refresca cada 30 segundos"""
    from datetime import datetime
    
    # Recargar datos frescos
    db = DatabaseConnection()
    df = db.get_latest_by_device()
    
    if df is not None and not df.empty:
        prev_states = st.session_state.get('device_health_states', {})
        
        try:
            detected = SensorRegistry.discover_sensors_from_dataframe(df)
            config_manager.sync_with_detected_sensors(detected)
            global_thresholds = config_manager.get_all_configured_sensors()
            
            all_meta = config_manager.get_device_metadata()
            dev_specifics = {k: v.get('thresholds', {}) for k, v in all_meta.items()}
            device_manager = DeviceManager(global_thresholds, prev_states, dev_specifics)
        except:
            device_manager = DeviceManager(thresholds, prev_states)
        
        # Actualizar lista de dispositivos con datos frescos
        all_devices = device_manager.get_all_devices_info(df)
        st.session_state['device_health_states'] = device_manager.get_health_states()
        
        # IMPORTANTE: Actualizar el cache de cada dispositivo para que las tarjetas muestren datos frescos
        for device in all_devices:
            state_key = f"live_data_{device.device_id}"
            st.session_state[state_key] = device
    
    # Mostrar indicador de última actualización
    refresh_time = datetime.now().strftime("%H:%M:%S")
    st.caption(f" Última actualización: {refresh_time} • Auto-actualizando cada 30 segundos")
    
    # Renderizar KPIs
    device_manager_for_metrics = DeviceManager(thresholds, {})
    render_summary_metrics(device_manager_for_metrics, all_devices)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Aplicar filtros desde session_state
    show_offline = st.session_state.get('dashboard_show_offline', False)
    filtered_devices = apply_session_state_filters(all_devices, config_manager)
    
    # Si no mostrar offline, filtrar
    if not show_offline:
        filtered_devices = [d for d in filtered_devices if d.connection != ConnectionStatus.OFFLINE]
    
    # Renderizar Grid
    if not all_devices and not filtered_devices:
        render_empty_state()
        return
    
    if not filtered_devices and all_devices:
        st.info("No se encontraron dispositivos con los filtros actuales.")
        return
    
    render_device_grid(filtered_devices, thresholds, config_manager, show_offline)


def render_dashboard_content(all_devices, thresholds, config_manager):
    """Renderiza el contenido del dashboard con auto-refresh"""
    
    # --- Filtros (fuera del fragment para preservar interacción) ---
    with st.container(border=True):
        st.markdown("<div style='margin-bottom: 10px; font-weight: 600; color: #64748b; font-size: 0.9rem; display: flex; align-items: center; gap: 6px;'><svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='11' cy='11' r='8'/><path d='m21 21-4.3-4.3'/></svg> Filtros y Búsqueda</div>", unsafe_allow_html=True)
        render_filters(all_devices, config_manager)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- Fragment con auto-refresh ---
    refresh_dashboard_data(all_devices, thresholds, config_manager)


# Old render_dashboard_content - DEPRECATED
def render_dashboard_content_old(all_devices, thresholds, config_manager):
    """Renderiza el contenido del dashboard (KPIs, filtros, grid)"""
    # --- KPI Cards ---
    device_manager = DeviceManager(thresholds, {})
    render_summary_metrics(device_manager, all_devices)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- Filters ---
    with st.container(border=True):
        st.markdown("<div style='margin-bottom: 10px; font-weight: 600; color: #64748b; font-size: 0.9rem; display: flex; align-items: center; gap: 6px;'><svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='11' cy='11' r='8'/><path d='m21 21-4.3-4.3'/></svg> Filtros y Búsqueda</div>", unsafe_allow_html=True)
        filtered_devices, show_offline = render_filters(all_devices, config_manager)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- Grid ---
    if not all_devices and not filtered_devices:
         render_empty_state()
         return
         
    if not filtered_devices and all_devices:
        st.info("No se encontraron dispositivos con los filtros actuales.")
        return
        
    render_device_grid(filtered_devices, thresholds, config_manager, show_offline)


# Import fragment with fallback
try:
    from streamlit import fragment
except ImportError:
    try:
        from streamlit import experimental_fragment as fragment
    except ImportError:
        def fragment(func):
            return func


@fragment
def render_live_device_card(device_obj: DeviceInfo, thresholds: Dict, config_manager: ConfigManager):
    """
    Renderiza la tarjeta con actualizacion PARCIAL gracias a @fragment.
    Incluye paginacion minimalista para sensores.
    """
    dev_id = device_obj.device_id
    state_key = f"live_data_{dev_id}"
    page_key = f"sensor_page_{dev_id}"
    
    # Inicializar estados
    if state_key not in st.session_state:
        st.session_state[state_key] = device_obj
    if page_key not in st.session_state:
        st.session_state[page_key] = 0
    
    current_device = st.session_state[state_key]
    current_page = st.session_state[page_key]
    
    # Calcular paginacion de forma segura
    total_sensors = len(current_device.sensor_data) if current_device.sensor_data else 0
    sensors_per_page = 4
    total_pages = max(1, (total_sensors + sensors_per_page - 1) // sensors_per_page)
    
    # Auto-correccion de pagina si excede limites (evita paginas en blanco)
    if current_page >= total_pages:
        current_page = 0
        st.session_state[page_key] = 0
    
    # --- RENDER HTML DE LA TARJETA ---
    raw_html = build_card_html(
        current_device, 
        thresholds, 
        config_manager,
        sensor_page=current_page,
        total_pages=total_pages
    )
    st.markdown(clean_html(raw_html), unsafe_allow_html=True)
    
    # --- BARRA DE CONTROLES ---
    if total_pages > 1:
        # Layout de 3 columnas para navegacion
        c1, c2, c3 = st.columns([1, 4, 1])
        
        # Boton Anterior
        with c1:
            disable_prev = current_page <= 0
            if st.button("◀", key=f"prev_{dev_id}", disabled=disable_prev, width="stretch"):
                new_page = max(0, current_page - 1)
                st.session_state[page_key] = new_page
                
        # Boton Actualizar (Centro)
        with c2:
            refresh = st.button("Actualizar", key=f"refresh_{dev_id}", width="stretch")
            
        # Boton Siguiente
        with c3:
            disable_next = current_page >= total_pages - 1
            if st.button("▶", key=f"next_{dev_id}", disabled=disable_next, width="stretch"):
                new_page = min(total_pages - 1, current_page + 1)
                st.session_state[page_key] = new_page
    else:
        # Sin paginacion: solo actualizar
        refresh = st.button("Actualizar", key=f"refresh_{dev_id}", width="stretch")
    
    # --- LOGICA DE REFRESH ---
    if refresh:
        try:
            db = DatabaseConnection()
            new_df = db.get_latest_for_single_device(dev_id)
            if not new_df.empty:
                cfg = ConfigManager(db)
                # 1. Obtener umbrales globales
                global_thresholds = cfg.get_all_configured_sensors()
                
                # 2. Obtener umbrales ESPECIFICOS del dispositivo
                all_meta = cfg.get_device_metadata()
                dev_specifics = {k: v.get('thresholds', {}) for k, v in all_meta.items()}
                
                # 3. Recuperar estados previos para evitar flasheos
                prev_states = st.session_state.get('device_health_states', {})
                
                # 4. Crear DeviceManager con TODA la configuracion
                mgr = DeviceManager(global_thresholds, prev_states, dev_specifics)
                
                new_infos = mgr.get_all_devices_info(new_df)
                if new_infos:
                    st.session_state[state_key] = new_infos[0]
        except Exception as e:
            st.toast(f"Error: {e}")


def render_device_grid(devices, thresholds, config_manager=None, show_offline=False):
    
    # Filtrar dispositivos offline si show_offline es False
    if show_offline:
        display_devices = devices
    else:
        display_devices = [d for d in devices if d.connection != ConnectionStatus.OFFLINE]
    
    with st.container():
        PER_PAGE = 9
        total_pages = max(1, (len(display_devices) + PER_PAGE - 1) // PER_PAGE)
        
        if st.session_state.dashboard_page >= total_pages: st.session_state.dashboard_page = 0
        current_page = st.session_state.dashboard_page
        
        start = current_page * PER_PAGE
        end = start + PER_PAGE
        page_items = display_devices[start:end]
        
        cols = st.columns(3)
        for i, device in enumerate(page_items):
            with cols[i % 3]:
                render_live_device_card(device, thresholds, config_manager)
                
        if total_pages > 1:
            st.markdown("<br>", unsafe_allow_html=True)
            # Usar columnas con proporcion amplia para empujar botones a los extremos
            c1, c2, c3 = st.columns([1, 10, 1])
            with c1:
                # Boton izquierdo
                if st.button("←", disabled=current_page==0, key="prev", width="stretch"): 
                    st.session_state.dashboard_page -= 1
                    st.rerun()
            with c2: 
                st.markdown(f"<div style='text-align:center; color:#94a3b8; font-size:0.8rem; margin-top:8px; font-weight:600;'>Página {current_page+1} de {total_pages}</div>", unsafe_allow_html=True)
            with c3:
                # Boton derecho - width='stretch' ayuda a llenar la columna
                if st.button("→", disabled=current_page >= total_pages-1, key="next", width="stretch"): 
                    st.session_state.dashboard_page += 1
                    st.rerun()

def render_empty_state():
    st.markdown(clean_html("""
<div style="text-align: center; padding: 4rem; background: white; border-radius: 20px; border: 1px dashed #cbd5e1; box-shadow: 0 4px 6px -2px rgba(0,0,0,0.05);">
<div style="color: #cbd5e1; margin-bottom: 1.5rem;">
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20"/><path d="M2 12h20"/><path d="M12 12a5 5 0 0 1 5 5"/></svg>
</div>
<h3 style="color: #64748b; margin: 0; font-weight: 700;">Esperando Datos</h3>
<p style="color: #94a3b8; margin-top: 0.5rem;">El sistema está escuchando conexiones activas...</p>
</div>
    """), unsafe_allow_html=True)

def render_summary_metrics(manager, devices):
    with st.container():
        metrics = manager.calculate_summary_metrics(devices)
        cols = st.columns(6)
        def m(idx, label, key, bg, txt):
            with cols[idx]:
                st.markdown(clean_html(build_kpi_html(label, metrics.get(key, 0), bg, txt)), unsafe_allow_html=True)
        m(0, "Total", 'total', "#e0f2fe", "#0369a1")
        m(1, "En Línea", 'online', "#dcfce7", "#15803d")
        m(2, "Offline", 'offline', "#f1f5f9", "#475569")
        m(3, "OK", 'ok', "#dcfce7", "#15803d")
        m(4, "Alerta", 'warning', "#fef3c7", "#b45309")
        m(5, "Crítico", 'critical', "#fee2e2", "#b91c1c")

def build_kpi_html(label, value, bg_color, text_color):
    return f"""
        <div style="background: {bg_color}; border-radius: 12px; padding: 0.8rem; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid rgba(0,0,0,0.05); min-width: 0;">
        <div style="color: {text_color}; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{label}</div>
        <div style="color: {text_color}; font-size: 1.6rem; font-weight: 800; line-height: 1.1;">{value}</div>
        </div>
    """

def apply_session_state_filters(devices, config_manager=None):
    """Aplica los filtros almacenados en session_state a la lista de dispositivos"""
    alias_map = {}
    custom_loc_map = {}
    if config_manager:
        meta = config_manager.get_device_metadata()
        for dev_id, info in meta.items():
            alias_map[dev_id] = info.get("alias", "")
            custom_loc_map[dev_id] = info.get("location", "")

    canonical_locations = set()
    device_canon_map = {}
    for d in devices:
        eff_loc = custom_loc_map.get(d.device_id) or d.location
        if eff_loc:
             canonical_locations.add(eff_loc)
             device_canon_map[d.device_id] = eff_loc
    
    filtered = devices
    
    # Aplicar filtro de tipo
    filter_type = st.session_state.get('dashboard_filter_type', '-- Selección Rápida --')
    dynamic_filter = st.session_state.get('dashboard_dynamic_filter', [])
    
    if filter_type == "Por Estado" and dynamic_filter:
        res = []
        for d in filtered:
            s_str = "Offline" if d.connection == ConnectionStatus.OFFLINE else (
                "Crítico" if d.health == HealthStatus.CRITICAL else (
                    "Alerta" if d.health == HealthStatus.WARNING else "Normal"))
            if s_str in dynamic_filter:
                res.append(d)
        filtered = res
    elif filter_type == "Por Ubicación" and dynamic_filter:
        filtered = [d for d in filtered if device_canon_map.get(d.device_id) in dynamic_filter]
    elif filter_type == "Por Alias/ID" and dynamic_filter:
        filtered = [d for d in filtered if alias_map.get(d.device_id, d.device_id) in dynamic_filter]
    
    # Aplicar búsqueda
    search = st.session_state.get('dashboard_search', '').lower()
    if search:
        results = []
        for d in filtered:
            if any(search in x.lower() for x in [d.device_id, d.location, 
                   alias_map.get(d.device_id, ""), custom_loc_map.get(d.device_id, "")]):
                results.append(d)
        filtered = results
    
    # Ordenar
    filtered.sort(key=lambda x: alias_map.get(x.device_id, x.device_id.lower()))
    
    return filtered

def initialize_filter_session_state():
    """Inicializa el session_state de los filtros si no existe"""
    if 'dashboard_search' not in st.session_state:
        st.session_state.dashboard_search = ""
    if 'dashboard_filter_type' not in st.session_state:
        st.session_state.dashboard_filter_type = "-- Selección Rápida --"
    if 'dashboard_dynamic_filter' not in st.session_state:
        st.session_state.dashboard_dynamic_filter = []
    if 'dashboard_show_offline' not in st.session_state:
        st.session_state.dashboard_show_offline = False

def render_filters(devices, config_manager=None):
    """Renderiza los controles de filtrado y los almacena en session_state"""
    # Inicializar session state
    initialize_filter_session_state()
    
    alias_map = {}
    custom_loc_map = {}
    if config_manager:
        meta = config_manager.get_device_metadata()
        for dev_id, info in meta.items():
            alias_map[dev_id] = info.get("alias", "")
            custom_loc_map[dev_id] = info.get("location", "")

    canonical_locations = set()
    device_canon_map = {}
    for d in devices:
        eff_loc = custom_loc_map.get(d.device_id) or d.location
        if eff_loc:
             canonical_locations.add(eff_loc)
             device_canon_map[d.device_id] = eff_loc

    all_locations = sorted(list(canonical_locations))
    all_aliases = sorted([alias_map.get(d.device_id, d.device_id) for d in devices])
    
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([1.5, 1, 1.5, 0.8])
        
        with c1:
            st.text_input(
                "Búsqueda Rápida", 
                placeholder="Escribe para buscar...", 
                label_visibility="collapsed",
                key="dashboard_search"
            )
        
        with c2:
            st.selectbox(
                "Criterio de Filtrado", 
                ["-- Selección Rápida --", "Por Estado", "Por Ubicación", "Por Alias/ID"], 
                label_visibility="collapsed",
                key="dashboard_filter_type"
            )
        
        with c4:
            st.checkbox(
                "Mostrar Offline", 
                value=False, 
                help="Mostrar dispositivos offline en el grid",
                key="dashboard_show_offline"
            )
        
        # Dynamic filter basado en el tipo seleccionado
        with c3:
            filter_type = st.session_state.dashboard_filter_type
            if filter_type == "Por Estado":
                st.multiselect(
                    "Estado", 
                    ["Normal", "Alerta", "Crítico", "Offline"], 
                    label_visibility="collapsed",
                    key="dashboard_dynamic_filter"
                )
            elif filter_type == "Por Ubicación":
                st.multiselect(
                    "Ubicación", 
                    all_locations, 
                    label_visibility="collapsed",
                    key="dashboard_dynamic_filter"
                )
            elif filter_type == "Por Alias/ID":
                st.multiselect(
                    "ID o Alias", 
                    all_aliases, 
                    label_visibility="collapsed",
                    key="dashboard_dynamic_filter"
                )
            else:
                # Reset dynamic filter si no hay tipo seleccionado
                st.session_state.dashboard_dynamic_filter = []

def build_card_html(device: DeviceInfo, thresholds: Dict, config_manager: ConfigManager = None, sensor_page: int = 0, total_pages: int = 1) -> str:
    """Genera el HTML de una tarjeta de dispositivo con altura fija."""
    
    # Obtener nombre y ubicación personalizados
    display_name = device.device_id
    display_loc = device.location if device.location else "Sin ubicacion"
    
    if config_manager:
        meta = config_manager.get_device_info(device.device_id)
        alias_val = meta.get("alias", "")
        if alias_val and alias_val.strip(): 
            display_name = alias_val
        location_val = meta.get("location", "")
        if location_val and location_val.strip(): 
            display_loc = location_val
    
    # Determinar estado y colores
    is_offline = device.connection == ConnectionStatus.OFFLINE
    
    if is_offline:
        header_bg = "#64748b"
        status_txt = "OFFLINE"
        body_opacity = "0.6"
    elif device.health == HealthStatus.CRITICAL:
        header_bg = "#dc2626"
        status_txt = "CRITICO"
        body_opacity = "1"
    elif device.health == HealthStatus.WARNING:
        header_bg = "#d97706"
        status_txt = "ALERTA"
        body_opacity = "1"
    else:
        header_bg = "#059669"
        status_txt = "NORMAL"
        body_opacity = "1"

    # Generar grid de sensores con paginacion y layout adaptativo
    total_sensors = len(device.sensor_data) if device.sensor_data else 0
    sensors_per_page = 4
    
    if total_sensors == 0:
        # Sin datos
        sensors_html = f'''
            <div class="sensor-grid">
                <div class="sensor-cell" style="grid-column: span 2; display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:140px; background:transparent; border-style:dashed;">
                    <div style="opacity:0.4; margin-bottom:8px;">{ICON_WIFI_OFF}</div>
                    <div style="color:#94a3b8; font-size:0.75rem; font-weight:600;">Sin datos</div>
                </div>
            </div>
        '''
    else:
        # Calcular slice de sensores segun la pagina
        start_idx = sensor_page * sensors_per_page
        end_idx = start_idx + sensors_per_page
        sensors_list = list(device.sensor_data.items())[start_idx:end_idx]
        count = len(sensors_list)
        
        cells = []
        # Generar celdas
        for k, v in sensors_list:
            conf = thresholds.get(k, {})
            label = conf.get("label", k.replace("_", " ").title())
            unit = conf.get("unit", "")
            
            # Estilos base
            cell_style = ""
            
            # Ajustes visuales segun cantidad
            if count == 1:
                # 1 Sensor: Centrado vertical y horizontal, texto mas grande
                cell_style = "display:flex; flex-direction:column; justify-content:center; height:100%;"
                label_style = "font-size:0.8rem; margin-bottom:4px;"
                value_style = "font-size:1.8rem;"
            elif count == 2:
                # 2 Sensores: Centrado vertical (filas), texto mediano
                cell_style = "display:flex; flex-direction:row; justify-content:space-between; align-items:center; padding:0 1.5rem; height:100%;"
                label_style = "font-size:0.7rem;"
                value_style = "font-size:1.4rem;"
            else:
                # 3 o 4 Sensores: Grid estandar
                cell_style = ""
                label_style = "font-size:0.6rem; margin-bottom:2px;"
                value_style = "font-size:1.1rem;"

            # Template de celda
            if count == 2:
                # Layout horizontal para 2 sensores (Label a la izq, Valor a la der)
                cells.append(f'''
                    <div class="sensor-cell" style="{cell_style}">
                        <div style="{label_style} color:#64748b; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">{label}</div>
                        <div style="{value_style} color:#1e293b; font-weight:800;">{v:.2f}<span style="font-size:0.7rem; color:#94a3b8; font-weight:600; margin-left:4px;">{unit}</span></div>
                    </div>
                ''')
            else:
                # Layout vertical estandar
                cells.append(f'''
                    <div class="sensor-cell" style="{cell_style}">
                        <div style="{label_style} color:#64748b; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">{label}</div>
                        <div style="{value_style} color:#1e293b; font-weight:800;">{v:.2f}<span style="font-size:0.65rem; color:#94a3b8; font-weight:600; margin-left:2px;">{unit}</span></div>
                    </div>
                ''')

        # Definir Grid Layout basado en la cantidad
        if count == 1:
            # 1 columna completa
            grid_style = "grid-template-columns: 1fr;"
        elif count == 2:
            # 1 columna, 2 filas (uno arriba, otro abajo)
            grid_style = "grid-template-columns: 1fr; grid-template-rows: 1fr 1fr;"
        else:
            # Grid 2x2 estandar
            grid_style = "grid-template-columns: 1fr 1fr;"
            
            # Rellenar placeholder si son 3
            while len(cells) < 4:
                cells.append('<div class="sensor-cell" style="background:transparent; border-style:dashed; opacity:0.3;"></div>')
        
        sensors_html = f'<div class="sensor-grid" style="{grid_style}">{ "".join(cells) }</div>'
    
    # Indicador de pagina (puntos) si hay multiples paginas
    page_indicator_html = ""
    if total_pages > 1:
        dots = []
        for i in range(total_pages):
            if i == sensor_page:
                dots.append('<span style="width:8px; height:8px; background:#0284c7; border-radius:50%; display:inline-block;"></span>')
            else:
                dots.append('<span style="width:6px; height:6px; background:#cbd5e1; border-radius:50%; display:inline-block;"></span>')
        page_indicator_html = f'<div style="display:flex; justify-content:center; gap:6px; padding:8px 0;">{" ".join(dots)}</div>'

    # Alertas
    alerts_html = ""
    if device.alerts:
        alerts_html = f'''
            <div style="background:#fef2f2; border-left:3px solid #ef4444; border-radius:6px; padding:6px 10px; color:#b91c1c; font-size:0.7rem; display:flex; align-items:center; gap:6px; margin-top:8px;">
                {ICON_ALERT}
                <span style="font-weight:600;">{device.alerts[0]}</span>
            </div>
        '''

    # Timestamp
    ts_str = "--"
    if device.last_update:
        dt = device.last_update
        if dt.tzinfo: 
            dt = dt.replace(tzinfo=None)
        if dt.date() == datetime.now().date():
            ts_str = dt.strftime("%H:%M:%S")
        else:
            ts_str = dt.strftime("%d/%m %H:%M:%S")

    # Construir tarjeta completa
    card = f'''
    <div class="device-card">
        <div class="device-card-header" style="background:{header_bg};">
            <div style="color:white; min-width:0; flex:1;">
                <div style="font-weight:700; font-size:0.9rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{display_name}</div>
                <div style="font-size:0.7rem; opacity:0.9; display:flex; align-items:center; gap:4px; margin-top:2px;">
                    {ICON_LOC} {display_loc}
                </div>
            </div>
            <div style="display:flex; align-items:center; gap:6px;">
                <a href="?page=graficas&device_id={device.device_id}" target="_self" style="color:white; opacity:0.85; padding:4px; border-radius:4px; display:flex; text-decoration:none;" title="Ver Graficas">
                    {ICON_GRAPH_BTN}
                </a>
                <div style="background:rgba(255,255,255,0.2); color:white; border-radius:99px; padding:3px 10px; font-size:0.6rem; font-weight:700; border:1px solid rgba(255,255,255,0.3);">
                    {status_txt}
                </div>
            </div>
        </div>
        <div class="device-card-body" style="opacity:{body_opacity};">
            {sensors_html}
            {page_indicator_html}
            {alerts_html}
            <div class="device-card-footer">
                <div style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:55%;" title="{device.device_id}">
                    ID: {device.device_id}
                </div>
                <div style="display:flex; align-items:center; gap:4px;">
                    {ICON_CLOCK} {ts_str}
                </div>
            </div>
        </div>
    </div>
    '''
    return card