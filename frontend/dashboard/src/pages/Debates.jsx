import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import SynapseLogo from '../components/SynapseLogo';

const Debates = ({ theme, branding }) => {
  const [debates, setDebates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchDebates();
  }, [filter]);

  const fetchDebates = async () => {
    try {
      setLoading(true);
      
      // Simulación de datos
      const mockDebates = [
        {
          id: 'debate-1',
          topic: 'El futuro de la IA en la toma de decisiones',
          status: 'completed',
          mode: 'standard',
          duration: '2.5 min',
          participants: 4,
          consensus_score: 85,
          timestamp: new Date().toISOString()
        },
        {
          id: 'debate-2',
          topic: 'Ética en el desarrollo de sistemas autónomos',
          status: 'running',
          mode: 'consensus',
          duration: '1.2 min',
          participants: 6,
          consensus_score: 72,
          timestamp: new Date().toISOString()
        },
        {
          id: 'debate-3',
          topic: 'Impacto del razonamiento colaborativo',
          status: 'completed',
          mode: 'sequential',
          duration: '3.8 min',
          participants: 5,
          consensus_score: 91,
          timestamp: new Date().toISOString()
        }
      ];
      
      setDebates(mockDebates);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching debates:', error);
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-400 bg-green-900';
      case 'running': return 'text-blue-400 bg-blue-900';
      case 'failed': return 'text-red-400 bg-red-900';
      default: return 'text-gray-400 bg-gray-900';
    }
  };

  const getModeIcon = (mode) => {
    switch (mode) {
      case 'standard': return '🧠';
      case 'consensus': return '🤝';
      case 'sequential': return '🔄';
      default: return '📊';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4">
            <SynapseLogo size="large" animated={false} theme={theme} />
          </div>
          <div className="animate-pulse text-blue-400">
            <p className="text-lg font-semibold">Cargando debates...</p>
            <p className="text-sm text-gray-400 mt-2">Sincronizando con la red neuronal</p>
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
            Gestión de Debates
          </h1>
          <p className="text-gray-400 mt-2">
            {branding.tagline}
          </p>
        </div>
        <Link
          to="/debates/new"
          className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 font-semibold"
        >
          🧠 Nuevo Debate
        </Link>
      </div>

      {/* Filters */}
      <div className="glass rounded-xl p-6">
        <div className="flex flex-wrap gap-4 items-center">
          <span className="text-gray-400 font-medium">Filtrar:</span>
          {['all', 'running', 'completed', 'failed'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg transition-all duration-200 ${
                filter === status
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {status === 'all' ? '📊 Todos' :
               status === 'running' ? '⚡ Activos' :
               status === 'completed' ? '✅ Completados' :
               status === 'failed' ? '❌ Fallidos' : status}
            </button>
          ))}
        </div>
      </div>

      {/* Debates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {debates
          .filter(debate => filter === 'all' || debate.status === filter)
          .map((debate) => (
            <div key={debate.id} className="glass rounded-xl p-6 hover:scale-105 transition-all duration-300 border border-gray-700">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl">{getModeIcon(debate.mode)}</span>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-200">
                      {debate.mode === 'standard' ? 'Estándar' :
                       debate.mode === 'consensus' ? 'Consenso' :
                       debate.mode === 'sequential' ? 'Secuencial' : debate.mode}
                    </h3>
                    <span className={`px-2 py-1 text-xs rounded-full font-medium ${getStatusColor(debate.status)}`}>
                      {debate.status === 'completed' ? 'Completado' :
                       debate.status === 'running' ? 'Activo' :
                       debate.status === 'failed' ? 'Fallido' : debate.status}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-400">Puntuación</div>
                  <div className="text-xl font-bold text-yellow-400">
                    {debate.consensus_score}%
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <h4 className="font-medium text-gray-200 mb-2 line-clamp-2">
                    {debate.topic}
                  </h4>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-400">Participantes:</span>
                    <span className="ml-2 text-blue-400 font-medium">{debate.participants}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Duración:</span>
                    <span className="ml-2 text-green-400 font-medium">{debate.duration}</span>
                  </div>
                </div>

                <div className="text-xs text-gray-500">
                  {new Date(debate.timestamp).toLocaleString()}
                </div>
              </div>

              <div className="mt-6 flex space-x-2">
                <Link
                  to={`/debates/${debate.id}`}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-center transition-colors"
                >
                  Ver Detalles
                </Link>
                {debate.status === 'running' && (
                  <button className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors">
                    Detener
                  </button>
                )}
              </div>
            </div>
          ))}
      </div>

      {debates.filter(debate => filter === 'all' || debate.status === filter).length === 0 && (
        <div className="text-center py-12 glass rounded-xl">
          <div className="text-6xl mb-4">🧠</div>
          <h3 className="text-xl font-semibold text-gray-300 mb-2">
            No hay debates {filter === 'all' ? '' : filter === 'running' ? 'activos' : filter === 'completed' ? 'completados' : 'fallidos'}
          </h3>
          <p className="text-gray-500 mb-6">
            {filter === 'all' ? 'Inicia tu primer debate sináptico' :
             filter === 'running' ? 'No hay debates en proceso' :
             filter === 'completed' ? 'No hay debates completados' :
             'No hay debates fallidos'}
          </p>
          <Link
            to="/debates/new"
            className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-300 inline-block font-semibold"
          >
            🧠 Crear Nuevo Debate
          </Link>
        </div>
      )}

      {/* Statistics */}
      <div className="glass rounded-xl p-6">
        <h2 className="text-2xl font-bold mb-6 bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent">
          Estadísticas de Debates
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-400">
              {debates.filter(d => d.status === 'running').length}
            </div>
            <div className="text-sm text-gray-400">Debates Activos</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-400">
              {debates.filter(d => d.status === 'completed').length}
            </div>
            <div className="text-sm text-gray-400">Completados</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-yellow-400">
              {debates.length > 0 ? Math.round(debates.reduce((sum, d) => sum + d.consensus_score, 0) / debates.length) : 0}%
            </div>
            <div className="text-sm text-gray-400">Consenso Promedio</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-400">
              {debates.length > 0 ? Math.round(debates.reduce((sum, d) => sum + d.participants, 0) / debates.length) : 0}
            </div>
            <div className="text-sm text-gray-400">Participantes Promedio</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Debates;
