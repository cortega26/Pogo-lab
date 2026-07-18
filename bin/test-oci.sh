#!/usr/bin/env bash
set -euo pipefail
echo "=== Cargando .env-oci ==="
set -a
source "$(dirname "$0")/../.env-oci"
set +a

echo "=== Verificando OCI ==="
export SUPPRESS_LABEL_WARNING=True
if oci iam region list --all > /dev/null 2>&1; then
    echo "OCI OK: autenticación válida"
else
    echo "OCI FALLO: código de salida = $?"
    echo "Intentando sin redirección para ver el error:"
    SUPPRESS_LABEL_WARNING=True oci iam region list --all 2>&1 | head -3
fi
