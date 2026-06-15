# CERESA PMS

**Sistema modular de gestión hotelera / Modular Hotel Management System**

[Español](#español) · [English](#english)

---

# Español

## Descripción

**CERESA** es un PMS (*Property Management System*) modular y desacoplado, diseñado para adaptarse a hoteles de diferentes tamaños, estructuras y niveles tecnológicos.

El objetivo del proyecto es ofrecer una plataforma flexible que pueda utilizarse tanto en pequeños alojamientos como en hoteles de gran capacidad. Cada instalación podrá activar únicamente los módulos que necesite, sin depender de funciones o tecnologías que el establecimiento no utilice.

Un hotel podrá trabajar con Ceresa aunque no disponga de cerraduras electrónicas, tarjetas magnéticas, iluminación inteligente, control remoto de climatización, piscina, spa u otras integraciones avanzadas.

CERESA se encuentra actualmente en desarrollo activo y todavía no está preparado para uso en producción.

---

## Objetivos principales

Ceresa busca centralizar y simplificar las operaciones del hotel mediante una arquitectura que permita:

* Activar o desactivar módulos según las necesidades de cada establecimiento.
* Mantener separados los datos y responsabilidades de cada sector.
* Evitar que un módulo defectuoso impida la carga de los demás módulos.
* Adaptar la aplicación a hoteles pequeños, medianos o grandes.
* Permitir futuras integraciones con hardware, aplicaciones móviles y servicios externos.
* Reducir tareas repetitivas y mejorar la comunicación interna.
* Preparar cada módulo para que pueda evolucionar o separarse como servicio independiente.

---

## Arquitectura modular

Ceresa se desarrolla inicialmente como un **monolito modular**.

Cada módulo posee sus propias rutas, responsabilidades y pruebas. Un cargador dinámico controla qué módulos están activados, cuáles fueron implementados, cuáles se cargaron correctamente y cuáles presentaron errores.

Ejemplo del estado de un módulo:

```json
{
  "name": "reception",
  "enabled": true,
  "implemented": true,
  "loaded": true,
  "error": null
}
```

La configuración de cada instalación se gestiona mediante archivos externos:

```text
config/modules.json
config/hotel.json
```

Esto permite modificar la configuración del hotel sin alterar directamente el código fuente.

---

## Tecnologías principales

* Python
* FastAPI
* SQLite
* Pydantic
* Uvicorn
* pytest
* Git y GitHub

La aplicación funciona localmente durante su etapa inicial de desarrollo y utiliza una base de datos separada para las pruebas automatizadas.

---

## Módulos actuales

Ceresa cuenta actualmente con la infraestructura base para los siguientes módulos:

* System
* Rooms
* Users
* Guests
* Reservations
* Reception
* Housekeeping
* Maintenance
* Kitchen
* Bar
* Dining Room
* Beach
* Transport
* Tourism
* Security
* Laundry
* Leisure
* Inventory
* Billing
* Accounting

Algunos módulos ya contienen operaciones y persistencia real, mientras que otros disponen por el momento de una estructura inicial, un endpoint de estado y pruebas de carga.

### Diferencia entre módulos económicos

**Billing** administra las cuentas de los huéspedes:

* Alojamiento.
* Consumos.
* Servicios adicionales.
* Pagos.
* Descuentos.
* Saldo pendiente.
* Información necesaria durante el check-out.

**Accounting** administra la contabilidad general del hotel:

* Ingresos y egresos.
* Proveedores.
* Sueldos.
* Impuestos.
* Gastos por sector.
* Cierres mensuales.
* Informes financieros.

Recepción podrá consultar la información de `billing` durante el check-out, mientras que `accounting` mantendrá la visión económica general del establecimiento.

---

## Aislamiento de módulos

Ceresa está diseñado para que cada hotel pueda utilizar solamente las áreas que necesite.

Por ejemplo, una instalación pequeña podría activar:

```text
rooms
reception
guests
reservations
housekeeping
billing
```

Un hotel más grande podría agregar:

```text
maintenance
kitchen
bar
dining_room
beach
transport
tourism
security
laundry
leisure
inventory
accounting
```

Las integraciones opcionales no deben convertirse en dependencias obligatorias del núcleo del PMS.

Ceresa ya incorpora un mecanismo para detectar errores durante la carga de un módulo y mantener disponibles los módulos que pudieron iniciarse correctamente.

---

## Funciones planificadas

A medida que avance el proyecto, Ceresa podrá incorporar:

* Check-in y check-out.
* Perfiles e historial de huéspedes.
* Reservas y asignación de habitaciones.
* Cuentas, cargos y pagos.
* Gestión contable.
* Control de inventarios por sector.
* Comunicación interna entre empleados y responsables.
* Home page personalizada según usuario, rol y sector.
* Aplicación móvil para clientes y personal.
* Solicitudes de transporte.
* Ubicación GPS con consentimiento explícito.
* Integración con cerraduras electrónicas.
* Tarjetas magnéticas, NFC o llaves digitales.
* Control de luces y climatización.
* Gestión de piscina, spa y jacuzzi.
* Acceso desde dispositivos móviles y, cuando sea útil, relojes inteligentes.
* Registros de auditoría y trazabilidad de acciones.

Estas funciones se implementarán progresivamente y no deben considerarse terminadas hasta contar con sus respectivas pruebas.

---

## Automatización e inteligencia artificial

Ceresa podrá incluir herramientas opcionales de automatización o inteligencia artificial para reducir tareas administrativas repetitivas.

Un ejemplo futuro sería un asistente del módulo de contabilidad capaz de:

* Recibir documentos.
* Extraer información.
* Proponer el llenado de formularios.
* Clasificar comprobantes.
* Preparar datos para revisión.

Estas herramientas deberán funcionar con validación humana, permisos específicos y registros de auditoría. La IA será una ayuda para los empleados, no un reemplazo del control profesional.

---

## Seguridad

La seguridad de los datos es una prioridad del proyecto.

Las futuras fases contemplarán:

* Autenticación segura.
* Roles y permisos por sector.
* Separación entre clientes y personal.
* Protección de datos sensibles.
* Consentimiento explícito para compartir ubicación.
* Autenticación biométrica cuando el dispositivo lo permita.
* Códigos o métodos adicionales de acceso.
* Registro de acciones importantes.
* Protección de información contable y administrativa.
* Integración segura con tarjetas, cerraduras y dispositivos externos.

Cada usuario deberá acceder únicamente a los datos y funciones necesarios para su trabajo.

---

## Estado actual del desarrollo

El proyecto se encuentra en una fase de construcción de infraestructura y módulos principales.

El orden general de desarrollo es:

1. Crear los módulos principales.
2. Probar individualmente cada módulo.
3. Implementar la lógica funcional de cada área.
4. Crear submódulos.
5. Definir jerarquías y permisos.
6. Diseñar la comunicación entre sectores.
7. Crear home pages según usuario y rol.
8. Incorporar interfaz web y aplicación móvil.
9. Integrar hardware y servicios externos.
10. Ejecutar una prueba integral final del sistema.

---

## Instalación local en Windows

Clonar el repositorio:

```powershell
git clone https://github.com/juancruzgentile/PMS-Hotel-Ceresa.git
cd PMS-Hotel-Ceresa
```

Crear el entorno virtual:

```powershell
python -m venv .venv
```

Activarlo:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instalar las dependencias:

```powershell
python -m pip install -r requirements.txt
```

Ejecutar el servidor:

```powershell
$env:PYTHONPATH="src"
python -m uvicorn ceresa.main:app --reload
```

Abrir la documentación interactiva:

```text
http://127.0.0.1:8000/docs
```

---

## Pruebas automatizadas

Ceresa utiliza `pytest`.

Para ejecutar todas las pruebas:

```powershell
$env:PYTHONPATH="src"
pytest
```

Los tests utilizan una base de datos separada:

```text
data/ceresa_test.db
```

La aplicación local utiliza:

```text
data/ceresa.db
```

Ambas bases locales están excluidas del repositorio mediante `.gitignore`.

---

## Configuración

Los módulos se activan o desactivan desde:

```text
config/modules.json
```

Los datos básicos del hotel se configuran desde:

```text
config/hotel.json
```

Cada instalación podrá adaptar Ceresa sin modificar directamente el código de los módulos.

---

## Advertencia

Ceresa es actualmente un proyecto en desarrollo.

No debe utilizarse todavía para almacenar datos reales de clientes, pagos, documentos personales o información confidencial de un hotel en producción.

---

# English

## Description

**CERESA** is a modular and decoupled PMS (*Property Management System*) designed to adapt to hotels with different sizes, structures, and technological capabilities.

The goal of the project is to provide a flexible platform suitable for both small accommodations and large hotels. Each installation will be able to enable only the modules it needs, without depending on features or technologies that the property does not use.

A hotel will be able to use Ceresa even if it does not have electronic locks, magnetic cards, smart lighting, remote climate control, a swimming pool, a spa, or other advanced integrations.

CERESA is currently under active development and is not yet ready for production use.

---

## Main objectives

Ceresa aims to centralize and simplify hotel operations through an architecture that makes it possible to:

* Enable or disable modules according to each property's needs.
* Keep the data and responsibilities of each department separated.
* Prevent a defective module from blocking the loading of other modules.
* Adapt the application to small, medium, or large hotels.
* Support future integrations with hardware, mobile applications, and external services.
* Reduce repetitive tasks and improve internal communication.
* Prepare every module to evolve or become an independent service in the future.

---

## Modular architecture

Ceresa is initially being developed as a **modular monolith**.

Each module has its own routes, responsibilities, and tests. A dynamic module loader controls which modules are enabled, implemented, successfully loaded, or affected by errors.

Example module status:

```json
{
  "name": "reception",
  "enabled": true,
  "implemented": true,
  "loaded": true,
  "error": null
}
```

Installation-specific configuration is managed through external files:

```text
config/modules.json
config/hotel.json
```

This allows the hotel configuration to change without directly modifying the source code.

---

## Main technologies

* Python
* FastAPI
* SQLite
* Pydantic
* Uvicorn
* pytest
* Git and GitHub

During its initial development stage, the application runs locally and uses a separate database for automated tests.

---

## Current modules

Ceresa currently includes the base infrastructure for the following modules:

* System
* Rooms
* Users
* Guests
* Reservations
* Reception
* Housekeeping
* Maintenance
* Kitchen
* Bar
* Dining Room
* Beach
* Transport
* Tourism
* Security
* Laundry
* Leisure
* Inventory
* Billing
* Accounting

Some modules already contain real operations and persistence, while others currently provide an initial structure, a status endpoint, and module-loading tests.

### Difference between financial modules

**Billing** manages guest accounts:

* Accommodation charges.
* Consumption and services.
* Additional charges.
* Payments.
* Discounts.
* Outstanding balances.
* Check-out information.

**Accounting** manages the hotel's overall finances:

* Income and expenses.
* Suppliers.
* Payroll.
* Taxes.
* Department expenses.
* Monthly closings.
* Financial reports.

Reception will be able to access `billing` information during check-out, while `accounting` will maintain the overall financial view of the property.

---

## Module isolation

Ceresa is designed so that each property can use only the areas it needs.

A small installation could enable:

```text
rooms
reception
guests
reservations
housekeeping
billing
```

A larger hotel could also enable:

```text
maintenance
kitchen
bar
dining_room
beach
transport
tourism
security
laundry
leisure
inventory
accounting
```

Optional integrations must not become mandatory dependencies of the PMS core.

Ceresa already includes a mechanism that detects module-loading errors while keeping successfully loaded modules available.

---

## Planned capabilities

As development progresses, Ceresa may include:

* Check-in and check-out.
* Guest profiles and history.
* Reservations and room assignment.
* Accounts, charges, and payments.
* Hotel accounting.
* Department-specific inventory management.
* Internal communication between employees and supervisors.
* Personalized home pages based on user, role, and department.
* A mobile application for guests and staff.
* Transport requests.
* GPS location with explicit user consent.
* Electronic lock integrations.
* Magnetic cards, NFC, or digital keys.
* Lighting and climate control.
* Pool, spa, and jacuzzi management.
* Access from mobile devices and, when useful, smartwatches.
* Audit logs and action traceability.

These capabilities will be implemented progressively and should not be considered complete until their corresponding tests are available.

---

## Automation and artificial intelligence

Ceresa may include optional automation or artificial intelligence tools to reduce repetitive administrative tasks.

A future example could be an accounting assistant able to:

* Receive documents.
* Extract information.
* Suggest form completion.
* Classify receipts.
* Prepare data for human review.

These tools must operate with human validation, specific permissions, and audit logs. AI will support hotel employees rather than replace professional control.

---

## Security

Data security is a core priority of the project.

Future development phases will include:

* Secure authentication.
* Department-based roles and permissions.
* Separation between guest and staff access.
* Protection of sensitive data.
* Explicit consent for location sharing.
* Biometric authentication when supported by the device.
* PIN codes or additional access methods.
* Logging of important actions.
* Protection of accounting and administrative information.
* Secure integrations with cards, locks, and external devices.

Each user should access only the data and functions required for their responsibilities.

---

## Current development status

The project is currently in the infrastructure and main-module construction phase.

The general development order is:

1. Create the main modules.
2. Test each module individually.
3. Implement the functional logic of each area.
4. Create submodules.
5. Define hierarchies and permissions.
6. Design communication between departments.
7. Create role-specific home pages.
8. Build the web interface and mobile application.
9. Integrate hardware and external services.
10. Run the final complete system integration test.

---

## Local installation on Windows

Clone the repository:

```powershell
git clone https://github.com/juancruzgentile/PMS-Hotel-Ceresa.git
cd PMS-Hotel-Ceresa
```

Create the virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Start the server:

```powershell
$env:PYTHONPATH="src"
python -m uvicorn ceresa.main:app --reload
```

Open the interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Automated tests

Ceresa uses `pytest`.

Run all tests with:

```powershell
$env:PYTHONPATH="src"
pytest
```

Tests use a separate database:

```text
data/ceresa_test.db
```

The local application uses:

```text
data/ceresa.db
```

Both local databases are excluded from the repository through `.gitignore`.

---

## Configuration

Modules can be enabled or disabled through:

```text
config/modules.json
```

Basic hotel information is configured through:

```text
config/hotel.json
```

Each installation will be able to adapt Ceresa without directly modifying module source code.

---

## Disclaimer

Ceresa is currently a work in progress.

It should not yet be used to store real guest data, payments, personal documents, or confidential hotel information in a production environment.
