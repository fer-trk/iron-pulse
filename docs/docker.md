# Ejecutar Iron Pulse con Docker

Esta configuración permite levantar el frontend, la API y PostgreSQL desde una
misma copia del proyecto. La versión en desarrollo se integra en `developer`.
No requiere instalar Python en el equipo anfitrión ni copiar rutas de Portainer.

## Requisitos y arranque local

Instala Docker Engine o Docker Desktop con el motor de contenedores Linux activo
y Docker Compose v2 reciente, con soporte para `up --wait`. En Windows, abre
Docker Desktop y espera a que el motor esté disponible antes de ejecutar:

```powershell
docker compose up -d --build --wait --wait-timeout 180
```

La primera construcción descarga las imágenes y dependencias y puede tardar
varios minutos. No necesitas crear `.env` para una demostración local.

- Aplicación: [http://localhost:8080](http://localhost:8080).
- API interactiva: [http://localhost:8080/api/docs](http://localhost:8080/api/docs).
- Estado de la API: [http://localhost:8080/api/health](http://localhost:8080/api/health).

La base empieza vacía. Para preparar el primer administrador:

```powershell
docker compose exec api python -m app.scripts.create_admin
```

El comando pide usuario y contraseña de manera interactiva. Después inicia
sesión en la página de login. No hay contraseñas de administrador predefinidas.
Los detalles están en la [guía de autenticación](authentication.md).

Si el puerto 8080 está ocupado, en PowerShell puede cambiarse para esa terminal:

```powershell
$env:HTTP_PORT="8081"
docker compose up -d --build --wait --wait-timeout 180
```

En ese caso, abre `http://localhost:8081`. La API usa la ruta relativa `/api/v1`
del mismo servidor, así que no necesita editar direcciones en el JavaScript.

## Qué hace cada servicio

| Servicio | Responsabilidad | Acceso desde el equipo |
| --- | --- | --- |
| `db` | PostgreSQL 15 y volumen persistente de datos. | Sin puerto publicado. |
| `api` | Aplica Alembic y después arranca FastAPI como usuario sin privilegios. | Sin puerto publicado; Nginx la alcanza por la red de Compose. |
| `nginx` | Sirve HTML, CSS, JavaScript e imágenes y reenvía `/api/` a FastAPI. | `127.0.0.1:8080` por defecto. |

Compose espera a que PostgreSQL esté disponible antes de arrancar la API y a que
la API responda antes de iniciar Nginx. El proceso de la API ejecuta las
migraciones antes de atender peticiones. Los healthchecks indican si cada
servicio responde; no sustituyen a las pruebas funcionales.

El frontend se copia en su propia imagen y no depende de un directorio del
servidor. Las rutas de archivos inexistentes devuelven 404 en lugar de responder
con el login, para detectar recursos rotos. `/healthz` comprueba Nginx y
`/api/health` comprueba el proceso de FastAPI.

## Reinicios, cambios y datos

```powershell
docker compose ps
docker compose logs --tail 100 api nginx
docker compose restart api
docker compose down
```

`down` elimina los contenedores y la red, pero conserva el volumen de PostgreSQL.
Al volver a levantar los servicios, los datos siguen disponibles. Si cambia el
código, vuelve a ejecutar el comando de construcción: esta configuración no
monta el repositorio ni activa recarga automática dentro del contenedor.

`down --volumes` elimina también los datos. Se utiliza exclusivamente para
instalaciones de prueba desechables; no forma parte del apagado normal ni debe
usarse para actualizar una instalación que quieras conservar.

El archivo local utiliza el nombre de proyecto `iron-pulse-local`; el archivo de
despliegue utiliza `iron-pulse-demo`. Así tienen redes y volúmenes independientes.
Se puede elegir otro nombre con `-p` o `COMPOSE_PROJECT_NAME`. Los datos de una
instalación no aparecen automáticamente en la otra.

Si cambias DB_PASSWORD después de inicializar un volumen, PostgreSQL conserva la
contraseña anterior. Cambiar una variable no cambia la contraseña guardada en
la base: requiere una operación de administración de PostgreSQL. No borres el
volumen para resolverlo si contiene datos que quieras conservar.

## Configuración para un servidor o demo alojada

`docker-compose.prod.yml` es independiente: se utiliza solo, no como un overlay
del archivo local. Copia la plantilla:

```powershell
Copy-Item .env.production.example .env.production
```

Completa `SECRET_KEY` y `DB_PASSWORD` con valores privados e independientes. Para
generar cada valor puedes ejecutar en una terminal con Python:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

La plantilla deja esos campos vacíos deliberadamente. Compose rechaza una
configuración incompleta y la API rechaza claves de firma de desarrollo en
producción. Las credenciales de PostgreSQL se codifican al construir la URL,
por lo que caracteres como `@`, `:` o `%` no rompen la conexión.

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build --wait --wait-timeout 180
docker compose --env-file .env.production -f docker-compose.prod.yml exec api python -m app.scripts.create_admin
```

El archivo de producción fuerza `DEBUG=False`. También publica solo el puerto de
Nginx en loopback por defecto. Para una URL de entrevista desde otro equipo se
necesita un alojamiento y un proxy de entrada con HTTPS que reenvíe a ese puerto;
los certificados y el dominio dependen del servicio elegido y no se provisionan
en esta PR. `HOST_IP` permite adaptar el enlace de red cuando el alojamiento lo
requiera. No publiques directamente el puerto de PostgreSQL ni el de la API.

Se utiliza un único proceso de API mientras la revocación de sesiones siga en
memoria. La [guía de autenticación](authentication.md) explica esa limitación.
Esta configuración tampoco aporta copias de seguridad ni un catálogo de datos
de demostración; ambos requieren su preparación antes de una demo pública.

## Imágenes, secretos y privacidad

`.dockerignore` permite únicamente los archivos necesarios para construir las
imágenes. Git, `.venv`, los archivos `.env`, los informes y las pruebas quedan
fuera de las imágenes. Los Dockerfiles copian explícitamente los archivos que
necesita cada servicio. `.env.production` está excluido de Git.

Esto evita incluir archivos privados por accidente, pero Docker no impide
clonar un repositorio público. La visibilidad de GitHub se decidirá al finalizar
la puesta a punto del proyecto. No se publican imágenes en ningún registro en
este workflow; una imagen de la API también contiene código y debe mantenerse
privada si el objetivo es protegerlo. El navegador siempre puede inspeccionar
el HTML, CSS y JavaScript que recibe.

## Cómo se verifica en Actions

El workflow `Docker deployment` prueba los dos archivos Compose en instalaciones
vacías e independientes. Construye imágenes, espera a los servicios y ejecuta:

```bash
python scripts/check_docker_deployment.py
```

El script exige un proyecto cuyo nombre empiece por `iron-pulse-check-` para no
crear datos de prueba en una instalación de trabajo. Comprueba:

- Página de login, CSS, JavaScript, logo, Swagger y estado de API a través de Nginx.
- 404 para archivos ausentes o privados y rechazo de acceso anónimo a socios.
- Preparación del administrador, login real y creación de socio, plan, membresía
  y pago contra PostgreSQL, seguido de inscripción a clase, cancelación y reinscripción.
- Informes con un token válido, usuario de API sin privilegios y exclusión de
  archivos privados en la imagen.
- Persistencia al recrear el contenedor de PostgreSQL sin borrar su volumen y
  recuperación de la API tras reiniciarla y aplicar otra vez las migraciones.

Al terminar, Actions elimina únicamente su instalación temporal y su volumen.
Las imágenes no se publican y ninguna prueba modifica un servidor desplegado.
