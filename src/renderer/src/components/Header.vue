<script setup>
import { Settings, UserPen, ChevronDown } from 'lucide-vue-next'
import { ref } from 'vue'

defineProps({
  profiles: {
    type: Array,
    required: true
  },
  selectedProfile: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['profileChange', 'toggleSettings', 'toggleProfiles'])

const isDropdownOpen = ref(false)

function toggleDropdown() {
  isDropdownOpen.value = !isDropdownOpen.value
}

function selectProfile(profileName) {
  emit('profileChange', profileName)
  isDropdownOpen.value = false
}
</script>

<template>
  <header class="flex items-center justify-between">
    <h1 class="text-3xl font-bold">Dicto</h1>
    <div class="flex items-center space-x-2">
      <div class="relative">
        <button
          class="flex items-center w-32 justify-between space-x-2 px-3 py-1.5 rounded-lg bg-[#e5e5e7] text-sm hover:bg-[#d5d5d7] focus:outline-none"
          @click="toggleDropdown"
        >
          <span>{{ selectedProfile }}</span>
          <ChevronDown
            class="h-4 w-4 transition-transform duration-200"
            :class="{ 'rotate-180': isDropdownOpen }"
          />
        </button>
        <div
          v-if="isDropdownOpen"
          class="absolute mt-1 w-48 rounded-xl bg-white shadow-lg p-1 space-y-1 z-10"
        >
          <button
            v-for="profile in profiles"
            :key="profile.name"
            class="w-full px-4 py-2 rounded-lg text-left text-sm hover:bg-[#e5e5e7]"
            :class="{ 'bg-[#e5e5e7]': profile.name === selectedProfile }"
            @click="selectProfile(profile.name)"
          >
            {{ profile.name }}
          </button>
        </div>
      </div>
      <button
        class="p-2 rounded-full hover:bg-[#e5e5e7] text-[#1d1d1f]"
        title="Manage Profiles"
        @click="$emit('toggleProfiles')"
      >
        <UserPen class="h-5 w-5" />
      </button>
      <button
        class="p-2 rounded-full hover:bg-[#e5e5e7] text-[#1d1d1f]"
        title="Settings"
        @click="$emit('toggleSettings')"
      >
        <Settings class="h-5 w-5" />
      </button>
    </div>
  </header>
</template>
