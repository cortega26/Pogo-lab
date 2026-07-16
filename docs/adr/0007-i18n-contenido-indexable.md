# ADR-0007 — i18n con contenido indexable renderizado en servidor

- **Estado:** Aceptada
- **Fecha:** 2026-07-16
- **Relacionadas:** `plan.md` §4.10, §4.11, §19-#9 · ADR-0001

## Contexto

Pogo-lab es content/SEO-first y debe operar en es/en desde el inicio (pt preparado). Traducir solo cadenas del lado
del cliente no es una estrategia SEO multilingüe: el contenido editorial debe ser **indexable por idioma**.

## Decisión

- **Cadenas de UI:** `gettext` (`.po`/`.mo`) con `LocaleMiddleware` y `i18n_patterns` → rutas `/es/`, `/en/`
  (pt preparado).
- **Contenido editorial:** modelos `ContentPage` + `ContentPageTranslation` (por locale), **renderizado en servidor**.
- **SEO:** `hreflang` entre variantes, canonical, sitemaps **por idioma**, Open Graph localizado.
- El **motor matemático y el dataset son compartidos** entre idiomas; solo cambia la capa de presentación y los
  formatos de fecha/número (l10n de Django).

## Alternativas consideradas

- **Traducción solo en cliente (JS).** Contenido no indexable, mala SEO multilingüe, peor rendimiento inicial.
- **Un sitio por idioma duplicado.** Duplica lógica y datos (viola DRY) y multiplica el mantenimiento.

## Consecuencias

- **Positivas:** contenido indexable y rápido; una sola base de datos/motor; añadir pt es incremental.
- **Negativas / costes:** gestionar traducciones de UI (`.po`) y de contenido (`ContentPageTranslation`) por separado.
- **Mitigaciones:** el mapa SSOT mantiene el dato una sola vez; la calculadora comparte estado vía query params
  entre idiomas.

## Reversibilidad

Media. La arquitectura SSR + `i18n_patterns` es estándar de Django; migrar a otra estrategia i18n sería costoso pero
el contenido está normalizado por locale, lo que facilita cualquier transición.
