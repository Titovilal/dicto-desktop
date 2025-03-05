import { useEffect, useState } from 'react'
import { invokeIPC } from '@/lib/ipc-renderer'
import { type Profile, type StoreSchema } from '@/types/types'

type useStoreReturn = {
  settings: StoreSchema['settings']
  profiles: StoreSchema['profiles']
  user: StoreSchema['user']
  loadStore: () => Promise<void>
  updateSettings: (settings: StoreSchema['settings']) => Promise<void>
  addProfile: (profile: Profile) => Promise<void>
  updateProfile: (profile: Profile) => Promise<void>
  deleteProfile: (profile: Profile) => Promise<void>
  updateSelectedProfile: (profile: Profile) => Promise<void>
  updateUser: (user: StoreSchema['user']) => Promise<void>
}

export function useStore(): useStoreReturn {
  const [settings, setSettings] = useState<StoreSchema['settings']>()
  const [profiles, setProfiles] = useState<StoreSchema['profiles']>()
  const [user, setUser] = useState<StoreSchema['user']>()

  const loadStore = async (): Promise<void> => {
    const settings = await invokeIPC('get-settings')
    console.log('[STORE] Settings:', settings)
    setSettings(settings)
    const profiles = await invokeIPC('get-profiles')
    console.log('[STORE] Profiles:', profiles)
    setProfiles(profiles)
    const user = await invokeIPC('get-user')
    console.log('[STORE] User:', user)
    setUser(user)
  }

  const updateSettings = async (settings: StoreSchema['settings']): Promise<void> => {
    await invokeIPC('update-settings', settings)
    setSettings(settings)
  }

  const addProfile = async (profile: Profile): Promise<void> => {
    await invokeIPC('add-profile', profile)
    setProfiles([...profiles, profile])
  }

  const updateProfile = async (profile: Profile): Promise<void> => {
    try {
      await invokeIPC('update-profile', profile)
      setProfiles((prevProfiles) =>
        prevProfiles?.map((p) => (p.name === profile.name ? profile : p))
      )
    } catch (error) {
      console.error('Error updating profile:', error)
      throw error
    }
  }

  const deleteProfile = async (profile: Profile): Promise<void> => {
    await invokeIPC('delete-profile', profile)
    setProfiles(profiles?.filter((p) => p.name !== profile.name))
  }

  const updateSelectedProfile = async (profile: Profile): Promise<void> => {
    if (!settings) {
      return
    }
    const updatedSettings = {
      ...settings,
      selectedProfile: profile.name
    }
    await invokeIPC('update-settings', updatedSettings)
    setSettings(updatedSettings)
  }

  const updateUser = async (user: StoreSchema['user']): Promise<void> => {
    await invokeIPC('set-user', user)
    setUser(user)
  }

  useEffect(() => {
    loadStore()
  }, [])

  return {
    settings: settings,
    profiles: profiles,
    user: user,
    loadStore,
    updateSettings,
    addProfile,
    updateProfile,
    deleteProfile,
    updateSelectedProfile,
    updateUser
  }
}
