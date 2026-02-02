"""
Página de Gráficas y Tendencias - Versión Optimizada
Arquitectura: Carga completa -> DataFrame cacheado -> Filtrado en memoria
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from modules.database import DatabaseConnection
from modules.config_manager import ConfigManager

# =============================================================================
# ICONOS SVG INLINE
# =============================================================================

ICON_CHART = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'

ICON_REFRESH = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px;"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>'

ICON_SETTINGS = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>'

ICON_DATABASE = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px;"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>'

ICON_CALENDAR = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px;"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>'

ICON_DEVICE = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px;"><path d="M5 12.55a11 11 0 0 1 14.08 0"></path><path d="M1.42 9a16 16 0 0 1 21.16 0"></path><path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path><line x1="12" y1="20" x2="12.01" y2="20"></line></svg>'

ICON_TRENDING = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px;"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>'

ICON_INFO = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'

ICON_POINTER = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px;"><path d="M18 8L22 12L18 16"></path><path d="M2 12H22"></path></svg>'

ICON_RULER = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px;"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><path d="M12 11h4"></path><path d="M12 16h4"></path><path d="M8 11h.01"></path><path d="M8 16h.01"></path></svg>'

ICON_CLIPBOARD = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px;"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>'

ICON_LIGHTBULB = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 4px;"><line x1="9" y1="18" x2="15" y2="18"></line><line x1="10" y1="22" x2="14" y2="22"></line><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"></path></svg>'

# Mapa de normalizacion de nombres de sensores (diferentes esquemas -> nombre estandar)
SENSOR_ALIASES = {
    # Temperatura
    "temperatura": "temperature",
    "temp": "temperature",
    "temperature": "temperature",
    "TEMPERATURA": "temperature",
    "TEMP": "temperature",
    # pH
    "ph": "ph",
    "PH": "ph",
    "Ph": "ph",
    # Oxigeno
    "oxigeno": "oxygen",
    "oxygen": "oxygen",
    "do": "oxygen",
    "OD": "oxygen",
    # Otros
    "humedad": "humidity",
    "humidity": "humidity",
}

# Labels para mostrar al usuario
SENSOR_LABELS = {
    "temperature": {"label": "Temperatura", "unit": "°C"},
    "ph": {"label": "pH", "unit": ""},
    "oxygen": {"label": "Oxígeno Disuelto", "unit": "mg/L"},
    "humidity": {"label": "Humedad", "unit": "%"},
}


def normalize_sensor_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombres de columnas de sensores para unificar datos de diferentes fuentes."""
    if df.empty:
        return df
    
    df = df.copy()
    columns_to_rename = {}
    
    for col in df.columns:
        col_lower = col.lower().strip()
        if col_lower in SENSOR_ALIASES:
            standard_name = SENSOR_ALIASES[col_lower]
            # Si ya existe la columna estandar, combinar datos
            if standard_name in df.columns and standard_name != col:
                df[standard_name] = df[standard_name].combine_first(df[col])
                df = df.drop(columns=[col])
            elif standard_name != col:
                columns_to_rename[col] = standard_name
    
    if columns_to_rename:
        df = df.rename(columns=columns_to_rename)
    
    # Eliminar columnas duplicadas que puedan quedar
    df = df.loc[:, ~df.columns.duplicated()]
    
    return df


def get_sensor_display_info(sensor_name: str, sensor_config: dict) -> tuple:
    """Obtiene label y unidad para un sensor, usando config o defaults."""
    # Primero buscar en config del usuario
    if sensor_name in sensor_config:
        cfg = sensor_config[sensor_name]
        return cfg.get('label', sensor_name.title()), cfg.get('unit', '')
    
    # Luego buscar en defaults
    if sensor_name in SENSOR_LABELS:
        info = SENSOR_LABELS[sensor_name]
        return info['label'], info['unit']
    
    # Fallback
    return sensor_name.replace('_', ' ').title(), ''


# =============================================================================
# ARQUITECTURA OPTIMIZADA: Carga completa + Cache + Filtrado en memoria
# =============================================================================

# TTL de 24 horas (86400 segundos) para evitar recargas constantes
# El usuario puede forzar la recarga con el botón "Actualizar"
@st.cache_data(ttl=86400, show_spinner=False)
def cargar_historial_completo() -> pd.DataFrame:
    """
    Carga TODO el historial de datos sin límite.
    Esta función se cachea por 24 HORAS para evitar recargas innecesarias.
    
    Para obtener datos nuevos, el usuario debe presionar "Actualizar".
    
    Arquitectura basada en recomendación: 
    - Crear la solicitud una vez
    - Trabajar en un DataFrame que haga toda la pega
    - Sin límite de datos
    """
    try:
        start_time_total = time.time()
        db = DatabaseConnection()
        
        if db.collection is None:
            return pd.DataFrame()
        
        # Definir TIEMPO DE CORTE para sincronización
        cut_off_time = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-3))).replace(tzinfo=None)
        print(f"[graphs.py] Tiempo de corte de sincronización: {cut_off_time}")
        
        # Calcular fecha de inicio para la consulta (1 semana atrás + margen de 1 hora)
        start_date = cut_off_time - timedelta(weeks=1, hours=1)
        start_date_iso = start_date.isoformat()
        
        print(f"[graphs.py] Limitando consulta a datos desde: {start_date}")

        # Proyección optimizada
        projection = {
            '_id': 1, 'timestamp': 1, 'device_id': 1, 'dispositivo_id': 1,
            'sensors': 1, 'datos': 1, 'location': 1, 'metadata': 1
        }
        
        # Construir Query con filtro de fecha
        query = {
            "$or": [
                {"timestamp": {"$gte": start_date}},        # Para objetos Date
                {"timestamp": {"$gte": start_date_iso}}     # Para strings ISO
            ]
        }
        
        # Cargar documentos (intenta sort, fallback a sin sort)
        try:
            cursor = db.collection.find(query, projection).sort('timestamp', -1)
            raw_documents = list(cursor)
        except Exception as sort_error:
            print(f"[graphs.py] Sort falló: {sort_error}")
            cursor = db.collection.find(query, projection)
            raw_documents = list(cursor)
        
        print(f"[graphs.py] {len(raw_documents)} documentos cargados")
        
        # Normalizar documentos y FILTRAR por cut_off_time
        valid_docs = []
        docs_futuros = 0
        for doc in raw_documents:
            norm_doc = db._normalize_document(doc)
            ts = norm_doc.get("timestamp")
            
            if ts is not None and norm_doc.get("device_id") != "unknown":
                # Filtro de sincronización: ignorar datos posteriores al corte
                if ts > cut_off_time:
                    docs_futuros += 1
                    continue
                    
                valid_docs.append(norm_doc)
        
        print(f"[graphs.py] {len(valid_docs)} documentos válidos ({docs_futuros} ignorados por ser posteriores al corte)")
        
        if not valid_docs:
            return pd.DataFrame()
        
        # Convertir a DataFrame flat
        df = db._parse_historical_flat(valid_docs)
        
        # Normalizar columnas de sensores
        df = normalize_sensor_columns(df)
        
        # =====================================================================
        # FILTRAR TIMESTAMPS INVÁLIDOS
        # Excluir registros con fechas anteriores a 2020 (datos corruptos)
        # =====================================================================
        if 'timestamp' in df.columns and not df.empty:
            fecha_minima_valida = pd.Timestamp('2020-01-01')
            registros_antes = len(df)
            df = df[df['timestamp'] >= fecha_minima_valida]
            registros_filtrados = registros_antes - len(df)
            if registros_filtrados > 0:
                print(f"[graphs.py] Filtrados {registros_filtrados} registros con timestamps inválidos (<2020)")
        
        # Ordenar por timestamp ascendente
        if 'timestamp' in df.columns and not df.empty:
            df = df.sort_values('timestamp', ascending=True)
        
        elapsed_time = time.time() - start_time_total
        print(f"[graphs.py] Tiempo total de carga y procesamiento: {elapsed_time:.2f} segundos")
        
        # DEBUG: Mostrar t_max por dispositivo
        if 'timestamp' in df.columns and 'device_id' in df.columns and not df.empty:
            print(f"\n[graphs.py] === DATOS CARGADOS (t_max por dispositivo) ===")
            device_summary = df.groupby('device_id')['timestamp'].agg(['max', 'count']).reset_index()
            for _, row in device_summary.iterrows():
                print(f"  - {row['device_id']}: último dato = {row['max']} ({row['count']} registros)")
        
        return df
        
    except Exception as e:
        st.error(f"Error cargando historial: {str(e)}")
        return pd.DataFrame()



def filtrar_dataframe(
    df: pd.DataFrame, 
    dispositivos: List[str], 
    delta: Optional[timedelta],
    debug: bool = False
) -> pd.DataFrame:
    """
    Filtra el DataFrame cacheado por dispositivos y rango de tiempo.
    Esta operación es rápida porque trabaja en memoria.
    
    IMPORTANTE: El filtro de tiempo se aplica POR DISPOSITIVO para evitar que
    un dispositivo con mayor latencia "oculte" los datos de otro.
    """
    if df.empty:
        return df
    
    df_filtrado = df.copy()
    
    # Filtrar por dispositivos
    if dispositivos and 'device_id' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['device_id'].isin(dispositivos)]
    
    # DEBUG: Mostrar t_max por dispositivo ANTES del filtro de tiempo
    if debug and 'timestamp' in df_filtrado.columns and 'device_id' in df_filtrado.columns:
        pre_filter = df_filtrado.groupby('device_id').agg({
            'timestamp': ['min', 'max', 'count']
        }).reset_index()
        pre_filter.columns = ['device_id', 't_min', 't_max', 'count']
        print(f"\n[filtrar_dataframe] ANTES del filtro de tiempo:")
        for _, row in pre_filter.iterrows():
            print(f"  - {row['device_id']}: {row['t_min']} -> {row['t_max']} ({row['count']} registros)")
    
    # Filtrar por rango de tiempo POR DISPOSITIVO
    # Esto evita que un dispositivo con latencia diferente "oculte" a otro
    if delta is not None and 'timestamp' in df_filtrado.columns and 'device_id' in df_filtrado.columns:
        # Calcular t_max y t_min por dispositivo (vectorizado, mucho más rápido que apply)
        device_times = df_filtrado.groupby('device_id')['timestamp'].max().reset_index()
        device_times.columns = ['device_id', 't_max']
        device_times['t_min'] = device_times['t_max'] - delta
        
        # DEBUG: Mostrar los límites calculados
        if debug:
            print(f"\n[filtrar_dataframe] Límites para delta={delta}:")
            for _, row in device_times.iterrows():
                print(f"  - {row['device_id']}: t_max={row['t_max']}, filtrando desde t_min={row['t_min']}")
        
        # Merge para obtener t_min por registro
        df_filtrado = df_filtrado.merge(device_times[['device_id', 't_min']], on='device_id', how='left')
        
        # Filtrar y limpiar
        df_filtrado = df_filtrado[df_filtrado['timestamp'] >= df_filtrado['t_min']]
        df_filtrado = df_filtrado.drop(columns=['t_min'])
        
        # DEBUG: Mostrar resultado después del filtro
        if debug:
            post_filter = df_filtrado.groupby('device_id')['timestamp'].agg(['min', 'max', 'count']).reset_index()
            post_filter.columns = ['device_id', 't_min', 't_max', 'count']
            print(f"\n[filtrar_dataframe] DESPUÉS del filtro de tiempo:")
            for _, row in post_filter.iterrows():
                print(f"  - {row['device_id']}: {row['t_min']} -> {row['t_max']} ({row['count']} registros)")
    elif delta is not None and 'timestamp' in df_filtrado.columns:
        # Fallback: filtro global si no hay device_id
        t_max = df_filtrado['timestamp'].max()
        if pd.notna(t_max):
            t_min = t_max - delta
            df_filtrado = df_filtrado[df_filtrado['timestamp'] >= t_min]
    
    return df_filtrado


def show_view():
    # --- HEADER ---
    col_h1, col_h2 = st.columns([4, 1])
    with col_h1:
        st.markdown(f"<h3 style='margin:0;'>{ICON_CHART} Gráficas y Tendencias</h3>", unsafe_allow_html=True)
    with col_h2:
        if st.button("Actualizar", type="secondary", help="Recargar datos desde la base de datos"):
            print(f"\n[graphs.py] ========================================")
            print(f"[graphs.py] BOTÓN ACTUALIZAR PRESIONADO - Limpiando cache...")
            print(f"[graphs.py] ========================================")
            cargar_historial_completo.clear()
            st.rerun()
    
    # --- CONEXION Y CONFIG ---
    try:
        db = DatabaseConnection()
        config_manager = ConfigManager(db)
        sensor_config = config_manager.get_all_configured_sensors()
        device_metadata = config_manager.get_device_metadata()
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return
    
    # --- CARGA INICIAL DE DATOS (CACHEADA POR 24 HORAS) ---
    with st.spinner("Cargando historial completo (solo la primera vez, después será instantáneo)..."):
        df_completo = cargar_historial_completo()
    
    if df_completo is None or df_completo.empty:
        st.warning("No se encontraron datos en la base de datos.")
        st.markdown(f"{ICON_LIGHTBULB} Verifica que los dispositivos estén enviando datos correctamente.", unsafe_allow_html=True)
        return
    
    # Mostrar info de cache
    total_registros = len(df_completo)
    fecha_min_data = df_completo['timestamp'].min()
    fecha_max_data = df_completo['timestamp'].max()
    
    # --- FILTROS EN CONTENEDOR ---
    with st.container(border=True):
        st.markdown(f"<div style='margin-bottom: 10px; font-weight: 600; color: #475569;'>{ICON_SETTINGS} Configuración de Visualización</div>", unsafe_allow_html=True)
        
        # Info del dataset cargado
        st.markdown(f"<span style='font-size: 0.85rem; color: #64748b;'>{ICON_DATABASE} Dataset: {total_registros:,} registros | Desde: {fecha_min_data.strftime('%d/%m/%Y %H:%M') if pd.notna(fecha_min_data) else 'N/A'}</span>", unsafe_allow_html=True)
        
        c_time, c_dev, c_param = st.columns([1, 1, 1])
        
        # Opciones de tiempo (sin límites de datos, solo deltas)
        with c_time:
            time_options = {
                "5 Minutos": timedelta(minutes=5),
                "30 Minutos": timedelta(minutes=30),
                "1 Hora": timedelta(hours=1),
                "6 Horas": timedelta(hours=6),
                "24 Horas": timedelta(hours=24),
                "3 Días": timedelta(days=3),
                "1 Semana": timedelta(weeks=1),
            }
            time_keys = list(time_options.keys())
            
            # Inicializar session_state para el widget de tiempo
            if 'graphs_time_selector' not in st.session_state:
                st.session_state.graphs_time_selector = "5 Minutos"
            
            # Calcular índice seguro
            try:
                current_index = time_keys.index(st.session_state.graphs_time_selector)
            except ValueError:
                current_index = 0
            
            selected_range = st.selectbox(
                "Rango de Tiempo", 
                time_keys, 
                index=current_index,
                key="graphs_time_selector"
            )
            delta = time_options[selected_range]
        
        # Obtener dispositivos disponibles
        all_devices = sorted(df_completo['device_id'].unique().tolist())
        
        def get_device_alias(dev_id):
            """Obtiene el alias del dispositivo o retorna None si no hay alias."""
            meta = device_metadata.get(dev_id, {})
            return meta.get('alias', None)
        
        def has_configured_alias(dev_id):
            """Verifica si el dispositivo tiene un alias configurado."""
            return get_device_alias(dev_id) is not None
        
        # Filtrar: solo dispositivos con alias configurado (excluir desconocidos)
        devices = [dev_id for dev_id in all_devices if has_configured_alias(dev_id)]
        
        # Si no hay dispositivos con alias, mostrar todos (fallback)
        if not devices:
            devices = all_devices
        
        # Crear mapeo ID -> Alias para mostrar
        device_display_map = {dev_id: get_device_alias(dev_id) or dev_id for dev_id in devices}
        
        # Leer device_id de la URL
        url_device_id = st.query_params.get("device_id", None)
        
        # =====================================================================
        # MANEJO DE ESTADO: Preservar selecciones del usuario
        # Usamos 'default' para la primera carga, sin key (evita conflictos)
        # =====================================================================
        
        # Calcular default inicial
        if url_device_id and url_device_id in devices:
            initial_default = [url_device_id]
        else:
            # Usar selección previa si existe y es válida
            if 'graphs_prev_devices' in st.session_state:
                prev = st.session_state.graphs_prev_devices
                valid_prev = [d for d in prev if d in devices]
                initial_default = valid_prev if valid_prev else devices[:min(2, len(devices))]
            else:
                initial_default = devices[:min(2, len(devices))]
        
        with c_dev:
            selected_devices = st.multiselect(
                "Dispositivos", 
                devices, 
                default=initial_default,
                format_func=lambda x: device_display_map.get(x, x),
                key="graphs_device_multiselect"
            )
            # Guardar selección actual para próximo rerun
            st.session_state.graphs_prev_devices = selected_devices
        
        # Filtrar para obtener parámetros disponibles
        excluded = ['timestamp', 'device_id', 'location', 'id', '_id', 'lat', 'lon', 'device_name']
        numeric_cols = df_completo.select_dtypes(include=['number']).columns
        params = [c for c in numeric_cols if c not in excluded]
        
        # Filtrar parámetros disponibles para dispositivos seleccionados
        available_params = []
        if selected_devices:
            subset_df = df_completo[df_completo['device_id'].isin(selected_devices)]
            for col in params:
                if col in subset_df.columns and subset_df[col].notna().any():
                    available_params.append(col)
        else:
            available_params = params
        
        # Calcular default inicial para parámetros
        if url_device_id and url_device_id in devices:
            initial_params = available_params
        else:
            # Usar selección previa si existe y es válida
            if 'graphs_prev_params' in st.session_state:
                prev = st.session_state.graphs_prev_params
                valid_prev = [p for p in prev if p in available_params]
                initial_params = valid_prev if valid_prev else available_params[:min(2, len(available_params))]
            else:
                initial_params = available_params[:min(2, len(available_params))]
        
        with c_param:
            selected_params = st.multiselect(
                "Parámetros", 
                available_params, 
                default=initial_params,
                format_func=lambda x: get_sensor_display_info(x, sensor_config)[0],
                key="graphs_param_multiselect"
            )
            # Guardar selección actual para próximo rerun
            st.session_state.graphs_prev_params = selected_params

    if not selected_devices or not selected_params:
        st.markdown(f"<div style='padding: 12px; background: #e0f2fe; border-radius: 8px; color: #0369a1;'>{ICON_POINTER} Seleccione dispositivos y parámetros para visualizar.</div>", unsafe_allow_html=True)
        return

    # --- FILTRAR DATOS EN MEMORIA (RÁPIDO) ---
    # DEBUG desactivado para producción
    filtered_df = filtrar_dataframe(df_completo, selected_devices, delta, debug=False)
    
    if filtered_df.empty:
        st.warning("No hay datos para la selección actual.")
        return
    
    # Agregar columna de nombre/alias para gráficos
    def get_display_name(dev_id):
        alias = device_display_map.get(dev_id, dev_id)
        return alias
    
    filtered_df = filtered_df.copy()
    filtered_df['device_name'] = filtered_df['device_id'].apply(get_display_name)

    # --- INFO DE RANGO ---
    t_min = filtered_df['timestamp'].min()
    t_max = filtered_df['timestamp'].max()
    intervalo_str = f"{t_min.strftime('%d/%m %H:%M')} - {t_max.strftime('%d/%m %H:%M')}"
    
    # Info de dispositivos en datos
    devices_in_data = filtered_df['device_name'].nunique()
    
    st.markdown(
        f"""<div style='text-align: center; color: #64748b; font-size: 0.9rem; margin: 10px 0;'>
        {ICON_CHART} Mostrando: {intervalo_str} | Registros: {len(filtered_df):,} | Dispositivos: {devices_in_data}
        </div>""", 
        unsafe_allow_html=True
    )

    # --- GRÁFICOS ---
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Opción de escala compartida (con estado persistente)
    use_shared_scale = st.checkbox(
        "Usar escala Y compartida entre dispositivos", 
        value=True,
        key="graphs_shared_scale"
    )

    for param in selected_params:
        label, unit = get_sensor_display_info(param, sensor_config)
        unit_str = f" ({unit})" if unit else ""
        
        # Datos limpios para este gráfico
        chart_data = filtered_df[['timestamp', 'device_id', 'device_name', param]].dropna(subset=[param])
        
        if chart_data.empty:
            continue
        
        # Ordenar por dispositivo y timestamp
        chart_data = chart_data.sort_values(['device_name', 'timestamp'])

        with st.container(border=True):
            # Header del gráfico con promedios por dispositivo
            st.markdown(f"### {label}{unit_str}")
            
            # Calcular promedios por dispositivo
            promedios_dispositivos = chart_data.groupby('device_name')[param].mean()
            promedio_global = chart_data[param].mean()
            
            # Mostrar promedios por dispositivo en columnas dinámicas
            num_dispositivos = len(promedios_dispositivos)
            cols_promedios = st.columns(num_dispositivos + 1)  # +1 para el promedio global
            
            for idx, (dev_name, avg_val) in enumerate(promedios_dispositivos.items()):
                with cols_promedios[idx]:
                    st.metric(
                        label=dev_name,
                        value=f"{avg_val:.2f}",
                        help=f"Promedio de {label} para {dev_name}"
                    )
            
            # Última columna: Promedio Global
            with cols_promedios[-1]:
                st.metric(
                    label="Global",
                    value=f"{promedio_global:.2f}",
                    delta=None,
                    help=f"Promedio combinado de todos los dispositivos"
                )
            
            # Calcular rango Y si se comparte escala
            if use_shared_scale:
                y_min = chart_data[param].min()
                y_max = chart_data[param].max()
                y_margin = (y_max - y_min) * 0.1 if y_max != y_min else 1
                y_range = [y_min - y_margin, y_max + y_margin]
            else:
                y_range = None
            
            # Crear figura con múltiples trazos
            fig = go.Figure()
            
            # Colores distintivos para cada dispositivo
            colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']
            
            # Calcular ventana de SMA basada en cantidad de datos
            n_total = len(chart_data)
            window = 5 if n_total < 1000 else (20 if n_total < 10000 else 50)
            
            # Agregar trazos por dispositivo
            for idx, (dev_name, dev_data) in enumerate(chart_data.groupby('device_name', sort=False)):
                color = colors[idx % len(colors)]
                dev_sorted = dev_data.sort_values('timestamp')
                
                # Línea de valores reales (fina, semi-transparente)
                fig.add_trace(go.Scatter(
                    x=dev_sorted['timestamp'],
                    y=dev_sorted[param],
                    mode='lines',
                    name=f'{dev_name}',
                    line=dict(color=color, width=1),
                    opacity=0.5,
                    hovertemplate=f'{dev_name}<br>%{{x}}<br>{label}: %{{y:.2f}}{unit}<extra></extra>',
                    legendgroup=dev_name
                ))
                
                # Línea de tendencia (SMA) - gruesa, sólida
                if len(dev_sorted) > window:
                    sma = dev_sorted[param].rolling(window=window, min_periods=1).mean()
                    fig.add_trace(go.Scatter(
                        x=dev_sorted['timestamp'],
                        y=sma,
                        mode='lines',
                        name=f'{dev_name} (Tendencia)',
                        line=dict(color=color, width=2.5),
                        opacity=1.0,
                        hoverinfo='skip',
                        legendgroup=dev_name,
                        showlegend=True
                    ))
            
            # Personalización del layout
            fig.update_layout(
                hovermode="x unified",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    title=None
                ),
                margin=dict(l=20, r=20, t=30, b=20),
                height=380,
                template="plotly_white",
                xaxis=dict(
                    tickformat="%H:%M" if (delta and delta <= timedelta(hours=24)) else "%d/%m %H:%M",
                    showgrid=True,
                    gridcolor='rgba(0,0,0,0.05)'
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(0,0,0,0.05)',
                    range=y_range,
                    title=f'{label}{unit_str}'
                )
            )
            
            st.plotly_chart(fig, width='stretch')
            
            # --- ESTADÍSTICAS ---
            with st.expander("Estadísticas Detalladas", expanded=False):
                stats = chart_data.groupby('device_name')[param].agg(
                    Mínimo='min',
                    Promedio='mean',
                    Mediana='median',
                    Máximo='max',
                    Registros='count'
                ).reset_index()
                
                # Formatear columnas numéricas
                for col in ['Mínimo', 'Promedio', 'Mediana', 'Máximo']:
                    stats[col] = stats[col].map('{:.2f}'.format)
                
                stats = stats.rename(columns={'device_name': 'Dispositivo'})
                
                st.dataframe(
                    stats,
                    width='stretch',
                    hide_index=True
                )