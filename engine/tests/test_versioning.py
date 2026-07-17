"""Tests para engine/versioning.py — versionado del engine."""

from engine.versioning import ALGORITHM_VERSION, SCHEMA_VERSION, algorithm_version, schema_version


class TestAlgorithmVersion:
    def test_algorithm_version_is_string(self):
        assert isinstance(algorithm_version(), str)
        assert len(algorithm_version()) > 0

    def test_algorithm_version_equals_constant(self):
        assert algorithm_version() == ALGORITHM_VERSION
        assert ALGORITHM_VERSION == "0.1.0-dev"


class TestSchemaVersion:
    def test_schema_version_is_string(self):
        assert isinstance(schema_version(), str)
        assert len(schema_version()) > 0

    def test_schema_version_equals_constant(self):
        assert schema_version() == SCHEMA_VERSION
        assert SCHEMA_VERSION == "1.0"
