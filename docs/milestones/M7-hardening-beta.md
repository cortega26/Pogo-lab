# M7 — Hardening y beta

| Campo | Valor |
|---|---|
| **Estado** | 🟨 Técnico completo; pendiente humano: dominio/TLS y apertura de beta |
| **Tamaño** | M |
| **Depende de** | M1 … M6 |
| **PRs** | PR-20, PR-21 |
| **Actualizado** | 2026-07-19 |

## Objetivo

Endurecer para beta: E2E completos, accesibilidad, rendimiento, seguridad, backup/restore, despliegue, analítica
de producto y revisión legal.

## Historias

- Como responsable, quiero desplegar con bajo costo y un restore probado antes de abrir la beta cerrada.
- Como usuario, quiero una experiencia accesible y rápida en móvil.

## Tareas

### PR-20 · hardening

- [x] **CSP** estricta (JS autohospedado; sin inline salvo hashes).
- [x] **Rate limiting** en login/registro/contribución.
- [x] `pip-audit` en CI (sin vulnerabilidades críticas).
- [x] Suite **Playwright completa**: los 10 flujos críticos (plan §13).
- [x] Auditoría de **accesibilidad** (teclado, contraste, tabla alternativa a gráficos) + **Core Web Vitals**.
- [x] **Determinismo del agregado** comunitario (mismo dataset → mismo p-valor).
- [x] **Verificación de email** activa (`mandatory` en prod).

### PR-21 · deploy + beta

- [x] `Dockerfile` de producción + `.github/workflows/deploy.yml`.
- [x] **DECIDIR hosting** — Oracle Cloud Infrastructure (OCI) capa gratuita (ARM Ampere A1, Docker Compose). Ver ADR-0009.
- [x] Postgres administrado + **backup** + **procedimiento de restore** documentado.
- [x] Métricas de producto (plan §12/§18) sin invadir privacidad.
- [x] Completar **exportación** y **eliminación** de cuenta (stubs de M1).
- [x] Revisión legal/marca: disclaimer no afiliación, privacidad, ToS, licencias. **Bloqueantes resueltos (B1 responsable+correo, B2 código abierto→propietario, B3 Argon2 configurado). Altos/medios/bajos atendidos (ley chilena, menores, ubicación datos, licencia dataset CC BY 4.0, jurisdicción). Revisión profesional recomendada pero no bloqueante.**

## Archivos / módulos afectados

`.github/workflows/`, `infra/`, `compose.prod.yaml`, `compose.micro.yaml`, `bin/` (setup-oci, backup, restore),
`apps/audit/`, `apps/accounts/` (export/delete), `templates/legal/`, `docs/`.

## Pruebas

- [x] Los 10 E2E verdes en CI.
- [x] Smoke de despliegue en el entorno objetivo (health, páginas públicas, redirects autenticados y cabeceras).
- [x] **Restore** verificado desde backup en una base aislada (30 tablas, 44 migraciones).

## Criterios de aceptación

- [x] **Definición de terminado** del plan (§O) — hardening completo.
- [ ] Entorno desplegado accesible + beta cerrada operativa. **PENDIENTE-HUMANO: requiere dominio, certificado TLS (Let's Encrypt) y decisión de apertura.**

## Demo verificable

**Entorno desplegado con beta cerrada funcionando. PENDIENTE-HUMANO: requiere dominio, TLS y apertura.**

## Pendiente humano — pasos para completar M7

1. **Dominio y TLS:**
   - Comprar `pogo-lab.com` (o similar) en un registrador.
   - Apuntar DNS A/AAAA a la IP `146.181.47.12` (OCI Santiago).
   - Ejecutar certbot/Let's Encrypt para el certificado SSL.
   - Actualizar `infra/nginx/default.conf` con el dominio y redirigir HTTP→HTTPS.
   - Configurar `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` en `config/settings/prod.py`.

2. **Beta cerrada:**
   - Decidir mecanismo (invitaciones por correo / código de acceso / lista blanca).
   - Configurar `ACCOUNT_EMAIL_VERIFICATION = "mandatory"` (ya está en prod).
   - Aviso legal en signup + consentimiento GDPR/chileno.

3. **Revisión legal con abogado (recomendado, no bloqueante):**
   - Validar encuadre bajo Ley 21.719 (entrada en vigor ~12/2026).
   - Confirmar umbral de edad para menores bajo ley chilena.
   - Evaluar riesgo de marca del nombre "Pogo-lab".

- Revisión legal pendiente puede bloquear el lanzamiento → iniciarla temprano (no bloquea el código).

## Recortes posibles

Profundidad de la analítica de producto (empezar con métricas mínimas).

## Registro de avance

| Fecha | Estado | Nota |
|---|---|---|
| 2026-07-16 | ⬜ | Hoja creada. |
| 2026-07-17 | 🟨 | PR-20 hardening completo. Hosting decidido: OCI Santiago (AMD Micro, 1 GB). Desplegado en <http://146.181.47.12>. Pendiente: GitHub Actions secrets, SSL/Lets Encrypt, backup automático, revisión legal. |
| 2026-07-18 | 🟨 | PR-21: deploy.yml + compose.prod/micro + OCI scripts + ADR-0009 + backup/restore. Legal templates pulidos (ToS/privacy/disclaimer). healthcheck.json fuera de i18n. Tests de vistas legales (11 nuevos, 491 total). Pendiente humano: revisión legal, smoke deploy, restore verify. |
| 2026-07-19 | 🟨 | Revisión legal completa: B1 (responsable nombrado, correo privado), B2 (código propietario), B3 (Argon2 verificado en base.py). Altos resueltos: A1 (ley chilena/jurisdicción en ToS), A2 (privacidad reencuadrada bajo ley 19.628/21.719), A3 (sección Menores + casilla edad en signup), A4 (dataset CC BY 4.0). Medios/bajos: M1 (bases legales separadas), M2 (ubicación Chile), M3 (anonimización irreversible afirmada), Bj1 (README actualizado), Bj2 (fecha en disclaimer), Bj3 (control vs propiedad). E2E reparados (selector .specimen-card). 563 tests verdes. Pendiente humano: dominio/certificado TLS, apertura de beta. |
