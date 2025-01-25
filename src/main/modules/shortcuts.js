import { globalShortcut } from 'electron'

let currentShortcut = 'CommandOrControl+Space'
let isRecordingShortcut = false

export function registerGlobalShortcuts(mainWindow) {
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

export function unregisterGlobalShortcuts() {
  globalShortcut.unregisterAll()
}

export function startShortcutRecording() {
  isRecordingShortcut = true
  unregisterGlobalShortcuts()
}

export function stopShortcutRecording() {
  isRecordingShortcut = false
}

export function getCurrentShortcut() {
  return currentShortcut
}

export function isRecordingShortcuts() {
  return isRecordingShortcut
}

export function handleKeyboardEvent(input) {
  if (!isRecordingShortcut) return null

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
      console.log('New shortcut recorded:', currentShortcut)
      return currentShortcut
    }
  }
  
  return null
} 