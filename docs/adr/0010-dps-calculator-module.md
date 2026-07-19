# ADR-0010: Módulo DPS/TDO para raids PvE

- **Fecha**: 2026-07-18
- **Contexto**: El MVP (M0–M6) cubría intercambios/IV/Lucky. Tras M6,
  se incorporó una calculadora de DPS/TDO (Damage Per Second / Total
  Damage Output) para raids PvE como primera expansión del roadmap
  Fase 2 (Ola A). Se decidió implementarla sin esperar a que M7 y
  PR-21 estuvieran completamente cerrados, priorizando la disponibilidad
  de la herramienta para la beta cerrada.
- **Decisión**: Construir un módulo DPS como app Django (`apps.dps`)
  con un motor puro en `engine/dps.py` + `engine/dps_data.py`, siguiendo
  la misma separación de capas que el resto del proyecto (engine puro
  sin Django, apps delgadas). Los datos estáticos (species, moves,
  type chart) se almacenan como dicts Python en `dps_data.py` con
  procedencia registrada en comentarios.
- **Consecuencias positivas**: Los datos estáticos son versionables
  (via git) y no requieren base de datos ni migraciones. El motor
  es testeable en aislamiento. La feature está disponible sin esperar
  la resolución completa del hosting.
- **Consecuencias negativas**: engine/dps_data.py es grande y mezcla
  datos con tipos. A futuro, los datos del Game Master deberían
  cargarse desde un snapshot versionado (ver ADR sobre data pipeline
  de Fase 2). Los datos actuales no han pasado por Gate 0
  (verificación contra fuente primaria).
- **Status**: Aceptada.
