import { invokeIPC } from '@/lib/ipc-renderer'
import { Home, Users, Settings, LineChart, Minimize2, LucideIcon } from 'lucide-react' // Add Minimize2

interface SidebarButtonProps {
  icon: LucideIcon
  label: string
  isActive?: boolean
  onClick: () => void
}

function SidebarButton({ icon: Icon, label, isActive, onClick }: SidebarButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-200 ${
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

export function Sidebar({ currentSection, onSectionChange, onToggleCompactMode }: SidebarProps) {
  const openDashboard = () => {
    invokeIPC('open-external', 'https://dicto.io/dashboard')
  }

  return (
    <aside className="bg-zinc-900 border-r border-zinc-800 backdrop-blur-lg bg-opacity-80 w-42 h-screen fixed left-0 top-0">
      <div className="flex flex-col h-full p-4">
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
          <SidebarButton icon={Minimize2} label="Compact" onClick={onToggleCompactMode} />
          <SidebarButton icon={LineChart} label="Dicto Web" onClick={openDashboard} />
        </nav>

        <div className="mt-auto flex flex-col gap-2">
          <div className="text-zinc-500 text-sm text-center font-medium tracking-wide">
            Made with ❤️
          </div>
        </div>
      </div>
    </aside>
  )
}
