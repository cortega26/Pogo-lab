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
# El script genera un archivo .sql.gz con timestamp en BACKUP_DIR (directorio
# actual por defecto). Los archivos se crean de forma atómica y privada.
# También es compatible con la URL del compose.yaml local:
#   DATABASE_URL=postgres://pogo:pogo@localhost:5433/pogo ./bin/backup.sh
# --------------------------------------------------------------------------

if [ -z "${DATABASE_URL:-}" ]; then
    echo "Error: DATABASE_URL no está definida."
    echo "Ejemplo: export DATABASE_URL=postgres://usuario:clave@host:puerto/bd"
    exit 1
fi

TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
BACKUP_DIR="${BACKUP_DIR:-.}"
OUTPUT="${BACKUP_DIR%/}/pogo-lab-backup-${TIMESTAMP}.sql.gz"
TEMP_OUTPUT="${OUTPUT}.tmp"

umask 077
mkdir -p "${BACKUP_DIR}"
trap 'rm -f "${TEMP_OUTPUT}"' EXIT

echo "==> Iniciando backup en: ${OUTPUT}"
pg_dump "${DATABASE_URL}" | gzip > "${TEMP_OUTPUT}"
mv "${TEMP_OUTPUT}" "${OUTPUT}"
trap - EXIT
echo "==> Backup completado: ${OUTPUT}"

if [ -n "${BACKUP_RETENTION_DAYS:-}" ]; then
    find "${BACKUP_DIR}" -maxdepth 1 -type f \
        -name 'pogo-lab-backup-*.sql.gz' \
        -mtime "+${BACKUP_RETENTION_DAYS}" -delete
fi
