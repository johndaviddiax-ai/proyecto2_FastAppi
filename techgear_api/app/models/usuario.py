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