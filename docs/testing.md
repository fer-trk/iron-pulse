# Cómo se prueban los cambios de Iron Pulse

El trabajo se integra mediante PR en `developer`. `main` se reserva para la
entrega final. Actions ejecuta las comprobaciones; la revisión de la PR permite
entender qué cambió y qué demuestran sus resultados.

## Ejecutar la suite

Con Python 3.11, desde la raíz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Si `.venv` ya existe, no hace falta crearlo de nuevo. En Linux o macOS, el
intérprete está en `.venv/bin/python`. No se necesita PostgreSQL para esta suite.
`requirements-dev.txt` incluye las dependencias de la aplicación, pytest y httpx.
`pytest.ini` selecciona `app/tests`; las migraciones se ejecutan por separado.

Para investigar un caso concreto:

```powershell
.\.venv\Scripts\python.exe -m pytest app/tests/test_payment.py -v
```

Una prueba sigue tres pasos: preparar datos, ejecutar una operación y comprobar
el resultado. Por ejemplo, un pago vinculado a una membresía cancelada debe
devolver HTTP 400. La prueba prepara esa membresía, envía el pago y comprueba
el código y el mensaje de error.

## Qué comprueba cada grupo

| Archivos | Comprobaciones |
| --- | --- |
| `test_member.py`, `test_member_service.py` | Altas, correo duplicado, consultas, actualización, baja y reactivación mediante `is_active`, borrado y errores de socio inexistente. |
| `test_plan.py` | Creación, nombre duplicado, precios y duración inválidos, consultas, filtro de planes activos, actualización y protección del borrado de planes con membresías. |
| `test_membership.py` | Creación, rechazo de socios suspendidos, renovación y vencimientos próximos. |
| `test_payment.py` | Asociación a membresía, membresía inexistente o cancelada, consulta, paginación, filtro por membresía y actualización del estado del pago. |
| `test_shift.py`, `test_reservation.py` | Operaciones de clases, capacidad, disponibilidad, creación de reservas y error de clase inexistente. |
| `test_attendance.py`, `test_attendance_service.py` | Registro, pertenencia de la reserva, cancelaciones, duplicados, consultas y salida. |
| `test_report.py`, `test_report_service.py` | Resúmenes, agrupaciones por socio o reserva, ausencia de datos y rangos de fechas inválidos. |
| `test_auth.py`, `test_security_config.py` | Login real, permisos de creación de cuentas, usuarios activos, validación de tokens, hashes anteriores, comando inicial y claves de producción. |
| `test_api_auth.py` | Rechazo de peticiones anónimas a todas las operaciones de negocio publicadas en OpenAPI y rechazo de un token inválido. |

Las pruebas unitarias de servicios usan `MagicMock`: sustituyen el acceso a datos
para aislar la lógica. Las de endpoints usan `TestClient`, la aplicación FastAPI
y una base SQLite nueva en memoria para cada prueba. SQLite tiene las claves
foráneas activadas: una referencia a un registro inexistente debe fallar también
en pruebas. Los contextos y sustituciones se limpian al terminar cada caso.

Las pruebas de negocio solicitan explícitamente `auth_headers`, que sustituye
la dependencia de autenticación por un identificador de prueba. Esto permite
investigar negocio sin mezclar fallos de login. Los casos de `test_api_auth.py` y `test_auth.py`
no usan esa sustitución. No hay una desactivación global de la seguridad.

## Qué se reparó y por qué

La suite original no podía ejecutarse por un archivo de pagos truncado y dos
importaciones inexistentes. Tras corregir solo esos bloqueos, se obtuvo una
línea de base de 24 pruebas aprobadas y 73 fallidas.

Se actualizaron los nombres de servicios, sus resultados Pydantic y las
excepciones HTTP esperadas. `test_plan.py` era una copia de las pruebas de socios;
ahora prueba planes. La API actual usa `PATCH /members/{id}` con `is_active`,
no las antiguas rutas `/suspend` y `/reactivate`. Este cambio en las pruebas
verifica la activación y desactivación disponibles; no demuestra que exista
una operación de suspensión mediante el campo `status`.

Un pago referencia una membresía y utiliza `payment_method`; no recibe un
`member_id` independiente ni el campo `method`. Por eso se sustituyó el caso
de socio inexistente por el rechazo de una membresía cancelada y se corrigió
el filtro a `membership_id`. Para evitar falsos positivos, la prueba del filtro
crea también un pago de otra membresía, y la paginación comprueba los registros
devueltos además de su cantidad.

Esta reparación modifica las pruebas y su infraestructura, sin cambiar el
comportamiento del backend. Conserva el historial Git de las contribuciones
originales; el historial de commits y las PR registran las modificaciones.

## Actions y límites de la validación

`Backend tests` instala `requirements-dev.txt`, ejecuta pytest y guarda el
informe JUnit como artefacto descargable. El host de base de datos de la aplicación
se configura como inaccesible: los tests deben utilizar su conexión temporal.

`Database migrations` utiliza PostgreSQL 15 desechable. Valida SQL offline,
credenciales codificadas, precedencia de `DATABASE_URL` frente a `DB_*` y creación
del esquema ejecutando la migración dos veces. Su comando independiente es:

```bash
python -m unittest discover -s tests/migrations -v
```

Ese comando requiere una base PostgreSQL vacía y desechable. No debe apuntarse
a datos de trabajo. Ambas validaciones se ejecutan en PR y en pushes a
`developer` y `main`; ninguna aplica cambios a una base desplegada.

Una suite aprobada confirma los casos descritos, no garantiza que el producto
esté terminado. Quedan para mejoras posteriores:

- Revocación persistente y compartida entre procesos, recuperación de contraseñas
  y permisos más detallados. El login real, el registro reservado al administrador
  y la protección de todos los módulos de negocio ya están cubiertos.
- Relación explícita entre usuario autenticado y socio en las reservas; los
  casos actuales usan deliberadamente un socio cuyo ID coincide con el stub.
- Coherencia entre `Member.status`, `is_active` y vigencia de la membresía.
- Activación financiera de membresías, devoluciones, importes y concurrencia.
- Más escenarios de reservas, informes de ingresos y exportación CSV.
- Pruebas de negocio sobre PostgreSQL y pruebas de navegador. SQLite no
  reproduce todos los tipos, restricciones o bloqueos de PostgreSQL.

La mejora de autenticación migró la configuración a `SettingsConfigDict` y eliminó
la advertencia de Pydantic. La [guía de autenticación](authentication.md) detalla
los controles y los límites actuales.


## Prueba del despliegue Docker

El workflow `Docker deployment` construye y levanta los tres servicios usando
cada uno de los archivos Compose. Ejecuta el script de comprobación HTTP contra
PostgreSQL real y verifica persistencia al recrear la base y reiniciar la API.
Esta prueba complementa la suite SQLite y la prueba de migraciones; consulta la
[guía de Docker](docker.md) para su alcance y los requisitos de aislamiento.
