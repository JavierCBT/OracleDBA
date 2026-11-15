/**
 * OracleDBA - GitHub Gist Automatic Sync Service
 * Seamless two-way cloud synchronization for PC, Tablet and Mobile
 * Uses GitHub REST API v3 to read and write a secret Gist containing study stats.
 */

(function (global) {
  'use strict';

  const GIST_FILENAME = 'oracledba_sync.json';
  const STORAGE_KEYS = {
    token: 'oracle_dba_gist_token',
    gistId: 'oracle_dba_gist_id',
    lastSync: 'oracle_dba_gist_last_sync',
    deviceId: 'oracle_dba_device_id'
  };

  let debounceTimer = null;
  let isSyncing = false;

  // Generate or get unique device ID
  function getDeviceId() {
    let id = localStorage.getItem(STORAGE_KEYS.deviceId);
    if (!id) {
      id = 'dev_' + Math.random().toString(36).substring(2, 9) + '_' + Date.now().toString(36);
      localStorage.setItem(STORAGE_KEYS.deviceId, id);
    }
    return id;
  }

  function getConfig() {
    return {
      token: (localStorage.getItem(STORAGE_KEYS.token) || '').trim(),
      gistId: (localStorage.getItem(STORAGE_KEYS.gistId) || '').trim(),
      lastSync: localStorage.getItem(STORAGE_KEYS.lastSync) || null,
      deviceId: getDeviceId()
    };
  }

  function isConfigured() {
    const cfg = getConfig();
    return Boolean(cfg.token && cfg.gistId);
  }

  // Update visual status pill across any page
  function updateStatusUI(status, message) {
    const pills = document.querySelectorAll('.gist-sync-status');
    pills.forEach(pill => {
      pill.className = `gist-sync-status status-${status}`;
      if (status === 'synced') {
        pill.innerHTML = `☁️ <span class="sync-text">Gist: Sincronizado</span>`;
        pill.title = message || 'Progreso sincronizado en GitHub Gist';
      } else if (status === 'syncing') {
        pill.innerHTML = `⏳ <span class="sync-text">Sincronizando...</span>`;
        pill.title = 'Guardando cambios en GitHub Gist...';
      } else if (status === 'error') {
        pill.innerHTML = `⚠️ <span class="sync-text">Error Gist</span>`;
        pill.title = message || 'Error al conectar con GitHub Gist. Clic para configurar.';
      } else {
        pill.innerHTML = `☁️ <span class="sync-text">Conectar Gist</span>`;
        pill.title = 'Configura tu GitHub Token para sincronización automática';
      }
    });
  }

  // Gather all local exam stats into a bundle
  function getLocalPayload() {
    const stats78 = JSON.parse(localStorage.getItem('oracle_dba_stats_1z0-078') || localStorage.getItem('1z0_078_stats_v2') || '{}');
    const th78 = parseInt(localStorage.getItem('oracle_dba_threshold_1z0-078') || localStorage.getItem('1z0_078_threshold_v2') || '3', 10);

    const stats83 = JSON.parse(localStorage.getItem('oracle_dba_stats_1z0-083') || localStorage.getItem('1z0_stats_en') || '{}');
    const th83 = parseInt(localStorage.getItem('oracle_dba_threshold_1z0-083') || localStorage.getItem('1z0_threshold_en') || '3', 10);

    return {
      version: '2.0',
      updatedAt: new Date().toISOString(),
      updatedBy: getDeviceId(),
      exams: {
        '1z0-078': {
          stats: stats78,
          threshold: th78,
          updatedAt: new Date().toISOString()
        },
        '1z0-083': {
          stats: stats83,
          threshold: th83,
          updatedAt: new Date().toISOString()
        }
      }
    };
  }

  // Intelligent merge: combine local and remote data without data loss
  function mergeExamStats(localStats, remoteStats) {
    const merged = Object.assign({}, localStats);

    Object.keys(remoteStats || {}).forEach(qid => {
      const r = remoteStats[qid];
      const l = merged[qid];

      if (!l) {
        merged[qid] = r;
      } else {
        merged[qid] = {
          streak: Math.max(l.streak || 0, r.streak || 0),
          correct: Math.max(l.correct || 0, r.correct || 0),
          wrong: Math.max(l.wrong || 0, r.wrong || 0),
          mastered: Boolean(l.mastered || r.mastered)
        };
      }
    });

    return merged;
  }

  function applyRemoteData(remotePayload) {
    if (!remotePayload || !remotePayload.exams) return false;

    let modified = false;

    // Merge 1Z0-078
    if (remotePayload.exams['1z0-078']) {
      const remote78 = remotePayload.exams['1z0-078'];
      const local78 = JSON.parse(localStorage.getItem('oracle_dba_stats_1z0-078') || localStorage.getItem('1z0_078_stats_v2') || '{}');
      const merged78 = mergeExamStats(local78, remote78.stats || {});

      localStorage.setItem('oracle_dba_stats_1z0-078', JSON.stringify(merged78));
      if (remote78.threshold) {
        localStorage.setItem('oracle_dba_threshold_1z0-078', remote78.threshold);
      }
      modified = true;
    }

    // Merge 1Z0-083
    if (remotePayload.exams['1z0-083']) {
      const remote83 = remotePayload.exams['1z0-083'];
      const local83 = JSON.parse(localStorage.getItem('oracle_dba_stats_1z0-083') || localStorage.getItem('1z0_stats_en') || '{}');
      const merged83 = mergeExamStats(local83, remote83.stats || {});

      localStorage.setItem('oracle_dba_stats_1z0-083', JSON.stringify(merged83));
      if (remote83.threshold) {
        localStorage.setItem('oracle_dba_threshold_1z0-083', remote83.threshold);
      }
      modified = true;
    }

    return modified;
  }

  // GitHub REST API: Fetch remote Gist
  async function fetchGist(token, gistId) {
    const res = await fetch(`https://api.github.com/gists/${gistId}`, {
      headers: {
        'Accept': 'application/vnd.github+json',
        'Authorization': `Bearer ${token}`,
        'X-GitHub-Api-Version': '2022-11-28'
      }
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.message || `Error HTTP ${res.status}`);
    }

    const gist = await res.json();
    const file = gist.files && gist.files[GIST_FILENAME];
    if (!file) return null;

    try {
      return JSON.parse(file.content);
    } catch (e) {
      console.warn('Gist content parse error:', e);
      return null;
    }
  }

  // GitHub REST API: Update remote Gist
  async function updateGist(token, gistId, payload) {
    const body = {
      description: 'Oracle 19c DBA Exam Progress Sync',
      files: {
        [GIST_FILENAME]: {
          content: JSON.stringify(payload, null, 2)
        }
      }
    };

    const res = await fetch(`https://api.github.com/gists/${gistId}`, {
      method: 'PATCH',
      headers: {
        'Accept': 'application/vnd.github+json',
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        'X-GitHub-Api-Version': '2022-11-28'
      },
      body: JSON.stringify(body)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.message || `Error HTTP ${res.status}`);
    }

    return await res.json();
  }

  // GitHub REST API: Create secret Gist if not exists
  async function createGist(token, initialPayload) {
    const body = {
      description: 'Oracle 19c DBA Exam Progress Sync',
      public: false,
      files: {
        [GIST_FILENAME]: {
          content: JSON.stringify(initialPayload, null, 2)
        }
      }
    };

    const res = await fetch('https://api.github.com/gists', {
      method: 'POST',
      headers: {
        'Accept': 'application/vnd.github+json',
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        'X-GitHub-Api-Version': '2022-11-28'
      },
      body: JSON.stringify(body)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.message || `Error HTTP ${res.status}`);
    }

    const data = await res.json();
    return data.id;
  }

  // Full two-way synchronize: Pull, Merge, and Push back
  async function syncNow(notify = false) {
    if (!isConfigured()) {
      updateStatusUI('unconfigured');
      return;
    }

    if (isSyncing) return;
    isSyncing = true;
    updateStatusUI('syncing');

    const cfg = getConfig();

    try {
      // 1. Pull remote data
      const remoteData = await fetchGist(cfg.token, cfg.gistId);

      // 2. Apply & merge with local
      if (remoteData) {
        const changed = applyRemoteData(remoteData);
        if (changed) {
          // Trigger page UI refresh if OracleApp exists
          if (global.OracleApp && typeof global.OracleApp.onSearch === 'function') {
            global.OracleApp.onSearch();
          }
          if (typeof global.loadDashboardStats === 'function') {
            global.loadDashboardStats();
          }
        }
      }

      // 3. Prepare merged payload and push back to Gist
      const mergedPayload = getLocalPayload();
      await updateGist(cfg.token, cfg.gistId, mergedPayload);

      const now = new Date().toISOString();
      localStorage.setItem(STORAGE_KEYS.lastSync, now);
      updateStatusUI('synced', `Última sincronización: ${new Date().toLocaleTimeString()}`);

      if (notify) {
        alert('✅ ¡Sincronización completada con éxito!');
      }
    } catch (err) {
      console.error('Gist sync failed:', err);
      updateStatusUI('error', err.message);
      if (notify) {
        alert('❌ Error durante la sincronización: ' + err.message);
      }
    } finally {
      isSyncing = false;
    }
  }

  // Debounced auto-save (called after user answers questions)
  function triggerDebouncedSync() {
    if (!isConfigured()) return;
    updateStatusUI('syncing');
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      syncNow(false);
    }, 2500); // 2.5s debounce to batch consecutive questions
  }

  // Configuration modal helpers
  function openConfigModal() {
    let modal = document.getElementById('gist-modal');
    if (!modal) {
      createConfigModalDOM();
      modal = document.getElementById('gist-modal');
    }

    const cfg = getConfig();
    document.getElementById('gist-token-input').value = cfg.token;
    document.getElementById('gist-id-input').value = cfg.gistId;

    const lastSyncEl = document.getElementById('gist-last-sync-text');
    if (lastSyncEl) {
      lastSyncEl.innerText = cfg.lastSync ? new Date(cfg.lastSync).toLocaleString() : 'Nunca';
    }

    modal.classList.add('active');
  }

  function closeConfigModal() {
    const modal = document.getElementById('gist-modal');
    if (modal) modal.classList.remove('active');
  }

  async function saveConfiguration() {
    const token = (document.getElementById('gist-token-input').value || '').trim();
    let gistId = (document.getElementById('gist-id-input').value || '').trim();

    if (!token) {
      alert('Por favor introduce tu GitHub Personal Access Token.');
      return;
    }

    const saveBtn = document.getElementById('btn-save-gist');
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.innerText = 'Conectando con GitHub...';
    }

    try {
      if (!gistId) {
        // Auto-create secret Gist
        const initialPayload = getLocalPayload();
        gistId = await createGist(token, initialPayload);
        document.getElementById('gist-id-input').value = gistId;
      } else {
        // Validate access
        await fetchGist(token, gistId);
      }

      localStorage.setItem(STORAGE_KEYS.token, token);
      localStorage.setItem(STORAGE_KEYS.gistId, gistId);

      alert(`✅ ¡Conexión con GitHub Gist exitosa!\n\nID del Gist: ${gistId}\n\nUsa este mismo ID y Token en tu Tablet para sincronizar.`);
      closeConfigModal();
      syncNow(true);
    } catch (err) {
      alert('❌ Error al conectar con GitHub Gist: ' + err.message);
    } finally {
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.innerText = 'Guardar y Sincronizar';
      }
    }
  }

  function disconnect() {
    if (confirm('¿Deseas desconectar la sincronización de GitHub Gist en este dispositivo? (Tu progreso local no se borrará)')) {
      localStorage.removeItem(STORAGE_KEYS.token);
      localStorage.removeItem(STORAGE_KEYS.gistId);
      localStorage.removeItem(STORAGE_KEYS.lastSync);
      updateStatusUI('unconfigured');
      closeConfigModal();
      alert('GitHub Gist desconectado.');
    }
  }

  function createConfigModalDOM() {
    const div = document.createElement('div');
    div.id = 'gist-modal';
    div.className = 'modal';
    div.innerHTML = `
      <div class="modal-content" style="max-width:540px;">
        <h3>☁️ Sincronización Automática con GitHub Gist</h3>
        <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:16px;">
          Sincroniza tus estadísticas, preguntas falladas y rachas automáticamente entre tu PC y tu Tablet utilizando un <strong>Gist secreto</strong> personal en tu cuenta de GitHub.
        </p>

        <div style="background:#0b1120; border:1px solid var(--border); border-radius:8px; padding:14px; margin-bottom:16px; font-size:0.82rem; line-height:1.6; color:#94a3b8;">
          <strong style="color:var(--accent);">¿Cómo obtener tu Token de GitHub?</strong><br>
          1. Ve a GitHub &rarr; <strong>Settings</strong> &rarr; <strong>Developer settings</strong> &rarr; <strong>Personal access tokens (classic)</strong>.<br>
          2. Genera un nuevo token con solo el permiso <code>gist</code> marcado.<br>
          3. Pega el token generado a continuación. Si es la primera vez, el Gist se creará automáticamente.
        </div>

        <div style="display:flex; flex-direction:column; gap:12px;">
          <div>
            <label style="font-size:0.85rem; font-weight:600; display:block; margin-bottom:4px;">GitHub Personal Access Token (PAT):</label>
            <input type="password" id="gist-token-input" placeholder="ghp_xxxxxxxxxxxxxxxxxxxx" style="width:100%; background:#0b1120; border:1px solid var(--border); color:#fff; padding:10px 12px; border-radius:6px; font-family:var(--font-mono); font-size:0.85rem;">
          </div>

          <div>
            <label style="font-size:0.85rem; font-weight:600; display:block; margin-bottom:4px;">Gist ID (Opcional en la primera configuración):</label>
            <input type="text" id="gist-id-input" placeholder="Déjalo vacío para crear uno nuevo automáticamente" style="width:100%; background:#0b1120; border:1px solid var(--border); color:#fff; padding:10px 12px; border-radius:6px; font-family:var(--font-mono); font-size:0.85rem;">
            <small style="font-size:0.75rem; color:var(--text-muted);">Para enlazar tu Tablet, copia y pega aquí el Gist ID creado en tu PC.</small>
          </div>

          <div style="font-size:0.8rem; color:var(--text-muted); margin-top:4px;">
            Última sincronización: <strong id="gist-last-sync-text" style="color:var(--text-main);">-</strong>
          </div>
        </div>

        <div class="modal-actions" style="margin-top:24px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
          <button style="border-color:var(--error); color:var(--error); background:none;" onclick="GistSync.disconnect()">Desconectar</button>
          <div style="display:flex; gap:8px;">
            <button onclick="GistSync.closeModal()">Cerrar</button>
            <button class="primary" id="btn-save-gist" onclick="GistSync.saveConfiguration()">Guardar y Sincronizar</button>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(div);
  }

  // Auto-init on page load
  window.addEventListener('DOMContentLoaded', () => {
    createConfigModalDOM();
    if (isConfigured()) {
      updateStatusUI('synced');
      // Background pull on startup
      syncNow(false);
    } else {
      updateStatusUI('unconfigured');
    }
  });

  // Public API
  global.GistSync = {
    syncNow: () => syncNow(true),
    triggerDebouncedSync: triggerDebouncedSync,
    openModal: openConfigModal,
    closeModal: closeConfigModal,
    saveConfiguration: saveConfiguration,
    disconnect: disconnect,
    isConfigured: isConfigured
  };

})(window);
