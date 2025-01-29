import { ref, onMounted } from 'vue'
import { usePlaySound } from './usePlaySound'
import { useShortcutEditor } from './useShortcutEditor'

export function useAudioRecorder() {
  const isRecording = ref(false)
  const mediaRecorder = ref(null)
  const audioChunks = ref([])
  const transcription = ref('')
  const editableText = ref('')
  const apiKey = 'UmZq7RrONiR8gkPj8PPVeUKvfdx4Vs51'
  const errorMessage = ref('')
  const isLoading = ref(false)
  const alwaysOnTop = ref(false)
  const aiProcessedText = ref('')

  const { playStartSound, playStopSound, playFinishSound, soundEnabled } = usePlaySound()
  const { currentShortcut } = useShortcutEditor() // Remove setToggleCallback

  const toggleRecording = () => {
    console.log('Toggle recording called, current state:', isRecording.value)
    if (isRecording.value) {
      stopRecording()
    } else {
      startRecording()
    }
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
      playStartSound()
    } catch (error) {
      handleRecordingError(error, 'accessing the microphone')
    }
  }
  const stopRecording = () => {
    if (mediaRecorder.value && isRecording.value) {
      mediaRecorder.value.stop()
      mediaRecorder.value.stream.getTracks().forEach((track) => track.stop())
      isRecording.value = false
      playStopSound()
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
        handleRecordingError(error, 'proccessing the audio')
      }
    }
  }

  const handleRecordingError = (error, context) => {
    errorMessage.value = `Error ${context}: ${error.message}`
    console.error(`Error ${context}:`, error)
    isLoading.value = false
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
      aiProcessedText.value = data.text
    } catch (error) {
      handleRecordingError(error, 'en la transcripción')
    } finally {
      isLoading.value = false
    }
  }

  onMounted(() => {
    console.log('Component mounted, setting up listeners')

    // Setup direct listeners for shortcut events
    window.electron.ipcRenderer.on('toggle-recording', () => {
      if (!isLoading.value) {
        toggleRecording()
      }
    })

    window.electron.ipcRenderer.on('start-recording-hotkey', () => {
      if (!isLoading.value) {
        toggleRecording()
      }
    })

    window.electron.ipcRenderer.send('set-always-on-top', alwaysOnTop.value)
  })

  return {
    isRecording,
    isLoading,
    errorMessage,
    transcription,
    editableText,
    currentShortcut,
    soundEnabled,
    toggleRecording,
    aiProcessedText,
    playFinishSound
  }
}
