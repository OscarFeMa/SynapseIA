"""
Synapse Council v2.0 - Branding & Visual Identity System
Sistema de branding único y personalidad distintiva para SynapseIA
"""
from typing import Dict, Any, List
from enum import Enum
import json


class SynapseTheme(Enum):
    """Temas visuales predefinidos"""
    NEURAL_NETWORK = "neural_network"
    QUANTUM_REALM = "quantum_realm"
    COSMIC_CONSCIOUSNESS = "cosmic_consciousness"
    DIGITAL_SYNAPSE = "digital_synapse"


class SynapsePersonality:
    """Personalidad y voz única de SynapseIA"""
    
    def __init__(self):
        self.name = "SynapseIA"
        self.tagline = "Conectando Mentes, Amplificando Inteligencia"
        self.mission = "Crear un espacio donde la inteligencia colectiva florece a través del debate estructurado"
        self.vision = "Ser la plataforma líder de razonamiento colaborativo artificial"
        
        # Personalidad de marca
        self.traits = {
            "innovadora": "Siempre explorando nuevos horizontes",
            "colaborativa": "Creemos juntos, no por separado",
            "intuitiva": "La complejidad hecha simple y bella",
            "confiable": "Precisión y honestidad en cada interacción",
            "visionaria": "El futuro del pensamiento artificial hoy"
        }
        
        # Tono de comunicación
        self.communication_tone = {
            "profesional_innovador": "Profesional pero con un toque de magia tecnológica",
            "accesible_experto": "Explicaciones complejas hechas simples",
            "inspirador_confiable": "Inspirar confianza mientras sorprendemos"
        }
    
    def get_branding_config(self) -> Dict[str, Any]:
        """Obtiene configuración completa de branding"""
        return {
            "identity": {
                "name": self.name,
                "tagline": self.tagline,
                "mission": self.mission,
                "vision": self.vision,
                "traits": self.traits,
                "communication_tone": self.communication_tone
            },
            "visual": {
                "primary_colors": {
                    "neural_blue": "#0066FF",
                    "synapse_purple": "#7C3AED", 
                    "quantum_cyan": "#00CED1",
                    "consciousness_gold": "#FFD700"
                },
                "secondary_colors": {
                    "deep_space": "#0A0E27",
                    "nebula_pink": "#FF006E",
                    "plasma_green": "#00FF41",
                    "void_black": "#000000"
                },
                "gradients": {
                    "synapse_flow": "linear-gradient(135deg, #0066FF 0%, #7C3AED 50%, #FFD700 100%)",
                    "quantum_shift": "linear-gradient(45deg, #00CED1, #FF006E, #00FF41)",
                    "consciousness_wave": "radial-gradient(circle, #FFD700, #7C3AED, #0066FF)"
                },
                "typography": {
                    "headings": "'Inter', sans-serif - Apple System, BlinkMacSystemFont, 'Segoe UI', Roboto",
                    "body": "'JetBrains Mono', 'Fira Code', monospace",
                    "accent": "'Space Grotesk', sans-serif"
                },
                "animations": {
                    "synapse_pulse": "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
                    "neural_flicker": "flicker 3s ease-in-out infinite alternate",
                    "quantum_shift": "transform 0.5s ease-in-out",
                    "consciousness_breath": "breathe 4s ease-in-out infinite"
                }
            },
            "experience": {
                "loading_messages": [
                    "Conectando sinapsis neuronales...",
                    "Calibrando red cuántica...",
                    "Sincronizando conciencia colectiva...",
                    "Iniciando cascada sináptica...",
                    "Estableciendo puente dimensional..."
                ],
                "success_messages": [
                    "Sinfonía intelectual alcanzada",
                    "Convergencia neural exitosa",
                    "Estado cuántico establecido",
                    "Consciencia colectiva activada",
                    "Puente dimensional establecido"
                ],
                "error_messages": [
                    "Disrupción en la matriz neuronal",
                    "Colapso cuántico detectado",
                    "Desincronización de conciencia",
                    "Interferencia en la red sináptica",
                    "Anomalía dimensional detectada"
                ],
                "microcopy": {
                    "create_debate": "Iniciar debate sináptico",
                    "add_agent": "Añadir nodo neuronal",
                    "view_metrics": "Monitorear conciencia colectiva",
                    "sync_cloud": "Sincronizar con el cosmos",
                    "manage_workers": "Orquestar red neuronal"
                }
            },
            "unique_features": {
                "synaptic_visualization": "Visualización de conexiones en tiempo real",
                "consciousness_meter": "Medidor de nivel de convergencia intelectual",
                "quantum_states": "Estados cuánticos de los debates",
                "neural_pathways": "Rutas de pensamiento visualizadas",
                "collective_pulse": "Pulso de actividad colectiva"
            }
        }
    
    def get_theme_config(self, theme: SynapseTheme) -> Dict[str, Any]:
        """Obtiene configuración de tema específico"""
        configs = {
            SynapseTheme.NEURAL_NETWORK: {
                "name": "Red Neuronal",
                "description": "Visualización de conexiones cerebrales artificiales",
                "primary": "#0066FF",
                "secondary": "#7C3AED",
                "accent": "#FFD700",
                "background": "linear-gradient(135deg, #0A0E27 0%, #1a1f3a 100%)",
                "animation": "neural_pulse"
            },
            SynapseTheme.QUANTUM_REALM: {
                "name": "Reino Cuántico",
                "description": "Estados superpuestos y probabilidades",
                "primary": "#00CED1",
                "secondary": "#FF006E", 
                "accent": "#00FF41",
                "background": "radial-gradient(circle at center, #0A0E27, #1a0033)",
                "animation": "quantum_shift"
            },
            SynapseTheme.COSMIC_CONSCIOUSNESS: {
                "name": "Conciencia Cósmica",
                "description": "La mente colectiva como fenómeno universal",
                "primary": "#FFD700",
                "secondary": "#7C3AED",
                "accent": "#0066FF",
                "background": "radial-gradient(ellipse at top, #0A0E27, #2d1b69)",
                "animation": "consciousness_breath"
            },
            SynapseTheme.DIGITAL_SYNAPSE: {
                "name": "Sinapsis Digital",
                "description": "La conexión perfecta entre mente y máquina",
                "primary": "#7C3AED",
                "secondary": "#0066FF",
                "accent": "#FF006E",
                "background": "linear-gradient(180deg, #0A0E27, #1a1f3a, #0A0E27)",
                "animation": "synapse_pulse"
            }
        }
        return configs.get(theme, configs[SynapseTheme.NEURAL_NETWORK])
    
    def get_loading_sequence(self) -> List[str]:
        """Secuencia de carga animada"""
        return [
            "🧠 Iniciando red neuronal...",
            "⚡ Calibrando sinapsis...",
            "🌌 Estableciendo conexión cuántica...",
            "✨ Sincronizando conciencia...",
            "🔗 Conectando nodos de pensamiento...",
            "💫 Amplificando inteligencia colectiva..."
        ]
    
    def get_success_animation(self) -> Dict[str, str]:
        """Animación de éxito"""
        return {
            "icon": "🧠✨",
            "message": "Sinfonía Intelectual Activada",
            "subtext": "La convergencia ha sido alcanzada",
            "colors": ["#0066FF", "#7C3AED", "#FFD700"]
        }
    
    def generate_brand_guidelines(self) -> str:
        """Genera guías de marca para desarrolladores"""
        guidelines = f"""
# {self.name} - Guías de Marca v2.0

## Identidad Visual
- **Colores Primarios**: Neural Blue (#0066FF), Synapse Purple (#7C3AED)
- **Colores Secundarios**: Deep Space (#0A0E27), Nebula Pink (#FF006E)
- **Gradientes**: Usar synapse_flow para elementos principales
- **Tipografía**: Inter para headings, JetBrains Mono para código

## Personalidad
- **Tono**: Profesional-innovador, accesible-experto
- **Verbos**: Conectar, amplificar, converger, sincronizar
- **Evitar**: Lenguaje corporativo tradicional, metáforas básicas

## Experiencia Única
- **Loading**: Secuencias temáticas (neuronal, cuántica, cósmica)
- **Microcopy**: Usar términos específicos del dominio
- **Animaciones**: synapse_pulse, quantum_shift, consciousness_breath

## Características Distintivas
- Visualización de conexiones en tiempo real
- Medidor de convergencia intelectual
- Estados cuánticos de debates
- Rutas de pensamiento animadas

## Mensajes Clave
- Éxito: "Sinfonía intelectual alcanzada"
- Error: "Disrupción en la matriz neuronal"
- Creación: "Iniciando cascada sináptica"
        """
        return guidelines


# Singleton instance
_synapse_branding: SynapsePersonality = None


def get_synapse_branding() -> SynapsePersonality:
    """Obtiene instancia singleton del branding"""
    global _synapse_branding
    if _synapse_branding is None:
        _synapse_branding = SynapsePersonality()
    return _synapse_branding
