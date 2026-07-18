# Paquete de Investigación de Dominio: Huevos, Probabilidades Shiny y Muestreo

Este documento especifica las matemáticas y distribuciones necesarias para calcular las **probabilidades de eclosión, shiny acumulado y tamaño de muestra para auditorías comunitarias**.

## 1. Misión del Dominio
Proporcionar a los usuarios respuestas deterministas sobre:
- ¿Cuántos encuentros/huevos necesito realizar para asegurar al menos un Shiny con un 95% o 99% de confianza?
- ¿Cuál es el Valor Esperado ($EV$) de mis incubadoras en caramelos, polvos y especies deseadas en este evento?
- ¿La tasa observada por mi comunidad local difiere significativamente de la tasa teórica oficial o comunitaria?

## 2. Especificación Matemática

### Probabilidad Acumulada de Shiny (Distribución Geométrica)
La probabilidad de obtener al menos un shiny en $N$ encuentros independientes con una tasa constante de shiny $p$:

$$P(Shiny \ge 1) = 1 - (1 - p)^N$$

La probabilidad de no ver ninguno (sequía) es:

$$P(Shiny = 0) = (1 - p)^N$$

El número de encuentros $N$ requeridos para alcanzar un nivel de confianza deseado $C \in [0, 1)$ (ej. 95%):

$$N = \lceil \frac{\ln(1 - C)}{\ln(1 - p)} \rceil$$

### Tasas Shiny de Referencia (Comunidad)

| Método de Encuentro | Tasa Teórica ($p$) | Fracción Común |
|---|---|---|
| Salvaje Estándar | 0.00195 | 1/512 |
| Permaboost (ej. Gible, Scyther, Onix) | 0.01562 | 1/64 |
| Incursión Legendaria | 0.05000 | 1/20 |
| Incursión de Megas | 0.01562 | 1/64 |
| Día de la Comunidad | 0.04000 | 1/25 |
| Día de Incursiones | 0.10000 | 1/10 |
| Día de Investigación Limitada | 0.10000 | 1/10 |

### Valor Esperado de Eclosión de Huevos ($EV$)
Dado un pool de eclosión de huevo con especies $S = \{s_1, s_2, \dots, s_k\}$, con probabilidades de eclosión $P(s_i)$ y un valor de utilidad asignado por el usuario $U(s_i) \in [0, 10]$:

$$EV_{hatch} = \sum_{i=1}^k P(s_i) \times U(s_i)$$

Además, la cantidad esperada de caramelos por eclosión depende de la distancia del huevo:

| Huevo | Rango de Caramelos | Caramelo Promedio | Rango de Polvos |
|---|---|---|---|
| 2 km | 5 - 15 | 10 | 400 - 800 |
| 5 km / 7 km | 10 - 21 | 15.5 | 800 - 1600 |
| 10 km | 16 - 32 | 24 | 1600 - 3200 |
| 12 km (Extraño) | 16 - 32 | 24 | 3200 - 6400 |

### Intervalo de Confianza para Tasas de Shiny Observadas
Al auditar muestras comunitarias de tamaño $n$ con $x$ éxitos observados (rango de shiny $\hat{p} = x/n$):
- Por defecto, usar el **Intervalo de Confianza de Wilson score**:

$$\hat{p} \pm Z_{1-\alpha/2} \frac{\sqrt{\hat{p}(1-\hat{p})/n + Z_{1-\alpha/2}^2/(4n^2)}}{1 + Z_{1-\alpha/2}^2/n}$$

Donde $Z_{1-\alpha/2} = 1.96$ para un 95% de confianza. Evitar la aproximación normal de Wald cuando $x < 5$ o $n(1-p) < 5$.

## 3. Especificación de Datos Requeridos
- **Egg Pool Database:** DAT002 (`egg_tier`, `species_id`, `rarity_level_eggs`).
- **Shiny Rates Archive:** DAT003 (`species_id`, `rate_by_method`).

## 4. Test Vector de Referencia
**Encuentros para Shiny Legendario ($p = 1/20 = 0.05$) con 95% de confianza:**
- $C = 0.95$, $p = 0.05$.
- $N = \lceil \frac{\ln(1 - 0.95)}{\ln(1 - 0.05)} \rceil = \lceil \frac{-2.99573}{-0.05129} \rceil = \lceil 58.40 \rceil = 59$ encuentros.
- Si un usuario realiza 100 incursiones y no obtiene ningún shiny, la probabilidad de esa sequía es:
  $P(Shiny = 0) = (1 - 0.05)^{100} = 0.95^{100} \approx 0.0059 \approx 0.59\%$.

## 5. Tareas para el Siguiente Investigador
1. Crear el validador estadístico de muestras en `engine/stat_tests.py` usando Wilson score e intervalos Clopper-Pearson exactos.
2. Implementar la interfaz para valorar pools de huevos donde el usuario asigne pesos subjetivos a cada especie del pool.
