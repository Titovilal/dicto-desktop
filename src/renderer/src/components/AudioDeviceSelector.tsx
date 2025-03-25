import { useState, useEffect, useRef } from 'react'
import { Mic, Play, StopCircle } from 'lucide-react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/Select'
import { StoreSchema } from '@/types/types'

interface AudioDeviceSelectorProps {
  settings: StoreSchema['settings'] | null
  updateSettings: (settings: StoreSchema['settings']) => void
}

export function AudioDeviceSelector({
  settings,
  updateSettings
}: AudioDeviceSelectorProps): JSX.Element {
  const [audioDevices, setAudioDevices] = useState<MediaDeviceInfo[]>([])
  const [isTesting, setIsTesting] = useState(false)
  const [audioStream, setAudioStream] = useState<MediaStream | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [audioLevel, setAudioLevel] = useState(0)

  // References
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animationFrameRef = useRef<number | null>(null)

  useEffect(() => {
    // Get available audio devices
    const getAudioDevices = async (): Promise<void> => {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices()
        const audioInputDevices = devices.filter((device) => device.kind === 'audioinput')
        setAudioDevices(audioInputDevices)
      } catch (error) {
        console.error('Error getting audio devices:', error)
        setErrorMessage('Could not access audio devices. Check permissions.')
      }
    }

    getAudioDevices()

    // Clean up resources when unmounting
    return (): void => {
      stopAudioTest()
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close()
      }
    }
  }, [])

  const handleAudioDeviceChange = (deviceId: string): void => {
    if (!settings) return
    updateSettings({ ...settings, defaultMediaDevice: deviceId })
    stopAudioTest()
  }

  const startAudioTest = async (): Promise<void> => {
    try {
      setErrorMessage(null)

      const deviceId = settings?.defaultMediaDevice || 'default'

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { deviceId: deviceId !== 'default' ? { exact: deviceId } : undefined }
      })

      setAudioStream(stream)
      setIsTesting(true)

      // Set up audio analyzer for volume visualization
      const audioContext = new AudioContext()
      audioContextRef.current = audioContext
      const analyser = audioContext.createAnalyser()
      analyserRef.current = analyser
      analyser.fftSize = 256

      const source = audioContext.createMediaStreamSource(stream)
      source.connect(analyser)

      const dataArray = new Uint8Array(analyser.frequencyBinCount)

      const updateAudioLevel = (): void => {
        if (!analyserRef.current) return

        analyserRef.current.getByteFrequencyData(dataArray)
        const average = dataArray.reduce((acc, val) => acc + val, 0) / dataArray.length
        const normalizedLevel = average / 255 // Normalize to 0-1
        setAudioLevel(normalizedLevel)

        animationFrameRef.current = requestAnimationFrame(updateAudioLevel)
      }

      updateAudioLevel()
    } catch (error) {
      console.error('Error testing microphone:', error)
      setErrorMessage('Could not access microphone. Check permissions.')
      setIsTesting(false)
    }
  }

  const stopAudioTest = (): void => {
    // Stop all tracks in the stream
    if (audioStream) {
      audioStream.getTracks().forEach((track) => track.stop())
      setAudioStream(null)
    }

    // Clean up audio analysis
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }

    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close()
      audioContextRef.current = null
      analyserRef.current = null
    }

    // Reset state
    setIsTesting(false)
    setAudioLevel(0)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium text-zinc-100">Audio Input Device</h2>
        <div className="px-3 py-1 rounded-full bg-zinc-700/30 text-xs text-zinc-400">Recording</div>
      </div>
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-zinc-700/50 text-zinc-300">
            <Mic size={20} />
          </div>
          <div className="flex-1">
            <Select
              value={settings?.defaultMediaDevice || 'default'}
              onValueChange={handleAudioDeviceChange}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select microphone" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="default">System Default</SelectItem>
                {audioDevices.map((device) => (
                  <SelectItem key={device.deviceId} value={device.deviceId}>
                    {device.label || `Microphone ${device.deviceId.slice(0, 5)}...`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <button
            onClick={isTesting ? stopAudioTest : startAudioTest}
            className={`p-2 rounded-lg transition-all duration-200 ${
              isTesting
                ? 'bg-red-500/20 text-red-500 hover:bg-red-500/30'
                : 'bg-zinc-700/50 text-zinc-300 hover:bg-zinc-700/70'
            }`}
            title={isTesting ? 'Stop test' : 'Test microphone'}
          >
            {isTesting ? <StopCircle size={20} /> : <Play size={20} />}
          </button>
        </div>

        {isTesting && (
          <div className="space-y-3">
            {/* Audio level meter */}
            <div className="space-y-1">
              <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 transition-all duration-100"
                  style={{ width: `${audioLevel * 100}%` }}
                />
              </div>
              <div className="flex justify-between text-xs text-zinc-400">
                <span>Audio Level</span>
                <span>{Math.round(audioLevel * 100)}%</span>
              </div>
            </div>
          </div>
        )}

        {errorMessage && <p className="text-xs text-red-400 mt-1">{errorMessage}</p>}

        <p className="text-sm text-zinc-400">
          Select the microphone you want to use for voice recording. If you don&apos;t select any
          device, the system default will be used.
        </p>
      </div>
    </div>
  )
}
