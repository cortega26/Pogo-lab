from django.shortcuts import render


def healthz(request):
    return render(request, "core/healthz.html")
