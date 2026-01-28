# Manual de Operación - Biofloc Monitor UCN

Este documento describe el funcionamiento y operación de la plataforma de monitoreo Biofloc.

---

## 1. Panel de Control Operativo (Dashboard)

El Dashboard es la interfaz principal para la supervisión en tiempo real de las unidades de cultivo.

### 1.1 Estados de Operación

Cada tarjeta de dispositivo presenta un indicador de color que refleja el estado consolidado de la unidad:

| Estado | Color | Descripción |
|--------|-------|-------------|
| **Normal** | 🟢 Verde | Todos los parámetros dentro de rangos óptimos |
| **Alerta** | 🟡 Amarillo | Parámetros fuera del rango óptimo pero dentro de límites seguros |
| **Crítico** | 🔴 Rojo | Valores fuera de límites de seguridad biológica |
| **Offline** | ⚫ Gris | Sin transmisión de datos por más de 5 minutos |

### 1.2 Tarjetas de Dispositivo

Cada tarjeta muestra:

- **Encabezado**: Nombre del dispositivo, ubicación y estado
- **Sensores**: Hasta 4 lecturas de sensores con sus valores actuales
- **Metadata**: ID técnico y hora de última actualización
- **Botón de Gráficas**: Acceso directo a gráficas del dispositivo (📊)

### 1.3 Actualización Parcial (Nuevo ✨)

Cada tarjeta tiene un botón **"Actualizar"** en la parte inferior que permite:

- Refrescar **solo los datos de ese dispositivo** sin recargar toda la página
- Obtener la lectura más reciente de la base de datos
- Ver cambios instantáneos sin perder el scroll o estado de la página

> **Tip**: Usa el botón "Actualizar Todo" en la barra superior para refrescar todos los dispositivos a la vez.

### 1.4 Filtrado y Búsqueda

La barra de herramientas superior permite filtrar los dispositivos visibles por:
- **Estado**: Mostrar solo unidades en Alerta o Críticas
- **Ubicación**: Filtrar por sector (ej: Laboratorio, Invernadero)
- **Texto**: Búsqueda libre por ID técnico o alias

---

## 2. Análisis de Tendencias (Gráficas)

Módulo para la evaluación visual del comportamiento de parámetros en el tiempo.

### 2.1 Funcionalidades

- **Rango Temporal**: Seleccionar desde la última hora hasta el último mes
- **Comparativa**: Superponer curvas de múltiples dispositivos
- **Estadística Descriptiva**: Tabla con Min, Max, Promedio y Mediana
- **Interactividad**: Zoom, pan y exportación de gráficas como imagen

### 2.2 Uso

1. Selecciona un dispositivo del menú desplegable
2. Define el rango de fechas deseado
3. Elige los sensores a visualizar
4. La gráfica se actualiza automáticamente

---

## 3. Gestión de Datos Históricos (Datos)

Acceso al registro completo de mediciones almacenadas en la base de datos.

### 3.1 Consulta de Datos

- **Filtrado**: Por rango de fechas y dispositivos específicos
- **Tabla Interactiva**: Visualización con paginación
- **Ordenamiento**: Click en columnas para ordenar

### 3.2 Exportación de Datos (Nuevo ✨)

| Formato | Recomendado Para |
|---------|------------------|
| **Excel (.xlsx)** | Reportes, análisis pequeños (<50,000 registros) |
| **CSV** | Backups masivos, procesamiento externo |

**Cómo exportar:**
1. Aplica los filtros deseados
2. Haz clic en el botón de descarga correspondiente
3. El archivo se descargará automáticamente

---

## 4. Configuración del Sistema

Panel administrativo para la gestión de metadatos y parámetros de control.

### 4.1 Gestión de Identidad

Permite asignar nombres amigables a los IDs técnicos:

| Campo | Descripción |
|-------|-------------|
| **ID Técnico** | Identificador único del hardware (inmutable) |
| **Alias** | Nombre operativo visible en el Dashboard |
| **Ubicación** | Sector físico de instalación |

### 4.2 Configuración de Umbrales

El sistema utiliza un modelo de cuatro puntos para definir los estados:

```
[CRÍTICO] ← Mín Crítico ← [ALERTA] ← Mín Óptimo ← [NORMAL] → Máx Óptimo → [ALERTA] → Máx Crítico → [CRÍTICO]
```

1. **Mínimo Crítico**: Límite inferior de seguridad biológica
2. **Mínimo Óptimo**: Inicio del rango ideal de producción
3. **Máximo Óptimo**: Fin del rango ideal de producción
4. **Máximo Crítico**: Límite superior de seguridad biológica

---

## 5. Scripts de Utilidad

El proyecto incluye scripts para tareas especiales en la carpeta `scripts/`:

### 5.1 Generador de Datos Mock

```bash
python scripts/mock_data_generator.py
```

Genera datos de prueba realistas para testing:
- Múltiples dispositivos simulados
- Variaciones naturales en parámetros
- Escenarios de alerta y condiciones críticas

### 5.2 Exportación Directa a Excel

```bash
python scripts/export_to_excel.py
```

Exporta datos directamente desde MongoDB a un archivo Excel local.

---

## 6. Solución de Problemas

### El dispositivo aparece como "Offline"

- Verificar alimentación eléctrica del nodo sensor
- Comprobar conectividad WiFi
- Revisar estado de la antena

### Los datos no se actualizan

1. Hacer clic en "Actualizar" en la tarjeta del dispositivo
2. Si persiste, usar "Actualizar Todo"
3. Verificar conexión a la base de datos

### Errores de conexión a MongoDB

- Verificar que las credenciales en `.env` sean correctas
- Comprobar que la IP esté en la whitelist de MongoDB Atlas
- Revisar el estado del cluster en la consola de Atlas

---

**Desarrollado por**: [Marton1123](https://github.com/Marton1123)  
**Escuela de Ingeniería Coquimbo - Universidad Católica del Norte (UCN)**
