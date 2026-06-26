import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'

// GitHub Pages SPA redirect: if 404.html redirected here, restore the path
;(() => {
  const redirect = sessionStorage.getItem('redirect')
  if (redirect) {
    sessionStorage.removeItem('redirect')
    history.replaceState(null, '', redirect)
  }
})()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
