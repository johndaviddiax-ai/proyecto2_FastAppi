from fastapi import Depends, FastAPI, HTTPException, status
from app.controllers import producto_controller as productos
from app.models.producto import ProductoCreate, ProductoOut, ProductoUpdate

from app.controllers import pedidos_controller as pedidos
from app.models.pedido import PedidoCreate, PedidoOut

from app.controllers import usuario_controller as usuarios
from app.models.usuario import TokenOut, UsuarioLogin, UsuarioOut, UsuarioRegistro
from app.security import crear_token, solo_admin, usuario_actual

app = FastAPI(title="TechGear API", version="1.0.0")


@app.post("/productos", response_model=ProductoOut, status_code=status.HTTP_201_CREATED,
          dependencies=[Depends(solo_admin)])
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


@app.put("/productos/{id}", response_model=ProductoOut, dependencies=[Depends(solo_admin)])
def actualizar_producto(id: str, producto: ProductoUpdate):
    cambios = producto.model_dump(exclude_unset=True)
    if not cambios:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")
    actualizado = productos.actualizar(id, cambios)
    if not actualizado:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return actualizado


@app.delete("/productos/{id}", dependencies=[Depends(solo_admin)])
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


# ---------- Usuarios ----------

@app.post("/usuarios/registro", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def registrar_usuario(datos: UsuarioRegistro):
    try:
        return usuarios.registrar(datos)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error))


@app.post("/usuarios/login", response_model=TokenOut)
def iniciar_sesion(datos: UsuarioLogin):
    try:
        usuario = usuarios.autenticar(datos.email, datos.password, datos.rol)
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error))
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error))
    token, segundos = crear_token(usuario)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": segundos,
        "usuario": usuario,
    }


@app.get("/usuarios/me", response_model=UsuarioOut)
def mi_perfil(payload: dict = Depends(usuario_actual)):
    usuario = usuarios.obtener_por_id(payload["sub"])
    if not usuario:
        raise HTTPException(status_code=401, detail="El usuario ya no existe")
    return usuario
