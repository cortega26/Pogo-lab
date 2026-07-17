"""Servicios de moderación.

Funciones para marcar observaciones y datasets como sospechosos/duplicados,
con auditoría (AuditEvent) en cada acción.
"""

from apps.audit.models import AuditEvent
from apps.contributions.models import DatasetVersion
from apps.trades.models import TradeObservation


def mark_observation(
    observation_id: int,
    state: str,
    reason: str = "",
    actor=None,
) -> TradeObservation:
    obs = TradeObservation.objects.get(pk=observation_id)
    previous_state = obs.state
    obs.state = state
    obs.exclusion_reason = reason
    obs.save(update_fields=["state", "exclusion_reason", "updated_at"])

    AuditEvent.log(
        verb=f"observation_marked_{state}",
        actor=actor,
        target_type="TradeObservation",
        target_id=obs.pk,
        metadata={"reason": reason, "previous_state": previous_state},
    )

    return obs


def mark_dataset_suspicious(
    dataset_id: int,
    reason: str = "",
    actor=None,
) -> DatasetVersion:
    version = DatasetVersion.objects.get(pk=dataset_id)
    AuditEvent.log(
        verb="dataset_marked_suspicious",
        actor=actor,
        target_type="DatasetVersion",
        target_id=version.pk,
        metadata={
            "reason": reason,
            "number": version.number,
            "row_count": version.row_count,
        },
    )
    return version
