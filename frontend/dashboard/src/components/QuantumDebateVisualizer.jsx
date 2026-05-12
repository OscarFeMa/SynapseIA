import React, { useState, useEffect, useRef } from 'react';

const QuantumDebateVisualizer = ({ debateData, theme = 'quantum_realm' }) => {
  const canvasRef = useRef(null);
  const [selectedState, setSelectedState] = useState(null);
  const [animationSpeed, setAnimationSpeed] = useState(1);
  const [isPlaying, setIsPlaying] = useState(true);

  const themeConfigs = {
    quantam_realm: {
      background: 'radial-gradient(ellipse at center, #0A0E27, #1a0033)',
      states: {
        superposition: 'rgba(0, 206, 209, 0.8)',
        collapsed: 'rgba(255, 0, 110, 0.8)',
        entangled: 'rgba(0, 255, 65, 0.8)',
        measured: 'rgba(255, 215, 0, 0.8)'
      },
      connections: 'rgba(0, 206, 209, 0.6)',
      particles: 'rgba(0, 255, 65, 0.4)'
    },
    cosmic_consciousness: {
      background: 'radial-gradient(ellipse at top, #0A0E27, #2d1b69)',
      states: {
        superposition: 'rgba(255, 215, 0, 0.8)',
        collapsed: 'rgba(124, 58, 237, 0.8)',
        entangled: 'rgba(0, 102, 255, 0.8)',
        measured: 'rgba(255, 0, 110, 0.8)'
      },
      connections: 'rgba(255, 215, 0, 0.6)',
      particles: 'rgba(124, 58, 237, 0.4)'
    }
  };

  const config = themeConfigs[theme] || themeConfigs.quantam_realm;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let animationId;

    // Clase para estados cuánticos
    class QuantumState {
      constructor(x, y, state, agentName) {
        this.x = x;
        this.y = y;
        this.state = state; // superposition, collapsed, entangled, measured
        this.agentName = agentName;
        this.energy = Math.random() * 100;
        this.phase = Math.random() * Math.PI * 2;
        this.connections = [];
        this.targetX = x;
        this.targetY = y;
        this.oscillation = 0;
      }

      update() {
        this.phase += 0.05 * animationSpeed;
        this.oscillation = Math.sin(this.phase) * 10;
        
        // Movimiento sutil
        this.x += (this.targetX - this.x) * 0.02;
        this.y += (this.targetY - this.y) * 0.02;
        
        // Cambio de estado aleatorio (simulación de colapso)
        if (Math.random() < 0.001) {
          const states = ['superposition', 'collapsed', 'entangled', 'measured'];
          this.state = states[Math.floor(Math.random() * states.length)];
        }
      }

      draw() {
        const baseSize = 20 + this.energy / 5;
        const size = baseSize + Math.sin(this.phase) * 5;
        
        // Efecto de brillo según estado
        const glowSize = size * 2;
        const gradient = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, glowSize);
        
        if (this.state === 'superposition') {
          gradient.addColorStop(0, config.states.superposition);
          gradient.addColorStop(0.5, config.states.superposition.replace('0.8', '0.4'));
          gradient.addColorStop(1, 'transparent');
        } else if (this.state === 'collapsed') {
          gradient.addColorStop(0, config.states.collapsed);
          gradient.addColorStop(0.3, config.states.collapsed.replace('0.8', '0.6'));
          gradient.addColorStop(1, 'transparent');
        } else if (this.state === 'entangled') {
          gradient.addColorStop(0, config.states.entangled);
          gradient.addColorStop(0.4, config.states.entangled.replace('0.8', '0.5'));
          gradient.addColorStop(1, 'transparent');
        } else {
          gradient.addColorStop(0, config.states.measured);
          gradient.addColorStop(0.5, config.states.measured.replace('0.8', '0.7'));
          gradient.addColorStop(1, 'transparent');
        }
        
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(this.x, this.y, size, 0, Math.PI * 2);
        ctx.fill();
        
        // Núcleo brillante
        ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
        ctx.beginPath();
        ctx.arc(this.x, this.y, size / 4, 0, Math.PI * 2);
        ctx.fill();
      }

      addConnection(state) {
        if (!this.connections.includes(state)) {
          this.connections.push(state);
        }
      }
    }

    // Clase para conexiones cuánticas
    class QuantumConnection {
      constructor(state1, state2) {
        this.state1 = state1;
        this.state2 = state2;
        this.strength = Math.random() * 0.8 + 0.2;
        this.phase = Math.random() * Math.PI * 2;
      }

      update() {
        this.phase += 0.03 * animationSpeed;
      }

      draw() {
        const gradient = ctx.createLinearGradient(
          this.state1.x, this.state1.y,
          this.state2.x, this.state2.y
        );
        
        const opacity = 0.3 + Math.sin(this.phase) * 0.2;
        gradient.addColorStop(0, config.connections.replace('0.6', `${opacity}`));
        gradient.addColorStop(0.5, config.connections.replace('0.6', `${opacity * 0.5}`));
        gradient.addColorStop(1, config.connections.replace('0.6', `${opacity * 0.3}`));
        
        ctx.strokeStyle = gradient;
        ctx.lineWidth = 2 + Math.sin(this.phase) * 1;
        ctx.beginPath();
        ctx.moveTo(this.state1.x, this.state1.y);
        
        // Conexión con efecto cuántico
        const midX = (this.state1.x + this.state2.x) / 2;
        const midY = (this.state1.y + this.state2.y) / 2;
        const offset = Math.sin(this.phase) * 20;
        
        ctx.quadraticCurveTo(
          midX + offset, midY - offset,
          midX - offset, midY + offset,
          this.state2.x, this.state2.y
        );
        
        ctx.stroke();
      }
    }

    // Inicializar estados cuánticos desde datos de debate
    const quantumStates = [];
    const agents = debateData?.agents || [];
    
    agents.forEach((agent, index) => {
      const angle = (index / agents.length) * Math.PI * 2;
      const radius = 150;
      const x = canvas.width / 2 + Math.cos(angle) * radius;
      const y = canvas.height / 2 + Math.sin(angle) * radius;
      
      const state = new QuantumState(x, y, 'superposition', agent.name);
      quantumStates.push(state);
    });

    // Conectar estados cercanos
    quantumStates.forEach((state, i) => {
      const nearbyStates = quantumStates.filter((other, j) => {
        if (i === j) return false;
        const distance = Math.hypot(other.x - state.x, other.y - state.y);
        return distance < 200;
      });
      
      nearbyStates.slice(0, 2 + Math.floor(Math.random() * 2)).forEach(nearby => {
        state.addConnection(nearby);
      });
    });

    // Partículas cuánticas flotantes
    const particles = [];
    for (let i = 0; i < 30; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        size: Math.random() * 3 + 1,
        life: 1
      });
    }

    const resizeCanvas = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    const animate = () => {
      // Fondo cuántico
      const bgGradient = ctx.createRadialGradient(
        canvas.width / 2, canvas.height / 2, 0,
        canvas.width / 2, canvas.height / 2, Math.max(canvas.width, canvas.height) / 2
      );
      bgGradient.addColorStop(0, config.background);
      bgGradient.addColorStop(1, 'rgba(0, 0, 0, 0.95)');
      ctx.fillStyle = bgGradient;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Actualizar y dibujar partículas
      particles.forEach((particle, index) => {
        particle.x += particle.vx * animationSpeed;
        particle.y += particle.vy * animationSpeed;
        particle.life -= 0.005;
        
        // Rebote en bordes
        if (particle.x < 0 || particle.x > canvas.width) particle.vx *= -1;
        if (particle.y < 0 || particle.y > canvas.height) particle.vy *= -1;
        
        // Regenerar partícula muerta
        if (particle.life <= 0) {
          particles[index] = {
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            size: Math.random() * 3 + 1,
            life: 1
          };
        }
        
        // Dibujar partícula
        ctx.fillStyle = config.particles.replace('0.4', `${particle.life * 0.4}`);
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fill();
      });

      // Actualizar y dibujar estados cuánticos
      quantumStates.forEach(state => {
        state.update();
        state.draw();
      });

      // Dibujar conexiones cuánticas
      const connections = [];
      quantumStates.forEach(state => {
        state.connections.forEach(connectedState => {
          if (!connections.some(conn => 
            (conn[0] === state && conn[1] === connectedState) ||
            (conn[0] === connectedState && conn[1] === state))) {
            connections.push([state, connectedState]);
          }
        });
      });

      connections.forEach(([state1, state2]) => {
        const connection = new QuantumConnection(state1, state2);
        connection.update();
        connection.draw();
      });

      // Efecto de onda cuántica ocasional
      if (Math.random() < 0.02) {
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const waveRadius = (Date.now() / 100) % 200;
        
        ctx.strokeStyle = config.connections;
        ctx.lineWidth = 1;
        ctx.globalAlpha = 0.3;
        ctx.beginPath();
        ctx.arc(centerX, centerY, waveRadius, 0, Math.PI * 2);
        ctx.stroke();
        ctx.globalAlpha = 1;
      }

      if (isPlaying) {
        animationId = requestAnimationFrame(animate);
      }
    };

    if (isPlaying) {
      animate();
    }

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }, [debateData, theme, animationSpeed, isPlaying]);

  return (
    <div className="relative w-full h-full bg-black rounded-lg overflow-hidden">
      {/* Canvas principal */}
      <canvas
        ref={canvasRef}
        className="w-full h-full"
        onClick={() => {
          // Seleccionar estado aleatorio al hacer clic
          const states = ['superposition', 'collapsed', 'entangled', 'measured'];
          setSelectedState(states[Math.floor(Math.random() * states.length)]);
        }}
      />
      
      {/* Controles superpuestos */}
      <div className="absolute top-4 left-4 right-4 flex justify-between items-start pointer-events-none">
        {/* Panel de información */}
        <div className="bg-black bg-opacity-80 text-white p-4 rounded-lg pointer-events-auto max-w-sm">
          <h3 className="text-lg font-bold mb-3 text-cyan-400">Visualizador Cuántico</h3>
          
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-300">Estados Activos:</span>
              <span className="text-cyan-400 font-mono">{debateData?.agents?.length || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Estado Seleccionado:</span>
              <span className="text-yellow-400 capitalize">
                {selectedState || 'superposition'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Velocidad:</span>
              <span className="text-green-400 font-mono">{animationSpeed}x</span>
            </div>
          </div>
          
          {/* Leyenda de estados */}
          <div className="mt-4 pt-3 border-t border-gray-700">
            <h4 className="text-sm font-semibold mb-2 text-cyan-300">Estados Cuánticos</h4>
            <div className="space-y-1 text-xs">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-cyan-400"></div>
                <span>Superposición</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <span>Colapsado</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-green-400"></div>
                <span>Entrelazado</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
                <span>Medido</span>
              </div>
            </div>
          </div>
        </div>
        
        {/* Controles de animación */}
        <div className="bg-black bg-opacity-80 text-white p-3 rounded-lg pointer-events-auto">
          <div className="flex flex-col space-y-2">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="px-3 py-1 bg-cyan-600 hover:bg-cyan-700 rounded text-sm transition-colors"
            >
              {isPlaying ? '⏸ Pausar' : '▶ Reproducir'}
            </button>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setAnimationSpeed(Math.max(0.1, animationSpeed - 0.5))}
                className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs transition-colors"
              >
                -
              </button>
              <span className="text-xs text-gray-400">Velocidad</span>
              <select
                id="animation-speed-select"
                name="animation-speed-select"
                value={animationSpeed}
                onChange={(e) => setAnimationSpeed(parseInt(e.target.value))}
                className="bg-gray-900 text-gray-300 px-3 py-2 rounded-lg border border-gray-700 focus:border-blue-500 focus:outline-none text-sm"
              >
                <option value="0.1">0.1x</option>
                <option value="0.5">0.5x</option>
                <option value="1">1x</option>
                <option value="1.5">1.5x</option>
                <option value="2">2x</option>
                <option value="2.5">2.5x</option>
                <option value="3">3x</option>
              </select>
              <button
                onClick={() => setAnimationSpeed(Math.min(3, animationSpeed + 0.5))}
                className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs transition-colors"
              >
                +
              </button>
            </div>
            
            <button
              onClick={() => {
                // Resetear animación
                setAnimationSpeed(1);
                setSelectedState(null);
              }}
              className="px-2 py-1 bg-purple-600 hover:bg-purple-700 rounded text-xs transition-colors"
            >
              🔄 Reset
            </button>
          </div>
        </div>
      </div>
      
      {/* Mensaje flotante */}
      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-80 text-white px-4 py-2 rounded-lg pointer-events-none">
        <p className="text-sm text-cyan-300">
          🌌 Click en cualquier punto para seleccionar estado cuántico
        </p>
      </div>
    </div>
  );
};

export default QuantumDebateVisualizer;
