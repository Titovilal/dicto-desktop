<template>
  <div class="bg-white rounded-2xl p-6 shadow-sm space-y-6">
    <h3 class="text-2xl font-medium text-[#1d1d1f]">Profile Management</h3>

    <!-- Profile List -->
    <div class="space-y-4">
      <div class="flex justify-between items-center">
        <h4 class="text-sm font-medium text-[#86868b]">Profiles</h4>
        <button
          class="px-4 py-1.5 rounded-full text-sm font-medium bg-[#f5f5f7] hover:bg-[#e5e5e7] text-[#1d1d1f] transition-all duration-200"
          @click="addNewProfile"
        >
          Add Profile
        </button>
      </div>

      <!-- Profile List -->
      <div class="space-y-4">
        <!-- New Profile Form -->
        <div v-if="newProfile" class="bg-white border-2 border-[#1d1d1f] p-4 rounded-lg">
          <div class="space-y-4">
            <div>
              <input
                v-model="newProfile.name"
                type="text"
                required
                placeholder="Profile Name"
                class="w-full px-3 py-2 bg-[#f5f5f7] rounded-lg focus:outline-none focus:bg-white focus:ring-2 focus:ring-[#1d1d1f]"
              />
            </div>
            <div>
              <textarea
                v-model="newProfile.prompt"
                required
                placeholder="Enter prompt"
                rows="2"
                class="w-full px-3 py-2 bg-[#f5f5f7] rounded-lg focus:outline-none focus:bg-white focus:ring-2 focus:ring-[#1d1d1f]"
              ></textarea>
            </div>
            <div class="flex gap-4">
              <label class="flex items-center">
                <input
                  v-model="newProfile.useAI"
                  type="checkbox"
                  class="form-checkbox h-4 w-4 text-[#1d1d1f]"
                />
                <span class="ml-2 text-sm">Use AI</span>
              </label>
              <label class="flex items-center">
                <input
                  v-model="newProfile.copyToClipboard"
                  type="checkbox"
                  class="form-checkbox h-4 w-4 text-[#1d1d1f]"
                />
                <span class="ml-2 text-sm">Copy to Clipboard</span>
              </label>
            </div>
            <div class="flex justify-end gap-2">
              <button
                class="px-3 py-1.5 text-sm font-medium text-[#86868b] hover:text-[#1d1d1f]"
                type="button"
                @click="cancelNewProfile"
              >
                Cancel
              </button>
              <button
                class="px-3 py-1.5 text-sm font-medium bg-[#1d1d1f] text-white rounded-lg hover:bg-[#2d2d2f]"
                type="button"
                @click="saveNewProfile"
              >
                Save
              </button>
            </div>
          </div>
        </div>

        <!-- Profile Items -->
        <div
          v-for="profile in profiles"
          :key="profile.name"
          class="bg-[#f5f5f7] p-4 rounded-lg"
          :class="{ 'border-2 border-[#1d1d1f] bg-white': editingId === profile.name }"
        >
          <div v-if="editingId === profile.name">
            <div class="space-y-4">
              <div>
                <input
                  v-model="editingProfile.name"
                  type="text"
                  required
                  class="w-full px-3 py-2 bg-[#f5f5f7] rounded-lg focus:outline-none focus:bg-white focus:ring-2 focus:ring-[#1d1d1f]"
                />
              </div>
              <div>
                <textarea
                  v-model="editingProfile.prompt"
                  required
                  rows="2"
                  class="w-full px-3 py-2 bg-[#f5f5f7] rounded-lg focus:outline-none focus:bg-white focus:ring-2 focus:ring-[#1d1d1f]"
                ></textarea>
              </div>
              <div class="flex gap-4">
                <label class="flex items-center">
                  <input
                    v-model="editingProfile.useAI"
                    type="checkbox"
                    class="form-checkbox h-4 w-4 text-[#1d1d1f]"
                  />
                  <span class="ml-2 text-sm">Use AI</span>
                </label>
                <label class="flex items-center">
                  <input
                    v-model="editingProfile.copyToClipboard"
                    type="checkbox"
                    class="form-checkbox h-4 w-4 text-[#1d1d1f]"
                  />
                  <span class="ml-2 text-sm">Copy to Clipboard</span>
                </label>
              </div>
              <div class="flex justify-end gap-2">
                <button
                  class="px-3 py-1.5 text-sm font-medium text-[#86868b] hover:text-[#1d1d1f]"
                  type="button"
                  @click="cancelEdit"
                >
                  Cancel
                </button>
                <button
                  class="px-3 py-1.5 text-sm font-medium bg-[#1d1d1f] text-white rounded-lg hover:bg-[#2d2d2f]"
                  type="button"
                  @click="saveEditingProfile"
                >
                  Save
                </button>
              </div>
            </div>
          </div>
          <div v-else class="flex justify-between items-start">
            <div>
              <h5 class="font-medium">{{ profile.name }}</h5>
              <p class="text-sm text-[#86868b] mt-1">{{ profile.prompt }}</p>
              <div class="flex gap-2 mt-2">
                <span class="text-xs bg-[#e5e5e7] px-2 py-1 rounded-full">
                  {{ profile.useAI ? 'AI Enabled' : 'AI Disabled' }}
                </span>
                <span class="text-xs bg-[#e5e5e7] px-2 py-1 rounded-full">
                  {{ profile.copyToClipboard ? 'Auto Copy' : 'Manual Copy' }}
                </span>
              </div>
            </div>
            <div class="flex gap-2">
              <button
                class="p-2 rounded-full hover:bg-[#e5e5e7] text-[#1d1d1f]"
                @click="startEdit(profile)"
              >
                <Pencil class="h-4 w-4" />
              </button>
              <button
                class="p-2 rounded-full hover:bg-red-100 text-red-600"
                @click="deleteProfile(profile.name)"
              >
                <Trash2 class="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useProfiles } from '../composables/useProfiles'
import { Pencil, Trash2 } from 'lucide-vue-next'

const {
  profiles,
  newProfile,
  editingProfile,
  editingId,
  loadProfiles,
  addNewProfile,
  cancelNewProfile,
  saveNewProfile,
  startEdit,
  cancelEdit,
  saveEditingProfile,
  deleteProfile
} = useProfiles()

onMounted(async () => {
  await loadProfiles()
})
</script>
