import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';

// Limpiar cache y forzar recarga
const clearCacheAndReload = () => {
  // Limpiar todos los tipos de cache
  if ('caches' in window) {
    caches.keys().then(names => {
      names.forEach(name => {
        caches.delete(name);
      });
    });
  }
  
  // Limpiar localStorage
  localStorage.clear();
  
  // Limpiar sessionStorage
  sessionStorage.clear();
  
  // Forzar recarga con timestamp
  const timestamp = new Date().getTime();
  window.location.href = window.location.href.split('?')[0] + '?v=' + timestamp;
};

// Montar React inmediatamente
const appElement = document.getElementById('app');
if (appElement) {
  const root = createRoot(appElement);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
  
  // Ocultar loading screen después de montar React
  setTimeout(() => {
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
      loadingScreen.style.display = 'none';
    }
  }, 2000);
  
  // Forzar limpieza de cache cada 30 segundos
  setInterval(() => {
    const lastClear = localStorage.getItem('lastCacheClear');
    const now = new Date().getTime();
    if (!lastClear || (now - parseInt(lastClear)) > 30000) {
      clearCacheAndReload();
      localStorage.setItem('lastCacheClear', now.toString());
    }
  }, 10000);
} else {
  console.error('Element #app not found');
}
