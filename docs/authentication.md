# Autenticación y creación de cuentas

Esta mejora protege la API de gestión interna de Iron Pulse. Se integra mediante
PR en `developer`; `main` se reserva para la entrega final.

## El problema anterior

El token firmado solo se convertía en un identificador. No se comprobaba que la
cuenta siguiera existiendo o activa. Además, los informes, el CSV de asistencias,
el detalle de una asistencia y el registro de salida podían invocarse sin login.
El registro público aceptaba `is_admin=true`, aunque todavía no se comprobaba
ese permiso para crear cuentas.

## Qué comprueba ahora una petición

1. La cabecera debe incluir `Authorization: Bearer <token>`.
2. Se verifica la firma con el algoritmo configurado y se exige caducidad y
   sujeto. El token debe ser de tipo `access`; un refresh token no sirve.
3. El sujeto debe ser un identificador positivo válido y corresponder a un
   usuario existente en PostgreSQL.
4. La cuenta debe estar activa.
5. Para crear cuentas, también debe tener `is_admin=true` en la base de datos.

Los ocho módulos de negocio se agrupan en un router protegido en `main.py`.
Esto cubre todos sus métodos y también las nuevas operaciones que se añadan a
esos routers. El login y la comprobación básica de salud permanecen públicos.
La documentación OpenAPI también sigue visible; no contiene datos de socios.

El estado y el permiso se consultan en cada petición. Por tanto, eliminar o
inactivar una cuenta invalida su acceso con tokens anteriores; retirar el rol
administrador impide crear cuentas sin esperar a la caducidad del token.

| Operación | Acceso |
| --- | --- |
| `POST /api/v1/auth/token` | Público; exige credenciales válidas de una cuenta activa. |
| Endpoints de socios, planes, membresías, pagos, clases, reservas, asistencias e informes | Cualquier cuenta del personal activa y autenticada. |
| `POST /api/v1/auth/register` | Administrador activo y autenticado. Puede crear personal u otros administradores. |
| `POST /api/v1/auth/logout` | Cuenta activa con token de acceso válido. |
| `GET /` y documentación de API | Público. |

Esta política es para personal del gimnasio. Todavía no hay un portal de socios
ni permisos por propietario de cada reserva. `User` y `Member` son entidades
distintas y su relación se resolverá en otra mejora.

Una autenticación inválida responde `401` con `WWW-Authenticate: Bearer`.
Una cuenta autenticada sin permiso de administrador recibe `403` al intentar
crear otra cuenta. Un nombre de usuario duplicado responde `409`; un payload
inválido responde `422`.

## Contraseñas y compatibilidad

Se utiliza `bcrypt==5.0.0` directamente y se retira la dependencia de Passlib.
El algoritmo de los hashes existentes se conserva: BCrypt. Las pruebas verifican
hashes públicos compatibles de los formatos `$2a$` y `$2b$` de la documentación
original de Passlib. No se obliga a reescribir hashes en la base de datos.

Las cuentas nuevas requieren un nombre no vacío de hasta 100 caracteres y una
contraseña de al menos 12 caracteres y como máximo 72 bytes UTF-8. No se recortan
contraseñas; por ejemplo, algunos caracteres Unicode ocupan más de un byte.
El login sigue admitiendo contraseñas antiguas cortas con hashes válidos. Las
contraseñas de más de 72 bytes se rechazan; si una instalación antigua dependía
del truncado de BCrypt, esas credenciales requieren revisión y restablecimiento.

El esquema usa `SecretStr` para representar contraseñas y la respuesta de creación
solo contiene `id`, `username`, `is_admin` e `is_active`. Nunca devuelve el hash.
Los parámetros SQL se ocultan en los logs del motor incluso con DEBUG activado.

## Preparar la primera cuenta administradora

El registro HTTP no tiene una excepción pública para el primer administrador.
La persona que instala la aplicación ejecuta el comando una vez, desde una
terminal de confianza, con acceso a la base configurada y migraciones aplicadas:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.scripts.create_admin
```

En un contenedor API ya configurado, se usa su intérprete `python` en lugar del
del entorno virtual. El comando pide el nombre y la contraseña dos veces; las
contraseñas se introducen sin eco y no se pasan como argumentos del proceso.

Si ya existe un administrador, el comando se detiene. Si el nombre pertenece a
una cuenta del personal, no la sobrescribe ni la convierte en administradora.
Las siguientes cuentas se crean desde el endpoint autenticado de registro.
No se crean usuarios predeterminados ni credenciales públicas.

No ejecutes varias instancias del comando de preparación simultáneamente; es
una operación de instalación controlada, no un servicio público de registro.

## Configurar la clave de firma

Con `DEBUG=True` se permite la clave de desarrollo de `.env.example`. Para usar
`DEBUG=False`, debe configurarse una clave privada de al menos 32 caracteres,
diferente de las claves de desarrollo o de ejemplo. Puede generarse en la
terminal del operador con:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Guárdala en la configuración privada del entorno; no en Git. La aplicación no
arranca con una clave inválida en modo producción. Las duraciones de tokens
deben ser positivas. Los workflows usan claves públicas solo de prueba en
bases desechables, nunca claves de un despliegue.

## Cambios que verá quien usa la API

- Las rutas antes públicas ahora requieren login.
- El registro devuelve `201` y los campos públicos de la cuenta creada.
- Solo un administrador puede registrar cuentas. `is_admin` es una decisión
  autorizada de ese administrador, no un privilegio elegido por un visitante.
- Los tokens anteriores sin el nuevo campo `type=access` dejan de aceptarse:
  después de actualizar hay que iniciar sesión de nuevo.
- Cada token nuevo incluye un `jti` aleatorio. Dos logins del mismo usuario no
  generan el mismo token aunque ocurran durante el mismo segundo.

## Qué se prueba y qué queda pendiente

La suite valida login y acceso real, contraseñas incorrectas, cuentas inactivas,
tokens caducados o manipulados, claims ausentes, refresh tokens, sujetos inválidos,
usuarios eliminados, registro con y sin permisos, duplicados y validación de
credenciales. Recorre todas las operaciones de negocio del OpenAPI para verificar
que una petición anónima se rechaza. Además comprueba que el personal pueda
consultar informes y exportar CSV con un token real, y prueba el comando inicial
sin crear cuentas en una base de trabajo.

La configuración de Pydantic se actualizó a `SettingsConfigDict`; las pruebas
cubren el rechazo de claves inadecuadas en producción.

Esta PR no completa la gestión de sesiones: el logout todavía revoca tokens en
memoria del proceso. La revocación compartida entre procesos y persistente tras
reinicios tendrá su propia migración y PR. Tampoco incluye recuperación de
contraseñas, límites de intentos de login, permisos detallados por operación,
portal de socios ni la unificación del login del frontend. HTTPS y la
configuración de despliegue siguen pendientes de su revisión correspondiente.

Referencias técnicas: [FastAPI y JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/),
[autorización de OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
y [formatos BCrypt de Passlib](https://passlib.readthedocs.io/en/stable/lib/passlib.hash.bcrypt.html).
