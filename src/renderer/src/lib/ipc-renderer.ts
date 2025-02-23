export async function invokeIPC(functionName: string, ...args: any[]) {
    return await window.electron.ipcRenderer.invoke(functionName, ...args)
}

export async function sendIPC(functionName: string, ...args: any[]) {
    window.electron.ipcRenderer.send(functionName, ...args)
}
