# Protocolo de cohorte beta cerrada

**Estado:** BLOCKED — listo para autorización operativa.
**Última actualización:** 2026-07-26.
**Alcance:** beta cerrada por invitación; no autoriza apertura pública, envío de
correo ni cambios de producción.

## Objetivo y límites

Comprobar que una persona invitada puede completar el ciclo
**registro → verificación de correo → inicio de sesión → cálculo → primera
observación → análisis**, exportar sus datos y solicitar su borrado, sin usar
telemetría invasiva. La cohorte debe aportar evidencia de usabilidad y
operación, no demostrar causalidad estadística ni perfilar a participantes.

El owner debe aprobar por escrito antes de la primera invitación: tamaño máximo,
duración máxima, sender verificado, entorno y umbrales numéricos. Hasta entonces
estos campos permanecen como `pendiente de aprobación`; no se inventan
porcentajes ni se envían invitaciones.

## Roles, inclusión y soporte

| Rol | Responsabilidad |
|---|---|
| Owner de producto | Aprueba cohorte, umbrales y decisión go/no-go. |
| Operador de beta | Crea invitaciones, ejecuta el smoke autorizado y mantiene el registro sanitizado. |
| Responsable de privacidad | Atiende exportación/borrado y revisa que las métricas sigan agregadas. |
| Responsable técnico | Atiende incidentes, rollback y evidencia de disponibilidad. |

Se incluyen únicamente personas adultas invitadas que acepten los documentos
legales vigentes. Se excluye cualquier persona que no pueda recibir soporte en
el idioma acordado o que no acepte el tratamiento descrito. El soporte usa el
canal privado aprobado; no se copian emails, tokens, IPs, notas ni contenido de
observaciones al registro de la cohorte.

## Flujo operativo

```text
Owner autoriza → operador crea invitación → sender entrega correo
→ persona abre enlace → registro y verificación → inicio de sesión
→ calcula → registra observación válida → ejecuta análisis
→ exporta o solicita borrado → operador registra solo resultado agregado
```

Ante una solicitud de borrado, se aplica el flujo de eliminación de cuenta
existente, se confirma por el canal de soporte y se excluye a la cuenta de
builds comunitarios futuros. Las notas privadas no se agregan nunca.

## Métricas agregadas permitidas

La ventana, denominador mínimo para publicación y retención exacta se aprueban
antes de iniciar. Solo se conservan conteos agregados de la ventana aprobada;
no hay series por persona ni eventos individuales.

| Métrica | Numerador / denominador | Ventana | Fuente permitida | Retención | Decisión que informa |
|---|---|---|---|---|---|
| Invitación entregada | invitaciones con entrega confirmada / invitaciones enviadas | cohorte | confirmación agregada del proveedor | ventana aprobada | viabilidad del sender |
| Registro iniciado | personas que abren registro / invitaciones entregadas | cohorte | conteo agregado del flujo | ventana aprobada | claridad del enlace |
| Correo verificado | cuentas verificadas / registros iniciados | cohorte | conteo agregado de cuentas | ventana aprobada | fricción de verificación |
| Primera calculadora | cuentas con primer cálculo / cuentas verificadas | cohorte | contador agregado de producto | ventana aprobada | activación inicial |
| Primera observación válida | cuentas con observación válida / primer cálculo | cohorte | contador agregado de producto | ventana aprobada | comprensión de registro |
| Primera ejecución de análisis | cuentas con análisis / primera observación válida | cohorte | contador agregado de producto | ventana aprobada | valor del ciclo completo |
| Consentimiento | consentimientos / cuentas verificadas | cohorte | conteo agregado de consentimiento | ventana aprobada | comprensión y aceptación |
| Retorno | cuentas activas en ventana posterior / cuentas activadas | ventana aprobada | contador agregado de producto | ventana aprobada | utilidad sostenida |

Quedan prohibidos email, IP, token, notas, contenido de observaciones,
fingerprints, SDKs de terceros y cualquier denominador tan pequeño que permita
identificar a una persona.

## Umbrales, incidentes y rollback

Los umbrales numéricos son `pendiente de aprobación del owner` y deben quedar
fechados antes de observar resultados.

- **Suspender:** incidente de seguridad, exposición de datos, correo no
  verificable o fallo que impida el flujo crítico. Se deja de invitar, se
  preserva solo evidencia sanitizada y se abre incidente técnico.
- **Corregir:** fallo recurrente de registro, verificación, login, cálculo,
  observación o análisis por encima del umbral aprobado. Se pausa la cohorte,
  se corrige con pruebas y se repite smoke autorizado.
- **Continuar:** activación y ausencia de incidentes alcanzan los umbrales
  aprobados. El owner registra una decisión explícita; no hay apertura pública
  automática.

El rollback consiste en pausar la creación/envío de invitaciones, conservar
`INVITATION_ONLY=True`, revocar acceso operativo si corresponde, retirar la
cohorte de cualquier build futuro y atender exportación/borrado. No se borra un
evento de auditoría; se documenta el incidente sin PII.

## Smoke y registro de evidencia

**Estado del smoke de producción:** BLOCKED — falta autorización del owner,
confirmación segura de sender y entorno. No se ha enviado correo por este
protocolo.

Cuando se autorice, una sola cuenta de prueba controlada ejecutará: crear y
enviar invitación, abrir enlace, registro, verificar correo, login, cálculo,
observación, análisis, exportación y borrado. El registro posterior contendrá
solo fecha, identificador no sensible de la ejecución, `PASS` o `BLOCKED` y
errores sanitizados.
