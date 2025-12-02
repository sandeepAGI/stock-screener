/**
 * StockAnalyzer Pro - Preload Script
 *
 * Exposes a secure bridge between the renderer process and main process.
 * Uses contextBridge to expose specific APIs without exposing Node.js globals.
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // App information
  getAppInfo: () => ipcRenderer.invoke('get-app-info'),
  getBackendUrl: () => ipcRenderer.invoke('get-backend-url'),

  // External links
  openExternal: (url) => ipcRenderer.invoke('open-external', url),

  // Platform detection
  platform: process.platform,
  isElectron: true,

  // Version info
  versions: {
    node: process.versions.node,
    chrome: process.versions.chrome,
    electron: process.versions.electron
  }
});

// Log that preload script has loaded
console.log('StockAnalyzer Pro preload script loaded');
