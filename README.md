# 🌿 Dashboard MicroAlgas UCN

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.36+-red?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green?logo=mongodb&logoColor=white)](https://www.mongodb.com/cloud/atlas)

**Sistema de monitoreo IoT para cultivos de Microalgas con dashboard web en tiempo real**

[Demo en Vivo](#) · [Documentación](docs/MANUAL_USUARIO.md) · [Reportar Bug](https://github.com/Menderin/Dashboard-MicroAlgas-/issues)

---

## 📋 Descripción

Plataforma web para la supervisión remota de parámetros fisicoquímicos críticos (pH, oxígeno disuelto, temperatura, entre otros) en sistemas de cultivo de microalgas. El sistema procesa datos de telemetría provenientes de múltiples nodos sensores IoT almacenados en MongoDB Atlas, con acceso protegido por contraseña.

### ✨ Funcionalidades Principales

| Función | Descripción |
|---|---|
| **🔒 Autenticación** | Acceso protegido por contraseña configurable vía variable de entorno |
| **📊 Dashboard en Tiempo Real** | Visualización del estado de cada dispositivo con actualizaciones parciales por tarjeta |
| **🚦 Sistema de Alertas** | Semaforización automática (Normal / Alerta / Crítico) basada en umbrales configurables |
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
Dashboard-MicroAlgas-/
├── home.py                    # Punto de entrada, autenticación y navegación
├── requirements.txt           # Dependencias del proyecto
├── .env                       # Variables de entorno (NO incluir en git)
├── .streamlit/
│   └── secrets.toml           # Secretos para Streamlit Cloud
│
├── views/                     # Vistas de la aplicación
│   ├── dashboard.py           # Dashboard principal con tarjetas por dispositivo
│   ├── graphs.py              # Gráficas interactivas de parámetros
│   ├── history.py             # Historial y exportación de datos
│   └── settings.py            # Configuración de sensores y dispositivos
│
├── modules/                   # Lógica de negocio
│   ├── database.py            # Conexión y queries a MongoDB
│   ├── device_manager.py      # Evaluación de estado de dispositivos
│   ├── config_manager.py      # Gestión de configuración
│   ├── sensor_registry.py     # Registro de sensores detectados
│   └── styles.py              # Estilos CSS globales
│
├── scripts/
│   └── mock_data_generator.py # Generador de datos de prueba
│
├── config/
│   └── sensor_defaults.json   # Valores por defecto de sensores
│
├── assets/                    # Recursos estáticos (logos, imágenes)
│
└── docs/
    └── MANUAL_USUARIO.md
```

---

## 🚀 Instalación Local

### Prerrequisitos

- [Anaconda](https://www.anaconda.com/download) o Python 3.10+
- Cuenta en [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) (plan gratuito disponible)

### 1. Clonar el Repositorio

```bash
git clone https://github.com/Menderin/Dashboard-MicroAlgas-.git
cd Dashboard-MicroAlgas-
```

### 2. Crear Entorno Virtual

```bash
conda create --name microalgas_env python=3.10 -y
conda activate microalgas_env
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
MONGO_URI=mongodb+srv://<usuario>:<password>@<cluster>.mongodb.net/
MONGO_DB=MicroalgasDB
MONGO_COLLECTION=SensorReadings
SITE_PASSWORD=tu_contraseña_aqui
```

> ⚠️ **Importante:** Nunca subas el archivo `.env` al repositorio. Ya está incluido en `.gitignore`.

### 5. Ejecutar la Aplicación

```bash
streamlit run home.py
```

Accede a `http://localhost:8501` en tu navegador e ingresa la contraseña configurada en `SITE_PASSWORD`.

---

## 🧪 Generar Datos de Prueba

El proyecto incluye un generador de datos mock para testing sin hardware físico:

```bash
python scripts/mock_data_generator.py
```

El generador:
- Crea lecturas para múltiples dispositivos simulados
- Incluye variaciones realistas en los parámetros (pH, temperatura, OD, etc.)
- Simula escenarios de alerta y condiciones críticas
- Inserta los datos directamente en MongoDB Atlas

---

## ☁️ Deploy en Streamlit Cloud

### 1. Preparar el Repositorio

Asegúrate de que tu repositorio tenga:
- `requirements.txt` actualizado
- `.gitignore` con `.env` excluido

### 2. Configurar Secrets en Streamlit Cloud

En la configuración de tu app en [share.streamlit.io](https://share.streamlit.io), añade:

```toml
[mongo]
uri = "mongodb+srv://<usuario>:<password>@<cluster>.mongodb.net/"
db = "MicroalgasDB"
collection = "SensorReadings"

SITE_PASSWORD = "tu_contraseña_aqui"
```

### 3. Desplegar

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Conecta tu repositorio de GitHub
3. Selecciona `home.py` como archivo principal
4. Añade los secrets y haz clic en **Deploy**

---

## 📊 Vistas de la Aplicación

### 🔒 Login
Pantalla de acceso con contraseña. El fondo con gradiente verde y diseño tipo glassmorphism identifica visualmente el sistema de microalgas.

### 🏠 Dashboard (Inicio)
Vista principal con tarjetas por dispositivo. Cada tarjeta muestra:
- Estado del dispositivo (Normal / Alerta / Crítico / Offline)
- Últimas lecturas de los sensores
- Botón de **Actualización Parcial** (solo recarga esa tarjeta)
- Acceso directo a las gráficas de ese dispositivo

### 📈 Gráficas
Visualización interactiva de datos históricos:
- Selector de dispositivo y rango de fechas
- Gráficas multi-sensor con Plotly
- Zoom, pan y exportación de imágenes PNG

### 📥 Datos (Historial)
Tabla con historial completo de lecturas:
- Filtros por dispositivo, fecha y tipo de sensor
- Paginación de resultados
- Exportación a Excel y CSV

### ⚙️ Configuración
Gestión del sistema:
- Umbrales de alerta por sensor (mínimo / máximo)
- Metadatos de dispositivos (alias, ubicación)
- Configuración persistente en MongoDB

---



**Desarrollado por [Menderin](https://github.com/Menderin) 🌿**

*Escuela de Ingeniería Coquimbo — Universidad Católica del Norte (UCN)*
