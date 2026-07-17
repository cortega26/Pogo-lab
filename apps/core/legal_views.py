from django.shortcuts import render


def disclaimer(request):
    return render(request, "legal/disclaimer.html")


def privacy(request):
    return render(request, "legal/privacy.html")


def tos(request):
    return render(request, "legal/tos.html")
