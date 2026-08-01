"""Template tags de la app calculators."""

from django import template

register = template.Library()


@register.filter
def choice_label(choices, key):
    """Devuelve la etiqueta legible de una lista de choices (val, label) dado su val."""
    for val, label in choices:
        if val == key:
            return label
    return ""
