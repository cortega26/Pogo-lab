# Modelo de dominio — Pogo-lab

> Fuente única: [`docs/plan.md` §E](plan.md). Este documento refina el ERD del plan en
> especificaciones de campos, constraints, índices, privacidad y versionado para cada entidad.
> **No reemplaza el plan: lo detalla.** Las migraciones Django se derivan de aquí (M2+).

## Convenciones globales

- **PK:** `BigAutoField` (`id`).
- **Timestamps:** `created_at`/`updated_at` en toda entidad (mixin `TimestampedModel` en `apps/core`).
- **TZ:** almacenar en UTC (`USE_TZ=True`). Capturar zona/offset del usuario donde importe (`tz_offset`).
- **Soft delete** solo donde hay linaje/auditoría (`TradeObservation`, `DataContributionConsent`).
  Resto: borrado duro.
- **Provenance:** entidades de conocimiento (`RuleParameter`, `MechanicRuleSet`) enlazan
  `SourceClaim`.
- **Versionado inmutable:** `MechanicRuleSet`, `DatasetVersion` y `algorithm_version` del engine son
  **inmutables al publicar**; los cambios crean nuevas versiones con `effective_from/to`.
- **Índices:** claves foráneas + campos de filtro caliente + únicos de deduplicación + `hreflang`.

## Entidades (21)

---

### 1. User

Modelo de auth estándar Django (o custom `accounts.User` con email como login).

| Campo | Tipo | Constraints | Notas |
|---|---|---|---|
| `email` | EmailField | `unique`, `not null` | Login principal |
| `password` | CharField | `not null` | Hash (allauth) |
| `is_active` | BooleanField | default `True` | |
| `is_staff` | BooleanField | default `False` | |
| `date_joined` | DateTimeField | auto | |
| `last_login` | DateTimeField | nullable | |

**Privacidad:** email es PII; nunca en logs. Retención: eliminación de cuenta borra/anonimiza en
cascada.

---

### 2. UserProfile

| Campo | Tipo | Constraints | Notas |
|---|---|---|---|
| `user` | FK→User | `unique`, `not null`, `on_delete=CASCADE` | 1:1 |
| `locale` | CharField(10) | default `"es"` | Código de locale (`es`, `en`, `pt`) |
| `country` | CharField(2) | nullable, opcional | ISO 3166-1 alpha-2, **solo país agregado** |
| `default_contribution_optin` | BooleanField | default `False` | Opt-in por defecto al contribuir |
| `display_prefs` | JSONField | default `dict` | Preferencias de visualización (tema, etc.) |

**Privacidad:** sin nombre de entrenador. País es opcional y solo agregado.

---

### 3. Mechanic

Catálogo de familias de mecánicas.

| Campo | Tipo | Constraints | Notas |
|---|---|---|---|
| `slug` | SlugField | `unique`, `not null` | Identificador URL |
| `key` | CharField(64) | `unique`, `not null` | Cód interno, ej. `"trade_iv"` |
| `name` | CharField(128) | `not null` | Nombre visible |
| `description` | TextField | nullable | |
| `status` | CharField(16) | default `"active"` | `active` / `deprecated` / `experimental` |
| `current_ruleset` | FK→MechanicRuleSet | nullable | Reglas vigentes |
| `sort_order` | IntegerField | default `0` | Para orden en índices |

---

### 4. MechanicRuleSet

Unidad de **versionado de reglas**. Inmutable al publicar.

| Campo | Tipo | Constraints | Notas |
|---|---|---|---|
| `mechanic` | FK→Mechanic | `not null` | |
| `version` | IntegerField | `not null` | Incremental por mechanic |
| `name` | CharField(128) | `not null` | |
| `effective_from` | DateTimeField | `not null` | Inicio de vigencia |
| `effective_to` | DateTimeField | nullable | Fin de vigencia (`null` = vigente) |
| `is_published` | BooleanField | default `False` | Inmutable si `True` |
| `confidence_level` | CharField(32) | nullable | `high` / `medium` / `low` / `hypothetical` |
| `notes` | TextField | nullable | |

**Constraints:** único `(mechanic, version)`. No editable si `is_published`. Resolución por
fecha: `resolve_active_ruleset(mechanic, at)`.

---

### 5. RuleParameter

Valores concretos de un ruleset (pisos por amistad, Lucky, etc.).

| Campo | Tipo | Constraints | Notas |
|---|---|---|---|
| `ruleset` | FK→MechanicRuleSet | `not null` | |
| `key` | CharField(64) | `not null` | Ej. `"floor.friendship.best"`, `"floor.lucky"` |
| `value` | JSONField | `not null` | Valor numérico o compuesto |
| `data_type` | CharField(32) | default `"integer"` | `integer` / `float` / `boolean` / `string` / `json` |
| `unit` | CharField(32) | nullable | `"int"` / `"probability"` / etc. |

Aquí viven los **pisos por amistad** y **Lucky=12** como datos configurables, nunca hardcodeados.

---

### 6. SourceReference

Fuente de información (oficial, comunidad, datamining, etc.).

| Campo | Tipo | Constraints | Notas |
|---|---|---|---|
| `title` | CharField(256) | `not null` | |
| `url` | URLField | nullable | |
| `source_type` | CharField(32) | `not null` | `oficial` / `community_research` / `datamining` / `inference` / `internal_hypothesis` |
| `author_org` | CharField(128) | nullable | |
| `published_at` | DateTimeField | nullable | |
| `retrieved_at` | DateTimeField | nullable | Cuándo se obtuvo/revisó |
| `status` | CharField(32) | default `"vigente"` | `vigente` / `en_revision` / `obsoleta` / `contradicha` |
| `effective_from` | DateTimeField | nullable | Desde cuándo es relevante |
| `effective_to` | DateTimeField | nullable | Hasta cuándo es relevante |
| `notes` | TextField | nullable | |

---

### 7. SourceClaim

Vincula una afirmación con su fuente de evidencia.

| Campo | Tipo | Constraints | Notas |
|---|---|---|---|
| `source` | FK→SourceReference | `not null` | |
| `ruleset` | FK→MechanicRuleSet | nullable | Ruleset al que aplica |
| `parameter` | FK→RuleParameter | nullable | Parámetro específico que respalda |
| `scope` | CharField(128) | nullable | Ámbito de la afirmación |
| `quote_summary` | TextField | nullable | Resumen / cita textual |
| `confidence_level` | CharField(32) | default `"medium"` | `high` / `medium` / `low` / `hypothetical` |

**Privacidad:** no contiene PII. **Índices:** por `source`, `ruleset`, `parameter`.

---

### 8. Experiment / 9. ExperimentProtocol

Define qué se está intentando medir/verificar.

**Experiment:**

| Campo | Tipo | Constraints | Notas |
|---|---|---|---|
| `mechanic` | FK→Mechanic | `not null` | |
| `hypothesis` | TextField | `not null` | Hipótesis a probar |
| `status` | CharField(16) | default `"draft"` | `draft` / `active` / `completed` / `rejected` |
| `min_sample` | IntegerField | nullable | Mínimo de observaciones requeridas |
| `method_notes` | TextField | nullable | |
| `dataset_version` | FK→DatasetVersion | nullable | Versión del dataset usada |
| `protocol` | FK→ExperimentProtocol | nullable | |

**ExperimentProtocol:**

| Campo | Tipo | Constraints | Notas |
|---|---|---|---|
| `name` | CharField(128) | `not null` | |
| `description` | TextField | `not null` | |
| `method_definition` | JSONField | `not null` | Pasos/parámetros del método |

---

### 10. TradeSession

Sesión de intercambios de un usuario.

| Campo | Tipo | Constraints | Notas |
|---|---|---|---|
| `owner` | FK→User | `not null`, `on_delete=CASCADE` | |
| `started_at` | DateTimeField | `not null` | |
| `label` | CharField(128) | nullable | Etiqueta libre |
| `default_friendship` | CharField(16) | nullable | `good` / `great` / `ultra` / `best` |
| `default_trade_type` | CharField(16) | default `"normal"` | `normal` / `lucky` / `lucky_guaranteed` |
| `notes` | TextField | nullable | Privado del usuario |

**Privacidad:** `notes` nunca se agrega al dataset público.

---

### 11. TradeObservation

Observación individual de un intercambio.

| Campo | Tipo | Constraints | Notas |
|---|---|---|---|
| `session` | FK→TradeSession | `not null` | |
| `owner` | FK→User | `not null` | Denormalizado para filtros |
| `observed_at` | DateTimeField | `not null` | |
| `tz_offset` | CharField(6) | nullable | Ej. `"-03:00"` |
| `friendship_level` | CharField(16) | `not null` | `good` / `great` / `ultra` / `best` |
| `trade_type` | CharField(16) | `not null` | `normal` / `lucky` / `lucky_guaranteed` |
| `is_lucky` | BooleanField | `not null` | Si resultó Lucky |
| `lucky_guaranteed` | BooleanField | nullable | `True` si era Lucky garantizado |
| `atk` | SmallIntegerField | `0 <= atk <= 15` | IV individual |
| `def` | SmallIntegerField | `0 <= def <= 15` | IV individual |
| `hp` | SmallIntegerField | `0 <= hp <= 15` | IV individual |
| `species` | CharField(64) | nullable | Especie del Pokémon (opcional) |
| `special_trade` | BooleanField | nullable | Intercambio especial (costo alto) |
| `oldest_age_bucket` | CharField(16) | nullable | Rango de edad del Pokémon más antiguo |
| `event_context` | CharField(64) | nullable | Evento especial vigente |
| `app_version` | CharField(16) | nullable | Versión de la app |
| `input_method` | CharField(16) | default `"manual"` | `manual` / `batch` / `csv` |
| `ruleset` | FK→MechanicRuleSet | nullable | Ruleset vigente al registrar |
| `state` | CharField(16) | default `"valid"` | `draft` / `valid` / `excluded` / `suspicious` / `duplicate` / `deleted` |
| `exclusion_reason` | TextField | nullable | |
| `contribution_optin` | BooleanField | default `False` | |
| `dedup_hash` | CharField(64) | nullable, indexed | Hash de deduplicación |
| `notes` | TextField | nullable | **Privado** — nunca se agrega |

**Constraints:** `0 <= atk/def/hp <= 15`; coherencia piso↔resultado por ruleset; `is_lucky`
consistente con `trade_type`. **Índices:** `(owner, is_lucky, ruleset, observed_at)`, `dedup_hash`.
**Privacidad:** `notes` nunca sale a contribuciones.

---

### 12. DataContributionConsent

Consentimiento explícito y revocable para contribuir datos al dataset comunitario.

| Campo | Tipo | Constraints | Notas |
|---|---|---|---|
| `user` | FK→User | `not null` | |
| `scope` | CharField(64) | default `"trade_iv"` | Ámbito del consentimiento |
| `consent_text_version` | CharField(32) | `not null` | Versión del texto legal aceptado |
| `granted_at` | DateTimeField | auto_now_add | |
| `revoked_at` | DateTimeField | nullable | Fecha de revocación |
| `is_active` | BooleanField | default `True` | |

**Privacidad:** auditado y revocable. La revocación excluye al usuario de builds futuros del
dataset (no elimina versiones ya publicadas).

---

### 13. DatasetVersion

Snapshot anonimizado e inmutable del dataset comunitario.

| Campo | Tipo | Constraints | Notas |
|---|---|---|---|
| `number` | IntegerField | `unique`, `not null` | Incremental |
| `built_at` | DateTimeField | auto_now_add | |
| `criteria` | JSONField | `not null` | Filtros/umbrales usados |
| `min_sample_met` | BooleanField | default `False` | Supera el umbral mínimo |
| `row_count` | IntegerField | default `0` | |
| `checksum` | CharField(64) | nullable | SHA-256 del contenido |
| `is_public` | BooleanField | default `False` | |
| `pipeline_version` | CharField(16) | nullable | Versión del pipeline de build |

**Inmutable** una vez publicado. Anonimizado: excluye `notes`, sin trainer/ubicación, solo país
agregado, con `dedup_hash`.

---

### 14. AnalysisRun

Ejecución de un análisis. Clave de **reproducibilidad**.

| Campo | Tipo | Constraints | Notas |
|---|---|---|---|
| `dataset_version` | FK→DatasetVersion | nullable | Análisis sobre dataset público |
| `owner` | FK→User | nullable | Análisis personal (sin dataset_version) |
| `filters` | JSONField | nullable | Filtros aplicados |
| `ruleset` | FK→MechanicRuleSet | nullable | Ruleset usado |
| `algorithm_version` | CharField(32) | `not null` | Semver del algoritmo |
| `method_params` | JSONField | default `dict` | Parámetros del método |
| `random_seed` | IntegerField | nullable | Semilla para MC |
| `code_sha` | CharField(40) | nullable | SHA del código en el momento |
| `created_at` | DateTimeField | auto_now_add | |

**Reproducibilidad:** re-ejecutar con `dataset_version + ruleset.version + algorithm_version +
random_seed + code_sha` reproduce el resultado.

---

### 15. AnalysisResult

Resultado de una métrica dentro de un `AnalysisRun`.

| Campo | Tipo | Constraints | Notas |
|---|---|---|---|
| `run` | FK→AnalysisRun | `not null` | |
| `metric_key` | CharField(64) | `not null` | Identificador de la métrica |
| `payload` | JSONField | `not null` | Estimador, IC, p-valor, tamaño de efecto, método, n, esperados mínimos |

**Payload típico:** `{"estimate": 0.25, "ci_method": "wilson", "ci_lo": 0.1, "ci_hi": 0.4,
"p_value": 0.03, "effect_size": 0.15, "method_used": "exact_binomial", "n": 64,
"min_expected": 0.5}`.

---

### 16. DecisionRule

Regla determinista versionada. Evaluada por `engine/decisions.py`.

| Campo | Tipo | Constraints | Notas |
|---|---|---|---|
| `key` | CharField(64) | `unique`, `not null` | Cód interno |
| `version` | CharField(16) | default `"1.0"` | Semver |
| `condition_spec` | JSONField | `not null` | Especificación declarativa de la condición |
| `message_key` | CharField(128) | `not null` | Clave i18n del mensaje |
| `severity` | CharField(16) | default `"info"` | `info` / `warning` / `critical` |
| `is_active` | BooleanField | default `True` | |

**Determinista:** las recomendaciones se generan por `engine.decisions.evaluate()`, nunca por LLM.

---

### 17. DecisionRecommendation

Recomendación generada para un análisis, trazable a su regla.

| Campo | Tipo | Constraints | Notas |
|---|---|---|---|
| `analysis_result` | FK→AnalysisResult | nullable | |
| `context` | JSONField | nullable | Contexto adicional |
| `rule` | FK→DecisionRule | `not null` | Regla que la produjo |
| `params` | JSONField | default `dict` | Parámetros de la recomendación |
| `created_at` | DateTimeField | auto_now_add | |

---

### 18. ContentPage

Página de contenido editorial.

| Campo | Tipo | Constraints | Notas |
|---|---|---|---|
| `slug` | SlugField | `unique`, `not null` | |
| `mechanic` | FK→Mechanic | nullable | Mecánica explicada |
| `page_type` | CharField(32) | `not null` | `mechanics` / `guide` / `methodology` / `legal` / `landing` |
| `status` | CharField(16) | default `"draft"` | `draft` / `published` / `archived` |
| `updated_at` | DateTimeField | auto_now | |
| `review_date` | DateTimeField | nullable | |

---

### 19. ContentPageTranslation

Traducción de una página de contenido por locale.

| Campo | Tipo | Constraints | Notas |
|---|---|---|---|
| `page` | FK→ContentPage | `not null` | |
| `locale` | CharField(10) | `not null` | Código de locale (`es`, `en`, `pt`) |
| `title` | CharField(256) | `not null` | |
| `body` | TextField | `not null` | Contenido renderizable (HTML/Markdown) |
| `seo_title` | CharField(128) | nullable | |
| `seo_description` | CharField(320) | nullable | |
| `og_fields` | JSONField | default `dict` | Open Graph específico |
| `is_published` | BooleanField | default `False` | |

**Constraint:** único `(page, locale)`. Contenido **indexable** por idioma (SSR).

---

### 20. AuditEvent

Auditoría de acciones sensibles.

| Campo | Tipo | Constraints | Notas |
|---|---|---|---|
| `actor` | FK→User | nullable | `null` = acción del sistema |
| `verb` | CharField(64) | `not null` | `observation.state_changed` / `ruleset.published` / `dataset.built` / `consent.revoked` |
| `target_type` | CharField(64) | nullable | Modelo/entidad afectada |
| `target_id` | BigIntegerField | nullable | PK de la entidad |
| `metadata` | JSONField | default `dict` | **Sin PII** |
| `correlation_id` | UUIDField | nullable | Para trazar flujos |
| `created_at` | DateTimeField | auto_now_add | |

**Privacidad:** `metadata` nunca contiene PII (email, nombres). Usar `correlation_id` para
trazar sin exponer datos personales.

---

### 21. Contenido estático (no entidad)

Estas piezas no son modelos Django, sino archivos/documentos que viven en el repo:

- **Disclaimer de no afiliación** — texto en `templates/` o páginas legales.
- **Política de privacidad** — `ContentPage` con `page_type=legal`.
- **Términos de uso** — `ContentPage` con `page_type=legal`.
- **Licencia del dataset** — texto referenciado desde la UI de dataset.
- **Plantilla CSV** — `docs/csv_template.csv`.

---

## Resumen de índices planificados

| Entidad | Índices |
|---|---|
| TradeObservation | `(owner, is_lucky, ruleset, observed_at)`, `dedup_hash` |
| MechanicRuleSet | `(mechanic, version)` único, `effective_from`, `effective_to` |
| ContentPageTranslation | `(page, locale)` único |
| SourceClaim | `source`, `ruleset`, `parameter` |
| AnalysisRun | `owner`, `dataset_version`, `ruleset`, `algorithm_version` |
| AuditEvent | `actor`, `verb`, `target_type`, `correlation_id`, `created_at` |

## Resumen de privacidad

| Dato | ¿Se almacena? | ¿Se agrega? | Notas |
|---|---|---|---|
| Email | Sí | No | PII; nunca en logs |
| País | Opcional | Sí | Solo agregado, sin ubicación precisa |
| Nombre de entrenador | No | — | Explícitamente excluido |
| Notes (observación) | Sí | No | Privadas del usuario |
| Atk/Def/HP | Sí | Sí (anonimizado) | Sin identificar al usuario |
| Fecha/hora UTC | Sí | Sí | Sin zona horaria precisa |

## Versionado

- `MechanicRuleSet` — inmutable al publicar; `version` incremental por `mechanic`.
- `DatasetVersion` — inmutable; `number` incremental global.
- `algorithm_version` en `engine/versioning.py` — semver, fijado en cada `AnalysisRun`.
- `DecisionRule.version` — semver, independiente del ruleset.
