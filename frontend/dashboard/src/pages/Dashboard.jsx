import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import ConsciousnessMeter from '../components/ConsciousnessMeter';
import SynapseLogo from '../components/SynapseLogo';

const Dashboard = ({ theme, branding }) => {
  const [stats, setStats] = useState({
    totalDebates: 0,
    activeDebates: 0,
    connectedWorkers: 0,
    avgResponseTime: 0,
    successRate: 0,
    consciousnessLevel: 0
  });
  const [recentDebates, setRecentDebates] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 5000);
    return () => clearInterval(interval);
  }, []);

  // Función para forzar recarga completa
  const forceCompleteReload = () => {
    // Limpiar toda la caché
    localStorage.clear();
    sessionStorage.clear();
    
    // Limpiar caché del navegador
    if ('caches' in window) {
      caches.keys().then(names => {
        names.forEach(name => {
          caches.delete(name);
        });
      });
    }
    
    // Forzar recarga con timestamp único
    const timestamp = new Date().getTime();
    window.location.href = window.location.href.split('?')[0] + '?force_reload=' + timestamp;
  };

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Simulación de datos - en producción usar API real
      const mockStats = {
        totalDebates: Math.floor(Math.random() * 100) + 50,
        activeDebates: Math.floor(Math.random() * 10) + 1,
        connectedWorkers: Math.floor(Math.random() * 5) + 3,
        avgResponseTime: Math.random() * 5 + 1,
        successRate: 85 + Math.random() * 15,
        consciousnessLevel: Math.random() * 100
      };
      
      const mockDebates = [
        {
          id: 'debate-1',
          topic: 'El futuro de la IA en la toma de decisiones',
          status: 'completed',
          mode: 'standard',
          duration: '2.5 min',
          timestamp: new Date().toISOString()
        },
        {
          id: 'debate-2',
          topic: 'Ética en el desarrollo de sistemas autónomos',
          status: 'running',
          mode: 'consensus',
          duration: '1.2 min',
          timestamp: new Date().toISOString()
        },
        {
          id: 'debate-3',
          topic: 'Impacto del razonamiento colaborativo',
          status: 'completed',
          mode: 'sequential',
          duration: '3.8 min',
          timestamp: new Date().toISOString()
        }
      ];
      
      setStats(mockStats);
      setRecentDebates(mockDebates);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon, color = 'blue', description }) => {
    const colorClasses = {
      blue: 'bg-gradient-to-br from-blue-600 to-blue-800 text-white',
      purple: 'bg-gradient-to-br from-purple-600 to-purple-800 text-white',
      green: 'bg-gradient-to-br from-green-600 to-green-800 text-white',
      yellow: 'bg-gradient-to-br from-yellow-600 to-yellow-800 text-white',
      red: 'bg-gradient-to-br from-red-600 to-red-800 text-white'
    };

    return (
      <div className={`${colorClasses[color]} rounded-xl p-6 shadow-2xl transform transition-all duration-300 hover:scale-105 hover:shadow-3xl border border-white border-opacity-20`}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm opacity-90 mb-1">{title}</p>
            <p className="text-3xl font-bold mb-2">{value}</p>
            <p className="text-xs opacity-80">{description}</p>
          </div>
          <div className="text-4xl opacity-80 ml-4">{icon}</div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4">
            <SynapseLogo size="medium" animated={false} theme={theme} />
          </div>
          <div className="animate-pulse text-blue-400">
            <p className="text-lg font-semibold">Conectando con la red neuronal...</p>
            <p className="text-sm text-gray-400 mt-2">Sincronizando conciencia colectiva</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-2">
      {/* Header Compacto */}
      <div className="text-center py-2 mb-2">
        <h1 className="text-2xl font-bold mb-1 bg-gradient-to-r from-blue-400 via-purple-600 to-yellow-500 bg-clip-text text-transparent">
          SynapseIA Dashboard
        </h1>
        <p className="text-sm text-gray-400 italic">
          {branding.tagline}
        </p>
      </div>

      {/* Grid Compacto - Todo en una pantalla */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 mb-2">
        <StatCard 
          title="Debates" 
          value={stats.totalDebates} 
          icon="🧠" 
          color="blue"
          description="Totales"
        />
        <StatCard 
          title="Activos" 
          value={stats.activeDebates} 
          icon="⚡" 
          color="purple"
          description="En proceso"
        />
        <StatCard 
          title="Workers" 
          value={stats.connectedWorkers} 
          icon="🔗" 
          color="green"
          description="Conectados"
        />
        <StatCard 
          title="Éxito" 
          value={`${stats.successRate.toFixed(1)}%`} 
          icon="✅" 
          color={stats.successRate >= 90 ? 'green' : stats.successRate >= 70 ? 'yellow' : 'red'}
          description="Tasa"
        />
      </div>

      {/* Segunda Fila */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 mb-2">
        <StatCard 
          title="Tiempo" 
          value={`${stats.avgResponseTime.toFixed(1)}s`} 
          icon="⏱️" 
          color="blue"
          description="Promedio"
        />
        <StatCard 
          title="Conciencia" 
          value={`${stats.consciousnessLevel.toFixed(0)}%`} 
          icon="🌌" 
          color="purple"
          description="Nivel"
        />
        <StatCard 
          title="API" 
          value="Online" 
          icon="🌐" 
          color="green"
          description="Status"
        />
        <StatCard 
          title="Cache" 
          value="Activo" 
          icon="💾" 
          color="cyan"
          description="Estado"
        />
      </div>

      {/* Fila Principal - Consciousness Meter + Acciones */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2 mb-2">
        <div className="glass rounded-lg p-3">
          <h2 className="text-lg font-bold mb-2 text-center bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
            Convergencia Neuronal
          </h2>
          <ConsciousnessMeter 
            level={stats.consciousnessLevel} 
            maxLevel={100} 
            theme={theme}
          />
        </div>

        <div className="glass rounded-lg p-3">
          <h2 className="text-lg font-bold mb-2 text-center bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent">
            Acciones Rápidas
          </h2>
          <div className="grid grid-cols-2 gap-2">
            <Link 
              to="/debates/new" 
              className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-3 py-2 rounded hover:from-blue-700 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 text-center font-semibold text-xs"
            >
              🧠 Nuevo Debate
            </Link>
            <Link 
              to="/workers" 
              className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-3 py-2 rounded hover:from-purple-700 hover:to-pink-700 transition-all duration-300 transform hover:scale-105 text-center font-semibold text-xs"
            >
              🔗 Workers
            </Link>
            <Link 
              to="/metrics" 
              className="bg-gradient-to-r from-green-600 to-blue-600 text-white px-3 py-2 rounded hover:from-green-700 hover:to-blue-700 transition-all duration-300 transform hover:scale-105 text-center font-semibold text-xs"
            >
              📊 Métricas
            </Link>
            <button 
              onClick={fetchDashboardData}
              className="w-full block bg-gradient-to-r from-gray-600 to-gray-700 text-white px-3 py-2 rounded hover:from-gray-700 hover:to-gray-800 transition-all duration-300 transform hover:scale-105 text-center font-semibold text-xs"
            >
              🔄 Sincronizar
            </button>
            <button 
              onClick={forceCompleteReload}
              className="w-full block bg-gradient-to-r from-red-600 to-orange-600 text-white px-3 py-2 rounded hover:from-red-700 hover:to-orange-800 transition-all duration-300 transform hover:scale-105 text-center font-semibold text-xs mt-2"
            >
              🔄 Forzar Recarga Completa
            </button>
          </div>
        </div>
      </div>

      {/* Tabla Compacta de Debates Recientes */}
      <div className="glass rounded-lg p-3">
        <h2 className="text-lg font-bold mb-2 bg-gradient-to-r from-cyan-400 to-blue-600 bg-clip-text text-transparent">
          Debates Recientes
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-1 px-2 text-gray-400">Tema</th>
                <th className="text-left py-1 px-2 text-gray-400">Estado</th>
                <th className="text-left py-1 px-2 text-gray-400">Modo</th>
                <th className="text-left py-1 px-2 text-gray-400">Duración</th>
                <th className="text-left py-1 px-2 text-gray-400">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {recentDebates.slice(0, 3).map((debate) => (
                <tr key={debate.id} className="border-b border-gray-800 hover:bg-gray-800 hover:bg-opacity-50 transition-colors">
                  <td className="py-2 px-2">
                    <div className="max-w-xs truncate">
                      {debate.topic}
                    </div>
                  </td>
                  <td className="py-2 px-2">
                    <span className={`px-1 py-0.5 text-xs rounded-full font-medium ${
                      debate.status === 'completed' ? 'bg-green-900 text-green-300' :
                      debate.status === 'running' ? 'bg-blue-900 text-blue-300' :
                      debate.status === 'failed' ? 'bg-red-900 text-red-300' :
                      'bg-gray-900 text-gray-300'
                    }`}>
                      {debate.status === 'completed' ? '✅' :
                       debate.status === 'running' ? '⚡' :
                       debate.status === 'failed' ? '❌' :
                       debate.status}
                    </span>
                  </td>
                  <td className="py-2 px-2">
                    <span className="text-purple-400 font-medium">
                      {debate.mode === 'standard' ? '🧠' :
                       debate.mode === 'consensus' ? '🤝' :
                       debate.mode === 'sequential' ? '🔄' :
                       debate.mode}
                    </span>
                  </td>
                  <td className="py-2 px-2 text-gray-400">
                    {debate.duration}
                  </td>
                  <td className="py-2 px-2">
                    <Link 
                      to={`/debates/${debate.id}`}
                      className="text-blue-400 hover:text-blue-300 transition-colors font-medium"
                    >
                      Ver →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {recentDebates.length === 0 && (
            <div className="text-center py-4 text-gray-500">
              <div className="text-2xl mb-1">🧠</div>
              <p className="text-xs font-medium">No hay debates activos</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
