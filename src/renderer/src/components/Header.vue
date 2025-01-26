<script setup>
import { Settings } from 'lucide-vue-next'

defineProps({
  selectedProfile: {
    type: String,
    required: true
  }
})

defineEmits(['update:selectedProfile', 'toggleSettings'])
</script>

<template>
  <header class="flex justify-between items-center">
    <div>
      <h1 class="text-3xl font-semibold">Dicto</h1>
      <p class="mt-1 text-[#86868b]">Instantly convert your voice to text</p>
    </div>
    <div class="flex items-center space-x-4">
      <button
        class="py-2 px-4 text-sm flex items-center gap-2 rounded-full bg-white shadow-md hover:shadow-xl transition-colors"
        @click="$emit('toggleSettings')"
      >
        <Settings class="w-5 h-5 text-[#1d1d1f]" />
        Settings
      </button>
    </div>
  </header>
</template>
