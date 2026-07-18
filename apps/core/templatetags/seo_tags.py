"""Template tags para SEO multilingue."""

from django import template
from django.urls import translate_url

register = template.Library()


@register.simple_tag(takes_context=True)
def change_lang(context, lang: str) -> str:
    """Devuelve la URL actual traducida a otro idioma (p. ej. /en/calculator/)."""
    request = context.get("request")
    if not request:
        return f"/{lang}/"
    return translate_url(request.get_full_path(), lang)
