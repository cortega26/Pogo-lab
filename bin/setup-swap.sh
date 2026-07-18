#!/usr/bin/env bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
# Pogo-lab — Configuración de swap en la VM
#
# Imprescindible en instancias de 1 GB de RAM (p. ej. la
# VM.Standard.E2.1.Micro de OCI): sin swap, `docker build` y las
# migraciones mueren por OOM (Out Of Memory).
#
# Idempotente: si ya hay swap del tamaño pedido, no hace nada.
#
# Uso (en la VM, como root):
#   sudo ./bin/setup-swap.sh [tamaño_GB]      # por defecto 2 GB
# ═══════════════════════════════════════════════════════════════

SIZE_GB="${1:-2}"
SWAPFILE="/swapfile"

if [ "$(id -u)" -ne 0 ]; then
    echo "❌ Ejecuta como root: sudo ./bin/setup-swap.sh ${SIZE_GB}"
    exit 1
fi

echo "── Configurando ${SIZE_GB} GB de swap ─────────────"

# ── ¿Ya existe swap suficiente? ───────────────────────────────
CURRENT_SWAP_MB=$(free -m | awk '/^Swap:/ {print $2}')
WANT_MB=$((SIZE_GB * 1024))

if [ "${CURRENT_SWAP_MB:-0}" -ge "$WANT_MB" ]; then
    echo "   ✅ Ya hay ${CURRENT_SWAP_MB} MB de swap activa (≥ ${WANT_MB} MB). Nada que hacer."
else
    # Desactivar y borrar swapfile previo si existiera (para redimensionar)
    if swapon --show=NAME --noheadings 2>/dev/null | grep -qx "$SWAPFILE"; then
        swapoff "$SWAPFILE"
    fi
    rm -f "$SWAPFILE"

    echo "   Creando ${SWAPFILE} de ${SIZE_GB} GB..."
    # fallocate es instantáneo; si el FS no lo soporta, cae a dd.
    if ! fallocate -l "${SIZE_GB}G" "$SWAPFILE" 2>/dev/null; then
        echo "   fallocate no disponible; usando dd (más lento)..."
        dd if=/dev/zero of="$SWAPFILE" bs=1M count="$((SIZE_GB * 1024))" status=progress
    fi

    chmod 600 "$SWAPFILE"
    mkswap "$SWAPFILE" >/dev/null
    swapon "$SWAPFILE"
    echo "   ✅ Swap activada."
fi

# ── Persistir en /etc/fstab ───────────────────────────────────
if ! grep -qE "^\s*${SWAPFILE}\s" /etc/fstab; then
    echo "${SWAPFILE} none swap sw 0 0" >> /etc/fstab
    echo "   ✅ Entrada añadida a /etc/fstab (persiste tras reinicio)."
fi

# ── Ajustar swappiness (servidor: usar swap solo bajo presión) ─
SYSCTL_FILE="/etc/sysctl.d/99-pogo-swap.conf"
cat > "$SYSCTL_FILE" << 'EOF'
vm.swappiness=10
vm.vfs_cache_pressure=50
EOF
sysctl -p "$SYSCTL_FILE" >/dev/null
echo "   ✅ vm.swappiness=10 aplicado."

echo ""
echo "── Estado de memoria ──────────────────────────"
free -h
