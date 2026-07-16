from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def export_data(request):
    """Exporta los datos del usuario en CSV.

    Stub: implementación completa en M7.
    """
    return render(request, "accounts/export.html")


@login_required
def delete_account(request):
    """Elimina la cuenta y anonimiza/borra datos asociados.

    Stub: implementación completa en M7.
    """
    return render(request, "accounts/delete.html")
