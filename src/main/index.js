import { app, shell, BrowserWindow } from 'electron'
import { join } from 'path';
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'
import { createTray } from './modules/tray'
import { 
  registerGlobalShortcuts, 
  getCurrentShortcut,
  unregisterGlobalShortcuts
} from './modules/shortcuts'
import { setupIPC } from './modules/ipc'

let mainWindow = null

function createWindow() {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 900,
    height: 670,
    show: false,
    autoHideMenuBar: true,
    alwaysOnTop: false,
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      nodeIntegration: true,
      contextIsolation: true,
      webSecurity: true
    }
  })

  // Configurar CSP
  mainWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [
          "default-src 'self'",
          "script-src 'self'",
          "connect-src 'self' https://api.lemonfox.ai",
          "style-src 'self' 'unsafe-inline'",
          "media-src 'self' blob:",
          "img-src 'self' data: blob:"
        ].join('; ')
      }
    })
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

  // Evitar que la aplicación se cierre al presionar la X
  mainWindow.on('close', (event) => {
    if (!app.isQuitting) {
      event.preventDefault()
      mainWindow.hide()
    }
    return false
  })

  // Setup IPC handlers
  setupIPC(mainWindow)
}

// Add keyboard event listener to the main window
app.whenReady().then(() => {
  // Set app user model id for windows
  electronApp.setAppUserModelId('com.electron')

  // Default open or close DevTools by F12 in development
  // and ignore CommandOrControl + R in production.
  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  createWindow()
  createTray({ mainWindow, app })
  
  // Pequeño retraso para asegurar que todo esté inicializado
  setTimeout(() => {
    registerGlobalShortcuts(mainWindow)
  }, 1000)

  // Send initial shortcut to renderer
  setTimeout(() => {
    mainWindow?.webContents.send('current-shortcut', getCurrentShortcut())
  }, 1000)

  app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', (event) => {
  if (process.platform !== 'darwin') {
    // No cerramos la app, solo la ocultamos
    event.preventDefault()
  }
})

app.on('will-quit', () => {
  unregisterGlobalShortcuts()
})
// In this file you can include the rest of your app"s specific main process
// code. You can also put them in separate files and require them here.

