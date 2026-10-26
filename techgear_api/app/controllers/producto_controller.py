from bson import ObjectId
from pymongo import ReturnDocument
from app.database import productos_collection
from app.models.producto import ProductoCreate, ProductoUpdate


def _convertir_id(id: str) -> ObjectId | None:
    """Devuelve el ObjectId, o None si el id no tiene formato válido."""
    return ObjectId(id) if ObjectId.is_valid(id) else None


def crear(producto: ProductoCreate) -> dict:
    data = producto.model_dump()
    productos_collection.insert_one(data)  # agrega "_id" a data
    return data


def listar() -> list[dict]:
    return list(productos_collection.find())


def obtener_por_id(id: str) -> dict | None:
    object_id = _convertir_id(id)
    if object_id is None:
        return None
    return productos_collection.find_one({"_id": object_id})


def actualizar(id: str, cambios: dict) -> dict | None:
    object_id = _convertir_id(id)
    if object_id is None:
        return None
    return productos_collection.find_one_and_update(
        {"_id": object_id},
        {"$set": cambios},
        return_document=ReturnDocument.AFTER,
    )


def eliminar(id: str) -> bool:
    object_id = _convertir_id(id)
    if object_id is None:
        return False
    return productos_collection.delete_one({"_id": object_id}).deleted_count > 0