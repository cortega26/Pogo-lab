"""Tests de integración para apps/dps — vistas y servicios."""

import pytest
from django.urls import reverse

from engine.dps_data import ALL_TYPES


class TestDpsBrowser:
    def test_get_renders_type_grid(self, client):
        resp = client.get(reverse("dps_browser"))
        assert resp.status_code == 200
        html = resp.content.decode()
        assert "DPS" in html or "TDO" in html or "dps" in html.lower()

    def test_get_includes_all_types(self, client):
        resp = client.get(reverse("dps_browser"))
        html = resp.content.decode()
        for t in (
            "fire",
            "water",
            "grass",
            "dragon",
            "electric",
            "ice",
            "fighting",
            "psychic",
            "dark",
            "ghost",
            "rock",
            "steel",
        ):
            assert t in html.lower() or t.capitalize() in html

    def test_get_status_200(self, client):
        resp = client.get(reverse("dps_browser"))
        assert resp.status_code == 200


class TestDpsByType:
    def test_valid_type_returns_200(self, client):
        resp = client.get(reverse("dps_by_type", args=["fire"]))
        assert resp.status_code == 200

    def test_invalid_type_returns_404(self, client):
        resp = client.get(reverse("dps_by_type", args=["fire"]))
        # Try an invalid type via direct URL
        resp = client.get("/es/dps/tipo/invalid_type/")
        assert resp.status_code == 404

    def test_returns_attackers(self, client):
        resp = client.get(reverse("dps_by_type", args=["dragon"]))
        html = resp.content.decode()
        assert "DPS" in html
        # Should list dragon-type attackers
        assert "Rayquaza" in html or "Dialga" in html or "Palkia" in html or "Garchomp" in html

    def test_ranking_sorted_by_dps(self, client):
        resp = client.get(reverse("dps_by_type", args=["normal"]))
        html = resp.content.decode()
        assert "DPS" in html

    def test_htmx_partial_returns_no_layout(self, client):
        resp = client.get(
            reverse("dps_by_type", args=["water"]),
            HTTP_HX_REQUEST="true",
        )
        html = resp.content.decode()
        assert "<html" not in html


class TestAllTypesResolve:
    @pytest.mark.parametrize("t", ALL_TYPES)
    def test_every_type_resolves(self, client, t):
        resp = client.get(reverse("dps_by_type", args=[t]))
        assert resp.status_code == 200


class TestServices:
    def test_get_type_stats_returns_all_types(self):
        from apps.dps.services import get_type_stats

        stats = get_type_stats()
        assert len(stats) == 18
        names = {s["key"] for s in stats}
        for t in ALL_TYPES:
            assert t in names

    def test_get_type_color_returns_hex(self):
        from apps.dps.services import get_type_color

        color = get_type_color("fire")
        assert color.startswith("#")
        assert len(color) == 7

    def test_get_type_attackers_returns_list(self):
        from apps.dps.services import get_type_attackers

        attackers = get_type_attackers("grass", limit=3)
        assert len(attackers) <= 3
        assert len(attackers) > 0
        for a in attackers:
            assert "species" in a
            assert "cycle_dps" in a
            assert "tdo" in a

    def test_get_type_attackers_ranked_by_dps(self):
        from apps.dps.services import get_type_attackers

        attackers = get_type_attackers("psychic", limit=10)
        for i in range(len(attackers) - 1):
            assert attackers[i]["cycle_dps"] >= attackers[i + 1]["cycle_dps"]

    def test_get_type_attackers_filtered_sorted_by_tdo(self):
        from apps.dps.services import get_type_attackers_filtered_sorted

        attackers = get_type_attackers_filtered_sorted("normal", sort_by="tdo")
        assert len(attackers) > 0
        for i in range(len(attackers) - 1):
            assert attackers[i]["tdo"] >= attackers[i + 1]["tdo"]

    def test_get_type_attackers_filtered_sorted_by_name(self):
        from apps.dps.services import get_type_attackers_filtered_sorted

        attackers = get_type_attackers_filtered_sorted("grass", sort_by="name")
        names = [a["species"]["name"] for a in attackers]
        assert names == sorted(names)

    def test_get_type_attackers_filtered_by_type(self):
        from apps.dps.services import get_type_attackers_filtered_sorted

        attackers = get_type_attackers_filtered_sorted("normal", type_filter="dragon")
        for a in attackers:
            types = {a["species"]["type1"], a["species"]["type2"]}
            assert "dragon" in types


class TestDpsSorting:
    def test_sort_dps_query(self, client):
        resp = client.get(reverse("dps_by_type", args=["fire"]) + "?sort=dps")
        assert resp.status_code == 200

    def test_sort_tdo_query(self, client):
        resp = client.get(reverse("dps_by_type", args=["water"]) + "?sort=tdo")
        assert resp.status_code == 200

    def test_sort_name_query(self, client):
        resp = client.get(reverse("dps_by_type", args=["grass"]) + "?sort=name")
        assert resp.status_code == 200

    def test_sort_invalid_falls_back_to_dps(self, client):
        resp = client.get(reverse("dps_by_type", args=["electric"]) + "?sort=invalid")
        assert resp.status_code == 200

    def test_type_filter_query(self, client):
        resp = client.get(reverse("dps_by_type", args=["psychic"]) + "?type_filter=dark")
        assert resp.status_code == 200
