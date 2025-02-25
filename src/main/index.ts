import { app, shell, BrowserWindow, ipcMain, clipboard } from "electron";
import { join } from "path";
import { electronApp, optimizer, is } from "@electron-toolkit/utils";
import iconPath from "../../resources/icon.png?asset";
import { initStore } from "./modules.ts/electron-store";
import { initApiCallsV1 } from "./modules.ts/api-calls-v1";
import { createTray, destroyTray } from "./modules.ts/tray";
import { initResize } from "./modules.ts/resize";
import { keyboard, Key } from '@nut-tree-fork/nut-js';

// Remove the tray variable since it's now managed in the tray module
function createWindow(): void {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 900,
    minWidth: 900,
    height: 670,
    minHeight: 420,

    show: false,
    autoHideMenuBar: true,
    // ...(process.platform === "linux" ? { icon: iconPath } : {}),
    icon: iconPath,
    webPreferences: {
      preload: join(__dirname, "../preload/index.js"),
      sandbox: false,
    },
  });

  // Add this to handle window close button
  mainWindow.on('close', (event) => {
    event.preventDefault();
    mainWindow.hide();
  });

  mainWindow.on("ready-to-show", () => {
    mainWindow.show();
  });

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url);
    return { action: "deny" };
  });

  // HMR for renderer base on electron-vite cli.
  // Load the remote URL for development or the local html file for production.
  if (is.dev && process.env["ELECTRON_RENDERER_URL"]) {
    mainWindow.loadURL(process.env["ELECTRON_RENDERER_URL"]);
  } else {
    mainWindow.loadFile(join(__dirname, "../renderer/index.html"));
  }

  // Open Website
  ipcMain.on('open-external', async (_event, url) => {
    await shell.openExternal(url)
  })

  // Copy to clipboard
  ipcMain.on('copy-to-clipboard', async (_event, text) => {
    clipboard.writeText(text)
  })

  // Simulate paste
  ipcMain.on('simulate-paste', async () => {
    try {
      await keyboard.pressKey(Key.LeftControl);
      await keyboard.pressKey(Key.V);
      await keyboard.releaseKey(Key.V);
      await keyboard.releaseKey(Key.LeftControl);
    } catch (error) {
      console.error('Error simulating paste:', error);
    }
  });


}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(async () => {
  // Set app user model id for windows
  electronApp.setAppUserModelId("com.electron");

  // Initialize store and register shortcut
  const store = await initStore();
  const recordShortcut = store.get("settings").recordShortcut;
  await initApiCallsV1(recordShortcut, app);
  await initResize();

  // see https://github.com/alex8088/electron-toolkit/tree/master/packages/utils
  app.on("browser-window-created", (_, window) => {
    optimizer.watchWindowShortcuts(window);
  });

  createWindow();

  // Replace tray creation with the new module
  createTray(iconPath);

  app.on("activate", function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});


// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
// Modify the window-all-closed event
// app.on('window-all-closed', (event: any) => {
//   event.preventDefault();
// });

// Add cleanup in will-quit event
app.on('will-quit', () => {
  destroyTray();
  // Remove IPC handlers
  ipcMain.removeHandler('resize-window');
});
// In this file you can include the rest of your app"s specific main process
// code. You can also put them in separate files and require them here.
// Add this import at the top


// Add this in your IPC handlers section
