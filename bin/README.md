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
