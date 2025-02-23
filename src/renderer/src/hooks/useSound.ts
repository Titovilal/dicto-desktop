import { useCallback } from 'react'
import recordingOff from '../assets/off.mp3' // Asegúrate de tener este archivo
import recordingOk from '../assets/ok.mp3'
import recordingOn from '../assets/on.mp3'


export function useSound() {
    const playSound = useCallback((soundFile: string, volume = 1) => {
        const audio = new Audio(soundFile)
        audio.volume = volume
        audio.play()
    }, [])

    const playTestSound = useCallback((volume = 1) => {
        playSound(recordingOk, volume)
    }, [playSound])

    const playRecordStartSound = useCallback((volume = 1) => {
        playSound(recordingOn, volume)
    }, [playSound])

    const playRecordStopSound = useCallback((volume = 1) => {
        playSound(recordingOff, volume)
    }, [playSound])

    const playFinishSound = useCallback((volume = 1) => {
        playSound(recordingOk, volume)
    }, [playSound])

    return {
        playTestSound,
        playRecordStartSound,
        playRecordStopSound,
        playFinishSound
    }
}