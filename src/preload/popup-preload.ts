import { contextBridge, ipcRenderer } from 'electron';

// Registrar un log para verificar que el preload se está cargando
console.log('Popup preload script loaded');

// Crear un store para los callbacks
const callbacks: ((state: 'recording' | 'processing' | 'finished') => void)[] = [];

// Configurar el listener una sola vez
ipcRenderer.on('update-popup-state', (_event, state) => {
    console.log('IPC update-popup-state received in preload:', state);
    // Notificar a todos los callbacks registrados
    callbacks.forEach(callback => callback(state));
});

// Exponer una API segura para la ventana emergente
contextBridge.exposeInMainWorld('popupAPI', {
    onUpdateState: (callback: (state: 'recording' | 'processing' | 'finished') => void) => {
        console.log('Registering update-popup-state listener');
        // Añadir el callback al array
        callbacks.push(callback);

        // Función de limpieza para eliminar el listener cuando el componente se desmonte
        return () => {
            console.log('Removing update-popup-state listener');
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        };
    }
});

// Log para verificar que el objeto popupAPI se ha expuesto correctamente
console.log('popupAPI exposed:', !!window.popupAPI); 