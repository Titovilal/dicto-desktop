<script setup>
import { ref } from 'vue'
import { Copy, Check } from 'lucide-vue-next'

defineProps({
  modelValue: {
    type: String,
    required: true
  }
})

defineEmits(['update:modelValue'])

const showCopied = ref(false)

const copyToClipboard = async () => {
  await navigator.clipboard.writeText(props.modelValue)
  showCopied.value = true
  setTimeout(() => {
    showCopied.value = false
  }, 2000)
}
</script>

<template>
  <div class="w-full flex flex-col flex-grow bg-white rounded-2xl p-6 shadow-sm mb-6">
    <div class="flex justify-between items-center mb-4">
      <h3 class="text-base font-medium text-[#1d1d1f]">Transcription</h3>
      <button
        class="p-2 rounded-full hover:bg-gray-50 transition-colors"
        :title="showCopied ? 'Copied!' : 'Copy to clipboard'"
        @click="copyToClipboard"
      >
        <Check v-if="showCopied" class="w-5 h-5 text-green-600" />
        <Copy v-else class="w-5 h-5 text-[#86868b]" />
      </button>
    </div>
    <textarea
      :value="modelValue"
      @input="$emit('update:modelValue', $event.target.value)"
      class="w-full flex-grow p-4 rounded-xl bg-[#f5f5f7] border-0 transition-colors duration-200 resize-none text-[#1d1d1f] placeholder-[#86868b]"
      placeholder="Start recording or type here..."
    ></textarea>
  </div>
</template>
