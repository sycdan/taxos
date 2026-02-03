import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { TaxosProvider } from './contexts/TaxosContext'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <TaxosProvider>
      <App />
    </TaxosProvider>
  </StrictMode>,
)
