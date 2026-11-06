# TechGear - Sistema híbrido de catálogo y pedidos

Aplicación web para una tienda de hardware y accesorios tecnológicos. Combina una **API REST con FastAPI** (que maneja el catálogo, los pedidos y los usuarios sobre MongoDB Atlas) y un **portal web con Django** (patrón MVT) que consume esa API para mostrar el catálogo y permitir comprar.

**Autor:** John David Diaz Correa

## Enlaces

- API desplegada en Render (Swagger UI): https://proyecto2-fastappi.onrender.com/docs
- Portal web desplegado en Vercel: https://proyecto2-fast-appi.vercel.app
- Repositorio: https://github.com/johndaviddiax-ai/proyecto2_FastAppi

> La API usa el plan gratuito de Render: si lleva un rato sin uso se "duerme" y la primera petición puede tardar cerca de un minuto.

## Descripción

El sistema tiene dos roles:

**Cliente**
- Se registra e inicia sesión.
- Ve el catálogo con los productos disponibles.
- Compra un producto indicando la cantidad. La API valida el stock y lo descuenta.
- Consulta sus compras en **Mis pedidos** y puede retirar un pedido pendiente (el stock vuelve al catálogo).

**Administrador**
- Entra al panel administrativo con el mismo formulario de inicio de sesión (el rol de la cuenta decide a dónde se entra).
- Crea, edita y elimina productos (nombre, categoría, descripción, precio, stock e imagen por URL).
- Ve el resumen del inventario: productos, unidades en stock y agotados.

Otras características:
- Validación estricta de datos de entrada y salida con Pydantic.
- Autenticación con tokens JWT; las contraseñas se guardan cifradas (bcrypt).
- Manejo de errores: avisos claros cuando la API no responde, cuando no hay stock suficiente y páginas propias de error 404 y 500.

## Tecnologías y librerías

| Capa | Tecnología | Para qué se usa |
|---|---|---|
| API | Python, FastAPI, Uvicorn | Servicio REST y documentación Swagger |
| API | Pydantic, email-validator | Esquemas y validación de datos |
| API | PyMongo, MongoDB Atlas | Base de datos no relacional en la nube |
| API | PyJWT, bcrypt | Tokens de sesión y cifrado de contraseñas |
| API | python-dotenv | Lectura de variables de entorno |
| Web | Django (MVT) | Vistas, plantillas y sesiones |
| Web | requests | Consumo de la API por HTTP |
| Web | WhiteNoise | Servir los archivos estáticos en producción |
| Despliegue | Render (API) y Vercel (web) | Publicación en la nube |
| Control de versiones | Git y GitHub | Rama `main`, commits progresivos |

## Estructura del proyecto

```
proyecto2_FastAppi/
├── manage.py
├── requirements.txt              # dependencias de Django
├── vercel.json                   # configuración de despliegue en Vercel
├── README.md
├── techgear_api/                 # API (FastAPI)
│   ├── requirements.txt          # dependencias de la API
│   └── app/
│       ├── main.py               # endpoints
│       ├── database.py           # conexión a MongoDB Atlas
│       ├── security.py           # contraseñas y tokens JWT
│       ├── controllers/          # lógica con la base de datos
│       │   ├── producto_controller.py
│       │   ├── pedidos_controller.py
│       │   └── usuario_controller.py
│       └── models/               # esquemas Pydantic
│           ├── producto.py
│           ├── pedido.py
│           └── usuario.py
└── techgear_web/                 # Proyecto Django
    ├── settings.py
    ├── urls.py
    ├── wsgi.py
    └── store/                    # App principal
        ├── views.py              # vistas
        ├── urls.py               # rutas
        ├── api.py                # cliente HTTP que consume la API
        ├── decorators.py         # control de acceso por rol
        ├── templates/            # plantillas HTML (incluye 404 y 500)
        └── static/store/css/     # estilos
```

## Instalación y ejecución local

Requisitos: Python 3.12 o superior, Git y una cuenta de MongoDB Atlas.

**1. Clonar el repositorio**

```bash
git clone https://github.com/johndaviddiax-ai/proyecto2_FastAppi.git
cd proyecto2_FastAppi
```

**2. Crear y activar el entorno virtual**

```powershell
# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1
```

```bash
# Mac / Linux
python3 -m venv venv
source venv/bin/activate
```

**3. Instalar las dependencias**

```bash
pip install -r techgear_api/requirements.txt
pip install -r requirements.txt
```

**4. Crear el archivo `techgear_api/.env`** (ver la sección de variables de entorno).

**5. Levantar la API** (primera terminal):

```bash
cd techgear_api
uvicorn app.main:app --reload
```

La API queda en http://127.0.0.1:8000 y su documentación en http://127.0.0.1:8000/docs

**6. Levantar el portal web** (segunda terminal, con el entorno virtual activo y desde la carpeta raíz del repositorio):

```bash
python manage.py runserver 8001
```

El portal queda en http://127.0.0.1:8001. Se usa el puerto 8001 porque el 8000 ya lo ocupa la API.

## Variables de entorno

**API** (`techgear_api/.env`, este archivo no se sube a GitHub):

```
MONGO_URI=mongodb+srv://USUARIO:PASSWORD@CLUSTER.mongodb.net/?appName=Cluster0
JWT_SECRET=una_clave_larga_y_secreta
```

| Variable | Descripción |
|---|---|
| `MONGO_URI` | Cadena de conexión del cluster de MongoDB Atlas |
| `JWT_SECRET` | Clave con la que se firman los tokens de sesión |

**Portal web:**

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `API_URL` | Dirección de la API | `http://127.0.0.1:8000` |

En producción (Vercel) `API_URL` se configura como variable de entorno del proyecto apuntando a la API de Render.

## Crear una cuenta de administrador

El registro público siempre crea cuentas de **cliente**. Para tener un administrador:

1. Regístrate normalmente desde el portal.
2. En MongoDB Atlas abre la colección `usuarios` de la base `techgear`.
3. Edita tu usuario y cambia el campo `rol` de `cliente` a `administrador`.
4. Cierra sesión y vuelve a entrar: el sistema te lleva al panel administrativo.

## Endpoints de la API

| Método | Ruta | Descripción | Acceso |
|---|---|---|---|
| POST | `/usuarios/registro` | Crea una cuenta de cliente | Público |
| POST | `/usuarios/login` | Devuelve el token de sesión | Público |
| GET | `/usuarios/me` | Datos del usuario con sesión | Con sesión |
| GET | `/productos` | Lista los productos | Público |
| GET | `/productos/{id}` | Detalle de un producto | Público |
| POST | `/productos` | Crea un producto | Administrador |
| PUT | `/productos/{id}` | Edita un producto | Administrador |
| DELETE | `/productos/{id}` | Elimina un producto | Administrador |
| POST | `/pedidos` | Crea un pedido, valida y descuenta el stock | Con sesión |
| GET | `/pedidos/mios` | Lista los pedidos del usuario | Con sesión |
| PUT | `/pedidos/{id}/cancelar` | Cancela un pedido pendiente y devuelve el stock | Con sesión (dueño del pedido) |

Para probar los endpoints protegidos en Swagger: inicia sesión en `/usuarios/login`, copia el `access_token` y pégalo en el botón **Authorize**.

## Despliegue

- **API:** Render, a partir de la carpeta `techgear_api`.
- **Portal web:** Vercel, a partir de la raíz del repositorio (usa `vercel.json` y `requirements.txt`). Requiere la variable de entorno `API_URL`.

## Autor

John David Diaz Correa
