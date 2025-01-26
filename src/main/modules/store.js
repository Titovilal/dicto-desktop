let Store
let store

async function initStore() {
  Store = (await import('electron-store')).default
  store = new Store({
    defaults: {
      globalShortcut: 'CommandOrControl+Space',
      selectedProfile: 'Default',
      profiles: [
        {
          name: 'Default',
          prompt: 'Transcribe the following audio:',
          useAI: true,
          copyToClipboard: false
        }
      ]
    }
  })
}

export async function saveShortcut(shortcut) {
  if (!store) await initStore()
  store.set('globalShortcut', shortcut)
}

export async function loadShortcut() {
  if (!store) await initStore()
  return store.get('globalShortcut')
}

export async function getProfiles() {
  if (!store) await initStore()
  return store.get('profiles')
}

export async function createProfile(profile) {
  if (!store) await initStore()
  const profiles = await getProfiles()
  if (profiles.some((p) => p.name === profile.name)) {
    throw new Error('Profile with this name already exists')
  }
  profiles.push(profile)
  store.set('profiles', profiles)
}

export async function updateProfile(profile) {
  if (!store) await initStore()
  const profiles = await getProfiles()
  const index = profiles.findIndex((p) => p.name === profile.originalName)
  if (index === -1) {
    throw new Error('Profile not found')
  }
  const { originalName, ...profileData } = profile
  profiles[index] = profileData
  store.set('profiles', profiles)
}

export async function deleteProfile(name) {
  if (!store) await initStore()
  const profiles = await getProfiles()
  if (profiles.length === 1) {
    throw new Error('Cannot delete the last profile')
  }
  const filteredProfiles = profiles.filter((p) => p.name !== name)
  store.set('profiles', filteredProfiles)

  // If we're deleting the currently selected profile, switch to the first available one
  const selectedProfile = await getSelectedProfile()
  if (selectedProfile === name) {
    store.set('selectedProfile', filteredProfiles[0].name)
  }
}

export async function saveSelectedProfile(profileName) {
  if (!store) await initStore()
  store.set('selectedProfile', profileName)
}

export async function getSelectedProfile() {
  if (!store) await initStore()
  return store.get('selectedProfile')
}

// Initialize store immediately
initStore()
