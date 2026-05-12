import React, { useState, useEffect } from 'react';
import SynapseLogo from '../components/SynapseLogo';

const Settings = ({ theme, branding }) => {
  const [settings, setSettings] = useState({
    theme: 'neural_network',
    darkMode: true,
    autoRefresh: true,
    refreshInterval: 5,
    notifications: true,
    soundEnabled: false,
    language: 'es',
    maxDebates: 10,
    workerPoolStrategy: 'least_loaded',
    cacheEnabled: true,
    supabaseSync: false,
    monitoringEnabled: true
  });

  useEffect(() => {
    // Load settings from localStorage
    const savedSettings = localStorage.getItem('synapse_settings');
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
    }
  }, []);

  const saveSettings = (newSettings) => {
    setSettings(newSettings);
    localStorage.setItem('synapse_settings', JSON.stringify(newSettings));
  };

  const themes = [
    { value: 'neural_network', label: 'Red Neuronal', icon: '🧠', description: 'Conexiones cerebrales artificiales' },
    { value: 'quantum_realm', label: 'Reino Cuántico', icon: '⚛️', description: 'Estados superpuestos y probabilidades' },
    { value: 'cosmic_consciousness', label: 'Conciencia Cósmica', icon: '🌌', description: 'La mente colectiva universal' },
    { value: 'digital_synapse', label: 'Sinapsis Digital', icon: '🔗', description: 'Conexión mente-máquina perfecta' }
  ];

  const workerStrategies = [
    { value: 'round_robin', label: 'Round Robin', description: 'Distribución equitativa' },
    { value: 'least_loaded', label: 'Least Loaded', description: 'Worker con menor carga' },
    { value: 'random', label: 'Random', description: 'Selección aleatoria' },
    { value: 'weighted', label: 'Weighted', description: 'Ponderado por capacidad' }
  ];

  const handleSettingChange = (key, value) => {
    saveSettings({ ...settings, [key]: value });
  };

  const resetSettings = () => {
    const defaultSettings = {
      theme: 'neural_network',
      darkMode: true,
      autoRefresh: true,
      refreshInterval: 5,
      notifications: true,
      soundEnabled: false,
      language: 'es',
      maxDebates: 10,
      workerPoolStrategy: 'least_loaded',
      cacheEnabled: true,
      supabaseSync: false,
      monitoringEnabled: true
    };
    saveSettings(defaultSettings);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
          Configuración de SynapseIA
        </h1>
        <p className="text-xl text-gray-400 mt-2">
          {branding.tagline}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Appearance Settings */}
        <div className="glass rounded-xl p-6">
          <h2 className="text-2xl font-bold mb-6 bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
            Apariencia
          </h2>
          
          <div className="space-y-6">
            {/* Theme Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-3">Tema Visual</label>
              <div className="grid grid-cols-2 gap-3">
                {themes.map((t) => (
                  <button
                    key={t.value}
                    onClick={() => handleSettingChange('theme', t.value)}
                    className={`p-4 rounded-lg border-2 transition-all duration-200 ${
                      settings.theme === t.value
                        ? 'border-blue-500 bg-blue-900 bg-opacity-30'
                        : 'border-gray-600 hover:border-gray-500 bg-gray-800'
                    }`}
                  >
                    <div className="text-2xl mb-2">{t.icon}</div>
                    <div className="text-sm font-medium text-gray-200">{t.label}</div>
                    <div className="text-xs text-gray-500">{t.description}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Dark Mode */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">Modo Oscuro</label>
                <p className="text-xs text-gray-500">Interfaz nocturna</p>
              </div>
              <button
                onClick={() => handleSettingChange('darkMode', !settings.darkMode)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.darkMode ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.darkMode ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Language */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Idioma</label>
              <select
                id="language-select"
                name="language-select"
                value={settings.language}
                onChange={(e) => handleSettingChange('language', e.target.value)}
                className="w-full bg-gray-800 text-gray-300 px-3 py-2 rounded-lg border border-gray-700 focus:border-blue-500 focus:outline-none"
              >
                <option value="es">Español</option>
                <option value="en">English</option>
                <option value="fr">Français</option>
                <option value="de">Deutsch</option>
              </select>
            </div>
          </div>
        </div>

        {/* System Settings */}
        <div className="glass rounded-xl p-6">
          <h2 className="text-2xl font-bold mb-6 bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent">
            Sistema
          </h2>
          
          <div className="space-y-6">
            {/* Auto Refresh */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">Auto Refresh</label>
                <p className="text-xs text-gray-500">Actualizar datos automáticamente</p>
              </div>
              <button
                onClick={() => handleSettingChange('autoRefresh', !settings.autoRefresh)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.autoRefresh ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.autoRefresh ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Refresh Interval */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Intervalo de Refresh (segundos)
              </label>
              <input
                type="range"
                id="refresh-interval"
                name="refresh-interval"
                min="1"
                max="60"
                value={settings.refreshInterval}
                onChange={(e) => handleSettingChange('refreshInterval', parseInt(e.target.value))}
                className="w-full"
                disabled={!settings.autoRefresh}
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>1s</span>
                <span>{settings.refreshInterval}s</span>
                <span>60s</span>
              </div>
            </div>

            {/* Max Debates */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Máximo de Debates Concurrentes
              </label>
              <input
                type="number"
                id="max-debates"
                name="max-debates"
                min="1"
                max="50"
                value={settings.maxDebates}
                onChange={(e) => handleSettingChange('maxDebates', parseInt(e.target.value))}
                className="w-full bg-gray-800 text-gray-300 px-3 py-2 rounded-lg border border-gray-700 focus:border-blue-500 focus:outline-none"
              />
            </div>

            {/* Worker Pool Strategy */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Estrategia de Worker Pool
              </label>
              <select
                id="worker-pool-strategy"
                name="worker-pool-strategy"
                value={settings.workerPoolStrategy}
                onChange={(e) => handleSettingChange('workerPoolStrategy', e.target.value)}
                className="w-full bg-gray-800 text-gray-300 px-3 py-2 rounded-lg border border-gray-700 focus:border-blue-500 focus:outline-none"
              >
                {workerStrategies.map((strategy) => (
                  <option key={strategy.value} value={strategy.value}>
                    {strategy.label} - {strategy.description}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Integration Settings */}
        <div className="glass rounded-xl p-6">
          <h2 className="text-2xl font-bold mb-6 bg-gradient-to-r from-cyan-400 to-blue-600 bg-clip-text text-transparent">
            Integraciones
          </h2>
          
          <div className="space-y-6">
            {/* Cache */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">Redis Cache</label>
                <p className="text-xs text-gray-500">Almacenamiento en caché</p>
              </div>
              <button
                onClick={() => handleSettingChange('cacheEnabled', !settings.cacheEnabled)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.cacheEnabled ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.cacheEnabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Supabase Sync */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">Supabase Sync</label>
                <p className="text-xs text-gray-500">Sincronización en la nube</p>
              </div>
              <button
                onClick={() => handleSettingChange('supabaseSync', !settings.supabaseSync)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.supabaseSync ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.supabaseSync ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Monitoring */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">Prometheus Metrics</label>
                <p className="text-xs text-gray-500">Métricas de monitoreo</p>
              </div>
              <button
                onClick={() => handleSettingChange('monitoringEnabled', !settings.monitoringEnabled)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.monitoringEnabled ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.monitoringEnabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Notification Settings */}
        <div className="glass rounded-xl p-6">
          <h2 className="text-2xl font-bold mb-6 bg-gradient-to-r from-yellow-400 to-orange-600 bg-clip-text text-transparent">
            Notificaciones
          </h2>
          
          <div className="space-y-6">
            {/* Enable Notifications */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">Notificaciones</label>
                <p className="text-xs text-gray-500">Alertas del sistema</p>
              </div>
              <button
                onClick={() => handleSettingChange('notifications', !settings.notifications)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.notifications ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.notifications ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Sound Effects */}
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-300">Efectos de Sonido</label>
                <p className="text-xs text-gray-500">Alertas auditivas</p>
              </div>
              <button
                onClick={() => handleSettingChange('soundEnabled', !settings.soundEnabled)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.soundEnabled ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.soundEnabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="glass rounded-xl p-6 border border-red-500 border-opacity-30">
        <h2 className="text-2xl font-bold mb-6 bg-gradient-to-r from-red-400 to-orange-600 bg-clip-text text-transparent">
          Zona de Peligro
        </h2>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
            <div>
              <h3 className="font-medium text-gray-200">Restablecer Configuración</h3>
              <p className="text-sm text-gray-500">Volver a valores predeterminados</p>
            </div>
            <button
              onClick={resetSettings}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              🔄 Restablecer
            </button>
          </div>
          
          <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
            <div>
              <h3 className="font-medium text-gray-200">Limpiar Caché</h3>
              <p className="text-sm text-gray-500">Eliminar datos temporales</p>
            </div>
            <button className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg transition-colors">
              🗑️ Limpiar
            </button>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="text-center">
        <button className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-4 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 font-semibold text-lg">
          💾 Guardar Configuración
        </button>
        <p className="text-sm text-gray-500 mt-4">
          Los cambios se guardan automáticamente en tu navegador
        </p>
      </div>
    </div>
  );
};

export default Settings;
