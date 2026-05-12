import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Debates from './pages/Debates';
import Workers from './pages/Workers';
import Metrics from './pages/Metrics';
import Settings from './pages/Settings';
import NeuralBackground from './components/NeuralBackground';
import SynapseLogo from './components/SynapseLogo';
// import { get_synapse_branding } from '../../backend/branding/synapse_identity';
import './App.css';

function App() {
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem('darkMode') === 'true';
  });
  const [theme, setTheme] = useState('neural_network');
  const [branding, setBranding] = useState({
    name: "SynapseIA",
    tagline: "Conectando Mentes, Amplificando Inteligencia",
    mission: "Crear un espacio donde la inteligencia colectiva florece a través del debate estructurado"
  });

  useEffect(() => {
    localStorage.setItem('darkMode', darkMode);
    localStorage.setItem('theme', theme);
    if (darkMode) {
      document.body.classList.add('dark');
    } else {
      document.body.classList.remove('dark');
    }
  }, [darkMode, theme]);

  return (
    <div className={`min-h-screen ${darkMode ? 'dark' : ''}`}>
      <NeuralBackground theme={theme}>
        <div className="relative z-10">
          {/* Header con branding único */}
          <header className="bg-black bg-opacity-80 backdrop-blur-md border-b border-blue-500 border-opacity-30">
            <div className="container mx-auto px-4 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <SynapseLogo size="medium" animated={false} theme={theme} />
                  <div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
                      {branding.name}
                    </h1>
                    <p className="text-sm text-gray-400 italic">
                      {branding.tagline}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  {/* Selector de tema */}
                  <select
                    id="app-theme-selector"
                    name="app-theme-selector"
                    value={theme}
                    onChange={(e) => setTheme(e.target.value)}
                    className="bg-gray-900 text-gray-300 px-3 py-2 rounded-lg border border-gray-700 focus:border-blue-500 focus:outline-none text-sm"
                  >
                    <option value="neural_network">Red Neuronal</option>
                    <option value="quantum_realm">Reino Cuántico</option>
                    <option value="cosmic_consciousness">Conciencia Cósmica</option>
                    <option value="digital_synapse">Sinapsis Digital</option>
                  </select>
                  
                  {/* Toggle dark mode */}
                  <button
                    onClick={() => setDarkMode(!darkMode)}
                    className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors"
                  >
                    {darkMode ? '🌞' : '🌞'}
                  </button>
                </div>
              </div>
            </div>
          </header>

          <Router>
            <Navbar darkMode={darkMode} setDarkMode={setDarkMode} branding={branding} />
            <main className="container mx-auto px-4 py-8">
              <Routes>
                <Route path="/" element={<Dashboard theme={theme} branding={branding} />} />
                <Route path="/debates" element={<Debates theme={theme} branding={branding} />} />
                <Route path="/workers" element={<Workers theme={theme} branding={branding} />} />
                <Route path="/metrics" element={<Metrics theme={theme} branding={branding} />} />
                <Route path="/settings" element={<Settings theme={theme} branding={branding} />} />
              </Routes>
            </main>
          </Router>
          
          {/* Footer con branding */}
          <footer className="bg-black bg-opacity-90 backdrop-blur-md border-t border-blue-500 border-opacity-30 mt-12">
            <div className="container mx-auto px-4 py-6">
              <div className="text-center">
                <p className="text-gray-400 text-sm">
                  🧠 {branding.mission}
                </p>
                <p className="text-gray-500 text-xs mt-2">
                  Powered by <span className="text-blue-400 font-semibold">SynapseIA</span> - Conectando Mentes, Amplificando Inteligencia
                </p>
              </div>
            </div>
          </footer>
        </div>
      </NeuralBackground>
    </div>
  );
}

export default App;
