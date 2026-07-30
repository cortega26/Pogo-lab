# Hosting OCI — A1 en producción y micro de rollback

Complementa **[ADR-0009](adr/0009-hosting-oracle-cloud.md)**. La asignación Always Free vigente para
**Ampere A1 Flex** es **2 OCPU / 12 GB RAM**; una configuración de **4 OCPU / 24 GB** requiere PAYG
y puede generar cargos.

## Estado actual

Desde el **2026-07-30**, producción corre en una A1 ARM64 de **2 OCPU / 12 GB RAM** con
un boot volume de 100 GB en `sa-santiago-1`. La topología activa es un monolito simple:

| Componente | Implementación actual |
|---|---|
| Aplicación | Django/Gunicorn como servicio systemd |
| Base de datos | PostgreSQL 14 local |
| Edge del host | nginx con certificado Cloudflare Origin CA |
| DNS/TLS público | Cloudflare proxied; ver [deploy-tooltician.md](deploy-tooltician.md) |
| Backups | `pogo-lab-backup.timer` diario, retención local de 14 días |
| Despliegue | GitHub Actions por SSH al host A1 |
| Rollback | micro OCI de 1 GB detenida, conservada temporalmente |

Docker Compose sigue disponible como artefacto portable, pero **no es el orquestador del entorno
productivo activo**. Esta precisión evita operar con una topología distinta de la real.

## Qué habilita la A1

El salto principal es de memoria: **1 GB → 12 GB**. La CPU solo aumenta de 1 a 2 OCPU, por lo que
la mejora es capacidad operativa y estabilidad bajo concurrencia, no cómputo ilimitado.

- Ejecutar Django, PostgreSQL y nginx juntos sin depender continuamente de swap.
- Construir dependencias, aplicar migraciones y recolectar estáticos en el host con menor riesgo de OOM.
- Ejecutar análisis estadísticos, agregaciones comunitarias e importaciones CSV sin asfixiar al proceso web.
- Hacer backups, restores de verificación y mantenimiento mientras el servicio conserva margen de memoria.
- Mantener temporalmente una base restaurada o un entorno de smoke aislado durante una operación.
- Aumentar trabajadores de Gunicorn después de medir latencia, memoria y saturación de CPU.
- Dar a PostgreSQL más caché y memoria de mantenimiento después de obtener una línea base.
- Incorporar monitoreo local liviano sin añadir Redis, colas ni microservicios.

Estas capacidades son **margen disponible**, no garantías de tráfico. Cualquier cambio de concurrencia o
memoria se valida con métricas y carga representativa antes de aplicarlo en producción.

## Mejoras priorizadas

| Prioridad | Mejora | Criterio |
|---|---|---|
| P0 · aplicada | Backup diario local + restore probado | Mantener timer activo y revisar fallos |
| P0 · aplicada | Health, TLS, firewall y servicios systemd | Verificar después de cada despliegue |
| P0 · siguiente | Copia de backups fuera de la VM | Evita que una pérdida de disco destruya original y backup |
| P1 · siguiente | Alertas de salud, disco, memoria y unidades systemd | Alertar antes de saturación o falta de espacio |
| P1 · medir | Gunicorn: evaluar 3 trabajadores | Comparar latencia y CPU con los 2 actuales; revertir si empeora |
| P1 · medir | Afinar PostgreSQL para 12 GB | Basarse en métricas; no copiar valores genéricos a ciegas |
| P2 · opcional | Restore aislado programado | Probar que el backup no solo existe, sino que restaura |
| P2 · opcional | Staging efímero | Solo durante verificación; sin secretos ni datos personales de producción |

## Límites que permanecen

- Es un **único host**: no hay alta disponibilidad ni failover automático.
- Dos OCPU pueden saturarse con simulaciones o análisis sostenidos; los trabajos pesados deben acotarse.
- No hay GPU.
- El boot volume sigue siendo finito; logs, media y backups necesitan límites y monitoreo.
- Un backup en el mismo disco no protege frente a pérdida total de la VM.
- Más RAM no justifica introducir Redis, colas, microservicios u otros componentes sin necesidad demostrada.

---

## Histórico y recuperación de capacidad

## A · Conseguir o recrear una A1 en OCI

### A.0 — Corrige el destino de región (bug en setup-oci.sh)

Los recursos **Always Free solo existen en la región HOME** (aquí `sa-santiago-1`). El
`setup-oci.sh` original tenía `OCI_REGION` con default `us-ashburn-1`: con cuenta gratuita
**falla** y con PAYG **factura** silenciosamente.

**Estado: ya corregido.** Tu `.env-oci` fija `OCI_REGION=sa-santiago-1` (el bug no estaba activo),
y además se endureció el default del script a la región home (`OCI_REGION="${OCI_REGION:-$OCI_HOME_REGION}"`),
así una corrida futura sin esa variable ya no cae en Ashburn.

### A.1 — Pay As You Go (PAYG): cuotas pagadas, no más Always Free

Es una acción **manual** de consola (no se puede automatizar) que permite usar más tipos y cuotas de
Compute, pero no amplía la asignación Always Free ni garantiza capacidad física A1:

1. Consola OCI → menú de usuario → **Upgrade to Paid** / *Upgrade and manage payment*.
2. Añades tarjeta. No hay cargos mientras te quedes dentro del límite Always Free vigente
   (**2 OCPU + 12 GB RAM**); 4 OCPU / 24 GB lo excede.
3. Revisa la capacidad antes de lanzar una VM: PAYG no elimina un `Out of host capacity`.

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
envuelto en reintentos con backoff, y el default de región es la home region. El tamaño por defecto
es 2 OCPU / 12 GB para respetar Always Free; 4/24 exige cambiar ambas variables explícitamente y
aceptar PAYG. Verificado con un simulacro del launch bajo `set -euo pipefail`:

- **Capacidad transitoria** (`Out of host capacity`, `LimitExceeded`, `InternalError`,
  `TooManyRequests`) → reintenta cada `A1_RETRY_SECONDS` segundos (por defecto 60).
- **Error real** (shape inexistente, permisos, cuota) → **aborta** al instante con el mensaje, sin
  quedar en bucle.

Como `OCI_REGION` y `OCI_HOME_REGION` ya valen `sa-santiago-1`, todas las llamadas de creación
(VCN, subnet, launch) usan la misma región. Uso si hay que recrear la A1:

```bash
./bin/setup-oci.sh                 # reintenta cada 60 s hasta conseguir la A1
A1_RETRY_SECONDS=120 ./bin/setup-oci.sh   # o espacia más los reintentos
```

Santiago suele tener un solo Availability Domain, así que reintentar sobre el mismo AD basta. Si
tuviera varios, habría que iterar `AD` en cada intento (no implementado; no necesario para Santiago).

---

## B · Fallback y rollback: micro de 1 GB

La micro anterior permanece detenida como rollback temporal. Si hay que reconstruir un fallback de 1 GB,
conviene sacar Postgres de la caja y añadir swap. Ficheros provistos:
`compose.micro.yaml` + `bin/setup-swap.sh`.

### B.1 — Postgres gestionado gratuito (Neon o Supabase)

1. Crea un proyecto en [neon.tech](https://neon.tech) (o Supabase). Ambos tienen capa gratuita real.
2. Copia el connection string. **Debe** llevar SSL:
   `postgres://USER:PASS@HOST/DB?sslmode=require`
3. En la VM, en `/opt/pogo-lab/.env.prod`, añade la línea:

   ```dotenv
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

El stack es portable (Docker + `DATABASE_URL`). Las opciones siguientes son referencias históricas;
antes de usarlas hay que verificar disponibilidad, límites y precios vigentes:

- **Google Cloud "Always Free" e2-micro** (`us-west1`/`us-central1`/`us-east1`): 1 GB RAM
  compartida pero **disponible de forma fiable** (sin lotería de capacidad) + 30 GB de disco.
  Mismo tamaño que la micro de OCI, sin sorpresas. Empareja con Neon/Supabase (§B.1).
- **Koyeb:** instancia nano gratis, always-on.
- **Render:** web service gratis pero **se duerme a los 15 min** y su Postgres gratuito expira —
  molesto para una beta persistente.
- **Fly.io:** ya **no** es gratis de verdad para orgs nuevas (uso medido).

---

## Resumen de decisión

1. **Producción:** A1 de 2 OCPU / 12 GB dentro de la asignación prevista; no ampliar a 4/24 sin
   aceptación explícita de PAYG.
2. **Operación:** mantener el monolito systemd simple y medir antes de aumentar workers o memoria de PostgreSQL.
3. **Durabilidad:** priorizar backup fuera de la VM y alertas antes de añadir nuevas piezas de infraestructura.
4. **Rollback:** conservar la micro detenida durante la ventana operativa acordada; después, retirarla
   explícitamente para evitar drift y superficie de mantenimiento.
5. **Escape:** si OCI deja de ser adecuado, usar la portabilidad de `Dockerfile`/`DATABASE_URL` (§C).
