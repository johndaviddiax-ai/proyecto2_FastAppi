import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from . import api
from .decorators import admin_requerido, login_requerido


def inicio(request):
    productos, error = api.listar_productos()
    return render(request, "store/inicio.html", {"productos": productos, "error": error})


def robots_txt(request):
    return HttpResponse("User-agent: *\nAllow: /\n", content_type="text/plain")


# ---------- Login, registro y logout ----------

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        datos, error = api.iniciar_sesion(email, password)
        if error:
            messages.error(request, error)
            # devolvemos el correo para que no lo escriba otra vez
            return render(request, "store/login.html", {"email": email})

        # guardamos en la sesión lo que necesitamos del usuario
        request.session.cycle_key()
        request.session["token"] = datos["access_token"]
        request.session["rol"] = datos["usuario"]["rol"]
        request.session["nombre"] = datos["usuario"]["nombre"]
        # la sesión dura lo mismo que el token
        request.session.set_expiry(datos["expires_in"])

        # según el rol de la cuenta, va al panel o al catálogo
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
    request.session.flush()
    return redirect("inicio")


# ---------- Panel del administrador (CRUD de productos) ----------

@admin_requerido
def panel_admin(request):
    productos, error = api.listar_productos()
    resumen = {
        "total": len(productos),
        "unidades": sum(p["stock"] for p in productos),
        "agotados": sum(1 for p in productos if p["stock"] == 0),
    }
    return render(request, "store/panel_admin.html", {
        "productos": productos, "error": error, "resumen": resumen,
    })


def _leer_formulario(request):
    # lee el formulario del producto y devuelve (valores, datos para la API, error)
    campos = ("nombre", "descripcion", "categoria", "precio", "stock", "imagen_url")
    valores = {campo: request.POST.get(campo, "").strip() for campo in campos}
    
    if not 10 <= len(valores["descripcion"]) <= 200:
        return valores, None, "La descripción debe tener entre 10 y 200 caracteres."

    if valores["imagen_url"] and not valores["imagen_url"].startswith("https://"):
        return valores, None, "La URL de la imagen debe empezar por https://."
    if not valores["nombre"] or not valores["categoria"]:
        return valores, None, "El nombre y la categoría son obligatorios."

    try:
        precio = float(valores["precio"])
        stock = int(valores["stock"])
    except ValueError:
        return valores, None, "El precio debe ser un número y el stock un número entero."
    if not math.isfinite(precio):
        return valores, None, "El precio debe ser un número válido."

    datos = {
        "nombre": valores["nombre"],
        "descripcion": valores["descripcion"],
        "categoria": valores["categoria"],
        "precio": precio,
        "stock": stock,
        "imagen_url": valores["imagen_url"] or None,
    }
    return valores, datos, None


@admin_requerido
def producto_nuevo(request):
    if request.method == "POST":
        valores, datos, error = _leer_formulario(request)
        if not error:
            _, error = api.crear_producto(request.session["token"], datos)
        if error:
            messages.error(request, error)
            return render(request, "store/producto_form.html", {"valores": valores, "modo": "crear"})
        messages.success(request, f"Producto «{datos['nombre']}» creado.")
        return redirect("panel_admin")

    return render(request, "store/producto_form.html", {"valores": {}, "modo": "crear"})


@admin_requerido
def producto_editar(request, producto_id):
    contexto = {"modo": "editar", "producto_id": producto_id}

    if request.method == "POST":
        valores, datos, error = _leer_formulario(request)
        if not error:
            _, error = api.actualizar_producto(request.session["token"], producto_id, datos)
        if error:
            messages.error(request, error)
            return render(request, "store/producto_form.html", {**contexto, "valores": valores})
        messages.success(request, f"Producto «{datos['nombre']}» actualizado.")
        return redirect("panel_admin")

    # GET: trae el producto para llenar el formulario
    producto, error = api.obtener_producto(producto_id)
    if error:
        messages.error(request, error)
        return redirect("panel_admin")
    return render(request, "store/producto_form.html", {**contexto, "valores": producto})


@admin_requerido
@require_POST
def producto_eliminar(request, producto_id):
    _, error = api.eliminar_producto(request.session["token"], producto_id)
    if error:
        messages.error(request, error)
    else:
        messages.success(request, "Producto eliminado.")
    return redirect("panel_admin")


# ---------- Pedidos del cliente ----------

@login_requerido
@require_POST
def comprar(request, producto_id):
    # solo los clientes pueden comprar
    if request.session.get("rol") != "cliente":
        messages.error(request, "Solo las cuentas de cliente pueden comprar.")
        return redirect("inicio")

    try:
        cantidad = int(request.POST.get("cantidad", "1"))
    except ValueError:
        cantidad = 0
    if cantidad < 1:
        messages.error(request, "La cantidad debe ser al menos 1.")
        return redirect("inicio")

    # la API revisa el stock y lo descuenta
    _, error = api.crear_pedido(request.session["token"], producto_id, cantidad)
    if error:
        messages.error(request, error)
    else:
        messages.success(request, "¡Pedido realizado! Lo puedes ver en «Mis pedidos».")
    return redirect("inicio")


@login_requerido
def mis_pedidos(request):
    pedidos, error = api.mis_pedidos(request.session["token"])
    if error:
        return render(request, "store/mis_pedidos.html", {"pedidos": [], "error": error})

    # el pedido solo guarda el id del producto, así que buscamos el nombre en el catálogo
    productos, error_productos = api.listar_productos()
    nombres = {p["id"]: p["nombre"] for p in productos}
    sin_nombre = "Producto" if error_productos else "Producto eliminado"

    for pedido in pedidos:
        pedido["codigo"] = pedido["_id"][-6:].upper()
        pedido["id"] = pedido["_id"]
        pedido["lineas"] = [
            {"nombre": nombres.get(i["producto_id"], sin_nombre), "cantidad": i["cantidad"]}
            for i in pedido["items"]
        ]
        # la fecha llega en UTC, la pasamos a hora de Colombia
        fecha = datetime.fromisoformat(pedido["fecha"])
        if fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=timezone.utc)
        pedido["fecha"] = fecha.astimezone(ZoneInfo("America/Bogota")).strftime("%d/%m/%Y %H:%M")

    return render(request, "store/mis_pedidos.html", {"pedidos": pedidos, "error": None})


@login_requerido
@require_POST
def pedido_cancelar(request, pedido_id):
    # la API cancela el pedido y devuelve el stock
    _, error = api.cancelar_pedido(request.session["token"], pedido_id)
    if error:
        messages.error(request, error)
    else:
        messages.success(request, "Pedido retirado. Los productos volvieron al catálogo.")
    return redirect("mis_pedidos")