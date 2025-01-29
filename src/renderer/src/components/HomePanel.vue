<script setup>
import { Mic, Square } from 'lucide-vue-next'
import { ref, defineEmits } from 'vue'

defineProps({
  shortcut: {
    type: String,
    required: true
  },
  isRecording: {
    type: Boolean,
    required: true
  },
  isLoading: {
    type: Boolean,
    required: true
  },
  modelValue: {
    type: String,
    required: true
  },
  aiProcessedText: {
    type: String,
    required: true
  }
})

const copiedStates = ref({
  transcription: false,
  ai: false
})

async function copyToClipboard(text, type) {
  try {
    await navigator.clipboard.writeText(text)
    copiedStates.value[type] = true
    setTimeout(() => {
      copiedStates.value[type] = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}

defineEmits(['toggle-recording'])
</script>

<template>
  <div class="flex gap-4">
    <!-- Recording button -->
    <div class="flex items-center">
      <button
        class="relative transition-all duration-200 focus:outline-none shrink-0 flex items-center justify-center w-16 h-16 rounded-full"
        :class="{
          'bg-red-500': isRecording,
          'bg-[#007AFF]': !isRecording,
          'opacity-70': isLoading
        }"
        :disabled="isLoading"
        @click="$emit('toggle-recording')"
      >
        <div class="absolute inset-0 flex items-center justify-center">
          <div
            v-if="isLoading"
            class="w-8 h-8 border-4 border-white border-t-transparent rounded-full animate-spin"
          ></div>
          <template v-else>
            <Mic v-if="!isRecording" class="w-8 h-8 text-white" />
            <Square v-else class="w-6 h-6 text-white" />
          </template>
        </div>
      </button>
    </div>

    <!-- Text area -->
    <div class="flex flex-col gap-3 w-full">
      <!-- Transcription box -->
      <div class="flex items-center justify-between p-2 bg-white rounded-lg">
        <span class="text-sm font-medium">Transcription</span>
        <button
          class="text-sm text-[#1d1d1f] hover:bg-[#e5e5e7] px-2 py-1 rounded-lg flex items-center gap-1"
          @click="copyToClipboard(modelValue, 'transcription')"
        >
          <span v-if="!copiedStates.transcription">Copy</span>
          <span v-else class="text-green-600">✓ Copied</span>
        </button>
      </div>

      <!-- AI Process box -->
      <div class="flex items-center justify-between p-2 bg-white rounded-lg">
        <span class="text-sm font-medium">Processed</span>
        <button
          class="text-sm text-[#1d1d1f] hover:bg-[#e5e5e7] px-2 py-1 rounded-lg flex items-center gap-1"
          @click="copyToClipboard(aiProcessedText, 'ai')"
        >
          <span v-if="!copiedStates.ai">Copy</span>
          <span v-else class="text-green-600">✓ Copied</span>
        </button>
      </div>
    </div>
  </div>

  <!-- Shortcut info -->
  <div class="text-sm text-gray-500 text-center">
    <kbd class="px-2 py-1 mr-1 bg-white rounded-lg shadow-sm">
      {{ shortcut }}
    </kbd>
    to start/stop recording.
  </div>
</template>
