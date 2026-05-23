import { useState, useEffect } from 'react'
import { listen } from '@tauri-apps/api/event'
import { invoke } from '@tauri-apps/api/core'
import { getCurrentWindow } from '@tauri-apps/api/window'
import Waveform from '../components/ui/Waveform'
import { AppStatus } from '../types'
import { useTranslation } from 'react-i18next'

export default function OverlayWindow() {
  const [status, setStatus] = useState<AppStatus>('idle')
  const [audioLevel, setAudioLevel] = useState(0)
  const [showMenu, setShowMenu] = useState(false)
  const { t } = useTranslation()

  useEffect(() => {
    const unlisteners: Array<() => void> = []

    listen<{ status: AppStatus }>('app-status-changed', (e) => {
      setStatus(e.payload.status)
    }).then(u => unlisteners.push(u))

    listen<{ level: number }>('audio-level', (e) => {
      setAudioLevel(e.payload.level)
    }).then(u => unlisteners.push(u))

    return () => unlisteners.forEach(u => u())
  }, [])

  async function handleMouseDown() {
    const win = getCurrentWindow()
    await win.startDragging()
  }

  const statusColors: Record<AppStatus, string> = {
    idle: 'bg-gray-800/90',
    recording: 'bg-red-900/90',
    processing: 'bg-amber-900/90',
    editing: 'bg-blue-900/90',
    success: 'bg-green-900/90',
    error: 'bg-red-950/90',
  }

  return (
    <div className="w-screen h-screen flex items-center justify-center bg-transparent select-none">
      <div
        className={`flex items-center gap-3 px-4 py-3 rounded-2xl shadow-2xl ${statusColors[status]} text-white cursor-grab active:cursor-grabbing transition-colors duration-300`}
        onMouseDown={handleMouseDown}
        style={{ backdropFilter: 'blur(12px)', border: '1px solid rgba(255,255,255,0.1)' }}
      >
        <StatusDot status={status} />

        <span className="text-sm font-medium min-w-[80px]">
          {t(`app.status.${status}`, { defaultValue: status })}
        </span>

        {status === 'recording' && (
          <Waveform level={audioLevel} bars={8} color="white" />
        )}

        <button
          className="ml-1 opacity-60 hover:opacity-100 transition-opacity text-lg leading-none"
          onMouseDown={e => e.stopPropagation()}
          onClick={() => setShowMenu(!showMenu)}
        >
          ⋯
        </button>
      </div>

      {showMenu && (
        <OverlayMenu onClose={() => setShowMenu(false)} />
      )}
    </div>
  )
}

function StatusDot({ status }: { status: AppStatus }) {
  const colors: Record<AppStatus, string> = {
    idle: 'bg-gray-400',
    recording: 'bg-red-400 animate-pulse',
    processing: 'bg-amber-400 animate-spin',
    editing: 'bg-blue-400 animate-pulse',
    success: 'bg-green-400',
    error: 'bg-red-600',
  }
  return <div className={`w-2.5 h-2.5 rounded-full ${colors[status]}`} />
}

function OverlayMenu({ onClose }: { onClose: () => void }) {
  return (
    <div className="absolute bottom-full mb-2 right-0 bg-gray-900 rounded-xl p-2 shadow-2xl border border-white/10 min-w-[160px]">
      <button
        className="w-full text-left px-3 py-2 text-sm text-white hover:bg-white/10 rounded-lg"
        onClick={async () => {
          await invoke('show_main_window')
          onClose()
        }}
      >
        Abrir app
      </button>
      <button
        className="w-full text-left px-3 py-2 text-sm text-white hover:bg-white/10 rounded-lg"
        onClick={async () => {
          const win = getCurrentWindow()
          await win.hide()
          onClose()
        }}
      >
        Ocultar overlay
      </button>
      <button
        className="w-full text-left px-3 py-2 text-sm text-white hover:bg-white/10 rounded-lg"
        onClick={async () => {
          const win = getCurrentWindow()
          const { PhysicalPosition } = await import('@tauri-apps/api/dpi')
          await win.setPosition(new PhysicalPosition(100, 100))
          onClose()
        }}
      >
        Resetear posición
      </button>
    </div>
  )
}
