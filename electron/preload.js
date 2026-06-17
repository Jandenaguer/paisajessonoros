// Puente seguro entre el cuestionario (renderer) y el proceso principal.
// Expone window.electronAPI.sendResults(csv, filename) -> Promise<{ok, error?}>

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  sendResults: (csv, filename) =>
    ipcRenderer.invoke('send-results-email', { csv, filename })
});
