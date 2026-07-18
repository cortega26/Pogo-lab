# Paquete de Investigación de Dominio: Combate PvP, GBL y Stat Product

Este documento detalla las matemáticas y algoritmos necesarios para implementar la **simulación PvP, rankings de IVs y breakpoints de Trainer Battles (GBL)**.

## 1. Misión del Dominio
Proporcionar a los usuarios respuestas deterministas sobre:
- ¿Qué combinaciones de IVs maximizan el Stat Product de mi Pokémon para ligas con límite de CP (1500/2500)?
- ¿Quién gana la prioridad del ataque cargado (CMP) en un espejo?
- ¿Cuáles son los matchups clave y contadores en un meta de copa temático?

## 2. Especificación Matemática

### Daño en Trainer Battles (PvP)
El daño por turno en PvP tiene un multiplicador plano de 1.3:

$$Damage = \lfloor 0.5 \times Power \times \frac{Atk_{effective}}{Def_{effective}} \times STAB \times Effectiveness \times 1.3 \times Shadow \times StageMultiplier \rfloor + 1$$

Donde:
- $Atk_{effective} = (BaseAttack + IV_{Attack}) \times CPM_{attacker}$
- $Def_{effective} = (BaseDefense + IV_{Defense}) \times CPM_{defender}$
- El factor **1.3** es un multiplicador global constante exclusivo de PvP.
- $StageMultiplier$ es el multiplicador de bufos/debufos en la estadística.

### Multiplicadores de Stage (Buffs/Debuffs)
Los bufos de ataque o defensa se miden en niveles de -4 a +4:

| Stage | Multiplicador | Valor Decimal |
|:---:|:---:|:---:|
| -4 | 4/8 | 0.50 |
| -3 | 4/7 | 0.5714 |
| -2 | 4/6 | 0.6667 |
| -1 | 4/5 | 0.80 |
| 0 | 4/4 | 1.00 |
| +1 | 5/4 | 1.25 |
| +2 | 6/4 | 1.50 |
| +3 | 7/4 | 1.75 |
| +4 | 8/4 | 2.00 |

### Stat Product (Producto de Estadísticas)
Para optimizar un Pokémon bajo un cap de CP (e.g. 1500 CP):

$$StatProduct = Atk_{eff} \times Def_{eff} \times Stam_{eff}$$

Donde:
- $Atk_{eff} = (BaseAttack + IV_{Attack}) \times CPM$
- $Def_{eff} = (BaseDefense + IV_{Defense}) \times CPM$
- $Stam_{eff} = \lfloor (BaseStamina + IV_{Stamina}) \times CPM \rfloor$
- Se busca maximizar $StatProduct$ variando el nivel y los IVs de forma que el CP proyectado sea $\le CP_{cap}$.
- Generalmente, IVs bajos en Ataque y altos en Defensa/HP maximizan el Stat Product porque el Ataque pondera el doble en la fórmula de CP.

### Turnos PvP y CMP Tie (Prioridad)
- Cada turno en PvP dura exactamente **0.5 segundos**.
- Los ataques rápidos duran entre 1 y 5 turnos.
- La energía y el daño de los ataques rápidos se aplican en el último turno de su duración.
- Si ambos jugadores lanzan un ataque cargado en el mismo turno, se desempata por **CMP (Charged Move Priority)**: el Pokémon con el **Ataque Real más alto** ($Atk_{eff}$) actúa primero. Si empatan en Ataque Real, se decide al azar.

## 3. Especificación de Datos Requeridos
- **Base Stats (Especies):** DAT001 (`base_atk`, `base_def`, `base_stam`).
- **Moves Database (PvP):** `move_id`, `power`, `energy_gain` (rápido), `energy_cost` (cargado), `duration_turns`, `stat_effects_spec`.
- **CP Caps:** 1500 (Great League), 2500 (Ultra League), 500 (Little League).

## 4. Test Vector de Referencia
**Stat Product de Medicham (L50, 15/15/15) en Great League (Cap 1500):**
- Medicham Base: Atk=121, Def=152, Stam=155.
- A L50, CPM = 0.840000.
- $CP = \lfloor (136 \times \sqrt{167} \times \sqrt{170} \times 0.84^2) / 10 \rfloor = 1431$ CP.
- $StatProduct = (136 \times 0.84) \times (167 \times 0.84) \times \lfloor 170 \times 0.84 \rfloor = 114.24 \times 140.28 \times 142 \approx 2,275,548$.
- Si sube a L50.5 (Best Buddy, CPM = 0.8427), su CP es 1449 y el Stat Product aumenta.

## 5. Tareas para el Siguiente Investigador
1. Crear la app `apps/pvp/` con el backend para calcular el ranking de IVs (1 a 4096).
2. Implementar `engine/combat/pvp.py` con el motor de turnos y CMP.
3. Asegurar que los rankings de IVs para PvP se precalculen o cacheen para evitar latencia de base de datos.
