import React, { useEffect, useState, useRef } from 'react'
import { Mic, Loader2, CheckCircle2 } from 'lucide-react'

type PopupState = 'recording' | 'processing' | 'finished'

const PopupWindow: React.FC = () => {
  const [state, setState] = useState<PopupState>('recording')
  const stateRef = useRef(state)

  // Actualizar la referencia cuando cambia el estado
  useEffect(() => {
    stateRef.current = state
    console.log('State updated to:', state)
  }, [state])

  useEffect(() => {
    console.log('PopupWindow mounted, initial state:', state)
    console.log('window.popupAPI available:', !!window.popupAPI)

    if (window.popupAPI && window.popupAPI.onUpdateState) {
      console.log('Registering onUpdateState callback')

      const cleanup = window.popupAPI.onUpdateState((newState) => {
        console.log('Callback received state update:', newState, 'Current state:', stateRef.current)
        setState(newState)
      })

      return cleanup
    } else {
      console.error('popupAPI is not available')
    }
  }, [])

  return (
    <div className="flex items-center justify-center h-screen w-full">
      <div className="px-4 py-3 bg-zinc-800 backdrop-blur-sm w-full border border-zinc-700/50 rounded-full shadow-lg">
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
              <span className="ml-2 text-sm text-zinc-200">Done!</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default PopupWindow
