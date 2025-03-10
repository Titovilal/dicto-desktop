import { sendIPC } from '@/lib/ipc-renderer'
import {
  Home,
  Users,
  Settings,
  Minimize2,
  LucideIcon,
  LayoutDashboard,
  FlaskConical
} from 'lucide-react'
import { UpdateButton } from './UpdateButton'
import { useState, useEffect } from 'react'

interface SidebarButtonProps {
  icon: LucideIcon
  label: string
  isActive?: boolean
  onClick: () => void
}

export function SidebarButton({
  icon: Icon,
  label,
  isActive,
  onClick
}: SidebarButtonProps): JSX.Element {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-all duration-200 ${
        isActive
          ? 'bg-zinc-700/50 text-zinc-100'
          : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/50'
      }`}
    >
      <Icon size={18} />
      <span className="text-sm font-medium">{label}</span>
    </button>
  )
}

interface SidebarProps {
  currentSection: string
  onSectionChange: (section: string) => void
  onToggleCompactMode: () => void
}

export function Sidebar({
  currentSection,
  onSectionChange,
  onToggleCompactMode
}: SidebarProps): JSX.Element {
  const [appVersion, setAppVersion] = useState<string>('')

  useEffect(() => {
    // Get app version from main process
    window.electron.ipcRenderer.invoke('get-app-version').then((version) => {
      setAppVersion(version)
    })
  }, [])

  const openDashboard = (): void => {
    sendIPC('open-external', 'https://dicto.io/dashboard')
  }

  return (
    <aside className="bg-zinc-900 border-r border-zinc-800 backdrop-blur-lg bg-opacity-80 w-42 h-screen fixed left-0 top-0">
      <div className="flex flex-col h-full p-4">
        {/* Main Navigation */}
        <div className="flex items-center gap-2 text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 px-4">
          All you need
        </div>
        <nav className="flex flex-col gap-2">
          <SidebarButton
            icon={Home}
            label="Home"
            isActive={currentSection === 'home'}
            onClick={() => onSectionChange('home')}
          />
          <SidebarButton
            icon={Users}
            label="Profiles"
            isActive={currentSection === 'profiles'}
            onClick={() => onSectionChange('profiles')}
          />
          <SidebarButton
            icon={Settings}
            label="Settings"
            isActive={currentSection === 'settings'}
            onClick={() => onSectionChange('settings')}
          />
        </nav>

        {/* Tools Section */}
        <div className="mt-6">
          <div className="flex items-center gap-2 text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 px-4">
            TOOLS
          </div>
          <nav className="flex flex-col gap-2">
            <SidebarButton icon={Minimize2} label="Compact" onClick={onToggleCompactMode} />
          </nav>
        </div>

        {/* External Links */}
        <div className="mt-6 ">
          <div className="flex items-center gap-2 text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 px-4">
            LINKS
          </div>
          <nav className="flex flex-col gap-2">
            <SidebarButton icon={LayoutDashboard} label="Dashboard" onClick={openDashboard} />
            <SidebarButton icon={FlaskConical} label="Playground" onClick={openDashboard} />
          </nav>
        </div>

        <div className="mt-auto flex flex-col gap-4">
          <UpdateButton />
          <div className="text-zinc-500 text-xs text-center">
            {appVersion && <div className="opacity-75"></div>}
            <div className="font-medium tracking-wide mb-1">(v{appVersion}) Made with ❤️</div>
          </div>
        </div>
      </div>
    </aside>
  )
}
