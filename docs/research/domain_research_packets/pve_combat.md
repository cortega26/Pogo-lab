# Paquete de Investigación de Dominio: Combate PvE, Incursiones y Breakpoints

Este documento es una guía técnica y matemática para el agente que implemente el motor de **combate PvE, estimadores de incursiones y breakpoints**.

## 1. Misión del Dominio
Proporcionar a los usuarios respuestas deterministas sobre:
- ¿Qué nivel e IV de Ataque requiere mi Pokémon para infligir el máximo daño posible por golpe rápido contra un jefe de raid específico (breakpoint)?
- ¿Cuál es la probabilidad matemática y el tiempo esperado para derrotar a un jefe de raid (Solo/Duo/Trio)?
- ¿Cuándo es eficiente esquivar los ataques cargados del jefe (dodge ROI)?

## 2. Especificación Matemática

### Daño por Golpe (PvE)
El daño discreto por golpe rápido o cargado se calcula mediante:

$$Damage = \lfloor 0.5 \times Power \times \frac{Atk_{effective}}{Def_{effective}} \times STAB \times Effectiveness \times Weather \times Friend \times Shadow \times Mega \rfloor + 1$$

Donde:
- $Atk_{effective} = (BaseAttack + IV_{Attack}) \times CPM_{attacker}$
- $Def_{effective} = (BaseDefense + IV_{Defense}) \times CPM_{defender}$ (para jefes de raid, la Defensa se multiplica por el CPM específico del tier del Boss).
- $STAB = 1.2$ si el tipo del movimiento coincide con el tipo del atacante; $1.0$ de lo contrario.
- $Effectiveness \in \{2.56, 1.6, 0.625, 0.39\}$ para multiplicadores de tipos (doble debilidad, debilidad, resistencia, doble resistencia/inmunidad).
- $Weather = 1.2$ si el tipo del movimiento está potenciado por el clima activo.
- $Friend \in \{1.03, 1.05, 1.07, 1.10\}$ según el nivel máximo de amistad en la sala.
- $Shadow = 1.2$ para daño infligido por un Pokémon oscuro.
- $Mega = 1.3$ si hay un compañero con Mega activa compartiendo tipo; $1.1$ para tipos distintos (no acumulativos).

### Ticks de Servidor y Discretización (0.5s)
El combate en raids no es continuo. El servidor procesa el daño en ventanas discretas de **0.5 segundos (ticks)**. 
- La duración de un movimiento rápido en el Game Master está definida en milisegundos (e.g. 1200ms).
- En el juego real, este movimiento dura $\lceil 1200ms / 500ms \rceil \times 500ms = 1500ms$ (3 ticks) bajo validaciones del servidor con lag de red.
- **Regla del Motor:** El simulador PvE debe modelar el flujo de combate por ticks discretos, no por DPS promedio continuo.

### Weave DPS (DPS de Ciclo)
Para comparar combinaciones de ataques rápidos y cargados:

$$CycleDPS = \frac{N_{fast} \times Damage_{fast} + Damage_{charged}}{N_{fast} \times Duration_{fast} + Duration_{charged}}$$

Donde $N_{fast}$ es el número de ataques rápidos requeridos para acumular la energía del ataque cargado:

$$N_{fast} = \lceil \frac{Energy_{charged}}{Energy_{fast}} \rceil$$

## 3. Especificación de Datos Requeridos
- **Base Stats (Especies):** DAT001 (`base_atk`, `base_def`, `base_stam`).
- **CPM Table:** Multiplicador por nivel de 1 a 50 (con medios niveles).
- **Moves Database (PvE):** `move_id`, `power`, `energy_gain` (rápido), `energy_cost` (cargado), `duration_ms`.
- **Raid Boss Database:** `boss_species_id`, `tier`, `cp_boss`, `hp_boss` (fijo según el tier: Tier 1 = 600, Tier 3 = 3600, Tier 5 = 15000, Mega = 15000).

## 4. Test Vector de Referencia
**Caso Breakpoint Mewtwo L40 (Ataque=15) vs Machamp Raid Boss L30 (Defensa=162):**
- Atacante: Mewtwo, Movimiento Rápido: Confusión (Power=20, STAB=1.2, Tipo Psíquico).
- CPM Mewtwo L40 = 0.790300.
- $Atk_{effective} = (300 + 15) \times 0.7903 = 248.94$.
- CPM Boss Machamp L30 = 0.731700.
- $Def_{effective} = 162 \times 0.7317 = 118.53$ (multiplicado por CPM del Boss o tier).
- Daño proyectado sin modificadores adicionales:
  $$Damage = \lfloor 0.5 \times 20 \times \frac{248.94}{118.53} \times 1.2 \times 1.6 \rfloor + 1 = \lfloor 40.32 \rfloor + 1 = 41$$

## 5. Tareas para el Siguiente Investigador
1. Crear el modelo de datos `RaidBoss` para registrar las rotaciones vigentes.
2. Implementar `engine/combat/pve.py` puro sin dependencias de Django.
3. Escribir tests de Hypothesis para validar la monotonía de Weave DPS respecto a la energía obtenida.
