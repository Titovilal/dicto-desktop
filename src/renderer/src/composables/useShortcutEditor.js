import { ref, onMounted, onUnmounted } from 'vue'

export function useShortcutEditor() {
  const isRecording = ref(false)
  const currentShortcut = ref('CommandOrControl+Space')
  let toggleCallback = null

  const startRecording = () => {
    isRecording.value = true
    window.electron.ipcRenderer.send('start-shortcut-recording')
  }

  const stopRecording = () => {
    isRecording.value = false
    window.electron.ipcRenderer.send('stop-shortcut-recording')
  }

  const setToggleCallback = (callback) => {
    toggleCallback = callback
  }

  onMounted(() => {
    window.electron.ipcRenderer.on('shortcut-recorded', (shortcut) => {
      currentShortcut.value = shortcut
      isRecording.value = false
    })

    window.electron.ipcRenderer.on('current-shortcut', (shortcut) => {
      currentShortcut.value = shortcut
    })

    window.electron.ipcRenderer.on('toggle-recording', () => {
      if (toggleCallback) toggleCallback()
    })

    window.electron.ipcRenderer.on('start-recording-hotkey', () => {
      if (toggleCallback) toggleCallback()
    })

    window.electron.ipcRenderer.send('get-current-shortcut')
  })

  onUnmounted(() => {
    window.electron.ipcRenderer.removeAllListeners('shortcut-recorded')
    window.electron.ipcRenderer.removeAllListeners('current-shortcut')
    window.electron.ipcRenderer.removeAllListeners('toggle-recording')
    window.electron.ipcRenderer.removeAllListeners('start-recording-hotkey')
  })

  return {
    isRecording,
    currentShortcut,
    startRecording,
    stopRecording,
    setToggleCallback
  }
}
