# Pruebas de la versión esencial

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
node --test tests/frontend-catalog.test.cjs
```

La suite de negocio usa una base SQLite nueva por prueba, con claves foráneas
activadas. Los casos de negocio sustituyen explícitamente la autenticación;
`test_auth.py` y `test_api_auth.py` validan login, tokens, usuarios y permisos
reales sin ese reemplazo. No se desactiva globalmente la seguridad.

## Recorridos comprobados

- Socios: alta, correo duplicado, actualización, desactivación y protección del historial.
- Planes: precio decimal, duración, catálogo real y bloqueo del borrado con membresías.
- Cobros: activación exacta a 49,99, pagos parciales, cambio a completado, devolución,
  borrado, importe null y rechazo de importes inválidos o socios inactivos.
- Clases: alta, consulta, edición, disponibilidad y validaciones básicas.
- Inscripciones: socio seleccionado distinto del empleado, membresía pagada y
  vigente, fechas válidas, aforo, duplicados, cancelación y reinscripción.
- Ingresos: resumen financiero y rechazo de intervalos inválidos.
- Alcance: las rutas de asistencias retiradas responden 404.

Las pruebas JavaScript usan Node sin dependencias de frontend: verifican que los
formularios usen el catálogo real, que los nombres con apóstrofos no rompan la
edición ni se interpreten como HTML y que el login no recorte la contraseña.
No sustituyen una prueba visual de navegador.

## GitHub Actions

Cada PR y push a `developer` o `main` ejecuta:

1. Suite Python y pruebas JavaScript, con informe JUnit descargable.
2. Migraciones sobre PostgreSQL 15 con variables DB_* y DATABASE_URL. Se inserta
   un precio heredado 49,99 antes de aplicar la nueva migración, comprobando que
   se conserva como Decimal y que repetir upgrade head no produce errores.
3. Ambos Compose: construcción, healthchecks, frontend y API, login, socio, plan,
   membresía, cobro completo, inscripción, cancelación y reinscripción. Recrea
   PostgreSQL conservando su volumen y reinicia la API para comprobar persistencia.

El script Docker exige un proyecto iron-pulse-check-* y usa credenciales y datos
ficticios. No modifica una instalación de trabajo ni publica imágenes.

## Límites

No se pretende cubrir todos los escenarios posibles ni optimizar grandes
volúmenes en esta pasada. Quedan pendientes la revocación persistente del logout,
pruebas exhaustivas de concurrencia y una automatización completa de navegador.
Las pruebas de las antiguas asistencias se retiraron junto con esa funcionalidad;
no se contabilizan como cobertura de la versión esencial.
