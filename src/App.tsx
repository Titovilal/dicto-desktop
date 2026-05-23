import { HashRouter, Routes, Route } from 'react-router-dom'
import MainWindow from './pages/MainWindow'
import OverlayWindow from './pages/OverlayWindow'
import SplashScreen from './components/ui/SplashScreen'
import { useConfig } from './hooks/useConfig'
import './i18n'

function App() {
  const { loading } = useConfig()

  if (loading) {
    return <SplashScreen />
  }

  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<MainWindow />} />
        <Route path="/overlay" element={<OverlayWindow />} />
      </Routes>
    </HashRouter>
  )
}

export default App
