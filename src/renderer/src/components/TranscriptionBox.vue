<script setup>
defineProps({
  modelValue: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <div class="w-full space-y-4 bg-gray-50 rounded-2xl p-6">
    <h3 class="text-base font-medium text-gray-900">Transcription</h3>
    <textarea
      :value="modelValue"
      class="w-full min-h-[160px] p-4 rounded-xl bg-white border-0 transition-all duration-200 resize-y text-gray-700 placeholder-gray-400 shadow-sm"
      placeholder="Your transcription will appear here..."
      @input="emit('update:modelValue', $event.target.value)"
    ></textarea>
  </div>
</template>
