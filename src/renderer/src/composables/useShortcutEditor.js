import { ref, onMounted, onUnmounted } from 'vue'

export function useShortcutEditor() {
  const isRecording = ref(false)
  const currentShortcut = ref('CommandOrControl+Space')

  const startRecording = () => {
    isRecording.value = true
    window.electron.ipcRenderer.send('start-shortcut-recording')
  }

  const stopRecording = () => {
    isRecording.value = false
    window.electron.ipcRenderer.send('stop-shortcut-recording')
  }

  onMounted(() => {
    window.electron.ipcRenderer.on('shortcut-recorded', (shortcut) => {
      currentShortcut.value = shortcut
      isRecording.value = false
    })

    window.electron.ipcRenderer.on('current-shortcut', (shortcut) => {
      currentShortcut.value = shortcut
    })
  })

  onUnmounted(() => {
    window.electron.ipcRenderer.removeAllListeners('shortcut-recorded')
    window.electron.ipcRenderer.removeAllListeners('current-shortcut')
  })

  return {
    isRecording,
    currentShortcut,
    startRecording,
    stopRecording
  }
}
