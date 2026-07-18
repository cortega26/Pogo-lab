# Paquete de Investigación de Dominio: Mecánicas de Captura y Huida

Este documento especifica las matemáticas y variables necesarias para implementar la **calculadora de probabilidad de captura y optimización de recursos (bayas/bolas)**.

## 1. Misión del Dominio
Proporcionar a los usuarios respuestas deterministas sobre:
- ¿Qué probabilidad tengo de capturar a este jefe de incursión o Pokémon salvaje con mis recursos actuales?
- ¿Qué combinación de Poké Ball y baya minimiza el costo esperado de captura?
- ¿Cuál es el riesgo acumulado de que el Pokémon huya (flee rate) tras $N$ intentos fallidos?

## 2. Especificación Matemática

### Probabilidad de Captura por Lanzamiento
La probabilidad de éxito de captura en un tiro específico se define como:

$$P_{catch} = 1 - (1 - \frac{BCR}{2 \times CPM})^{Multiplier}$$

Donde:
- $BCR$ (Base Capture Rate) es la tasa de captura base de la especie (ej. 2% para legendarios, 20% para iniciales).
- $CPM$ es el multiplicador de CP del Pokémon según su nivel salvaje.
- $Multiplier$ es el factor de bonificación acumulado por lanzamiento:

$$Multiplier = Ball \times Berry \times Curveball \times Throw \times Medal$$

### Multiplicadores de Captura

| Variable | Opción | Valor del Multiplicador |
|---|---|---|
| **Ball** | Poké Ball / Premier Ball | 1.0 |
| | Great Ball | 1.5 |
| | Ultra Ball | 2.0 |
| | Beast Ball (vs Ultra Beasts) | 5.0 (1.0 vs otros) |
| **Berry** | Ninguna / Pinap / Nanab | 1.0 |
| | Razz Berry | 1.5 |
| | Silver Pinap Berry | 1.8 |
| | Golden Razz Berry | 2.5 |
| **Curveball**| Tiro recto | 1.0 |
| | Curveball (Tiro curvo) | 1.7 |
| **Medal** | Sin medallas | 1.0 |
| | Bronce (+1) | 1.1 |
| | Plata (+2) | 1.2 |
| | Oro (+3) | 1.3 |
| | Platino (+4) | 1.4 |

*Nota sobre medallas para Pokémon de doble tipo:* Se calcula el promedio aritmético de los bonos de ambos tipos:
$$Medal = \frac{Bono_{Tipo1} + Bono_{Tipo2}}{2}$$

### Multiplicador por Tamaño de Tiro (Throw)
El multiplicador de tiro no es discreto; depende linealmente del radio del anillo interno $r \in [0.1, 1.0]$:

$$Throw = 2 - r$$

- Si el tiro impacta fuera del círculo de color, $Throw = 1.0$.
- El juego dibuja etiquetas visuales según el rango de $r$ en el momento del impacto:
  - Nice: $r \in [0.701, 1.000]$ (Multiplicador $1.00$ a $1.30$)
  - Great: $r \in [0.301, 0.700]$ (Multiplicador $1.30$ a $1.70$)
  - Excellent: $r \in [0.100, 0.300]$ (Multiplicador $1.70$ a $2.00$)

### Probabilidad Acumulada y Huida (Flee)
La probabilidad de capturar al Pokémon en un número máximo de $N$ lanzamientos, considerando que el Pokémon puede huir en cada intento fallido con una tasa base de huida $BFR$ (Base Flee Rate):

- Probabilidad de huir tras tiro fallido: $P_{flee} = BFR \times CPM$ (salvo en incursiones, donde la huida solo ocurre al agotar las Premier Balls).
- Probabilidad de capturar exactamente en el tiro $i$:
  $$P(Catch = i) = P_{catch} \times \prod_{j=1}^{i-1} (1 - P_{catch}) \times (1 - P_{flee})$$

## 3. Especificación de Datos Requeridos
- **Base Stats (Especies):** DAT001 (`base_capture_rate`, `base_flee_rate`).
- **CPM Table:** Multiplicador por nivel de 1 a 35 (límite salvaje, 35 con boost de clima).

## 4. Test Vector de Referencia
**Captura de Mewtwo (BCR = 0.02) en Raid (CPM = 0.5974 a Nivel 20):**
- Tiro: Ultra Ball (2.0) + Baya Frambu Dorada (2.5) + Curva (1.7) + Tiro Excellent mediano ($r=0.2$ $\rightarrow$ $Throw=1.8$) + Doble Medalla de Platino de Tipo Psíquico (1.4).
- Multiplier = $2.0 \times 2.5 \times 1.7 \times 1.8 \times 1.4 = 21.42$ (si no hay caps en el multiplicador; en incursiones la bola es Premier Ball = 1.0, recalculamos):
- Multiplier (Raid) = $1.0 \times 2.5 \times 1.7 \times 1.8 \times 1.4 = 10.71$.
- Probabilidad de captura:
  $$P_{catch} = 1 - (1 - \frac{0.02}{2 \times 0.597400})^{10.71} = 1 - (1 - 0.016739)^{10.71} = 1 - (0.983261)^{10.71} \approx 0.1654 \approx 16.54\%$$

## 5. Tareas para el Siguiente Investigador
1. Crear el endpoint `/api/v1/capture/compute/` que devuelva la curva de probabilidad acumulada.
2. Implementar los deslizadores en Alpine.js para simular el radio del tiro de $1.0$ a $0.1$.
