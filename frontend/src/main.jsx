import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/global.css'
import App from './App.jsx'

// Prevent pinch-to-zoom on iOS Safari
document.addEventListener('gesturestart', function(e) {
  e.preventDefault();
});

// On PWA cold-start (iOS preserves the last in-app URL on resume and often
// ignores start_url), reset to the dashboard. The sessionStorage flag survives
// background/foreground but is cleared when the app process is killed, so
// mid-task resumes are left alone.
const isStandalone =
  window.matchMedia('(display-mode: standalone)').matches ||
  window.navigator.standalone === true;
if (isStandalone && !sessionStorage.getItem('pwa-launched')) {
  sessionStorage.setItem('pwa-launched', '1');
  const { pathname, search, hash } = window.location;
  if (pathname !== '/' && pathname !== '/login') {
    window.history.replaceState(null, '', '/' + (search || '') + (hash || ''));
  }
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
