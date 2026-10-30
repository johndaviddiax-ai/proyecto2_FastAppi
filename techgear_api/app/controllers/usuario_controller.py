from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.database import usuarios_collection
from app.models.usuario import RolUsuario, UsuarioRegistro
from app.security import hashear_password, verificar_password


def registrar(datos: UsuarioRegistro) -> dict:
    # Índice único: Mongo mismo impide dos cuentas con el mismo correo.
    usuarios_collection.create_index("email", unique=True)
    documento = {
        "nombre": datos.nombre.strip(),
        "email": datos.email.lower(),
        "password_hash": hashear_password(datos.password),
        "rol": RolUsuario.cliente.value,  # el registro público SIEMPRE crea clientes
    }
    try:
        usuarios_collection.insert_one(documento)  # agrega "_id" al documento
    except DuplicateKeyError:
        raise ValueError("Ya existe una cuenta con ese correo")
    return documento


def autenticar(email: str, password: str, rol: RolUsuario) -> dict:
    usuario = usuarios_collection.find_one({"email": email.lower()})
    # Mismo mensaje si el correo no existe o la contraseña falla: no revela cuál.
    if not usuario or not verificar_password(password, usuario["password_hash"]):
        raise ValueError("Correo o contraseña incorrectos")
    # Aquí la contraseña ya es correcta: ahora se compara el rol elegido con el REAL.
    if usuario["rol"] != rol.value:
        if usuario["rol"] == RolUsuario.administrador.value:
            raise PermissionError("Esta cuenta es de administrador. Elige Administrador para ingresar")
        raise PermissionError("Esta cuenta no tiene permisos de administrador")
    return usuario


def obtener_por_id(id: str) -> dict | None:
    if not ObjectId.is_valid(id):
        return None
    return usuarios_collection.find_one({"_id": ObjectId(id)})
