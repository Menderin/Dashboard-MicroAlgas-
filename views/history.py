import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone, time as dt_time
from io import BytesIO
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from modules.database import DatabaseConnection
from modules.config_manager import ConfigManager

# ICONOS SVG
ICON_SEARCH = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>'
ICON_SETTINGS = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>'
ICON_INFO = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
ICON_EYE = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>'
ICON_ALERT = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
ICON_CLOCK = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>'
ICON_LIST = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>'
ICON_CPU = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>'

# =============================================================================
# FUNCIÓN DE CARGA OPTIMIZADA (Paralela + Caché por Rango)
# =============================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def cargar_datos_rango(start_date: datetime, end_date: datetime, devices: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Carga datos corrigiendo desfases de zona horaria (UTC vs Local).
    Estrategia: Busca 1 día extra en el futuro para capturar datos UTC y luego normaliza a Local.
    Opción para filtrar por devices directamente en BD.
    """
    start_time_total = time.time()
    
    # 1. Extender rango de búsqueda en DB generosamente (+/- 2 días)
    mongo_end_date = end_date + timedelta(days=2)
    mongo_start_date = start_date - timedelta(days=2)
    
    # Normalizar inputs para comparaciones
    if start_date.tzinfo: start_date = start_date.replace(tzinfo=None)
    if end_date.tzinfo: end_date = end_date.replace(tzinfo=None)

    try:
        db = DatabaseConnection()
        if db.collection is None:
            return pd.DataFrame()

        start_iso = start_date.isoformat()
        mongo_start_iso = mongo_start_date.isoformat()
        mongo_end_iso = mongo_end_date.isoformat()
        
        # Base Query de tiempo EXTENDIDA
        time_query = {
            "$or": [
                {"timestamp": {"$gte": mongo_start_date, "$lte": mongo_end_date}},
                {"timestamp": {"$gte": mongo_start_iso, "$lte": mongo_end_iso}}
            ]
        }
        
        projection = {
            '_id': 1, 'timestamp': 1, 'device_id': 1, 'dispositivo_id': 1,
            'sensors': 1, 'datos': 1, 'location': 1, 'metadata': 1
        }
        
        # Sin sort en DB para velocidad
        cursor = db.collection.find(time_query, projection)
        raw_docs = list(cursor)
        
        valid_docs = []
        for doc in raw_docs:
            norm = db._normalize_document(doc)
            if norm.get("timestamp") and norm.get("device_id") != "unknown":
                
                # FILTRO DE DISPOSITIVOS (EN MEMORIA)
                if devices and norm.get("device_id") not in devices:
                    continue

                ts = norm["timestamp"]
                
                if isinstance(ts, str):
                    ts = pd.to_datetime(ts)
                
                # CONVERSIÓN EXPLÍCITA A UTC-3 (CHILE)
                target_offset = timedelta(hours=-3)
                
                if isinstance(ts, datetime):
                    if ts.tzinfo is not None:
                        ts_utc = ts.astimezone(timezone.utc)
                        ts_local = ts_utc + target_offset
                        ts = ts_local.replace(tzinfo=None)
                    else:
                        # Naive: Asumimos ya local
                        pass
                
                norm["timestamp"] = ts
                
                # Filtro FINAL EXACTO
                if start_date <= ts <= end_date:
                    valid_docs.append(norm)

        if not valid_docs:
            return pd.DataFrame()

        # Convertir a DataFrame
        df = db._parse_historical_flat(valid_docs)
        
        # Limpieza columnas
        try:
            cols_map = {}
            for c in df.columns:
                clean = c.lower().strip()
                if clean in ['temp', 'temperatura']: clean = 'temperature'
                cols_map[c] = clean
            df = df.rename(columns=cols_map)
        except:
            pass
        
        # Ordenar DESC
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp', ascending=False)
            
        print(f"[history.py] Total Global DataFrame: {len(df)} registros.")
        return df

    except Exception as e:
        print(f"[history.py] Error crítico: {e}")
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()

def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

def convert_df_to_excel(df):
    output = BytesIO()
    # Cambiado a openpyxl por compatibilidad
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Datos')
    return output.getvalue()

def show_view():
    c1, c2 = st.columns([5, 2])
    with c1:
        st.subheader("Base de Datos Histórica")
    with c2:
        if st.button("Actualizar Tabla", type="primary", key="refresh_btn", help="Recargar datos"):
            cargar_datos_rango.clear()
            st.rerun()

    # --- 1. CARGA INICIAL ---
    try:
        db = DatabaseConnection()
        config_manager = ConfigManager(db)
        sensor_config = config_manager.get_all_configured_sensors()
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return

    # --- 2. FILTROS GENERALES ---
    # --- 2. BARRA DE CONTROL ---
    
    # Pre-cargar dispositivos conocidos para el filtro
    known_devices = []
    alias_map_pre = {}
    try:
        cm_pre = ConfigManager(DatabaseConnection())
        meta_pre = cm_pre.get_device_metadata()
        if meta_pre:
            known_devices = sorted(list(meta_pre.keys()))
            for k, v in meta_pre.items():
                if isinstance(v, dict) and v.get("alias"):
                    alias_map_pre[k] = v.get("alias")
    except:
        pass

    with st.container(border=True):
        st.markdown(f"<div style='margin-bottom: 10px; font-weight: 600; color: #475569; display:flex; align-items:center; gap:8px;'>{ICON_SEARCH} Panel de Control</div>", unsafe_allow_html=True)
        
        # Fila 1: Fechas, Dispositivos y Acción
        c_date, c_dev, c_btn = st.columns([2, 2, 1.2])
        
        with c_date:
            today = datetime.now().date()
            default_start = today - timedelta(days=7)
            
            date_range = st.date_input(
                "Rango de Fechas",
                value=(default_start, today),
                max_value=today,
                format="DD/MM/YYYY"
            )
            
        with c_dev:
            def fmt_dev_pre(x):
                return alias_map_pre.get(x, x)
                
            sel_devices_pre = st.multiselect(
                "Dispositivos (Dejar vacío para todos)",
                options=known_devices,
                format_func=fmt_dev_pre,
                placeholder="Seleccionar sensores..."
            )
            
        with c_btn:
             # Espacio para alinear con el input
             st.markdown('<div style="margin-top: 29px;"></div>', unsafe_allow_html=True)
             buscar = st.button("BUSCAR REGISTROS", type="primary", use_container_width=True)

        
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_d, end_d = date_range
            start_time = datetime.combine(start_d, dt_time.min)
            end_time = datetime.combine(end_d, dt_time.max)
        else:
            st.info("Selecciona una fecha de inicio y fin válidas.")
            return

        # Inicializar estado
        if 'history_data' not in st.session_state:
            st.session_state.history_data = None
        if 'last_params' not in st.session_state:
            st.session_state.last_params = None
            
        # Detectar cambios en filtros para limpiar vista vieja
        # Tupla hashable de params actuales
        current_params = (start_time, end_time, tuple(sorted(sel_devices_pre)))
        
        if st.session_state.last_params != current_params and not buscar:
            # Si cambiaron los params y NO se ha pulsado buscar aun -> Limpiar
            st.session_state.history_data = None
            
        if buscar:
            # Definir lista de devices a buscar (None = Todos)
            devs_to_search = sel_devices_pre if sel_devices_pre else None
            
            with st.spinner(f"Consultando..."):
                st.session_state.history_data = cargar_datos_rango(start_time, end_time, devs_to_search)
                st.session_state.last_params = current_params
                
        df = st.session_state.history_data

        if df is None:
            st.markdown(f"""
            <div style="margin-top:20px; padding:15px; border-radius:8px; background-color:#f8fafc; border:1px dashed #cbd5e1; color:#64748b; display:flex; gap:10px; align-items:center;">
                {ICON_INFO} 
                <span>Configura los filtros y presiona <b>'BUSCAR REGISTROS'</b> para ver los datos.</span>
            </div>
            """, unsafe_allow_html=True)
            return
            
        if df.empty:
            st.warning("No se encontraron registros.")
            return

        # Preprocesamiento
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.dropna(subset=['timestamp'])
            if not df.empty and df['timestamp'].dt.tz is not None:
                df['timestamp'] = df['timestamp'].dt.tz_localize(None)

        # --- FILTROS SECUNDARIOS (Texto) ---
        st.markdown("---")
        
        cf1, cf2 = st.columns([3, 1])
        with cf1:
             text_search = st.text_input("Filtrar resultados por Texto (ID, Ubicación)", placeholder="Buscar en resultados cargados...")


    # Aplicar Filtros
    
    # Referenciar mapa de alias para uso local
    alias_map = alias_map_pre

    # (El filtro de dispositivos ya se aplicó en la consulta a BD)
    if text_search:
        s = text_search.lower()
        if 'location' not in df.columns: df['location'] = ""
        # Buscar tambien en alias
        df['temp_alias'] = df['device_id'].map(lambda x: alias_map.get(x, "").lower())
        
        df = df[df['device_id'].astype(str).str.lower().str.contains(s) | 
                df['location'].astype(str).str.lower().str.contains(s) |
                df['temp_alias'].str.contains(s)]
        df = df.drop(columns=['temp_alias'])

    # --- MÉTRICAS DE ESTADO ---
    if not df.empty:
        try:
            # Calcular desglose
            dev_counts = df['device_id'].value_counts().reset_index()
            dev_counts.columns = ['device_id', 'count']
            dev_counts['alias'] = dev_counts['device_id'].apply(lambda x: alias_map.get(x, x))
            
            summary_items = []
            for _, row in dev_counts.iterrows():
                summary_items.append(f"<span style='background:#e0f2fe; color:#0369a1; padding:2px 8px; border-radius:4px;'>{row['alias']}: <b>{row['count']}</b></span>")
            
            dev_summary_html = " ".join(summary_items)

            min_ts = df['timestamp'].min().strftime('%d/%m %H:%M:%S')
            max_ts = df['timestamp'].max().strftime('%d/%m %H:%M:%S')
            total_devs = df['device_id'].nunique()
            
            st.markdown(f"""
            <div style="background-color:#ffffff; padding:15px; border-radius:8px; font-size:0.9rem; color:#334155; border:1px solid #e2e8f0; margin-top:15px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:20px; border-bottom:1px solid #f1f5f9; padding-bottom:10px; margin-bottom:10px;">
                    <div style="display:flex; align-items:center; gap:6px;">
                        {ICON_CLOCK} <span style="font-weight:600;">Rango:</span> {min_ts} — {max_ts}
                    </div>
                    <div style="display:flex; align-items:center; gap:6px;">
                        {ICON_LIST} <span style="font-weight:600;">Total Registros:</span> {len(df)}
                    </div>
                    <div style="display:flex; align-items:center; gap:6px;">
                        {ICON_CPU} <span style="font-weight:600;">Dispositivos:</span> {total_devs}
                    </div>
                </div>
                <div style="font-size:0.8rem; display:flex; align-items:center; gap:8px;">
                    <span style="color:#64748b;">Detalle:</span> {dev_summary_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error métricas: {e}")

    # --- 3. SECCIÓN DE DESCARGA ---
    st.markdown("---")
    res_txt = f"Registros seleccionados: {len(df)}"
    st.markdown(f"#### Exportar Datos ({res_txt})")
    
    c_down1, c_down2 = st.columns(2)
    
    # Generar nombre de archivo base
    try:
        f_start = start_d.strftime('%Y%m%d')
        f_end = end_d.strftime('%Y%m%d')
    except:
        f_start = "inicio"
        f_end = "fin"
        
    file_base = f"biofloc_data_{f_start}_{f_end}"
    
    with c_down1:
        csv_data = convert_df_to_csv(df)
        st.download_button(
            label="Descargar Selección (CSV)",
            data=csv_data,
            file_name=f"{file_base}.csv",
            mime="text/csv",
            help="Formato ligero, ideal para análisis de datos masivos.",
            type="primary",
            width="stretch"
        )

    with c_down2:
        try:
            excel_data = convert_df_to_excel(df)
            st.download_button(
                label="Descargar Selección (Excel)",
                data=excel_data,
                file_name=f"{file_base}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Formato Excel con encabezados y formato de celdas.",
                type="primary",
                width="stretch"
            )
        except Exception as e:
             st.warning(f"Error generando Excel: {e}")

    # Separador
    st.markdown("<br>", unsafe_allow_html=True)

    # --- 4. OPCIÓN: DESCARGAR TODO ---
    with st.expander("Descargar Base de Datos Completa (Backup)", expanded=False):
        st.info("Esta opción descargará TODOS los datos históricos disponibles. Puede tardar varios minutos.")
        if st.button("Generar Backup Completo (CSV)"):
            with st.spinner("Generando backup completo..."):
                # Cargar últimos 10 años
                now = datetime.now()
                backup_start = now - timedelta(days=3650)
                df_all = cargar_datos_rango(backup_start, now)
                
                if not df_all.empty:
                    csv_all = convert_df_to_csv(df_all)
                    st.success(f"Backup generado: {len(df_all)} registros.")
                    st.download_button(
                        label="Descargar Archivo Backup Completo",
                        data=csv_all,
                        file_name=f"FULL_BACKUP_BIOFLOC_{now.strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        type="secondary"
                    )
                else:
                    st.error("No se encontraron datos para el backup.")

    st.markdown("---")

    # --- 5. VISTA PREVIA ---
    # --- 5. VISTA PREVIA ---
    st.markdown(f"**Vista Previa (Últimos {min(500, len(df))} registros)**")
    
    # Preparar DF para mostrar (Alias en vez de ID)
    df_show = df.head(500).copy()
    if 'device_id' in df_show.columns:
        df_show['Dispositivo'] = df_show['device_id'].apply(lambda x: alias_map.get(x, x))
        
    # Reordenar columnas para visualización
    base_cols = ['timestamp', 'Dispositivo', 'location']
    final_cols = [c for c in base_cols if c in df_show.columns] + [c for c in df_show.columns if c not in base_cols and c != 'device_id' and c != '_id']
    df_show = df_show[final_cols]
    
    column_config = {
        "timestamp": st.column_config.DatetimeColumn("Fecha/Hora", format="DD/MM/YYYY HH:mm:ss"),
        "location": "Ubicación",
    }
    
    # Configurar columnas dinámicas
    num_preview_cols = [c for c in df_show.select_dtypes(include=['number']).columns]
    for col in num_preview_cols:
        label = sensor_config.get(col, {}).get('label', col.title())
        unit = sensor_config.get(col, {}).get('unit', '')
        column_config[col] = st.column_config.NumberColumn(f"{label} ({unit})", format="%.2f")
            
    st.dataframe(
        df_show,
        column_config=column_config,
        use_container_width=True,
        hide_index=True
    )
