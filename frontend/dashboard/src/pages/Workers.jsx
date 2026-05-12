import React, { useState, useEffect } from 'react';
import SynapseLogo from '../components/SynapseLogo';

const Workers = ({ theme, branding }) => {
  const [workers, setWorkers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedWorker, setSelectedWorker] = useState(null);

  useEffect(() => {
    fetchWorkers();
    const interval = setInterval(fetchWorkers, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchWorkers = async () => {
    try {
      setLoading(true);
      
      // Simulación de datos
      const mockWorkers = [
        {
          id: 'worker-1',
          name: 'Neural Node Alpha',
          host: '192.168.1.100',
          port: 8001,
          status: 'active',
          load: 25,
          max_concurrent: 5,
          current_tasks: 2,
          total_requests: 1250,
          success_rate: 98.5,
          avg_response_time: 1.2,
          last_heartbeat: new Date().toISOString(),
          model: 'llama3-8b',
          provider: 'ollama'
        },
        {
          id: 'worker-2',
          name: 'Quantum Node Beta',
          host: '192.168.1.101',
          port: 8002,
          status: 'active',
          load: 60,
          max_concurrent: 5,
          current_tasks: 3,
          total_requests: 980,
          success_rate: 96.2,
          avg_response_time: 1.8,
          last_heartbeat: new Date().toISOString(),
          model: 'gpt-4',
          provider: 'openrouter'
        },
        {
          id: 'worker-3',
          name: 'Cosmic Node Gamma',
          host: '192.168.1.102',
          port: 8003,
          status: 'idle',
          load: 0,
          max_concurrent: 5,
          current_tasks: 0,
          total_requests: 750,
          success_rate: 97.8,
          avg_response_time: 1.5,
          last_heartbeat: new Date().toISOString(),
          model: 'claude-3',
          provider: 'anthropic'
        }
      ];
      
      setWorkers(mockWorkers);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching workers:', error);
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-400 bg-green-900';
      case 'idle': return 'text-yellow-400 bg-yellow-900';
      case 'error': return 'text-red-400 bg-red-900';
      case 'offline': return 'text-gray-400 bg-gray-900';
      default: return 'text-gray-400 bg-gray-900';
    }
  };

  const getLoadColor = (load) => {
    if (load < 30) return 'text-green-400';
    if (load < 70) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getProviderIcon = (provider) => {
    switch (provider) {
      case 'ollama': return '🦙';
      case 'openrouter': return '🌐';
      case 'anthropic': return '🧠';
      case 'groq': return '⚡';
      case 'deepseek': return '🔍';
      default: return '🤖';
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
            <p className="text-lg font-semibold">Conectando con la red neuronal...</p>
            <p className="text-sm text-gray-400 mt-2">Detectando nodos de procesamiento</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
          Gestión de Red Neuronal
        </h1>
        <p className="text-xl text-gray-400 mt-2">
          {branding.tagline}
        </p>
      </div>

      {/* Pool Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="glass rounded-xl p-6 text-center">
          <div className="text-3xl font-bold text-blue-400">
            {workers.length}
          </div>
          <div className="text-sm text-gray-400">Total Workers</div>
        </div>
        <div className="glass rounded-xl p-6 text-center">
          <div className="text-3xl font-bold text-green-400">
            {workers.filter(w => w.status === 'active').length}
          </div>
          <div className="text-sm text-gray-400">Workers Activos</div>
        </div>
        <div className="glass rounded-xl p-6 text-center">
          <div className="text-3xl font-bold text-yellow-400">
            {workers.filter(w => w.status === 'idle').length}
          </div>
          <div className="text-sm text-gray-400">Workers Inactivos</div>
        </div>
        <div className="glass rounded-xl p-6 text-center">
          <div className="text-3xl font-bold text-purple-400">
            {workers.length > 0 ? Math.round(workers.reduce((sum, w) => sum + w.load, 0) / workers.length) : 0}%
          </div>
          <div className="text-sm text-gray-400">Carga Promedio</div>
        </div>
      </div>

      {/* Workers Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {workers.map((worker) => (
          <div key={worker.id} className="glass rounded-xl p-6 hover:scale-105 transition-all duration-300 border border-gray-700">
            <div className="flex justify-between items-start mb-4">
              <div className="flex items-center space-x-3">
                <div className="text-2xl">{getProviderIcon(worker.provider)}</div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-200">{worker.name}</h3>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs rounded-full font-medium ${getStatusColor(worker.status)}`}>
                      {worker.status === 'active' ? '🟢 Activo' :
                       worker.status === 'idle' ? '🟡 Inactivo' :
                       worker.status === 'error' ? '🔴 Error' :
                       worker.status === 'offline' ? '⚫ Offline' : worker.status}
                    </span>
                    <span className="text-xs text-gray-500">
                      {worker.host}:{worker.port}
                    </span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => setSelectedWorker(worker)}
                className="text-blue-400 hover:text-blue-300 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              {/* Load Bar */}
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-400">Carga</span>
                  <span className={getLoadColor(worker.load)}>{worker.load}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${
                      worker.load < 30 ? 'bg-green-500' :
                      worker.load < 70 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${worker.load}%` }}
                  ></div>
                </div>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Tareas:</span>
                  <span className="ml-2 text-blue-400">{worker.current_tasks}/{worker.max_concurrent}</span>
                </div>
                <div>
                  <span className="text-gray-400">Éxito:</span>
                  <span className="ml-2 text-green-400">{worker.success_rate}%</span>
                </div>
                <div>
                  <span className="text-gray-400">Tiempo:</span>
                  <span className="ml-2 text-yellow-400">{worker.avg_response_time}s</span>
                </div>
                <div>
                  <span className="text-gray-400">Total:</span>
                  <span className="ml-2 text-purple-400">{worker.total_requests}</span>
                </div>
              </div>

              {/* Model Info */}
              <div className="flex items-center space-x-2 text-sm">
                <span className="text-gray-400">Modelo:</span>
                <span className="text-cyan-400 font-medium">{worker.model}</span>
                <span className="text-gray-500">({worker.provider})</span>
              </div>

              {/* Last Heartbeat */}
              <div className="text-xs text-gray-500">
                Último heartbeat: {new Date(worker.last_heartbeat).toLocaleString()}
              </div>
            </div>

            {/* Actions */}
            <div className="mt-6 flex space-x-2">
              <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors text-sm">
                🔄 Reiniciar
              </button>
              <button className="flex-1 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors text-sm">
                ⚙️ Configurar
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Worker Detail Modal */}
      {selectedWorker && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="glass rounded-xl p-8 max-w-2xl w-full mx-4 max-h-screen overflow-y-auto">
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-200">{selectedWorker.name}</h2>
                <p className="text-gray-400">{selectedWorker.host}:{selectedWorker.port}</p>
              </div>
              <button
                onClick={() => setSelectedWorker(null)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-blue-400">Estado General</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Estado:</span>
                    <span className={getStatusColor(selectedWorker.status)}>
                      {selectedWorker.status === 'active' ? 'Activo' :
                       selectedWorker.status === 'idle' ? 'Inactivo' :
                       selectedWorker.status === 'error' ? 'Error' :
                       selectedWorker.status === 'offline' ? 'Offline' : selectedWorker.status}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Carga:</span>
                    <span className={getLoadColor(selectedWorker.load)}>{selectedWorker.load}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Tareas Actuales:</span>
                    <span className="text-blue-400">{selectedWorker.current_tasks}/{selectedWorker.max_concurrent}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-purple-400">Rendimiento</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Tasa de Éxito:</span>
                    <span className="text-green-400">{selectedWorker.success_rate}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Tiempo Promedio:</span>
                    <span className="text-yellow-400">{selectedWorker.avg_response_time}s</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Total de Solicitudes:</span>
                    <span className="text-purple-400">{selectedWorker.total_requests}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-cyan-400">Configuración</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Modelo:</span>
                    <span className="text-cyan-400">{selectedWorker.model}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Proveedor:</span>
                    <span className="text-cyan-400">{selectedWorker.provider}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Max Concurrente:</span>
                    <span className="text-cyan-400">{selectedWorker.max_concurrent}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-yellow-400">Conectividad</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Host:</span>
                    <span className="text-yellow-400">{selectedWorker.host}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Puerto:</span>
                    <span className="text-yellow-400">{selectedWorker.port}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Último Heartbeat:</span>
                    <span className="text-yellow-400">
                      {new Date(selectedWorker.last_heartbeat).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 flex space-x-4">
              <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg transition-colors">
                🔄 Reiniciar Worker
              </button>
              <button className="flex-1 bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg transition-colors">
                ⛔ Desconectar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Worker Button */}
      <div className="text-center">
        <button className="bg-gradient-to-r from-green-600 to-blue-600 text-white px-8 py-4 rounded-lg hover:from-green-700 hover:to-blue-700 transition-all duration-300 transform hover:scale-105 font-semibold">
          🔗 Añadir Nuevo Worker
        </button>
      </div>
    </div>
  );
};

export default Workers;
