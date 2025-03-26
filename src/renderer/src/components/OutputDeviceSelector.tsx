import { StoreSchema } from '@/types/types'
import { useState, useEffect } from 'react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/Select'

interface OutputDeviceSelectorProps {
  settings: StoreSchema['settings'] | null
  updateSettings: (settings: StoreSchema['settings']) => void
}

export function OutputDeviceSelector({
  settings,
  updateSettings
}: OutputDeviceSelectorProps): JSX.Element {
  const [outputDevices, setOutputDevices] = useState<MediaDeviceInfo[]>([])

  useEffect(() => {
    // Get output audio devices
    const getOutputDevices = async (): Promise<void> => {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices()
        const audioOutputDevices = devices.filter(
          (device) => device.kind === 'audiooutput' && device.deviceId !== 'communications'
        )
        setOutputDevices(audioOutputDevices)
      } catch (error) {
        console.error('Error getting output devices:', error)
      }
    }

    getOutputDevices()
  }, [])

  const handleOutputDeviceChange = (deviceId: string): void => {
    if (!settings) return
    updateSettings({ ...settings, outputDevice: deviceId })
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium text-zinc-100">Output Audio Device</h2>
        <div className="px-3 py-1 rounded-full bg-zinc-700/30 text-xs text-zinc-400">App-wide</div>
      </div>
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <Select
              value={settings?.outputDevice || 'default'}
              onValueChange={handleOutputDeviceChange}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select output device" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="default">Default Output Device</SelectItem>
                {outputDevices.map((device) => (
                  <SelectItem key={device.deviceId} value={device.deviceId}>
                    {device.label || `Output Device ${device.deviceId.slice(0, 5)}...`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <p className="text-sm text-zinc-400">
          Select which audio output device to use for app sounds. Changes will apply immediately.
        </p>
      </div>
    </div>
  )
}
