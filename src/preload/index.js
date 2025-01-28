import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

// Custom APIs for renderer
const api = {
  ipcRenderer: {
    send: (channel, ...args) => {
      const validChannels = [
        'recording-status-changed',
        'ping',
        'toggle-recording',
        'start-recording-hotkey',
        'set-always-on-top',
        'set-sound-enabled',
        'start-shortcut-recording',
        'stop-shortcut-recording',
        'get-current-shortcut'
      ]
      if (validChannels.includes(channel)) {
        ipcRenderer.send(channel, ...args)
      }
    },
    on: (channel, func) => {
      const validChannels = [
        'toggle-recording',
        'always-on-top-changed',
        'sound-enabled-changed',
        'shortcut-recorded',
        'current-shortcut'
      ]
      if (validChannels.includes(channel)) {
        ipcRenderer.on(channel, (event, ...args) => func(...args))
      }
    },
    removeAllListeners: (channel) => {
      const validChannels = [
        'toggle-recording',
        'sound-enabled-changed',
        'shortcut-recorded',
        'current-shortcut'
      ]
      if (validChannels.includes(channel)) {
        ipcRenderer.removeAllListeners(channel)
      }
    },
    invoke: (channel, ...args) => {
      const validChannels = [
        'start-recording',
        'stop-recording',
        'save-shortcut',
        'load-shortcut',
        'get-profiles',
        'create-profile',
        'update-profile',
        'delete-profile',
        'save-selected-profile',
        'get-selected-profile',
        'process-with-ai'
      ]
      if (validChannels.includes(channel)) {
        return ipcRenderer.invoke(channel, ...args)
      }
    }
  }
}

// Use `contextBridge` APIs to expose Electron APIs to
// renderer only if context isolation is enabled, otherwise
// just add to the DOM global.
if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', api)
    contextBridge.exposeInMainWorld('electronAPI', electronAPI)
  } catch (error) {
    console.error(error)
  }
} else {
  window.electron = api
  window.electronAPI = electronAPI
}
