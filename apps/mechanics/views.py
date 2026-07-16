from django.db import models
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Mechanic, MechanicRuleSet


def mechanic_list(request):
    mechanics = Mechanic.objects.filter(status="active").order_by("sort_order")
    return render(request, "mechanics/list.html", {"mechanics": mechanics})


def mechanic_detail(request, slug):
    mechanic = get_object_or_404(Mechanic, slug=slug, status="active")
    now = timezone.now()
    ruleset = (
        MechanicRuleSet.objects.filter(
            mechanic=mechanic,
            is_published=True,
            effective_from__lte=now,
        )
        .filter(
            models.Q(effective_to__isnull=True) | models.Q(effective_to__gt=now),
        )
        .order_by("-version")
        .first()
    )
    return render(
        request,
        "mechanics/detail.html",
        {
            "mechanic": mechanic,
            "ruleset": ruleset,
        },
    )
