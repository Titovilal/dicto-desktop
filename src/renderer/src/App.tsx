import { useState, useEffect } from 'react'
import { Sidebar } from './components/ui/Sidebar'
import { HomeSection } from './components/HomeSection'
import { ProfilesSection } from './components/ProfilesSection'
import { SettingsSection } from './components/SettingsSection'
import { useStore } from './hooks/useStore'
import { Paintbrush2, Mic, Bot, Keyboard } from 'lucide-react'
import { useRecord } from './hooks/useRecord'
import { sendIPC } from './lib/ipc-renderer'

function App(): JSX.Element {
  const [currentSection, setCurrentSection] = useState('home')
  const [isStartingApp, setIsStartingApp] = useState(true)
  const [isCompactMode, setIsCompactMode] = useState(false)

  const toggleCompactMode = () => {
    if (!isCompactMode) {
      setCurrentSection('home')
      setIsCompactMode(true)
      sendIPC('toggle-compact-mode', true)
    } else {
      setIsCompactMode(false)
      sendIPC('toggle-compact-mode', false)
    }
  }

  const {
    profiles,
    addProfile,
    updateProfile,
    deleteProfile,
    updateSelectedProfile,
    settings,
    updateSettings,
    user,
    updateUser
  } = useStore()

  const {
    isRecording,
    isProcessing,
    transcription,
    processedText,
    handleToggleRecording,
    cancelRecording
  } = useRecord()

  const loadingIcons = [
    { icon: Paintbrush2, color: '#f59e0b', phrase: 'Painting the interface...' },
    { icon: Mic, color: '#3b82f6', phrase: 'Testing the microphone...' },
    { icon: Keyboard, color: '#06b6d4', phrase: 'Pounding the keyboard...' },
    { icon: Bot, color: '#8b5cf6', phrase: 'Waking up the AI...' }
  ]

  const [loadingIconIndex, setLoadingIconIndex] = useState(0)

  useEffect(() => {
    const iconInterval = setInterval(() => {
      setLoadingIconIndex((prev) => (prev + 1) % loadingIcons.length)
    }, 500)

    setTimeout(() => {
      setIsStartingApp(false)
    }, 2000)

    return () => {
      clearInterval(iconInterval)
    }
  }, [])

  useEffect(() => {
    const handleShortcutToggle = () => {
      if (settings && profiles.length > 0) {
        handleToggleRecording(settings, profiles)
      } else {
        console.error('[APP] Settings or profiles not loaded yet')
      }
    }

    window.electron.ipcRenderer.removeAllListeners('toggle-recording')
    window.electron.ipcRenderer.on('toggle-recording', handleShortcutToggle)

    return () => {
      window.electron.ipcRenderer.removeAllListeners('toggle-recording')
    }
  }, [settings, profiles, handleToggleRecording])

  if (isStartingApp) {
    const CurrentIcon = loadingIcons[loadingIconIndex].icon
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-zinc-900">
        <div className="relative">
          <div className="w-20 h-20 border-4 border-zinc-700 border-t-zinc-100 rounded-full animate-spin"></div>
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
            <CurrentIcon
              className="w-8 h-8"
              style={{ color: loadingIcons[loadingIconIndex].color }}
            />
          </div>
        </div>
        <h2 className="mt-6 text-zinc-100 text-lg font-medium animate-fade-in">
          {loadingIcons[loadingIconIndex].phrase}
        </h2>
      </div>
    )
  }

  return (
    <div className="flex bg-zinc-900 h-screen">
      {!isCompactMode && (
        <Sidebar
          currentSection={currentSection}
          onSectionChange={setCurrentSection}
          onToggleCompactMode={toggleCompactMode}
        />
      )}

      <main className={`flex-1 p-6 ${!isCompactMode ? 'ml-42' : ''} h-full overflow-hidden`}>
        {currentSection === 'home' && (
          <HomeSection
            isRecording={isRecording}
            onToggleRecording={() => handleToggleRecording(settings!, profiles)}
            onCancelRecording={() => cancelRecording(settings!)}
            transcription={transcription}
            processedText={processedText}
            profiles={profiles}
            onSelectProfile={updateSelectedProfile}
            isProcessing={isProcessing}
            settings={settings}
            isCompactMode={isCompactMode}
            onExitCompactMode={toggleCompactMode}
          />
        )}
        {currentSection === 'profiles' && (
          <ProfilesSection
            profiles={profiles}
            onAddProfile={addProfile}
            onUpdateProfile={updateProfile}
            onDeleteProfile={deleteProfile}
            onSelectProfile={updateSelectedProfile}
            settings={settings}
          />
        )}
        {currentSection === 'settings' && (
          <SettingsSection
            settings={settings}
            updateSettings={updateSettings}
            user={user}
            updateUser={updateUser}
          />
        )}
      </main>
    </div>
  )
}

export default App
