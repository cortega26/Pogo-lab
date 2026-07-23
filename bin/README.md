# Scripts de operación

## Backup (`backup.sh`)

Genera un dump comprimido, privado y atómico de la base de datos PostgreSQL.

```bash
# Con DATABASE_URL explícita:
DATABASE_URL=postgres://pogo:pogo@localhost:5433/pogo ./bin/backup.sh

# Cargando .env:
export $(grep -v '^#' .env | xargs)
./bin/backup.sh
```

Salida: `pogo-lab-backup-YYYYMMDDTHHMMSSZ.sql.gz` en el directorio actual.
Usa `BACKUP_DIR` para cambiar el destino y `BACKUP_RETENTION_DAYS` para eliminar
automáticamente backups antiguos.

## Restore (`restore.sh`)

Restaura un backup (.sql o .sql.gz) en la base de datos de destino.

```bash
DATABASE_URL=postgres://pogo:pogo@localhost:5433/pogo ./bin/restore.sh pogo-lab-backup-20250101T000000Z.sql.gz
```

El script pide confirmación antes de sobrescribir y no imprime credenciales.
Para automatización controlada se puede definir `RESTORE_ASSUME_YES=1`.

## Backup diario con systemd

En la VM de producción:

```bash
sudo ./bin/install-backup-timer.sh
sudo systemctl start pogo-lab-backup.service
sudo systemctl status pogo-lab-backup.service
```

El timer conserva 14 días en `/var/backups/pogo-lab` y recupera ejecuciones
perdidas después de un reinicio.

## Variables de entorno requeridas

- `DATABASE_URL`: string de conexión PostgreSQL (`postgres://user:pass@host:port/db`)

## Operación externa pendiente

- [ ] Subir backups a OCI Object Storage (capa gratuita, 10 GB).
- [ ] Repetir el procedimiento completo de disaster recovery periódicamente.

## Monitor de capacidad OCI Ampere A1

El workflow [`oci-a1-capacity-monitor.yml`](../.github/workflows/oci-a1-capacity-monitor.yml)
consulta cada cinco minutos la capacidad de `VM.Standard.A1.Flex`; no crea instancias, redes ni discos.
Cuando OCI responde `AVAILABLE`, abre un issue de GitHub y, si se configuró, envía un webhook compatible
con Slack o Discord. Al volver a no haber capacidad cierra el issue para que una disponibilidad futura
genere una alerta nueva.

Configura estos **Actions secrets** en el repositorio:

- `OCI_USER_OCID`, `OCI_TENANCY_OCID`, `OCI_FINGERPRINT`, `OCI_PRIVATE_KEY` y `OCI_REGION`.
- `OCI_COMPARTMENT_OCID` es opcional; si se omite se consulta el compartimento raíz de la tenancy.
- `OCI_CAPACITY_WEBHOOK_URL` es opcional para la notificación adicional. Sin él, se usa el issue de GitHub;
  activa las notificaciones de *Issues* del repositorio para recibirlo por correo o en la aplicación.

El workflow vigila exclusivamente `2 OCPU / 12 GB`, la asignación Always Free vigente para A1. No acepta
variables de repositorio que cambien ese tamaño, para no convertir por error el monitor en una comprobación
de recursos PAYG.

GitHub ejecuta los cron aproximadamente cada cinco minutos, pero no garantiza puntualidad absoluta. El
workflow se activa una vez que el archivo esté en la rama por defecto; se puede probar antes desde
**Actions → Monitor de capacidad OCI A1 → Run workflow**.
