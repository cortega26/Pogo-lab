# Registros de Decisiones de Arquitectura (ADR)

Registro **detallado** de las decisiones arquitectónicas **significativas** de Pogo-lab: es la fuente única del
*rationale* (contexto, decisión, consecuencias). El resumen de una línea por decisión vive en
[`../plan.md`](../plan.md) §19, que **enlaza** aquí — no se duplica el razonamiento (DRY).

No toda decisión merece un ADR: solo las **arquitectónicamente significativas** (difíciles de revertir, que definen
la forma del sistema o los límites de dominio). Las decisiones menores/reversibles (librería de gráficos, formato
CSV, etc.) quedan en el resumen de `plan.md` §19.

Formato: MADR simplificado ([`0000-template.md`](0000-template.md)).

| ADR | Título | Estado |
|---|---|:--:|
| [0001](0001-stack-django-htmx-engine-puro.md) | Stack: Django + PostgreSQL + HTMX + motor puro | Aceptada |
| [0002](0002-versionado-inmutable-rulesets.md) | Versionado inmutable de rulesets con procedencia | Aceptada |
| [0003](0003-motor-dominio-puro.md) | Motor de dominio puro `engine/` (DIP, import-linter) | Aceptada |
| [0004](0004-metodos-estadisticos.md) | Métodos estadísticos y comunicación honesta | Aceptada |
| [0005](0005-separacion-datos-privados-publicos.md) | Separación de datos privados/públicos, consentimiento y anonimización | Aceptada |
| [0006](0006-recomendaciones-deterministas.md) | Recomendaciones deterministas sin LLM en runtime | Aceptada |
| [0007](0007-i18n-contenido-indexable.md) | i18n con contenido indexable renderizado en servidor | Aceptada |
| [0008](0008-user-custom-email.md) | Modelo User custom con email como login | Aceptada |

**Nuevo ADR:** copia `0000-template.md`, numéralo secuencialmente, enlázalo en esta tabla. Un ADR **Aceptada** no se
reescribe: si cambia la decisión, se crea uno nuevo y el anterior pasa a **Reemplazada por [ADR-XXXX]** u **Obsoleta**.
