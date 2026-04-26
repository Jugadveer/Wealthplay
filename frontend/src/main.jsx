import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

if (
  typeof window !== 'undefined' &&
  window.location.protocol === 'https:' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
) {
  const url = new URL(window.location.href)
  url.protocol = 'http:'
  window.location.replace(url.toString())
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)



