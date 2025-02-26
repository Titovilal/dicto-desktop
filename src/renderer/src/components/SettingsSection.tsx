import { StoreSchema } from '@/types/types'
import { useState, useEffect } from 'react'
import { CaseLower, Volume2, VolumeX, Play, InfoIcon } from 'lucide-react'
import { invokeIPC } from '@/lib/ipc-renderer'
import { useSound } from '@/hooks/useSound'

interface SettingsSectionProps {
  settings: StoreSchema['settings'] | null
  updateSettings: (settings: StoreSchema['settings']) => void
  user: StoreSchema['user'] | null
  updateUser?: (user: StoreSchema['user']) => void
}

function CharactersInfoCard() {
  return (
    <div className="p-4 rounded-lg bg-blue-500/5 border border-blue-500/10">
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <InfoIcon className="w-4 h-4 text-blue-400" />
          <h4 className="text-sm font-medium text-blue-400">About Character Usage</h4>
        </div>
        <div className="space-y-2 text-sm text-zinc-400">
          <p>Characters are counted in two ways:</p>
          <ol className="list-decimal list-inside space-y-1 ml-1">
            <li>When transcribing audio to text</li>
            <li>When processing text with AI models</li>
          </ol>
          <p className="text-xs border-l-2 border-blue-500/20 pl-3 mt-3">
            <span className="text-blue-400">Important:</span> Character count is based on the input
            text, not the AI's response. For example, transcribing a 30-second audio might use 100
            characters, and if you process that text with AI, it will count those same 100
            characters, regardless of how long the AI's response is.
          </p>
          <p className="text-xs text-zinc-500 mt-2">
            Currently, AI processing is free. We plan to add more powerful models in the future
            which may use your available characters.
          </p>
        </div>
      </div>
    </div>
  )
}

export function SettingsSection({
  settings,
  updateSettings,
  user,
  updateUser
}: SettingsSectionProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [apiKey, setApiKey] = useState(settings?.apiKey || '')
  const [isValidating, setIsValidating] = useState(false)
  const [validationStatus, setValidationStatus] = useState<'none' | 'success' | 'error'>('none')

  const { playTestSound } = useSound()

  useEffect(() => {
    const fetchUserData = async () => {
      if (!settings || !settings.apiKey || !updateUser || settings.apiKey !== apiKey) return

      try {
        const userData = await invokeIPC('get-user-data', settings.apiKey)
        updateUser(userData)
      } catch (error) {
        console.error('Error fetching user data:', error)
      }
    }

    fetchUserData()
  }, [])

  const handleShortcutClick = () => {
    setIsRecording(true)
    const handleKeyDown = async (e: KeyboardEvent) => {
      e.preventDefault()

      // Build the shortcut with Electron-compatible format
      const keys: string[] = []

      // Use CommandOrControl instead of Ctrl/Command
      if (e.ctrlKey || e.metaKey) {
        keys.push('CommandOrControl')
      }
      if (e.altKey) keys.push('Alt')
      if (e.shiftKey) keys.push('Shift')

      // Map special keys
      const specialKeys: { [key: string]: string } = {
        ' ': 'Space',
        ArrowUp: 'Up',
        ArrowDown: 'Down',
        ArrowLeft: 'Left',
        ArrowRight: 'Right'
      }

      // Add the main key if it's not a modifier
      if (!['Control', 'Alt', 'Shift', 'Meta'].includes(e.key)) {
        const mainKey = specialKeys[e.key] || (e.key.length === 1 ? e.key.toUpperCase() : e.key)
        keys.push(mainKey)
      }

      const shortcut = keys.join('+')

      // Only update if we have a valid combination (at least one modifier + one key)
      if (keys.length > 1 && settings) {
        updateSettings({ ...settings, recordShortcut: shortcut })
        // Update the global shortcut in the main process
        await invokeIPC('update-shortcut', shortcut)
        setIsRecording(false)
        window.removeEventListener('keydown', handleKeyDown)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
  }

  const handleApiKeyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setApiKey(e.target.value)
    setValidationStatus('none')
  }

  const validateApiKey = async () => {
    if (!updateUser || !settings) return

    setIsValidating(true)
    setValidationStatus('none')

    try {
      const userData = await invokeIPC('get-user-data', apiKey)

      // Verificar explícitamente si hay un error en la respuesta
      if (userData.error || userData.status === 401) {
        throw new Error(userData.error || 'Authentication failed')
      }

      updateUser(userData)
      updateSettings({ ...settings, apiKey })
      setValidationStatus('success')
    } catch (error) {
      console.error('Error validating API key:', error)
      // Reset user data and remove API key from settings
      const emptyUser = {
        name: '',
        email: '',
        otp_credits: 0,
        otp_date_time: '',
        has_subscription: false,
        sub_credits: 0,
        sub_date_time: '',
        cancel_next_month: false,
        has_access: false,
        created_at: '',
        updated_at: ''
      }
      updateUser(emptyUser)
      // Usar undefined para limpiar el valor en lugar de cadena vacía
      updateSettings({ ...settings, apiKey: '' })
      setApiKey('')
      setValidationStatus('error')
    } finally {
      setIsValidating(false)
    }
  }

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!settings) return
    const volume = parseFloat(e.target.value)
    updateSettings({ ...settings, soundVolume: volume })
  }

  const toggleSound = () => {
    if (!settings) return
    updateSettings({ ...settings, soundEnabled: !settings.soundEnabled })
  }

  const handleTestSound = () => {
    if (!settings?.soundEnabled) return
    playTestSound(settings.soundVolume)
  }

  return (
    <section className="h-full flex flex-col">
      <div className="space-y-12 pl-2 overflow-y-auto pr-4 [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-track]:bg-zinc-800/30 [&::-webkit-scrollbar-thumb]:bg-zinc-600/50 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:border-2 [&::-webkit-scrollbar-thumb]:border-zinc-800/30 hover:[&::-webkit-scrollbar-thumb]:bg-zinc-500/50">
        {/* Add Sound Settings Section before the Shortcut Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium text-zinc-100">Sound Settings</h2>
            <div className="px-3 py-1 rounded-full bg-zinc-700/30 text-xs text-zinc-400">
              App-wide
            </div>
          </div>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <button
                onClick={toggleSound}
                className={`p-2 rounded-lg transition-all duration-200 
                  ${
                    settings?.soundEnabled
                      ? 'bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500/30'
                      : 'bg-zinc-700/50 text-zinc-400 hover:bg-zinc-700/70'
                  }`}
              >
                {settings?.soundEnabled ? <Volume2 size={20} /> : <VolumeX size={20} />}
              </button>
              <div className="flex-1">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={settings?.soundVolume ?? 1}
                  onChange={handleVolumeChange}
                  disabled={!settings?.soundEnabled}
                  className={`w-full h-2 rounded-lg appearance-none cursor-pointer 
                    ${
                      settings?.soundEnabled
                        ? 'bg-zinc-700/50'
                        : 'bg-zinc-800/50 cursor-not-allowed'
                    }`}
                />
              </div>
              <span className="text-sm text-zinc-400 w-12">
                {Math.round((settings?.soundVolume ?? 1) * 100)}%
              </span>
              <button
                onClick={handleTestSound}
                disabled={!settings?.soundEnabled}
                className={`p-2 rounded-lg transition-all duration-200
                  ${
                    settings?.soundEnabled
                      ? 'bg-zinc-700/50 text-zinc-300 hover:bg-zinc-700/70'
                      : 'bg-zinc-800/50 text-zinc-600 cursor-not-allowed'
                  }`}
                title="Test Sound"
              >
                <Play size={20} />
              </button>
            </div>
            <p className="text-sm text-zinc-400">
              Adjust the volume of app sounds or disable them completely. Use the play button to
              test the current volume.
            </p>
          </div>
        </div>

        {/* Shortcut Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium text-zinc-100">Recording Shortcut</h2>
            <div className="px-3 py-1 rounded-full bg-zinc-700/30 text-xs text-zinc-400">
              System-wide
            </div>
          </div>
          <div className="space-y-4">
            <div className="relative">
              <button
                onClick={handleShortcutClick}
                className={`w-fit px-6 py-2 rounded-lg text-sm text-left transition-all duration-200
                  ${
                    isRecording
                      ? 'bg-zinc-700/50 border-2 border-emerald-500/50'
                      : 'bg-zinc-800/50 border border-zinc-700/50 hover:bg-zinc-800/70'
                  }
                `}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-2 h-2 rounded-full ${isRecording ? 'bg-emerald-500 animate-pulse' : 'bg-zinc-600'}`}
                  />
                  <span className="text-zinc-100">
                    {isRecording
                      ? 'Press your shortcut...'
                      : settings?.recordShortcut || 'No shortcut set'}
                  </span>
                </div>
              </button>
            </div>
            <p className="text-sm text-zinc-400">
              Click the button above and press your desired key combination to set a global shortcut
            </p>
          </div>
        </div>

        {/* API Key Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium text-zinc-100">API Key</h2>
            <div className="px-3 py-1 rounded-full bg-zinc-700/30 text-xs text-zinc-400">
              Required
            </div>
          </div>
          <div className="space-y-4">
            <div className="relative">
              <div className="relative">
                <input
                  type="password"
                  value={apiKey}
                  onChange={handleApiKeyChange}
                  placeholder="Enter your API key"
                  className={`w-full px-6 py-2 text-sm pr-28 rounded-lg bg-zinc-800/50 text-zinc-100 transition-all duration-200
                    ${
                      validationStatus === 'success'
                        ? 'border-2 border-emerald-500/50'
                        : validationStatus === 'error'
                          ? 'border-2 border-red-500/50'
                          : 'border border-zinc-700/50'
                    }
                    focus:outline-none focus:border-zinc-600 placeholder:text-zinc-600`}
                />
                <button
                  onClick={validateApiKey}
                  disabled={isValidating || !apiKey}
                  className={`absolute right-1 top-1/2 -translate-y-1/2 px-2 py-1 rounded-lg text-sm font-medium transition-all duration-200
                    ${
                      isValidating
                        ? 'bg-zinc-700/50 text-zinc-400'
                        : validationStatus === 'success'
                          ? 'bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500/30'
                          : 'bg-zinc-700/50 text-zinc-300 hover:bg-zinc-700/70'
                    }
                    disabled:bg-zinc-800/30 disabled:text-zinc-600 disabled:cursor-not-allowed`}
                >
                  {isValidating
                    ? 'Validating...'
                    : validationStatus === 'success'
                      ? 'Validated'
                      : validationStatus === 'error'
                        ? 'Not Validated'
                        : 'Validate'}
                </button>
              </div>
            </div>

            <div className="flex items-center gap-2 px-1">
              {validationStatus === 'success' && (
                <div className="flex items-center gap-2 text-emerald-500">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  <p className="text-sm">API key validated successfully</p>
                </div>
              )}
              {validationStatus === 'error' && (
                <div className="flex items-center gap-2 text-red-500">
                  <div className="w-1.5 h-1.5 rounded-full bg-red-500" />
                  <p className="text-sm">Invalid API key. Please try again.</p>
                </div>
              )}
              {validationStatus === 'none' && (
                <div className="flex items-center gap-2 text-zinc-400">
                  <div className="w-1.5 h-1.5 rounded-full bg-zinc-400" />
                  <p className="text-sm">Enter your API key and click validate to verify</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Account Information Section */}
        {user && user.email && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-medium text-zinc-100">Account Information</h2>
              <div className="px-3 py-1 rounded-full bg-zinc-700/30 text-xs text-zinc-400">
                Information
              </div>
            </div>

            <CharactersInfoCard />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Personal Information */}
              <div className="space-y-3 p-4 rounded-lg bg-zinc-800/50 border border-zinc-700/50">
                <h3 className="text-sm font-medium text-zinc-200">Personal Details</h3>
                <div className="space-y-2">
                  <div className="flex flex-col">
                    <span className="text-xs text-zinc-400">Name</span>
                    <span className="text-sm text-zinc-100">{user.name}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-xs text-zinc-400">Email</span>
                    <span className="text-sm text-zinc-100">{user.email}</span>
                  </div>
                </div>
              </div>

              {/* Credits Information */}
              <div className="space-y-3 p-4 rounded-lg bg-zinc-800/50 border border-zinc-700/50">
                <h3 className="text-sm font-medium text-zinc-200">One Time Characters</h3>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-zinc-400">One Time Characters</span>
                    <span className="text-sm text-zinc-100 flex items-end gap-1">
                      {user.otp_credits.toLocaleString()} <CaseLower className="w-4 h-4" />
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-zinc-400">Last Purchase</span>
                    <span className="text-sm text-zinc-100">
                      {user.otp_date_time && new Date(user.otp_date_time).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Subscription Information */}
              <div className="space-y-3 p-4 rounded-lg bg-zinc-800/50 border border-zinc-700/50 md:col-span-2">
                <h3 className="text-sm font-medium text-zinc-200">Subscription Details</h3>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-zinc-400">Status</span>
                    <span
                      className={`text-sm ${user.has_subscription ? 'text-emerald-400' : 'text-zinc-100'}`}
                    >
                      {user.has_subscription ? 'Active' : 'No subscription'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-zinc-400">Characters</span>
                    <span className="text-sm text-zinc-100 flex items-end gap-1">
                      {user.sub_credits.toLocaleString()} <CaseLower className="w-4 h-4" />
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-zinc-400">Renewal Date</span>
                    <span className="text-sm text-zinc-100">
                      {user.sub_date_time
                        ? new Date(user.sub_date_time).toLocaleDateString()
                        : 'None'}
                    </span>
                  </div>
                  {user.has_subscription && (
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-zinc-400">Auto-Renewal</span>
                      <span
                        className={`text-sm ${user.cancel_next_month ? 'text-red-400' : 'text-emerald-400'}`}
                      >
                        {user.cancel_next_month ? 'Disabled' : 'Enabled'}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
