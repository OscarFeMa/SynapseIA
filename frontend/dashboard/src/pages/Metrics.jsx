import React, { useState, useEffect } from 'react';
import SynapseLogo from '../components/SynapseLogo';

const Metrics = ({ theme, branding }) => {
  const [metrics, setMetrics] = useState({
    debates_total: 0,
    active_debates: 0,
    connected_workers: 0,
    avg_response_time: 0,
    success_rate: 0,
    tokens_generated: 0,
    uptime_seconds: 0
  });
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('1h');

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, [timeRange]);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      
      // Simulación de datos
      const mockMetrics = {
        debates_total: Math.floor(Math.random() * 100) + 50,
        active_debates: Math.floor(Math.random() * 10) + 1,
        connected_workers: Math.floor(Math.random() * 5) + 3,
        avg_response_time: Math.random() * 5 + 1,
        success_rate: 85 + Math.random() * 15,
        tokens_generated: Math.floor(Math.random() * 100000) + 50000,
        uptime_seconds: Math.floor(Math.random() * 86400) + 3600
      };
      
      setMetrics(mockMetrics);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching metrics:', error);
      setLoading(false);
    }
  };

  const formatUptime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const formatTokens = (tokens) => {
    if (tokens >= 1000000) {
      return (tokens / 1000000).toFixed(1) + 'M';
    } else if (tokens >= 1000) {
      return (tokens / 1000).toFixed(1) + 'K';
    }
    return tokens.toString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4">
            <SynapseLogo size="large" animated={false} theme={theme} />
          </div>
          <div className="animate-pulse text-blue-400">
            <p className="text-lg font-semibold">Cargando métricas...</p>
            <p className="text-sm text-gray-400 mt-2">Sincronizando datos de conciencia</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
            Métricas de Conciencia
          </h1>
          <p className="text-gray-400 mt-2">
            {branding.tagline}
          </p>
        </div>
        
        {/* Time Range Selector */}
        <div className="flex space-x-2">
          <select
            id="time-range-select"
            name="time-range-select"
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="bg-gray-900 text-gray-300 px-3 py-2 rounded-lg border border-gray-700 focus:border-blue-500 focus:outline-none text-sm"
          >
            {['1h', '6h', '24h', '7d'].map((range) => (
              <option key={range} value={range}>
                {range === '1h' ? '1h' :
                 range === '6h' ? '6h' :
                 range === '24h' ? '24h' :
                 range === '7d' ? '7d' : range}
              </option>
            ))}
          </select>
          <button 
            onClick={() => {
              const now = new Date();
              const startTime = timeRange === '1h' ? new Date(now.getTime() - 3600000) :
                           timeRange === '6h' ? new Date(now.getTime() - 21600000) :
                           timeRange === '24h' ? new Date(now.getTime() - 86400000) :
                           new Date(now.getTime() - 604800000);
              setCustomRange(startTime);
            }}
            className="bg-gray-900 text-gray-300 px-3 py-2 rounded-lg border border-gray-700 focus:border-blue-500 focus:outline-none text-sm"
          >
            Aplicar Rango
          </button>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass rounded-xl p-6 text-center">
          <div className="text-4xl font-bold text-blue-400 mb-2">
            {metrics.debates_total}
          </div>
          <div className="text-sm text-gray-400">Debates Totales</div>
          <div className="text-xs text-gray-500 mt-1">Últimas 24 horas</div>
        </div>
        
        <div className="glass rounded-xl p-6 text-center">
          <div className="text-4xl font-bold text-green-400 mb-2">
            {metrics.active_debates}
          </div>
          <div className="text-sm text-gray-400">Debates Activos</div>
          <div className="text-xs text-gray-500 mt-1">En proceso</div>
        </div>
        
        <div className="glass rounded-xl p-6 text-center">
          <div className="text-4xl font-bold text-purple-400 mb-2">
            {metrics.connected_workers}
          </div>
          <div className="text-sm text-gray-400">Workers Conectados</div>
          <div className="text-xs text-gray-500 mt-1">Nodos activos</div>
        </div>
        
        <div className="glass rounded-xl p-6 text-center">
          <div className="text-4xl font-bold text-yellow-400 mb-2">
            {metrics.success_rate.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-400">Tasa de Éxito</div>
          <div className="text-xs text-gray-500 mt-1">Convergencia</div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="glass rounded-xl p-6">
          <h2 className="text-2xl font-bold mb-6 bg-gradient-to-r from-blue-400 to-cyan-600 bg-clip-text text-transparent">
            Rendimiento del Sistema
          </h2>
          
          <div className="space-y-6">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-400">Tiempo de Respuesta</span>
                <span className="text-blue-400 font-semibold">{metrics.avg_response_time.toFixed(2)}s</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-3">
                <div 
                  className="h-3 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-500"
                  style={{ width: `${Math.min(metrics.avg_response_time * 20, 100)}%` }}
                ></div>
              </div>
            </div>
            
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-400">Tokens Generados</span>
                <span className="text-purple-400 font-semibold">{formatTokens(metrics.tokens_generated)}</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-3">
                <div 
                  className="h-3 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
                  style={{ width: `${Math.min((metrics.tokens_generated / 1000000) * 100, 100)}%` }}
                ></div>
              </div>
            </div>
            
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-400">Uptime</span>
                <span className="text-green-400 font-semibold">{formatUptime(metrics.uptime_seconds)}</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-3">
                <div 
                  className="h-3 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 transition-all duration-500"
                  style={{ width: `${Math.min((metrics.uptime_seconds / 86400) * 100, 100)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        {/* System Health */}
        <div className="glass rounded-xl p-6">
          <h2 className="text-2xl font-bold mb-6 bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent">
            Salud del Sistema
          </h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-gray-300">API Status</span>
              </div>
              <span className="text-green-400 font-semibold">Healthy</span>
            </div>
            
            <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-gray-300">Database</span>
              </div>
              <span className="text-green-400 font-semibold">Connected</span>
            </div>
            
            <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-gray-300">Redis Cache</span>
              </div>
              <span className="text-green-400 font-semibold">Active</span>
            </div>
            
            <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full animate-pulse ${
                  metrics.connected_workers > 0 ? 'bg-green-500' : 'bg-yellow-500'
                }`}></div>
                <span className="text-gray-300">Worker Pool</span>
              </div>
              <span className={`${metrics.connected_workers > 0 ? 'text-green-400' : 'text-yellow-400'} font-semibold`}>
                {metrics.connected_workers > 0 ? 'Operational' : 'Warning'}
              </span>
            </div>
            
            <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-gray-300">Supabase Sync</span>
              </div>
              <span className="text-green-400 font-semibold">Synced</span>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Debates Timeline */}
        <div className="glass rounded-xl p-6">
          <h3 className="text-xl font-bold mb-6 text-blue-400">Timeline de Debates</h3>
          <div className="h-64 flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl mb-4">📊</div>
              <p className="text-gray-400">Gráfico de debates en tiempo real</p>
              <p className="text-sm text-gray-500 mt-2">Integración con Chart.js próximamente</p>
            </div>
          </div>
        </div>

        {/* Performance Chart */}
        <div className="glass rounded-xl p-6">
          <h3 className="text-xl font-bold mb-6 text-purple-400">Rendimiento de Workers</h3>
          <div className="h-64 flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl mb-4">⚡</div>
              <p className="text-gray-400">Métricas de rendimiento detalladas</p>
              <p className="text-sm text-gray-500 mt-2">Visualización de carga y latencia</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="glass rounded-xl p-6">
        <h3 className="text-xl font-bold mb-6 bg-gradient-to-r from-cyan-400 to-blue-600 bg-clip-text text-transparent">
          Actividad Reciente
        </h3>
        <div className="space-y-3">
          {[
            { icon: '🧠', action: 'Debate iniciado', target: 'Futuro de la IA', time: 'Hace 2 min', color: 'text-blue-400' },
            { icon: '🔗', action: 'Worker conectado', target: 'Neural Node Alpha', time: 'Hace 5 min', color: 'text-green-400' },
            { icon: '✅', action: 'Debate completado', target: 'Ética en sistemas autónomos', time: 'Hace 8 min', color: 'text-purple-400' },
            { icon: '💾', action: 'Datos sincronizados', target: 'Supabase Cloud', time: 'Hace 12 min', color: 'text-cyan-400' },
            { icon: '⚡', action: 'Worker reiniciado', target: 'Quantum Node Beta', time: 'Hace 15 min', color: 'text-yellow-400' }
          ].map((activity, index) => (
            <div key={index} className="flex items-center space-x-4 p-3 bg-gray-800 rounded-lg hover:bg-gray-700 transition-colors">
              <div className="text-2xl">{activity.icon}</div>
              <div className="flex-1">
                <div className="font-medium text-gray-200">{activity.action}</div>
                <div className="text-sm text-gray-400">{activity.target}</div>
              </div>
              <div className="text-sm text-gray-500">{activity.time}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Export Options */}
      <div className="glass rounded-xl p-6">
        <h3 className="text-xl font-bold mb-6 bg-gradient-to-r from-yellow-400 to-orange-600 bg-clip-text text-transparent">
          Exportar Datos
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg transition-colors">
            📊 Exportar CSV
          </button>
          <button className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg transition-colors">
            📈 Exportar JSON
          </button>
          <button className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg transition-colors">
            📋 Copiar Métricas
          </button>
        </div>
      </div>
    </div>
  );
};

export default Metrics;
