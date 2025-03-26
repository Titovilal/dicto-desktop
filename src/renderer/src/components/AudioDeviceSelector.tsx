import { useState, useEffect, useRef } from 'react'
import { Play, StopCircle, Volume2, VolumeX, Download } from 'lucide-react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/Select'
import { StoreSchema } from '@/types/types'
import { Slider } from './ui/Slider'

interface AudioDeviceSelectorProps {
  settings: StoreSchema['settings'] | null
  updateSettings: (settings: StoreSchema['settings']) => void
}

// Audio processing related types
interface AudioProcessingRefs {
  audioContext: AudioContext | null
  analyser: AnalyserNode | null
  gainNode: GainNode | null
  audioElement: HTMLAudioElement | null
  animationFrame: number | null
  mediaRecorder: MediaRecorder | null
}

export function AudioDeviceSelector({
  settings,
  updateSettings
}: AudioDeviceSelectorProps): JSX.Element {
  // State
  const [audioDevices, setAudioDevices] = useState<MediaDeviceInfo[]>([])
  const [isTesting, setIsTesting] = useState(false)
  const [audioStream, setAudioStream] = useState<MediaStream | null>(null)
  const [audioLevel, setAudioLevel] = useState(0)
  const [volume, setVolume] = useState(settings?.inputVolume || 1)
  const [recordedChunks, setRecordedChunks] = useState<Blob[]>([])
  const [recordingAvailable, setRecordingAvailable] = useState(false)

  // Audio processing references
  const refs = useRef<AudioProcessingRefs>({
    audioContext: null,
    analyser: null,
    gainNode: null,
    audioElement: null,
    animationFrame: null,
    mediaRecorder: null
  })

  // Load audio devices on component mount
  useEffect(() => {
    loadAudioDevices()

    // Initialize volume from settings
    if (settings?.inputVolume !== undefined) {
      setVolume(settings.inputVolume)
    }

    // Clean up resources when unmounting
    return (): void => {
      cleanupAudioResources()
    }
  }, [settings?.inputVolume])

  // Audio device management
  const loadAudioDevices = async (): Promise<void> => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices()
      const audioInputDevices = devices.filter((device) => device.kind === 'audioinput')
      setAudioDevices(audioInputDevices)
    } catch (error) {
      console.error('Error getting audio devices:', error)
    }
  }

  const handleAudioDeviceChange = (deviceId: string): void => {
    if (!settings) return
    updateSettings({ ...settings, inputDevice: deviceId })
    stopAudioTest()
  }

  // Volume control
  const handleVolumeChange = (newVolume: number): void => {
    if (!settings) return

    // Update local state
    setVolume(newVolume)

    // Update gain node if it exists
    if (refs.current.gainNode) {
      refs.current.gainNode.gain.value = newVolume
    }

    // Update settings without causing immediate re-render
    const settingsCopy = { ...settings, inputVolume: newVolume }
    setTimeout(() => {
      updateSettings(settingsCopy)
    }, 0)
  }

  // Audio testing functionality
  const startAudioTest = async (): Promise<void> => {
    if (isTesting) {
      stopAudioTest()
      return
    }

    try {
      const deviceId = settings?.inputDevice || 'default'

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { deviceId: deviceId !== 'default' ? { exact: deviceId } : undefined }
      })

      setAudioStream(stream)
      setIsTesting(true)
      setRecordedChunks([])
      setRecordingAvailable(false)

      setupAudioProcessing(stream)
      startAudioLevelMonitoring()
      startRecording(stream)
    } catch (error) {
      console.error('Error testing microphone:', error)
      setIsTesting(false)
    }
  }

  const setupAudioProcessing = (stream: MediaStream): void => {
    // Create audio context and nodes
    const audioContext = new AudioContext()
    refs.current.audioContext = audioContext

    // Create gain node for volume control
    const gainNode = audioContext.createGain()
    gainNode.gain.value = volume
    refs.current.gainNode = gainNode

    // Create analyzer for level visualization
    const analyser = audioContext.createAnalyser()
    refs.current.analyser = analyser
    analyser.fftSize = 256

    // Connect the audio graph
    const source = audioContext.createMediaStreamSource(stream)

    // Conectar la fuente al nodo de ganancia
    source.connect(gainNode)

    // Conectar el nodo de ganancia al analizador para visualización
    gainNode.connect(analyser)

    // Conectar el nodo de ganancia a la salida de audio para monitoreo
    gainNode.connect(audioContext.destination)
  }

  const startAudioLevelMonitoring = (): void => {
    const analyser = refs.current.analyser
    if (!analyser) return

    const dataArray = new Uint8Array(analyser.frequencyBinCount)

    const updateAudioLevel = (): void => {
      if (!refs.current.analyser) return

      refs.current.analyser.getByteFrequencyData(dataArray)

      // Calcular el promedio de manera más sensible
      let sum = 0
      let count = 0
      for (let i = 0; i < dataArray.length; i++) {
        if (dataArray[i] > 0) {
          sum += dataArray[i]
          count++
        }
      }

      // Evitar división por cero
      const average = count > 0 ? sum / count : 0
      const normalizedLevel = Math.min(1, average / 128) // Normalizar a 0-1 con mayor sensibilidad

      setAudioLevel(normalizedLevel)
      refs.current.animationFrame = requestAnimationFrame(updateAudioLevel)
    }

    updateAudioLevel()
  }

  const startRecording = (stream: MediaStream): void => {
    const mediaRecorder = new MediaRecorder(stream)
    refs.current.mediaRecorder = mediaRecorder

    mediaRecorder.ondataavailable = (event): void => {
      if (event.data.size > 0) {
        setRecordedChunks((prev) => [...prev, event.data])
      }
    }

    mediaRecorder.onstop = (): void => {
      if (recordedChunks.length > 0) {
        setRecordingAvailable(true)
      }
    }

    mediaRecorder.start()
  }

  const stopAudioTest = (): void => {
    // Stop recording
    if (refs.current.mediaRecorder && refs.current.mediaRecorder.state !== 'inactive') {
      refs.current.mediaRecorder.stop()
    }

    cleanupAudioResources()

    // Reset state
    setIsTesting(false)
    setAudioLevel(0)
  }

  const cleanupAudioResources = (): void => {
    // Stop audio monitoring
    if (refs.current.audioElement) {
      try {
        refs.current.audioElement.pause()
        refs.current.audioElement.srcObject = null
      } catch (err) {
        console.error('Error stopping audio monitoring:', err)
      }
      refs.current.audioElement = null
    }

    // Stop all tracks in the stream
    if (audioStream) {
      audioStream.getTracks().forEach((track) => track.stop())
      setAudioStream(null)
    }

    // Clean up animation frame
    if (refs.current.animationFrame) {
      cancelAnimationFrame(refs.current.animationFrame)
      refs.current.animationFrame = null
    }

    // Close audio context
    if (refs.current.audioContext && refs.current.audioContext.state !== 'closed') {
      refs.current.audioContext.close()
      refs.current.audioContext = null
      refs.current.analyser = null
      refs.current.gainNode = null
    }

    // Clean up media recorder
    refs.current.mediaRecorder = null
  }

  const handleDownloadRecording = (): void => {
    if (recordedChunks.length === 0) return

    const blob = new Blob(recordedChunks, { type: 'audio/webm' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.style.display = 'none'
    a.href = url
    a.download = `mic-test-recording-${new Date().toISOString().slice(0, 19)}.webm`
    document.body.appendChild(a)
    a.click()

    setTimeout(() => {
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }, 100)
  }

  // UI Components
  const renderDeviceSelector = (): JSX.Element => (
    <div className="flex-1">
      <Select value={settings?.inputDevice || 'default'} onValueChange={handleAudioDeviceChange}>
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
  )

  const renderTestButton = (): JSX.Element => (
    <button
      onClick={startAudioTest}
      className={`w-full p-2 rounded-lg transition-all duration-200 ${
        isTesting
          ? 'bg-red-500/20 text-red-500 hover:bg-red-500/30'
          : 'bg-zinc-700/50 text-zinc-300 hover:bg-zinc-700/70'
      }`}
      title={isTesting ? 'Stop test' : 'Test microphone'}
    >
      <div className="flex items-center justify-center gap-2">
        {isTesting ? <StopCircle size={20} /> : <Play size={20} />}
        <span>{isTesting ? 'Stop Testing' : 'Test Microphone'}</span>
      </div>
    </button>
  )

  const renderAudioLevelMeter = (): JSX.Element => (
    <div className="space-y-1">
      <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-100 ${
            isTesting ? 'bg-emerald-500' : 'bg-zinc-700'
          }`}
          style={{ width: `${isTesting ? audioLevel * 100 : 0}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-zinc-400">
        <span>Audio Level</span>
        <span>{isTesting ? `${Math.round(audioLevel * 100)}%` : '0%'}</span>
      </div>
    </div>
  )

  const renderVolumeControl = (): JSX.Element => (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm text-zinc-300">Input Volume</span>
        <span className="text-xs text-zinc-400">{Math.round(volume * 100)}%</span>
      </div>
      <div className="flex items-center gap-2">
        <VolumeX size={16} className="text-zinc-400" />
        <Slider
          value={[volume]}
          min={0}
          max={5}
          step={0.1}
          onValueChange={(values) => handleVolumeChange(values[0])}
          className="flex-1"
        />
        <Volume2 size={16} className="text-zinc-400" />
      </div>
    </div>
  )

  const renderDownloadButton = (): JSX.Element | null => {
    if (!recordingAvailable) return null

    return (
      <button
        onClick={handleDownloadRecording}
        className="w-full p-2 rounded-lg transition-all duration-200 bg-blue-500/20 text-blue-400 hover:bg-blue-500/30"
        title="Download test recording"
      >
        <div className="flex items-center justify-center gap-2">
          <Download size={20} />
          <span>Download Recording</span>
        </div>
      </button>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium text-zinc-100">Audio Input Device</h2>
        <div className="px-3 py-1 rounded-full bg-zinc-700/30 text-xs text-zinc-400">Recording</div>
      </div>
      <div className="space-y-4">
        {renderDeviceSelector()}
        {renderTestButton()}
        {renderDownloadButton()}
        {renderAudioLevelMeter()}
        {renderVolumeControl()}

        {/* Monitoring status message */}
        {isTesting && (
          <div className="text-xs text-zinc-400 italic">
            Audio monitoring is active. You should hear your microphone input.
          </div>
        )}
      </div>
    </div>
  )
}
