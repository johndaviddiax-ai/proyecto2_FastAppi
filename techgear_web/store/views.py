from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from . import api
from .decorators import admin_requerido


def inicio(request):
    productos, error = api.listar_productos()
    return render(request, "store/inicio.html", {"productos": productos, "error": error})


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        rol = request.POST.get("rol", "cliente")

        datos, error = api.iniciar_sesion(email, password, rol)
        if error:
            messages.error(request, error)
            # Se devuelven correo y rol para no obligar a escribirlos de nuevo.
            return render(request, "store/login.html", {"email": email, "rol": rol})

        # Sesión nueva (evita reutilizar una sesión anterior) y guarda lo
        # que el resto del sitio necesita saber del usuario.
        request.session.cycle_key()
        request.session["token"] = datos["access_token"]
        request.session["rol"] = datos["usuario"]["rol"]
        request.session["nombre"] = datos["usuario"]["nombre"]
        # La sesión dura lo mismo que el JWT: cuando el token vence, la sesión también.
        request.session.set_expiry(datos["expires_in"])

        if datos["usuario"]["rol"] == "administrador":
            return redirect("panel_admin")
        return redirect("inicio")

    return render(request, "store/login.html")


def registro_view(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        contexto = {"nombre": nombre, "email": email}

        if password != password2:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, "store/registro.html", contexto)

        _, error = api.registrar_usuario(nombre, email, password)
        if error:
            messages.error(request, error)
            return render(request, "store/registro.html", contexto)

        messages.success(request, "Cuenta creada. Ya puedes iniciar sesión.")
        return redirect("login")

    return render(request, "store/registro.html")


@require_POST
def logout_view(request):
    request.session.flush()  # borra token, rol y nombre de la sesión
    return redirect("inicio")


@admin_requerido
def panel_admin(request):
    productos, error = api.listar_productos()
    return render(request, "store/panel_admin.html", {"productos": productos, "error": error})
