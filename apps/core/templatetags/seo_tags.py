"""Template tags para SEO multilingue y utilidades."""

from html.parser import HTMLParser

from django import template
from django.urls import translate_url

from engine.dps_data import TYPE_COLORS, PokemonType

register = template.Library()

ALLOWED_TAGS = {
    "a",
    "abbr",
    "b",
    "blockquote",
    "br",
    "caption",
    "cite",
    "code",
    "col",
    "colgroup",
    "dd",
    "del",
    "dfn",
    "div",
    "dl",
    "dt",
    "em",
    "figcaption",
    "figure",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "i",
    "img",
    "ins",
    "kbd",
    "li",
    "mark",
    "ol",
    "p",
    "pre",
    "q",
    "s",
    "samp",
    "small",
    "span",
    "strong",
    "sub",
    "sup",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "u",
    "ul",
    "var",
}
ALLOWED_ATTRS = {
    "a": {"href", "title", "rel", "target"},
    "img": {"src", "alt", "width", "height", "loading"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan"},
    "abbr": {"title"},
    "dfn": {"title"},
}
HTTP_URL_SCHEMES = frozenset({"http", "https", "mailto"})
ATTR_PREFIX_KILL = frozenset(
    {
        "on",
        "formaction",
        "form",
        "xlink:href",
        "data",
    }
)


class _Sanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._result: list[str] = []
        self._open_tags: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in ALLOWED_TAGS:
            return
        allowed = ALLOWED_ATTRS.get(tag, set())
        safe_attrs = []
        for k, v in attrs:
            key_lower = k.lower()
            if key_lower in allowed:
                if key_lower == "href" or key_lower == "src":
                    if v.startswith("javascript:") or v.startswith("data:"):
                        continue
                    if ":" in v and not any(v.startswith(s + ":") for s in HTTP_URL_SCHEMES):
                        continue
                safe_attrs.append((k, v))
            elif key_lower == "style":
                continue
            elif key_lower == "class" or (
                tag == "a" and key_lower == "target" and v in ("_blank", "_self", "_top")
            ):
                safe_attrs.append((k, v))
        attr_str = "".join(f' {k}="{self.escape_html(v)}"' for k, v in safe_attrs)
        self._result.append(f"<{tag}{attr_str}>")
        if tag not in (
            "br",
            "hr",
            "img",
            "input",
            "area",
            "base",
            "col",
            "embed",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        ):
            self._open_tags.append(tag)

    def handle_endtag(self, tag):
        if tag not in ALLOWED_TAGS:
            return
        self._result.append(f"</{tag}>")

    def handle_data(self, data):
        self._result.append(self.escape_html(data))

    def handle_entityref(self, name):
        self._result.append(f"&{name};")

    def handle_charref(self, name):
        self._result.append(f"&#{name};")

    @staticmethod
    def escape_html(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def get_safe_html(self) -> str:
        return "".join(self._result)


@register.filter
def safe_html(html_content: str) -> str:
    """Sanitiza HTML permitiendo solo etiquetas y atributos seguros."""
    parser = _Sanitizer()
    parser.feed(html_content)
    return parser.get_safe_html()


@register.simple_tag(takes_context=True)
def change_lang(context, lang: str) -> str:
    """Devuelve la URL actual traducida a otro idioma (p. ej. /en/calculator/)."""
    request = context.get("request")
    if not request:
        return f"/{lang}/"
    return translate_url(request.get_full_path(), lang)


@register.filter
def type_color(type_name: str) -> str:
    """Devuelve el color hex para un tipo Pokémon."""
    try:
        return TYPE_COLORS[PokemonType(type_name)]
    except (ValueError, KeyError):
        return "#A8A77A"
