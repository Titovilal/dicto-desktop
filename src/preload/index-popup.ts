import { contextBridge, ipcRenderer } from 'electron'

// Create the popup API
contextBridge.exposeInMainWorld('popupAPI', {
    onUpdateProcessingState: (callback: (isProcessing: boolean) => void) => {
        ipcRenderer.on('update-processing-state', (_event, isProcessing) => callback(isProcessing))
        return () => {
            ipcRenderer.removeAllListeners('update-processing-state')
        }
    }
}) 