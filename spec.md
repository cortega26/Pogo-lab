# Especificación de implementación — planes 062 y 063

## Objetivo

Cerrar los hallazgos que pueden implementarse y verificarse localmente sin
operar producción ni adquirir datos de terceros:

1. La acción de administración que envía invitaciones conserva trazabilidad
   mínima sin exponer el email de la persona invitada en eventos de auditoría,
   mensajes de administración ni logs.
2. La beta cerrada cuenta con un protocolo documentado de métricas agregadas,
   soporte, retención, rollback y decisión go/no-go previa a observar datos.
3. La futura incorporación de datos de referencia tiene un ADR y un registro
   de fuentes que preservan procedencia, reproducibilidad y cálculo sin red.
   Al no existir licencia y autorización del owner verificadas, el resultado
   debe quedar explícitamente como `blocked`; no se descargan ni ingieren
   datos, ni se modifica runtime.

## Límites y decisiones

- No enviar invitaciones, correo real ni ejecutar smoke de producción.
- No modificar secretos, configuración productiva ni artefactos de terceros.
- La auditoría de una invitación conserva `verb`, actor, tipo/id de invitación
  y `correlation_id`; `metadata` queda vacío salvo que aparezca una necesidad
  no sensible posteriormente revisada.
- En un fallo de envío, el operador recibe solo conteos y una referencia no
  sensible (ID de invitación); el log incluye la misma referencia, nunca el
  email ni el detalle de la excepción que pudiera contenerlo.
- Las métricas de beta son agregadas, con ocho o menos definiciones y sin
  email, IP, token, notas ni contenido de observaciones.

## Implementación

1. Añadir una prueba E2E local de la acción de admin con un email centinela.
   Simular un fallo cuyo mensaje también contiene el centinela y comprobar
   eventos, mensaje al admin y logs capturados.
2. Ajustar `InvitationAdmin.send_invitations` para emitir eventos sin email,
   registrar errores sanitizados y presentar un resumen de IDs/conteos.
3. Actualizar la prueba histórica que esperaba el email en `AuditEvent`.
4. Crear `docs/beta-cohort.md` con el protocolo y registrar que el smoke y la
   decisión final están bloqueados por autorización operativa.
5. Crear ADR-0012, el registro de fuentes y actualizar Fase 2 con el bloqueo
   legal actual. No crear plan sucesor porque ninguna fuente está aprobada.
6. Actualizar `plans/README.md` para que 062 y 063 reflejen el trabajo local
   completado y los bloqueos humanos restantes, sin marcar los planes como
   terminados.

## Verificación exacta

| Pieza | Prueba/evidencia | Resultado esperado |
|---|---|---|
| Sin PII en envío exitoso | `uv run pytest tests/e2e/test_beta_cohort.py -q` | El centinela no aparece en metadata, mensajes ni logs; se preservan actor, target ID y correlation ID de la request. |
| Sin PII en error de envío | misma prueba | El centinela del email y de la excepción no aparece; el mensaje/log usa solo el ID, no hay evento y `sent_at` queda vacío. |
| Contrato de invitaciones | `uv run pytest tests/test_invitations.py tests/test_audit_immutable.py -q` | Todos verdes, incluidos token válido/expirado/consumido, email ligado y consumo atómico. |
| Protocolo beta | `git diff --check -- docs/beta-cohort.md` y revisión de contenido | Máximo ocho métricas, retención, soporte, rollback y umbrales sin porcentajes inventados. |
| Contrato snapshots | `git diff --check -- docs/adr/0012-snapshots-datos-referencia.md docs/research/reference-data-source-register.md` | ADR incluye manifest, validadores, rollback y cero red; registro queda `blocked` sin raw ni secretos. |
| Sin regresiones de dominio | `uv run pytest engine/tests -q && uv run lint-imports` | Verde, sin cambio de runtime del plan 063. |
| Calidad final | `uv run pytest && uv run ruff check . && uv run ruff format --check . && uv run mypy config engine apps tests` | Todos exit 0. |
