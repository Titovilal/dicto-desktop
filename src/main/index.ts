import { app, shell, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import iconPath from '../../resources/icon.png?asset'
import { initLogger, initLoggerIPC } from './modules.ts/logger'
import { initStore } from './modules.ts/electron-store'
import { initApiCallsV1 } from './modules.ts/api-calls-v1'
import { createTray, destroyTray } from './modules.ts/tray'
import { initResize } from './modules.ts/resize'
import { destroyRecordingPopup } from './modules.ts/popup-window'
import { initShortcuts, unregisterAllShortcuts } from './modules.ts/shortcuts'
import { initAutoUpdater } from './modules.ts/auto-updater'

// Initialize logger as early as possible
initLogger()

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
    icon: iconPath,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false
    }
  })

  // Add a name or identifier to the main window
  mainWindow.setTitle('Dicto Main Window')

  // Add this to handle window close button
  mainWindow.on('close', (event) => {
    event.preventDefault()
    mainWindow.hide()
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // HMR for renderer base on electron-vite cli.
  // Load the remote URL for development or the local html file for production.
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }

  // Open Website
  ipcMain.on('open-external', async (_event, url) => {
    await shell.openExternal(url)
  })
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(async () => {
  // Set app user model id for windows
  electronApp.setAppUserModelId('com.electron')

  // Initialize logger IPC
  initLoggerIPC()

  // Initialize store first
  const store = await initStore()

  // Get shortcut settings from store
  const recordShortcut = store.get('settings').recordShortcut
  const changeProfileShortcut = store.get('settings').changeProfileShortcut

  // Initialize shortcuts
  initShortcuts(app, recordShortcut, changeProfileShortcut, store)

  // Initialize API calls without shortcut registration
  await initApiCallsV1(app)

  // Initialize resize functionality
  await initResize(app)

  // see https://github.com/alex8088/electron-toolkit/tree/master/packages/utils
  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  createWindow()

  await initAutoUpdater()

  // Replace tray creation with the new module
  createTray(iconPath)

  app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
// Modify the window-all-closed event
// app.on('window-all-closed', (event: any) => {
//   event.preventDefault();
// });

// Add cleanup in will-quit event
app.on('will-quit', () => {
  destroyTray()
  destroyRecordingPopup()
  unregisterAllShortcuts()
})
// In this file you can include the rest of your app"s specific main process
// code. You can also put them in separate files and require them here.
// Add this import at the top

// Add this in your IPC handlers section
