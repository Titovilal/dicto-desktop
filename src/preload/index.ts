import { contextBridge } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'
import { ipcRenderer } from 'electron'

// Define the logger API for the renderer process
const loggerAPI = {
  log: (message: string): void => ipcRenderer.send('log', { level: 'info', message }),
  info: (message: string): void => ipcRenderer.send('log', { level: 'info', message }),
  warn: (message: string): void => ipcRenderer.send('log', { level: 'warn', message }),
  error: (message: string): void => ipcRenderer.send('log', { level: 'error', message }),
  debug: (message: string): void => ipcRenderer.send('log', { level: 'debug', message })
}

if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('logger', loggerAPI)
  } catch (error) {
    console.error(error)
  }
} else {
  // @ts-ignore (define in dts)
  window.electron = electronAPI
  // @ts-ignore (define in dts)
  window.logger = loggerAPI
}
