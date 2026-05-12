import React from 'react';

const SynapseLogo = ({ size = 'medium', animated = true, theme = 'neural_network' }) => {
  const sizeClasses = {
    small: 'w-8 h-8',
    medium: 'w-12 h-12',
    large: 'w-16 h-16',
    xlarge: 'w-24 h-24'
  };

  const themeConfigs = {
    neural_network: {
      primary: '#0066FF',
      secondary: '#7C3AED',
      accent: '#FFD700',
      glow: 'rgba(0, 102, 255, 0.6)'
    },
    quantam_realm: {
      primary: '#00CED1',
      secondary: '#FF006E',
      accent: '#00FF41',
      glow: 'rgba(0, 206, 209, 0.6)'
    },
    cosmic_consciousness: {
      primary: '#FFD700',
      secondary: '#7C3AED',
      accent: '#0066FF',
      glow: 'rgba(255, 215, 0, 0.6)'
    }
  };

  const config = themeConfigs[theme] || themeConfigs.neural_network;

  return (
    <div className={`relative ${sizeClasses[size]}`}>
      {/* Logo SVG animado */}
      <svg
        viewBox="0 0 100 100"
        className={`w-full h-full ${animated ? 'animate-pulse' : ''}`}
        style={{
          filter: `drop-shadow(0 0 ${size === 'small' ? '8px' : size === 'medium' ? '12px' : '16px'} ${config.glow})`
        }}
      >
        {/* Círculo exterior - representando la red neuronal */}
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke={config.secondary}
          strokeWidth="2"
          strokeDasharray="5 3"
          className={animated ? 'animate-spin' : ''}
          style={{
            transformOrigin: 'center',
            animationDuration: '20s'
          }}
        />
        
        {/* Sinapsis principales - conexiones neuronales */}
        <g>
          {/* Conexión 1-2 */}
          <line
            x1="30"
            y1="30"
            x2="70"
            y2="30"
            stroke={config.primary}
            strokeWidth="3"
            strokeLinecap="round"
            className={animated ? 'animate-pulse' : ''}
            style={{
              animationDelay: '0s',
              animationDuration: '2s'
            }}
          />
          
          {/* Conexión 2-3 */}
          <line
            x1="70"
            y1="30"
            x2="70"
            y2="70"
            stroke={config.primary}
            strokeWidth="3"
            strokeLinecap="round"
            className={animated ? 'animate-pulse' : ''}
            style={{
              animationDelay: '0.5s',
              animationDuration: '2s'
            }}
          />
          
          {/* Conexión 3-4 */}
          <line
            x1="70"
            y1="70"
            x2="30"
            y2="70"
            stroke={config.primary}
            strokeWidth="3"
            strokeLinecap="round"
            className={animated ? 'animate-pulse' : ''}
            style={{
              animationDelay: '1s',
              animationDuration: '2s'
            }}
          />
          
          {/* Conexión 4-1 */}
          <line
            x1="30"
            y1="70"
            x2="30"
            y2="30"
            stroke={config.primary}
            strokeWidth="3"
            strokeLinecap="round"
            className={animated ? 'animate-pulse' : ''}
            style={{
              animationDelay: '1.5s',
              animationDuration: '2s'
            }}
          />
          
          {/* Conexión diagonal 1-3 */}
          <line
            x1="30"
            y1="30"
            x2="70"
            y2="70"
            stroke={config.accent}
            strokeWidth="1"
            strokeLinecap="round"
            opacity="0.6"
            className={animated ? 'animate-pulse' : ''}
            style={{
              animationDelay: '2s',
              animationDuration: '3s'
            }}
          />
          
          {/* Conexión diagonal 2-4 */}
          <line
            x1="70"
            y1="30"
            x2="30"
            y2="70"
            stroke={config.accent}
            strokeWidth="1"
            strokeLinecap="round"
            opacity="0.6"
            className={animated ? 'animate-pulse' : ''}
            style={{
              animationDelay: '2.5s',
              animationDuration: '3s'
            }}
          />
        </g>
        
        {/* Nodos neuronales */}
        <g>
          {/* Nodo 1 - Top-left */}
          <circle
            cx="30"
            cy="30"
            r="8"
            fill={config.primary}
            className={animated ? 'animate-ping' : ''}
            style={{
              animationDelay: '0s',
              animationDuration: '2s'
            }}
          >
            <animate
              attributeName="r"
              values="8;10;8"
              dur="2s"
              repeatCount="indefinite"
            />
          </circle>
          
          {/* Nodo 2 - Top-right */}
          <circle
            cx="70"
            cy="30"
            r="8"
            fill={config.primary}
            className={animated ? 'animate-ping' : ''}
            style={{
              animationDelay: '0.5s',
              animationDuration: '2s'
            }}
          >
            <animate
              attributeName="r"
              values="8;10;8"
              dur="2s"
              repeatCount="indefinite"
            />
          </circle>
          
          {/* Nodo 3 - Bottom-right */}
          <circle
            cx="70"
            cy="70"
            r="8"
            fill={config.primary}
            className={animated ? 'animate-ping' : ''}
            style={{
              animationDelay: '1s',
              animationDuration: '2s'
            }}
          >
            <animate
              attributeName="r"
              values="8;10;8"
              dur="2s"
              repeatCount="indefinite"
            />
          </circle>
          
          {/* Nodo 4 - Bottom-left */}
          <circle
            cx="30"
            cy="70"
            r="8"
            fill={config.primary}
            className={animated ? 'animate-ping' : ''}
            style={{
              animationDelay: '1.5s',
              animationDuration: '2s'
            }}
          >
            <animate
              attributeName="r"
              values="8;10;8"
              dur="2s"
              repeatCount="indefinite"
            />
          </circle>
        </g>
        
        {/* Centro - Conciencia colectiva */}
        <g>
          {/* Círculo central brillante */}
          <circle
            cx="50"
            cy="50"
            r="12"
            fill={config.accent}
            opacity="0.8"
            className={animated ? 'animate-pulse' : ''}
            style={{
              animationDelay: '0s',
              animationDuration: '3s'
            }}
          />
          
          {/* Núcleo central */}
          <circle
            cx="50"
            cy="50"
            r="6"
            fill="white"
            className={animated ? 'animate-ping' : ''}
            style={{
              animationDelay: '0.5s',
              animationDuration: '1.5s'
            }}
          />
          
          {/* Partículas de energía */}
          {[...Array(6)].map((_, i) => (
            <circle
              key={i}
              cx={50 + Math.cos((i * 60) * Math.PI / 180) * 15}
              cy={50 + Math.sin((i * 60) * Math.PI / 180) * 15}
              r="2"
              fill={config.primary}
              opacity="0.6"
              className={animated ? 'animate-pulse' : ''}
              style={{
                animationDelay: `${i * 0.2}s`,
                animationDuration: '2s'
              }}
            >
              <animate
                attributeName="opacity"
                values="0.6;1;0.6"
                dur="2s"
                repeatCount="indefinite"
              />
            </circle>
          ))}
        </g>
        
        {/* Efecto de ondas expansivas */}
        <g opacity="0.3">
          {[...Array(3)].map((_, i) => (
            <circle
              key={i}
              cx="50"
              cy="50"
              r={20 + i * 10}
              fill="none"
              stroke={config.accent}
              strokeWidth="1"
              className={animated ? 'animate-ping' : ''}
              style={{
                animationDelay: `${i * 0.5}s`,
                animationDuration: '3s'
              }}
            />
          ))}
        </g>
      </svg>
      
      {/* Texto "SynapseIA" */}
      {size !== 'small' && (
        <div 
          className="absolute inset-0 flex items-center justify-center"
          style={{ 
            textShadow: `0 0 10px ${config.glow}`,
            color: config.primary,
            fontWeight: 'bold',
            fontSize: size === 'xlarge' ? '8px' : size === 'large' ? '10px' : '12px',
            fontFamily: 'Inter, sans-serif'
          }}
        >
          <span style={{ 
            letterSpacing: '0.05em',
            textTransform: 'uppercase'
          }}>
            Synapse
          </span>
          <span style={{ 
            color: config.accent,
            marginLeft: '2px',
            fontWeight: '900'
          }}>
            IA
          </span>
        </div>
      )}
      
      {/* Estilos CSS en línea */}
      <style jsx>{`
        @keyframes ping {
          0% {
            transform: scale(1);
            opacity: 1;
          }
          50% {
            transform: scale(1.1);
            opacity: 0.8;
          }
          100% {
            transform: scale(1);
            opacity: 1;
          }
        }
        
        @keyframes pulse {
          0%, 100% {
            opacity: 0.3;
          }
          50% {
            opacity: 0.8;
          }
        }
        
        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
};

export default SynapseLogo;
