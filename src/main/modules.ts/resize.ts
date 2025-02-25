import { ipcMain, BrowserWindow } from 'electron';

export async function initResize() {
    console.log("[RESIZE] Initializing resize")

    ipcMain.on('toggle-compact-mode', (_event, isCompact) => {
        console.log("[RESIZE] Toggling compact mode", isCompact);
        const window = BrowserWindow.getAllWindows()[0];

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

}