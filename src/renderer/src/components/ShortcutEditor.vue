<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

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
</script>

<template>
  <div class="shortcut-editor">
    <button
      @click="isRecording ? stopRecording() : startRecording()"
      :class="{ recording: isRecording }"
    >
      {{ isRecording ? 'Presiona las teclas deseadas...' : 'Cambiar atajo' }}
    </button>
    <div class="current-shortcut">
      Atajo actual: <kbd>{{ currentShortcut }}</kbd>
    </div>
  </div>
</template>

<style scoped>
.shortcut-editor {
  margin: 20px 0;
  text-align: center;
}

button {
  padding: 10px 20px;
  font-size: 14px;
  border: none;
  border-radius: 5px;
  background-color: #4caf50;
  color: white;
  cursor: pointer;
  transition: background-color 0.3s;
}

button:hover {
  background-color: #45a049;
}

button.recording {
  background-color: #ff4444;
  animation: pulse 2s infinite;
}

.current-shortcut {
  margin-top: 10px;
  color: #666;
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
</style>
