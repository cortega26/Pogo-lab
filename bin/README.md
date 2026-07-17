# Scripts de operación

## Backup (`backup.sh`)

Genera un dump comprimido de la base de datos PostgreSQL.

```bash
# Con DATABASE_URL explícita:
DATABASE_URL=postgres://pogo:pogo@localhost:5433/pogo ./bin/backup.sh

# Cargando .env:
export $(grep -v '^#' .env | xargs)
./bin/backup.sh
```

Salida: `pogo-lab-backup-YYYYMMDDTHHMMSSZ.sql.gz` en el directorio actual.

## Restore (`restore.sh`)

Restaura un backup (.sql o .sql.gz) en la base de datos de destino.

```bash
DATABASE_URL=postgres://pogo:pogo@localhost:5433/pogo ./bin/restore.sh pogo-lab-backup-20250101T000000Z.sql.gz
```

El script pide confirmación antes de sobrescribir.

## Variables de entorno requeridas

- `DATABASE_URL`: string de conexión PostgreSQL (`postgres://user:pass@host:port/db`)

## PENDIENTE-HUMANO

- [ ] Verificar la restauración en el entorno de producción real.
- [ ] Configurar backups automáticos diarios (cron, systemd timer, o scheduler del PaaS).
- [ ] Subir backups a almacenamiento externo (S3, GCS, Backblaze B2).
- [ ] Probar el procedimiento completo de disaster recovery al menos una vez.
