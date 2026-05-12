import React, { useState, useEffect } from 'react';

const ConsciousnessMeter = ({ level = 0, maxLevel = 100, theme = 'neural_network' }) => {
  const [currentLevel, setCurrentLevel] = useState(level);
  const [pulseAnimation, setPulseAnimation] = useState(false);

  useEffect(() => {
    setCurrentLevel(level);
    
    // Animar cuando cambia el nivel
    if (level > currentLevel) {
      setPulseAnimation(true);
      setTimeout(() => setPulseAnimation(false), 500);
    }
  }, [level, currentLevel]);

  // Configuración de temas
  const themeConfigs = {
    neural_network: {
      primary: '#0066FF',
      secondary: '#7C3AED',
      accent: '#FFD700',
      glow: 'rgba(0, 102, 255, 0.5)',
      label: 'Convergencia Neural'
    },
    quantam_realm: {
      primary: '#00CED1',
      secondary: '#FF006E',
      accent: '#00FF41',
      glow: 'rgba(0, 206, 209, 0.5)',
      label: 'Estado Cuántico'
    },
    cosmic_consciousness: {
      primary: '#FFD700',
      secondary: '#7C3AED',
      accent: '#0066FF',
      glow: 'rgba(255, 215, 0, 0.5)',
      label: 'Conciencia Cósmica'
    }
  };

  const config = themeConfigs[theme] || themeConfigs.neural_network;
  const percentage = Math.min((currentLevel / maxLevel) * 100, 100);

  // Estados de conciencia
  const getConsciousnessState = () => {
    if (percentage < 20) return { state: 'Dormante', emoji: '😴', color: '#6B7280' };
    if (percentage < 40) return { state: 'Despertando', emoji: '🌅', color: '#9CA3AF' };
    if (percentage < 60) return { state: 'Conectando', emoji: '🔗', color: '#3B82F6' };
    if (percentage < 80) return { state: 'Sincronizado', emoji: '🌊', color: '#8B5CF6' };
    if (percentage < 95) return { state: 'Elevado', emoji: '✨', color: '#A855F7' };
    return { state: 'Transcendental', emoji: '🧠', color: '#FFD700' };
  };

  const consciousnessState = getConsciousnessState();

  return (
    <div className="relative w-full max-w-md mx-auto p-6">
      {/* Título */}
      <div className="text-center mb-6">
        <h3 className="text-2xl font-bold text-gray-800 dark:text-white mb-2">
          {config.label}
        </h3>
        <div className="flex items-center justify-center space-x-2">
          <span className="text-4xl">{consciousnessState.emoji}</span>
          <span className="text-lg font-semibold text-gray-600 dark:text-gray-400">
            {consciousnessState.state}
          </span>
        </div>
      </div>

      {/* Medidor Principal */}
      <div className="relative">
        {/* Anillo exterior decorativo */}
        <div 
          className={`absolute inset-0 rounded-full transition-all duration-1000 ${
            pulseAnimation ? 'animate-ping' : ''
          }`}
          style={{
            background: `conic-gradient(from 0deg, 
              ${config.glow} 0deg, 
              ${config.primary} ${percentage * 3.6}deg, 
              transparent ${percentage * 3.6}deg)`,
            transform: 'scale(1.1)',
            filter: 'blur(2px)'
          }}
        />
        
        {/* Círculo principal */}
        <div className="relative w-full h-64 rounded-full overflow-hidden bg-gray-900 dark:bg-black">
          {/* Gradiente de fondo */}
          <div 
            className="absolute inset-0 transition-all duration-1000"
            style={{
              background: `conic-gradient(from 0deg, 
                ${config.primary} 0deg, 
                ${config.secondary} 180deg, 
                ${config.accent} 360deg)`,
              opacity: 0.2
            }}
          />
          
          {/* Círculo interior con máscara */}
          <div 
            className="absolute inset-4 rounded-full bg-gray-900 dark:bg-black transition-all duration-1000"
            style={{
              background: `conic-gradient(from 0deg, 
                ${config.primary} 0deg, 
                ${config.primary} ${percentage * 3.6}deg, 
                transparent ${percentage * 3.6}deg)`,
              mask: 'radial-gradient(circle at center, transparent 65%, black 65%)',
              WebkitMask: 'radial-gradient(circle at center, transparent 65%, black 65%)'
            }}
          >
            {/* Centro brillante */}
            <div 
              className="absolute inset-0 rounded-full transition-all duration-1000"
              style={{
                background: `radial-gradient(circle at center, 
                  ${config.primary} 0%, 
                  ${config.secondary} 50%, 
                  transparent 70%)`,
                opacity: 0.8 + (percentage / 100) * 0.2,
                filter: `blur(${2 + (percentage / 100) * 3}px)`
              }}
            />
            
            {/* Punto central */}
            <div 
              className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-4 h-4 rounded-full transition-all duration-1000"
              style={{
                backgroundColor: config.primary,
                boxShadow: `0 0 ${20 + (percentage / 100) * 30}px ${config.primary}`,
                opacity: 0.9 + (percentage / 100) * 0.1
              }}
            />
          </div>
          
          {/* Partículas flotantes */}
          {[...Array(8)].map((_, i) => (
            <div
              key={i}
              className="absolute w-1 h-1 rounded-full transition-all duration-1000"
              style={{
                backgroundColor: config.primary,
                left: `${50 + Math.cos((i * 45 + percentage * 3.6) * Math.PI / 180) * 40}%`,
                top: `${50 + Math.sin((i * 45 + percentage * 3.6) * Math.PI / 180) * 40}%`,
                opacity: 0.6 + (percentage / 100) * 0.4,
                transform: `scale(${0.5 + (percentage / 100) * 1})`,
                boxShadow: `0 0 ${4 + (percentage / 100) * 6}px ${config.primary}`
              }}
            />
          ))}
        </div>
      </div>

      {/* Información numérica */}
      <div className="mt-6 text-center">
        <div className="text-4xl font-bold transition-all duration-1000"
             style={{ color: consciousnessState.color }}>
          {Math.round(percentage)}%
        </div>
        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          {currentLevel} / {maxLevel} unidades de conciencia
        </div>
      </div>

      {/* Indicadores de estado */}
      <div className="mt-6 grid grid-cols-3 gap-4">
        <div className="text-center p-3 rounded-lg bg-gray-100 dark:bg-gray-800">
          <div className="text-xs text-gray-500 dark:text-gray-400 uppercase">Nivel</div>
          <div className="text-lg font-semibold" style={{ color: config.primary }}>
            {Math.floor(percentage / 20) + 1}
          </div>
        </div>
        <div className="text-center p-3 rounded-lg bg-gray-100 dark:bg-gray-800">
          <div className="text-xs text-gray-500 dark:text-gray-400 uppercase">Sinapsis</div>
          <div className="text-lg font-semibold" style={{ color: config.secondary }}>
            {Math.floor(currentLevel * 1.5)}
          </div>
        </div>
        <div className="text-center p-3 rounded-lg bg-gray-100 dark:bg-gray-800">
          <div className="text-xs text-gray-500 dark:text-gray-400 uppercase">Convergencia</div>
          <div className="text-lg font-semibold" style={{ color: config.accent }}>
            {Math.round(percentage)}%
          </div>
        </div>
      </div>

      {/* Mensaje de estado */}
      <div className="mt-6 text-center p-4 rounded-lg bg-gradient-to-r from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-700">
        <div className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {percentage < 20 && "La red neuronal está en estado de reposo..."}
          {percentage >= 20 && percentage < 40 && "Iniciando secuencia de activación..."}
          {percentage >= 40 && percentage < 60 && "Estableciendo conexiones sinápticas..."}
          {percentage >= 60 && percentage < 80 && "Sincronizando nodos de pensamiento..."}
          {percentage >= 80 && percentage < 95 && "Alcanzando estado de convergencia elevada..."}
          {percentage >= 95 && "¡Conciencia colectiva transcendental alcanzada!"}
        </div>
      </div>

      {/* Estilos CSS en línea */}
      <style jsx>{`
        @keyframes ping {
          75%, 100% {
            transform: scale(1.1);
            opacity: 0;
          }
        }
        
        .animate-ping {
          animation: ping 1s cubic-bezier(0, 0, 0.2, 1) infinite;
        }
      `}</style>
    </div>
  );
};

export default ConsciousnessMeter;
