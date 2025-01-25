import { ipcMain } from 'electron'
import { updateTrayTooltip, updateSoundMenuItem } from './tray'
import { 
  startShortcutRecording, 
  stopShortcutRecording, 
  registerGlobalShortcuts,
  handleKeyboardEvent
} from './shortcuts'

export function setupIPC(mainWindow) {
  // Test IPC
  ipcMain.on('ping', () => console.log('pong'))

  // Recording status
  ipcMain.on('recording-status-changed', (_, isRecording) => {
    updateTrayTooltip(isRecording)
  })

  // Always on top
  ipcMain.on('set-always-on-top', (_, value) => {
    if (mainWindow) {
      mainWindow.setAlwaysOnTop(value)
      mainWindow.webContents.send('always-on-top-changed', mainWindow.isAlwaysOnTop())
    }
  })

  // Sound settings
  ipcMain.on('set-sound-enabled', (_, value) => {
    updateSoundMenuItem(value)
  })

  // Shortcut recording
  ipcMain.on('start-shortcut-recording', () => {
    startShortcutRecording()
  })

  ipcMain.on('stop-shortcut-recording', () => {
    stopShortcutRecording()
    registerGlobalShortcuts(mainWindow)
  })

  // Keyboard event handling for shortcuts
  if (mainWindow) {
    mainWindow.webContents.on('before-input-event', (event, input) => {
      const newShortcut = handleKeyboardEvent(input)
      if (newShortcut) {
        mainWindow.webContents.send('shortcut-recorded', newShortcut)
        stopShortcutRecording()
        registerGlobalShortcuts(mainWindow)
      }
    })
  }

  // Always on top sync
  mainWindow.on('always-on-top-changed', (event, isOnTop) => {
    mainWindow.webContents.send('always-on-top-changed', isOnTop)
  })
} 