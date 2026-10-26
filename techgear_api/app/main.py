from fastapi import FastAPI, HTTPException, status
from app.controllers import producto_controller as productos
from app.models.producto import ProductoCreate, ProductoOut, ProductoUpdate

from app.controllers import pedidos_controller as pedidos
from app.models.pedido import PedidoCreate, PedidoOut

app = FastAPI(title="TechGear API", version="1.0.0")


@app.post("/productos", response_model=ProductoOut, status_code=status.HTTP_201_CREATED)
def crear_producto(producto: ProductoCreate):
    return productos.crear(producto)


@app.get("/productos", response_model=list[ProductoOut])
def listar_productos():
    return productos.listar()


@app.get("/productos/{id}", response_model=ProductoOut)
def obtener_producto(id: str):
    producto = productos.obtener_por_id(id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


@app.put("/productos/{id}", response_model=ProductoOut)
def actualizar_producto(id: str, producto: ProductoUpdate):
    cambios = producto.model_dump(exclude_unset=True)
    if not cambios:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")
    actualizado = productos.actualizar(id, cambios)
    if not actualizado:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return actualizado


@app.delete("/productos/{id}")
def eliminar_producto(id: str):
    if not productos.eliminar(id):
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"mensaje": "Producto eliminado correctamente"}

@app.post("/pedidos", response_model=PedidoOut, status_code=status.HTTP_201_CREATED)
def crear_pedido(pedido: PedidoCreate):
    try:
        return pedidos.crear(pedido)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))