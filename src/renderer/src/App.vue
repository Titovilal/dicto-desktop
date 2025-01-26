<script setup>
import { ref } from 'vue'
import { useAudioRecorder } from './composables/useAudioRecorder'
import { useShortcutEditor } from './composables/useShortcutEditor'
import Header from './components/Header.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import ProfilePanel from './components/ProfilePanel.vue'
import RecordingButton from './components/RecordingButton.vue'
import TranscriptionBox from './components/TranscriptionBox.vue'
import ShortcutInfo from './components/ShortcutInfo.vue'

const showSettings = ref(false)
const showProfiles = ref(false)
const selectedProfile = ref('Default')

const {
  isRecording: audioIsRecording,
  isLoading,
  errorMessage,
  editableText,
  toggleRecording
} = useAudioRecorder()

const {
  isRecording: shortcutIsRecording,
  currentShortcut,
  startRecording,
  stopRecording
} = useShortcutEditor()
</script>

<template>
  <div class="h-screen flex flex-col bg-[#f5f5f7] text-[#1d1d1f]">
    <div class="flex flex-col flex-grow px-6 py-6">
      <Header
        v-model:selectedProfile="selectedProfile"
        @toggleSettings="showSettings = !showSettings"
        @toggleProfiles="showProfiles = !showProfiles"
      />

      <main class="flex flex-col flex-grow mt-8">
        <SettingsPanel
          v-if="showSettings"
          :audio-current-shortcut="currentShortcut"
          :shortcut-is-recording="shortcutIsRecording"
          @startRecording="startRecording"
          @stopRecording="stopRecording"
        />

        <ProfilePanel v-else-if="showProfiles" v-model:selectedProfile="selectedProfile" />

        <div v-else class="flex flex-col flex-grow">
          <RecordingButton
            :is-loading="isLoading"
            :is-recording="audioIsRecording"
            @toggleRecording="toggleRecording"
          />

          <div
            v-if="errorMessage"
            class="w-full p-4 rounded-2xl bg-red-50 text-red-600 text-sm mb-6"
            role="alert"
          >
            {{ errorMessage }}
          </div>

          <TranscriptionBox v-model="editableText" />

          <ShortcutInfo :shortcut="currentShortcut" :is-recording="audioIsRecording" />
        </div>
      </main>
    </div>
  </div>
</template>
