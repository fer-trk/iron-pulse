# Alcance de la primera versión presentable

La primera pasada cubre inscripción de socios, asignación de planes, registro
manual de cobros e inscripción de socios a clases. Se corrigen los fallos graves
de esos recorridos y las referencias a funciones inexistentes. La optimización
general y el rediseño quedan para otra pasada.

## Cobros y planes

Los precios se almacenan con dos decimales exactos. La migración convierte los
precios anteriores redondeándolos a céntimos. La API devuelve importes como cadenas
decimales; la interfaz los convierte solo para mostrarlos.

Las membresías nuevas empiezan pendientes y se activan cuando los cobros
completados cubren el precio del plan. Pagos parciales, cambios a completado,
devoluciones y borrados recalculan el saldo. Las membresías canceladas o expiradas
no se reactivan por registrar otro movimiento. Un plan gratuito se activa al
asignarlo. Registrar un cobro no conecta con un proveedor ni mueve dinero.

Un importe omitido o null usa el precio del plan. Importes no positivos, con más
de dos decimales o fuera de rango se rechazan. Los socios inactivos no reciben
nuevas membresías. Los formularios usan planes y precios reales de la API.

## Inscripción a clases

Un empleado selecciona el socio explícitamente: su ID de usuario nunca se usa
como ID del socio. Se exige membresía pagada y válida para la fecha de clase,
socio y clase activos, día semanal correcto y aforo disponible. Cancelar libera
la plaza y reinscribirse reutiliza el registro, evitando errores de unicidad.
Las clases con historial se desactivan en lugar de borrarse.

La inscripción no registra presencia. Se retiran las rutas, servicios y pantallas
de asistencias; los datos históricos se mantienen únicamente en la base y las
migraciones existentes. Las mejoras futuras están enumeradas en el README.
