<script setup>
import { ref, onMounted, watch } from 'vue'
import { useAudioRecorder } from './composables/useAudioRecorder'
import { useShortcutEditor } from './composables/useShortcutEditor'
import { useProfiles } from './composables/useProfiles'
import { useAIProcess } from './composables/useAIProcess'
import Header from './components/Header.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import ProfilePanel from './components/ProfilePanel.vue'
import HomePanel from './components/HomePanel.vue'

const showSettings = ref(false)
const showProfiles = ref(false)

// Initialize composables
const { profiles, selectedProfile, loadProfiles, setSelectedProfile } = useProfiles()

const {
  isRecording: audioIsRecording,
  isLoading: audioIsLoading,
  editableText,
  currentShortcut,
  toggleRecording: toggleAudioRecording,
  aiProcessedText,
  playFinishSound
} = useAudioRecorder()

const {
  isRecording: shortcutIsRecording,
  startRecording: startShortcutRecording,
  stopRecording: stopShortcutRecording
} = useShortcutEditor()

// AI setup
const { processWithAI } = useAIProcess()

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
        playFinishSound
        console.log('AI processed text:', aiProcessedText.value)
      }
    } catch (error) {
      console.error('Error processing with AI:', error)
    }
  } else {
    aiProcessedText.value = ''
    if (profile.copyToClipboard) {
      await copyToClipboard(newText)
    }
    playFinishSound()
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

function handleCloseAll() {
  showSettings.value = false
  showProfiles.value = false
}
</script>

<template>
  <div class="h-screen p-6 bg-gray-100 space-y-3">
    <Header
      :profiles="profiles"
      :selected-profile="selectedProfile"
      @profile-change="handleProfileChange"
      @toggle-settings="showSettings = !showSettings"
      @toggle-profiles="showProfiles = !showProfiles"
      @close-all="handleCloseAll"
    />

    <SettingsPanel
      v-if="showSettings"
      :current-shortcut="currentShortcut"
      :shortcut-is-recording="shortcutIsRecording"
      @start-recording="startShortcutRecording"
      @stop-recording="stopShortcutRecording"
    />

    <ProfilePanel v-if="showProfiles" v-model:selected-profile="selectedProfile" />

    <HomePanel
      v-if="!showProfiles && !showSettings"
      :shortcut="currentShortcut"
      :is-recording="audioIsRecording"
      :is-loading="audioIsLoading"
      :model-value="editableText"
      :ai-processed-text="aiProcessedText"
      @toggle-recording="toggleAudioRecording"
    />
  </div>
</template>
