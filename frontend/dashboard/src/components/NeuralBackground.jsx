import React, { useEffect, useRef } from 'react';

const NeuralBackground = ({ theme = 'neural_network', children }) => {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const isPlaying = useRef(true);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const particles = [];
    const connections = [];
    const neuralNodes = [];
    
    // Configuración según tema
    const themeConfigs = {
      neural_network: {
        particleColor: 'rgba(0, 102, 255, 0.6)',
        connectionColor: 'rgba(124, 58, 237, 0.3)',
        nodeColor: '#0066FF',
        backgroundColor: 'rgba(10, 14, 39, 0.95)'
      },
      quantam_realm: {
        particleColor: 'rgba(0, 206, 209, 0.6)',
        connectionColor: 'rgba(255, 0, 110, 0.3)',
        nodeColor: '#00CED1',
        backgroundColor: 'rgba(26, 0, 51, 0.95)'
      },
      cosmic_consciousness: {
        particleColor: 'rgba(255, 215, 0, 0.6)',
        connectionColor: 'rgba(124, 58, 237, 0.3)',
        nodeColor: '#FFD700',
        backgroundColor: 'rgba(45, 27, 105, 0.95)'
      }
    };

    const config = themeConfigs[theme] || themeConfigs.neural_network;

    // Resize canvas
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Clase para partículas
    class Particle {
      constructor(x, y) {
        this.x = x;
        this.y = y;
        this.vx = (Math.random() - 0.5) * 0.5;
        this.vy = (Math.random() - 0.5) * 0.5;
        this.radius = Math.random() * 2 + 1;
        this.life = 1;
      }

      update() {
        this.x += this.vx;
        this.y += this.vy;
        this.life -= 0.003;
        
        // Bordes con rebote
        if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
        if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
      }

      draw() {
        ctx.save();
        ctx.globalAlpha = this.life * 0.6;
        ctx.fillStyle = config.particleColor;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
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
        this.phase += 0.03;
      }

      draw() {
        const gradient = ctx.createLinearGradient(
          this.state1.x, this.state1.y,
          this.state2.x, this.state2.y
        );
        
        const opacity = 0.3 + Math.sin(this.phase) * 0.2;
        gradient.addColorStop(0, config.connectionColor.replace('0.6', `${opacity}`));
        gradient.addColorStop(0.5, config.connectionColor.replace('0.6', `${opacity * 0.5}`));
        gradient.addColorStop(1, config.connectionColor.replace('0.6', `${opacity * 0.3}`));
        
        ctx.strokeStyle = gradient;
        ctx.lineWidth = 2 + Math.sin(this.phase) * 1;
        ctx.beginPath();
        ctx.moveTo(this.state1.x, this.state1.y);
        
        // Conexión con efecto cuántico
        const midX = (this.state1.x + this.state2.x) / 2;
        const midY = (this.state1.y + this.state2.y) / 2;
        const offset = Math.sin(this.phase) * 20;
        
        ctx.quadraticCurveTo(
          midX, midY - offset,
          midX - offset, midY + offset,
          this.state2.x, this.state2.y
        );
        
        ctx.stroke();
      }
    }

    // Crear nodos neurales
    class NeuralNode {
      constructor(x, y) {
        this.x = x;
        this.y = y;
        this.connections = [];
        this.pulsePhase = Math.random() * Math.PI * 2;
        this.pulseSpeed = 0.02 + Math.random() * 0.02;
        this.baseRadius = 4 + Math.random() * 4;
      }

      addConnection(node) {
        if (!this.connections.includes(node)) {
          this.connections.push(node);
        }
      }

      update() {
        this.pulsePhase += this.pulseSpeed;
      }

      draw() {
        const pulseFactor = 1 + Math.sin(this.pulsePhase) * 0.3;
        const radius = this.baseRadius * pulseFactor;
        
        // Dibujar conexiones
        this.connections.forEach(node => {
          const distance = Math.hypot(node.x - this.x, node.y - this.y);
          const opacity = Math.max(0.1, 1 - distance / 300);
          
          ctx.strokeStyle = config.connectionColor.replace('0.3', opacity.toString());
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(this.x, this.y);
          ctx.lineTo(node.x, node.y);
          ctx.stroke();
        });
        
        // Dibujar nodo
        ctx.save();
        ctx.shadowBlur = 15;
        ctx.shadowColor = config.nodeColor;
        ctx.fillStyle = config.nodeColor;
        ctx.beginPath();
        ctx.arc(this.x, this.y, radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
    }

    // Inicializar nodos neurales en grid
    const nodeRows = 5;
    const nodeCols = 7;
    const nodeSpacingX = canvas.width / (nodeCols + 1);
    const nodeSpacingY = canvas.height / (nodeRows + 1);

    for (let row = 0; row < nodeRows; row++) {
      for (let col = 0; col < nodeCols; col++) {
        const x = (col + 1) * nodeSpacingX + (Math.random() - 0.5) * 50;
        const y = (row + 1) * nodeSpacingY + (Math.random() - 0.5) * 50;
        neuralNodes.push(new NeuralNode(x, y));
      }
    }

    // Conectar nodos cercanos
    neuralNodes.forEach((node, i) => {
      // Conectar con nodos vecinos
      const nearbyNodes = neuralNodes.filter((other, j) => {
        if (i === j) return false;
        const distance = Math.hypot(other.x - node.x, other.y - node.y);
        return distance < 200;
      });
      
      nearbyNodes.slice(0, 2 + Math.floor(Math.random() * 2)).forEach(neighbor => {
        node.addConnection(neighbor);
      });
    });

    // Crear partículas flotantes
    for (let i = 0; i < 50; i++) {
      particles.push(new Particle(
        Math.random() * canvas.width,
        Math.random() * canvas.height
      ));
    }

    // Animación simplificada - solo fondo estático
    const animate = () => {
      // Fondo con degradado sutil
      const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
      gradient.addColorStop(0, config.backgroundColor);
      gradient.addColorStop(1, 'rgba(0, 0, 0, 0.95)');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Sin animaciones gráficas - solo fondo estático
      // Sin partículas, nodos, conexiones u ondas

      if (isPlaying.current) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [theme]);

  return (
    <div className="fixed inset-0 pointer-events-none">
      <canvas
        ref={canvasRef}
        className="w-full h-full"
        style={{ 
          background: 'transparent',
          zIndex: 0
        }}
      />
      <div className="relative z-10 pointer-events-auto">
        {children}
      </div>
    </div>
  );
};

export default NeuralBackground;
