from django.shortcuts import get_object_or_404, render
from django.utils.translation import get_language

from .models import ContentPage, ContentPageTranslation


def content_page(request, slug):
    page = get_object_or_404(ContentPage, slug=slug, status="published")
    locale = get_language()
    translation = get_object_or_404(
        ContentPageTranslation,
        page=page,
        locale=locale,
        is_published=True,
    )
    return render(
        request,
        "content/page.html",
        {
            "page": page,
            "translation": translation,
        },
    )
