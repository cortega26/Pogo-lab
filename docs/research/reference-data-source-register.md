# Registro de fuentes de datos de referencia

**Estado:** BLOCKED — ninguna fuente está aprobada para adquisición,
almacenamiento o distribución.
**Última actualización:** 2026-07-26.

Este registro evalúa candidatos sin descargar, copiar ni publicar contenido de
terceros. `approved` exige licencia/ToS comprobados, atribución definida,
input inmutable con checksum y aprobación escrita del owner. La presencia de
una fila no autoriza una integración.

| Fuente candidata | URL | Procedencia | Fecha de revisión | Licencia/ToS revisados | ¿Almacenamiento/distribución? | Atribución | Estabilidad | Input inmutable | Responsable | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|
| Game Master publicado por PokeMiners (DAT001) | https://github.com/PokeMiners/game_masters | datamining comunitario publicado | Pendiente | Pendiente de revisión específica | No verificado | Pendiente | Cambios frecuentes; no verificada | Posible por commit/tag + checksum; no verificado | Owner de producto + responsable legal | `blocked` |
| Datos PvP publicados por PvPoke (DAT004) | https://github.com/pvpoke/pvpoke | comunidad / FOSS | Pendiente | Pendiente de confirmar alcance de licencia y datos incluidos | No verificado | Pendiente | Estacional; no verificada | Posible por release/commit + checksum; no verificado | Owner de producto + responsable legal | `blocked` |
| Anuncios oficiales para roster de raids (DAT005) | https://pokemongolive.com/ | oficial | Pendiente | Pendiente de revisión de ToS y uso derivado | No verificado | Pendiente | Por evento; no verificada | Requiere captura fechada y checksum; no verificado | Owner de producto + responsable legal | `blocked` |

## Condiciones de aprobación

Para cambiar una fila a `approved`, la persona responsable debe registrar:

1. URL específica revisada, fecha, licencia/ToS y compatibilidad con el uso
   previsto (almacenamiento local, cálculo, atribución y distribución).
2. La clase de procedencia y atribución visible exigida.
3. Un input fijado por release, commit o archivo con checksum; nunca `latest`.
4. La autorización escrita del owner y un responsable de mantenimiento.
5. Cumplimiento de la política de datos, en particular que no se redistribuye
   raw protegido ni se usan APIs privadas o credenciales.

Hasta cumplir todas las condiciones no se descarga, ingiere, redistribuye ni
usa ninguna fuente como verdad de runtime.
