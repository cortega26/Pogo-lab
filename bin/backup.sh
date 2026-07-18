#!/usr/bin/env bash
set -euo pipefail

# --------------------------------------------------------------------------
# Pogo-lab — Backup de base de datos
#
# Uso:
#   DATABASE_URL=postgres://usuario:clave@host:puerto/bd ./bin/backup.sh
#
# O con un archivo .env:
#   export $(grep -v '^#' .env | xargs)
#   ./bin/backup.sh
#
# El script genera un archivo .sql.gz con timestamp en el directorio actual.
# También es compatible con la URL del compose.yaml local:
#   DATABASE_URL=postgres://pogo:pogo@localhost:5433/pogo ./bin/backup.sh
# --------------------------------------------------------------------------

if [ -z "${DATABASE_URL:-}" ]; then
    echo "Error: DATABASE_URL no está definida."
    echo "Ejemplo: export DATABASE_URL=postgres://usuario:clave@host:puerto/bd"
    exit 1
fi

TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
OUTPUT="pogo-lab-backup-${TIMESTAMP}.sql.gz"

echo "==> Iniciando backup en: ${OUTPUT}"
pg_dump "${DATABASE_URL}" | gzip > "${OUTPUT}"
echo "==> Backup completado: ${OUTPUT}"

# PENDIENTE-HUMANO: Configurar backups automáticos diarios en OCI (cron o systemd
# timer). Subir el backup a OCI Object Storage (capa gratuita, 10 GB).
