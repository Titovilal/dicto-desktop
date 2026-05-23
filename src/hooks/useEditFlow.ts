import { useState, useCallback, useEffect, useRef } from 'react'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { readText, writeText } from '@tauri-apps/plugin-clipboard-manager'

export function useEditFlow(config: {
  apiKey: string
  editModel: string
  editAutoPaste: boolean
  editAutoEnter: boolean
}) {
  const [isEditing, setIsEditing] = useState(false)
  const capturedTextRef = useRef('')

  useEffect(() => {
    let unlisten: (() => void) | null = null

    listen('edit-copy-done', async () => {
      try {
        const text = await readText()
        capturedTextRef.current = text || ''
      } catch {
        capturedTextRef.current = ''
      }
    }).then(u => { unlisten = u })

    return () => { if (unlisten) unlisten() }
  }, [])

  const startEdit = useCallback(async () => {
    setIsEditing(true)
    await invoke('start_edit_flow')
  }, [])

  const completeEdit = useCallback(async (): Promise<string> => {
    if (!isEditing) return ''
    try {
      const editedText = await invoke<string>('complete_edit_flow', {
        originalText: capturedTextRef.current,
        apiKey: config.apiKey,
        model: config.editModel,
      })

      await writeText(editedText)

      if (config.editAutoPaste) {
        await new Promise(r => setTimeout(r, 100))
        await invoke('simulate_paste_cmd')
      }
      if (config.editAutoEnter) {
        await new Promise(r => setTimeout(r, 100))
        await invoke('simulate_enter_cmd')
      }

      return editedText
    } finally {
      setIsEditing(false)
      capturedTextRef.current = ''
    }
  }, [isEditing, config])

  return { isEditing, startEdit, completeEdit }
}
