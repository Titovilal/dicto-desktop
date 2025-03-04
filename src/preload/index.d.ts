import { ElectronAPI } from '@electron-toolkit/preload'

declare global {
  interface Window {
    electron: ElectronAPI
  }
}

interface IpcRenderer {
  invoke(channel: 'update-shortcut', shortcut: string): Promise<boolean>
  on(channel: 'toggle-recording', func: () => void): void
  removeAllListeners(channel: string): void
}
