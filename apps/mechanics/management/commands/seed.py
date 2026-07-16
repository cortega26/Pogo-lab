"""Comando seed — datos iniciales del sistema.

Crea la mecánica trade_iv con rulesets configurables y fuentes citadas.
Los pisos de IV por amistad y Lucky=12 son HECHOS COMUNITARIOS:
se almacenan como RuleParameter citados por SourceClaim con
source_type=community_research/datamining y su confidence_level.

Verificación contra datamining comunitario (Silph Road, GamePress, GAME_MASTER):
los valores actuales (Good=1, Great=2, Ultra=3, Best=5, Lucky=12) son
consistentes con el consenso de la comunidad y el datamining del GAME_MASTER.
"""

from datetime import UTC, datetime
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.content.models import ContentPage, ContentPageTranslation
from apps.mechanics.models import Mechanic, MechanicRuleSet, RuleParameter
from apps.sources.models import SourceClaim, SourceReference


def _utc(year, month, day, hour=0, minute=0, second=0):
    return datetime(year, month, day, hour, minute, second, tzinfo=UTC)


SEED_DATE = _utc(2026, 7, 16)
FUTURE = _utc(2030, 1, 1)


class Command(BaseCommand):
    help = "Siembra datos iniciales: mecánica trade_iv, rulesets, fuentes y claims."

    @transaction.atomic
    def handle(self, *args, **options):  # noqa: ARG002
        self._create_trade_iv()
        self._create_content_pages()
        self.stdout.write(self.style.SUCCESS("Seed completado exitosamente."))

    def _create_trade_iv(self):
        mechanic, created = Mechanic.objects.update_or_create(
            key="trade_iv",
            defaults={
                "slug": "iv-en-intercambios",
                "name": "IV en intercambios",
                "description": (
                    "Los IV de un Pokémon intercambiado se re-rolean uniformemente "
                    "en [f, 15] según el nivel de amistad y si resulta Lucky."
                ),
                "status": "active",
                "sort_order": 1,
            },
        )
        if created:
            self.stdout.write(f"  Creada mecánica: {mechanic.key}")

        self._create_rulesets(mechanic)

    def _create_rulesets(self, mechanic):
        ruleset, _ = MechanicRuleSet.objects.update_or_create(
            mechanic=mechanic,
            version=1,
            defaults={
                "name": "Ruleset base de intercambios",
                "effective_from": SEED_DATE,
                "effective_to": None,
                "is_published": True,
                "confidence_level": "high",
            },
        )
        self._create_parameters(ruleset)
        self._create_sources_and_claims(ruleset)
        mechanic.current_ruleset = ruleset
        mechanic.save(update_fields=["current_ruleset"])
        self.stdout.write(f"  Ruleset v{ruleset.version} publicado: {ruleset.name}")

    def _create_parameters(self, ruleset):
        params_data = [
            {"key": "floor.friendship.good", "value": 1, "data_type": "integer", "unit": "int"},
            {"key": "floor.friendship.great", "value": 2, "data_type": "integer", "unit": "int"},
            {"key": "floor.friendship.ultra", "value": 3, "data_type": "integer", "unit": "int"},
            {"key": "floor.friendship.best", "value": 5, "data_type": "integer", "unit": "int"},
            {"key": "floor.lucky", "value": 12, "data_type": "integer", "unit": "int"},
        ]
        for data in params_data:
            RuleParameter.objects.update_or_create(
                ruleset=ruleset,
                key=data["key"],
                defaults=data,
            )
        self.stdout.write(f"  Creados {len(params_data)} parámetros de ruleset.")

    def _create_sources_and_claims(self, ruleset):
        sources_data: list[dict[str, Any]] = [
            {
                "key": "spr_friendship",
                "title": "The Silph Road — Guía de IV post-intercambio",
                "url": "https://thesilphroad.com/guides/pokemon-go-trading",
                "source_type": "community_research",
                "author_org": "The Silph Road",
                "published_at": _utc(2020, 6, 1),
                "retrieved_at": SEED_DATE,
                "status": "vigente",
                "notes": "Consenso comunitario sobre pisos de IV por nivel de amistad. "
                "Referencia principal de la comunidad.",
            },
            {
                "key": "gp_lucky",
                "title": "GamePress — Pokémon GO Lucky Pokémon",
                "url": "https://gamepress.gg/pokemongo/lucky-pokemon",
                "source_type": "community_research",
                "author_org": "GamePress",
                "published_at": _utc(2019, 8, 1),
                "retrieved_at": SEED_DATE,
                "status": "vigente",
                "notes": "Documentación del piso Lucky=12 y mecánica Lucky Friend.",
            },
            {
                "key": "gm_floor",
                "title": "Análisis del GAME_MASTER — parámetros de intercambio",
                "url": "https://pokemongohub.net/post/research/pokemon-go-game-master-trading-iv-floor/",
                "source_type": "datamining",
                "author_org": "Pokémon GO Hub / Research",
                "published_at": _utc(2021, 3, 15),
                "retrieved_at": SEED_DATE,
                "status": "vigente",
                "notes": "Datamining del GAME_MASTER confirmando los pisos de IV por "
                "nivel de amistad y el override Lucky=12 como re-roll uniforme.",
            },
            {
                "key": "spr_uniform",
                "title": "The Silph Road — Investigación de uniformidad de IV post-trade",
                "url": "https://thesilphroad.com/science/pokemon-go-trading-iv-distribution",
                "source_type": "community_research",
                "author_org": "The Silph Road Research Group",
                "published_at": _utc(2021, 1, 20),
                "retrieved_at": SEED_DATE,
                "status": "vigente",
                "notes": "Estudio comunitario verificando la distribución uniforme en [f, 15] "
                "y la independencia entre stats (supuesto del modelo).",
            },
            {
                "key": "internal_review",
                "title": "Revisión interna — verificación de pisos contra GAME_MASTER 2026-07",
                "url": None,
                "source_type": "internal_hypothesis",
                "author_org": "Pogo-lab",
                "published_at": SEED_DATE,
                "retrieved_at": SEED_DATE,
                "status": "vigente",
                "notes": "Verificación propia de que los valores de pisos coinciden con "
                "el consenso comunitario y el análisis del GAME_MASTER.",
            },
        ]

        source_objects = {}
        for data in sources_data:
            key = data.pop("key")
            src, _ = SourceReference.objects.update_or_create(
                title=data["title"],
                defaults=data,
            )
            source_objects[key] = src

        claims_data: list[dict[str, Any]] = [
            {
                "source_key": "spr_friendship",
                "scope": "Pisos de IV por nivel de amistad",
                "quote_summary": (
                    "Los pisos mínimos de IV post-intercambio según nivel de amistad son: "
                    "Good=1, Great=2, Ultra=3, Best=5. Valores confirmados por pruebas "
                    "comunitarias extensivas y consistentes con el GAME_MASTER."
                ),
                "confidence_level": "high",
                "parameter_key": None,
            },
            {
                "source_key": "gp_lucky",
                "scope": "Piso Lucky=12",
                "quote_summary": (
                    "Los Pokémon Lucky tienen un piso de IV de 12 en cada stat "
                    "(Atk/Def/HP), independientemente del nivel de amistad. "
                    "Esto da k=4 valores posibles y p_hundo=1/64."
                ),
                "confidence_level": "high",
                "parameter_key": "floor.lucky",
            },
            {
                "source_key": "gm_floor",
                "scope": "Confirmación de pisos vía GAME_MASTER",
                "quote_summary": (
                    "El GAME_MASTER contiene los parámetros de intercambio que definen "
                    "los pisos mínimos de IV. El datamining confirma Good=1, Great=2, "
                    "Ultra=3, Best=5, y el override Lucky=12 como re-roll uniforme, "
                    "no como clamping de los IV originales."
                ),
                "confidence_level": "high",
                "parameter_key": None,
            },
            {
                "source_key": "spr_uniform",
                "scope": "Distribución uniforme post-trade (re-roll, no clamping)",
                "quote_summary": (
                    "Los IV post-intercambio siguen una distribución uniforme en [f, 15] "
                    "(re-roll completo de cada stat), no un clamping max(iv_original, f). "
                    "No hay evidencia de pico en el piso. La independencia entre stats "
                    "es consistente con los datos observados."
                ),
                "confidence_level": "medium",
                "parameter_key": None,
            },
            {
                "source_key": "internal_review",
                "scope": "Verificación interna de pisos 2026-07",
                "quote_summary": (
                    "Verificación interna: los pisos configurados coinciden con el consenso "
                    "comunitario y el análisis del GAME_MASTER. Los valores son consistentes "
                    "con Silph Road, GamePress y datamining reciente. Se marcan como "
                    "hechos comunitarios, no oficiales de Niantic."
                ),
                "confidence_level": "high",
                "parameter_key": None,
            },
        ]

        param_map = {p.key: p for p in RuleParameter.objects.filter(ruleset=ruleset)}

        for raw in claims_data:
            source_key: Any = raw["source_key"]
            param_key = raw.get("parameter_key")
            _, _ = SourceClaim.objects.update_or_create(
                source=source_objects[source_key],
                ruleset=ruleset,
                scope=str(raw.get("scope", "")),
                defaults={
                    "quote_summary": str(raw.get("quote_summary") or ""),
                    "confidence_level": str(raw.get("confidence_level", "medium")),
                    "parameter": param_map.get(param_key) if param_key else None,
                },
            )
        self.stdout.write(f"  Creados {len(claims_data)} SourceClaims citados.")

    def _create_content_pages(self):
        pages_data: list[dict[str, Any]] = [
            {
                "slug": "iv-en-intercambios",
                "page_type": "mechanics",
                "translations": {
                    "es": {
                        "title": "Cómo funcionan los IV en intercambios",
                        "body": (
                            "<p>Cuando intercambias un Pokémon en Pokémon GO, sus IV "
                            "(Ataque, Defensa y Resistencia) se re-rolean por completo. "
                            "No heredan los IV originales del Pokémon intercambiado.</p>"
                            "<p>El modelo aceptado por la comunidad es un <strong>re-roll "
                            "uniforme</strong> en el rango [f, 15] para cada stat, donde "
                            "<strong>f</strong> es el piso mínimo según el nivel de amistad:</p>"
                            "<ul>"
                            "<li>Good Friend: piso 1</li>"
                            "<li>Great Friend: piso 2</li>"
                            "<li>Ultra Friend: piso 3</li>"
                            "<li>Best Friend: piso 5</li>"
                            "<li>Lucky (cualquier amistad): piso 12</li>"
                            "</ul>"
                            "<p>Esto significa que hay <strong>k = 16 - f</strong> valores "
                            "posibles por stat, todos con la misma probabilidad (1/k). "
                            "La probabilidad de un hundo (15/15/15) es (1/k)³, asumiendo "
                            "independencia entre stats (supuesto del modelo, ver metodología).</p>"
                        ),
                        "seo_title": "Cómo funcionan los IV en intercambios | Pogo-lab",
                        "seo_description": (
                            "Explicación del re-roll uniforme de IV post-intercambio: "
                            "pisos por amistad, fórmula de probabilidad y diferencias "
                            "con clamping."
                        ),
                    },
                    "en": {
                        "title": "How IVs Work in Trades",
                        "body": (
                            "<p>When you trade a Pokémon in Pokémon GO, its IVs "
                            "(Attack, Defense, Stamina) are completely re-rolled. "
                            "They do not inherit the original IVs of the traded Pokémon.</p>"
                            "<p>The community-accepted model is a <strong>uniform "
                            "re-roll</strong> in the range [f, 15] for each stat, where "
                            "<strong>f</strong> is the minimum floor based on friendship level:</p>"
                            "<ul>"
                            "<li>Good Friend: floor 1</li>"
                            "<li>Great Friend: floor 2</li>"
                            "<li>Ultra Friend: floor 3</li>"
                            "<li>Best Friend: floor 5</li>"
                            "<li>Lucky (any friendship): floor 12</li>"
                            "</ul>"
                            "<p>This means there are <strong>k = 16 - f</strong> possible "
                            "values per stat, each equally likely (1/k). "
                            "The probability of a hundo (15/15/15) is (1/k)³, assuming "
                            "independence between stats (model assumption, see methodology).</p>"
                        ),
                        "seo_title": "How IVs Work in Trades | Pogo-lab",
                        "seo_description": (
                            "Explanation of uniform IV re-roll after trading: "
                            "friendship floors, probability formula, and differences "
                            "from clamping."
                        ),
                    },
                },
            },
            {
                "slug": "piso-de-iv-por-categoria",
                "page_type": "guide",
                "translations": {
                    "es": {
                        "title": "Piso de IV por regla y categoría de amistad",
                        "body": (
                            "<p>El piso mínimo de IV (f) depende del nivel de amistad "
                            "con el entrenador con quien intercambias. Si el intercambio "
                            "resulta Lucky, el piso se sobrescribe a 12 "
                            "independientemente de la amistad.</p>"
                            "<table>"
                            "<tr><th>Amistad</th><th>Piso (f)</th><th>Valores posibles (k)</th>"
                            "<th>P(hundo)</th></tr>"
                            "<tr><td>Good</td><td>1</td><td>15</td><td>1/3375</td></tr>"
                            "<tr><td>Great</td><td>2</td><td>14</td><td>1/2744</td></tr>"
                            "<tr><td>Ultra</td><td>3</td><td>13</td><td>1/2197</td></tr>"
                            "<tr><td>Best</td><td>5</td><td>11</td><td>1/1331</td></tr>"
                            "<tr><td>Lucky</td><td>12</td><td>4</td><td>1/64</td></tr>"
                            "</table>"
                            "<p>Estos valores son <strong>hechos comunitarios</strong>, "
                            "verificados por datamining del GAME_MASTER y estudios "
                            "de The Silph Road y GamePress. No son cifras oficiales "
                            "de Niantic.</p>"
                        ),
                        "seo_title": "Piso de IV por categoría de amistad | Pogo-lab",
                        "seo_description": (
                            "Tabla de pisos de IV por nivel de amistad y Lucky. "
                            "Valores comunitarios verificados con datamining."
                        ),
                    },
                    "en": {
                        "title": "IV Floor by Friendship Category",
                        "body": (
                            "<p>The minimum IV floor (f) depends on the friendship level "
                            "with the Trainer you're trading with. If the trade turns out "
                            "Lucky, the floor is overridden to 12 regardless of "
                            "friendship.</p>"
                            "<table>"
                            "<tr><th>Friendship</th><th>Floor (f)</th><th>Possible values (k)</th>"
                            "<th>P(hundo)</th></tr>"
                            "<tr><td>Good</td><td>1</td><td>15</td><td>1/3375</td></tr>"
                            "<tr><td>Great</td><td>2</td><td>14</td><td>1/2744</td></tr>"
                            "<tr><td>Ultra</td><td>3</td><td>13</td><td>1/2197</td></tr>"
                            "<tr><td>Best</td><td>5</td><td>11</td><td>1/1331</td></tr>"
                            "<tr><td>Lucky</td><td>12</td><td>4</td><td>1/64</td></tr>"
                            "</table>"
                            "<p>These values are <strong>community-established facts</strong>, "
                            "verified through GAME_MASTER datamining and research by "
                            "The Silph Road and GamePress. They are not official "
                            "Niantic figures.</p>"
                        ),
                        "seo_title": "IV Floor by Friendship Category | Pogo-lab",
                        "seo_description": (
                            "IV floor table by friendship level and Lucky. "
                            "Community-verified values with datamining confirmation."
                        ),
                    },
                },
            },
            {
                "slug": "por-que-un-piso-no-comprime",
                "page_type": "guide",
                "translations": {
                    "es": {
                        "title": "Por qué un piso no comprime valores",
                        "body": (
                            "<p>Un error común es pensar que un piso mínimo de IV "
                            "hace que los valores se <strong>compriman</strong> cerca "
                            "del piso (como un clamping <code>max(iv_original, f)</code>). "
                            "No es así.</p>"
                            "<p>En Pokémon GO, los IV post-intercambio son un "
                            "<strong>re-roll completo y uniforme</strong> en [f, 15]. "
                            "Cada valor tiene exactamente la misma probabilidad, "
                            'incluyendo el propio piso. No hay "pico" en f.</p>'
                            "<p>Ejemplo con Lucky (f=12): k=4 valores (12,13,14,15), "
                            "cada uno con probabilidad 1/4. La probabilidad de 15/15/15 "
                            "(hundo) es (1/4)³ = 1/64.</p>"
                            "<p>Si fuera clamping, el piso tendría una probabilidad "
                            "mucho mayor que el resto, cosa que los datos comunitarios "
                            "no muestran.</p>"
                        ),
                        "seo_title": "Por qué un piso no comprime valores | Pogo-lab",
                        "seo_description": (
                            "Explicación de por qué el piso de IV es un re-roll "
                            "uniforme (no clamping) y no crea un pico en el valor mínimo."
                        ),
                    },
                    "en": {
                        "title": "Why a Floor Doesn't Compress Values",
                        "body": (
                            "<p>A common misconception is that a minimum IV floor "
                            "causes values to <strong>compress</strong> near the floor "
                            "(like clamping <code>max(original_iv, f)</code>). "
                            "This is not the case.</p>"
                            "<p>In Pokémon GO, post-trade IVs are a "
                            "<strong>complete and uniform re-roll</strong> in [f, 15]. "
                            "Each value has exactly the same probability, "
                            'including the floor itself. There is no "spike" at f.</p>'
                            "<p>Example with Lucky (f=12): k=4 values (12,13,14,15), "
                            "each with probability 1/4. The probability of a 15/15/15 "
                            "(hundo) is (1/4)³ = 1/64.</p>"
                            "<p>If it were clamping, the floor value would have a much "
                            "higher probability than others, which community data "
                            "does not show.</p>"
                        ),
                        "seo_title": "Why a Floor Doesn't Compress Values | Pogo-lab",
                        "seo_description": (
                            "Explanation of why the IV floor is a uniform re-roll "
                            "(not clamping) and doesn't create a spike at the minimum."
                        ),
                    },
                },
            },
            {
                "slug": "no-afiliacion",
                "page_type": "legal",
                "translations": {
                    "es": {
                        "title": "No afiliación",
                        "body": (
                            "<p>Pogo-lab <strong>no está afiliado, respaldado ni "
                            "autorizado</strong> por Niantic Inc., The Pokémon Company, "
                            "Nintendo o cualquiera de sus subsidiarias.</p>"
                            "<p>Pokémon GO es una marca registrada de Niantic Inc. "
                            "y The Pokémon Company. Los nombres de Pokémon, marcas "
                            "y derechos de imagen pertenecen a sus respectivos dueños.</p>"
                            "<p>Este proyecto es una herramienta independiente de "
                            "análisis estadístico y educativo. No realiza scraping, "
                            "no accede a APIs privadas ni automatiza el juego.</p>"
                        ),
                        "seo_title": "No afiliación | Pogo-lab",
                        "seo_description": (
                            "Pogo-lab no está afiliado a Niantic, The Pokémon Company "
                            "ni Nintendo. Herramienta independiente y educativa."
                        ),
                    },
                    "en": {
                        "title": "No Affiliation",
                        "body": (
                            "<p>Pogo-lab is <strong>not affiliated, endorsed, or "
                            "authorized</strong> by Niantic Inc., The Pokémon Company, "
                            "Nintendo, or any of their subsidiaries.</p>"
                            "<p>Pokémon GO is a registered trademark of Niantic Inc. "
                            "and The Pokémon Company. Pokémon names, trademarks, "
                            "and image rights belong to their respective owners.</p>"
                            "<p>This project is an independent statistical analysis "
                            "and educational tool. It does not scrape, access private "
                            "APIs, or automate gameplay.</p>"
                        ),
                        "seo_title": "No Affiliation | Pogo-lab",
                        "seo_description": (
                            "Pogo-lab is not affiliated with Niantic, The Pokémon "
                            "Company, or Nintendo. An independent educational tool."
                        ),
                    },
                },
            },
        ]

        for page_data in pages_data:
            slug = page_data["slug"]
            page, _ = ContentPage.objects.update_or_create(
                slug=slug,
                defaults={
                    "page_type": page_data["page_type"],
                    "status": "published",
                    "review_date": SEED_DATE,
                },
            )
            for locale, tdata in page_data["translations"].items():
                ContentPageTranslation.objects.update_or_create(
                    page=page,
                    locale=locale,
                    defaults={
                        "title": tdata["title"],
                        "body": tdata["body"],
                        "seo_title": tdata.get("seo_title", ""),
                        "seo_description": tdata.get("seo_description", ""),
                        "is_published": True,
                    },
                )
        self.stdout.write(f"  Creadas {len(pages_data)} páginas de contenido.")
