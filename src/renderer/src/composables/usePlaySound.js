import { ref, onMounted, onUnmounted } from 'vue'

export function usePlaySound() {
  const soundEnabled = ref(true)

  const startSound = new Audio('/src/assets/start-recording.mp3')
  const stopSound = new Audio('/src/assets/stop-recording.mp3')
  const finishSound = new Audio('/src/assets/finish-processing.mp3')

  const playSound = (sound) => {
    if (soundEnabled.value) {
      sound.play().catch((error) => {
        console.error('Error playing sound:', error)
      })
    }
  }
  const playStartSound = () => {
    playSound(startSound)
  }

  const playStopSound = () => {
    playSound(stopSound)
  }

  const playFinishSound = () => {
    playSound(finishSound)
  }

  onMounted(() => {
    window.electron.ipcRenderer.on('sound-enabled-changed', (value) => {
      soundEnabled.value = value
    })
    window.electron.ipcRenderer.send('set-sound-enabled', soundEnabled.value)
  })

  onUnmounted(() => {
    window.electron.ipcRenderer.removeAllListeners('sound-enabled-changed')
  })

  const setSoundEnabled = (value) => {
    soundEnabled.value = value
    window.electron.ipcRenderer.send('set-sound-enabled', value)
  }

  return {
    soundEnabled,
    setSoundEnabled,
    playStartSound,
    playStopSound,
    playFinishSound
  }
}
