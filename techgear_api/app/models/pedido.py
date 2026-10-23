from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from app.models.producto import PyObjectId


class EstadoPedido(str, Enum):
    pendiente = "pendiente"
    enviado = "enviado"
    entregado = "entregado"
    cancelado = "cancelado"


class ItemPedido(BaseModel):
    producto_id: str
    cantidad: int = Field(gt=0)


class PedidoCreate(BaseModel):
    cliente_id: str  # id del usuario de Django
    items: list[ItemPedido] = Field(min_length=1)


class PedidoOut(BaseModel):
    id: PyObjectId = Field(alias="_id")
    cliente_id: str
    items: list[ItemPedido]
    total: float
    estado: EstadoPedido = EstadoPedido.pendiente
    fecha: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)