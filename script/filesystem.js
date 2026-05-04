"use strict";

// File System Access API helper to store a single CSV in a local folder.
// This uses IndexedDB to persist the directory handle across sessions.

const CSV_FILENAME = 'paisajes_sonoros.csv';
const DB_NAME = 'paisajes_csv_fs';
const STORE_NAME = 'handles';
const DIR_KEY = 'csv_dir';

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
    const store = tx.objectStore(STORE_NAME);
    const req = store.put({ key, value });
    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error);
    tx.oncomplete = () => resolve();
  });
}

async function getHandle(key) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const req = store.get(key);
    req.onsuccess = () => resolve(req.result ? req.result.value : null);
    req.onerror = () => reject(req.error);
  });
}

// Configurar carpeta CSV (FS API) - debe ejecutarse por usuario
window.setupCsvDirectory = async function() {
  try {
    const dirHandle = await window.showDirectoryPicker({ mode: 'readwrite' });
    dirHandle && await putHandle(DIR_KEY, dirHandle);
    window._dirHandle = dirHandle;
    if (document.getElementById('setup_csv_status')) {
      document.getElementById('setup_csv_status').textContent = 'Carpeta CSV configurada';
    }
  } catch (e) {
    console.error('Error configurando carpeta CSV', e);
  }
};

async function loadConfiguredDirectory() {
  const saved = await getHandle(DIR_KEY);
  if (saved) {
    window._dirHandle = saved;
    if (document.getElementById('setup_csv_status')) {
      document.getElementById('setup_csv_status').textContent = 'Carpeta CSV configurada';
    }
  }
}
window.addEventListener('load', loadConfiguredDirectory);

async function readCsvFromDir() {
  const dir = window._dirHandle;
  if (!dir) {
    await loadConfiguredDirectory();
  }
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
  if (!window._dirHandle) {
    await loadConfiguredDirectory();
  }
  if (!window._dirHandle) return;
  try {
    const fileHandle = await window._dirHandle.getFileHandle(CSV_FILENAME, { create: true });
    const writable = await fileHandle.createWritable();
    await writable.write(content);
    await writable.close();
  } catch (err) {
    console.error('Error escribiendo CSV en directorio:', err);
  }
}
