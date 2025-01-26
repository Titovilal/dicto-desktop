<script setup>
defineProps({
  isRecording: {
    type: Boolean,
    required: true
  }
})

const emit = defineEmits(['toggle'])
</script>

<template>
  <div class="w-full space-y-6">
    <button
      :class="{
        'w-full py-3 px-8 rounded-2xl font-medium text-base transition-all duration-200 focus:outline-none': true,
        'bg-blue-500 hover:bg-blue-600 text-white': !isRecording,
        'bg-red-500 hover:bg-red-600 text-white': isRecording
      }"
      @click="emit('toggle')"
    >
      {{ isRecording ? 'Stop Recording' : 'Start Recording' }}
    </button>
  </div>
</template>
