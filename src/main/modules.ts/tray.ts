import { app, Tray, Menu, BrowserWindow } from 'electron';

let tray: Tray | null = null;

export function getMainWindow(): BrowserWindow | undefined {
    // Buscar la ventana principal excluyendo la ventana popup
    return BrowserWindow.getAllWindows().find(window =>
        !window.webContents.getURL().includes('index-popup.html')
    );
}

export function createTray(icon: string): Tray {
    console.log("[TRAY] Creating tray")
    tray = new Tray(icon);

    const contextMenu = Menu.buildFromTemplate([
        {
            label: 'Show app',
            click: () => {
                const window = getMainWindow();
                if (window) {
                    window.show();
                }
            }
        },
        {
            label: 'Always on Top',
            type: 'checkbox',
            checked: false,
            click: (menuItem) => {
                const window = getMainWindow();
                if (window) {
                    window.setAlwaysOnTop(menuItem.checked);
                }
            }
        },
        {
            label: 'Quit',
            click: () => {
                app.exit();
            }
        }
    ]);

    tray.setContextMenu(contextMenu);
    tray.setToolTip('Dicto Desktop');

    tray.on('click', () => {
        const window = getMainWindow();
        if (window) {
            window.show();
        }
    });

    return tray;
}

export function destroyTray(): void {
    if (tray) {
        tray.destroy();
    }
}