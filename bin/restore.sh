#!/usr/bin/env bash
set -euo pipefail

# --------------------------------------------------------------------------
# Pogo-lab — Restauración de base de datos
#
# Uso:
#   DATABASE_URL=postgres://usuario:clave@host:puerto/bd ./bin/restore.sh backup.sql.gz
#
# El archivo de backup puede estar comprimido (.gz) o sin comprimir (.sql).
# ATENCIÓN: Este script SOBRESCRIBE la base de datos de destino.
#            No ejecutar en producción sin verificar antes.
# --------------------------------------------------------------------------

if [ -z "${DATABASE_URL:-}" ]; then
    echo "Error: DATABASE_URL no está definida."
    exit 1
fi

if [ -z "${1:-}" ]; then
    echo "Uso: DATABASE_URL=postgres://... ./bin/restore.sh <archivo_backup>"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: el archivo ${BACKUP_FILE} no existe."
    exit 1
fi

echo "==> ADVERTENCIA: Vas a sobrescribir la base de datos configurada."
if [ "${RESTORE_ASSUME_YES:-0}" != "1" ]; then
    echo "==> Presiona Ctrl-C para cancelar o Enter para continuar..."
    read -r _UNUSED
fi

echo "==> Restaurando desde: ${BACKUP_FILE}"

if [[ "${BACKUP_FILE}" == *.gz ]]; then
    gunzip -c "${BACKUP_FILE}" | psql --set ON_ERROR_STOP=1 --single-transaction "${DATABASE_URL}"
else
    psql --set ON_ERROR_STOP=1 --single-transaction "${DATABASE_URL}" < "${BACKUP_FILE}"
fi

echo "==> Restauración completada."

# Ejecutar migrate después de restaurar si el backup es de una versión anterior:
#   uv run python manage.py migrate --settings=config.settings.prod
