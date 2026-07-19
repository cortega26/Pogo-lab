#!/usr/bin/env bash
set -euo pipefail

# Instala el timer diario de backup en una VM con despliegue systemd.
# Uso: sudo ./bin/install-backup-timer.sh

if [ "$(id -u)" -ne 0 ]; then
    echo "Error: ejecuta este script como root." >&2
    exit 1
fi

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ENV_FILE="${POGO_ENV_FILE:-${ROOT_DIR}/.env}"
BACKUP_DIR="${POGO_BACKUP_DIR:-/var/backups/pogo-lab}"

if [ ! -f "${ENV_FILE}" ]; then
    echo "Error: no existe el archivo de entorno ${ENV_FILE}." >&2
    exit 1
fi

install -d -m 0700 -o ubuntu -g ubuntu "${BACKUP_DIR}"
install -m 0644 "${ROOT_DIR}/infra/systemd/pogo-lab-backup.service" /etc/systemd/system/
install -m 0644 "${ROOT_DIR}/infra/systemd/pogo-lab-backup.timer" /etc/systemd/system/

mkdir -p /etc/systemd/system/pogo-lab-backup.service.d
cat > /etc/systemd/system/pogo-lab-backup.service.d/local.conf <<EOF
[Service]
WorkingDirectory=${ROOT_DIR}
EnvironmentFile=${ENV_FILE}
Environment=BACKUP_DIR=${BACKUP_DIR}
EOF

systemctl daemon-reload
systemctl enable --now pogo-lab-backup.timer
echo "Timer de backup instalado. Próxima ejecución:"
systemctl list-timers pogo-lab-backup.timer --no-pager
