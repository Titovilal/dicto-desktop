import { useState, useCallback, useEffect } from 'react'
import { invoke } from '@tauri-apps/api/core'

export interface Preset {
  id: string
  name: string
  description?: string
  prompt: string
}

export function usePresets(apiKey: string) {
  const [presets, setPresets] = useState<Preset[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadPresets = useCallback(async () => {
    if (!apiKey) return
    setLoading(true)
    setError(null)
    try {
      const result = await invoke<Preset[]>('fetch_presets', { apiKey })
      setPresets(result)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }, [apiKey])

  useEffect(() => {
    if (apiKey) loadPresets()
  }, [apiKey, loadPresets])

  const applyPreset = useCallback(async (
    preset: Preset,
    text: string,
    model: string,
    transcriptionId?: string,
  ): Promise<string> => {
    return invoke<string>('transform_text', {
      text,
      prompt: preset.prompt,
      model,
      apiKey,
      transcriptionId,
    })
  }, [apiKey])

  const applyCustomPrompt = useCallback(async (
    prompt: string,
    text: string,
    model: string,
    transcriptionId?: string,
  ): Promise<string> => {
    return invoke<string>('transform_text', {
      text,
      prompt,
      model,
      apiKey,
      transcriptionId,
    })
  }, [apiKey])

  return { presets, loading, error, loadPresets, applyPreset, applyCustomPrompt }
}
