import { useEffect, useState } from 'react'
import { invokeIPC } from '@/lib/ipc-renderer'
import { type Profile, type StoreSchema } from '@/types/types'

export function useStore() {
    const [settings, setSettings] = useState<StoreSchema['settings'] | null>(null)
    const [profiles, setProfiles] = useState<StoreSchema['profiles'] | []>([])
    const [user, setUser] = useState<StoreSchema['user'] | null>(null)

    const loadStore = async () => {
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

    const updateSettings = async (settings: StoreSchema['settings']) => {
        await invokeIPC('update-settings', settings)
        setSettings(settings)
    }

    const addProfile = async (profile: Profile) => {
        await invokeIPC('add-profile', profile)
        setProfiles([...profiles, profile])
    }

    const updateProfile = async (profile: Profile) => {
        try {
            await invokeIPC('update-profile', profile)
            setProfiles(prevProfiles =>
                prevProfiles.map(p => p.name === profile.name ? profile : p)
            )
        } catch (error) {
            console.error('Error updating profile:', error)
            throw error
        }
    }

    const deleteProfile = async (profile: Profile) => {
        await invokeIPC('delete-profile', profile)
        setProfiles(profiles.filter((p) => p.name !== profile.name))
    }


    const updateSelectedProfile = async (profile: Profile) => {
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

    const updateUser = async (user: StoreSchema['user']) => {
        await invokeIPC('set-user', user)
        setUser(user)
    }

    useEffect(() => {
        loadStore()
    }, [])

    return {
        settings,
        profiles,
        user,
        loadStore,
        updateSettings,
        addProfile,
        updateProfile,
        deleteProfile,
        updateSelectedProfile,
        updateUser,
    }
}
