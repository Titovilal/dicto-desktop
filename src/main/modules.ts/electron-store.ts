/* eslint-disable @typescript-eslint/no-explicit-any */
import { ipcMain } from 'electron'
import { Profile, StoreSchema } from '../../renderer/src/types/types'
import { DEFAULT_PROFILES } from './default-profiles'

export async function initStore(): Promise<any> {
  const Store = (await import('electron-store')).default
  const store = new Store<StoreSchema>({
    defaults: {
      settings: {
        theme: 'light',
        appLanguage: 'es',
        outputVolumeEnabled: true,
        outputVolume: 1,
        recordShortcut: 'CommandOrControl+Space',
        changeProfileShortcut: 'CommandOrControl+P',
        selectedProfile: 'Default',
        apiKey: '',
        inputDevice: '',
        inputVolume: 1,
        outputDevice: ''
      },
      profiles: DEFAULT_PROFILES,
      user: {
        email: '',
        name: '',
        sub_credits: 0,
        otp_credits: 0,
        sub_date_time: null,
        otp_date_time: null,
        has_access: false,
        has_subscription: false,
        cancel_next_month: false,
        created_at: '',
        updated_at: ''
      }
    }
  })

  await Promise.all([
    initSettingsIPC(store),
    initUserIPC(store),
    initProfilesIPC(store),
    initClearStoreIPC(store)
  ])
  return store as any
}

async function initSettingsIPC(store: any): Promise<void> {
  console.log('[STORE] Initializing settings IPC')
  ipcMain.handle('get-settings', async () => {
    return await store.get('settings')
  })

  ipcMain.handle('update-settings', async (_, settings: Partial<StoreSchema['settings']>) => {
    console.log('[STORE] Updating settings', settings)
    return await store.set('settings', { ...store.get('settings'), ...settings })
  })
}

async function initUserIPC(store: any): Promise<void> {
  console.log('[STORE] Initializing user IPC')
  ipcMain.handle('get-user', async () => {
    return await store.get('user')
  })

  ipcMain.handle('set-user', async (_, userData: StoreSchema['user']) => {
    console.log('[STORE] Updating user', userData)
    return await store.set('user', userData)
  })
}

// Update the clear-profiles handler
async function initProfilesIPC(store: any): Promise<void> {
  console.log('[STORE] Initializing profiles IPC')
  ipcMain.handle('get-profiles', async () => {
    return await store.get('profiles')
  })

  ipcMain.handle('add-profile', async (_, profile: Profile) => {
    console.log('[STORE] Adding profile', profile)
    return await store.set('profiles', [...store.get('profiles'), profile])
  })

  ipcMain.handle('update-profile', async (_, profile: Profile) => {
    console.log('[STORE] Updating profile', profile)
    try {
      const currentProfiles = store.get('profiles') as Profile[]
      const updatedProfiles = currentProfiles.map((p) => (p.name === profile.name ? profile : p))
      await store.set('profiles', updatedProfiles)
      return updatedProfiles
    } catch (error) {
      console.error('Error in update-profile handler:', error)
      throw error
    }
  })

  ipcMain.handle('delete-profile', async (_, profile: Profile) => {
    console.log('[STORE] Deleting profile', profile)
    const currentProfiles = store.get('profiles')
    const updatedProfiles = currentProfiles.filter((p: Profile) => p.name !== profile.name)
    return await store.set('profiles', updatedProfiles)
  })

  ipcMain.handle('set-selected-profile', async (_, profileName: string) => {
    console.log('[STORE] Setting selected profile', profileName)
    return await store.set('settings.selectedProfile', profileName)
  })

  ipcMain.handle('get-selected-profile', async () => {
    console.log('[STORE] Getting selected profile')
    return await store.get('settings.selectedProfile')
  })

  ipcMain.handle('clear-profiles', async () => {
    console.log('[STORE] Clearing profiles')
    return await store.set('profiles', DEFAULT_PROFILES)
  })
}

async function initClearStoreIPC(store: any): Promise<void> {
  console.log('[STORE] Initializing clear store IPC')
  ipcMain.handle('clear-store', async () => {
    return await store.clear()
  })
}
