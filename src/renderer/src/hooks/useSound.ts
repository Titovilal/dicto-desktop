import { useCallback } from 'react'
import recordingOff from '../assets/off.mp3' // Asegúrate de tener este archivo
import recordingOk from '../assets/ok.mp3'
import recordingOn from '../assets/on.mp3'

type useSoundReturn = {
  playTestSound: (volume?: number, enabled?: boolean) => void
  playRecordStartSound: (volume?: number, enabled?: boolean) => void
  playRecordStopSound: (volume?: number, enabled?: boolean) => void
  playFinishSound: (volume?: number, enabled?: boolean) => void
}

export function useSound(): useSoundReturn {
  const playSound = useCallback((soundFile: string, volume = 1, enabled = true) => {
    // Don't play if sounds are disabled
    if (!enabled) return

    const audio = new Audio(soundFile)
    audio.volume = volume
    audio.play()
  }, [])

  const playTestSound = useCallback(
    (volume = 1, enabled = true) => {
      playSound(recordingOk, volume, enabled)
    },
    [playSound]
  )

  const playRecordStartSound = useCallback(
    (volume = 1, enabled = true) => {
      playSound(recordingOn, volume, enabled)
    },
    [playSound]
  )

  const playRecordStopSound = useCallback(
    (volume = 1, enabled = true) => {
      playSound(recordingOff, volume, enabled)
    },
    [playSound]
  )

  const playFinishSound = useCallback(
    (volume = 1, enabled = true) => {
      playSound(recordingOk, volume, enabled)
    },
    [playSound]
  )

  return {
    playTestSound,
    playRecordStartSound,
    playRecordStopSound,
    playFinishSound
  }
}
