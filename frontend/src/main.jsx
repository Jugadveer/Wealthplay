import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import App from './App'
import { initTheme } from './lib/theme'
import './index.css'

// Applied before the first paint so there is no flash of the wrong theme.
initTheme()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
