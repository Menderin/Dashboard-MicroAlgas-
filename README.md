# 🦐 Biofloc Monitor UCN

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.36+-red?logo=streamlit&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green?logo=mongodb&logoColor=white)

**Sistema de monitoreo y control de calidad de agua para acuicultura Biofloc**

[Demo en Vivo](#) · [Documentación](docs/MANUAL_USUARIO.md) · [Reportar Bug](https://github.com/Marton1123/Biofloc-Monitor-UCN/issues)

</div>

---

## 📋 Descripción

Plataforma web para la supervisión remota de parámetros fisicoquímicos críticos (pH, oxígeno disuelto, temperatura, entre otros) en sistemas de cultivo Biofloc. El sistema procesa datos de telemetría provenientes de múltiples nodos sensores IoT almacenados en MongoDB Atlas.

### ✨ Funcionalidades Principales

| Función | Descripción |
|---------|-------------|
| **📊 Dashboard en Tiempo Real** | Visualización del estado de cada dispositivo con actualizaciones parciales por tarjeta |
| **🚦 Sistema de Alertas** | Semaforización automática (Normal/Alerta/Crítico) basada en umbrales configurables |
| **📈 Gráficas Interactivas** | Análisis de tendencias con Plotly, zoom, pan y exportación de imágenes |
| **📥 Exportación de Datos** | Descarga de históricos en formato Excel (.xlsx) y CSV |
| **⚙️ Configuración Dinámica** | Ajuste de umbrales y metadatos de dispositivos sin reiniciar el sistema |
| **🔄 Actualización Parcial** | Botón de refresh por dispositivo que solo recarga esa tarjeta (sin recargar toda la página) |

---

## 🏗️ Arquitectura

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   ESP32 + IoT   │────▶│  MongoDB Atlas   │◀────│  Streamlit App  │
│   Sensores      │     │  (Base de Datos) │     │  (Esta App)     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

**Stack Tecnológico:**
- **Frontend**: Streamlit 1.36+ con estilos CSS personalizados
- **Backend**: Python 3.10+ con PyMongo
- **Base de Datos**: MongoDB Atlas (Cloud)
- **Visualización**: Plotly Express
- **Procesamiento**: Pandas, NumPy

---

## 📁 Estructura del Proyecto

```
Biofloc-Monitor-UCN/
├── Home.py                    # Punto de entrada y navegación
├── requirements.txt           # Dependencias del proyecto
├── .env                       # Variables de entorno (NO en git)
├── .streamlit/
│   └── secrets.toml          # Secretos para Streamlit Cloud
│
├── views/                     # Vistas de la aplicación
│   ├── dashboard.py          # Dashboard principal con tarjetas
│   ├── graphs.py             # Gráficas interactivas
│   ├── history.py            # Historial y exportación de datos
│   └── settings.py           # Configuración de sensores y dispositivos
│
├── modules/                   # Lógica de negocio
│   ├── database.py           # Conexión y queries a MongoDB
│   ├── device_manager.py     # Evaluación de estado de dispositivos
│   ├── config_manager.py     # Gestión de configuración
│   ├── sensor_registry.py    # Registro de sensores detectados
│   └── styles.py             # Estilos CSS globales
│
├── scripts/                   # Scripts de utilidad
│   └── mock_data_generator.py # Generador de datos de prueba
│
├── config/                    # Configuración estática
│   └── sensor_defaults.json  # Valores por defecto de sensores
│
├── assets/                    # Recursos estáticos
│   ├── logo_acui.png
│   └── logo_eic.png
│
└── docs/                      # Documentación
    └── MANUAL_USUARIO.md
```

---

## 🚀 Instalación Local

### Prerrequisitos

- [Anaconda](https://www.anaconda.com/download) o Python 3.10+
- Cuenta en [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) (gratis)

### 1. Clonar el Repositorio

```bash
git clone https://github.com/Marton1123/Biofloc-Monitor-UCN.git
cd Biofloc-Monitor-UCN
```

### 2. Crear Entorno Virtual (Anaconda)

```bash
conda create --name biofloc_env python=3.10 -y
conda activate biofloc_env
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```ini
MONGO_URI=mongodb+srv://<usuario>:<password>@<cluster>.mongodb.net/
MONGO_DB=BioflocDB
MONGO_COLLECTION=SensorReadings
```

### 5. Ejecutar la Aplicación

```bash
streamlit run Home.py
```

Accede a `http://localhost:8501` en tu navegador.

---

## 🧪 Generar Datos de Prueba

El proyecto incluye un generador de datos mock para testing:

```bash
python scripts/mock_data_generator.py
```

**Opciones del generador:**
- Genera lecturas para múltiples dispositivos simulados
- Incluye variaciones realistas en los parámetros
- Simula escenarios de alerta y condiciones críticas
- Los datos se insertan directamente en MongoDB

---

## ☁️ Deploy en Streamlit Cloud

### 1. Preparar el Repositorio

Asegúrate de que tu repositorio tenga:
- `requirements.txt` actualizado
- `.gitignore` con `.env` excluido

### 2. Crear Secrets en Streamlit Cloud

En la configuración de tu app en Streamlit Cloud, añade estos secretos:

```toml
[mongo]
uri = "mongodb+srv://<usuario>:<password>@<cluster>.mongodb.net/"
db = "BioflocDB"
collection = "SensorReadings"
```

### 3. Desplegar

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Conecta tu repositorio de GitHub
3. Selecciona `Home.py` como archivo principal
4. ¡Deploy!

---

## 📊 Vistas de la Aplicación

### 🏠 Dashboard (Inicio)

Vista principal con tarjetas de dispositivos. Cada tarjeta muestra:
- Estado del dispositivo (Normal/Alerta/Crítico/Offline)
- Últimas lecturas de sensores (hasta 4)
- Botón de **Actualización Parcial** (solo recarga esa tarjeta)
- Acceso directo a gráficas del dispositivo

### 📈 Gráficas

Visualización interactiva de datos históricos:
- Selector de dispositivo y rango de fechas
- Gráficas multi-sensor con Plotly
- Zoom, pan y exportación de imágenes

### 📥 Datos (Historial)

Tabla con historial completo de lecturas:
- Filtros por dispositivo, fecha y sensor
- Paginación de resultados
- **Exportación a Excel y CSV**

### ⚙️ Configuración

Gestión del sistema:
- Umbrales de alerta por sensor (mínimo/máximo)
- Metadatos de dispositivos (alias, ubicación)
- Configuración persistente en MongoDB

---

## 🔧 Características Técnicas

### Actualización Parcial con @fragment

Las tarjetas del dashboard usan el decorador `@fragment` de Streamlit para actualizaciones parciales:

```python
@fragment
def render_live_device_card(device, thresholds, config):
    # Solo esta tarjeta se re-renderiza al hacer clic
    if st.button("Actualizar"):
        # Consulta solo este dispositivo
        fresh_data = db.get_latest_for_single_device(device.device_id)
```

### Conexión Resiliente a MongoDB

El sistema implementa reconexión automática con reintentos:

```python
def get_latest_by_device(self, max_retries=3):
    for attempt in range(max_retries):
        try:
            # Query a MongoDB
        except Exception as e:
            time.sleep(0.5 * (attempt + 1))
```

### Sistema de Caché en Session State

Los datos se cachean en `st.session_state` para evitar consultas innecesarias:

```python
if f"live_data_{device_id}" not in st.session_state:
    st.session_state[f"live_data_{device_id}"] = fetch_from_db()
```

---

## 📝 Changelog

### v2.0.0 (Enero 2025)
- ✅ Nuevo sistema de actualización parcial por dispositivo
- ✅ Botón de refresh integrado en tarjetas del dashboard
- ✅ Generador de datos mock para testing
- ✅ Exportación de datos a Excel/CSV
- ✅ Rediseño visual de tarjetas con iconos SVG
- ✅ Navegación mejorada con iconos Material
- ✅ Soporte para Streamlit Cloud

### v1.0.0 (Diciembre 2024)
- Dashboard inicial con tarjetas de dispositivos
- Gráficas interactivas con Plotly
- Configuración de umbrales
- Conexión a MongoDB Atlas

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

<div align="center">

**Desarrollado con 🦐 por [Marton1123](https://github.com/Marton1123)**

**Escuela de Ingeniería Coquimbo - Universidad Católica del Norte (UCN)**

</div>