# 🎓 Oracle 19c DBA Exam Simulators

Suite de simuladores web de preparación para las certificaciones oficiales de **Oracle Database 19c**, optimizada para su uso en **PC, Tablet (iPad / Android) y Móvil**, con soporte **100% Offline (PWA)** y sincronización de progreso entre dispositivos.

---

## 📌 Certificaciones Incluidas

1. **Oracle 1Z0-078 — RAC and Grid Infrastructure Administration**
   - **78 preguntas** auditadas y verificadas.
   - Dominios: Real Application Clusters (RAC), Clusterware, Automatic Storage Management (ASM) y ACFS.
   - Acceso: [`/1z0-078/`](1z0-078/index.html).

2. **Oracle 1Z0-083 — Database Administration II (OCP 19c)**
   - **181 preguntas** auditadas y verificadas.
   - Dominios: Multitenant Architecture, Backup & RMAN, Database Upgrade, Performance & Tuning, y Flashback Technologies.
   - Acceso: [`/1z0-083/`](1z0-083/index.html).

---

## 🚀 Características Principales

- **4 Modos de Estudio**:
  - 📖 **Practice / Study Mode**: Evaluación pregunta a pregunta con verificación inmediata, explicaciones técnicas completas y enlaces a la documentación oficial de Oracle 19c.
  - ⏱️ **Real Exam Simulator**: Simulación cronometrada (120 minutos, 60 preguntas en 078 / 68 en 083) con algoritmo de barajado imparcial (*Fisher-Yates*), cálculo de percentil y desglose por dominio.
  - ⚠️ **Weak Questions**: Repaso enfocado exclusivamente en las preguntas falladas o sin racha.
  - 🧠 **Memory Mode**: Memorización activa rápida con respuestas correctas pre-resaltadas.
- **Sistema de Maestría (*Spaced Repetition*)**: Contador de rachas por pregunta con umbral configurable de 1 a 5 aciertos consecutivos.
- **📱 Optimización Tablet & Táctil**:
  - **Gestos de deslizamiento (*Swipe*)**: Pasa a la siguiente o anterior pregunta arrastrando el dedo a izquierda o derecha.
  - **Zonas táctiles ampliadas**: Botones y opciones de respuesta con altura mínima de 48px para pulsación cómoda.
  - **Teclado numérico nativo**: Selector rápido de pregunta con teclado numérico en iPad/Android.
- **💾 Sincronización PC ↔ Tablet**: Exportación e importación de progreso mediante ficheros `.json` unificados.
- **⚡ 100% Offline (PWA)**: *Service Worker* integrado que almacena en caché todas las preguntas y assets para estudiar sin conexión a internet.

---

## 📱 Cómo utilizarlo desde tu Tablet

### Opción A: Despliegue en GitHub Pages (Recomendada - Acceso universal)

Para acceder desde cualquier lugar sin depender de tu PC encendido:

1. **Crea un repositorio en GitHub**:
   - Entra en [github.com](https://github.com) y crea un nuevo repositorio (puede ser público o privado).
2. **Sube el proyecto desde tu terminal**:
   ```bash
   git add .
   git commit -m "OracleDBA Suite 2.0 con soporte Tablet y PWA"
   git remote add origin https://github.com/TU-USUARIO/OracleDBA.git
   git branch -M main
   git push -u origin main
   ```
3. **Activa GitHub Pages**:
   - En tu repositorio de GitHub, ve a **Settings** &rarr; **Pages**.
   - En **Build and deployment** / **Branch**, selecciona `main` y la carpeta `/(root)`. Haz clic en **Save**.
   - En 1 minuto tendrás tu URL activa: `https://TU-USUARIO.github.io/OracleDBA/`.
4. **Instálalo en tu Tablet como App**:
   - **En iPad (Safari)**: Entra a tu URL, pulsa el botón **Compartir** (icono de cuadrado con flecha hacia arriba) y selecciona **"Añadir a pantalla de inicio"**.
   - **En Android (Chrome)**: Entra a tu URL, pulsa en el menú (tres puntos) y elige **"Instalar aplicación"** o **"Añadir a pantalla de inicio"**.
   - *¡Listo! Se abrirá a pantalla completa y funcionará incluso sin cobertura o en modo avión.*

---

### Opción B: Uso en Red Local Wi-Fi (Sin subir nada a internet)

Si prefieres mantener todo en local en tu red doméstica:

1. En tu PC, haz doble clic en `start_server.bat` (o ejecuta `python scripts/server.py`).
2. En la consola verás una línea con la IP de tu PC, por ejemplo:
   ```text
   Acceso TABLET : http://192.168.1.45:8080
   ```
3. Abre el navegador de tu tablet (conectada a la misma Wi-Fi) y escribe esa dirección.

---

## 🔄 Sincronización Automática con GitHub Gist

La suite incluye un backend serverless utilizando **GitHub Gist**. Puedes responder preguntas en tu PC y continuar en tu Tablet sin necesidad de enviar archivos manualmente ni crear bases de datos externas:

### Paso 1: Obtener tu Token de GitHub (PAT)
1. Inicia sesión en [GitHub](https://github.com/) y dirígete a:  
   👉 **Settings** &rarr; **Developer Settings** &rarr; **Personal Access Tokens** &rarr; **Tokens (classic)**  
   *(o accede a [github.com/settings/tokens](https://github.com/settings/tokens))*.
2. Haz clic en **Generate new token (classic)**.
3. Dale una descripción (ej. `OracleDBA Sync`) y marca únicamente la casilla:
   - [x] **`gist`** *(Create gists)*.
4. Genera el token y copia el valor resultante (`ghp_...`).

### Paso 2: Conectar en tu PC
1. Abre el simulador en tu PC y haz clic en el botón **"☁️ Conectar Gist"** en la cabecera.
2. Pega tu Token en el campo correspondiente (deja el campo *Gist ID* vacío).
3. Haz clic en **"Guardar y Sincronizar"**.
4. La aplicación creará automáticamente un Gist secreto y te mostrará el **Gist ID generado** (ej. `a1b2c3d4e5f6...`).

### Paso 3: Conectar en tu Tablet
1. Abre la aplicación en tu Tablet y pulsa en **"☁️ Conectar Gist"**.
2. Pega tu **mismo Token** y el **Gist ID** obtenido en el paso anterior.
3. Pulsa **"Guardar y Sincronizar"**.
4. ¡Listo! A partir de ese momento:
   - Cada vez que respondas una pregunta, el progreso se guardará automáticamente en el Gist tras unos segundos de inactividad.
   - Cada vez que abras la app en cualquier dispositivo, se descargará y fusionará (*merge inteligente*) el progreso más reciente sin sobrescribir preguntas contestadas en el otro equipo.

---

### Método Alternativo: Copia de Seguridad Manual (JSON)

Si no deseas utilizar GitHub Gist o no tienes conexión:
1. Pulsa **"💾 Exportar"** para descargar el fichero `OracleDBA_GlobalBackup_YYYY-MM-DD.json`.
2. Envíalo a tu tablet y pulsa **"📥 Importar"** para restaurarlo.

---

## 🗂️ Estructura del Proyecto

```
OracleDBA/
├── index.html                   # Portal principal con Dashboard y sincronización
├── manifest.webmanifest         # Manifiesto PWA para instalación en tablets/móviles
├── sw.js                        # Service Worker para funcionamiento 100% offline
├── start_server.bat             # Lanzador rápido de servidor local para red Wi-Fi
├── README.md                    # Documentación del proyecto
├── .gitignore                   # Exclusiones de Git
│
├── 1z0-078/                     # Módulo para Oracle RAC & Grid
│   ├── index.html               # Simulador modular 1Z0-078
│   └── 1z0-078.html             # Redirección de compatibilidad
│
├── 1z0-083/                     # Módulo para Oracle Database Admin II
│   ├── index.html               # Simulador modular 1Z0-083
│   └── 1z0-083.html             # Redirección de compatibilidad
│
├── assets/
│   ├── css/
│   │   └── simulator.css        # Hoja de estilos unificada y responsive
│   ├── js/
│   │   └── simulator-core.js    # Motor lógico, barajado Fisher-Yates y eventos táctiles
│   └── icons/
│       ├── icon.svg             # Icono vectorial escalable
│       ├── icon-192.png         # Icono PWA para pantalla de inicio
│       └── icon-512.png         # Icono PWA alta resolución
│
├── data/
│   ├── 1z0-078.json             # Banco de 78 preguntas desacoplado
│   └── 1z0-083.json             # Banco de 181 preguntas desacoplado
│
├── scripts/
│   ├── server.py                # Servidor HTTP local con detección de IP para tablet
│   ├── validate_questions.py    # Validador de esquemas e integridad del banco
│   ├── generate_icons.py        # Generador de iconos PWA PNG
│   └── extract_questions.py     # Utilidad de extracción de datos
│
└── archive/                     # Respaldo seguro de los ficheros monolíticos originales
    ├── 1z0-078-legacy.html
    └── 1z0-083-legacy.html
```

---

## 🧪 Validación y Mantenimiento

Para comprobar la consistencia de los datos en cualquier momento (preguntas, opciones, claves correctas y dominios), ejecuta:

```bash
python scripts/validate_questions.py
```
Este script audita automáticamente que no existan IDs duplicados, que todas las respuestas tengan coincidencia en sus opciones y que los tipos de selección sean coherentes.
