# Despliegue de BazarNimal (plan gratis)

```
Navegador ──> Vercel (frontend)
                 │  /api/*  (rewrite: el navegador ve un solo sitio)
                 ▼
              Render (backend FastAPI) ──> Aiven (MySQL 8, TLS)
                 │
                 └──> Cloudflare R2 (imágenes)
```

| Parte | Servicio | Por qué |
|---|---|---|
| Frontend | Vercel | Gratis |
| Backend | Render (plan free) | Corre FastAPI tal cual. Se duerme tras 15 min sin uso |
| Base de datos | Aiven for MySQL (free) | MySQL 8 real, 1 GB, sin tarjeta |
| Imágenes | Cloudflare R2 | El disco de Render es temporal: las imágenes se perderían en cada reinicio |

Orden recomendado: **1 → 2 → 3 → 4 → 5**. Los límites de los planes gratis cambian; revísalos al crear cada cuenta.

---

## 1. Secretos de producción

Producción usa **secretos distintos** a los de tu `.env` local. Crea en la carpeta `Backend` un archivo `.env.production` (está en `.gitignore`, nunca se sube) y genera los valores:

```powershell
.\.venv\Scripts\python.exe scripts\generate_secrets.py
```

Copia al `.env.production` estas líneas de la salida:

```
DB_PASSWORD=...
DB_MIGRATION_PASSWORD=...
ENCRYPTION_KEYS=...
HMAC_KEY=...
ADMIN_PASSWORD=...
```

**Respalda `ENCRYPTION_KEYS` y `HMAC_KEY`** (por ejemplo, en un gestor de contraseñas). Si se pierden, los correos y teléfonos guardados ya no se pueden leer y nadie podrá iniciar sesión.

## 2. Base de datos en Aiven

1. Crea una cuenta en https://aiven.io y un servicio **MySQL** con el plan **Free**. Elige una región cercana a la de Render (por ejemplo, Estados Unidos).
2. En la página del servicio, sección **Connection information**, anota **Host**, **Port**, **User** (`avnadmin`) y **Password**, y descarga el **CA certificate** como `ca.pem` en la carpeta `Backend` (los `.pem` están en `.gitignore`).
3. Crea la base, los usuarios y las tablas (pide la contraseña de `avnadmin`):

   ```powershell
   .\scripts\setup_database.ps1 -Remote -EnvFile .env.production `
       -MysqlHost <host>.aivencloud.com -MysqlPort <puerto> -MysqlUser avnadmin -SslCa .\ca.pem
   ```

   Con `-Remote` los usuarios `bazarnimal_app` y `bazarnimal_migrator` se crean para conexiones remotas, y la conexión va cifrada con TLS verificando el certificado.

## 3. Imágenes en Cloudflare R2

1. En https://dash.cloudflare.com → **R2**, crea un bucket, por ejemplo `bazarnimal-images` (Cloudflare puede pedir una tarjeta para activar R2, aunque el uso quede dentro del límite gratis).
2. En el bucket → **Settings** → **Public access**, activa la **Public Development URL** (`https://pub-xxxx.r2.dev`) o conecta un dominio propio.
3. En **R2** → **Manage API tokens**, crea un token con permiso **Object Read & Write** solo para ese bucket. Anota **Access Key ID** y **Secret Access Key**.
4. El endpoint es `https://<ACCOUNT_ID>.r2.cloudflarestorage.com` (el Account ID aparece en la página de R2).

## 4. Backend en Render

1. Sube el repositorio del backend a GitHub (el `render.yaml` está en la raíz).
2. En https://render.com → **New** → **Blueprint**, elige el repositorio. Render lee `render.yaml` y pide los valores marcados como secretos:

   | Variable | Valor |
   |---|---|
   | `PUBLIC_BASE_URL` | URL que Render le da al servicio, p. ej. `https://bazarnimal-api.onrender.com` |
   | `CORS_ORIGINS` | URL del frontend en Vercel, p. ej. `https://bazarnimal.vercel.app` |
   | `DB_HOST`, `DB_PORT` | Los de Aiven |
   | `DB_PASSWORD`, `DB_MIGRATION_PASSWORD` | Los de `.env.production` |
   | `ENCRYPTION_KEYS`, `HMAC_KEY` | Los de `.env.production` |
   | `S3_ENDPOINT_URL`, `S3_BUCKET`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_PUBLIC_BASE_URL` | Los de R2 |
   | `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Credenciales del administrador inicial |

   `JWT_SECRET` lo genera Render solo.
3. En el servicio → **Environment** → **Secret Files**, agrega un archivo llamado **`aiven-ca.pem`** con el contenido de `ca.pem` (queda en `/etc/secrets/aiven-ca.pem`, que es lo que espera `DB_SSL_CA`).
4. Despliega. En **Logs** deben aparecer `migrations_finished` y `server_started`, y `https://<tu-servicio>.onrender.com/health` debe responder:

   ```json
   {"status": "ok", "database": "ok"}
   ```

Si el backend no arranca, el log dice qué variable falta o es inválida (en producción se exige `https://`, TLS hacia MySQL y almacenamiento de imágenes completo).

Swagger está apagado en producción. Para una demo, cambia `DOCS_ENABLED` a `true` en Render.

## 5. Frontend en Vercel (conexión con el backend)

El frontend (`*.vercel.app`) y el backend (`*.onrender.com`) son sitios distintos, y el navegador no enviaría las cookies de sesión (`SameSite=Strict`). La solución es que Vercel reenvíe `/api/*` al backend: para el navegador todo es el mismo sitio.

En la raíz del proyecto del **frontend**, crea `vercel.json`:

```json
{
  "rewrites": [
    { "source": "/api/:path*", "destination": "https://bazarnimal-api.onrender.com/api/:path*" },
    { "source": "/((?!api/).*)", "destination": "/index.html" }
  ]
}
```

(La segunda regla es para aplicaciones de una sola página como React/Vite; quítala si tu framework no la necesita.)

En el frontend, llama a la API con rutas relativas: `fetch("/api/v1/pets")`. En desarrollo local configura el mismo reenvío en el servidor de desarrollo (en Vite, `server.proxy` de `/api` a `http://localhost:8000`).

## 6. Mantenerlo despierto (opcional)

- Render (plan gratis) se duerme tras 15 min sin uso; la primera petición después tarda cerca de 1 minuto.
- Aiven puede apagar el servicio gratis tras un periodo sin uso.

Un monitor gratuito como https://uptimerobot.com que llame a `https://<tu-servicio>.onrender.com/health` cada 5 minutos mantiene despiertos ambos, porque `/health` también consulta la base de datos. Las 750 horas gratis de Render alcanzan para un servicio encendido todo el mes.

## Notas

- **Rate limit:** los contadores viven en memoria; con una sola instancia (plan gratis) funciona bien. Con varias instancias habría que pasarlos a Redis.
- **IP del cliente:** `FORWARDED_ALLOW_IPS="*"` hace que el backend confíe en el encabezado `X-Forwarded-For` que pone el proxy de Render. Es necesario para que el rate limit vea la IP real de cada usuario.
- **Migraciones nuevas:** se aplican solas en cada despliegue, al arrancar el backend.
- **Desarrollo local:** no cambia nada. Con `STORAGE_DRIVER=local` las imágenes se guardan en `src/uploads/images`.
