<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useAudioRecorder } from './composables/useAudioRecorder'
import { useShortcutEditor } from './composables/useShortcutEditor'
import { useProfiles } from './composables/useProfiles'
import { useAI } from './composables/useAI'
import Header from './components/Header.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import ProfilePanel from './components/ProfilePanel.vue'
import RecordingButton from './components/RecordingButton.vue'
import TranscriptionBox from './components/TranscriptionBox.vue'
import ShortcutInfo from './components/ShortcutInfo.vue'

const showSettings = ref(false)
const showProfiles = ref(false)

// Initialize composables
const { profiles, selectedProfile, loadProfiles, setSelectedProfile } = useProfiles()

const {
  isRecording: audioIsRecording,
  isLoading: audioIsLoading,
  errorMessage,
  editableText,
  currentShortcut: audioCurrentShortcut,
  toggleRecording: toggleAudioRecording,
  playSound,
  finishSound
} = useAudioRecorder()

const {
  isRecording: shortcutIsRecording,
  currentShortcut,
  startRecording: startShortcutRecording,
  stopRecording: stopShortcutRecording
} = useShortcutEditor()

// AI setup
const { processWithAI } = useAI()
const aiProcessedText = ref('')

// Add the currentProfile computed property
const currentProfile = computed(() => profiles.value.find((p) => p.name === selectedProfile.value))

// Initialize profiles
onMounted(async () => {
  await loadProfiles()
  const savedProfile = await window.electron.ipcRenderer.invoke('get-selected-profile')
  selectedProfile.value = savedProfile
})

// Watch for profiles changes
watch(
  profiles,
  async (newProfiles) => {
    if (newProfiles.length > 0) {
      await loadProfiles()
    }
  },
  { deep: true }
)

const copyToClipboard = async (text) => {
  try {
    console.log('Copying to clipboard...')
    await navigator.clipboard.writeText(text)
    console.log('Copied to clipboard!')
  } catch (err) {
    console.error('Clipboard Copy Error:', err)
  }
}

// Watch for editableText changes
watch(editableText, async (newText) => {
  if (!newText) return

  // Get fresh profile data directly from profiles ref
  const profile = profiles.value.find((p) => p.name === selectedProfile.value)
  if (!profile) return

  if (profile.useAI) {
    console.log('Processing with AI...')
    try {
      const processedText = await processWithAI(newText, profile.prompt)
      if (processedText) {
        aiProcessedText.value = processedText
        if (profile.copyToClipboard) {
          await copyToClipboard(processedText)
        }
        playSound(finishSound)
      }
    } catch (error) {
      console.error('Error processing with AI:', error)
    }
  } else {
    aiProcessedText.value = ''
    if (profile.copyToClipboard) {
      await copyToClipboard(newText)
    }
    playSound(finishSound)
  }
})

// Handle profile change
async function handleProfileChange(newProfile) {
  await setSelectedProfile(newProfile)
  selectedProfile.value = newProfile
}

// Watch for selected profile changes
watch(selectedProfile, async (newProfile) => {
  if (newProfile) {
    await window.electron.ipcRenderer.invoke('set-selected-profile', newProfile)
  }
})
</script>

<template>
  <div class="h-screen flex flex-col bg-[#f5f5f7] text-[#1d1d1f]">
    <div class="flex flex-col flex-grow px-6 py-6">
      <Header
        :profiles="profiles"
        :selected-profile="selectedProfile"
        @profile-change="handleProfileChange"
        @toggle-settings="showSettings = !showSettings"
        @toggle-profiles="showProfiles = !showProfiles"
      />

      <main class="flex flex-col flex-grow mt-8">
        <SettingsPanel
          v-if="showSettings"
          :audio-current-shortcut="audioCurrentShortcut"
          :shortcut-is-recording="shortcutIsRecording"
          @start-recording="startShortcutRecording"
          @stop-recording="stopShortcutRecording"
        />

        <ProfilePanel v-else-if="showProfiles" v-model:selected-profile="selectedProfile" />

        <div v-else class="flex flex-col flex-grow">
          <RecordingButton
            :is-loading="audioIsLoading"
            :is-recording="audioIsRecording"
            @toggle-recording="toggleAudioRecording"
          />

          <div
            v-if="errorMessage"
            class="w-full p-4 rounded-2xl bg-red-50 text-red-600 text-sm mb-6"
            role="alert"
          >
            {{ errorMessage }}
          </div>

          <TranscriptionBox
            v-model="editableText"
            :ai-processed-text="aiProcessedText"
            :show-ai-box="!!currentProfile?.useAI"
          />

          <ShortcutInfo :shortcut="currentShortcut" :is-recording="audioIsRecording" />
        </div>
      </main>
    </div>
  </div>
</template>
