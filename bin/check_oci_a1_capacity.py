#!/usr/bin/env python3
"""Consulta la capacidad de una configuración Ampere A1 sin crear una instancia."""

from __future__ import annotations

import json
import math
import os
import sys
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

AVAILABLE_STATUS = "AVAILABLE"
Status = Literal["available", "unavailable"]


@dataclass(frozen=True)
class CapacitySummary:
    """Resultado reducido y seguro para usar en la automatización."""

    status: Status
    available_fault_domains: tuple[str, ...]
    fault_domain_statuses: tuple[tuple[str, str], ...]


def parse_shape_configuration(ocpus_raw: str, memory_gb_raw: str) -> tuple[float, float]:
    """Valida la configuración flexible recibida por variables de entorno."""
    try:
        ocpus = float(ocpus_raw)
        memory_gb = float(memory_gb_raw)
    except ValueError as exc:
        raise ValueError("OCI_A1_OCPUS y OCI_A1_MEMORY_GB deben ser números.") from exc

    if not all(math.isfinite(value) and value > 0 for value in (ocpus, memory_gb)):
        raise ValueError("OCI_A1_OCPUS y OCI_A1_MEMORY_GB deben ser positivos y finitos.")

    return ocpus, memory_gb


def summarize_availability(entries: Iterable[tuple[str, str]]) -> CapacitySummary:
    """Marca disponible solo cuando OCI confirma capacidad en un fault domain."""
    statuses = tuple(entries)
    available_fault_domains = tuple(
        fault_domain
        for fault_domain, availability_status in statuses
        if availability_status == AVAILABLE_STATUS
    )
    status: Status = "available" if available_fault_domains else "unavailable"
    return CapacitySummary(status, available_fault_domains, statuses)


def get_required_environment(environ: Mapping[str, str], name: str) -> str:
    """Obtiene una variable requerida sin incluir su valor en mensajes de error."""
    value = environ.get(name, "").strip()
    if not value:
        raise ValueError(f"Falta la variable de entorno requerida: {name}.")
    return value


def build_oci_config(environ: Mapping[str, str]) -> dict[str, str]:
    """Construye la configuración de OCI a partir de secretos del entorno."""
    return {
        "user": get_required_environment(environ, "OCI_USER_OCID"),
        "tenancy": get_required_environment(environ, "OCI_TENANCY_OCID"),
        "fingerprint": get_required_environment(environ, "OCI_FINGERPRINT"),
        "key_file": get_required_environment(environ, "OCI_PRIVATE_KEY_PATH"),
        "region": get_required_environment(environ, "OCI_REGION"),
    }


def resolve_compartment_id(environ: Mapping[str, str], config: Mapping[str, str]) -> str:
    """Usa la tenancy cuando el compartimento opcional no fue configurado."""
    return environ.get("OCI_COMPARTMENT_OCID", "").strip() or config["tenancy"]


def check_capacity(
    config: dict[str, str],
    compartment_id: str,
    ocpus: float,
    memory_gb: float,
) -> CapacitySummary:
    """Solicita a OCI un informe de capacidad para todos los fault domains de la región."""
    try:
        import oci
        from oci.core.models import (
            CapacityReportInstanceShapeConfig,
            CreateCapacityReportShapeAvailabilityDetails,
            CreateComputeCapacityReportDetails,
        )
    except ImportError as exc:
        raise RuntimeError("Falta el paquete 'oci'. Instala las dependencias del monitor.") from exc

    oci.config.validate_config(config)
    identity = oci.identity.IdentityClient(config)
    availability_domains = identity.list_availability_domains(config["tenancy"]).data
    if not availability_domains:
        raise RuntimeError("OCI no devolvió ningún availability domain para la tenancy.")

    compute = oci.core.ComputeClient(config)
    all_statuses: list[tuple[str, str]] = []
    for availability_domain in availability_domains:
        fault_domains = identity.list_fault_domains(
            config["tenancy"], availability_domain.name
        ).data
        if not fault_domains:
            raise RuntimeError(
                "OCI no devolvió fault domains para "
                f"el availability domain {availability_domain.name}."
            )

        shape_availabilities = [
            CreateCapacityReportShapeAvailabilityDetails(
                fault_domain=fault_domain.name,
                instance_shape="VM.Standard.A1.Flex",
                instance_shape_config=CapacityReportInstanceShapeConfig(
                    ocpus=ocpus,
                    memory_in_gbs=memory_gb,
                ),
            )
            for fault_domain in fault_domains
        ]
        report = compute.create_compute_capacity_report(
            CreateComputeCapacityReportDetails(
                compartment_id=compartment_id,
                availability_domain=availability_domain.name,
                shape_availabilities=shape_availabilities,
            )
        ).data
        all_statuses.extend(
            (entry.fault_domain, entry.availability_status) for entry in report.shape_availabilities
        )

    return summarize_availability(all_statuses)


def publish_github_output(summary: CapacitySummary) -> None:
    """Expone el estado a GitHub Actions cuando el runner ofrece GITHUB_OUTPUT."""
    github_output = os.environ.get("GITHUB_OUTPUT")
    if not github_output:
        return

    output_path = Path(github_output)
    available_fault_domains = ",".join(summary.available_fault_domains)
    with output_path.open("a", encoding="utf-8") as output_file:
        output_file.write(f"status={summary.status}\n")
        output_file.write(f"available_fault_domains={available_fault_domains}\n")


def main() -> int:
    """Ejecuta la consulta y escribe un resultado apto para humanos y Actions."""
    try:
        config = build_oci_config(os.environ)
        compartment_id = resolve_compartment_id(os.environ, config)
        ocpus, memory_gb = parse_shape_configuration(
            os.environ.get("OCI_A1_OCPUS", "2"),
            os.environ.get("OCI_A1_MEMORY_GB", "12"),
        )
        summary = check_capacity(config, compartment_id, ocpus, memory_gb)
    except Exception as exc:  # La CLI debe devolver un error accionable, sin secretos.
        sys.stderr.write(f"Error al consultar la capacidad A1: {exc}\n")
        return 1

    result = {
        "shape": "VM.Standard.A1.Flex",
        "ocpus": ocpus,
        "memory_gb": memory_gb,
        **asdict(summary),
    }
    sys.stdout.write(f"{json.dumps(result, ensure_ascii=False)}\n")
    publish_github_output(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
