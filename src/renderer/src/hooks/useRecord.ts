import { useState, useRef } from 'react'
import { invokeIPC } from '@/lib/ipc-renderer'
import { Profile, StoreSchema } from '@/types/types'
import { useSound } from './useSound'

export function useRecord() {
    const [isRecording, setIsRecording] = useState(false)
    const [isProcessing, setIsProcessing] = useState(false)
    const [transcription, setTranscription] = useState('')
    const [processedText, setProcessedText] = useState('')
    const mediaRecorderRef = useRef<MediaRecorder | null>(null)
    const audioChunksRef = useRef<Blob[]>([])
    const isCancellingRef = useRef<boolean>(false)
    const { playRecordStartSound, playRecordStopSound, playFinishSound } = useSound()

    const startRecording = async (settings: StoreSchema['settings'], profiles: Profile[]) => {
        if (!settings) {
            console.error('[RECORD] Settings not found')
            return
        }

        try {
            audioChunksRef.current = []
            isCancellingRef.current = false
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

            mediaRecorderRef.current = new MediaRecorder(stream)

            mediaRecorderRef.current.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data)
                }
            }

            mediaRecorderRef.current.onstop = async () => {
                // Skip processing if this is a cancellation
                if (isCancellingRef.current) {
                    return
                }

                try {
                    const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
                    const arrayBuffer = await audioBlob.arrayBuffer()
                    const audioData = new Uint8Array(arrayBuffer)
                    const selectedProfile = profiles.find((p) => p.name === settings.selectedProfile)

                    const result = await invokeIPC('process-recording', {
                        audioData,
                        profile: selectedProfile,
                        apiKey: settings?.apiKey
                    })

                    playFinishSound(settings.soundVolume)
                    setIsProcessing(false)
                    setTranscription(result.transcription)
                    setProcessedText(result.processedText)

                } catch (error) {
                    console.error('Error processing recording:', error)
                    setIsProcessing(false)
                }
            }

            mediaRecorderRef.current.start(1000)
            playRecordStartSound(settings.soundVolume)
            setIsRecording(true)
        } catch (error) {
            console.error('Error starting recording:', error)
            setIsRecording(false)
            setIsProcessing(false)
        }
    }

    const cancelRecording = (settings: StoreSchema['settings']) => {
        if (mediaRecorderRef.current && isRecording) {
            isCancellingRef.current = true
            mediaRecorderRef.current.stop()
            mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop())
            playRecordStopSound(settings.soundVolume)
            setIsRecording(false)
            setIsProcessing(false)
            audioChunksRef.current = []
        }
    }

    const stopRecording = (settings: StoreSchema['settings']) => {
        if (mediaRecorderRef.current && isRecording) {
            // Make sure cancelling flag is false for normal stops
            isCancellingRef.current = false

            mediaRecorderRef.current.stop()
            mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop())
            playRecordStopSound(settings.soundVolume)
            setIsRecording(false)
            setIsProcessing(true)
        }
    }

    const handleToggleRecording = (settings: StoreSchema['settings'], profiles: Profile[]) => {
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