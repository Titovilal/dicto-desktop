import './assets/global.css'

import React from 'react'
import ReactDOM from 'react-dom/client'
import PopupWindow from './components/PopupWindow'

console.log('Popup main script loaded')

// Asegurarse de que el elemento root existe
const rootElement = document.getElementById('root')

if (rootElement) {
  console.log('Root element found, rendering PopupWindow')
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <PopupWindow />
    </React.StrictMode>
  )
} else {
  console.error('Root element not found')
}
