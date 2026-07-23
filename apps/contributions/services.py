"""Servicios de dominio para apps/contributions.

build_dataset_version: construye un snapshot anonimizado con inclusión AND
compound (state="valid" AND contribution_optin AND consentimiento activo).
Anonimiza excluyendo PII (notes, owner, timestamps exactos, country, dedup_hash).
Calcula checksum SHA-256 sobre contenido anonimizado canonicalizado.
"""

import hashlib
import json
from typing import Any

from apps.audit.models import AuditEvent
from apps.contributions.models import DataContributionConsent, DatasetVersion
from apps.trades.models import TradeObservation

DEFAULT_PIPELINE_VERSION = "1.0.0"


def _canonical_row(row: dict[str, Any]) -> str:
    """Serializa una fila anonimizada de forma canónica para el checksum."""
    return json.dumps(row, sort_keys=True, ensure_ascii=False, default=str)


def build_dataset_version(
    criteria: dict[str, Any] | None = None,
    pipeline_version: str = DEFAULT_PIPELINE_VERSION,
    consent_text_version: str = "1.0.0",
) -> DatasetVersion:
    """Construye una nueva versión de dataset comunitario anonimizado.

    INCLUSIÓN (AND compuesto, los tres):
      - observation.state == "valid"
      - observation.contribution_optin == True
      - owner tiene DataContributionConsent activo (scope="community_dataset")
        con consent_text_version coincidente (plan 052)

    ANONIMIZACIÓN por fila — solo campos no identificantes:
      - atk, iv_def (como "def"), hp
      - friendship_level, trade_type, is_lucky
      - ruleset_version (del ruleset_id asociado)
      - observed_month (YYYY-MM, bucket de mes)

    EXCLUYE explícitamente: notes, owner (id/email), timestamp exacto,
    country por fila, dedup_hash, pk/id de observación.

    CHECKSUM: SHA-256 sobre todas las filas anonimizadas, ordenadas de forma
    estable (por los propios campos anonimizados + observed_month), serializadas
    con sort_keys. Incluye pipeline_version en el contenido hasheado.

    ATOMICIDAD: selección, checksum, creación y audit en una transacción
    con select_for_update (plan 052).
    """
    from django.db import transaction

    criteria = criteria or _default_criteria()

    min_sample = criteria.get("min_sample", 30)
    scope = "community_dataset"

    with transaction.atomic():
        user_ids_with_consent = set(
            DataContributionConsent.objects.filter(
                scope=scope,
                is_active=True,
                consent_text_version=consent_text_version,
            ).values_list("user_id", flat=True)
        )

        qs = TradeObservation.objects.select_related("ruleset").filter(
            state="valid",
            contribution_optin=True,
            owner_id__in=user_ids_with_consent,
        )

        ruleset_versions: dict[int, int] = {}

        rows: list[dict[str, Any]] = []
        for obs in qs.iterator(chunk_size=1000):
            rs_id = obs.ruleset_id
            if rs_id is not None and rs_id not in ruleset_versions:
                ruleset_versions[rs_id] = obs.ruleset.version if obs.ruleset else 0

            rows.append(
                {
                    "atk": obs.atk,
                    "def": obs.iv_def,
                    "hp": obs.hp,
                    "friendship_level": obs.friendship_level,
                    "trade_type": obs.trade_type,
                    "is_lucky": obs.is_lucky,
                    "ruleset_version": ruleset_versions.get(obs.ruleset_id, 0)
                    if obs.ruleset_id
                    else 0,
                    "observed_month": obs.observed_at.strftime("%Y-%m"),
                }
            )

        row_count = len(rows)
        min_sample_met = row_count >= min_sample

        sorted_rows = sorted(rows, key=_canonical_row)
        canonicalized = "\n".join(_canonical_row(r) for r in sorted_rows)
        checksum_input = f"{pipeline_version}\n{canonicalized}"
        checksum = hashlib.sha256(checksum_input.encode("utf-8")).hexdigest()

        latest = DatasetVersion.objects.select_for_update().order_by("-number").first()
        next_number = (latest.number + 1) if latest else 1

        publication_status = "public" if min_sample_met else "draft"

        version = DatasetVersion.objects.create(
            number=next_number,
            criteria=criteria,
            min_sample_met=min_sample_met,
            row_count=row_count,
            checksum=checksum,
            is_public=min_sample_met,
            publication_status=publication_status,
            consent_text_version=consent_text_version,
            pipeline_version=pipeline_version,
            anonymized_rows=rows,
        )

        version.rows_cache = rows  # type: ignore[attr-defined]

        AuditEvent.log(
            verb="dataset_built",
            target_type="DatasetVersion",
            target_id=version.pk,
            metadata={
                "number": version.number,
                "row_count": row_count,
                "min_sample_met": min_sample_met,
                "pipeline_version": pipeline_version,
                "consent_text_version": consent_text_version,
                "publication_status": publication_status,
            },
        )

    return version


def _default_criteria() -> dict[str, Any]:
    return {"min_sample": 30, "state_filter": "valid"}


def aggregate_community_distribution(
    dataset_version: DatasetVersion,
) -> list[dict[str, Any]]:
    """Agregado comunitario pooled (sin owner).

    Delega en apps.analysis.services.compute_pooled_statistics, que reutiliza
    la misma disciplina que run_personal_analysis (M5): agrupa por
    (is_lucky, friendship_level, ruleset), resuelve el piso con
    floor_for_ruleset, y ejecuta las mismas pruebas del engine.
    """
    from apps.analysis.services import compute_pooled_statistics

    rows = dataset_version.anonymized_rows or getattr(dataset_version, "rows_cache", [])
    if not rows:
        return []

    return compute_pooled_statistics(rows)
