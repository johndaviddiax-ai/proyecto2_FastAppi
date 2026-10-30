from enum import Enum
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.producto import PyObjectId


class RolUsuario(str, Enum):
    cliente = "cliente"
    administrador = "administrador"


class UsuarioCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)
    rol: RolUsuario = RolUsuario.cliente


class UsuarioUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None
    rol: RolUsuario | None = None


class UsuarioOut(BaseModel):
    id: PyObjectId = Field(alias="_id")
    nombre: str
    email: EmailStr
    rol: RolUsuario

    model_config = ConfigDict(populate_by_name=True)


# ---------- Nuevos: registro, login y respuesta con token ----------

class UsuarioRegistro(BaseModel):
    """Datos del registro público. No incluye "rol": toda cuenta nueva es cliente."""
    nombre: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str
    rol: RolUsuario  # el rol con el que la persona quiere entrar


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos que dura el token
    usuario: UsuarioOut
