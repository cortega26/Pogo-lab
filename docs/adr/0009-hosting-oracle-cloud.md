# ADR-0009 — Hosting en Oracle Cloud Infrastructure (OCI)

- **Estado:** Aceptada
- **Fecha:** 2026-07-17
- **Relacionadas:** `plan.md` §P, §S8 · ADR-0001 · M7 PR-21

## Contexto

Pogo-lab necesita un entorno de producción accesible para la beta cerrada (M7). El plan original (§S8)
recomendaba un PaaS gestionado (Fly.io, Railway, Render) por defecto, con la decisión reversible antes de
M7. La especificación pide bajo costo operativo, simplicidad de infraestructura (sin microservicios ni
orquestadores adicionales) y un contenedor OCI portable.

El usuario ha decidido usar **Oracle Cloud Infrastructure** como proveedor, aprovechando su capa gratuita
generosa que cubre el 100% de las necesidades del MVP sin coste mensual.

## Decisión

**Oracle Cloud Infrastructure (OCI)** — un VPS ARM Ampere A1 (4 OCPU, 24 GB RAM, 200 GB bloque) en la
capa siempre gratuita, con **Docker Compose** para orquestar Django + PostgreSQL en la misma instancia.
Sin servicios administrados de pago en el MVP.

## Alternativas consideradas

- **Fly.io / Railway / Render (PaaS).** Despliegue más simple (git push), pero: (1) el costo crece con el
  tráfico incluso en beta; (2) la capa gratuita de OCI es 4 OCPU × 24 GB — órdenes de magnitud más
  generosa que cualquier PaaS; (3) el contenedor OCI de Django ya es portable a cualquier VPS/PaaS — no
  hay lock-in con OCI. Si OCI resultara problemático, migrar a Fly.io es un cambio de destino en el
  `deploy.yml`, no de arquitectura.
- **VPS tradicional (Hetzner, DigitalOcean).** Más baratos que PaaS en $/mes, pero OCI gratuita los
  iguala a coste cero indefinidamente.

## Consecuencias

- **Positivas:** Coste = 0 €/mes para el MVP completo (cómputo + almacenamiento + transferencia dentro
  de los límites gratuitos). Suficiente para beta + crecimiento inicial. Docker Compose mantiene la misma
  experiencia de desarrollo (compose.local vs compose.prod). Sin dependencia de servicios propietarios de
  OCI — solo se usa la VM.
- **Negativas / costes:** Requiere administración manual de la VM (actualizaciones de SO, firewall,
  reinicios). Sin balanceo de carga ni alta disponibilidad automática (innecesario en MVP). La región más
  cercana al público objetivo (Europa/LATAM) puede no estar disponible en la capa gratuita — elegir la
  más próxima.
- **Mitigaciones:** Documentar procedimiento de **backup + restore** y **actualización del SO** en el
  README de infraestructura. Automatizar el despliegue vía GitHub Actions + SSH (`deploy.yml`).
  Monitoreo básico con `/healthz` + alerta por correo si el servicio cae. Si el tráfico supera la
  capacidad de la VM gratuita, migrar a PaaS es trivial (el `Dockerfile` es portable).

## Reversibilidad

Alta. El `Dockerfile` y `compose.prod.yaml` son estándar; la aplicación no usa ningún servicio nativo de
OCI. Migrar a Fly.io, Railway, Render o cualquier VPS requiere solo: (1) cambiar el target en `deploy.yml`,
(2) apuntar `DATABASE_URL` a la nueva instancia de Postgres, (3) restaurar el backup más reciente. Coste
estimado de migración: < 2 horas.
