import { BrowserWindow, screen, ipcMain } from 'electron';
import { join } from 'path';
import { is } from '@electron-toolkit/utils';

let popupWindow: BrowserWindow | null = null;
let ipcHandlersRegistered = false; // Track if handlers are already registered

// Define popup states
export type PopupState = 'recording' | 'processing' | 'finished' | 'using';

// Store current state
let currentState: PopupState = 'recording';

// Añadir esta interfaz al inicio del archivo
interface PopupOptions {
    state: PopupState;
    message?: string;
}

function createRecordingPopup() {
    console.log('[POPUP] Creating window popup');
    if (popupWindow) {
        return popupWindow;
    }

    popupWindow = new BrowserWindow({
        width: 480,
        height: 80,
        frame: false,
        resizable: false,
        transparent: true,
        alwaysOnTop: true,
        skipTaskbar: true,
        show: false,
        backgroundColor: '#00000000',
        focusable: false,
        webPreferences: {
            preload: join(__dirname, '../preload/index-popup.js'),
            contextIsolation: true,
            nodeIntegration: false
        }
    });

    // Hacer que la ventana ignore eventos del ratón por defecto
    popupWindow.setIgnoreMouseEvents(true, { forward: true });

    // Position the window in the bottom right corner of the screen
    const { width: screenWidth, height: screenHeight } = screen.getPrimaryDisplay().workAreaSize;
    const [width, height] = popupWindow.getSize();
    popupWindow.setPosition(screenWidth - width - 20, screenHeight - height - 20);

    // Load the React popup window
    if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
        popupWindow.loadURL(`${process.env['ELECTRON_RENDERER_URL']}/index-popup.html`);
    } else {
        popupWindow.loadFile(join(__dirname, '../renderer/index-popup.html'));
    }

    popupWindow.on('ready-to-show', () => {
        if (popupWindow) {
            popupWindow.showInactive();
            popupWindow.webContents.send('update-popup-state', currentState);
        }
    });

    popupWindow.on('closed', () => {
        popupWindow = null;
    });

    return popupWindow;
}

export function showRecordingPopup(options: PopupState | PopupOptions) {
    if (!popupWindow) {
        popupWindow = createRecordingPopup();
    }

    if (popupWindow) {
        console.log('[POPUP] Recording popup found');
        if (!popupWindow.isVisible()) {
            popupWindow.showInactive();
        }

        // Manejar tanto el formato antiguo como el nuevo
        if (typeof options === 'string') {
            currentState = options;
            popupWindow.webContents.send('update-popup-state', options);
        } else {
            currentState = options.state;
            popupWindow.webContents.send('update-popup-state', options.state);
            if (options.message) {
                popupWindow.webContents.send('update-popup-message', options.message);
            }
        }
    }
}

export function updatePopupState(state: PopupState) {
    currentState = state;
    if (popupWindow) {
        try {
            popupWindow.webContents.send('update-popup-state', state);
        } catch (error) {
            console.error('Error updating popup state:', error);
        }
    }
}

export function hideRecordingPopup() {
    if (popupWindow && popupWindow.isVisible()) {
        popupWindow.hide();
    }
}

export function destroyRecordingPopup() {
    if (popupWindow) {
        try {
            popupWindow.destroy();
            popupWindow = null;
        } catch (error) {
            console.error('Error destroying recording popup:', error);
        }
    }
}

export function updatePopupMessage(message: string) {
    if (popupWindow) {
        try {
            popupWindow.webContents.send('update-popup-message', message);
        } catch (error) {
            console.error('Error updating popup message:', error);
        }
    } else {
        console.error('[POPUP] Cannot update message, popup window is null');
    }
}

// Actualizar el registro del manejador IPC
export function initPopupWindow() {
    if (!ipcHandlersRegistered) {
        ipcMain.handle('show-popup', async (_, options: PopupState | PopupOptions) => {
            showRecordingPopup(options);
        });

        ipcMain.handle('update-popup-state', async (_, state: PopupState) => {
            updatePopupState(state);
            return true;
        });

        ipcMain.handle('hide-popup', async () => {
            hideRecordingPopup();
            return true;
        });

        ipcMain.handle('update-popup-message', async (_, message: string) => {
            updatePopupMessage(message);
            return true;
        });

        // Handle popup message updates
        ipcMain.on('update-popup-message', (_, message: string) => {
            updatePopupMessage(message);
        });

        ipcHandlersRegistered = true;
        console.log('[POPUP] IPC handlers registered');
    }

    return {
        showRecordingPopup,
        updatePopupState,
        hideRecordingPopup,
        destroyRecordingPopup,
        updatePopupMessage
    };
}