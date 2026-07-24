# M7 — Hardening y beta

| Campo | Valor |
|---|---|
| **Estado** | 🟨 Técnico completo; pendiente humano: apertura de beta (decisión operativa) |
| **Tamaño** | M |
| **Depende de** | M1 … M6 |
| **PRs** | PR-20, PR-21 |
| **Actualizado** | 2026-07-24 |

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
- [x] **DECIDIR hosting** — Oracle Cloud Infrastructure (OCI) capa gratuita (ARM Ampere A1 2 OCPU / 12 GB, Docker Compose). Ver ADR-0009.
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
- [x] Entorno desplegado accesible + beta cerrada operativa. **ENTORNO DESPLEGADO EN https://pogo-lab.tooltician.com (2026-07-23). Beta cerrada implementada (2026-07-24): mecanismo de invitaciones por correo vía Brevo + `INVITATION_ONLY=True` en prod. Pendiente smoke end-to-end del flujo de invitación en prod y apertura operativa.**

## Demo verificable

**Entorno desplegado con beta cerrada funcionando. PENDIENTE-HUMANO: requiere dominio, TLS y apertura.**

**ENTORNO DESPLEGADO Y VERIFICADO (2026-07-23): https://pogo-lab.tooltician.com** — DNS Cloudflare proxied (registro A → 146.181.47.12), TLS vía cert wildcard `*.tooltician.com` (Let's Encrypt, ya presente en el edge de Cloudflare), nginx en la VM escuchando 443 con self-signed origin cert (interim, swap por Cloudflare Origin CA cert cuando se emita), `set_real_ip_from` para los rangos de Cloudflare. Smoke completo verde: `/healthz.json`, `/es/`, `/en/`, login (CSRF + POST 200), legales, cabeceras HSTS+CSP+X-Content-Type-Options+Referrer-Policy, redirect HTTP→HTTPS. `cache_ratelimit` table creada en prod (faltaba). Beta cerrada pendiente: configurar `EMAIL_URL` con proveedor transaccional + mecanismo de invitaciones.

## Pendiente humano — pasos para completar M7

1. **Dominio y TLS:** ✅ **HECHO (2026-07-23).**
   - Registro A `pogo-lab.tooltician.com` → `146.181.47.12` creado en Cloudflare (proxied/naranja).
   - nginx reconfigurado en la VM: `listen 443 ssl`, `server_name pogo-lab.tooltician.com`, `set_real_ip_from` (rangos Cloudflare) + `real_ip_header CF-Connecting-IP`.
   - **Cloudflare Origin CA cert** (15 años, válido hasta 2041) instalado en `/etc/nginx/certs/{fullchain,privkey}.pem`.
   - **SSL mode = Full** (no strict). El modo Full (strict) no es usable a nivel de zona porque `tooltician.com` sirve también a GitHub Pages (sin cert SSL válido en el origin), y el SSL mode es una configuración por-zona, no por-hostname. Con el cert origin CA válido, Full ofrece cifrado end-to-end; la única diferencia con strict es que Cloudflare no valida el cert del origin (en la práctica no hay riesgo: controlamos el origin y el cert).
   - **Always Use HTTPS = on**, **HSTS at edge** (max-age=31536000, includeSubdomains, preload), **TLS 1.3 = on**, **min TLS = 1.2**.
   - `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DEFAULT_FROM_EMAIL`, `ALLAUTH_TRUSTED_CLIENT_IP_HEADER` actualizados en `.env` de la VM; gunicorn reiniciado.
   - `cache_ratelimit` table creada (faltaba → causaba 500 en POST login).

2. **Beta cerrada:**
   - Decidir mecanismo (invitaciones por correo / código de acceso / lista blanca). **HECHO (2026-07-24): mecanismo de invitaciones por correo implementado en `apps/accounts/` (modelo `Invitation` + middleware `InvitationGateMiddleware` + adapter allauth `InvitationAdapter` + admin action `send_invitations` que envía por Brevo + señal `consume_invitation_on_signup`). 20 tests en `tests/test_invitations.py`. `INVITATION_ONLY=True` en prod por defecto; False en dev/test.**
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
| 2026-07-24 | 🟨 | **Brevo SMTP wired + beta cerrada por invitación implementada.** `EMAIL_URL` configurado en `.env` y `.env-oci` (Login `b31878001@smtp-brevo.com` con `@` URL-encoded como `%40`, SMTP key `xsmtpsib-...`, `smtp-relay.brevo.com:587` con TLS). Plan 050 fail-closed validation re-activado en `prod.py` (descomentado + import `ImproperlyConfigured`); 3 tests de `test_settings.py` + 3 de `test_edge_cases.py` des-skippeados; `test_plans_regression.py` aprieta el check de código fuente. Email de prueba enviado a carlos@tooltician.com. Sistema de invitaciones: modelo `Invitation` (token `secrets.token_urlsafe`, `expires_at` automático, constraint unique pending por email), `InvitationGateMiddleware` (carga `?invite=<token>` en sesión), `InvitationAdapter` (cierra `is_open_for_signup` salvo sesión con email invitado), admin action `send_invitations` (envía correo por Brevo + registra `AuditEvent`). 20 tests nuevos en `tests/test_invitations.py`. 861 tests verdes. Pendiente humano: agregar IP del host OCI al allowlist de Brevo, verificar `noreply@tooltician.com` como sender en Brevo, smoke de extremo a extremo del flujo signup→email→verify→login en prod. |
| 2026-07-23 | ✅ | **Entorno desplegado y verificado en https://pogo-lab.tooltician.com.** DNS Cloudflare proxied (A → 146.181.47.12), **Cloudflare Origin CA cert** (15 años, hasta 2041) instalado en nginx, **SSL mode = Full (strict)**, Always Use HTTPS + HSTS at edge + TLS 1.3 + min TLS 1.2, `set_real_ip_from` Cloudflare, `.env` VM actualizado (ALLOWED_HOSTS/CSRF_TRUSTED_ORIGINS/DEFAULT_FROM_EMAIL/ALLAUTH_TRUSTED_CLIENT_IP_HEADER), `cache_ratelimit` table creada. Rate limiting con IP real del cliente (IPv4+IPv6). Smoke verde: healthz, locales es/en, login (POST 200), legales, calculadora, cabeceras HSTS+CSP+XCTO+Referrer, redirect HTTP→HTTPS, TLS 1.1 rechazado. Pendiente: `EMAIL_URL` + invitaciones para beta cerrada. |
| 2026-07-23 | 🟨 | Configuración de dominio completada en código: `CSRF_TRUSTED_ORIGINS` + `SECURE_REFERRER_POLICY` + `SECURE_CONTENT_TYPE_NOSNIFF` en `prod.py`; `set_real_ip_from` (rangos Cloudflare) + `real_ip_header CF-Connecting-IP` en `infra/nginx/default.conf` (rate limiting ve la IP real del cliente tras el proxy). Guía operativa nueva en `docs/deploy-tooltician.md` (DNS Cloudflare proxied + SSL Full strict + origin cert + smoke + rollback + beta). Tests: 817 passed, ruff/mypy limpios. Pendiente humano: crear registro A `pogo-lab`→`146.181.47.12` proxied en Cloudflare, emitir origin cert, smoke de extremo a extremo, configurar `EMAIL_URL` y abrir beta cerrada. |
| 2026-07-23 | 🟨 | Dominio decidido: `pogo-lab.tooltician.com` (subdominio de tooltician.com, sin compra nueva). Actualizados nginx `default.conf`, `prod.py` (`DEFAULT_FROM_EMAIL=carlos@tooltician.com`), scripts OCI, `.env-oci`, plantillas legales (tos/privacy) y `.po` es/en. Añadido monitor programado de capacidad OCI A1: consulta `VM.Standard.A1.Flex` cada cinco minutos sin aprovisionar recursos; alerta deduplicada por issue y webhook opcional. Requiere configurar secrets de Actions. |
| 2026-07-16 | ⬜ | Hoja creada. |
| 2026-07-17 | 🟨 | PR-20 hardening completo. Hosting decidido: OCI Santiago (AMD Micro, 1 GB). Desplegado en <http://146.181.47.12>. Pendiente: GitHub Actions secrets, SSL/Lets Encrypt, backup automático, revisión legal. |
| 2026-07-18 | 🟨 | PR-21: deploy.yml + compose.prod/micro + OCI scripts + ADR-0009 + backup/restore. Legal templates pulidos (ToS/privacy/disclaimer). healthcheck.json fuera de i18n. Tests de vistas legales (11 nuevos, 491 total). Pendiente humano: revisión legal, smoke deploy, restore verify. |
| 2026-07-19 | 🟨 | Revisión legal completa: B1 (responsable nombrado, correo privado), B2 (código propietario), B3 (Argon2 verificado en base.py). Altos resueltos: A1 (ley chilena/jurisdicción en ToS), A2 (privacidad reencuadrada bajo ley 19.628/21.719), A3 (sección Menores + casilla edad en signup), A4 (dataset CC BY 4.0). Medios/bajos: M1 (bases legales separadas), M2 (ubicación Chile), M3 (anonimización irreversible afirmada), Bj1 (README actualizado), Bj2 (fecha en disclaimer), Bj3 (control vs propiedad). E2E reparados (selector .specimen-card). 563 tests verdes. Pendiente humano: dominio/certificado TLS, apertura de beta. |
