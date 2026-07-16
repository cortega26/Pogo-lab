"""Template tags para SEO multilingue."""

from django import template
from django.urls import resolve, reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def change_lang(context, lang: str) -> str:
    """Devuelve la URL actual en otro idioma.

    Uso: {% change_lang "en" %} -> /en/ruta/actual/
    """
    request = context["request"]
    try:
        url_parts = resolve(request.path_info)
        url = reverse(
            url_parts.view_name,
            args=url_parts.args,
            kwargs=url_parts.kwargs,
        )
        return f"/{lang}{url}"
    except Exception:
        return request.path
