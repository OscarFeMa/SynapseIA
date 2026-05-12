import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import SynapseLogo from './SynapseLogo';

const Navbar = ({ darkMode, setDarkMode, branding }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  const navItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/debates', label: 'Debates', icon: '🧠' },
    { path: '/workers', label: 'Workers', icon: '🔗' },
    { path: '/metrics', label: 'Métricas', icon: '📈' },
    { path: '/settings', label: 'Configuración', icon: '⚙️' }
  ];

  return (
    <nav className="bg-black bg-opacity-80 backdrop-blur-md border-b border-blue-500 border-opacity-30 sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo y branding */}
          <Link to="/" className="flex items-center space-x-3">
            <SynapseLogo size="small" animated={false} theme="neural_network" />
            <div className="hidden md:block">
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
                {branding.name}
              </h1>
              <p className="text-xs text-gray-400 italic">
                {branding.tagline}
              </p>
            </div>
          </Link>

          {/* Navigation Desktop */}
          <div className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive(item.path)
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'text-gray-300 hover:text-white hover:bg-gray-700'
                }`}
              >
                <span className="mr-2">{item.icon}</span>
                {item.label}
              </Link>
            ))}
          </div>

          {/* Right side controls */}
          <div className="flex items-center space-x-4">
            {/* Theme selector */}
            <select
              id="theme-selector"
              name="theme-selector"
              value={darkMode ? 'dark' : 'light'}
              onChange={(e) => setDarkMode(e.target.value === 'dark')}
              className="bg-gray-900 text-gray-300 px-3 py-2 rounded-lg border border-gray-700 focus:border-blue-500 focus:outline-none text-sm"
            >
              <option value="light">🌞 Light</option>
              <option value="dark">🌞 Dark</option>
            </select>

            {/* User menu */}
            <div className="relative">
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16m-7 6h7m-7 6h7" />
                </svg>
              </button>
              
              {/* Dropdown menu */}
              {isMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-gray-900 rounded-lg shadow-xl border border-gray-700">
                  <div className="py-1">
                    <Link
                      to="/settings"
                      className="block px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      ⚙️ Configuración
                    </Link>
                    <Link
                      to="/metrics"
                      className="block px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white"
                      onClick={() => setIsMenuOpen(false)}
                    >
                      📈 Métricas
                    </Link>
                    <div className="border-t border-gray-700 my-1"></div>
                    <button
                      className="block w-full text-left px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-white"
                      onClick={() => {
                        setDarkMode(!darkMode);
                        setIsMenuOpen(false);
                      }}
                    >
                      {darkMode ? '🌞 Modo Light' : '🌞 Modo Dark'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16m-7 6h7m-7 6h7" />
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden absolute top-16 left-0 right-0 bg-gray-900 border-b border-gray-700">
            <div className="px-2 py-3 space-y-1">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`block px-3 py-2 rounded-lg text-base font-medium transition-all duration-200 ${
                    isActive(item.path)
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:text-white hover:bg-gray-700'
                  }`}
                  onClick={() => setIsMenuOpen(false)}
                >
                  <span className="mr-3">{item.icon}</span>
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
