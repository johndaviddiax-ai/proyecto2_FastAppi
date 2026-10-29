import requests
from django.conf import settings

# Timeout largo: en el plan gratuito de Render la API puede tardar
# cerca de un minuto en despertar.
TIMEOUT = 60

ERROR_CONEXION = "No pudimos conectar con el servidor. Intenta de nuevo en un momento."


def listar_productos():
    """Pide los productos a la API de FastAPI.

    Devuelve (productos, error). Si la API no responde, productos es una
    lista vacía y error trae un mensaje para mostrar en pantalla.
    """
    try:
        respuesta = requests.get(f"{settings.API_URL}/productos", timeout=TIMEOUT)
        respuesta.raise_for_status()
        productos = respuesta.json()
    except (requests.RequestException, ValueError):
        return [], "No pudimos cargar los productos. Intenta de nuevo en un momento."

    # La API devuelve "_id", pero los templates de Django no permiten
    # variables que empiecen con guion bajo. Lo renombramos a "id".
    for producto in productos:
        producto["id"] = producto.pop("_id")
    return productos, None


def _enviar(ruta, datos, error_por_defecto):
    """POST a la API. Devuelve (respuesta_json, error); uno de los dos es None."""
    try:
        respuesta = requests.post(f"{settings.API_URL}{ruta}", json=datos, timeout=TIMEOUT)
    except requests.RequestException:
        return None, ERROR_CONEXION

    try:
        cuerpo = respuesta.json()
    except ValueError:
        return None, ERROR_CONEXION

    if respuesta.status_code in (200, 201):
        return cuerpo, None

    # La API manda el motivo en "detail" como texto. En errores de validación
    # (422) "detail" es una lista técnica, así que mostramos un mensaje claro.
    detalle = cuerpo.get("detail") if isinstance(cuerpo, dict) else None
    return None, detalle if isinstance(detalle, str) else error_por_defecto


def registrar_usuario(nombre, email, password):
    return _enviar(
        "/usuarios/registro",
        {"nombre": nombre, "email": email, "password": password},
        "Revisa los datos: el correo debe ser válido y la contraseña tener mínimo 8 caracteres.",
    )


def iniciar_sesion(email, password, rol):
    return _enviar(
        "/usuarios/login",
        {"email": email, "password": password, "rol": rol},
        "Revisa el correo, la contraseña y el rol elegido.",
    )
