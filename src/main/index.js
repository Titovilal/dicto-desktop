import { app, shell, BrowserWindow, ipcMain, Tray, Menu, globalShortcut } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'

let tray = null
let mainWindow = null
let currentShortcut = 'CommandOrControl+Space'
let isRecordingShortcut = false
let trayContextMenu = null  // Add this to store menu reference

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

  // Agregar comunicación IPC para controlar la grabación
  ipcMain.on('recording-status-changed', (_, isRecording) => {
    // Opcional: Actualizar el icono del tray o mostrar indicador de grabación
    if (isRecording) {
      tray?.setToolTip('Dicto Desktop - Grabando...')
    } else {
      tray?.setToolTip('Dicto Desktop')
    }
  })

  // Agregar el manejador para siempre visible
  ipcMain.on('set-always-on-top', (_, value) => {
    if (mainWindow) {
      // Establecer alwaysOnTop
      mainWindow.setAlwaysOnTop(value)
      
      // Confirmar el cambio enviando el estado actual de vuelta al renderer
      mainWindow.webContents.send('always-on-top-changed', mainWindow.isAlwaysOnTop())
    }
  })

  // Agregar el manejador para sonidos
  ipcMain.on('set-sound-enabled', (_, value) => {
    if (mainWindow && tray && trayContextMenu) {
      // Actualizar el menú del tray usando la referencia almacenada
      const soundMenuItem = trayContextMenu.items.find(item => item.label === 'Sonidos')
      if (soundMenuItem) {
        soundMenuItem.checked = value
        tray.setContextMenu(trayContextMenu)
      }
    }
  })

  // Mantener sincronizado el estado
  mainWindow.on('always-on-top-changed', (event, isOnTop) => {
    mainWindow.webContents.send('always-on-top-changed', isOnTop)
  })
}

function createTray() {
  tray = new Tray(icon)
  trayContextMenu = Menu.buildFromTemplate([
    {
      label: 'Mostrar App',
      click: () => {
        mainWindow.show()
      }
    },
    {
      label: 'Sonidos',
      type: 'checkbox',
      checked: true,
      click: (menuItem) => {
        mainWindow?.webContents.send('sound-enabled-changed', menuItem.checked)
      }
    },
    {
      label: 'Siempre Visible',
      type: 'checkbox',
      checked: false,
      click: (menuItem) => {
        mainWindow.setAlwaysOnTop(menuItem.checked)
      }
    },
    {
      type: 'separator'
    },
    {
      label: 'Salir',
      click: () => {
        app.isQuitting = true
        app.quit()
      }
    }
  ])

  tray.setToolTip('Dicto Desktop')
  tray.setContextMenu(trayContextMenu)

  // Doble clic en el icono del tray muestra la app
  tray.on('double-click', () => {
    mainWindow.show()
  })
}

function registerGlobalShortcuts() {
  // Unregister any existing shortcuts first
  unregisterGlobalShortcuts()
  
  const wasRegistered = globalShortcut.register(currentShortcut, () => {
    console.log('Shortcut triggered!')
    if (mainWindow) {
      console.log('Sending toggle-recording to window')
      mainWindow.webContents.send('toggle-recording')
    } else {
      console.log('No window found!')
    }
  })
  
  console.log('Shortcut registration successful:', wasRegistered)
}

function unregisterGlobalShortcuts() {
  globalShortcut.unregisterAll()
}

// Add these IPC handlers after createWindow()
ipcMain.on('start-shortcut-recording', () => {
  isRecordingShortcut = true
  // Unregister current shortcut while recording
  unregisterGlobalShortcuts()
})

ipcMain.on('stop-shortcut-recording', () => {
  isRecordingShortcut = false
  // Re-register the current shortcut
  registerGlobalShortcuts()
})

// Add keyboard event listener to the main window
app.whenReady().then(() => {
  // Set app user model id for windows
  electronApp.setAppUserModelId('com.electron')

  // Default open or close DevTools by F12 in development
  // and ignore CommandOrControl + R in production.
  // see https://github.com/alex8088/electron-toolkit/tree/master/packages/utils
  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  // IPC test
  ipcMain.on('ping', () => console.log('pong'))

  createWindow()
  createTray()
  
  // Pequeño retraso para asegurar que todo esté inicializado
  setTimeout(() => {
    registerGlobalShortcuts()
  }, 1000)

  // Send initial shortcut to renderer
  setTimeout(() => {
    mainWindow?.webContents.send('current-shortcut', currentShortcut)
  }, 1000)

  // Listen for keyboard events when recording shortcut
  if (mainWindow) {
    mainWindow.webContents.on('before-input-event', (event, input) => {
      if (!isRecordingShortcut) return

      if (input.type === 'keyDown') {
        let newShortcut = []
        
        // Usar CommandOrControl en lugar de Control/Meta en macOS
        if (process.platform === 'darwin') {
          if (input.meta) newShortcut.push('CommandOrControl')
        } else if (input.control) {
          newShortcut.push('CommandOrControl')
        }
        
        // Agregar otros modificadores
        if (input.alt) newShortcut.push('Alt')
        if (input.shift) newShortcut.push('Shift')
        
        // Formatear la tecla principal
        let key = input.key
        if (key.length === 1) {
          key = key.toUpperCase()
        } else {
          // Mapear teclas especiales
          const specialKeys = {
            'Control': '',
            'Alt': '',
            'Shift': '',
            'Meta': '',
            ' ': 'Space',
            'ArrowUp': 'Up',
            'ArrowDown': 'Down',
            'ArrowLeft': 'Left',
            'ArrowRight': 'Right',
            'AudioVolumeMute': 'VolumeMute',
            'AudioVolumeDown': 'VolumeDown',
            'AudioVolumeUp': 'VolumeUp',
            'MediaTrackNext': 'MediaNextTrack',
            'MediaTrackPrevious': 'MediaPreviousTrack',
            'MediaStop': 'MediaStop',
            'MediaPlayPause': 'MediaPlayPause'
          }
          key = specialKeys[key] || key
        }
        
        // Solo agregar la tecla si no es un modificador
        if (key && !['', 'Control', 'Alt', 'Shift', 'Meta'].includes(key)) {
          newShortcut.push(key)
        }

        // Solo registrar si tenemos una combinación válida
        if (newShortcut.length > 1 || (newShortcut.length === 1 && !['CommandOrControl', 'Alt', 'Shift'].includes(newShortcut[0]))) {
          currentShortcut = newShortcut.join('+')
          console.log('Registering new shortcut:', currentShortcut)
          mainWindow.webContents.send('shortcut-recorded', currentShortcut)
          isRecordingShortcut = false
          registerGlobalShortcuts()
        }
      }
    })
  }

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

