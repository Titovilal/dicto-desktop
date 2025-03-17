/* eslint-disable @typescript-eslint/no-explicit-any */
interface IpcRenderer {
  invoke(channel: string, ...args: any[]): Promise<any>
  send(channel: string, ...args: any[]): void
}

interface ElectronAPI {
  ipcRenderer: IpcRenderer
}

declare global {
  interface Window {
    electron: ElectronAPI
  }
}

export {}
