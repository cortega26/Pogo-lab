"""Pruebas unitarias del monitor de capacidad OCI, sin requerir credenciales."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parents[1] / "bin" / "check_oci_a1_capacity.py"


def load_monitor_module():
    spec = importlib.util.spec_from_file_location("oci_a1_capacity_monitor", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_validates_a1_shape_configuration() -> None:
    monitor = load_monitor_module()

    assert monitor.parse_shape_configuration("4", "24") == (4.0, 24.0)

    with pytest.raises(ValueError, match="positivos"):
        monitor.parse_shape_configuration("0", "24")


def test_summarizes_only_available_fault_domains() -> None:
    monitor = load_monitor_module()

    result = monitor.summarize_availability(
        [
            ("FAULT-DOMAIN-1", "OUT_OF_HOST_CAPACITY"),
            ("FAULT-DOMAIN-2", "AVAILABLE"),
            ("FAULT-DOMAIN-3", "UNKNOWN"),
        ]
    )

    assert result.status == "available"
    assert result.available_fault_domains == ("FAULT-DOMAIN-2",)


def test_marks_unavailable_when_no_fault_domain_can_host_the_shape() -> None:
    monitor = load_monitor_module()

    result = monitor.summarize_availability([("FAULT-DOMAIN-1", "OUT_OF_HOST_CAPACITY")])

    assert result.status == "unavailable"
    assert result.available_fault_domains == ()


def test_uses_tenancy_when_optional_compartment_is_empty() -> None:
    monitor = load_monitor_module()

    assert (
        monitor.resolve_compartment_id(
            {"OCI_COMPARTMENT_OCID": ""}, {"tenancy": "ocid1.tenancy.oc1..example"}
        )
        == "ocid1.tenancy.oc1..example"
    )
