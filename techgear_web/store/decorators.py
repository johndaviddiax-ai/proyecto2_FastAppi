from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from . import api

def admin_requerido(vista):
    """Solo deja pasar a quien tenga sesión iniciada y rol administrador.

    Además, si la API rechaza el token mientras la vista trabaja (venció o
    perdió permisos), cierra la sesión y manda al login.
    """

    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.session.get("token"):
            messages.warning(request, "Inicia sesión para entrar al panel administrativo.")
            return redirect("login")
        if request.session.get("rol") != "administrador":
            messages.error(request, "Tu cuenta no tiene permisos para el panel administrativo.")
            return redirect("inicio")
        try:
            return vista(request, *args, **kwargs)
        except api.SesionInvalida:
            request.session.flush()
            messages.warning(request, "Tu sesión expiró. Inicia sesión de nuevo.")
            return redirect("login")

    return envoltura

def login_requerido(vista):
    """Solo deja pasar a quien tenga sesión iniciada (cliente o administrador)."""

    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.session.get("token"):
            messages.warning(request, "Inicia sesión para continuar.")
            return redirect("login")
        try:
            return vista(request, *args, **kwargs)
        except api.SesionInvalida:
            request.session.flush()
            messages.warning(request, "Tu sesión expiró. Inicia sesión de nuevo.")
            return redirect("login")

    return envoltura
