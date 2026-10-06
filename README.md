# BazarNimal — Backend

API de la tienda de mascotas **BazarNimal**: adopción de perros y gatos, catálogo de la tienda (solo existencia, sin carrito) y publicaciones de Día de Muertos validadas por el admin.

FastAPI + MySQL 8, con Swagger en `/docs`. Sigue `REQUERIMIENTOS_BACKEND_BD.md` (Clean Architecture + vertical slice).

## Puesta en marcha

Todo se ejecuta con el Python del `.venv` del proyecto.

1. Instala dependencias (si el `.venv` no existe: `py -3.12 -m venv .venv`):

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

2. Configura el entorno. El `.env` local ya trae secretos generados; si no existe, copia `.env.example` como `.env` y completa los valores vacíos con:

   ```powershell
   .\.venv\Scripts\python.exe scripts\generate_secrets.py
   ```

   Toda la configuración sensible o que depende del ambiente vive en el `.env`. El backend no arranca si falta un valor obligatorio, si un secreto es débil o si conserva un valor de ejemplo.

3. Crea la base de datos (pide la contraseña de `root` de MySQL y toma las de la app del `.env`):

   ```powershell
   .\scripts\setup_database.ps1
   ```

4. Arranca el servidor ejecutando el main (en VS Code también puedes usar F5 → "BazarNimal: main"). Al iniciar ejecuta las migraciones pendientes y crea el admin inicial (`ADMIN_EMAIL` / `ADMIN_PASSWORD` del `.env`). Si la migración falla, no arranca.

   ```powershell
   .\.venv\Scripts\python.exe src/main.py
   ```

   Host, puerto y recarga automática salen del `.env` (`APP_HOST`, `APP_PORT`, `APP_RELOAD`).

   - Swagger: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - En producción Swagger se deshabilita (salvo `DOCS_ENABLED=true`).

   Para probar rutas protegidas en Swagger, ejecuta primero `POST /api/v1/auth/login`; el navegador guarda las cookies y las manda solo.

## CORS

Configurado en `src/core/security/cors.py` con los orígenes de `CORS_ORIGINS` (separados por coma):

- Credenciales habilitadas (las cookies de sesión viajan con `credentials: "include"` / `withCredentials: true`).
- Métodos `GET, POST, PUT, PATCH, DELETE`; headers `Content-Type` y `X-CSRF-Token`.
- El frontend puede leer `RateLimit-*` y `Retry-After`.
- Nunca se acepta `*`, y en producción solo orígenes `https://`.

Usa el mismo host en frontend y backend (`localhost` con `localhost`): para las cookies `SameSite=Strict`, `localhost` y `127.0.0.1` son sitios distintos.

## Endpoints

| Rol | Método y ruta | Descripción |
|---|---|---|
| Público | `POST /api/v1/auth/register` | Registro (nombre, correo, teléfono, contraseña) |
| Público | `POST /api/v1/auth/login` | Inicia sesión. Devuelve `role` para redirigir a la vista de user o admin |
| Sesión | `POST /api/v1/auth/refresh` · `POST /api/v1/auth/logout` · `GET /api/v1/auth/me` | Rotación de sesión, cierre y datos propios |
| Público | `GET /api/v1/pets` · `GET /api/v1/pets/{id}` | Mascotas (filtros: `species`, `status`, `search`) |
| User | `POST /api/v1/adoption-requests` · `GET /api/v1/adoption-requests/me` | Solicitar adopción y ver mis solicitudes |
| Admin | `/api/v1/admin/pets` (CRUD) | Mascotas en adopción con foto |
| Admin | `GET /api/v1/admin/adoption-requests` · `PATCH …/{id}/approve` · `PATCH …/{id}/reject` | Solicitudes con nombre, correo y teléfono del usuario |
| Público | `GET /api/v1/products` · `GET /api/v1/products/{id}` | Catálogo con existencia |
| Admin | `/api/v1/admin/products` (CRUD) | Artículos: nombre, imagen, peso y piezas opcionales, estatus |
| Público | `GET /api/v1/posts` · `GET /api/v1/posts/{id}` | Solo publicaciones aprobadas |
| User | `POST /api/v1/posts` · `GET /api/v1/posts/me` · `DELETE /api/v1/posts/{id}` | Crear (queda pendiente), ver las mías, borrar una propia |
| Admin | `GET /api/v1/admin/posts` · `PATCH …/{id}/approve` · `PATCH …/{id}/reject` · `DELETE …/{id}` | Validación de publicaciones |
| Público | `GET /health` | Monitoreo |

### Reglas de negocio

- **Sesión:** el access token dura 15 min para `user` y 2 h para `admin`. El refresh token (7 días) se rota en cada uso; si se reutiliza uno ya rotado, se cierran todas las sesiones del usuario.
- **Adopción:** solo usuarios registrados (rol `user`), una solicitud pendiente por mascota y usuario, y no se puede solicitar una mascota adoptada. Al aprobar una solicitud, la mascota pasa a `adopted` y las demás solicitudes pendientes de esa mascota se rechazan, todo en una sola transacción.
- **Publicaciones:** nacen `pending`; solo las `approved` se muestran al público. El admin puede retirar una aprobada (rechazarla) o aprobar una rechazada.
- **Valores de los enums:** especie `dog`/`cat`; mascota `in_adoption`/`adopted`; artículo `available`/`unavailable`; publicación y solicitud `pending`/`approved`/`rejected`.

## Arquitectura

```
src/
├── core/        config, database (migraciones, seeders), di, server, security, errors, logger, storage
├── shared/      contracts (interfaces), middlewares (authenticate, authorize, rate_limit), validators, utils, types
├── routes/      index.py monta todo bajo /api/v1
├── features/
│   ├── auth/                         {domain, data, infrastructure, di, routes}
│   ├── adoptions/{user,admin}/       {domain, data, infrastructure, di, routes}
│   ├── products/{user,admin}/        …
│   └── posts/{user,admin}/           …
├── uploads/images/                   imágenes (fuera de git)
└── main.py
bd/bazarnimal.sql                     base de datos completa en un solo archivo
```

El proyecto **no usa archivos `__init__.py`** (paquetes de espacio de nombres de Python 3). Una prueba (`tests/unit/test_project_rules.py`) falla si aparece alguno.

- Un caso de uso por acción, cada uno con un único `execute`.
- El contenedor de DI (`src/core/di`) escanea `features/**/di/*_module.py` y registra todo automáticamente.
- Los controladores reciben sus casos de uso por constructor.

### Equivalentes en Python de los requerimientos

| Requerimiento | Implementación |
|---|---|
| Validación (Zod/Joi) | Pydantic con `extra="forbid"` (lista blanca de campos) |
| Migraciones (Knex/TypeORM) | Alembic, ejecutado al arrancar, con `upgrade`/`downgrade` |
| Consultas parametrizadas | SQLAlchemy Core (sin SQL concatenado); `ORDER BY` por lista blanca |
| DI (tsyringe/Awilix) | Contenedor propio con autowiring y autoregistro (`singleton`/`scoped`/`transient`) |
| JWT | PyJWT, HS256 fijo (se rechaza `alg: none`), solo en cookies HttpOnly |
| Contraseñas | Argon2id (argon2-cffi), con bloqueo temporal tras 5 intentos |
| Datos personales | AES-256-GCM con versión de llave + HMAC-SHA256 para buscar por correo |
| Rate limit | Middleware propio: 429 + `Retry-After` + `RateLimit-*` (en memoria; Redis si hay varias instancias) |
| Helmet / CORS | Middleware de cabeceras de seguridad propio + `CORSMiddleware` restringido |
| multer + sharp | `UploadFile` + magic bytes + Pillow (recodifica a WEBP, sin EXIF), nombre UUID |
| Logs (pino) | JSON estructurado con campos sensibles ocultos |

## Pruebas

No necesitan MySQL: las e2e levantan la app completa (con migraciones) sobre SQLite temporal.

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Migraciones nuevas

Nunca edites una migración ya ejecutada; crea una nueva:

```powershell
.\.venv\Scripts\python.exe -m alembic revision -m "agrega columna x"
```

El backend la aplica sola al arrancar.

## Producción

- `APP_ENV=production`, HTTPS obligatorio (activa HSTS), `COOKIE_SECURE=true`.
- `PUBLIC_BASE_URL` y `CORS_ORIGINS` deben ser `https://` (el backend lo valida).
- Detrás de un proxy, pon su IP en `FORWARDED_ALLOW_IPS` para obtener la IP real del cliente.
- `APP_RELOAD` debe ser `false`.
- Si MySQL está en otra máquina, `DB_SSL_CA` es obligatorio (TLS).
