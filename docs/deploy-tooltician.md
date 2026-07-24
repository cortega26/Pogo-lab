# Despliegue en `pogo-lab.tooltician.com`

Guía operativa para poner la beta en producción bajo el subdominio
`pogo-lab.tooltician.com` (dominio `tooltician.com` gestionado en Cloudflare).

**Topología:** Cloudflare (proxy naranja) → VM OCI `146.181.47.12` (nginx + Django).
SSL termina en Cloudflare (modo **Full (strict)**) con un **origin certificate** de
Cloudflare instalado en nginx. La IP de la VM queda oculta; los rangos de Cloudflare
están listados en `infra/nginx/default.conf` (`set_real_ip_from` + `real_ip_header
CF-Connecting-IP`) para que Django vea la IP real del cliente (requerido por el rate
limiting).

Complementa [hosting-micro.md](hosting-micro.md) y [ADR-0009](adr/0009-hosting-oracle-cloud.md).

---

## 1. Crear el registro DNS en Cloudflare

Panel de Cloudflare → **tooltician.com** → **DNS** → **Records** → **Add record**.

| Tipo | Nombre | Contenido | Proxy | TTL |
|---|---|---|---|---|
| `A` | `pogo-lab` | `146.181.47.12` | **Proxied** (naranja) | Auto |
| `A` | `www.pogo-lab` | `146.181.47.12` | **Proxied** (naranja) | Auto |
| `AAAA` | `pogo-lab` | *(IPv6 de la VM, si la hay)* | **Proxied** | Auto |

> La VM OCI micro actual es IPv4. Si más adelante se habilita IPv6 en la VCN de OCI,
> añade el registro `AAAA` correspondiente. Sin él, Cloudflare entrega el sitio por IPv4
> y por IPv6 con su propio stack (suficiente para la beta).

**Verificar propagación** (1–5 minutos):

```bash
dig +short pogo-lab.tooltician.com        # debe devolver IPs de Cloudflare (104.x/172.x)
dig +short www.pogo-lab.tooltician.com    # igual
```

> Con proxy naranja, el registro resuelve a IPs de Cloudflare, **no** a `146.181.47.12`.
# Es esperado y deseado: la IP del origin queda oculta.

---

## 2. Configurar SSL/TLS en Cloudflare

Panel → **SSL/TLS** → **Overview**.

1. Modo de cifrado: **Full (strict)**. (No *Flexible* — expone cookies por HTTP interno
   y rompe HSTS; no *Full* a secas — acepta certs autocfirmados en el origin.)
2. **SSL/TLS → Edge Certificates**:
   - *Always Use HTTPS*: **On**.
   - *HSTS*: **On** con `max-age=31536000`, `includeSubdomains`, `preload`.
     (El header `Strict-Transport-Security` ya lo emite Django en `prod.py`, pero
     activarlo también en el edge endurece el caso de peticiones que nunca lleguen al
     origin.)
   - *Minimum TLS Version*: **TLS 1.2**.
   - *Opportunistic Encryption* / *TLS 1.3*: **On**.

### 2.1 Emitir un origin certificate (Cloudflare Origin CA)

Cloudflare → **SSL/TLS → Origin Server → Create Certificate**.

- Private key type: **RSA (2048)**.
- Hostnames: `pogo-lab.tooltician.com, *.pogo-lab.tooltician.com`.
- Validity: **15 years** (los origin certificates de CF son de larga duración y solo
  válidos tras el proxy de Cloudflare).

Guarda los dos bloques PEM y súbelos a la VM (ver §3).

> Alternativa: `certbot --nginx` con challenge HTTP-01. **No recomendado** en modo
# proxied naranja: Let's Encrypt no siempre puede alcanzar el origin por HTTP-01 con el
# proxy de por medio, y los origin certs de CF no caducan cada 90 días.

---

## 3. Instalar el certificado origin en la VM

En la VM OCI (`146.181.47.12`), como root:

```bash
# 1. Copiar los PEM (desde tu máquina o pegarlos en la VM)
ssh ubuntu@146.181.47.12

# 2. Crear el directorio de certs si no existe
sudo mkdir -p /etc/nginx/certs

# 3. Pegar el contenido del origin certificate
sudo nano /etc/nginx/certs/fullchain.pem
#   (pégalo y guarda)

# 4. Pegar la private key
sudo nano /etc/nginx/certs/privkey.pem
#   (pégala y guarda)

# 5. Permisos estrictos
sudo chmod 644 /etc/nginx/certs/fullchain.pem
sudo chmod 600 /etc/nginx/certs/privkey.pem
sudo chown -R root:root /etc/nginx/certs

# 6. Test de config y reload
sudo nginx -t
sudo systemctl reload nginx
```

> Si los certs se gestionan dentro del stack Docker de Pogo-lab, montalos como volumen
> en `compose.prod.yaml` (o `compose.micro.yaml`) apuntando a `/etc/nginx/certs/` del
> contenedor nginx. Verifica que `infra/nginx/default.conf` referencia
> `/etc/nginx/certs/fullchain.pem` y `privkey.pem` (ya lo hace).

---

## 4. Verificar extremo a extremo

Desde tu máquina, una vez propagado el DNS y con certs instalados:

```bash
# 1. Resolución DNS (IPs de Cloudflare)
dig +short pogo-lab.tooltician.com

# 2. HTTPS responde con 200/302
curl -sS -o /dev/null -w "HTTP %{http_code} en %{time_total}s\n" \
  https://pogo-lab.tooltician.com/

# 3. Cadena de certificados válida
curl -sS -v https://pogo-lab.tooltician.com/ 2>&1 | grep -E "SSL|TLS|subject|issuer"

# 4. Redirección HTTP -> HTTPS
curl -sS -o /dev/null -w "%{http_code} -> %{redirect_url}\n" \
  http://pogo-lab.tooltician.com/

# 5. Cabeceras de seguridad presentes
curl -sSI https://pogo-lab.tooltician.com/ | grep -iE "strict-transport|x-content|referrer"
```

**Resultado esperado:**
- `dig` devuelve IPs `104.x` o `172.x` (Cloudflare).
- `curl https` devuelve `302` (redirect de Django a login/locale) o `200`.
- `curl http` devuelve `301` a `https://`.
- HSTS, `X-Content-Type-Options`, `Referrer-Policy` presentes.

---

## 5. Smoke de despliegue (post-DNS/TLS)

Checklist mínimo antes de declarar la beta operativa. Corre cada paso y registra el
resultado en el registro de avance de `docs/milestones/M7-hardening-beta.md`.

- [ ] `https://pogo-lab.tooltician.com/` carga la home (locale por defecto `es`).
- [ ] `https://pogo-lab.tooltician.com/en/` carga la home en inglés.
- [ ] `https://pogo-lab.tooltician.com/healthz.json` responde `{"status": "ok"}`.
- [ ] `/accounts/login/` renderiza el formulario (sin errores 500).
- [ ] Un POST de login inválido devuelve 200 con error de formulario (no 403 CSRF).
- [ ] `/privacy/` y `/tos/` cargan con el correo `carlos@tooltician.com`.
- [ ] Cabeceras: HSTS, `X-Content-Type-Options: nosniff`, `Referrer-Policy`.
- [ ] CSP en la respuesta (sin violaciones en la consola del navegador).
- [ ] TLS: nota A+ en https://www.ssllabs.com/ssltest/ (opcional pero recomendado).
- [ ] Backup automático ejecutado al menos una vez tras el despliegue (ver
      `bin/backup-oci.sh`).

---

## 6. Apertura de beta cerrada

Ver también `docs/milestones/M7-hardening-beta.md` § "Pendiente humano — pasos para
completar M7".

1. **Mecanismo de acceso.** **IMPLEMENTADO (2026-07-24):** invitaciones por correo.
   - Modelo `apps.accounts.models.Invitation` (token `secrets.token_urlsafe`,
     `expires_at` automático con `INVITATION_EXPIRY_DAYS=14`, constraint de una
     invitación pendiente por email).
   - `apps.accounts.middleware.InvitationGateMiddleware` valida `?invite=<token>`
     en la URL de signup y carga el email en sesión.
   - `apps.accounts.adapter.InvitationAdapter` cierra `is_open_for_signup` salvo
     que la sesión tenga un email de invitación válido (renderiza
     `templates/account/signup_closed.html` cuando está cerrado).
   - Admin action `send_invitations` en `apps/accounts/admin.py` envía el correo
     de invitación vía Brevo y registra un `AuditEvent` (`invitation_sent`).
   - Señal `consume_invitation_on_signup` marca la invitación como consumida al
     crearse un usuario con el email invitado.
   - `INVITATION_ONLY=True` en `prod.py` por defecto; `False` en `dev.py`/`test.py`.
   - 20 tests en `tests/test_invitations.py` cubren modelo, middleware, adapter,
     señal, admin action y flujo end-to-end.

2. **Email transaccional.** `ACCOUNT_EMAIL_VERIFICATION = "mandatory"` ya está en
   `prod.py`. **CONFIGURADO (2026-07-24):** Brevo SMTP relay wired en `.env` y
   `.env-oci` (`EMAIL_URL=smtp+tls://b31878001%40smtp-brevo.com:...@smtp-relay.brevo.com:587`,
   `DEFAULT_FROM_EMAIL=noreply@tooltician.com`). Plan 050 fail-closed validation
   re-activado en `prod.py`. Test de envío real pasado (correo entregado a
   carlos@tooltician.com). Pendiente humano: agregar IP del host OCI al allowlist
   de Brevo (Settings → SMTP & API) y verificar `noreply@tooltician.com` como
   sender o dominio verificado en Brevo.

3. **Aviso legal + consentimiento.** Las plantillas `privacy.html` y `tos.html` ya
   citan a Carlos M. y `carlos@tooltician.com`. Falta:
   - Casilla de aceptación de ToS + privacidad en el formulario de signup
     (si no existe, añadir `BooleanField` obligatorio).
   - Registro de la versión de ToS aceptada por usuario (para auditoría ante cambios).

4. **Revisión legal con abogado** (recomendado, no bloqueante para código):
   - Encuadre definitivo bajo Ley 21.719 (entrada en vigor ~12/2026).
   - Umbral de edad para menores.
   - Riesgo de marca del nombre "Pogo-lab" (no contiene "pokemon/pokémon", pero un
     abogado debe confirmar).

---

## 7. Rollback

Si el despliegue con el nuevo dominio falla y hay que volver atrás rápido:

1. **DNS:** en Cloudflare, poner el registro `A pogo-lab` en modo **DNS only** (gris)
   o pausar el proxy de Cloudflare para aislar el problema del origin.
2. **Certificado:** si el origin cert está mal, reemplazar
   `/etc/nginx/certs/{fullchain,privkey}.pem` y `sudo systemctl reload nginx`.
3. **Código:** `git revert <commit>` del commit de dominio si el problema es de
   configuración de Django/nginx.
4. **Acceso de emergencia:** la VM sigue siendo alcanzable por IP
   (`http://146.181.47.12`) mientras `ALLOWED_HOSTS` lo permita; útil para debug.

---

## 8. Mantenimiento

- **Rotación de origin cert:** cada 15 años (o al rotar claves de Cloudflare).
- **Rangos IP de Cloudflare:** se actualizan ocasionalmente. Script oficial:
  `curl -sL https://www.cloudflare.com/ips/ | xargs`. Si se endurece más, montar un
  cron que regenere la lista `set_real_ip_from` en nginx. Por ahora, los rangos en
  `default.conf` son los vigentes a 2026-07.
- **Monitor de capacidad A1:** ver `.github/workflows/` (requiere secrets de Actions).
  Si consigue una A1, migrar de la micro (1 GB) a la A1 (12 GB) — ver
  `hosting-micro.md`.
