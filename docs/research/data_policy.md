# Política de datos — adquisición, fair use y procedencia

**Estado:** vigente · **Última revisión:** 2026-07-17 · **Ámbito:** todo dato externo que ingrese a Pogo-lab (ETL, datasets, fuentes de fórmulas, rosters).

## 1. Principio

Buena parte de la información de Pokémon GO ya es pública pero está dispersa, sin normalizar y sin procedencia. Ante la falta de datos oficiales de Niantic/Scopely, el rol de Pogo-lab es **curar, normalizar y procesar (ETL) información ya pública** y los aportes voluntarios de los usuarios, para derivar cálculos y análisis útiles **con procedencia explícita**.

Scraping y APIs de terceros **están permitidos** siempre que no sean abusivos. Esta política define esa frontera con reglas verificables, no a criterio caso por caso.

## 2. Lista verde — permitido sin condiciones especiales

- Consumir datasets/repos que la comunidad **publica abiertamente para reutilización** (p. ej. PokeMiners, PvPoke, archivos de The Silph Road).
- Anuncios y páginas oficiales de acceso público (Niantic/Scopely).
- Aportes voluntarios de los propios usuarios de la plataforma (con consentimiento, según el modelo de dataset comunitario ya existente).
- Cálculo e inferencia propios sobre cualquiera de lo anterior.

## 3. Lista amarilla — permitido si se cumplen TODAS las condiciones

Aplica a **scraping de sitios públicos** y **APIs de terceros**. Se permite solo si **todas** estas condiciones se cumplen (son verificables):

1. **robots.txt:** la ruta objetivo no está prohibida en `robots.txt` del sitio.
2. **ToS de la fuente:** el uso previsto no está prohibido por los Términos de Servicio de esa fuente (los del sitio/API de terceros, no solo los de Niantic).
3. **Rate-limit:** máximo **1 solicitud cada 2 s** por host por defecto (≤ 30 req/min); backoff exponencial ante `429`/`5xx`; nunca en paralelo agresivo contra un mismo host.
4. **Identificación:** `User-Agent` identificable y honesto (nombre del proyecto + URL de contacto). Nada de suplantar navegadores para ocultar el bot.
5. **Solo contenido público:** nada que requiera autenticación, pago o esté tras un muro de acceso.
6. **Caché, no martilleo:** se cachea el resultado y se re-consulta según la frecuencia real de cambio de la fuente (ver `update_frequency` del dataset), no en cada request de usuario.
7. **Atribución:** la fuente queda registrada como `SourceClaim`/entrada de procedencia y se atribuye en la UI cuando el dato se muestre.
8. **Solo derivados:** se publica/redistribuye el dato **normalizado o derivado con atribución**, nunca el volcado crudo de un tercero presentado como propio.

> Si una condición no se puede cumplir para una fuente concreta, esa fuente pasa a **lista roja** para ese uso.

## 4. Lista roja — nunca

- **Ingeniería inversa del cliente del juego** hecha por nosotros (extraer del binario/tráfico de la app). Consumir lo que la comunidad ya extrajo y publicó **sí** está permitido (lista verde).
- **Credenciales del jugador**, tokens de sesión o cualquier acceso a la cuenta de Niantic/Scopely.
- **Automatización o spoofing del juego** (bots, GPS falso, scanners de spawns/lobbies en tiempo real).
- **APIs privadas/no documentadas del juego** o de servicios que expongan estado en vivo del cliente.
- **Eludir controles de acceso**: autenticación, paywalls, CAPTCHAs, límites de tasa, o `robots.txt` cuando prohíbe la ruta.
- **Datos personales** de jugadores obtenidos sin consentimiento.
- **Redistribuir el dataset crudo de un tercero** como si fuera propio, o ignorar su licencia.

## 5. Obligaciones de procedencia (por cada dato que ingresa)

Alineado con la disciplina de procedencia del proyecto (procedencia separada, `SourceClaim` versionado):

- Clasificar la procedencia (oficial / datos públicos / datamining comunitario / investigación comunitaria / inferencia / hipótesis) — nunca presentar un dato comunitario como oficial.
- Registrar: fuente, URL, licencia, método de obtención, fecha de obtención y fecha de última verificación.
- Registrar el método de adquisición usado y contra qué reglas de la §3 se validó.

## 6. Checklist antes de añadir una fuente nueva

- [ ] ¿En qué lista cae (verde / amarilla / roja)? Si es roja, se descarta.
- [ ] Si es amarilla: ¿cumple **las 8** condiciones de la §3? (robots.txt, ToS, rate-limit, UA, solo público, caché, atribución, solo derivados).
- [ ] ¿Licencia identificada y compatible con el uso derivado con atribución?
- [ ] ¿Registrada como `SourceClaim`/entrada de procedencia con fecha y método?
- [ ] ¿Existe una fuente alternativa si esta desaparece? (`alternative_backup` en [dataset_registry.csv](dataset_registry.csv)).

## 7. Relación con otros documentos

- Barrera de contención general y taxonomía de procedencia: [investigacion.md](../investigacion.md) §3 y §11.
- Inventario de datasets y su procedencia/licencia: [dataset_registry.csv](dataset_registry.csv).
- Riesgos legales a nivel de estrategia: [research_report.md](research_report.md) §1.
