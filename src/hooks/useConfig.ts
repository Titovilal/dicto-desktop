import { useState, useEffect } from 'react'
import { LazyStore } from '@tauri-apps/plugin-store'
import { AppConfig, DEFAULT_CONFIG } from '../types'

const store = new LazyStore('config.json')

export function useConfig() {
  const [config, setConfig] = useState<AppConfig>(DEFAULT_CONFIG)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadConfig()
  }, [])

  async function loadConfig() {
    try {
      const saved = await store.get<Partial<AppConfig>>('config')
      if (saved) setConfig({ ...DEFAULT_CONFIG, ...saved })
    } finally {
      setLoading(false)
    }
  }

  async function saveConfig(updates: Partial<AppConfig>) {
    const next = { ...config, ...updates }
    setConfig(next)
    await store.set('config', next)
    await store.save()
  }

  return { config, saveConfig, loading }
}
