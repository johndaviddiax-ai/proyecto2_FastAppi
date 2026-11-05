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


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        datos, error = api.iniciar_sesion(email, password)
        if error:
            messages.error(request, error)
            # Se devuelve el correo para no obligar a escribirlo de nuevo.
            return render(request, "store/login.html", {"email": email})

        # Sesión nueva (evita reutilizar una sesión anterior) y guarda lo
        # que el resto del sitio necesita saber del usuario.
        request.session.cycle_key()
        request.session["token"] = datos["access_token"]
        request.session["rol"] = datos["usuario"]["rol"]
        request.session["nombre"] = datos["usuario"]["nombre"]
        # La sesión dura lo mismo que el JWT: cuando el token vence, la sesión también.
        request.session.set_expiry(datos["expires_in"])

        # El rol real de la cuenta decide a dónde entra.
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


# ---------- Dashboard del administrador: CRUD de productos ----------

@admin_requerido
def panel_admin(request):
    """Dashboard. READ: lista los productos (GET /productos) y calcula el resumen."""
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
    """Lee el formulario de producto. Devuelve (valores, datos_para_la_api, error).

    Los navegadores solo envían texto, así que aquí se convierten precio y
    stock a número antes de mandarlos a la API.
    """
    campos = ("nombre", "descripcion", "categoria", "precio", "stock", "imagen_url")
    valores = {campo: request.POST.get(campo, "").strip() for campo in campos}

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
    """CREATE: GET muestra el formulario vacío; POST envía POST /productos a la API."""
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
    """UPDATE: GET trae el producto (GET /productos/{id}); POST envía PUT /productos/{id}."""
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

    producto, error = api.obtener_producto(producto_id)
    if error:
        messages.error(request, error)
        return redirect("panel_admin")
    return render(request, "store/producto_form.html", {**contexto, "valores": producto})


@admin_requerido
@require_POST
def producto_eliminar(request, producto_id):
    """DELETE: el botón envía un POST a Django, que manda DELETE /productos/{id} a la API."""
    _, error = api.eliminar_producto(request.session["token"], producto_id)
    if error:
        messages.error(request, error)
    else:
        messages.success(request, "Producto eliminado.")
    return redirect("panel_admin")

def robots_txt(request):
    return HttpResponse("User-agent: *\nDisallow: /panel/\n", content_type="text/plain")
# ---------- Pedidos del cliente ----------

@login_requerido
@require_POST
def comprar(request, producto_id):
    """Crea un pedido de un producto. La API valida el stock y lo descuenta."""
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

    _, error = api.crear_pedido(request.session["token"], producto_id, cantidad)
    if error:
        messages.error(request, error)
    else:
        messages.success(request, "¡Pedido realizado! Lo puedes ver en «Mis pedidos».")
    return redirect("inicio")


@login_requerido
def mis_pedidos(request):
    """Lista los pedidos del usuario con sesión iniciada."""
    pedidos, error = api.mis_pedidos(request.session["token"])
    if error:
        return render(request, "store/mis_pedidos.html", {"pedidos": [], "error": error})

    # La API guarda solo el id del producto; se busca el nombre en el catálogo.
    productos, _ = api.listar_productos()
    nombres = {p["id"]: p["nombre"] for p in productos}

    for pedido in pedidos:
        pedido["codigo"] = pedido["_id"][-6:].upper()
        pedido["id"] = pedido["_id"]
        pedido["lineas"] = [
            {"nombre": nombres.get(i["producto_id"], "Producto eliminado"), "cantidad": i["cantidad"]}
            for i in pedido["items"]
        ]
        # La fecha llega en UTC; se muestra en hora de Colombia.
        fecha = datetime.fromisoformat(pedido["fecha"])
        if fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=timezone.utc)
        pedido["fecha"] = fecha.astimezone(ZoneInfo("America/Bogota")).strftime("%d/%m/%Y %H:%M")

    return render(request, "store/mis_pedidos.html", {"pedidos": pedidos, "error": None})

def robots_txt(request):
    return HttpResponse("User-agent: *\nDisallow: /panel/\n", content_type="text/plain")

@login_requerido
@require_POST
def pedido_cancelar(request, pedido_id):
    """Retira un pedido pendiente. La API devuelve el stock."""
    _, error = api.cancelar_pedido(request.session["token"], pedido_id)
    if error:
        messages.error(request, error)
    else:
        messages.success(request, "Pedido retirado. Los productos volvieron al catálogo.")
    return redirect("mis_pedidos")