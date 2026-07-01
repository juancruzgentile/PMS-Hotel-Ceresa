# CERESA MVP local

Guia practica para levantar, poblar y probar el MVP de CERESA en un entorno local de desarrollo.

CERESA no esta listo para produccion. No uses esta instalacion para datos reales de huespedes, pagos, documentos personales o informacion confidencial.

## Stack actual

- Backend: FastAPI + SQLite directo.
- Frontend: Vite + React + TypeScript.
- Tests: pytest.
- Base local de la app: `data/ceresa.db`.
- Base de tests: `data/ceresa_test.db`.

`actor_user_id` es trazabilidad manual para audit events. No es autenticacion, sesion, permiso ni identidad segura.

## Requisitos locales

- Python disponible en PowerShell.
- Node.js y npm disponibles.
- Entorno virtual del proyecto en `.venv`.
- Dependencias de frontend instaladas en `frontend/node_modules`.

Instalar dependencias backend desde la raiz del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Instalar dependencias frontend:

```powershell
cd frontend
npm.cmd install
cd ..
```

## Verificar backend

Ejecutar siempre pytest desde la raiz del proyecto y con el `.venv` local:

```powershell
$env:PYTHONPATH="src"; .\.venv\Scripts\pytest.exe
```

No uses `pytest` global para validar CERESA.

## Poblar datos demo

El seed local crea o reutiliza datos con prefijo `CERESA-DEMO`. Es idempotente y esta pensado para pruebas manuales del MVP.

Desde la raiz del proyecto:

```powershell
$env:PYTHONPATH="src"; .\.venv\Scripts\python.exe -m ceresa.dev.seed_demo
```

El comando imprime IDs utiles para pruebas manuales, incluyendo:

- `reservation_id` para el flujo Reception MVP.
- `billing_account_id` para Billing.
- `reservation_id` para Audit.

Datos demo principales:

- Huespedes: `CERESA-DEMO-GUEST-001`, `CERESA-DEMO-GUEST-002`.
- Habitaciones: `CERESA-DEMO-D101`, `CERESA-DEMO-D102`, `CERESA-DEMO-D201`, `CERESA-DEMO-D202`.
- Reservas: `CERESA-DEMO-RES-001`, `CERESA-DEMO-RES-002`.
- `CERESA-DEMO-D201` queda como habitacion sucia para Housekeeping.
- `CERESA-DEMO-D202` queda como habitacion con reparacion pendiente para Maintenance.
- `CERESA-DEMO-RES-001` queda como flujo cerrado con audit de check-in/check-out.
- `CERESA-DEMO-RES-002` queda como reserva con balance abierto para pruebas de Reception/Billing.

## Levantar el MVP

Opcion rapida en Windows:

```powershell
.\dev.cmd
```

Ese script abre dos terminales:

- API FastAPI: `http://127.0.0.1:8000`.
- Frontend Vite: normalmente `http://localhost:5173`.

Opcion manual, terminal 1:

```powershell
$env:PYTHONPATH="src"; .\.venv\Scripts\python.exe -m uvicorn ceresa.main:app --reload --app-dir src --host 127.0.0.1 --port 8000
```

Opcion manual, terminal 2:

```powershell
cd frontend
npm.cmd run dev
```

URLs utiles:

- Frontend: `http://localhost:5173`.
- API docs: `http://127.0.0.1:8000/docs`.
- Health check: `http://127.0.0.1:8000/`.
- Modulos cargados: `http://127.0.0.1:8000/system/modules`.

El frontend usa `/api` y Vite lo proxya al backend local en `http://localhost:8000`.

## Flujo manual MVP recomendado

1. Ejecuta el seed demo.
2. Levanta backend y frontend.
3. Abre el frontend.
4. Revisa System para confirmar modulos activos/cargados.
5. Revisa Rooms, Guests y Reservations para ver datos base.
6. En Billing, usa el `billing_account_id` impreso por el seed para revisar cargos, pagos y saldo.
7. En Reception MVP, usa el `reservation_id` de `CERESA-DEMO-RES-002`.
8. Si el balance esta abierto, registra el pago necesario desde Billing antes del check-out.
9. Completa check-in y check-out desde Reception.
10. Revisa Audit para confirmar los eventos registrados.
11. Revisa Housekeeping para habitaciones sucias.
12. Revisa Maintenance para habitaciones con reparacion pendiente.

## Endpoints utiles para pruebas manuales

Estos endpoints tambien se pueden probar desde `http://127.0.0.1:8000/docs`.

System:

- `GET /`
- `GET /system/health`
- `GET /system/modules`
- `GET /system/hotel`

Datos operativos:

- `GET /rooms`
- `GET /guests`
- `GET /reservations`
- `GET /billing/accounts`
- `GET /audit/events`
- `GET /housekeeping/dirty-rooms`
- `GET /maintenance/repair-rooms`

Reception:

- `GET /reception/status`
- `GET /reception/arrivals`
- `GET /reception/departures`
- `GET /reception/reservations/{reservation_id}/summary`
- `GET /reception/reservations/{reservation_id}/events`
- `POST /reception/reservations/{reservation_id}/check-in`
- `POST /reception/reservations/{reservation_id}/check-out`

Reservations operativas:

- `PATCH /reservations/{reservation_id}/cancel`
- `PATCH /reservations/{reservation_id}/dates`
- `PATCH /reservations/{reservation_id}/room`

## Audit y actor_user_id

Algunas operaciones aceptan `actor_user_id` opcional. Usalo solo para trazabilidad manual en audit events.

Ejemplo conceptual:

```json
{
  "actor_user_id": 1
}
```

No hay login real en esta fase. No hay sesiones, roles ni permisos reales asociados a ese valor.

## Detener servidores

Si usaste `dev.cmd`, cierra las dos ventanas de terminal abiertas por el script.

Si levantaste los servidores manualmente, usa `Ctrl+C` en cada terminal.

## Problemas frecuentes

Si el backend no encuentra modulos internos:

```powershell
$env:PYTHONPATH="src"
```

Si PowerShell bloquea scripts de npm, usa `npm.cmd`:

```powershell
npm.cmd run dev
npm.cmd run build
```

Si Vite usa otro puerto porque `5173` esta ocupado, revisa la URL impresa por la terminal de frontend.

Si los datos demo parecen repetidos, recuerda que el seed reutiliza registros `CERESA-DEMO` y no borra datos reales. Para pruebas automatizadas, usa la suite pytest, que limpia `data/ceresa_test.db`.

## Checklist antes de entregar cambios

Para cambios backend:

```powershell
$env:PYTHONPATH="src"; .\.venv\Scripts\pytest.exe
```

Para cambios frontend:

```powershell
cd frontend
npm.cmd run build
cd ..
```

Para revisar el estado del repo:

```powershell
git status --short --untracked-files=all
git diff --stat
```
