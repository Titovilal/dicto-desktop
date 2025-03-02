import { BrowserWindow, screen } from 'electron';
import { join } from 'path';
import { is } from '@electron-toolkit/utils';

let popupWindow: BrowserWindow | null = null;

// Define los posibles estados de la ventana emergente
export type PopupState = 'recording' | 'processing' | 'finished';

// Variable para almacenar el estado actual
let currentState: PopupState = 'recording';

export function createRecordingPopup() {
    // Don't create a new window if one already exists
    if (popupWindow) {
        return popupWindow;
    }

    // Create a small, frameless window for the recording indicator
    popupWindow = new BrowserWindow({
        width: 160,
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
            preload: join(__dirname, '../preload/popup-preload.js'),
            contextIsolation: true,
            nodeIntegration: false
        }
    });

    // Position the window in the bottom right corner of the screen
    const [width, height] = popupWindow.getSize();
    const { width: screenWidth, height: screenHeight } = screen.getPrimaryDisplay().workAreaSize;
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

export function showRecordingPopup(state: PopupState = 'recording') {
    currentState = state;
    try {
        const popup = createRecordingPopup();
        popup.show();

        // Only send the update if we have a valid popup window
        if (popup && popup.webContents) {
            popup.webContents.send('update-popup-state', state);
        }
    } catch (error) {
        console.error('Error showing recording popup:', error);
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
    } else {
        console.error('[POPUP] Cannot update state, popup window is null');
    }
}

export function hideRecordingPopup() {
    if (popupWindow) {
        try {
            popupWindow.hide();
        } catch (error) {
            console.error('Error hiding recording popup:', error);
        }
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