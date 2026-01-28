import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict

from modules.database import DatabaseConnection
from modules.config_manager import ConfigManager

# ICONOS SVG
ICON_CHART = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="M18.7 8l-5.1 5.2-2.8-2.7L7 14.3"/></svg>'


def show_view():
    # --- HEADER ---
    c1, c2 = st.columns([6, 1])
    with c1:
        st.subheader("Gráficas y Tendencias")
    with c2:
        if st.button("Actualizar", type="primary"):
            st.rerun()

    # --- DATOS ---
    try:
        db = DatabaseConnection()
        config_manager = ConfigManager(db)
        sensor_config = config_manager.get_all_configured_sensors()
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return

    # --- FILTROS ---
    with st.container(border=True):
        st.markdown("<div style='margin-bottom: 10px; font-weight: 600; color: #475569;'>Configuración de Visualización</div>", unsafe_allow_html=True)
        
        c_time, c_dev, c_param = st.columns([1, 1, 1])
        
        with c_time:
            time_options = {
                "Última hora": timedelta(hours=1),
                "Últimas 6 horas": timedelta(hours=6),
                "Últimas 24 horas": timedelta(days=1),
                "Últimos 3 días": timedelta(days=3),
                "Última semana": timedelta(weeks=1),
                "Último mes": timedelta(days=30),
            }
            selected_range = st.selectbox("Rango de Tiempo", list(time_options.keys()), index=2)
            delta = time_options[selected_range]
        
        # Cargar datos base
        end_time = datetime.now()
        start_time = end_time - delta
        
        with st.spinner("Refrescando datos..."):
            # Límite reducido por seguridad de memoria en MongoDB sin índices
            df = db.fetch_data(start_date=start_time, end_date=end_time, limit=50000)

        if df is None or df.empty:
            st.warning("No se encontraron datos en este rango de tiempo.")
            return

        # Procesar Timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.dropna(subset=['timestamp'])
            if not df.empty and df['timestamp'].dt.tz is not None:
                df['timestamp'] = df['timestamp'].dt.tz_localize(None)

        devices = sorted(df['device_id'].unique().tolist())
        excluded = ['timestamp', 'device_id', 'location', 'id', '_id', 'lat', 'lon']
        numeric_cols = df.select_dtypes(include=['number']).columns
        params = [c for c in numeric_cols if c not in excluded]

        # Leer device_id de la URL (viene del boton de graficas en el dashboard)
        url_device_id = st.query_params.get("device_id", None)
        
        # Determinar seleccion por defecto
        if url_device_id and url_device_id in devices:
            default_devices = [url_device_id]
        else:
            default_devices = devices[:min(3, len(devices))]

        with c_dev:
            selected_devices = st.multiselect("Dispositivos", devices, default=default_devices)
            
        # Filtrar parametros disponibles para los dispositivos seleccionados
        available_params = []
        if selected_devices:
            # Subconjunto de datos para dispositivos seleccionados
            subset_df = df[df['device_id'].isin(selected_devices)]
            # Identificar columnas que no sean todo NaN o cero
            for col in params:
                if col in subset_df.columns and subset_df[col].notna().any():
                    available_params.append(col)
        else:
            available_params = params

        with c_param:
            # Si viene de una tarjeta, mostrar TODOS los parametros disponibles
            if url_device_id and url_device_id in devices:
                default_params = available_params
            else:
                # Interseccion para asegurar que los defaults existan en available_params
                temps = [p for p in available_params if "temp" in p.lower()]
                defaults = temps if temps else available_params[:min(2, len(available_params))]
                default_params = defaults
            
            selected_params = st.multiselect(
                "Parámetros", 
                available_params, 
                default=default_params,
                format_func=lambda x: sensor_config.get(x, {}).get('label', x.replace('_', ' ').title())
            )

    if not selected_devices or not selected_params:
        st.info("Seleccione dispositivos y parámetros para visualizar.")
        return

    # Filtrar datos finales
    filtered_df = df[df['device_id'].isin(selected_devices)].copy()
    if filtered_df.empty:
        st.warning("No hay datos para la selección actual.")
        return

    # --- GRÁFICOS PLOTLY ---
    st.markdown("<br>", unsafe_allow_html=True)

    for param in selected_params:
        conf = sensor_config.get(param, {})
        label = conf.get('label', param.replace('_', ' ').title())
        unit = conf.get('unit', '')
        
        # Datos limpìos para este gráfico
        chart_data = filtered_df[['timestamp', 'device_id', param]].dropna()
        
        if chart_data.empty:
            continue

        with st.container(border=True):
            # Crear gráfico Plotly
            fig = px.line(
                chart_data, 
                x='timestamp', 
                y=param, 
                color='device_id',
                title=f"<b>{label}</b>",
                labels={'timestamp': 'Fecha / Hora', param: f'{label} ({unit})', 'device_id': 'Dispositivo'},
                template="plotly_white",
            )
            
            # Personalización Fina
            fig.update_layout(
                hovermode="x unified",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                margin=dict(l=20, r=20, t=60, b=20),
                height=350
            )
            
            # Líneas más suaves y puntos
            fig.update_traces(line=dict(width=2.5), mode='lines')
            
            st.plotly_chart(fig, width="stretch")
            
            # --- SECCIÓN DE ESTADÍSTICAS ---
            with st.expander(f"Estadísticas Detalladas: {label}", expanded=False):
                # Calcular métricas agrupadas por dispositivo
                stats = chart_data.groupby('device_id')[param].agg(
                    Mínimo='min',
                    Promedio='mean',
                    Mediana='median',
                    Máximo='max',
                    Registros='count'
                ).reset_index()
                
                # Formatear columnas numéricas
                cols_num = ['Mínimo', 'Promedio', 'Mediana', 'Máximo']
                for col in cols_num:
                    stats[col] = stats[col].map('{:.2f}'.format)
                
                # Renombrar columna índice para display
                stats = stats.rename(columns={'device_id': 'Dispositivo'})
                
                st.dataframe(
                    stats,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Dispositivo": st.column_config.TextColumn("Dispositivo", width="medium"),
                        "Registros": st.column_config.NumberColumn("N° Datos"),
                    }
                )