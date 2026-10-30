import base64
import hashlib
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    # Falla al arrancar en vez de firmar tokens con una clave vacía o por defecto.
    raise RuntimeError("Falta la variable de entorno JWT_SECRET (en .env o en Render).")

ALGORITMO = "HS256"
MINUTOS_EXPIRACION = 60


# ---------- Contraseñas ----------

def _preparar(password: str) -> bytes:
    # bcrypt solo lee los primeros 72 bytes; con este paso previo siempre
    # recibe 44 bytes, sin importar qué tan larga sea la contraseña.
    return base64.b64encode(hashlib.sha256(password.encode("utf-8")).digest())


def hashear_password(password: str) -> str:
    return bcrypt.hashpw(_preparar(password), bcrypt.gensalt()).decode("utf-8")


def verificar_password(password: str, hash_guardado: str) -> bool:
    try:
        return bcrypt.checkpw(_preparar(password), hash_guardado.encode("utf-8"))
    except ValueError:
        return False


# ---------- JWT ----------

def crear_token(usuario: dict) -> tuple[str, int]:
    """Firma un JWT con los datos del usuario. Devuelve (token, segundos de vida)."""
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario["_id"]),
        "email": usuario["email"],
        "nombre": usuario["nombre"],
        "rol": usuario["rol"],
        "iat": ahora,
        "exp": ahora + timedelta(minutes=MINUTOS_EXPIRACION),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITMO)
    return token, MINUTOS_EXPIRACION * 60


esquema_bearer = HTTPBearer(auto_error=False)


def usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
) -> dict:
    """Dependencia de FastAPI: lee y valida el token del encabezado Authorization."""
    if credenciales is None:
        raise HTTPException(401, "Falta el token de acceso", headers={"WWW-Authenticate": "Bearer"})
    try:
        return jwt.decode(credenciales.credentials, JWT_SECRET, algorithms=[ALGORITMO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "El token expiró, inicia sesión de nuevo", headers={"WWW-Authenticate": "Bearer"})
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Token inválido", headers={"WWW-Authenticate": "Bearer"})


def solo_admin(payload: dict = Depends(usuario_actual)) -> dict:
    """Dependencia de FastAPI: exige un token válido cuyo rol sea administrador."""
    if payload.get("rol") != "administrador":
        raise HTTPException(403, "Solo un administrador puede hacer esto")
    return payload
