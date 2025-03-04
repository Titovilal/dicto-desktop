import './assets/global.css'

import React from 'react'
import ReactDOM from 'react-dom/client'
import AppPopup from './AppPopup'

console.log('Popup main script loaded')

// Asegurarse de que el elemento root existe
const rootElement = document.getElementById('root')

if (rootElement) {
  console.log('Root element found, rendering AppPopup')
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <AppPopup />
    </React.StrictMode>
  )
} else {
  console.error('Root element not found')
}
