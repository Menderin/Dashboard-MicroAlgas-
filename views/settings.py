import streamlit as st
import pandas as pd
from typing import Dict, Any, List

from modules.database import DatabaseConnection
from modules.config_manager import ConfigManager

# --- ICONOS SVG ---
ICON_SAVE = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>'
ICON_DEVICE = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>'
ICON_SLIDERS = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>'
ICON_WARN = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
ICON_CHECK = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'
ICON_EDIT = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>'


def discover_available_params(df: pd.DataFrame, device_id: str) -> List[str]:
    """
    Analiza las filas recientes del DataFrame para encontrar parámetros numéricos
    configurables, soportando estructuras planas y anidadas (sensors -> key -> value).
    """
    if df.empty:
        return []
        
    # Filtrar solo este dispositivo
    dev_rows = df[df['device_id'] == device_id]
    if dev_rows.empty:
        return []

    found_params = set()
    
    # Analizar hasta 5 filas recientes para robustez
    for _, row in dev_rows.head(5).iterrows():
        row_dict = row.to_dict()
        
        # 1. Buscar en claves anidadas conocidas ('sensors' o 'sensor_data')
        target_keys = ['sensors', 'sensor_data']
        
        for t_key in target_keys:
            if t_key in row_dict and isinstance(row_dict[t_key], dict):
                sensors_dict = row_dict[t_key]
                for key, val in sensors_dict.items():
                    if isinstance(val, dict) and 'value' in val:
                        # Verificar si es numérico
                        if isinstance(val['value'], (int, float)) and not isinstance(val['value'], bool):
                            found_params.add(key)
                    
                    elif isinstance(val, (int, float)) and not isinstance(val, bool):
                        found_params.add(key)
        
        # 2. Buscar en Top Level
        EXCLUDED = {'_id', 'id', 'device_id', 'timestamp', 'location', 
                   'lat', 'lon', 'alerts', 'sensor_data', 'metadata', 
                   'config', 'status', 'sensors', '_ros_topic'}
        
        for k, v in row_dict.items():
            if k in EXCLUDED: continue
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                found_params.add(k)
                
    return sorted(list(found_params))


def show_view():
    c1, c2 = st.columns([6, 1])
    with c1:
        st.subheader("Configuración del Sistema")
    with c2:
        if st.button("Recargar", type="primary"): st.rerun()

    try:
        db = DatabaseConnection()
        config_manager = ConfigManager(db)
    except Exception as e:
        st.error(f"Error base de datos: {str(e)}")
        return

    t1, t2 = st.tabs(["Identidad Dispositivos", "Umbrales & Alertas"])

    # --- PESTAÑA 1: ALIAS ---
    with t1:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f"<div style='margin-bottom:10px; font-weight:600; color:#475569; display:flex; align-items:center; gap:8px;'>{ICON_DEVICE} Gestión de Alias</div>", unsafe_allow_html=True)
            
            try:
                recent_df = db.get_latest_by_device()
                detected_ids = sorted(recent_df['device_id'].unique().tolist()) if not recent_df.empty else []
            except:
                detected_ids = []
                recent_df = pd.DataFrame()
            
            metadata = config_manager.get_device_metadata()
            all_ids = sorted(list(set(detected_ids + list(metadata.keys()))))
            
            if not all_ids:
                st.info("No se han detectado dispositivos.")
            else:
                # Función para mostrar nombres legibles
                def format_device_display(dev_id):
                    dev_meta = metadata.get(dev_id, {})
                    alias = dev_meta.get("alias", dev_id)
                    return f"{alias} ({dev_id[:8]}...)" if len(dev_id) > 8 else alias
                
                c_sel, c_edit = st.columns([1, 2])
                with c_sel:
                    selected_id = st.selectbox("Selecciona ID Técnico", all_ids, format_func=format_device_display)
                    curr_meta = metadata.get(selected_id, {})
                
                with c_edit:
                    with st.form("meta_form"):
                        st.markdown(f"**Editando: {selected_id}**")
                        n_alias = st.text_input("Alias Visible", value=curr_meta.get("alias", selected_id))
                        n_loc = st.text_input("Ubicación Física", value=curr_meta.get("location", ""))
                        
                        if st.form_submit_button("Guardar Identidad", type="primary", width="stretch"):
                            if config_manager.update_device_metadata(selected_id, n_alias, n_loc):
                                st.success("Guardado correctamente.")
                                st.rerun()
                            else:
                                st.error("Error al guardar.")

    # --- PESTAÑA 2: UMBRALES POR DISPOSITIVO ---
    with t2:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f"<div style='margin-bottom:10px; font-weight:600; color:#475569; display:flex; align-items:center; gap:8px;'>{ICON_SLIDERS} Configuración de Rangos</div>", unsafe_allow_html=True)
            
            if not all_ids:
                st.warning("Sin dispositivos disponibles.")
            else:
                # Crear función de formato para mostrar nombres en lugar de IDs
                def format_device_name(dev_id):
                    dev_meta = metadata.get(dev_id, {})
                    alias = dev_meta.get("alias", dev_id)
                    return f"{alias} ({dev_id[:8]}...)" if len(dev_id) > 8 else alias
                
                # 1. Seleccionar Dispositivo
                target_dev = st.selectbox("1. Dispositivo", all_ids, key="thr_dev_sel", format_func=format_device_name)
                
                # 2. Descubrir Parámetros
                valid_params = discover_available_params(recent_df, target_dev)

                if not valid_params:
                    st.info("No se detectaron parámetros numéricos configurables para este dispositivo (revisar conexión de sensores).")
                    # Debug info si no encuentra nada
                    if st.checkbox("Ver Debug Data"):
                         st.write(recent_df[recent_df['device_id']==target_dev].head(1).to_dict())
                else:
                    target_param = st.selectbox("Parámetro", valid_params, format_func=lambda x: str(x).replace('_', ' ').title())
                    
                    # Cargar Conf
                    base_conf = config_manager.get_all_configured_sensors().get(target_param, {})
                    dev_specifics_raw = config_manager.get_device_thresholds(target_dev)
                    
                    # COMPATIBILIDAD: Convertir formato antiguo (ph_min, temp_max, etc.) a nuevo formato
                    # Si los umbrales están en formato plano, convertirlos
                    dev_specifics = {}
                    if dev_specifics_raw:
                        # Verificar si tiene formato nuevo (agrupado por parámetro)
                        has_new_format = any(isinstance(v, dict) and 'min_value' in v for v in dev_specifics_raw.values())
                        
                        if not has_new_format:
                            # Convertir formato antiguo a nuevo
                            # Mapear {ph_min: 6, ph_max: 8.2, temp_max: 30} 
                            # a {ph: {min_value: 6, max_value: 8.2}, temperatura: {max_value: 30}}
                            param_map = {
                                'ph': 'ph',
                                'temperatura': 'temperatura',
                                'temperature': 'temperatura',
                                'temp': 'temperatura'
                            }
                            
                            for key, value in dev_specifics_raw.items():
                                # Parsear keys como "ph_min", "temp_max", etc.
                                parts = key.lower().split('_')
                                if len(parts) >= 2:
                                    param_name = '_'.join(parts[:-1])  # todo menos el último
                                    threshold_type = parts[-1]  # min, max, etc
                                    
                                    # Normalizar nombre del parámetro
                                    normalized_param = param_map.get(param_name, param_name)
                                    
                                    if normalized_param not in dev_specifics:
                                        dev_specifics[normalized_param] = {}
                                    
                                    # Mapear el tipo de umbral
                                    if threshold_type == 'min':
                                        dev_specifics[normalized_param]['min_value'] = float(value)
                                    elif threshold_type == 'max':
                                        dev_specifics[normalized_param]['max_value'] = float(value)
                        else:
                            dev_specifics = dev_specifics_raw
                    
                    current_conf = dev_specifics.get(target_param, base_conf)
                    
                    # Get Values - Solo min y max
                    d_omin = float(current_conf.get("min_value", 4.0))
                    d_omax = float(current_conf.get("max_value", 8.0))
                    
                    # Calcular zonas automáticas (20% del rango)
                    range_size = d_omax - d_omin
                    alert_margin = range_size * 0.20
                    calc_alert_min = d_omin + alert_margin
                    calc_alert_max = d_omax - alert_margin

                    # 3. Form
                    st.markdown("---")
                    st.markdown(f"**Rangos para '{target_param.upper()}' en '{format_device_name(target_dev)}'**")
                    
                    # Información sobre el cálculo automático
                    st.info("ℹ **Cálculo Automático de Zonas**: El sistema calcula automáticamente las zonas de alerta (20% del rango) y crítico (fuera del rango). Solo necesitas definir el rango seguro mínimo y máximo.")
                    
                    with st.form(f"range_form_{target_dev}"):
                        # Solo 2 inputs: min y max del rango seguro
                        c1, c2 = st.columns(2)
                        
                        with c1:
                            st.markdown("**Valor Mínimo Seguro**")
                            val_opt_min = st.number_input("Mínimo del rango seguro", value=d_omin, step=0.1, 
                                                         help="Valor mínimo aceptable para condiciones normales")
                            
                        with c2:
                            st.markdown("** Valor Máximo Seguro**")
                            val_opt_max = st.number_input("Máximo del rango seguro", value=d_omax, step=0.1,
                                                         help="Valor máximo aceptable para condiciones normales")
                        
                        # Logic check
                        err = None
                        if val_opt_min >= val_opt_max: 
                            err = "El mínimo debe ser menor que el máximo"
                        
                        if err:
                            st.error(f" {err}")

                        submitted = st.form_submit_button(" Guardar Umbrales", type="primary", use_container_width=True)
                        
                        if submitted:
                            if err:
                                st.error(f"No se puede guardar: {err}")
                            else:
                                # Guardar en formato PLANO (temp_min, temp_max) en lugar de objetos anidados
                                # Normalizar nombre de parámetro para claves
                                param_key = target_param.lower().replace('temperature', 'temp').replace('temperatura', 'temp')
                                
                                # Crear claves planas
                                min_key = f"{param_key}_min"
                                max_key = f"{param_key}_max"
                                
                                # Preparar data para guardar en formato plano
                                flat_data = {
                                    min_key: val_opt_min,
                                    max_key: val_opt_max
                                }
                                
                                # Usar DatabaseConnection que ya está importada al inicio del archivo
                                db = DatabaseConnection()
                                
                                # Actualizar múltiples campos a la vez en formato plano
                                success = db.update_device_fields(target_dev, {f"umbrales.{k}": v for k, v in flat_data.items()})
                                
                                if success:
                                    st.success(f" Umbrales guardados para {target_param}. Zonas de alerta y crítico se calcularán automáticamente.")
                                    st.rerun()
                                else:
                                    st.error(" Error al guardar.")