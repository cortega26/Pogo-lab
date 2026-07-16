# ADR-0005 — Separación de datos privados/públicos, consentimiento y anonimización

- **Estado:** Aceptada
- **Fecha:** 2026-07-16
- **Relacionadas:** `plan.md` §E, §4.8, §10, §19-#7, §19-#8

## Contexto

Los usuarios registran observaciones privadas; el producto también publica un **dataset comunitario**. Mezclar
ambos, o construir el dataset público como una vista sobre datos vivos, arriesga fugas de PII e inestabilidad, y
choca con el derecho a **revocar** la contribución.

## Decisión

- Las `TradeObservation` son **privadas por defecto**, propiedad del usuario.
- La contribución es **opt-in explícito** vía `DataContributionConsent` (con versión del texto, `granted_at`/
  `revoked_at`, auditado y **revocable**).
- El dataset público es un **snapshot anonimizado e inmutable** (`DatasetVersion`), **no** una vista viva: excluye
  `notes`, sin nombre de entrenador ni ubicación precisa (solo **país agregado**), con `dedup_hash` y un
  **umbral mínimo** antes de publicar.
- La **revocación** excluye al usuario de **builds futuros**; las versiones ya publicadas son inmutables y documentan
  su estado de consentimiento.

## Alternativas consideradas

- **Vista/consulta en vivo sobre las observaciones.** Siempre "fresca", pero inestable, difícil de versionar y
  peligrosa para la privacidad; la revocación no puede reescribir el pasado publicado de forma coherente.
- **Contribución por defecto (opt-out).** Más datos, pero éticamente y legalmente frágil; contradice la minimización.

## Consecuencias

- **Positivas:** privacidad por diseño; datasets versionados y reproducibles; revocación coherente; se puede advertir
  del **sesgo de selección** (no es muestra aleatoria).
- **Negativas / costes:** pipeline de build/anonimización y almacenamiento de snapshots.
- **Mitigaciones:** el build es un management command idempotente; el umbral mínimo evita publicar ruido.

## Reversibilidad

Media-baja: la postura de privacidad es un compromiso con el usuario. Ajustar umbrales o campos agregados es
reversible; volver a opt-out no lo es sin romper la confianza.
