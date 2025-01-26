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
  <div class="flex flex-col items-center space-y-4 py-6">
    <button
      :class="{
        'px-6 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 focus:outline-none': true,
        'bg-gray-50 hover:bg-gray-100 text-gray-700 ': !isRecording,
        'bg-red-50 text-red-500 animate-pulse': isRecording
      }"
      @click="isRecording ? stopRecording() : startRecording()"
    >
      {{ isRecording ? 'Press desired keys...' : 'Change Shortcut' }}
    </button>
    <div class="text-sm text-gray-500">
      Current shortcut:
      <kbd
        class="px-2 py-1 text-xs font-medium bg-white border border-gray-200 rounded-lg shadow-sm text-gray-700 inline-flex items-center ml-1"
      >
        {{ currentShortcut }}
      </kbd>
    </div>
  </div>
</template>
