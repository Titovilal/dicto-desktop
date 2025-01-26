<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import ShortcutEditor from './ShortcutEditor.vue'
import RecordingStatus from './RecordingStatus.vue'
import TranscriptionBox from './TranscriptionBox.vue'
import { Loader2 } from 'lucide-vue-next'

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
    // Notificar al proceso principal
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
  const setupEventListeners = () => {
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
  }

  setupEventListeners()

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
  <div class="flex flex-col items-center space-y-6">
    <RecordingStatus :is-recording="isRecording" @toggle="toggleRecording" />

    <div v-if="isLoading" class="flex items-center justify-center space-x-2 text-gray-600">
      <Loader2 class="animate-spin h-5 w-5" />
      <span>Processing audio...</span>
    </div>

    <div
      v-if="errorMessage"
      class="w-full p-4 rounded-lg bg-red-50 text-red-600 text-sm"
      role="alert"
    >
      {{ errorMessage }}
    </div>

    <TranscriptionBox v-if="transcription" v-model="editableText" />

    <div class="text-sm text-gray-500">
      Press
      <kbd
        class="px-2 py-1 text-xs font-sans font-medium bg-gray-50 border border-gray-200 rounded-md shadow-sm text-gray-800 inline-flex items-center"
      >
        {{ currentShortcut }}
      </kbd>
      to {{ isRecording ? 'stop' : 'start' }} recording
    </div>

    <ShortcutEditor />
  </div>
</template>
