import { contextBridge, ipcRenderer } from 'electron'

// Create the popup API
contextBridge.exposeInMainWorld('popupAPI', {
    onUpdateState: (callback: (state: 'recording' | 'processing' | 'finished' | 'using') => void) => {
        ipcRenderer.on('update-popup-state', (_event, state) => {
            console.log('Received state update:', state)
            callback(state)
        })
        return () => {
            ipcRenderer.removeAllListeners('update-popup-state')
        }
    },
    onUpdateMessage: (callback: (message: string) => void) => {
        ipcRenderer.on('update-popup-message', (_event, message) => {
            console.log('Received message update:', message)
            callback(message)
        })
        return () => {
            ipcRenderer.removeAllListeners('update-popup-message')
        }
    }
})

console.log('popupAPI exposed in index-popup:', !!window.popupAPI) 