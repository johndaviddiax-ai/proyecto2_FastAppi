from datetime import datetime, timezone
from bson import ObjectId
from app.database import pedidos_collection, productos_collection
from app.models.pedido import EstadoPedido, PedidoCreate


def crear(pedido: PedidoCreate) -> dict:
    # Une los items repetidos del mismo producto
    cantidades: dict[str, int] = {}
    for item in pedido.items:
        cantidades[item.producto_id] = cantidades.get(item.producto_id, 0) + item.cantidad

    # Primero valida y luego calcula el total
    total = 0.0
    for producto_id, cantidad in cantidades.items():
        producto = None
        if ObjectId.is_valid(producto_id):
            producto = productos_collection.find_one({"_id": ObjectId(producto_id)})
        if not producto:
            raise ValueError(f"Producto no encontrado: {producto_id}")
        if producto["stock"] < cantidad:
            raise ValueError(
                f"Stock insuficiente para '{producto['nombre']}' "
                f"(disponible: {producto['stock']})"
            )
        total += producto["precio"] * cantidad

    # Si todo es válido, descuenta el stock
    for producto_id, cantidad in cantidades.items():
        productos_collection.update_one(
            {"_id": ObjectId(producto_id)},
            {"$inc": {"stock": -cantidad}},
        )

    data = {
        "cliente_id": pedido.cliente_id,
        "items": [{"producto_id": pid, "cantidad": cant} for pid, cant in cantidades.items()],
        "total": round(total, 2),
        "estado": EstadoPedido.pendiente.value,
        "fecha": datetime.now(timezone.utc),
    }
    pedidos_collection.insert_one(data)  # agrega "_id" a data
    return data