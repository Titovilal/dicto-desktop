import { useState, useRef } from 'react'
import { invokeIPC } from '@/lib/ipc-renderer'
import { Profile, StoreSchema } from '@/types/types'
import { useSound } from './useSound'

export function useRecord(): {
  isRecording: boolean
  isProcessing: boolean
  transcription: string
  processedText: string
  handleToggleRecording: (settings: StoreSchema['settings'], profiles: Profile[]) => void
  cancelRecording: (settings: StoreSchema['settings']) => void
  setTranscription: (transcription: string) => void
  setProcessedText: (processedText: string) => void
} {
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [transcription, setTranscription] = useState('')
  const [processedText, setProcessedText] = useState('')
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const isCancellingRef = useRef<boolean>(false)
  const { playRecordStartSound, playRecordStopSound, playFinishSound } = useSound()

  const startRecording = async (
    settings: StoreSchema['settings'],
    profiles: Profile[]
  ): Promise<void> => {
    if (!settings) {
      console.error('[RECORD] Settings not found')
      return
    }

    try {
      // Reset states at the start
      setIsRecording(false)
      setIsProcessing(false)
      audioChunksRef.current = []
      isCancellingRef.current = false

      // Use the selected input device from settings
      const deviceId = settings?.inputDevice || 'default'
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { deviceId: deviceId !== 'default' ? { exact: deviceId } : undefined }
      })

      console.log('[RECORD] Starting new recording...')

      mediaRecorderRef.current = new MediaRecorder(stream)

      // Apply input volume if specified in settings
      if (settings.inputVolume !== undefined && settings.inputVolume !== 1) {
        try {
          const audioContext = new AudioContext()
          const source = audioContext.createMediaStreamSource(stream)
          const gainNode = audioContext.createGain()
          gainNode.gain.value = settings.inputVolume
          source.connect(gainNode)

          // Create a destination stream that we can use with MediaRecorder
          const destinationNode = audioContext.createMediaStreamDestination()
          gainNode.connect(destinationNode)

          // Use the processed stream for recording
          mediaRecorderRef.current = new MediaRecorder(destinationNode.stream)
        } catch (error) {
          console.error('[RECORD] Error applying volume settings:', error)
          // Fall back to the original recorder if there's an error
        }
      }

      mediaRecorderRef.current.ondataavailable = (event): void => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorderRef.current.onstop = async (): Promise<void> => {
        // Skip processing if this is a cancellation
        if (isCancellingRef.current) {
          return
        }

        try {
          // Update popup to processing state
          console.log('Sending update-popup-state to processing')
          invokeIPC('update-popup-state', 'processing')

          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
          const arrayBuffer = await audioBlob.arrayBuffer()
          const audioData = new Uint8Array(arrayBuffer)
          const selectedProfile = profiles.find((p) => p.name === settings.selectedProfile)

          const result = await invokeIPC('process-recording', {
            audioData,
            profile: selectedProfile,
            apiKey: settings?.apiKey
          })

          // Update popup to finished state
          console.log('Sending update-popup-state to finished')
          invokeIPC('update-popup-state', 'finished')

          // Hide popup after a short delay
          setTimeout(() => {
            console.log('Sending hide-popup')
            invokeIPC('hide-popup')
          }, 2000)

          playFinishSound(
            settings.outputVolume,
            settings.outputVolumeEnabled,
            settings.outputDevice
          )
          setIsProcessing(false)
          setTranscription(result.transcription)
          setProcessedText(result.processedText)
        } catch (error) {
          console.error('Error processing recording:', error)
          setIsProcessing(false)
          // Hide popup on error
          invokeIPC('hide-popup')
        }
      }

      // Show popup with recording state before starting the recording
      await invokeIPC('show-popup', 'recording')

      mediaRecorderRef.current.start(1000)
      playRecordStartSound(
        settings.outputVolume,
        settings.outputVolumeEnabled,
        settings.outputDevice
      )
      setIsRecording(true)
    } catch (error) {
      console.error('[RECORD] Error starting recording:', error)
      setIsRecording(false)
      setIsProcessing(false)
      // Hide popup on error
      invokeIPC('hide-popup')
    }
  }

  const cancelRecording = (settings: StoreSchema['settings']): void => {
    if (mediaRecorderRef.current && isRecording) {
      isCancellingRef.current = true
      mediaRecorderRef.current.stop()
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop())
      playRecordStopSound(
        settings?.outputVolume,
        settings?.outputVolumeEnabled,
        settings?.outputDevice
      )
      setIsRecording(false)
      setIsProcessing(false)
      audioChunksRef.current = []

      // Hide the popup since we're cancelling
      invokeIPC('hide-popup')
    }
  }

  const stopRecording = (settings: StoreSchema['settings']): void => {
    if (mediaRecorderRef.current && isRecording) {
      // Make sure cancelling flag is false for normal stops
      isCancellingRef.current = false

      mediaRecorderRef.current.stop()
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop())
      playRecordStopSound(
        settings?.outputVolume,
        settings?.outputVolumeEnabled,
        settings?.outputDevice
      )
      setIsRecording(false)
      setIsProcessing(true)
    }
  }

  const handleToggleRecording = (settings: StoreSchema['settings'], profiles: Profile[]): void => {
    if (!isRecording && !isProcessing) {
      startRecording(settings, profiles)
    } else {
      stopRecording(settings)
    }
  }

  return {
    isRecording,
    isProcessing,
    transcription,
    processedText,
    handleToggleRecording,
    cancelRecording,
    setTranscription,
    setProcessedText
  }
}
