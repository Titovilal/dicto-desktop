<script setup>
import { ref } from 'vue'
import { Copy, Check, ChevronUp, ChevronDown } from 'lucide-vue-next'

defineProps({
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

const transcriptionCollapsed = ref(false)
const aiTextCollapsed = ref(false)

const toggleTranscription = () => {
  transcriptionCollapsed.value = !transcriptionCollapsed.value
}

const toggleAIText = () => {
  aiTextCollapsed.value = !aiTextCollapsed.value
}
</script>

<template>
  <div class="w-full flex flex-col flex-grow bg-white rounded-2xl p-6 shadow-sm mb-6">
    <div class="flex justify-between items-center mb-4">
      <div class="flex items-center gap-2">
        <button
          class="cursor-pointer px-2 py-1 flex items-center gap-2 rounded-full hover:bg-gray-50 transition-colors"
          @click="toggleTranscription"
        >
          <h3 class="text-base font-medium text-[#1d1d1f]">Transcription</h3>
          <ChevronUp v-if="!transcriptionCollapsed" class="w-4 h-4 text-[#86868b]" />
          <ChevronDown v-else class="w-4 h-4 text-[#86868b]" />
        </button>
      </div>
      <button
        class="cursor-pointer p-2 rounded-full hover:bg-gray-50 transition-colors"
        :title="showCopied ? 'Copied!' : 'Copy to clipboard'"
        @click="copyToClipboard(modelValue, showCopied)"
      >
        <Check v-if="showCopied" class="w-5 h-5 text-green-600" />
        <Copy v-else class="w-5 h-5 text-[#86868b]" />
      </button>
    </div>
    <textarea
      v-show="!transcriptionCollapsed"
      class="w-full flex-grow p-4 rounded-xl bg-[#f5f5f7] border-0 transition-colors duration-200 resize-none text-[#1d1d1f] placeholder-[#86868b]"
      :value="modelValue"
      readonly
      placeholder="Start recording or type here..."
      @input="$emit('update:modelValue', $event.target.value)"
    ></textarea>

    <!-- AI Processed Text -->
    <div class="mt-6">
      <div class="flex justify-between items-center mb-4">
        <div class="flex items-center gap-2">
          <button
            class="cursor-pointer px-2 py-1 flex items-center gap-2 rounded-full hover:bg-gray-50 transition-colors"
            @click="toggleAIText"
          >
            <h3 class="text-base font-medium text-[#1d1d1f]">AI Processed Text</h3>
            <ChevronUp v-if="!aiTextCollapsed" class="w-4 h-4 text-[#86868b]" />
            <ChevronDown v-else class="w-4 h-4 text-[#86868b]" />
          </button>
        </div>
        <button
          class="cursor-pointer p-2 rounded-full hover:bg-gray-50 transition-colors"
          :title="showAICopied ? 'Copied!' : 'Copy to clipboard'"
          @click="copyToClipboard(aiProcessedText, showAICopied)"
        >
          <Check v-if="showAICopied" class="w-5 h-5 text-green-600" />
          <Copy v-else class="w-5 h-5 text-[#86868b]" />
        </button>
      </div>
      <textarea
        v-show="!aiTextCollapsed"
        class="w-full flex-grow p-4 rounded-xl bg-[#f5f5f7] border-0 transition-colors duration-200 resize-none text-[#1d1d1f] placeholder-[#86868b]"
        :value="aiProcessedText"
        readonly
        placeholder="AI processed text will appear here..."
      ></textarea>
    </div>
  </div>
</template>
