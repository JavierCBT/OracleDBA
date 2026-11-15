# 🎓 Oracle 19c DBA Exam Simulators

Web-based exam preparation suite for official **Oracle Database 19c** certifications, optimized for **PC, Tablet (iPad / Android), and Mobile**, featuring **100% Offline support (PWA)** and cross-device progress synchronization via **GitHub Gist**.

---

## 📌 Included Certifications

1. **Oracle 1Z0-078 — RAC and Grid Infrastructure Administration**
   - **78 questions** audited and verified.
   - Domains: Real Application Clusters (RAC), Clusterware, Automatic Storage Management (ASM), and ACFS.
   - URL: [`/1z0-078/`](1z0-078/index.html).

2. **Oracle 1Z0-083 — Database Administration II (OCP 19c)**
   - **181 questions** audited and verified.
   - Domains: Multitenant Architecture, Backup & RMAN, Database Upgrade, Performance & Tuning, and Flashback Technologies.
   - URL: [`/1z0-083/`](1z0-083/index.html).

---

## 🚀 Key Features

- **4 Study Modes**:
  - 📖 **Practice / Study Mode**: Question-by-question evaluation with instant feedback, comprehensive technical explanations, and direct links to official Oracle 19c documentation.
  - ⏱️ **Real Exam Simulator**: Timed simulation (120 minutes, 60 questions for 078 / 68 questions for 083) using the unbiased **Fisher-Yates shuffle algorithm**, score breakdown, and domain percentile analytics.
  - ⚠️ **Weak Questions**: Targeted review mode focused exclusively on failed questions or questions with no streak.
  - 🧠 **Memory Mode**: Fast active-recall mode with correct options pre-highlighted and incorrect choices dimmed.
- **Spaced Repetition & Mastery**: Question-level streak tracking with a configurable mastery threshold (1 to 5 consecutive correct answers).
- **📱 Tablet & Touch Optimization**:
  - **Swipe Gestures**: Swipe left or right anywhere on screen to smoothly navigate between questions.
  - **Enlarged Touch Targets**: Answer options and action buttons feature a minimum touch height of 48px to prevent accidental taps.
  - **Native Numeric Keypad**: "Jump to #" inputs invoke the native numeric keypad on iOS and Android.
- **☁️ Automatic GitHub Gist Sync**: Seamless two-way cloud synchronization between PC and Tablet with smart merging.
- **⚡ 100% Offline (PWA)**: Integrated Service Worker that caches all static assets and question banks for offline study anywhere.

---

## 📱 How to Use on Your Tablet

### Option A: GitHub Pages (Recommended — Universal Cloud Access)

Access your exam simulators from anywhere without keeping your PC powered on:

1. **Push the project to GitHub**:
   ```bash
   git add .
   git commit -m "Update OracleDBA exam suite"
   git push origin main
   ```
2. **Enable GitHub Pages**:
   - Go to your repository on GitHub: **Settings** &rarr; **Pages**.
   - Under **Build and deployment** / **Branch**, select `main` and the root folder `/(root)`. Click **Save**.
   - Within 1–2 minutes, your site will be live at: `https://<YOUR_GITHUB_USERNAME>.github.io/OracleDBA/`.
3. **Install as a PWA App on your Tablet**:
   - **On iPad (Safari)**: Open your GitHub Pages URL, tap the **Share** button (box with upward arrow), and select **"Add to Home Screen"**.
   - **On Android (Chrome)**: Open your URL, tap the menu (three dots), and select **"Install app"** or **"Add to Home screen"**.
   - *The simulator will launch as a full-screen, standalone app that functions completely offline.*

---

### Option B: Local Wi-Fi Network (Without Cloud Hosting)

To study locally across your home network:

1. On your PC, double-click `start_server.bat` (or run `python scripts/server.py`).
2. The terminal displays your local network address, for example:
   ```text
   Access from TABLET: http://192.168.1.45:8080
   ```
3. Open your tablet's browser (connected to the same Wi-Fi) and navigate to that address.

---

## 🔄 Automatic Cloud Sync with GitHub Gist

The suite includes a serverless cloud backend powered by **GitHub Gist**. You can answer questions on your PC and continue seamlessly on your Tablet without manual file transfers:

### Step 1: Create your GitHub Personal Access Token (PAT)
1. Sign in to [GitHub](https://github.com/) and navigate to:  
   👉 **Settings** &rarr; **Developer Settings** &rarr; **Personal Access Tokens** &rarr; **Tokens (classic)**  
   *(or directly visit [github.com/settings/tokens](https://github.com/settings/tokens))*.
2. Click **Generate new token (classic)**.
3. Set a Note (e.g. `OracleDBA Sync`) and check only the following scope:
   - [x] **`gist`** *(Create gists)*.
4. Generate and copy your token (`ghp_...`).

### Step 2: Connect on your PC
1. Open the simulator on your PC and click the **"☁️ Connect Gist"** button in the header.
2. Paste your Token into the field (leave the *Gist ID* field empty).
3. Click **"Save & Sync"**.
4. The application automatically creates a secret Gist and displays your new **Gist ID** (e.g. `4f8a12bc90...`).

### Step 3: Connect on your Tablet
1. Open the application on your Tablet and tap **"☁️ Connect Gist"**.
2. Paste the **same Token** and the **Gist ID** generated in Step 2.
3. Tap **"Save & Sync"**.
4. *Done! From now on:*
   - Answering questions triggers an automatic, debounced background sync to the Gist.
   - Opening the application on any device automatically downloads and merges the latest progress without overwriting unreviewed questions.

---

### Alternative Method: Manual Backup & Restore (JSON)

If you prefer offline file backups:
1. Click **"💾 Export"** to download `OracleDBA_GlobalBackup_YYYY-MM-DD.json`.
2. Transfer the file to your tablet and click **"📥 Import"** to restore all progress.

---

## 🗂️ Project Structure

```
OracleDBA/
├── index.html                   # Central certification dashboard & sync controls
├── manifest.webmanifest         # PWA Web App Manifest for mobile/tablet install
├── sw.js                        # Service Worker for 100% offline caching
├── start_server.bat             # Quick launcher for local Wi-Fi server
├── README.md                    # Project documentation
├── .gitignore                   # Git exclusion rules
│
├── 1z0-078/                     # Oracle RAC & Grid Module
│   ├── index.html               # Modular 1Z0-078 simulator
│   └── 1z0-078.html             # Legacy redirector
│
├── 1z0-083/                     # Oracle Database Admin II Module
│   ├── index.html               # Modular 1Z0-083 simulator
│   └── 1z0-083.html             # Legacy redirector
│
├── assets/
│   ├── css/
│   │   └── simulator.css        # Unified responsive stylesheet (dark theme)
│   ├── js/
│   │   ├── simulator-core.js    # Core exam engine, Fisher-Yates shuffle & touch swipe
│   │   └── gist-sync.js         # GitHub Gist two-way cloud sync service
│   └── icons/
│       ├── icon.svg             # Scalable vector icon
│       ├── icon-192.png         # PWA home screen icon
│       └── icon-512.png         # High-resolution splash icon
│
├── data/
│   ├── 1z0-078.json             # 78 verified questions dataset
│   └── 1z0-083.json             # 181 verified questions dataset
│
├── scripts/
│   ├── server.py                # Local HTTP server with automatic IP detection
│   ├── validate_questions.py    # Automated dataset schema and integrity auditor
│   ├── generate_icons.py        # PWA bitmap icon generator
│   └── extract_questions.py     # Question extraction utility
│
└── archive/                     # Safe backup of original monolithic legacy files
    ├── 1z0-078-legacy.html
    └── 1z0-083-legacy.html
```

---

## 🧪 Dataset Validation & Maintenance

To verify dataset integrity (questions, choices, correct keys, domains, and explanations) at any time, run:

```bash
python scripts/validate_questions.py
```

The script audits both question banks and guarantees zero duplicate IDs, complete choice coverage, and schema conformity.
