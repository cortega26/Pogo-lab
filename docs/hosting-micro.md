# Hosting — plan A1 (ideal) y fallback en micro (1 GB)

Complementa **[ADR-0009](adr/0009-hosting-oracle-cloud.md)**. El objetivo sigue siendo la
**Ampere A1 Flex (4 OCPU / 24 GB RAM)** — el mejor VPS gratuito que existe. Este documento cubre
(A) cómo conseguirla pese al *"Out of host capacity"* y (B) cómo dejar la beta viva **hoy** en la
micro diminuta mientras tanto.

---

## A · Conseguir la A1 en OCI (lo ideal)

### A.0 — Corrige el destino de región (bug en setup-oci.sh)

Los recursos **Always Free solo existen en la región HOME** (aquí `sa-santiago-1`). El
`setup-oci.sh` original tenía `OCI_REGION` con default `us-ashburn-1`: con cuenta gratuita
**falla** y con PAYG **factura** silenciosamente.

**Estado: ya corregido.** Tu `.env-oci` fija `OCI_REGION=sa-santiago-1` (el bug no estaba activo),
y además se endureció el default del script a la región home (`OCI_REGION="${OCI_REGION:-$OCI_HOME_REGION}"`),
así una corrida futura sin esa variable ya no cae en Ashburn.

### A.1 — Sube la cuenta a Pay As You Go (PAYG) ← el desbloqueo real

Es una acción **manual** de consola (no se puede automatizar) y es lo que más veces habilita la
A1 al primer intento:

1. Consola OCI → menú de usuario → **Upgrade to Paid** / *Upgrade and manage payment*.
2. Añades tarjeta. **No te cobran** mientras te quedes dentro de los límites Always Free
   (4 OCPU + 24 GB RAM + 200 GB de bloque, en total).
3. PAYG elimina el estrangulamiento de capacidad A1 que Oracle aplica a las cuentas gratuitas.

**Red de seguridad (coste 0 garantizado):** crea una alerta de presupuesto a **0,01 USD** en
*Billing → Budgets*, así cualquier consumo accidental salta al instante.

### A.2 — Verifica que Santiago OFRECE A1 (antes de reintentar nada)

Un bucle de reintento solo tiene sentido si el shape existe en la región. Con `oci` CLI
configurado (`.env-oci` ya tiene tus OCIDs):

```bash
oci compute shape list \
  --compartment-id "$OCI_COMPARTMENT_OCID" \
  --region sa-santiago-1 --all \
  --query "data[?contains(shape,'A1')].shape" --output table
```

- **Resultado vacío** → Santiago no ofrece A1: el reintento es inútil. Opciones: cuenta nueva con
  otra home region grande (`sa-saopaulo-1`, `us-phoenix-1`, `eu-frankfurt-1`) **o** el fallback de
  la §B / el escape a GCP (§C).
- **Resultado con A1** → capacidad transitoria: aplica PAYG (§A.1) y el reintento (§A.3).

También conviene ver qué hay corriendo ya y en qué región (para no resolver el problema
equivocado):

```bash
for R in sa-santiago-1 us-ashburn-1; do
  oci compute instance list --compartment-id "$OCI_COMPARTMENT_OCID" --region "$R" \
    --query "data[].{name:\"display-name\",shape:shape,state:\"lifecycle-state\"}" --output table
done
```

### A.3 — Reintento + región home en setup-oci.sh (ya aplicado)

**Ya está en el script** (`bin/setup-oci.sh`): el bloque de `oci compute instance launch` está
envuelto en reintentos con backoff, y el default de región es la home region. Verificado con un
simulacro del launch bajo `set -euo pipefail`:

- **Capacidad transitoria** (`Out of host capacity`, `LimitExceeded`, `InternalError`,
  `TooManyRequests`) → reintenta cada `A1_RETRY_SECONDS` segundos (por defecto 60).
- **Error real** (shape inexistente, permisos, cuota) → **aborta** al instante con el mensaje, sin
  quedar en bucle.

Como `OCI_REGION` y `OCI_HOME_REGION` ya valen `sa-santiago-1`, todas las llamadas de creación
(VCN, subnet, launch) usan la misma región. Uso, cuando PAYG apruebe:

```bash
./bin/setup-oci.sh                 # reintenta cada 60 s hasta conseguir la A1
A1_RETRY_SECONDS=120 ./bin/setup-oci.sh   # o espacia más los reintentos
```

Santiago suele tener un solo Availability Domain, así que reintentar sobre el mismo AD basta. Si
tuviera varios, habría que iterar `AD` en cada intento (no implementado; no necesario para Santiago).

---

## B · Fallback: micro de 1 GB usable hoy

Independiente de la A1. Sirve una beta cerrada sin problemas si sacas Postgres de la caja y añades
swap. Ficheros ya provistos: `compose.micro.yaml` + `bin/setup-swap.sh`.

### B.1 — Postgres gestionado gratuito (Neon o Supabase)

1. Crea un proyecto en [neon.tech](https://neon.tech) (o Supabase). Ambos tienen capa gratuita real.
2. Copia el connection string. **Debe** llevar SSL:
   `postgres://USER:PASS@HOST/DB?sslmode=require`
3. En la VM, en `/opt/pogo-lab/.env.prod`, añade la línea:
   ```
   DATABASE_URL=postgres://USER:PASS@HOST/DB?sslmode=require
   ```
   (`config.settings.base` lee `DATABASE_URL` vía `env.db()` — cambio de una línea, sin tocar código.)

### B.2 — Swap (imprescindible en 1 GB)

```bash
cd /opt/pogo-lab
sudo ./bin/setup-swap.sh 2      # 2 GB; usa 4 si el build sigue muriendo
```

### B.3 — Desplegar con el compose afinado

```bash
cd /opt/pogo-lab
docker compose -f compose.micro.yaml up -d --build
docker compose -f compose.micro.yaml exec -T web python manage.py migrate --noinput
curl -s -o /dev/null -w "healthz → %{http_code}\n" http://localhost/healthz
```

`compose.micro.yaml` no arranca contenedor `db` (usa el Postgres externo) y baja gunicorn a 2
workers. Si el `build: .` aún muere por memoria pese al swap, ese es el momento —y no antes— de
construir la imagen fuera (GitHub Actions → registro) y hacer `pull` en la VM.

---

## C · Escape a otro proveedor gratuito

El stack es portable (Docker + `DATABASE_URL`), migrar cuesta minutos:

- **Google Cloud "Always Free" e2-micro** (`us-west1`/`us-central1`/`us-east1`): 1 GB RAM
  compartida pero **disponible de forma fiable** (sin lotería de capacidad) + 30 GB de disco.
  Mismo tamaño que la micro de OCI, sin sorpresas. Empareja con Neon/Supabase (§B.1).
- **Koyeb:** instancia nano gratis, always-on.
- **Render:** web service gratis pero **se duerme a los 15 min** y su Postgres gratuito expira —
  molesto para una beta persistente.
- **Fly.io:** ya **no** es gratis de verdad para orgs nuevas (uso medido).

---

## Resumen de decisión

1. **PAYG** (§A.1) — mantiene todo gratis y es lo que más veces desbloquea la A1. Alerta a 0,01 USD.
2. **En paralelo**, deja la beta viva con la micro afinada (§B): Neon + swap + `compose.micro.yaml`.
3. Verifica A1 en Santiago (§A.2); si existe, aplica el patch de reintento (§A.3).
4. Si Santiago nunca da A1: cuenta nueva con otra home region, o GCP e2-micro (§C).
