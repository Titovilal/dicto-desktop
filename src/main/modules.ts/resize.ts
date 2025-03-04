import { ipcMain, BrowserWindow, App } from 'electron';

export async function initResize(
    app: App
) {
    console.log("[RESIZE] Initializing resize")

    ipcMain.on('toggle-compact-mode', (_event, isCompact) => {
        console.log("[RESIZE] Toggling compact mode", isCompact);
        // Get the main window specifically, excluding the popup window
        const window = BrowserWindow.getAllWindows().find(window =>
            !window.webContents.getURL().includes('index-popup.html')
        );

        if (!window) {
            console.error('[RESIZE] No window found');
            return;
        }

        const width = isCompact ? 400 : 900;
        const height = isCompact ? 150 : 670;

        window.setAlwaysOnTop(isCompact);
        window.setMinimumSize(width, height);
        window.setSize(width, height);
    });

    app.on('will-quit', () => {
        ipcMain.removeHandler('resize-window');
    });
}