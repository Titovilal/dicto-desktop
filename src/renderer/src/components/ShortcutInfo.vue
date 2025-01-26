<script setup>
defineProps({
  shortcut: {
    type: String,
    required: true
  },
  isRecording: {
    type: Boolean,
    required: true
  }
})
</script>

<template>
  <div class="text-sm text-[#86868b] text-center">
    Press
    <kbd
      class="px-2 py-1 text-xs font-medium bg-white rounded-lg shadow-sm text-[#1d1d1f] inline-flex items-center"
    >
      {{ shortcut }}
    </kbd>
    to {{ isRecording ? 'stop' : 'start' }} recording
  </div>
</template>
