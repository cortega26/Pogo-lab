"""Seed content pages for key mechanics. Usage: python manage.py seed_content"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.content.models import ContentPage, ContentPageTranslation


def _seed():
    now = timezone.now()
    pages = [
        _cp(),
        _iv_trade(),
        _catch(),
        _pvp(),
        _shadow(),
        _shiny(),
    ]
    for data in pages:
        page, created = ContentPage.objects.update_or_create(
            slug=data["slug"],
            defaults={"page_type": data["page_type"], "status": "published", "review_date": now},
        )
        for lang in ("es", "en"):
            ContentPageTranslation.objects.update_or_create(
                page=page, locale=lang,
                defaults={
                    "title": data[f"title_{lang}"],
                    "body": data[f"body_{lang}"],
                    "is_published": True,
                },
            )
        yield page.slug, created

def _cp():
    return {
        "slug": "cp-como-funciona", "page_type": "mechanics",
        "title_es": "¿Cómo se calcula el CP y HP?",
        "body_es": "<h2>Fórmula de CP</h2><pre>CP = max(10, floor(Atk × √Def × √Sta × CPM² / 10))</pre><p>Donde Atk, Def, Sta = (base + IV) × CPM. El CPM es una tabla de 109 valores que aumenta con el nivel (0.094 a 0.865).</p><h2>Fórmula de HP</h2><pre>HP = max(10, floor(Sta × CPM))</pre><p>Fuente: comunidad (GamePress), verificada por datamining. Alta confianza.</p>",
        "title_en": "How CP and HP are calculated",
        "body_en": "<h2>CP Formula</h2><pre>CP = max(10, floor(Atk × √Def × √Sta × CPM² / 10))</pre><p>Where Atk, Def, Sta = (base + IV) × CPM. CPM is a table of 109 values increasing with level (0.094 to 0.865).</p><h2>HP Formula</h2><pre>HP = max(10, floor(Sta × CPM))</pre><p>Source: community (GamePress), verified via datamining. High confidence.</p>",
    }

def _iv_trade():
    return {
        "slug": "iv-en-intercambios", "page_type": "mechanics",
        "title_es":"IV en intercambios: pisos y probabilidades",
        "body_es":"<h2>Pisos de IV por amistad</h2><ul><li>Good: f=1</li><li>Great: f=2</li><li>Ultra: f=3</li><li>Best: f=5</li><li>Lucky: f=12</li></ul><h2>Modelo</h2><p>Cada stat recibe un valor uniforme en [f, 15]. k = 16−f valores posibles, prob=1/k. Asumiendo independencia: P(hundo)=1/k³.</p><p>Lucky f=12 → k=4 → P(hundo)=1/64≈1.56%</p><p>Fuente: comunidad (Silph Road). Los pisos se modelan como RuleParameter versionados.</p>",
        "title_en":"IVs in trades: floors and probabilities",
        "body_en":"<h2>IV floors by friendship</h2><ul><li>Good: f=1</li><li>Great: f=2</li><li>Ultra: f=3</li><li>Best: f=5</li><li>Lucky: f=12</li></ul><h2>Model</h2><p>Each stat gets a uniform value in [f, 15]. k = 16−f possible values, prob=1/k. Assuming independence: P(hundo)=1/k³.</p><p>Lucky f=12 → k=4 → P(hundo)=1/64≈1.56%</p><p>Source: community (Silph Road). Floors are modeled as versioned RuleParameters.</p>",
    }

def _catch():
    return {
        "slug": "captura-probabilidad", "page_type": "mechanics",
        "title_es":"Probabilidad de captura en Pokémon GO",
        "body_es":"<h2>Fórmula</h2><pre>P = 1 − (1 − BCR/(2×CPM))^M</pre><p>BCR=Base Catch Rate. CPM=CpMultiplier. M=Ball×Berry×Curve×Throw×Medal.</p><h2>Modificadores</h2><ul><li>Ball: 1.0/1.5/2.0</li><li>Berry: 1.0/1.5/2.5</li><li>Curve: 1.0/1.7</li><li>Throw: 2−radius (1.0 a 2.0)</li><li>Medal: 1.0 a 1.4</li></ul><p>Fuente: comunidad (GamePress), alta confianza.</p>",
        "title_en":"Catch probability in Pokémon GO",
        "body_en":"<h2>Formula</h2><pre>P = 1 − (1 − BCR/(2×CPM))^M</pre><p>BCR=Base Catch Rate. CPM=CpMultiplier. M=Ball×Berry×Curve×Throw×Medal.</p><h2>Modifiers</h2><ul><li>Ball: 1.0/1.5/2.0</li><li>Berry: 1.0/1.5/2.5</li><li>Curve: 1.0/1.7</li><li>Throw: 2−radius (1.0 to 2.0)</li><li>Medal: 1.0 to 1.4</li></ul><p>Source: community (GamePress), high confidence.</p>",
    }

def _pvp():
    return {
        "slug": "pvp-stat-product", "page_type": "guide",
        "title_es":"Stat Product y ranking de IV para PvP",
        "body_es":"<h2>Stat Product</h2><pre>SP = ATK_eff × DEF_eff × STAM_eff</pre><p>En ligas con cap de CP, el mejor IV NO es 15/15/15. Se busca maximizar SP sin exceder el cap.</p><h2>¿Por qué ATK bajo?</h2><p>El ATK pesa más en el CP. Con ATK bajo (0-5) y DEF/STA altos (14-15), el Pokémon alcanza más nivel (más bulk) bajo el mismo cap.</p><h2>Ranking</h2><p>Se evalúan las 4096 combinaciones de IV. Para cada una, se busca el nivel máximo sin exceder el cap. Se ordena por SP descendente; a igual SP, menor ATK primero.</p><p>Fuente: metodología estándar PvP (PvPoke). Alta confianza.</p>",
        "title_en":"Stat Product and IV ranking for PvP",
        "body_en":"<h2>Stat Product</h2><pre>SP = ATK_eff × DEF_eff × STAM_eff</pre><p>In CP-capped leagues, the best IV is NOT 15/15/15. You maximize SP without exceeding the cap.</p><h2>Why low ATK?</h2><p>ATK contributes more to CP. With low ATK (0-5) and high DEF/STA (14-15), the Pokémon reaches a higher level (more bulk) under the same cap.</p><h2>Ranking</h2><p>All 4096 IV combinations are evaluated. For each, the max level not exceeding the cap is found. Sorted by SP descending; at equal SP, lower ATK first.</p><p>Source: standard PvP methodology (PvPoke). High confidence.</p>",
    }

def _shadow():
    return {
        "slug": "shadow-vs-purified", "page_type": "guide",
        "title_es":"Shadow vs Purified: ¿cuál conviene?",
        "body_es":"<h2>Diferencias</h2><table><tr><th></th><th>Shadow</th><th>Purified</th></tr><tr><td>Ataque PvE</td><td>+20%</td><td>Normal</td></tr><tr><td>Defensa PvE</td><td>−17%</td><td>Normal</td></tr><tr><td>Costo Stardust</td><td>+20%</td><td>−10%</td></tr><tr><td>Costo Caramelos</td><td>Normal</td><td>−10%</td></tr></table><h2>PvE: Shadow casi siempre gana</h2><p>El +20% de daño supera el costo extra en stardust para atacantes top.</p><h2>PvP: depende</h2><p>Purificar puede mejorar IVs para PvP (ej: 13/13/13 → 15/15/15).</p><p>Fuente: comunidad (GamePress), alta confianza.</p>",
        "title_en":"Shadow vs Purified: which is better?",
        "body_en":"<h2>Differences</h2><table><tr><th></th><th>Shadow</th><th>Purified</th></tr><tr><td>PvE Attack</td><td>+20%</td><td>Normal</td></tr><tr><td>PvE Defense</td><td>−17%</td><td>Normal</td></tr><tr><td>Stardust Cost</td><td>+20%</td><td>−10%</td></tr><tr><td>Candy Cost</td><td>Normal</td><td>−10%</td></tr></table><h2>PvE: Shadow almost always wins</h2><p>The +20% damage outweighs the extra stardust cost for top attackers.</p><h2>PvP: depends</h2><p>Purifying can improve IVs for PvP (e.g., 13/13/13 → 15/15/15).</p><p>Source: community (GamePress), high confidence.</p>",
    }

def _shiny():
    return {
        "slug": "shiny-probabilidad", "page_type": "mechanics",
        "title_es":"Probabilidad de encontrar un Shiny",
        "body_es":"<h2>Fórmula</h2><pre>P = 1 − (1 − tasa)^n</pre><h2>Tasas típicas</h2><ul><li>Estándar: ~1/500 (0.2%)</li><li>Permaboost: ~1/125 (0.8%)</li><li>Community Day: ~1/25 (4%)</li><li>Legendario: ~1/20 (5%)</li></ul><h2>Encuentros para 95% confianza</h2><ul><li>1/500: ~1,496</li><li>1/125: ~373</li><li>1/25: ~73</li><li>1/20: ~58</li></ul><p>Importante: la probabilidad nunca llega a 100%. Siempre existe chance de no encontrar shiny.</p><p>Fuente: comunidad (Silph Road Research Group).</p>",
        "title_en":"Probability of finding a Shiny",
        "body_en":"<h2>Formula</h2><pre>P = 1 − (1 − rate)^n</pre><h2>Typical rates</h2><ul><li>Standard: ~1/500 (0.2%)</li><li>Permaboost: ~1/125 (0.8%)</li><li>Community Day: ~1/25 (4%)</li><li>Legendary: ~1/20 (5%)</li></ul><h2>Encounters for 95% confidence</h2><ul><li>1/500: ~1,496</li><li>1/125: ~373</li><li>1/25: ~73</li><li>1/20: ~58</li></ul><p>Important: probability never reaches 100%. There's always a chance of not finding a shiny.</p><p>Source: community (Silph Road Research Group).</p>",
    }


class Command(BaseCommand):
    help = "Siembra páginas de contenido editorial con traducciones es/en."

    def handle(self, **_kwargs):
        for slug, created in _seed():
            verb = "Creada" if created else "Actualizada"
            self.stdout.write(f"  {verb}: {slug}")
        self.stdout.write(self.style.SUCCESS("Contenido editorial sembrado."))
