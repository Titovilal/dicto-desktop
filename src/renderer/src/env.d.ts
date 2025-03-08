/* eslint-disable @typescript-eslint/no-explicit-any */
/// <reference types="vite/client" />

interface LoggerAPI {
  log: (message: string) => void
  info: (message: string) => void
  warn: (message: string) => void
  error: (message: string) => void
  debug: (message: string) => void
}

interface ElectronAPI {
  // Your existing ElectronAPI definition
  ipcRenderer: {
    invoke: (channel: string, ...args: any[]) => Promise<any>
    send: (channel: string, ...args: any[]) => void
    on: (channel: string, listener: (...args: any[]) => void) => void
    removeAllListeners: (channel: string) => void
  }
}

interface Window {
  electron: ElectronAPI
  logger: LoggerAPI
}
