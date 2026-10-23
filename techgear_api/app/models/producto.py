from typing import Annotated
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

# Convierte el ObjectId de Mongo a string
PyObjectId = Annotated[str, BeforeValidator(str)]


class ProductoCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    descripcion: str = ""
    categoria: str
    precio: float = Field(gt=0)
    stock: int = Field(ge=0)
    imagen_url: str | None = None


class ProductoUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=100)
    descripcion: str | None = None
    categoria: str | None = None
    precio: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    imagen_url: str | None = None


class ProductoOut(ProductoCreate):
    id: PyObjectId = Field(alias="_id")

    model_config = ConfigDict(populate_by_name=True)