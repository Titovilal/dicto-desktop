/* eslint-disable @typescript-eslint/no-explicit-any */
export async function invokeIPC(functionName: string, ...args: any[]): Promise<any> {
  return await window.electron.ipcRenderer.invoke(functionName, ...args)
}

export async function sendIPC(functionName: string, ...args: any[]): Promise<void> {
  window.electron.ipcRenderer.send(functionName, ...args)
}
