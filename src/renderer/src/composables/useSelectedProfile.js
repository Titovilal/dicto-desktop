import { ref, onMounted } from 'vue'

export function useSelectedProfile() {
  const selectedProfile = ref('Default')

  const setSelectedProfile = async (profileName) => {
    await window.electron.ipcRenderer.invoke('save-selected-profile', profileName)
    selectedProfile.value = profileName
  }

  onMounted(async () => {
    // Get initial selected profile
    const savedProfile = await window.electron.ipcRenderer.invoke('get-selected-profile')
    if (savedProfile) {
      selectedProfile.value = savedProfile
    }
  })

  return {
    selectedProfile,
    setSelectedProfile
  }
}
