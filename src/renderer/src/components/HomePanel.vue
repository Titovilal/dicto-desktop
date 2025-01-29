<script setup>
import { Mic, Square, Loader, Check, Copy } from 'lucide-vue-next'
import { ref, watch } from 'vue'

const props = defineProps({
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
  },
  isProcessing: {
    type: Boolean,
    required: true
  }
})

const timestamps = ref({
  transcription: '',
  ai: ''
})

// Actualizar timestamps automáticamente cuando cambian los valores
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue) {
      timestamps.value.transcription = new Date().toLocaleTimeString('en-US', { hour12: false })
    }
  }
)

watch(
  () => props.aiProcessedText,
  (newValue) => {
    if (newValue) {
      timestamps.value.ai = new Date().toLocaleTimeString('en-US', { hour12: false })
    }
  }
)

const copiedStates = ref({
  transcription: false,
  ai: false
})

async function copyToClipboard(text, type) {
  try {
    await navigator.clipboard.writeText(text)
    copiedStates.value[type] = true
    setTimeout(() => (copiedStates.value[type] = false), 2000)
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
        class="relative transition-all duration-200 shdow cursor-pointer focus:outline-none shrink-0 flex items-center justify-center w-16 h-16 rounded-full"
        :class="{
          'bg-red-600': isRecording,
          'bg-blue-500 hover:bg-blue-600 hover:shadow-xl': !isRecording,
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
            <Mic v-if="!isRecording" class="w-7 h-7 text-white" />
            <Square v-else class="w-7 h-7 text-white" />
          </template>
        </div>
      </button>
    </div>

    <!-- Text area -->
    <div class="flex flex-col gap-3 w-full">
      <!-- Transcription box -->
      <div
        class="flex items-center justify-between shadow p-2 rounded-lg"
        :class="{
          'bg-white': !isLoading,
          'bg-blue-50': isLoading
        }"
      >
        <span class="text-sm font-medium">Transcription</span>

        <div class="flex items-center gap-2">
          <template v-if="isLoading">
            <Loader class="w-4 h-4 animate-spin text-blue-500" />
          </template>
          <template v-else>
            <span v-if="timestamps.transcription" class="text-xs text-gray-500">
              {{ timestamps.transcription }}
            </span>
          </template>
          <button
            class="w-8 h-8 flex cursor-pointer items-center justify-center text-[#1d1d1f] hover:bg-[#e5e5e7] rounded-lg"
            @click="copyToClipboard(modelValue, 'transcription')"
          >
            <Check v-if="copiedStates.transcription" class="w-4 h-4 text-green-500" />
            <Copy v-else class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- AI Process box -->
      <div
        class="flex items-center justify-between shadow p-2 rounded-lg"
        :class="{
          'bg-white': !isProcessing,
          'bg-purple-50': isProcessing
        }"
      >
        <span class="text-sm font-medium">Processed</span>
        <div class="flex items-center gap-2">
          <template v-if="isProcessing">
            <Loader class="w-4 h-4 animate-spin text-purple-500" />
          </template>
          <template v-else>
            <span v-if="timestamps.ai" class="text-xs text-gray-500">
              {{ timestamps.ai }}
            </span>
          </template>
          <button
            class="w-8 h-8 flex cursor-pointer items-center justify-center text-[#1d1d1f] hover:bg-[#e5e5e7] rounded-lg"
            @click="copyToClipboard(aiProcessedText, 'ai')"
          >
            <Check v-if="copiedStates.ai" class="w-4 h-4 text-green-500" />
            <Copy v-else class="w-4 h-4" />
          </button>
        </div>
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
