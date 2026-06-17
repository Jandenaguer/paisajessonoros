// Proceso principal de Electron.
// Carga el cuestionario (audio_quiz.html) y expone un canal IPC para enviar
// los resultados de cada participante por correo (Gmail + nodemailer).

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const nodemailer = require('nodemailer');

const ROOT = path.join(__dirname, '..');

// Localiza email_config.json. Empaquetado: junto al ejecutable (editable, en
// la carpeta "resources"). En desarrollo: en la raiz del proyecto.
function configPath() {
  const candidates = [];
  if (process.resourcesPath) candidates.push(path.join(process.resourcesPath, 'email_config.json'));
  candidates.push(path.join(ROOT, 'email_config.json'));
  for (const c of candidates) {
    try { if (fs.existsSync(c)) return c; } catch (e) { /* ignore */ }
  }
  return path.join(ROOT, 'email_config.json');
}

// Lee las credenciales de envio desde email_config.json (NO versionado).
function loadConfig() {
  try {
    return JSON.parse(fs.readFileSync(configPath(), 'utf8'));
  } catch (e) {
    console.error('No se pudo leer email_config.json:', e.message);
    return null;
  }
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1100,
    height: 820,
    icon: path.join(ROOT, 'styles', 'images', 'logo3.ico'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });
  win.setMenuBarVisibility(false);
  win.loadFile(path.join(ROOT, 'audio_quiz.html'));
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// Canal IPC: recibe el CSV de un participante y lo envia por correo adjunto.
ipcMain.handle('send-results-email', async (event, payload) => {
  const config = loadConfig();
  if (!config || !config.sender || !config.appPassword) {
    return { ok: false, error: 'Configuracion de correo ausente o incompleta (email_config.json)' };
  }

  try {
    const transporter = nodemailer.createTransport({
      host: 'smtp.gmail.com',
      port: 465,
      secure: true,
      auth: { user: config.sender, pass: config.appPassword }
    });

    await transporter.sendMail({
      from: config.sender,
      to: config.recipient || 'm.hiniesto.2019@alumnos.urjc.es',
      subject: 'Resultados Paisajes Sonoros - ' + payload.filename,
      text: 'Nuevo participante completado. Se adjunta el CSV con sus respuestas.',
      attachments: [{ filename: payload.filename, content: payload.csv }]
    });

    return { ok: true };
  } catch (err) {
    return { ok: false, error: String((err && err.message) || err) };
  }
});
