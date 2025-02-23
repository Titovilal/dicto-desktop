import { ipcMain, BrowserWindow } from 'electron';

export async function initResize() {
    console.log("[RESIZE] Initializing resize")
    ipcMain.handle('resize-window', (_, width, height) => {
        BrowserWindow.getAllWindows()[0]?.setSize(width, height);
    });
}