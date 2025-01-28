import { ref } from 'vue'

export function useAI() {
  const isProcessing = ref(false)
  const error = ref('')

  const processWithAI = async (text, prompt) => {
    try {
      isProcessing.value = true
      error.value = ''

      const result = await window.electron.ipcRenderer.invoke('process-with-ai', {
        text,
        prompt
      })

      return result
    } catch (err) {
      error.value = `AI Processing Error: ${err.message}`
      return null
    } finally {
      isProcessing.value = false
    }
  }

  return {
    processWithAI,
    isProcessing,
    error
  }
}
