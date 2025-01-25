import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

// Custom APIs for renderer
const api = {}

// Use `contextBridge` APIs to expose Electron APIs to
// renderer only if context isolation is enabled, otherwise
// just add to the DOM global.
if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', {
      ...electronAPI,
      ipcRenderer: {
        send: (channel, ...args) => {
          const validChannels = ['recording-status-changed', 'ping', 'toggle-recording', 'start-recording-hotkey', 'set-always-on-top', 'set-sound-enabled', 'start-shortcut-recording', 'stop-shortcut-recording']
          if (validChannels.includes(channel)) {
            ipcRenderer.send(channel, ...args)
          }
        },
        on: (channel, func) => {
          const validChannels = ['toggle-recording', 'always-on-top-changed', 'sound-enabled-changed', 'shortcut-recorded', 'current-shortcut']
          if (validChannels.includes(channel)) {
            ipcRenderer.on(channel, (event, ...args) => func(...args))
          }
        },
        removeAllListeners: (channel) => {
          const validChannels = ['toggle-recording', 'sound-enabled-changed', 'shortcut-recorded', 'current-shortcut']
          if (validChannels.includes(channel)) {
            ipcRenderer.removeAllListeners(channel)
          }
        }
      }
    })
    contextBridge.exposeInMainWorld('api', api)
  } catch (error) {
    console.error(error)
  }
} else {
  window.electron = electronAPI
  window.api = api
}
