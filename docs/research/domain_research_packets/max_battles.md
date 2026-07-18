# Paquete de Investigación de Dominio: Max Battles, Dynamax y Gigantamax

Este documento sirve como especificación inicial para el motor de **Max Battles y optimización de Partículas Max**.

## 1. Misión del Dominio
Proporcionar a los usuarios respuestas deterministas sobre:
- ¿Cuántas Partículas Max (MP) y Caramelos necesito para desbloquear y subir de nivel los Max Moves de mi Pokémon?
- ¿Cuál es el mejor equipo y la estrategia de combate para derrotar a un Boss de Power Spot específico?
- ¿Cómo optimizar la recolección diaria de Partículas Max para no perder recursos (cap diario)?

## 2. Especificación Matemática

### Capacidad y Límites de Partículas Max
- **Límite de Almacenamiento:** Máximo de **1000 MP** en inventario de forma simultánea.
- **Límite Diario de Obtención:** **800 MP** por día (se puede exceder en el último reclamo del día, permitiendo hasta 1080 MP teóricos).
- **Fuentes de MP:**
  - Caminar 2 km: +300 MP.
  - Visitar Power Spot: +120 MP (o +100 MP si ya fue visitado).
  - Power Spot con bonificación: +150 MP.

### Costo de Subida de Max Moves (Nivel 1 a 3)
Los Pokémon se clasifican en grupos de coste para desbloquear y subir de nivel sus tres Max Moves (Max Attack/G-Max, Max Guard, Max Spirit).

*Ejemplo de costos estándar (Grupo Kanto/Normal):*
- **Desbloquear Movimiento (Nivel 1):** 400 MP + 100 Caramelos.
- **Subir a Nivel 2:** 600 MP + 40 Caramelos.
- **Subir a Nivel 3:** 800 MP + 40 Caramelos + 40 Caramelos XL.

### Tiers de Max Battle y Costos de Entrada
Para entrar a una batalla se consumen Partículas Max **solo si se derrota al Boss**:

| Tier de Batalla | Costo de Partículas Max (MP) |
|---|---|
| Tier 1 | 250 MP |
| Tier 3 | 400 MP |
| Tier 5 / Legendario | 800 MP |

## 3. Especificación de Datos Requeridos
- **Tablas de Costos por Especie (Grupos):** DAT006 (`unlock_mp`, `level2_mp`, `level3_mp`, `xl_candy_required`).
- **Boss List de Power Spots:** Especies Dynamax/Gigantamax activas con su tier y movimientos.

## 4. Test Vector de Referencia
**Optimización de G-Max Charizard (Nivel 3 Max Attack, Nivel 1 Max Guard, Nivel 1 Max Spirit):**
- Desbloquear Max Guard: 400 MP + 100 Caramelos.
- Desbloquear Max Spirit: 400 MP + 100 Caramelos.
- Subir Max Attack a Nivel 2: 600 MP + 40 Caramelos.
- Subir Max Attack a Nivel 3: 800 MP + 40 Caramelos + 40 Caramelos XL.
- **Costo total de inversión en la especie:** 2200 MP, 280 Caramelos, 40 Caramelos XL.
- Días mínimos de recolección de MP requeridos: $\lceil 2200 / 800 \rceil = 3$ días.

## 5. Tareas para el Siguiente Investigador
1. Investigar si Gigantamax utiliza multiplicadores de costo distintos en los grupos de especies.
2. Crear un planificador de MP que optimice qué spots visitar según la ruta del usuario.
3. Modelar el medidor Dynamax en el simulador de combate de Power Spots.
