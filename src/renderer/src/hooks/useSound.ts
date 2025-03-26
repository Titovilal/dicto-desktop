import recordingOff from '../assets/off.mp3' // Asegúrate de tener este archivo
import recordingOk from '../assets/ok.mp3'
import recordingOn from '../assets/on.mp3'

type useSoundReturn = {
  playTestSound: (
    volume: number | undefined,
    enabled: boolean | undefined,
    outputDevice?: string
  ) => void
  playRecordStartSound: (
    volume: number | undefined,
    enabled: boolean | undefined,
    outputDevice?: string
  ) => void
  playRecordStopSound: (
    volume: number | undefined,
    enabled: boolean | undefined,
    outputDevice?: string
  ) => void
  playFinishSound: (
    volume: number | undefined,
    enabled: boolean | undefined,
    outputDevice?: string
  ) => void
}

export function useSound(): useSoundReturn {
  const playSound = async (
    soundFile: string,
    volume: number | undefined,
    enabled: boolean | undefined,
    outputDevice?: string
  ): Promise<void> => {
    if (enabled === false) return

    try {
      const audio = new Audio(soundFile)
      audio.volume = volume ?? 1

      // Set the output device if specified
      if (outputDevice && audio.setSinkId) {
        try {
          await audio.setSinkId(outputDevice)
        } catch (error) {
          console.error('Error setting audio output device:', error)
        }
      }

      await audio.play()
    } catch (error) {
      console.error('Error playing sound:', error)
    }
  }

  const playTestSound = (
    volume: number | undefined,
    enabled: boolean | undefined,
    outputDevice?: string
  ): void => {
    playSound(recordingOk, volume, enabled, outputDevice)
  }

  const playRecordStartSound = (
    volume: number | undefined,
    enabled: boolean | undefined,
    outputDevice?: string
  ): void => {
    playSound(recordingOn, volume, enabled, outputDevice)
  }

  const playRecordStopSound = (
    volume: number | undefined,
    enabled: boolean | undefined,
    outputDevice?: string
  ): void => {
    playSound(recordingOff, volume, enabled, outputDevice)
  }

  const playFinishSound = (
    volume: number | undefined,
    enabled: boolean | undefined,
    outputDevice?: string
  ): void => {
    playSound(recordingOk, volume, enabled, outputDevice)
  }

  return {
    playTestSound,
    playRecordStartSound,
    playRecordStopSound,
    playFinishSound
  }
}
