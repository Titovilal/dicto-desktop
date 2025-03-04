import { createPortal } from 'react-dom'
import { LANGUAGES } from '@/lib/languages'

interface LanguageDropdownProps {
  isOpen: boolean
  onClose: () => void
  selectedLanguage: string
  onSelectLanguage: (key: string) => void
  buttonRef: React.RefObject<HTMLButtonElement>
}

export function LanguageDropdown({
  isOpen,
  selectedLanguage,
  onSelectLanguage,
  buttonRef
}: LanguageDropdownProps) {
  if (!isOpen || !buttonRef.current) return null

  const rect = buttonRef.current.getBoundingClientRect()
  const dropdownStyle = {
    position: 'fixed' as const,
    top: `${rect.bottom + 8}px`,
    left: `${rect.left}px`,
    width: `${rect.width}px`,
    zIndex: 9999
  }

  return createPortal(
    <div
      style={dropdownStyle}
      className="py-1 bg-zinc-800/95 backdrop-blur-sm rounded-lg border border-zinc-700/30 shadow-lg max-h-[200px] overflow-y-auto pr-2 [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-track]:bg-zinc-800/30 [&::-webkit-scrollbar-thumb]:bg-zinc-600/50 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:border-2 [&::-webkit-scrollbar-thumb]:border-zinc-800/30 hover:[&::-webkit-scrollbar-thumb]:bg-zinc-500/50"
    >
      {Object.entries(LANGUAGES).map(([key, value]) => (
        <button
          key={key}
          className={`w-full px-4 py-2 text-left rounded-r-lg text-sm transition-colors flex items-center justify-between ${
            key === selectedLanguage
              ? 'text-emerald-500 bg-emerald-500/10'
              : 'text-zinc-300 hover:bg-zinc-700/50'
          }`}
          onClick={() => onSelectLanguage(key)}
        >
          {value}
          {key === selectedLanguage && <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />}
        </button>
      ))}
    </div>,
    document.body
  )
}
