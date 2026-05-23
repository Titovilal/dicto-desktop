import { useState, useRef, useEffect } from 'react'
import { invoke } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'

export function useRecorder() {
  const [isRecording, setIsRecording] = useState(false)
  const [audioLevel, setAudioLevel] = useState(0)
  const unlistenRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    listen<{ level: number }>('audio-level', (e) => {
      setAudioLevel(e.payload.level)
    }).then((unlisten) => {
      unlistenRef.current = unlisten
    })

    return () => {
      unlistenRef.current?.()
    }
  }, [])

  async function startRecording() {
    await invoke('start_recording')
    setIsRecording(true)
  }

  async function stopRecording(): Promise<Uint8Array> {
    const bytes = await invoke<number[]>('stop_recording')
    setIsRecording(false)
    setAudioLevel(0)
    return new Uint8Array(bytes)
  }

  async function transcribeAudio(
    audioBytes: Uint8Array,
    apiKey: string,
    model: string,
    language: string
  ): Promise<{ text: string; transcription_id?: string }> {
    return invoke<{ text: string; transcription_id?: string }>('transcribe_audio', {
      audioBytes: Array.from(audioBytes),
      apiKey,
      model,
      language,
    })
  }

  return { isRecording, audioLevel, startRecording, stopRecording, transcribeAudio }
}
