<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import ShortcutEditor from './ShortcutEditor.vue'

const isRecording = ref(false)
const mediaRecorder = ref(null)
const audioChunks = ref([])
const transcription = ref('')
const editableText = ref('')
const apiKey = 'UmZq7RrONiR8gkPj8PPVeUKvfdx4Vs51' // Asegúrate de tener tu API key aquí
const errorMessage = ref('')
const isLoading = ref(false)
const soundEnabled = ref(true) // Nueva ref para controlar el sonido
const alwaysOnTop = ref(false) // Nueva ref para el estado de siempre visible
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

const startRecording = async () => {
  try {
    errorMessage.value = ''
    audioChunks.value = []
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

    mediaRecorder.value = new MediaRecorder(stream)

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
        errorMessage.value = 'Error al procesar el audio: ' + error.message
        console.error('Error processing audio:', error)
      } finally {
        isLoading.value = false
      }
    }

    mediaRecorder.value.start(1000)
    isRecording.value = true
    playSound(startSound)
    // Notificar al proceso principal
    window.electron.ipcRenderer.send('recording-status-changed', true)
  } catch (error) {
    errorMessage.value = 'Error al acceder al micrófono: ' + error.message
    console.error('Error accessing microphone:', error)
  }
}

const stopRecording = () => {
  if (mediaRecorder.value && isRecording.value) {
    mediaRecorder.value.stop()
    mediaRecorder.value.stream.getTracks().forEach((track) => track.stop())
    isRecording.value = false
    playSound(stopSound)
    // Notificar al proceso principal
    window.electron.ipcRenderer.send('recording-status-changed', false)
  }
}

const sendToWhisper = async (audioBlob) => {
  const formData = new FormData()
  formData.append('file', audioBlob, 'recording.webm')
  formData.append('language', 'spanish')
  formData.append('response_format', 'json')

  try {
    errorMessage.value = ''
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
    errorMessage.value = 'Error en la transcripción: ' + error.message
    console.error('Error en la transcripción:', error)
  }
}

// Función para alternar la grabación
const toggleRecording = () => {
  console.log('Toggle recording called, current state:', isRecording.value) // Debug log
  if (isRecording.value) {
    stopRecording()
  } else {
    startRecording()
  }
}

// Notificar al proceso principal sobre cambios en el estado de grabación
watch(isRecording, (newValue) => {
  window.electron.ipcRenderer.send('recording-status-changed', newValue)
})

// Notificar al proceso principal sobre cambios en el estado de sonido
watch(soundEnabled, (newValue) => {
  window.electron.ipcRenderer.send('set-sound-enabled', newValue)
})

// Escuchar el evento desde el proceso principal
onMounted(() => {
  console.log('Component mounted, setting up listeners')
  window.electron.ipcRenderer.on('toggle-recording', () => {
    console.log('Toggle recording event received')
    if (!isLoading.value) {
      toggleRecording()
    }
  })

  window.electron.ipcRenderer.on('start-recording-hotkey', () => {
    console.log('Hotkey event received') // Debug log
    toggleRecording()
  })

  window.electron.ipcRenderer.on('sound-enabled-changed', (value) => {
    soundEnabled.value = value
  })

  window.electron.ipcRenderer.on('current-shortcut', (shortcut) => {
    currentShortcut.value = shortcut
  })

  // Enviar estado inicial de sonidos
  window.electron.ipcRenderer.send('set-sound-enabled', soundEnabled.value)

  // Solicitar el estado actual de alwaysOnTop al proceso principal
  window.electron.ipcRenderer.send('set-always-on-top', alwaysOnTop.value)
})

// Limpiar los listeners cuando el componente se desmonta
onUnmounted(() => {
  window.electron.ipcRenderer.removeAllListeners('toggle-recording')
  window.electron.ipcRenderer.removeAllListeners('start-recording-hotkey')
  window.electron.ipcRenderer.removeAllListeners('sound-enabled-changed')
})
</script>

<template>
  <div class="audio-recorder">
    <div class="status-indicator" :class="{ recording: isRecording }">
      {{ isRecording ? 'Grabando...' : 'Listo para grabar' }}
    </div>

    <div class="controls">
      <button @click="toggleRecording" :class="{ recording: isRecording }">
        {{ isRecording ? 'Detener Grabación' : 'Iniciar Grabación' }}
      </button>
    </div>

    <div v-if="isLoading" class="loading">Procesando audio...</div>

    <div v-if="errorMessage" class="error">
      {{ errorMessage }}
    </div>

    <div v-if="transcription" class="transcription-container">
      <h3>Transcripción:</h3>
      <textarea
        v-model="editableText"
        class="transcription-input"
        rows="5"
        placeholder="La transcripción aparecerá aquí..."
      ></textarea>
    </div>

    <div class="shortcut-hint">
      Presiona <kbd>{{ currentShortcut }}</kbd> para {{ isRecording ? 'detener' : 'iniciar' }} la
      grabación
    </div>
    <ShortcutEditor />
  </div>
</template>

<style scoped>
.audio-recorder {
  padding: 20px;
  text-align: center;
}

.status-indicator {
  margin-bottom: 20px;
  padding: 10px;
  border-radius: 5px;
  background-color: #f0f0f0;
}

.status-indicator.recording {
  background-color: #ff4444;
  color: white;
  animation: pulse 2s infinite;
}

.controls button {
  padding: 10px 20px;
  font-size: 16px;
  border: none;
  border-radius: 5px;
  background-color: #4caf50;
  color: white;
  cursor: pointer;
  transition: background-color 0.3s;
}

.controls button:hover {
  background-color: #45a049;
}

.controls button.recording {
  background-color: #ff4444;
}

.controls button.recording:hover {
  background-color: #ff3333;
}

.loading {
  margin-top: 20px;
  color: #666;
}

.error {
  margin-top: 20px;
  color: #ff4444;
}

.shortcut-hint {
  margin-top: 20px;
  color: #666;
  font-size: 0.9em;
}

kbd {
  background-color: #f7f7f7;
  border: 1px solid #ccc;
  border-radius: 3px;
  box-shadow: 0 1px 0 rgba(0, 0, 0, 0.2);
  color: #333;
  display: inline-block;
  font-size: 0.85em;
  padding: 2px 4px;
  margin: 0 2px;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
  100% {
    opacity: 1;
  }
}

.transcription-container {
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f5f5;
  border-radius: 5px;
}

.transcription-input {
  width: 90%;
  max-width: 600px;
  margin: 10px auto;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 16px;
  line-height: 1.5;
  resize: vertical;
}

h3 {
  margin-bottom: 10px;
  color: #2c3e50;
}
</style>
