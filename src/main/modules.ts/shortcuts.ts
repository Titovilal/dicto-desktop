import { globalShortcut, BrowserWindow, ipcMain, App } from 'electron';
import { showRecordingPopup } from './popup-window';

// Track registered shortcuts
let currentRecordingShortcut: string | null = null;
let currentProfileShortcut: string | null = null;

/**
 * Register the main recording shortcut
 * @param shortcut The keyboard shortcut to register
 */
function registerRecordingShortcut(shortcut: string): boolean {
    // Unregister previous shortcut if it exists
    if (currentRecordingShortcut) {
        globalShortcut.unregister(currentRecordingShortcut);
        currentRecordingShortcut = null;
    }

    try {
        const success = globalShortcut.register(shortcut, () => {
            console.log('[SHORTCUTS] Recording shortcut triggered');
            const mainWindow = BrowserWindow.getAllWindows().find(window =>
                !window.webContents.getURL().includes('index-popup.html')
            );

            if (mainWindow) {
                mainWindow.webContents.send('toggle-recording');
            } else {
                console.error('[SHORTCUTS] Main window not found');
            }
        });

        if (success) {
            currentRecordingShortcut = shortcut;
            console.log(`[SHORTCUTS] Recording shortcut ${shortcut} registered successfully`);
            return true;
        } else {
            console.error(`[SHORTCUTS] Failed to register recording shortcut ${shortcut}`);
            return false;
        }
    } catch (error) {
        console.error(`[SHORTCUTS] Error registering recording shortcut ${shortcut}:`, error);
        return false;
    }
}

/**
 * Register the profile switching shortcut
 * @param shortcut The keyboard shortcut to register
 * @param store The electron-store instance to access settings
 */
function registerProfileShortcut(shortcut: string, store: any): boolean {
    // Unregister previous shortcut if it exists
    if (currentProfileShortcut) {
        globalShortcut.unregister(currentProfileShortcut);
        currentProfileShortcut = null;
    }

    try {
        const success = globalShortcut.register(shortcut, () => {
            console.log('[SHORTCUTS] Change profile shortcut triggered');
            const mainWindow = BrowserWindow.getAllWindows().find(window =>
                !window.webContents.getURL().includes('index-popup.html')
            );

            if (!mainWindow) {
                return
            }
            // Enviar evento para cambiar perfil
            mainWindow.webContents.send('cycle-profile');

            // Obtener el perfil actualizado y mostrar popup
            setTimeout(() => {
                const selectedProfile = store.get('settings.selectedProfile');
                showRecordingPopup({
                    state: 'using',
                    message: selectedProfile
                });
            }, 100);
        });

        if (success) {
            currentProfileShortcut = shortcut;
            console.log(`[SHORTCUTS] Profile shortcut ${shortcut} registered successfully`);
            return true;
        } else {
            console.error(`[SHORTCUTS] Failed to register profile shortcut ${shortcut}`);
            return false;
        }
    } catch (error) {
        console.error(`[SHORTCUTS] Error registering profile shortcut ${shortcut}:`, error);
        return false;
    }
}

/**
 * Unregister all shortcuts
 */
export function unregisterAllShortcuts(): void {
    globalShortcut.unregisterAll();
    currentRecordingShortcut = null;
    currentProfileShortcut = null;
    console.log('[SHORTCUTS] All shortcuts unregistered');
}

/**
 * Initialize the shortcuts module
 * @param initialRecordingShortcut The initial recording shortcut
 * @param initialProfileShortcut The initial profile shortcut
 * @param store The electron-store instance
 */
export function initShortcuts(
    app: App,
    initialRecordingShortcut: string,
    initialProfileShortcut: string,
    store: any
): void {

    ipcMain.handle('update-shortcut', async (_, newShortcut: string) => {
        return registerRecordingShortcut(newShortcut);
    });

    ipcMain.handle('update-profile-shortcut', async (_, newShortcut: string) => {
        return registerProfileShortcut(newShortcut, store);
    });
    registerRecordingShortcut(initialRecordingShortcut);
    registerProfileShortcut(initialProfileShortcut, store);

    app.on('will-quit', () => {
        unregisterAllShortcuts();
        ipcMain.removeHandler('update-shortcut');
        ipcMain.removeHandler('update-profile-shortcut');
    });

    console.log('[SHORTCUTS] Shortcuts module initialized');
}

