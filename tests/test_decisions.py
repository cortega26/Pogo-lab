"""Tests para apps/decisions — recomendaciones trazables y lenguaje honesto."""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.decisions.models import DecisionRecommendation, DecisionRule

User = get_user_model()


@pytest.mark.django_db
class TestDecisionRule:
    def test_create_rule(self):
        rule = DecisionRule.objects.create(
            key="test_rule",
            version="1.0",
            condition_spec={"min_n": 50},
            message_key="decision.test_rule",
            severity="warning",
        )
        assert rule.key == "test_rule"
        assert rule.version == "1.0"
        assert rule.is_active

    def test_rule_uniqueness(self):
        DecisionRule.objects.create(key="unique_rule", version="1.0")
        with pytest.raises(IntegrityError):
            DecisionRule.objects.create(key="unique_rule", version="2.0")


@pytest.mark.django_db
class TestDecisionRecommendation:
    def test_recommendation_traceable(self):
        """Recomendación trazable a rule.key + version."""
        rule = DecisionRule.objects.create(
            key="insufficient_sample",
            version="1.0",
            condition_spec={},
            message_key="decision.insufficient_sample",
            severity="warning",
        )

        from apps.analysis.models import AnalysisRun

        run = AnalysisRun.objects.create(
            owner_id=None,
            algorithm_version="1.0.0",
            random_seed=42,
        )

        rec = DecisionRecommendation.objects.create(
            analysis_run=run,
            rule=rule,
            params={"n": 5, "min_sample": 50},
        )

        assert rec.rule.key == "insufficient_sample"
        assert rec.rule.version == "1.0"
        assert rec.params["n"] == 5


@pytest.mark.django_db
class TestHonestLanguage:
    """Verifica que los message_keys nunca contengan lenguaje no-honesto."""

    def test_registered_rules_honest_language(self):
        """Los message_keys registrados no usan 'bug', 'manipulado', etc."""
        # Seedería desde engine/decisions.py
        from engine.decisions import REGISTERED_RULES

        forbidden = {
            "bug",
            "manipulado",
            "manipulación",
            "anomalía",
            "anomalia",
            "trucado",
            "amañado",
            "fraudulento",
        }

        for key in REGISTERED_RULES:
            message_key = f"decision.{key}"
            for word in forbidden:
                assert word not in message_key.lower(), (
                    f"Palabra prohibida '{word}' en message_key '{message_key}'"
                )
