import { ref, onMounted, onUnmounted, watch } from 'vue'

export function useAudioRecorder() {
  const isRecording = ref(false)
  const mediaRecorder = ref(null)
  const audioChunks = ref([])
  const transcription = ref('')
  const editableText = ref('')
  const apiKey = 'UmZq7RrONiR8gkPj8PPVeUKvfdx4Vs51'
  const errorMessage = ref('')
  const isLoading = ref(false)
  const soundEnabled = ref(true)
  const alwaysOnTop = ref(false)
  const currentShortcut = ref('CommandOrControl+Space')

  // Crear elementos de audio
  const startSound = new Audio('/src/assets/start-recording.mp3')
  const stopSound = new Audio('/src/assets/stop-recording.mp3')

  const playSound = (sound) => {
    if (soundEnabled.value) {
      sound.play().catch((error) => {
        console.error('Error playing sound:', error)
      })
    }
  }

  const handleRecordingError = (error, context) => {
    errorMessage.value = `Error ${context}: ${error.message}`
    console.error(`Error ${context}:`, error)
    isLoading.value = false
  }

  const startRecording = async () => {
    try {
      errorMessage.value = ''
      audioChunks.value = []
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      mediaRecorder.value = new MediaRecorder(stream)
      setupMediaRecorderEvents()

      mediaRecorder.value.start(1000)
      isRecording.value = true
      playSound(startSound)
      window.electron.ipcRenderer.send('recording-status-changed', true)
    } catch (error) {
      handleRecordingError(error, 'al acceder al micrófono')
    }
  }

  const setupMediaRecorderEvents = () => {
    mediaRecorder.value.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.value.push(event.data)
      }
    }

    mediaRecorder.value.onstop = async () => {
      try {
        isLoading.value = true
        const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' })
        await sendToWhisper(audioBlob)
      } catch (error) {
        handleRecordingError(error, 'al procesar el audio')
      }
    }
  }

  const stopRecording = () => {
    if (mediaRecorder.value && isRecording.value) {
      mediaRecorder.value.stop()
      mediaRecorder.value.stream.getTracks().forEach((track) => track.stop())
      isRecording.value = false
      playSound(stopSound)
      window.electron.ipcRenderer.send('recording-status-changed', false)
    }
  }

  const sendToWhisper = async (audioBlob) => {
    const formData = new FormData()
    formData.append('file', audioBlob, 'recording.webm')
    formData.append('language', 'spanish')
    formData.append('response_format', 'json')

    try {
      const response = await fetch('https://api.lemonfox.ai/v1/audio/transcriptions', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${apiKey}`
        },
        body: formData
      })

      if (!response.ok) {
        throw new Error(`Error en la transcripción: ${response.status}`)
      }

      const data = await response.json()
      console.log('Transcripción:', data)
      transcription.value = data.text
      editableText.value = data.text
    } catch (error) {
      handleRecordingError(error, 'en la transcripción')
    } finally {
      isLoading.value = false
    }
  }

  const toggleRecording = () => {
    console.log('Toggle recording called, current state:', isRecording.value)
    if (isRecording.value) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  // Watchers y event listeners
  watch(isRecording, (newValue) => {
    window.electron.ipcRenderer.send('recording-status-changed', newValue)
  })

  watch(soundEnabled, (newValue) => {
    window.electron.ipcRenderer.send('set-sound-enabled', newValue)
  })

  onMounted(() => {
    console.log('Component mounted, setting up listeners')
    const setupEventListeners = () => {
      window.electron.ipcRenderer.on('toggle-recording', () => {
        console.log('Toggle recording event received')
        if (!isLoading.value) {
          toggleRecording()
        }
      })

      window.electron.ipcRenderer.on('start-recording-hotkey', () => {
        console.log('Hotkey event received')
        toggleRecording()
      })

      window.electron.ipcRenderer.on('sound-enabled-changed', (value) => {
        soundEnabled.value = value
      })

      window.electron.ipcRenderer.on('current-shortcut', (shortcut) => {
        currentShortcut.value = shortcut
      })
    }

    setupEventListeners()
    window.electron.ipcRenderer.send('set-sound-enabled', soundEnabled.value)
    window.electron.ipcRenderer.send('set-always-on-top', alwaysOnTop.value)
  })

  onUnmounted(() => {
    window.electron.ipcRenderer.removeAllListeners('toggle-recording')
    window.electron.ipcRenderer.removeAllListeners('start-recording-hotkey')
    window.electron.ipcRenderer.removeAllListeners('sound-enabled-changed')
  })

  return {
    isRecording,
    isLoading,
    errorMessage,
    transcription,
    editableText,
    currentShortcut,
    soundEnabled,
    toggleRecording
  }
}
