#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# Pogo-lab — Asistente de configuración OCI + GitHub
#
# Te guía paso a paso para obtener cada variable y escribe .env-oci.
# Después, setup-oci.sh usa esas variables para crear la VM.
# ═══════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DOT_ENV="$ROOT_DIR/.env-oci"

echo "╔══════════════════════════════════════════════╗"
echo "║  Pogo-lab — Asistente de configuración OCI   ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Keygen check ──────────────────────────────────────────────
if [ ! -f "$ROOT_DIR/infra/keys/oci_api_key.pem" ]; then
    echo "❌ No se encuentra infra/keys/oci_api_key.pem. Ejecuta primero:"
    echo "   openssl genrsa -out infra/keys/oci_api_key.pem 2048"
    echo "   openssl rsa -pubout -in infra/keys/oci_api_key.pem -out infra/keys/oci_api_key_public.pem"
    exit 1
fi

if [ ! -f "$ROOT_DIR/infra/keys/deploy_key" ]; then
    echo "❌ No se encuentra infra/keys/deploy_key. Ejecuta primero:"
    echo "   ssh-keygen -t ed25519 -C \"pogo-lab-deploy\" -N \"\" -f infra/keys/deploy_key"
    exit 1
fi

# ── Función helper ────────────────────────────────────────────
ask_value() {
    local label="$1"
    local env_var="$2"
    local current="${!env_var:-}"

    if [ -n "$current" ] && [ "$current" != "__PLACEHOLDER__" ]; then
        echo "→ $label: [ya configurado: $current] (Enter para mantener)" >&2
    else
        echo "→ $label:" >&2
    fi
    read -r -p "  > " value
    if [ -z "$value" ] && [ -n "$current" ] && [ "$current" != "__PLACEHOLDER__" ]; then
        value="$current"
    fi
    echo "$value"
}

# ── 0. Cargar .env-oci si existe ──────────────────────────────
touch "$DOT_ENV"
set -a
source "$DOT_ENV" 2>/dev/null || true
set +a

# ── 1. OCI Tenancy OCID ───────────────────────────────────────
echo ""
echo "── Paso 1: OCI Tenancy OCID ───────────────────"
echo ""
echo "   ¿Tienes ya una cuenta de Oracle Cloud?"
echo "   [s] Sí, ya tengo cuenta"
echo "   [n] No, necesito crear una"
read -p "   > " has_account

if [ "$has_account" = "n" ]; then
    echo ""
    echo "   ► Abre https://www.oracle.com/cloud/free/"
    echo "   ► Haz clic en 'Start for free'"
    echo "   ► Completa el registro (necesitas tarjeta para verificación, NO se cobra)"
    echo "   ► Cuando termines, vuelve aquí y presiona Enter."
    read -p ""
fi

echo ""
echo "   ► Abre https://cloud.oracle.com y haz login."
echo "   ► En la parte superior, verás tu nombre de tenancy."
echo "   ► Haz clic en Profile (esquina superior derecha) → Tenancy: <nombre>."
echo "   ► Copia el 'OCID' del tenancy."
echo ""

OCI_TENANCY_OCID=$(ask_value "Pega aquí el Tenancy OCID" "OCI_TENANCY_OCID")

# ── 2. OCI User OCID ──────────────────────────────────────────
echo ""
echo "── Paso 2: OCI User OCID ──────────────────────"
echo ""
echo "   ► En la misma página de Profile → User Settings"
echo "   ► Copia el 'User OCID'"
echo ""

OCI_USER_OCID=$(ask_value "Pega aquí el User OCID" "OCI_USER_OCID")

# ── 3. OCI Region ─────────────────────────────────────────────
echo ""
echo "── Paso 3: Región OCI ─────────────────────────"
echo ""
    echo "   Ejemplos de regiones (todas las regiones comerciales"
    echo "   tienen capa gratuita, incluida Santiago):"
    echo "   us-ashburn-1, eu-frankfurt-1, sa-santiago-1, sa-saopaulo-1,"
    echo "   uk-london-1, ap-tokyo-1, ap-seoul-1, ap-mumbai-1, me-dubai-1"
echo ""

OCI_REGION=$(ask_value "¿Qué región? (ej: eu-frankfurt-1)" "OCI_REGION")

# ── 4. OCI API Key + Fingerprint ──────────────────────────────
echo ""
echo "── Paso 4: API Key + Fingerprint ──────────────"
echo ""
echo "   ► Ve a Profile → User Settings → API Keys → Add API Key."
echo "   ► Selecciona 'Paste a public key'."
echo "   ► Pega el contenido de este archivo (lo abro ahora):"
echo ""
cat "$ROOT_DIR/infra/keys/oci_api_key_public.pem"
echo ""
echo "   ► Haz clic en 'Add'."
echo "   ► En la ventana de confirmación verás un 'Fingerprint'."
echo "   ► Copia ese fingerprint (formato: xx:xx:xx:...)."
echo ""

OCI_FINGERPRINT=$(ask_value "Pega aquí el Fingerprint" "OCI_FINGERPRINT")

# ── 5. OCI Compartment ────────────────────────────────────────
echo ""
echo "── Paso 5: Compartment OCID ───────────────────"
echo ""
echo "   Si tu cuenta es nueva/tiene un solo compartment,"
echo "   usa el mismo valor que el Tenancy OCID."
echo "   Para verificarlo: Identity → Compartments."
echo ""

OCI_COMPARTMENT_OCID=$(ask_value "Compartment OCID (Enter para usar el del tenancy)" "OCI_COMPARTMENT_OCID")
if [ -z "$OCI_COMPARTMENT_OCID" ]; then
    OCI_COMPARTMENT_OCID="$OCI_TENANCY_OCID"
fi

# ── 6. Subnet OCID (opcional) ─────────────────────────────────
echo ""
echo "── Paso 6: Subred (opcional) ──────────────────"
echo ""
echo "   Si ya tienes una VCN con subnet pública, pega su OCID."
echo "   Si no, deja vacío y el script de setup creará una VCN nueva."
echo ""

OCI_SUBNET_OCID=$(ask_value "Subnet OCID (Enter para crear automáticamente)" "OCI_SUBNET_OCID")

# ── 7. GitHub ─────────────────────────────────────────────────
echo ""
echo "── Paso 7: GitHub ─────────────────────────────"
echo ""
echo "   Deploy key pública (cópiala):"
echo ""
cat "$ROOT_DIR/infra/keys/deploy_key.pub"
echo ""
echo "   ► Ve a tu repo en GitHub → Settings → Deploy keys → Add deploy key."
echo "   ► Title: 'OCI Pogo-lab'"
echo "   ► Pega la clave pública de arriba."
echo "   ► Marca 'Allow write access' si necesitas pushes desde la VM."
echo "   ► Add key."
echo ""

GITHUB_REPO_URL=$(ask_value "URL SSH del repo (ej: git@github.com:usuario/pogo-lab.git)" "GITHUB_REPO_URL")

# ── 8. App secrets ────────────────────────────────────────────
echo ""
echo "── Paso 8: Secretos de la app ─────────────────"
echo ""

APP_SECRET_KEY=$(ask_value "Django SECRET_KEY (Enter para generar una aleatoria)" "APP_SECRET_KEY")
if [ -z "$APP_SECRET_KEY" ]; then
    APP_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
    echo "   Generada: $APP_SECRET_KEY"
fi

DB_PASSWORD=$(ask_value "Contraseña de PostgreSQL (Enter para generar una aleatoria)" "DB_PASSWORD")
if [ -z "$DB_PASSWORD" ]; then
    DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")
    echo "   Generada: $DB_PASSWORD"
fi

DOMAIN=$(ask_value "Dominio (ej: pogo-lab.tooltician.com, o deja vacío si no tienes aún)" "DOMAIN")

if [ -z "${ALLOWED_HOSTS:-}" ] || [ "${ALLOWED_HOSTS:-}" = "__PLACEHOLDER__" ]; then
    ALLOWED_HOSTS="pogo-lab.tooltician.com,www.pogo-lab.tooltician.com"
    if [ -n "${DOMAIN:-}" ]; then
        ALLOWED_HOSTS="$DOMAIN,www.$DOMAIN"
    fi
fi

DEFAULT_FROM_EMAIL=$(ask_value "Email from (ej: carlos@tooltician.com)" "DEFAULT_FROM_EMAIL")
if [ -z "$DEFAULT_FROM_EMAIL" ]; then
    DEFAULT_FROM_EMAIL="carlos@tooltician.com"
fi

# ── 9. Escribir .env-oci ──────────────────────────────────────
echo ""
echo "── Escribiendo .env-oci ───────────────────────"

cat > "$DOT_ENV" << EOF
# ═══════════════════════════════════════════════════════════
# Pogo-lab — Configuración de despliegue en OCI
# Generado: $(date -Iseconds)
# ═══════════════════════════════════════════════════════════

OCI_TENANCY_OCID=$OCI_TENANCY_OCID
OCI_USER_OCID=$OCI_USER_OCID
OCI_FINGERPRINT=$OCI_FINGERPRINT
OCI_PRIVATE_KEY_PATH=$ROOT_DIR/infra/keys/oci_api_key.pem
OCI_REGION=$OCI_REGION
OCI_COMPARTMENT_OCID=$OCI_COMPARTMENT_OCID
OCI_SUBNET_OCID=$OCI_SUBNET_OCID

OCI_VM_SHAPE=VM.Standard.A1.Flex
# Límite Always Free vigente. Para 4/24 hay que sobreescribir ambas variables
# de forma explícita y aceptar el consumo PAYG que exceda esta asignación.
OCI_VM_OCPUS=2
OCI_VM_MEMORY_GB=12
OCI_VM_DISK_GB=100
OCI_VM_DISPLAY_NAME=pogo-lab-prod
OCI_VM_OS_IMAGE=Canonical Ubuntu 22.04

GITHUB_REPO_URL=$GITHUB_REPO_URL
GITHUB_DEPLOY_PRIVATE_KEY_PATH=$ROOT_DIR/infra/keys/deploy_key

APP_SECRET_KEY=$APP_SECRET_KEY
DB_PASSWORD=$DB_PASSWORD
ALLOWED_HOSTS=$ALLOWED_HOSTS
DOMAIN=$DOMAIN
DEFAULT_FROM_EMAIL=$DEFAULT_FROM_EMAIL
EOF

echo ""
echo "✅ .env-oci creado en: $DOT_ENV"
echo ""

# ── 10. Validación rápida ─────────────────────────────────────
echo "── Validando ──────────────────────────────────"
echo ""

MISSING=""

[ -z "$OCI_TENANCY_OCID" ] && MISSING="$MISSING  - OCI_TENANCY_OCID\n"
[ -z "$OCI_USER_OCID" ] && MISSING="$MISSING  - OCI_USER_OCID\n"
[ -z "$OCI_FINGERPRINT" ] && MISSING="$MISSING  - OCI_FINGERPRINT\n"
[ -z "$OCI_REGION" ] && MISSING="$MISSING  - OCI_REGION\n"
[ -z "$GITHUB_REPO_URL" ] && MISSING="$MISSING  - GITHUB_REPO_URL\n"

if [ -n "$MISSING" ]; then
    echo "⚠️  Faltan estos valores:"
    echo -e "$MISSING"
    echo "   Vuelve a ejecutar bin/assist-oci.sh para completarlos."
else
    echo "✅ Todas las variables requeridas están configuradas."
    echo ""
    echo "   Siguiente paso:"
    echo "   ./bin/setup-oci.sh"
    echo ""
    echo "   Ese script creará la VM ARM Ampere A1 en OCI,"
    echo "   instalará Docker, clonará el repo y desplegará la app."
fi
