/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect } from 'react'
import { RotateCw } from 'lucide-react'

export function UpdateButton(): JSX.Element | null {
  const [updateReady, setUpdateReady] = useState(false)
  const [isInitialized, setIsInitialized] = useState(false)

  useEffect(() => {
    // Check if there's a pending update that was already downloaded
    window.electron.ipcRenderer
      .invoke('is-update-downloaded')
      .then((isDownloaded: boolean) => {
        if (isDownloaded) {
          window.logger.info('[UpdateButton] Update already downloaded')
          setUpdateReady(true)
        }
        setIsInitialized(true)
      })
      .catch((err) => {
        window.logger.error('[UpdateButton] Error checking for downloaded updates:')
        window.logger.error(err)
        setIsInitialized(true)
      })

    // Listen for update-downloaded event
    window.electron.ipcRenderer.on('update-downloaded', () => {
      window.logger.info('[UpdateButton] Received update-downloaded event')
      setUpdateReady(true)
    })

    // Request check for updates after setting up listeners
    window.logger.info('[UpdateButton] Requesting check for updates')
    window.electron.ipcRenderer.send('check-for-updates')

    return (): void => {
      // Cleanup listeners
      window.electron.ipcRenderer.removeAllListeners('update-downloaded')
    }
  }, [])

  const handleRestartAndInstall = (): void => {
    window.logger.info('[UpdateButton] Restart and install requested')
    window.electron.ipcRenderer.send('restart-and-install')
  }

  // Si no está inicializado, no mostramos nada
  if (!isInitialized || !updateReady) {
    return null
  }

  // Solo mostrar cuando hay una actualización lista
  return (
    <div
      onClick={handleRestartAndInstall}
      className="flex items-center gap-2 px-3 py-2 text-xs text-green-400 hover:bg-zinc-800 cursor-pointer transition-colors duration-200 rounded-md mx-2 mb-2"
      title="Restart to install update"
    >
      <RotateCw className="w-4 h-4" />
      <span>Update Here</span>
    </div>
  )
}
