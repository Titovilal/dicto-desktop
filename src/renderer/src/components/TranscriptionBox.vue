<script setup>
import { ref } from 'vue'
import { Copy, Check } from 'lucide-vue-next'

const props = defineProps({
  modelValue: {
    type: String,
    required: true
  },
  aiProcessedText: {
    type: String,
    default: ''
  },
  showAIBox: {
    type: Boolean,
    default: false
  }
})

defineEmits(['update:modelValue'])

const showCopied = ref(false)
const showAICopied = ref(false)

const copyToClipboard = async (text, isCopied) => {
  await navigator.clipboard.writeText(text)
  isCopied.value = true
  setTimeout(() => {
    isCopied.value = false
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
        @click="copyToClipboard(modelValue, showCopied)"
      >
        <Check v-if="showCopied" class="w-5 h-5 text-green-600" />
        <Copy v-else class="w-5 h-5 text-[#86868b]" />
      </button>
    </div>
    <textarea
      class="w-full flex-grow p-4 rounded-xl bg-[#f5f5f7] border-0 transition-colors duration-200 resize-none text-[#1d1d1f] placeholder-[#86868b]"
      :value="modelValue"
      placeholder="Start recording or type here..."
      @input="$emit('update:modelValue', $event.target.value)"
    ></textarea>

    <!-- AI Processed Text -->
    <div class="mt-6">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-base font-medium text-[#1d1d1f]">AI Processed Text</h3>
        <button
          class="p-2 rounded-full hover:bg-gray-50 transition-colors"
          :title="showAICopied ? 'Copied!' : 'Copy to clipboard'"
          @click="copyToClipboard(aiProcessedText, showAICopied)"
        >
          <Check v-if="showAICopied" class="w-5 h-5 text-green-600" />
          <Copy v-else class="w-5 h-5 text-[#86868b]" />
        </button>
      </div>
      <textarea
        class="w-full h-32 p-4 rounded-xl bg-[#f5f5f7] border-0 transition-colors duration-200 resize-none text-[#1d1d1f] placeholder-[#86868b]"
        :value="aiProcessedText"
        readonly
        placeholder="AI processed text will appear here..."
      ></textarea>
    </div>
  </div>
</template>
