import { ref } from 'vue'

export function useProfiles() {
  const profiles = ref([])
  const newProfile = ref(null)
  const editingProfile = ref(null)
  const editingId = ref(null)
  const originalName = ref(null)

  async function loadProfiles() {
    profiles.value = await window.electron.ipcRenderer.invoke('get-profiles')
  }

  function addNewProfile() {
    newProfile.value = {
      name: '',
      prompt: '',
      useAI: false,
      copyToClipboard: false
    }
  }

  function cancelNewProfile() {
    newProfile.value = null
  }

  async function saveNewProfile() {
    const profileData = {
      name: newProfile.value.name,
      prompt: newProfile.value.prompt,
      useAI: newProfile.value.useAI,
      copyToClipboard: newProfile.value.copyToClipboard
    }
    await window.electron.ipcRenderer.invoke('create-profile', profileData)
    await loadProfiles()
    newProfile.value = null
  }

  function startEdit(profile) {
    editingProfile.value = { ...profile }
    editingId.value = profile.name
    originalName.value = profile.name
  }

  function cancelEdit() {
    editingProfile.value = null
    editingId.value = null
    originalName.value = null
  }

  async function saveEditingProfile() {
    const profileData = {
      originalName: originalName.value,
      name: editingProfile.value.name,
      prompt: editingProfile.value.prompt,
      useAI: editingProfile.value.useAI,
      copyToClipboard: editingProfile.value.copyToClipboard
    }
    await window.electron.ipcRenderer.invoke('update-profile', profileData)
    await loadProfiles()
    editingProfile.value = null
    editingId.value = null
    originalName.value = null
  }

  async function deleteProfile(name) {
    if (confirm('Are you sure you want to delete this profile?')) {
      await window.electron.ipcRenderer.invoke('delete-profile', name)
      await loadProfiles()
    }
  }

  return {
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
  }
}
