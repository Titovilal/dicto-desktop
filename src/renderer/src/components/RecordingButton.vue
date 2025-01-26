<script setup>
import { Loader2 } from 'lucide-vue-next'

defineProps({
  isLoading: {
    type: Boolean,
    required: true
  },
  isRecording: {
    type: Boolean,
    required: true
  }
})

defineEmits(['toggleRecording'])
</script>

<template>
  <div class="w-full mb-6">
    <button
      :disabled="isLoading"
      :class="{
        'w-full py-3 px-8 rounded-2xl font-medium text-base transition-all duration-200 focus:outline-none shadow-sm flex items-center justify-center gap-2': true,
        'bg-[#0066cc] hover:bg-[#0077ed] text-white': !isRecording && !isLoading,
        'bg-red-500 hover:bg-red-600 text-white': isRecording && !isLoading,
        'bg-gray-400 cursor-not-allowed': isLoading
      }"
      @click="$emit('toggleRecording')"
    >
      <Loader2 v-if="isLoading" class="animate-spin h-5 w-5" />
      <span>{{
        isLoading ? 'Processing audio...' : isRecording ? 'Stop Recording' : 'Start Recording'
      }}</span>
    </button>
  </div>
</template>
