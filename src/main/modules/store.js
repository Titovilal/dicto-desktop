let Store
let store

async function initStore() {
  Store = (await import('electron-store')).default
  store = new Store({
    defaults: {
      globalShortcut: 'CommandOrControl+Space'
    }
  })
}

export async function saveShortcut(shortcut) {
  if (!store) await initStore()
  store.set('globalShortcut', shortcut)
}

export async function loadShortcut() {
  if (!store) await initStore()
  return store.get('globalShortcut')
}

// Inicializar store inmediatamente
initStore()
