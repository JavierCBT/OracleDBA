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

## 🔄 Cómo sincronizar tu progreso entre PC y Tablet

El progreso de estudio (rachas, preguntas dominadas y precisión) se almacena en el navegador (`localStorage`). Para transferirlo:

1. **En tu PC**: En la página principal ([`index.html`](index.html)), pulsa el botón **"💾 Exportar Progreso Global"**. Se descargará un fichero llamado `OracleDBA_GlobalBackup_YYYY-MM-DD.json`.
2. **Envía el archivo a tu Tablet** (por AirDrop, Telegram, WhatsApp, Google Drive o correo).
3. **En tu Tablet**: Abre la aplicación, pulsa **"📥 Importar Progreso"** y selecciona el archivo `.json`.
4. ¡Tus rachas y estadísticas se actualizarán automáticamente en la tablet!

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
