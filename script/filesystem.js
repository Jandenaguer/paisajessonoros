"use strict";

// File System Access API helper to store a single CSV in a local folder.
// This uses IndexedDB to persist the directory handle across sessions.
//
// IMPORTANT: Browsers revoke readwrite permission when closed. On the next
// session the stored handle still exists in IndexedDB but needs the user to
// re-grant permission via a click (user gesture). The setup button handles
// this: if a handle already exists it calls requestPermission() instead of
// opening the directory picker again.

const CSV_FILENAME = 'paisajes_sonoros.csv';
const DB_NAME = 'paisajes_csv_fs';
const STORE_NAME = 'handles';
const DIR_KEY = 'csv_dir';

// ── IndexedDB helpers ────────────────────────────────────────────────────────

function openDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'key' });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function putHandle(key, value) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    tx.objectStore(STORE_NAME).put({ key, value });
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
}

async function getHandle(key) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const req = tx.objectStore(STORE_NAME).get(key);
    req.onsuccess = () => resolve(req.result ? req.result.value : null);
    req.onerror = () => reject(req.error);
  });
}

// ── Permission helper ────────────────────────────────────────────────────────

// Checks current permission state WITHOUT prompting (safe to call on load).
async function queryPermission(handle) {
  try {
    return await handle.queryPermission({ mode: 'readwrite' });
  } catch (e) {
    return 'denied';
  }
}

// Requests permission WITH a user gesture (must be called from a click handler).
async function requestPermission(handle) {
  try {
    return await handle.requestPermission({ mode: 'readwrite' });
  } catch (e) {
    return 'denied';
  }
}

// ── Public: setup button ─────────────────────────────────────────────────────

window.setupCsvDirectory = async function () {
  const statusEl = document.getElementById('setup_csv_status');
  const setStatus = (msg, color) => {
    if (statusEl) { statusEl.textContent = msg; statusEl.style.color = color; }
  };

  if (typeof window.showDirectoryPicker !== 'function') {
    setStatus('Su navegador no permite elegir carpeta (use Chrome o Edge en ordenador). El CSV se descargará automáticamente al finalizar.', '#f39c12');
    return;
  }

  // If we already have a stored handle, try to re-grant permission (no picker needed).
  const existing = await getHandle(DIR_KEY);
  if (existing) {
    const state = await requestPermission(existing); // requires user gesture ✓
    if (state === 'granted') {
      window._dirHandle = existing;
      setStatus('Carpeta CSV autorizada ✓', '#2ecc71');
      return;
    }
    // Permission denied or failed — fall through to show the picker
  }

  // No handle yet (or permission permanently denied) → let user pick a folder.
  try {
    const dirHandle = await window.showDirectoryPicker({ mode: 'readwrite' });
    if (!dirHandle) return;
    await putHandle(DIR_KEY, dirHandle);
    window._dirHandle = dirHandle;
    setStatus('Carpeta CSV configurada ✓', '#2ecc71');
  } catch (e) {
    if (e && e.name === 'AbortError') return;
    console.error('Error configurando carpeta CSV', e);
    setStatus('No se pudo configurar la carpeta. El CSV se descargará al finalizar.', '#f39c12');
  }
};

// ── On load: check silently (no prompt) ─────────────────────────────────────

async function loadConfiguredDirectory() {
  const saved = await getHandle(DIR_KEY);
  if (!saved) return;

  const state = await queryPermission(saved);
  const statusEl = document.getElementById('setup_csv_status');

  if (state === 'granted') {
    window._dirHandle = saved;
    if (statusEl) statusEl.textContent = 'Carpeta CSV autorizada ✓';
  } else {
    // Permission expired — keep handle in IndexedDB but warn user to re-authorize.
    if (statusEl) {
      statusEl.textContent = 'Haga clic en "Configurar carpeta CSV" para reautorizar';
      statusEl.style.color = '#f39c12';
    }
  }
}
window.addEventListener('load', loadConfiguredDirectory);

// ── Read / Write ─────────────────────────────────────────────────────────────

async function readCsvFromDir() {
  if (!window._dirHandle) return '';
  try {
    const fileHandle = await window._dirHandle.getFileHandle(CSV_FILENAME, { create: true });
    const file = await fileHandle.getFile();
    return await file.text();
  } catch (err) {
    console.warn('No se pudo leer CSV desde directorio:', err);
    return '';
  }
}

async function writeCsvToDir(content) {
  if (!window._dirHandle) return false;
  try {
    const fileHandle = await window._dirHandle.getFileHandle(CSV_FILENAME, { create: true });
    const writable = await fileHandle.createWritable();
    await writable.write(content);
    await writable.close();
    return true;
  } catch (err) {
    console.error('Error escribiendo CSV en directorio:', err);
    return false;
  }
}
