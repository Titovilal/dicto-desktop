import { useEffect } from 'react'
import { listen } from '@tauri-apps/api/event'
import { invoke } from '@tauri-apps/api/core'

export function useHotkeys(
  onRecordHotkey: () => void,
  onEditHotkey: () => void,
) {
  useEffect(() => {
    const unlisteners: Array<() => void> = []

    listen('hotkey-record', () => onRecordHotkey())
      .then(u => unlisteners.push(u))

    listen('hotkey-edit', () => onEditHotkey())
      .then(u => unlisteners.push(u))

    return () => unlisteners.forEach(u => u())
  }, [onRecordHotkey, onEditHotkey])

  async function updateHotkeys(recordHotkey: string, editHotkey: string) {
    await invoke('register_hotkeys', { recordHotkey, editHotkey })
  }

  return { updateHotkeys }
}
