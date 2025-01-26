<script setup>
import { Settings } from 'lucide-vue-next'

defineProps({
  selectedProfile: {
    type: String,
    required: true
  }
})

defineEmits(['update:selectedProfile', 'toggleSettings', 'toggleProfiles'])
</script>

<template>
  <header class="flex items-center justify-between">
    <div class="flex items-center space-x-4">
      <h1 class="text-2xl font-bold">Dicto</h1>
      <div class="text-sm text-[#86868b]">{{ selectedProfile }}</div>
    </div>
    <div class="flex items-center space-x-2">
      <button
        @click="$emit('toggleProfiles')"
        class="p-2 rounded-full hover:bg-[#e5e5e7] text-[#1d1d1f]"
        title="Manage Profiles"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-5 w-5"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"
          />
        </svg>
      </button>
      <button
        @click="$emit('toggleSettings')"
        class="p-2 rounded-full hover:bg-[#e5e5e7] text-[#1d1d1f]"
        title="Settings"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-5 w-5"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fill-rule="evenodd"
            d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z"
            clip-rule="evenodd"
          />
        </svg>
      </button>
    </div>
  </header>
</template>
