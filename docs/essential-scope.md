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

## Futuras mejoras, fuera de la aplicación inicial

- Cobranza integrada con un proveedor de pagos.
- Emisión de facturas.
- Registro de asistencia mediante QR del socio, visible para el administrador.

La inscripción a una clase es una reserva de plaza, no una prueba de asistencia.
