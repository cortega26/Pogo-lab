#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# Pogo-lab — Provisionamiento de VM en OCI y despliegue inicial
#
# Requisitos:
#   1. Ejecutar bin/assist-oci.sh primero (genera .env-oci + keys)
#   2. Deploy key pública añadida a GitHub (Settings → Deploy Keys)
#   3. API Key pública subida a OCI (Profile → API Keys)
#
# Uso: ./bin/setup-oci.sh
# ═══════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DOT_ENV="$ROOT_DIR/.env-oci"

echo "╔══════════════════════════════════════════════╗"
echo "║    Pogo-lab — Setup OCI VM + Deploy           ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Load .env-oci ─────────────────────────────────────────────
if [ ! -f "$DOT_ENV" ]; then
    echo "❌ No se encuentra .env-oci. Ejecuta primero: bin/assist-oci.sh"
    exit 1
fi

set -a
source "$DOT_ENV"
set +a

# ── Validate required vars ────────────────────────────────────
validate() {
    local var="$1"
    if [ -z "${!var:-}" ]; then
        echo "❌ Falta $var en .env-oci. Ejecuta: bin/assist-oci.sh"
        exit 1
    fi
}

validate OCI_TENANCY_OCID
validate OCI_USER_OCID
validate OCI_FINGERPRINT
validate OCI_REGION
validate OCI_COMPARTMENT_OCID
validate GITHUB_REPO_URL

# ── Configure OCI CLI ─────────────────────────────────────────
echo ""
echo "── Configurando OCI CLI ───────────────────────"
OCI_HOME_REGION="${OCI_HOME_REGION:-sa-santiago-1}"
# Los recursos Always Free SOLO existen en la región home. El destino de
# creación debe ser la home region; si no, con cuenta gratuita falla y con
# PAYG factura callado. Por eso el default de OCI_REGION es la home region.
OCI_REGION="${OCI_REGION:-$OCI_HOME_REGION}"

echo "   Home region: ${OCI_HOME_REGION}"
echo "   Target region (creación de recursos): ${OCI_REGION}"

mkdir -p ~/.oci

cat > ~/.oci/config << EOF
[DEFAULT]
user=${OCI_USER_OCID}
fingerprint=${OCI_FINGERPRINT}
tenancy=${OCI_TENANCY_OCID}
region=${OCI_HOME_REGION}
key_file=${OCI_PRIVATE_KEY_PATH}
EOF

chmod 600 ~/.oci/config

echo "   ✅ ~/.oci/config creado"

# Verify OCI auth (always against home region for new accounts)
echo "   Verificando autenticación OCI..."
export SUPPRESS_LABEL_WARNING=True
set +e
oci iam region list --all --region "$OCI_HOME_REGION" > /dev/null 2>&1
AUTH_EXIT=$?
set -e
if [ $AUTH_EXIT -ne 0 ]; then
    echo "   ❌ Falló la autenticación con OCI (exit=$AUTH_EXIT)."
    echo ""
    echo "   Diagnóstico:"
    echo "   - Home region: $OCI_HOME_REGION"
    echo "   - Config file:"
    cat ~/.oci/config | sed 's/^/     /'
    echo ""
    echo "   Error detallado:"
    SUPPRESS_LABEL_WARNING=True oci iam region list --all --region "$OCI_HOME_REGION" 2>&1 | head -10 | sed 's/^/     /'
    echo ""
    echo "   Verifica:"
    echo "   - Que la API key pública esté subida en: Profile → API Keys → Add API Key"
    echo "   - Que el fingerprint en .env-oci coincida con el de la consola"
    echo "   - Que OCI_PRIVATE_KEY_PATH apunte a la clave privada existente"
    exit 1
fi
echo "   ✅ Autenticación OCI OK"

# ── Check availability of Always Free shape ───────────────────
echo ""
echo "── Verificando disponibilidad ARM Ampere A1 ────"

# List availability domains
AD=$(oci iam availability-domain list \
    --compartment-id "$OCI_TENANCY_OCID" \
    --region "$OCI_REGION" \
    --query 'data[0].name' \
    --raw-output 2>/dev/null)

if [ -z "$AD" ]; then
    echo "   ❌ No se pudo obtener el availability domain. Revisa la región."
    exit 1
fi
echo "   Availability domain: $AD"

# ── Create or reuse VCN + subnet ──────────────────────────────
echo ""
echo "── Configurando red (VCN + subnet) ───────────"

VCN_NAME="pogo-lab-vcn"

if [ -n "${OCI_SUBNET_OCID:-}" ]; then
    echo "   Usando subnet existente: $OCI_SUBNET_OCID"
    SUBNET_OCID="$OCI_SUBNET_OCID"
else
    # Check if VCN exists
    VCN_OCID=$(oci network vcn list \
        --region "$OCI_REGION" \
        --compartment-id "$OCI_COMPARTMENT_OCID" \
        --display-name "$VCN_NAME" \
        --query 'data[0].id' \
        --raw-output 2>/dev/null || echo "")

    if [ -z "$VCN_OCID" ]; then
        echo "   Creando VCN '$VCN_NAME'..."
        VCN_OCID=$(oci network vcn create \
            --region "$OCI_REGION" \
            --compartment-id "$OCI_COMPARTMENT_OCID" \
            --display-name "$VCN_NAME" \
            --cidr-block "10.0.0.0/16" \
            --query 'data.id' \
            --raw-output)
        echo "   ✅ VCN creado: $VCN_OCID"
    else
        echo "   VCN existente: $VCN_OCID"
    fi

    # Internet Gateway
    IG_OCID=$(oci network internet-gateway list \
        --region "$OCI_REGION" \
        --compartment-id "$OCI_COMPARTMENT_OCID" \
        --vcn-id "$VCN_OCID" \
        --query 'data[0].id' \
        --raw-output 2>/dev/null || echo "")

    if [ -z "$IG_OCID" ]; then
        IG_OCID=$(oci network internet-gateway create \
            --region "$OCI_REGION" \
            --compartment-id "$OCI_COMPARTMENT_OCID" \
            --vcn-id "$VCN_OCID" \
            --is-enabled true \
            --display-name "pogo-lab-ig" \
            --query 'data.id' \
            --raw-output)
        echo "   ✅ Internet Gateway creado"
    fi

    # Route table
    RT_OCID=$(oci network route-table list \
        --region "$OCI_REGION" \
        --compartment-id "$OCI_COMPARTMENT_OCID" \
        --vcn-id "$VCN_OCID" \
        --query 'data[0].id' \
        --raw-output)

    # Add default route to IG
    oci network route-table update \
        --region "$OCI_REGION" \
        --rt-id "$RT_OCID" \
        --route-rules "[{\"destination\":\"0.0.0.0/0\",\"networkEntityId\":\"$IG_OCID\"}]" \
        --force 2>/dev/null || true

    # Security list (allow 22, 80, 443)
    SL_OCID=$(oci network security-list list \
        --region "$OCI_REGION" \
        --compartment-id "$OCI_COMPARTMENT_OCID" \
        --vcn-id "$VCN_OCID" \
        --query 'data[0].id' \
        --raw-output)

    echo "   Configurando reglas de firewall..."
    oci network security-list update \
        --region "$OCI_REGION" \
        --security-list-id "$SL_OCID" \
        --ingress-security-rules '[
            {"source":"0.0.0.0/0","protocol":"6","tcpOptions":{"destinationPortRange":{"min":22,"max":22}},"description":"SSH"},
            {"source":"0.0.0.0/0","protocol":"6","tcpOptions":{"destinationPortRange":{"min":80,"max":80}},"description":"HTTP"},
            {"source":"0.0.0.0/0","protocol":"6","tcpOptions":{"destinationPortRange":{"min":443,"max":443}},"description":"HTTPS"}
        ]' \
        --force 2>/dev/null || true

    # Subnet
    SUBNET_NAME="pogo-lab-subnet"
    SUBNET_OCID=$(oci network subnet list \
        --region "$OCI_REGION" \
        --compartment-id "$OCI_COMPARTMENT_OCID" \
        --vcn-id "$VCN_OCID" \
        --display-name "$SUBNET_NAME" \
        --query 'data[0].id' \
        --raw-output 2>/dev/null || echo "")

    if [ -z "$SUBNET_OCID" ]; then
        SUBNET_OCID=$(oci network subnet create \
            --region "$OCI_REGION" \
            --compartment-id "$OCI_COMPARTMENT_OCID" \
            --vcn-id "$VCN_OCID" \
            --cidr-block "10.0.1.0/24" \
            --display-name "$SUBNET_NAME" \
            --route-table-id "$RT_OCID" \
            --security-list-ids "[\"$SL_OCID\"]" \
            --query 'data.id' \
            --raw-output)
        echo "   ✅ Subnet creada: $SUBNET_OCID"
    else
        echo "   Subnet existente: $SUBNET_OCID"
    fi
fi

# ── Create VM ──────────────────────────────────────────────────
echo ""
echo "── Creando VM ARM Ampere A1 ───────────────────"

VM_NAME="${OCI_VM_DISPLAY_NAME:-pogo-lab-prod}"
VM_OCPUS="${OCI_VM_OCPUS:-4}"
VM_MEMORY="${OCI_VM_MEMORY_GB:-24}"
VM_DISK="${OCI_VM_DISK_GB:-100}"

# Check if VM already exists
VM_OCID=$(oci compute instance list \
    --region "$OCI_REGION" \
    --compartment-id "$OCI_COMPARTMENT_OCID" \
    --display-name "$VM_NAME" \
    --lifecycle-state RUNNING \
    --query 'data[0].id' \
    --raw-output 2>/dev/null || echo "")

if [ -n "$VM_OCID" ]; then
    echo "   VM ya existe y está corriendo: $VM_OCID"
else
    # Get latest Ubuntu image
    IMAGE_OCID=$(oci compute image list \
        --region "$OCI_REGION" \
        --compartment-id "$OCI_COMPARTMENT_OCID" \
        --operating-system "Canonical Ubuntu" \
        --operating-system-version "22.04" \
        --shape "VM.Standard.A1.Flex" \
        --sort-by TIMECREATED \
        --query 'data[0].id' \
        --raw-output 2>/dev/null)

    if [ -z "$IMAGE_OCID" ]; then
        echo "   Buscando imagen Ubuntu más reciente..."
        IMAGE_OCID=$(oci compute image list \
            --region "$OCI_REGION" \
            --compartment-id "$OCI_COMPARTMENT_OCID" \
            --operating-system "Canonical Ubuntu" \
            --shape "VM.Standard.A1.Flex" \
            --sort-by TIMECREATED \
            --query 'data[0].id' \
            --raw-output)
    fi

    echo "   Image OCID: $IMAGE_OCID"

    # Generate SSH key pair for VM access
    VM_KEY_PATH="$ROOT_DIR/infra/keys/vm_key"
    if [ ! -f "$VM_KEY_PATH" ]; then
        ssh-keygen -t ed25519 -C "pogo-lab-vm" -N "" -f "$VM_KEY_PATH" -q
    fi

    # La A1 gratuita suele fallar con "Out of host capacity" (transitorio).
    # Reintentamos con backoff hasta conseguir hueco. Configurable con
    # A1_RETRY_SECONDS (por defecto 60). Ctrl-C para abortar.
    echo "   Creando A1 con reintentos (Out of host capacity es transitorio)..."
    ATTEMPT=0
    until VM_OCID=$(oci compute instance launch \
        --region "$OCI_REGION" \
        --compartment-id "$OCI_COMPARTMENT_OCID" \
        --availability-domain "$AD" \
        --display-name "$VM_NAME" \
        --shape "VM.Standard.A1.Flex" \
        --shape-config "{\"ocpus\":${VM_OCPUS},\"memoryInGBs\":${VM_MEMORY}}" \
        --image-id "$IMAGE_OCID" \
        --boot-volume-size-in-gbs "$VM_DISK" \
        --subnet-id "$SUBNET_OCID" \
        --assign-public-ip true \
        --ssh-authorized-keys-file "$VM_KEY_PATH.pub" \
        --wait-for-state RUNNING \
        --query 'data.id' \
        --raw-output 2>/tmp/pogo_a1_err); do
        ATTEMPT=$((ATTEMPT + 1))
        # Solo reintentar capacidad transitoria; abortar en errores reales
        # (shape inexistente en la región, permisos, cuota agotada, etc.).
        if ! grep -qiE 'capacity|LimitExceeded|InternalError|TooManyRequests' /tmp/pogo_a1_err; then
            echo "   ❌ Error no transitorio al crear la A1:"
            sed 's/^/     /' /tmp/pogo_a1_err
            rm -f /tmp/pogo_a1_err
            exit 1
        fi
        echo "   Sin capacidad A1 (intento $ATTEMPT). Reintento en ${A1_RETRY_SECONDS:-60} s... [Ctrl-C para abortar]"
        sleep "${A1_RETRY_SECONDS:-60}"
    done
    rm -f /tmp/pogo_a1_err

    echo "   ✅ A1 creada tras $((ATTEMPT + 1)) intento(s): $VM_OCID"
fi

# ── Get public IP ─────────────────────────────────────────────
PUBLIC_IP=$(oci compute instance list-vnics \
    --region "$OCI_REGION" \
    --instance-id "$VM_OCID" \
    --query 'data[0]."public-ip"' \
    --raw-output)

echo ""
echo "   IP pública: $PUBLIC_IP"

# ── Wait for SSH ──────────────────────────────────────────────
echo ""
echo "── Esperando que SSH esté disponible ──────────"

for i in $(seq 1 30); do
    if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
        -i "$VM_KEY_PATH" "ubuntu@$PUBLIC_IP" "echo ok" 2>/dev/null; then
        echo "   ✅ SSH disponible"
        break
    fi
    echo "   Intentando ($i/30)..."
    sleep 10
done

# ── Install Docker + Compose on VM ────────────────────────────
echo ""
echo "── Instalando Docker en la VM ─────────────────"

ssh -o StrictHostKeyChecking=no -i "$VM_KEY_PATH" "ubuntu@$PUBLIC_IP" << 'DOCKEREOF'
set -e
sudo apt-get update -qq
sudo apt-get install -y -qq ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -qq
sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker ubuntu
echo "Docker instalado: $(docker --version)"
DOCKEREOF

echo "   ✅ Docker instalado"

# ── Clone repo on VM ──────────────────────────────────────────
echo ""
echo "── Clonando repo en la VM ────────────────────"

# Copy deploy key to VM
scp -o StrictHostKeyChecking=no -i "$VM_KEY_PATH" \
    "$GITHUB_DEPLOY_PRIVATE_KEY_PATH" "ubuntu@$PUBLIC_IP:/home/ubuntu/.ssh/deploy_key"
scp -o StrictHostKeyChecking=no -i "$VM_KEY_PATH" \
    "$GITHUB_DEPLOY_PRIVATE_KEY_PATH.pub" "ubuntu@$PUBLIC_IP:/home/ubuntu/.ssh/deploy_key.pub"

ssh -o StrictHostKeyChecking=no -i "$VM_KEY_PATH" "ubuntu@$PUBLIC_IP" << GITEOF
set -e
chmod 600 ~/.ssh/deploy_key
cat > ~/.ssh/config << 'SSHEOF'
Host github.com
    IdentityFile ~/.ssh/deploy_key
    StrictHostKeyChecking no
SSHEOF
chmod 600 ~/.ssh/config

if [ -d /opt/pogo-lab ]; then
    cd /opt/pogo-lab && git pull origin main
else
    sudo mkdir -p /opt/pogo-lab
    sudo chown ubuntu:ubuntu /opt/pogo-lab
    git clone --depth 1 ${GITHUB_REPO_URL} /opt/pogo-lab
fi
echo "Repo clonado en /opt/pogo-lab"
GITEOF

echo "   ✅ Repo clonado"

# ── Create .env.prod on VM ────────────────────────────────────
echo ""
echo "── Configurando .env.prod en la VM ───────────"

ssh -o StrictHostKeyChecking=no -i "$VM_KEY_PATH" "ubuntu@$PUBLIC_IP" << EOF
cat > /opt/pogo-lab/.env.prod << PRODEOF
SECRET_KEY=${APP_SECRET_KEY}
ALLOWED_HOSTS=${ALLOWED_HOSTS:-$PUBLIC_IP}
LANGUAGE_CODE=es
TIME_ZONE=UTC
DB_PASSWORD=${DB_PASSWORD}
DEFAULT_FROM_EMAIL=${DEFAULT_FROM_EMAIL:-noreply@pogo-lab.com}
CACHE_URL=locmem://
PRODEOF
chmod 600 /opt/pogo-lab/.env.prod
echo ".env.prod creado"
EOF

echo "   ✅ .env.prod configurado"

# ── Deploy ─────────────────────────────────────────────────────
echo ""
echo "── Desplegando aplicación ────────────────────"

ssh -o StrictHostKeyChecking=no -i "$VM_KEY_PATH" "ubuntu@$PUBLIC_IP" << 'DEPLOYEOF'
set -e
cd /opt/pogo-lab
docker compose -f compose.prod.yaml up -d --build --remove-orphans
docker compose -f compose.prod.yaml exec -T web python manage.py migrate --noinput
docker compose -f compose.prod.yaml exec -T web python manage.py collectstatic --noinput
docker system prune -f
echo "Despliegue completado"
DEPLOYEOF

echo "   ✅ App desplegada"

# ── Health check ───────────────────────────────────────────────
sleep 5
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "http://$PUBLIC_IP/healthz" || echo "000")
echo ""
echo "── Health check ───────────────────────────────"
echo "   GET http://$PUBLIC_IP/healthz → HTTP $HEALTH"

# ── GitHub Actions secrets ────────────────────────────────────
echo ""
echo "── GitHub Actions Secrets (pendiente) ────────"
echo ""
echo "   Agrega estos secretos en:"
echo "   https://github.com/<tu-repo>/settings/secrets/actions"
echo ""
echo "   Nombre               Valor"
echo "   ──────────────────   ──────────────────────"
echo "   OCI_HOST             $PUBLIC_IP"
echo "   OCI_USER             ubuntu"
echo "   OCI_SSH_KEY          (contenido de $VM_KEY_PATH)"
echo ""

# ── Summary ────────────────────────────────────────────────────
echo "╔══════════════════════════════════════════════╗"
echo "║ ✅ Setup completo                             ║"
echo "╠══════════════════════════════════════════════╣"
echo "║ IP:       $PUBLIC_IP"
echo "║ VM Key:   $VM_KEY_PATH"
echo "║ Health:   HTTP $HEALTH"
echo "║                                              ║"
echo "║ Siguientes pasos manuales:                   ║"
echo "║ 1. Apuntar DNS (A record) → $PUBLIC_IP"
echo "║ 2. Configurar secretos en GitHub Actions     ║"
echo "║ 3. Configurar SSL (Let's Encrypt) en la VM   ║"
echo "║ 4. Backup automático: cron + bin/backup.sh   ║"
echo "╚══════════════════════════════════════════════╝"
