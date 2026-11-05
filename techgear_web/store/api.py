from urllib.parse import quote

import requests
from django.conf import settings

# Timeout largo: en el plan gratuito de Render la API puede tardar
# cerca de un minuto en despertar.
TIMEOUT = 60

ERROR_CONEXION = "No pudimos conectar con el servidor. Intenta de nuevo en un momento."


class SesionInvalida(Exception):
    """La API rechazó el token (venció o ya no tiene permisos de administrador)."""


def _solicitar(metodo, ruta, *, token=None, datos=None, error_por_defecto=None, timeout=TIMEOUT):
    """Envía una petición a la API. Devuelve (cuerpo_json, error); uno de los dos es None.

    Si se manda un token, va en el encabezado Authorization (Bearer). Si con
    token la API responde 401 o 403, se lanza SesionInvalida.
    """
    cabeceras = {"Authorization": f"Bearer {token}"} if token else {}
    try:
                respuesta = requests.request(
            metodo, f"{settings.API_URL}{ruta}", json=datos, headers=cabeceras, timeout=timeout
        )
    except requests.RequestException:
        return None, ERROR_CONEXION

    try:
        cuerpo = respuesta.json()
    except ValueError:
        return None, ERROR_CONEXION

    if token and respuesta.status_code in (401, 403):
        raise SesionInvalida()

    if respuesta.status_code in (200, 201):
        return cuerpo, None

    # La API manda el motivo en "detail". Si es texto, se muestra tal cual.
    detalle = cuerpo.get("detail") if isinstance(cuerpo, dict) else None
    if isinstance(detalle, str):
        return None, detalle
    if error_por_defecto:
        return None, error_por_defecto
    # En errores de validación (422) "detail" es una lista técnica: se resume
    # en los nombres de los campos con problemas.
    if isinstance(detalle, list):
        campos = sorted({str(e["loc"][-1]) for e in detalle if isinstance(e, dict) and e.get("loc")})
        if campos:
            return None, "Revisa estos campos: " + ", ".join(campos) + "."
    return None, "No se pudo completar la operación."


# ---------- Productos ----------

def _con_id(producto):
    # La API devuelve "_id", pero los templates de Django no permiten
    # variables que empiecen con guion bajo. Lo renombramos a "id".
    producto["id"] = producto.pop("_id")
    return producto


def listar_productos():
    """GET /productos. Devuelve (productos, error)."""
    productos, error = _solicitar("GET", "/productos", timeout=8)
    if error:
        return [], "No pudimos cargar los productos. Intenta de nuevo en un momento."
    return [_con_id(p) for p in productos], None


def obtener_producto(producto_id):
    """GET /productos/{id}. Devuelve (producto, error)."""
    producto, error = _solicitar("GET", f"/productos/{quote(producto_id, safe='')}")
    return (_con_id(producto) if producto else None), error


def crear_producto(token, datos):
    """POST /productos (solo administrador)."""
    return _solicitar("POST", "/productos", token=token, datos=datos)


def actualizar_producto(token, producto_id, datos):
    """PUT /productos/{id} (solo administrador)."""
    return _solicitar("PUT", f"/productos/{quote(producto_id, safe='')}", token=token, datos=datos)


def eliminar_producto(token, producto_id):
    """DELETE /productos/{id} (solo administrador)."""
    return _solicitar("DELETE", f"/productos/{quote(producto_id, safe='')}", token=token)


# ---------- Usuarios ----------

def registrar_usuario(nombre, email, password):
    return _solicitar(
        "POST",
        "/usuarios/registro",
        datos={"nombre": nombre, "email": email, "password": password},
        error_por_defecto="Revisa los datos: el correo debe ser válido y la contraseña tener mínimo 8 caracteres.",
    )


def iniciar_sesion(email, password):
    return _solicitar(
        "POST",
        "/usuarios/login",
        datos={"email": email, "password": password},
        error_por_defecto="Revisa el correo y la contraseña.",
    )
    # ---------- Pedidos ----------

def crear_pedido(token, producto_id, cantidad):
    """POST /pedidos (requiere sesión). El comprador lo decide el token."""
    return _solicitar(
        "POST",
        "/pedidos",
        token=token,
        datos={"items": [{"producto_id": producto_id, "cantidad": cantidad}]},
    )


def mis_pedidos(token):
    """GET /pedidos/mios. Devuelve (pedidos, error)."""
    return _solicitar("GET", "/pedidos/mios", token=token)

def cancelar_pedido(token, pedido_id):
    """PUT /pedidos/{id}/cancelar (solo el dueño del pedido)."""
    return _solicitar("PUT", f"/pedidos/{quote(pedido_id, safe='')}/cancelar", token=token)