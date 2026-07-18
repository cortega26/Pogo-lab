## Cómo usar este paquete

Este paquete contiene **dos prompts secuenciales**.

### Prompt 1 — Mapa canónico y priorización

Ejecutarlo primero. Su función es:

- descubrir todos los dominios matemáticos, estadísticos y de optimización relevantes;
- localizar las mejores fuentes disponibles;
- distinguir datos oficiales, comunitarios, inferidos y empíricos;
- identificar discrepancias;
- construir un inventario de calculadoras y datasets;
- priorizar qué módulos deben investigarse e implementarse primero.

### Prompt 2 — Verificación e implementación por dominio

Ejecutarlo después, en una conversación nueva, adjuntando el informe completo del Prompt 1.

Debe ejecutarse una vez por cada dominio prioritario, por ejemplo:

- intercambios e IV;
- PvE, DPS, TDO y breakpoints;
- PvP;
- captura;
- recursos;
- Max Battles.

No conviene pedir al segundo agente que profundice todos los dominios simultáneamente. El resultado perdería precisión y auditabilidad.

---

# PROMPT 1 — MAPA CANÓNICO DE MECÁNICAS, MATEMÁTICAS, DATOS Y DECISIONES

## Rol

Actúa como un equipo interdisciplinario compuesto por:

- investigador de Pokémon GO;
- analista estadístico;
- matemático aplicado;
- data analyst;
- data engineer;
- especialista en simulación;
- diseñador de calculadoras;
- analista de producto;
- investigador de fuentes y procedencia;
- revisor adversarial de afirmaciones técnicas.

Tu misión es producir el **Research Pack v1** para una plataforma global que explique cómo funciona realmente Pokémon GO y convierta esa evidencia en calculadoras, análisis y recomendaciones prácticas.

No te limites a recopilar fórmulas conocidas. Debes determinar:

1. qué se conoce;
2. cómo se conoce;
3. qué fuente lo respalda;
4. qué tan vigente está;
5. qué supuestos utiliza;
6. qué contradicciones existen;
7. qué puede implementarse de forma reproducible;
8. qué sigue siendo incierto;
9. qué decisiones prácticas puede mejorar.

---

## 1. Visión del producto

La futura plataforma combinará:

### Mechanics Lab

Explicaciones matemáticas, estadísticas, experimentos, datasets, simulaciones y auditorías de mecánicas.

### Decision Planner

Herramientas que transforman la evidencia en decisiones prácticas:

- capturar o ignorar;
- intercambiar o conservar;
- evolucionar ahora o esperar;
- usar o guardar recursos;
- potenciar o no potenciar;
- priorizar PvE, PvP o Max Battles;
- comparar estrategias;
- estimar costos, beneficios y probabilidades.

La propuesta de valor unificada es:

> **Entiende cómo funciona realmente Pokémon GO y usa esos datos para decidir mejor.**

El flujo conceptual es:

> **Entender → Calcular → Comparar → Registrar → Analizar → Decidir**

---

## 2. Objetivo de esta investigación

Construye un mapa exhaustivo, trazable y priorizado de:

- mecánicas cuantificables;
- fórmulas;
- estadísticas;
- tasas;
- distribuciones;
- algoritmos;
- datasets;
- fuentes;
- calculadoras existentes;
- herramientas de optimización;
- brechas de información;
- discrepancias entre teoría y observación;
- oportunidades de análisis empírico;
- decisiones prácticas derivables.

El resultado debe servir simultáneamente como:

1. inventario de investigación;
2. mapa de fuentes;
3. backlog de calculadoras;
4. base para diseñar modelos de datos;
5. guía para validar fórmulas;
6. especificación inicial para un equipo de desarrollo;
7. lista de investigaciones empíricas futuras.

No diseñes todavía la aplicación completa ni desarrolles código de producción.

---

# 3. Principios obligatorios de investigación

## 3.1. No asumir que una tasa conocida es oficial

Para cada afirmación clasifica su procedencia:

- **Oficial:** publicada explícitamente por Pokémon GO, Scopely Explore, The Pokémon Company o soporte oficial.
- **Datos públicos del juego:** disponibles mediante archivos o datasets públicos mantenidos por terceros, con procedencia explicada.
- **Datamining documentado:** extraído por la comunidad, sin tratarlo como anuncio oficial.
- **Investigación comunitaria:** inferido mediante experimentos o grandes muestras.
- **Consenso comunitario:** repetido ampliamente, pero sin fuente primaria robusta.
- **Inferencia matemática:** derivado de reglas aceptadas.
- **Hipótesis:** explicación plausible pendiente de validación.
- **Desconocido:** no existe evidencia suficiente.

No presentes una afirmación comunitaria como oficial.

## 3.2. Vigencia

Pokémon GO cambia con frecuencia.

Para cada regla, fórmula o dato registra:

- fecha de publicación;
- fecha efectiva;
- fecha de última verificación;
- versión, temporada o periodo aplicable;
- si existe evidencia de cambios silenciosos;
- si el dato es histórico o vigente;
- si el cambio afecta resultados anteriores.

Usa como fecha de corte la fecha exacta de ejecución.

## 3.3. Triangulación

Una fórmula o tasa crítica debe verificarse, cuando sea posible, mediante:

1. fuente oficial;
2. fuente técnica o dataset independiente;
3. herramienta o implementación reconocida;
4. evidencia empírica;
5. cálculo independiente.

Cuando las fuentes discrepen, no elijas una sin explicar el conflicto.

## 3.4. Reproducibilidad

Para cada fórmula o algoritmo registra:

- variables;
- unidades;
- dominio;
- orden de operaciones;
- redondeos;
- truncamientos;
- caps;
- floors;
- multiplicadores;
- condiciones;
- valores por defecto;
- excepciones;
- ejemplo verificable;
- test vector;
- fuente.

## 3.5. No usar falsa precisión

Distingue:

- valor exacto;
- estimación;
- rango;
- aproximación;
- tasa observada;
- posterior o intervalo;
- regla teórica;
- dato no verificable.

No inventes volúmenes ni decimales.

---

# 4. Cobertura temática obligatoria

Investiga todos los dominios siguientes. Puedes agregar otros si encuentras valor real.

---

## 4.1. Estadísticas base, niveles, IV y CP

Investiga:

- base stats;
- transformación desde juegos principales, cuando corresponda;
- Attack, Defense y Stamina;
- niveles y medios niveles;
- CP Multiplier;
- fórmula de CP;
- fórmula de HP;
- redondeos y floors;
- IV;
- appraisal;
- pisos de IV por método;
- distribución de IV;
- probabilidad de hundos;
- probabilidad de combinaciones específicas;
- stat product;
- eficiencia marginal por nivel;
- breakpoints asociados a nivel;
- nivel efectivo;
- Best Buddy boost;
- cambios históricos de fórmulas.

Calculadoras candidatas:

- CP;
- HP;
- nivel aproximado;
- IV posibles;
- evolución;
- power-up;
- probabilidad de hundo;
- stat product;
- comparación de dos ejemplares;
- costo marginal por nivel.

---

## 4.2. Intercambios, amistad y Pokémon Lucky

Investiga:

- reroll de IV;
- pisos de IV por amistad;
- independencia o dependencia entre stats;
- distribución teórica;
- probabilidad de hundo;
- Lucky Trades;
- Lucky Friends;
- intercambios Lucky garantizados;
- efecto de antigüedad;
- límites diarios;
- intercambios especiales;
- costos de polvo;
- restricciones;
- cambios históricos;
- datos oficiales frente a investigación comunitaria;
- posibles anomalías o desacuerdos.

Calculadoras candidatas:

- hundo odds;
- probabilidad acumulada;
- número de intercambios para alcanzar una confianza;
- comparación normal frente a Lucky;
- costo esperado;
- distribución de resultados;
- prueba de compatibilidad de muestra;
- calculadora de tamaño de muestra;
- simulador Monte Carlo;
- valor esperado de una sesión.

---

## 4.3. Captura y huida

Investiga:

- Base Capture Rate;
- Base Flee Rate;
- Catch Probability;
- ball modifier;
- berry modifier;
- throw modifier;
- curveball;
- medallas por tipo;
- nivel del Pokémon;
- CP Multiplier;
- clima;
- encuentros de raid;
- Premier Balls;
- encuentros garantizados o especiales;
- critical catch;
- diferencias entre wild, raid, research, reward y otros métodos;
- redondeos;
- cambios históricos;
- probabilidades por lanzamiento y acumuladas.

Calculadoras candidatas:

- probabilidad de captura por lanzamiento;
- probabilidad de captura antes de agotar bolas;
- comparación de berries y balls;
- expected balls;
- riesgo de huida;
- estrategia óptima bajo costos definidos;
- impacto de medallas;
- valor esperado de Golden Razz;
- comparación de métodos de encuentro.

---

## 4.4. Rareza, shiny odds y encounters

Investiga:

- shiny odds por método;
- tasas permanentes y temporales;
- especies con boosted rate;
- raids;
- huevos;
- investigación;
- Community Day;
- Raid Day;
- eventos;
- shadow;
- Legendary;
- regionales;
- formas;
- límites de observabilidad;
- fuentes oficiales frente a muestras comunitarias;
- sesgo de reporte;
- cambios silenciosos.

Calculadoras candidatas:

- probabilidad acumulada de shiny;
- intentos para una confianza objetivo;
- probabilidad de cero;
- comparación entre métodos;
- costo esperado;
- poder estadístico de una muestra;
- compatibilidad entre tasa observada y tasa supuesta.

---

## 4.5. PvE: daño, raids y gimnasios

Investiga exhaustivamente:

### Fórmula de daño

- Attack efectivo;
- Defense efectivo;
- base power;
- STAB;
- type effectiveness;
- weather boost;
- friendship boost;
- Mega/Primal boost;
- Shadow bonus;
- Party Power;
- raid-specific modifiers;
- floors y redondeos;
- dodging;
- boss move timing;
- energy;
- fast y charged moves;
- duración;
- cooldown;
- daño por ventana;
- cambios históricos.

### Métricas

- DPS;
- TDO;
- DPS³ × TDO o Equivalent Rating;
- ER;
- TTW;
- deaths;
- estimator;
- bulk;
- breakpoints;
- bulkpoints;
- cycle DPS;
- weave DPS;
- energy waste;
- overkill;
- dodge DPS;
- relobby cost;
- team DPS;
- group scaling;
- raid timer effects;
- lag o discretización cuando corresponda.

### Stats de raid boss

- tier;
- HP;
- CPM;
- Attack;
- Defense;
- enrage u otros estados especiales;
- weather;
- friendship;
- Mega boosts;
- party size;
- remote damage modifiers;
- event modifiers.

### Decisiones

- mejor counter;
- mejor equipo;
- tiempo estimado;
- posibilidad de solo/duo/trio;
- cantidad mínima de jugadores;
- cuándo dodging mejora el resultado;
- Shadow frente a normal;
- Mega frente a daño puro;
- DPS frente a TDO;
- costo de inversión;
- mejora marginal por nivel.

Calculadoras candidatas:

- damage;
- move cycle;
- DPS;
- TDO;
- ER;
- TTW;
- breakpoint;
- bulkpoint;
- team simulator;
- raid estimator;
- costo por mejora de DPS;
- optimizador bajo presupuesto;
- comparación de equipos;
- comparación con y sin dodge.

---

## 4.6. PvP y GO Battle League

Investiga:

- fórmula de daño PvP;
- turns;
- durations;
- DPT;
- EPT;
- DPE;
- energy;
- CMP;
- Attack real;
- breakpoints;
- bulkpoints;
- stat product;
- rank de IV;
- caps de CP;
- buffs y debuffs;
- probabilities;
- shields;
- baiting;
- switch timer;
- fast move timing;
- charged move timing;
- nuevas reglas vigentes;
- diferencias entre ligas;
- copas;
- cambios de balance;
- team composition;
- coverage;
- consistency;
- safety;
- bulk;
- lead/safe swap/closer;
- algoritmos usados por simuladores existentes.

Distingue cuidadosamente:

- cálculo determinista;
- simulación;
- heurística;
- métrica subjetiva;
- resultado dependiente del comportamiento del rival.

Calculadoras candidatas:

- rank de IV;
- stat product;
- CMP;
- breakpoint;
- bulkpoint;
- move counts;
- energy;
- matchup simplificado;
- costo para construir;
- optimizador por presupuesto;
- comparación de ejemplares;
- equipo por inventario;
- matriz de cobertura;
- sensibilidad a IV.

No propongas copiar ni extraer ilegalmente código de herramientas existentes. Investiga implementaciones abiertas y documentación pública.

---

## 4.7. Max Battles, Dynamax y Gigantamax

Investiga:

- Max Moves;
- niveles;
- costo;
- Max Particles;
- Max Attack;
- Max Guard;
- Max Spirit;
- generación de energía o medidor;
- daño;
- shields;
- healing;
- team roles;
- Power Spots;
- boss stats;
- fases;
- límites;
- estrategia;
- diferencias entre Dynamax y Gigantamax;
- efectividad;
- breakpoints;
- valor marginal de mejoras;
- lagunas de conocimiento.

Este dominio puede estar menos documentado. Clasifica claramente lo conocido, inferido y desconocido.

Calculadoras candidatas:

- costo de subir Max Moves;
- daño estimado;
- supervivencia;
- optimización de roles;
- partículas necesarias;
- comparación de inversión;
- simulador por equipo;
- estrategia por boss.

---

## 4.8. Movimientos y eficiencia

Investiga:

- fast moves;
- charged moves;
- legacy moves;
- Elite TMs;
- exclusive moves;
- move availability;
- duración;
- energía;
- power;
- STAB;
- type;
- PvE y PvP separados;
- DPT;
- EPT;
- DPE;
- cycle DPS;
- move synergy;
- overkill;
- breakpoints;
- cambios históricos;
- nerfs y buffs;
- ventana de evolución.

Calculadoras candidatas:

- move comparison;
- mejor moveset;
- mejora marginal;
- Elite TM value;
- esperar o usar TM;
- disponibilidad histórica;
- probabilidad o cadencia de retorno, dejando claro cuando sea una estimación;
- costo de oportunidad.

---

## 4.9. Economía de recursos

Investiga:

- Stardust;
- Candy;
- Candy XL;
- Rare Candy;
- Rare Candy XL;
- Mega Energy;
- Primal Energy;
- Max Particles;
- TMs;
- Elite TMs;
- incubators;
- raid passes;
- purification;
- second charged move;
- evolution;
- power-up;
- trading costs;
- opportunity cost;
- fuentes y tasas de obtención;
- restricciones temporales;
- límites diarios y semanales.

Calculadoras candidatas:

- costo total de power-up;
- costo marginal;
- nivel óptimo bajo presupuesto;
- comparar dos inversiones;
- Shadow frente a normal;
- purificar o no;
- second move ROI;
- Elite TM ROI;
- costo por punto de DPS;
- costo por supervivencia;
- budget optimizer;
- plan de recursos.

No asumas que todos los recursos tienen un valor monetario objetivo. Permite pesos configurables.

---

## 4.10. Huevos, incubación y expected value

Investiga:

- egg pools;
- tiers;
- probabilidades publicadas o no publicadas;
- distancia;
- incubators;
- Super Incubators;
- Adventure Sync;
- eventos;
- shiny odds;
- IV floors;
- candy;
- stardust;
- valor esperado;
- sesgos;
- falta de transparencia;
- cambios de pool.

Calculadoras candidatas:

- costo esperado;
- distancia esperada;
- probabilidad de obtener objetivo;
- incubators necesarios;
- comparación de incubadores;
- valor esperado parametrizable;
- análisis de evento;
- tamaño de muestra para estimar tasas.

---

## 4.11. Mega, Primal, Shadow y formas especiales

Investiga:

- bonuses;
- damage boost;
- same-type bonus;
- candy bonus;
- XL candy bonus;
- Mega level;
- cooldown;
- energy cost;
- Primal boosts;
- Shadow attack/defense trade-off;
- purification;
- Apex u otras formas;
- fusion o mecánicas nuevas;
- cambios vigentes.

Calculadoras candidatas:

- Mega level progression;
- energy break-even;
- candy/XL expected benefit;
- Shadow vs normal;
- purify decision;
- raid team boost;
- costo de oportunidad.

---

## 4.12. Eventos y valor esperado

Investiga cómo cuantificar eventos sin fingir una utilidad universal.

Considera:

- spawn quality;
- shiny odds;
- XL availability;
- stardust;
- candy;
- XP;
- exclusive moves;
- research;
- raids;
- eggs;
- tiempo;
- costo;
- oportunidad;
- objetivos personales;
- rareza futura;
- reemplazabilidad.

Diseña un modelo parametrizable, no una puntuación absoluta única.

Calculadoras candidatas:

- event value;
- prioridad según objetivos;
- tiempo necesario;
- recursos esperados;
- comparación de eventos;
- qué vale la pena para PvE, PvP, colección o progreso.

---

## 4.13. Progresión y optimización general

Investiga:

- XP;
- level requirements;
- medals;
- friendship XP;
- raids;
- catches;
- evolution XP;
- Lucky Eggs;
- routes;
- research;
- party play;
- daily/weekly systems;
- limits;
- optimal timing;
- diminishing returns.

Calculadoras candidatas:

- tiempo a nivel;
- XP por estrategia;
- Lucky Egg optimization;
- costo por XP;
- plan semanal;
- comparación de actividades;
- objetivos de medallas.

---

## 4.14. Calidad estadística y experimentación comunitaria

Investiga y especifica métodos apropiados para:

- tasas binomiales;
- distribuciones multinomiales;
- uniformidad;
- independencia;
- intervalos de confianza;
- Wilson;
- Clopper–Pearson;
- métodos bayesianos simples;
- pruebas exactas;
- chi-cuadrado;
- Monte Carlo;
- bootstrap;
- power analysis;
- sequential testing;
- multiple comparisons;
- change-point detection;
- A/B natural experiments;
- sesgo de selección;
- sesgo de supervivencia;
- reporting bias;
- duplicados;
- fraude;
- datos incompletos;
- estratificación;
- metadatos;
- reproducibilidad.

No conviertas el sitio en un manual académico. Determina qué métodos son apropiados para cada calculadora y experimento.

---

# 5. Auditoría de herramientas existentes

Investiga herramientas, calculadoras, APIs, datasets y repositorios existentes.

Incluye:

- herramientas globales;
- herramientas en español;
- herramientas en portugués;
- aplicaciones;
- sitios web;
- repositorios open source;
- datasets;
- hojas de cálculo;
- bots;
- calculadoras de nicho;
- proyectos abandonados;
- implementaciones académicas o comunitarias.

Para cada solución registra:

- nombre;
- URL;
- idioma;
- dominio cubierto;
- fórmulas;
- fuentes;
- metodología;
- código abierto o cerrado;
- licencia;
- fecha de actualización;
- fortalezas;
- debilidades;
- discrepancias;
- posibilidad legal de reutilización;
- posibilidad de validación independiente;
- valor diferencial que aún falta.

No confundas popularidad con corrección.

No reproduzcas código propietario ni eludas restricciones de acceso.

---

# 6. Jerarquía de fuentes

Prioriza:

1. documentación oficial;
2. anuncios oficiales;
3. artículos técnicos oficiales;
4. repositorios y datasets abiertos con procedencia;
5. investigaciones comunitarias metodológicamente sólidas;
6. herramientas reconocidas con documentación;
7. discusiones técnicas con evidencia;
8. wikis;
9. publicaciones individuales como señal exploratoria.

Para cada fuente asigna:

- autoridad;
- actualidad;
- transparencia metodológica;
- reproducibilidad;
- independencia;
- cobertura;
- riesgo de obsolescencia.

Usa una escala de confianza:

- alta;
- media;
- baja;
- no verificable.

---

# 7. Registro canónico de fórmulas

Construye una tabla maestra con una fila por fórmula o algoritmo.

Columnas obligatorias:

- `formula_id`;
- nombre;
- dominio;
- propósito;
- fórmula;
- pseudocódigo;
- variables;
- unidades;
- inputs;
- outputs;
- rango;
- floors;
- caps;
- redondeos;
- condiciones;
- excepciones;
- rule set;
- fecha efectiva;
- estado;
- fuente primaria;
- fuentes secundarias;
- confianza;
- discrepancias;
- test vector;
- resultado esperado;
- calculadoras dependientes;
- riesgo de obsolescencia;
- notas de implementación.

No uses imágenes para fórmulas cuando puedan representarse como texto o LaTeX.

---

# 8. Registro canónico de datos

Construye un inventario con:

- `dataset_id`;
- nombre;
- dominio;
- variables;
- granularidad;
- cobertura temporal;
- cobertura geográfica;
- origen;
- método de obtención;
- licencia;
- formato;
- frecuencia de actualización;
- calidad;
- campos faltantes;
- sesgos;
- ToS;
- restricciones;
- uso permitido;
- calculadoras dependientes;
- mecanismo de validación;
- alternativa si desaparece.

Incluye datos necesarios para:

- Pokémon;
- formas;
- stats;
- tipos;
- moves;
- niveles;
- CPM;
- costos;
- encounters;
- raids;
- PvP;
- Max Battles;
- eventos;
- fuentes;
- rule sets.

---

# 9. Backlog de calculadoras

Genera entre 30 y 60 calculadoras candidatas, sin inflar la lista con variaciones triviales.

Para cada una incluye:

- `calculator_id`;
- nombre;
- pregunta que responde;
- usuario;
- frecuencia;
- inputs;
- outputs;
- fórmula;
- datasets;
- fuente;
- confianza;
- dificultad;
- valor;
- recurrencia;
- SEO;
- capacidad de compartir;
- personalización;
- riesgo;
- dependencia de datos;
- evergreen;
- recomendación:
  - MVP;
  - fase 2;
  - fase 3;
  - descartar;
  - investigar.

Prioriza mediante estos pesos:

| Dimensión                   | Peso |
| --------------------------- | ---: |
| Utilidad práctica           | 20 % |
| Demanda probable            | 15 % |
| Evergreen                   | 15 % |
| Reutilización global        | 10 % |
| Disponibilidad de datos     | 10 % |
| Confianza matemática        | 10 % |
| Diferenciación              | 10 % |
| Facilidad de implementación |  5 % |
| Potencial de recurrencia    |  5 % |

Incluye intervalo de confianza cualitativo y criterios de veto.

---

# 10. Brechas y contradicciones

Identifica:

- fórmulas con versiones incompatibles;
- diferencias entre herramientas;
- tasas aceptadas sin fuente robusta;
- cambios históricos no documentados;
- mecánicas con evidencia insuficiente;
- reglas oficiales ambiguas;
- datos que no pueden obtenerse legalmente;
- modelos populares con supuestos ocultos;
- métricas mal interpretadas;
- calculadoras que ofrecen falsa precisión;
- dominios apropiados para investigación comunitaria.

Para cada brecha incluye:

- afirmación;
- fuentes;
- contradicción;
- impacto;
- nivel de riesgo;
- investigación necesaria;
- tamaño de muestra aproximado;
- metadatos requeridos;
- criterio de resolución.

---

# 11. Seguridad, legalidad y propiedad intelectual

Evalúa:

- Términos de Servicio;
- APIs privadas;
- scraping;
- ingeniería inversa;
- datamining;
- licencias;
- uso de nombres;
- imágenes;
- sprites;
- logos;
- datasets de terceros;
- repositorios open source;
- atribución;
- redistribución;
- fair use;
- datasets comunitarios.

No afirmes certeza legal cuando no exista.

Clasifica cada fuente o dato como:

- reutilizable;
- reutilizable con atribución;
- solo referenciable;
- requiere permiso;
- incierto;
- no recomendable.

La plataforma no debe depender de:

- credenciales del jugador;
- automatización del juego;
- manipulación de ubicación;
- acceso no autorizado;
- extracción de datos personales;
- violación de ToS.

---

# 12. Entregables

## 12.1. Resumen ejecutivo

Incluye:

- dominios más valiosos;
- fuentes más confiables;
- principales riesgos;
- primeras calculadoras;
- principales brechas;
- áreas que requieren investigación primaria.

## 12.2. Taxonomía completa

Mapa jerárquico de mecánicas, fórmulas, datos, calculadoras y decisiones.

## 12.3. Matriz de cobertura

Por:

- dominio;
- mecánica;
- tipo de evidencia;
- idioma;
- fuente;
- vigencia;
- confianza;
- disponibilidad de datos.

## 12.4. Auditoría de herramientas

Tabla comparativa.

## 12.5. Registro de fórmulas

Según el esquema definido.

## 12.6. Registro de datasets

Según el esquema definido.

## 12.7. Backlog de calculadoras

Priorizado.

## 12.8. Top 10 de módulos iniciales

Para cada uno:

- problema;
- audiencia;
- fórmulas;
- fuentes;
- datos;
- dificultad;
- valor;
- riesgo;
- razón para priorizar;
- dependencias.

## 12.9. Discrepancias

Lista adversarial y plan de resolución.

## 12.10. Experimentos comunitarios

Entre 10 y 20 experimentos candidatos:

- hipótesis;
- diseño;
- variables;
- muestra;
- sesgos;
- análisis;
- riesgo;
- valor.

## 12.11. Data model conceptual

Entidades y relaciones necesarias.

## 12.12. API conceptual

Endpoints o contratos internos necesarios para:

- formulas;
- rule sets;
- calculators;
- datasets;
- experiments;
- sources;
- analyses;
- decisions.

## 12.13. Test vectors

Casos verificables para las fórmulas más importantes.

## 12.14. Research debt

Lista explícita de asuntos no resueltos.

## 12.15. Paquete para investigaciones de dominio

Para cada dominio prioritario, incluye:

- preguntas;
- fuentes iniciales;
- afirmaciones críticas;
- discrepancias;
- fórmulas;
- datos;
- test vectors;
- tareas del siguiente investigador.

---

# 13. Artefactos estructurados

Cuando la plataforma lo permita, entrega:

- `research_report.md`;
- `source_registry.csv`;
- `formula_registry.csv`;
- `dataset_registry.csv`;
- `calculator_backlog.csv`;
- `tool_audit.csv`;
- `discrepancy_log.csv`;
- `experiment_backlog.csv`;
- `test_vectors.json`;
- `domain_research_packets/`.

Si no puedes producir archivos, entrega tablas completas y bloques JSON válidos.

No omitas contenido importante para ahorrar espacio. Si el volumen supera la capacidad de un único informe, entrega primero los artefactos estructurados y continúa por secciones.

---

# 14. Criterios de calidad

El informe se considera insuficiente si:

- enumera fórmulas sin fuentes;
- mezcla PvE y PvP;
- no documenta redondeos;
- trata tasas comunitarias como oficiales;
- no registra fecha;
- depende de una sola herramienta;
- no identifica discrepancias;
- no produce test vectors;
- no prioriza;
- no distingue exacto de estimado;
- ignora ToS y licencias;
- no incluye datos necesarios para implementación;
- se limita a artículos narrativos;
- no identifica investigaciones empíricas.

---

# 15. Regla de cierre

No selecciones un producto completo ni diseñes todavía toda la interfaz.

La conclusión debe responder:

1. qué dominios investigar primero;
2. qué fórmulas pueden implementarse con confianza;
3. qué fuentes deben convertirse en canónicas;
4. qué calculadoras ofrecen más valor;
5. qué datos faltan;
6. qué afirmaciones requieren experimentos;
7. qué debe pasar a una investigación de dominio.

---

# PROMPT 2 — VERIFICACIÓN E IMPLEMENTACIÓN DE UN DOMINIO

## Instrucción de uso

Ejecuta este prompt en una conversación nueva.

Adjunta:

1. el informe completo del Prompt 1;
2. los registros de fuentes, fórmulas y datasets;
3. el paquete del dominio elegido.

Sustituye:

- `[DOMINIO]`
- `[OBJETIVO]`

Ejemplos:

- `[DOMINIO] = PvE, raids, DPS, TDO y breakpoints`
- `[OBJETIVO] = producir una especificación canónica y testeable para implementar calculadoras PvE`

---

## Rol

Actúa como:

- investigador técnico principal;
- matemático aplicado;
- analista estadístico;
- revisor de código y algoritmos;
- data engineer;
- especialista en validación;
- auditor adversarial.

Usa el informe adjunto como mapa inicial, no como fuente confiable.

Debes verificar de forma independiente cada afirmación crítica.

---

## Dominio

**[DOMINIO]**

## Objetivo

**[OBJETIVO]**

---

# 1. Misión

Producir una especificación matemática, estadística y de datos:

- completa;
- vigente;
- trazable;
- reproducible;
- implementable;
- testeable;
- resistente a errores;
- explícita sobre incertidumbre.

El resultado será usado directamente por un agente de código.

No entregues una explicación superficial ni una simple lista de enlaces.

---

# 2. Verificación adversarial

Para cada fórmula, regla, tasa o algoritmo del informe inicial:

- confirma;
- confirma parcialmente;
- refuta;
- marca como desactualizado;
- marca como no verificable.

Busca:

- fuentes omitidas;
- versiones históricas;
- cambios recientes;
- discrepancias;
- rounding distinto;
- excepciones;
- casos límite;
- supuestos ocultos;
- diferencias entre herramientas;
- errores repetidos por la comunidad.

No uses el informe adjunto como prueba.

---

# 3. Fuente canónica

Para cada elemento determina:

- mejor fuente primaria;
- mejor fuente secundaria;
- mejor implementación verificable;
- mejor evidencia empírica;
- licencia;
- fecha;
- confianza.

Si ninguna fuente es suficientemente sólida, decláralo.

---

# 4. Especificación matemática

Para cada fórmula incluye:

- `formula_id`;
- nombre;
- objetivo;
- expresión LaTeX;
- pseudocódigo;
- variables;
- tipos;
- unidades;
- dominios;
- valores permitidos;
- orden;
- rounding;
- floors;
- caps;
- condiciones;
- excepciones;
- fechas efectivas;
- rule sets;
- fuente;
- confianza;
- discrepancias;
- ejemplo;
- test vector;
- resultado esperado.

Explica cualquier diferencia entre:

- fórmula matemática ideal;
- implementación del juego;
- aproximación de calculadoras;
- simulación.

---

# 5. Especificación estadística

Cuando el dominio incluya tasas o datos empíricos, define:

- estimadores;
- intervalos;
- pruebas;
- tamaño de muestra;
- power;
- supuestos;
- estratificación;
- outliers;
- múltiples comparaciones;
- métodos exactos;
- simulación;
- comunicación al usuario.

Evita:

- `p-value` aislado;
- causalidad injustificada;
- falsa precisión;
- ignorar sesgo de selección;
- mezclar rule sets.

---

# 6. Especificación de datos

Produce:

- entidades;
- campos;
- tipos;
- constraints;
- índices;
- claves;
- versionado;
- provenance;
- fechas;
- unidades;
- diccionario;
- fuentes;
- licencia;
- actualización;
- validaciones.

Distingue:

- datos estáticos;
- datos temporales;
- datos derivados;
- datos del usuario;
- datos comunitarios;
- resultados calculados.

---

# 7. Calculadoras

Para cada calculadora del dominio:

- pregunta;
- usuario;
- inputs;
- defaults;
- outputs;
- explicación;
- fórmulas;
- datos;
- errores;
- casos límite;
- compartir URL;
- reproducibilidad;
- tests;
- complejidad;
- prioridad.

Entrega una especificación de interfaz independiente del framework.

---

# 8. Motor de decisiones

Define reglas prácticas derivadas de los cálculos.

Cada recomendación debe incluir:

- condición;
- evidencia;
- resultado;
- explicación;
- confianza;
- alternativas;
- riesgo;
- limitación;
- versión;
- test.

No uses LLM para producir la decisión numérica.

---

# 9. Comparación con herramientas existentes

Compara los resultados con al menos tres implementaciones independientes, cuando existan.

Para cada discrepancia:

- reproduce el caso;
- muestra inputs;
- muestra outputs;
- identifica causa;
- decide qué modelo adoptar;
- documenta por qué.

No copies código propietario.

---

# 10. Test suite de referencia

Entrega:

- unit tests;
- property-based tests;
- regression tests;
- edge cases;
- historical cases;
- golden test vectors;
- cross-tool comparison;
- tolerancias;
- expected failures.

Los test vectors deben ser manualmente auditables.

---

# 11. Riesgos

Incluye:

- datos;
- obsolescencia;
- rounding;
- rendimiento;
- sesgo;
- legalidad;
- licencias;
- experiencia de usuario;
- interpretación;
- mantenimiento.

Define mitigaciones.

---

# 12. Entregables

1. Informe técnico.
2. Registro verificado de fuentes.
3. Registro verificado de fórmulas.
4. Diccionario de datos.
5. Especificación de calculadoras.
6. Motor de decisiones.
7. Test vectors.
8. Discrepancy log.
9. Changelog histórico.
10. Lista de asuntos no resueltos.
11. Recomendación de implementación.
12. Contratos JSON o pseudocódigo.

Cuando sea posible, exporta:

- `domain_report.md`;
- `formulas.yaml`;
- `sources.csv`;
- `datasets.csv`;
- `calculators.yaml`;
- `test_vectors.json`;
- `decision_rules.yaml`;
- `discrepancies.csv`.

---

# 13. Criterio de finalización

El dominio se considera listo para implementación solo cuando:

- las fórmulas críticas tienen fuentes;
- los redondeos están documentados;
- los test vectors pasan;
- las discrepancias están resueltas o etiquetadas;
- los datos tienen licencia y procedencia;
- las calculadoras tienen contratos;
- la incertidumbre está explícita;
- existe una estrategia de actualización;
- los riesgos legales son aceptables.

Si no se cumplen, no declares el dominio “completo”. Entrega el research debt y los experimentos necesarios.
