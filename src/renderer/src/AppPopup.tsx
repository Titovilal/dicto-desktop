import React, { useEffect, useState, useCallback } from 'react'
import { Mic, Loader2, CheckCircle2, User } from 'lucide-react'
import debounce from 'lodash/debounce'

type PopupState = 'recording' | 'processing' | 'finished' | 'using'

const AppPopup: React.FC = () => {
  const [state, setState] = useState<PopupState>('recording')
  const [message, setMessage] = useState<string>('')
  const [visible, setVisible] = useState<boolean>(false)
  const [isReady, setIsReady] = useState<boolean>(false)

  // Crear una versión debounced de la función para ocultar
  const debouncedHide = useCallback(
    debounce(() => {
      setVisible(false)
    }, 2000),
    []
  )

  useEffect(() => {
    if (!window.popupAPI) {
      return
    }

    setIsReady(true)

    const stateCleanup = window.popupAPI.onUpdateState((newState) => {
      setState(newState)
      setVisible(true)

      // Cancelar cualquier hide pendiente
      debouncedHide.cancel()

      // Solo para estados 'finished' o 'using', programar ocultamiento
      if (newState === 'finished' || newState === 'using') {
        debouncedHide()
      }
    })

    const messageCleanup = window.popupAPI.onUpdateMessage?.((newMessage) => {
      setMessage(newMessage)
    })

    return (): void => {
      debouncedHide.cancel() // Limpiar cualquier debounce pendiente
      stateCleanup?.()
      messageCleanup?.()
    }
  }, [debouncedHide])

  if (!isReady) return null

  return (
    <div className="fixed bottom-5 right-5">
      <div
        className={`px-6 py-3 bg-zinc-800 border border-zinc-700/50 
                   rounded-xl transition-all duration-300 ease-in-out
                   ${
                     visible
                       ? 'opacity-100 transform translate-y-0'
                       : 'opacity-0 transform translate-y-2 pointer-events-none'
                   }`}
      >
        <div className="flex items-center gap-3">
          {state === 'recording' && (
            <div className="flex items-center">
              <div className="p-2 rounded-full bg-red-500/20 text-red-500">
                <Mic className="w-5 h-5" />
              </div>
              <span className="ml-2 text-sm text-zinc-200">Recording...</span>
            </div>
          )}

          {state === 'processing' && (
            <div className="flex items-center">
              <div className="p-2 rounded-full bg-yellow-500/20 text-yellow-500">
                <Loader2 className="w-5 h-5 animate-spin" />
              </div>
              <span className="ml-2 text-sm text-zinc-200">Processing...</span>
            </div>
          )}

          {state === 'finished' && (
            <div className="flex items-center">
              <div className="p-2 rounded-full bg-emerald-500/20 text-emerald-500">
                <CheckCircle2 className="w-5 h-5" />
              </div>
              <span className="ml-2 text-sm text-zinc-200">Finished!</span>
            </div>
          )}

          {state === 'using' && (
            <div className="flex items-center">
              <div className="p-2 rounded-full bg-blue-500/20 text-blue-500">
                <User className="w-5 h-5" />
              </div>
              <span className="ml-2 text-sm text-zinc-200">{message}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default AppPopup
