# Paquete de Investigación de Dominio: Economía de Recursos y Planificación de Mejoras

Este documento especifica los costos, multiplicadores y lógica para la **calculadora de recursos (Polvos/Caramelos) y optimización de inversión**.

## 1. Misión del Dominio
Proporcionar a los usuarios respuestas deterministas sobre:
- ¿Cuántos Polvos Estelares (Stardust), Caramelos (Candy) y Caramelos XL (Candy XL) exactos requiero para llevar a mi Pokémon de nivel $X$ a nivel $Y$?
- ¿Qué tan rentable es purificar a un Pokémon oscuro considerando el descuento de recursos y el cambio de nivel directo a Nivel 25?
- ¿Cómo maximizar los caramelos XL obtenidos al caminar o transferir Pokémon?

## 2. Especificación Matemática

### Modificadores de Costo por Estado del Pokémon

| Estado | Coste Polvos Estelares | Coste Caramelos | Nivel Inicial de Captura |
|---|---|---|---|
| Estándar | 100% | 100% | Salvaje: 1-35; Incursión: 20/25; Huevos: 20 |
| **Shadow** (Oscuro) | **120%** | **120%** | Incursión/Invasión: 8/13 (Boost clima) |
| **Lucky** (Afortunado) | **50%** | 100% | Intercambio: Nivel del Pokémon previo |
| **Purified** (Purificado) | **90%** | **90%** | Sube automáticamente a **Nivel 25** |

### Costo de Segundo Ataque Cargado
Desbloquear el segundo ataque cargado depende de la categoría de kilómetros del Pokémon Buddy:

| Grupo de Especie | Polvos Estelares | Caramelos | Ejemplos |
|---|---|---|---|
| Iniciales / Bebés | 10,000 | 25 | Pikachu, Bulbasaur, Lucario (Bebé) |
| Estándar 3km | 50,000 | 50 | Machop, Gastly |
| Raros 5km | 75,000 | 75 | Gible, Larvitar, Snorlax |
| Legendarios 20km | 100,000 | 100 | Mewtwo, Kyogre, Zacian |

*Nota:* Si el Pokémon es Shadow, el coste se multiplica por **1.2**. Si es Purificado, se multiplica por **0.9**. Si es Lucky, los costes de Polvo/Caramelo de segundo ataque no reciben el 50% de descuento (sólo aplica al power-up).

### Caramelos XL al Transferir Pokémon
La probabilidad de obtener Caramelos XL al transferir un Pokémon depende de su nivel:

| Nivel del Pokémon ($L$) | Probabilidad Base de obtener 1 Caramelo XL |
|---|---|
| $L < 15$ | ~0% a 5% |
| $15 \le L < 20$ | ~8% |
| $20 \le L < 25$ | ~15% |
| $25 \le L < 30$ | ~25% |
| $30 \le L < 35$ | ~33% |
| $35 \le L$ | ~60% a 80% |

## 3. Especificación de Datos Requeridos
- **Tabla Master de Power-Up:** DAT001 (`level`, `stardust_cost`, `candy_cost`, `candy_xl_cost` por cada paso de medio nivel de 1 a 50).

## 4. Test Vector de Referencia
**Subir Mewtwo de Nivel 20 (Raid) a Nivel 40 (Perfecto):**
- Mewtwo es Legendario, coste estándar.
- Coste acumulado de Polvo Estelar de L20 a L40: **225,000 Polvos**.
- Coste acumulado de Caramelos de L20 a L40: **248 Caramelos**.
- **Si fuera Shadow:**
  - Polvos: $225,000 \times 1.2 = 270,000$ Polvos.
  - Caramelos: $248 \times 1.2 = 297.6 \approx 298$ Caramelos.
- **Si fuera Lucky:**
  - Polvos: $225,000 \times 0.5 = 112,500$ Polvos.
  - Caramelos: $248 \times 1.0 = 248$ Caramelos.

## 5. Tareas para el Siguiente Investigador
1. Importar la tabla completa de costos de power-up (80 filas de 0.5 en 0.5 niveles hasta nivel 50).
2. Crear la interfaz interactiva `ResourcePlanner` para presupuestar múltiples Pokémon simultáneamente.
