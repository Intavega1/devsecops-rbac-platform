# DevSecOps RBAC Platform

Plataforma RBAC multiempresa orientada a microservicios para gestionar identidades, roles, permisos, sincronización de matrices y auditoría. El repositorio proporciona una base ejecutable con FastAPI, Docker Compose y servicios desacoplados, preparada para evolucionar hacia una plataforma completa de control de acceso con prácticas DevSecOps.

> **Estado actual:** scaffold técnico / MVP inicial. Los servicios disponen de endpoints de salud y el servicio de auditoría incluye un endpoint de recepción de eventos; la persistencia, autenticación JWT, autorización RBAC, sincronización real de Excel, mensajería y despliegues Terraform/K3s todavía deben implementarse.

## Índice

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Servicios](#servicios)
- [Stack tecnológico](#stack-tecnológico)
- [Requisitos](#requisitos)
- [Configuración](#configuración)
- [Ejecución local con Docker Compose](#ejecución-local-con-docker-compose)
- [Ejecución individual de servicios](#ejecución-individual-de-servicios)
- [API disponible](#api-disponible)
- [Comprobaciones y troubleshooting](#comprobaciones-y-troubleshooting)
- [Persistencia e infraestructura](#persistencia-e-infraestructura)
- [Seguridad y DevSecOps](#seguridad-y-devsecops)
- [Pruebas](#pruebas)
- [Roadmap](#roadmap)
- [Contribución](#contribución)
- [Licencia](#licencia)

## Características

- Arquitectura de microservicios con separación inicial por contexto de negocio.
- API Gateway basado en FastAPI para exponer el punto de entrada HTTP.
- Servicios independientes para identidad, RBAC, sincronización y auditoría.
- Worker separado para futuros trabajos asíncronos relacionados con archivos Excel.
- Un PostgreSQL dedicado por contexto: identidad, RBAC, sincronización y auditoría.
- RabbitMQ preparado como broker de mensajería.
- MinIO preparado como almacenamiento de objetos para archivos y artefactos.
- Contenedores basados en `python:3.14-slim` que ejecutan como usuario no root (`appuser`).
- Red Docker privada `backend` y volúmenes persistentes para las dependencias de infraestructura.
- Estructura reservada para Terraform y manifiestos de K3s.

## Arquitectura

```text
                         Cliente / consumidor HTTP
                                  |
                                  v
                    +-----------------------------+
                    | API Gateway :8000           |
                    | FastAPI + httpx              |
                    +--------------+--------------+
                                   |
              +--------------------+--------------------+
              |                    |                    |
              v                    v                    v
       identity-service     rbac-service         sync-service
              |                    |                    |
          identity-db           rbac-db             sync-db

              +------------------------------------------+
              |                                          |
              v                                          v
       audit-service                              excel-worker
              |                                          |
          audit-db                         RabbitMQ / MinIO (preparados)

       Todos los componentes internos se conectan mediante la red Docker `backend`.
```

### Flujo actual

1. El cliente llama al `api-gateway` en el puerto `8000`.
2. El gateway mantiene el mapa interno `SERVICES` y resuelve los servicios por sus nombres DNS de Docker: `identity-service`, `rbac-service`, `sync-service` y `audit-service`.
3. Las comprobaciones delegadas de salud se realizan mediante `httpx.AsyncClient` con timeout de cinco segundos.
4. Los microservicios FastAPI responden actualmente a `/health`.
5. `audit-service` valida eventos con el modelo Pydantic `AuditEvent` y devuelve una marca temporal UTC, pero todavía no persiste el evento.
6. `excel-worker` permanece en un bucle de espera de trabajos y todavía no consume mensajes ni procesa archivos.

## Estructura del repositorio

```text
.
├── .env.example                         # Variables de entorno de desarrollo
├── .gitignore                            # Exclusiones de Python, Terraform, secretos y logs
├── docker-compose.yml                     # Topología local completa
├── infraestructura/
│   └── terraform/                        # Reservado para IaC con Terraform
├── orquestacion/
│   └── k3s/                              # Reservado para manifiestos de K3s/Kubernetes
├── servicios/
│   ├── api-gateway/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/main.py                   # Entrada HTTP y proxy de health checks
│   ├── identity-service/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/main.py                   # Servicio de identidades; health check actual
│   ├── rbac-service/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/main.py                   # Servicio RBAC; health check actual
│   ├── sync-service/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/main.py                   # Servicio de sincronización; health check actual
│   ├── audit-service/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/main.py                   # Recepción y validación de eventos de auditoría
│   └── excel-worker/
│       ├── Dockerfile
│       ├── requirements.txt
│       └── app/worker.py                  # Worker base con bucle de espera
└── tests/                                 # Directorio reservado; actualmente contiene .gitkeep
```

## Servicios

| Componente | Responsabilidad | Puerto expuesto | Estado implementado |
|---|---|---:|---|
| `api-gateway` | Punto de entrada HTTP y health checks delegados | `8000` | `/health` y `/api/{service}/health` |
| `identity-service` | Identidades, usuarios y autenticación futura | Interno `8000` | `/health` |
| `rbac-service` | Roles, permisos y políticas futuras | Interno `8000` | `/health` |
| `sync-service` | Sincronización futura de matrices Excel | Interno `8000` | `/health` |
| `audit-service` | Registro de eventos de auditoría | Interno `8000` | `/health` y `POST /audit/events` |
| `excel-worker` | Procesamiento asíncrono futuro de Excel | No HTTP | Bucle de espera cada 30 segundos |
| PostgreSQL x4 | Bases aisladas por contexto | Solo red interna | Volúmenes Docker |
| RabbitMQ | Broker para tareas/eventos futuros | `5672`, `15672` | Contenedor disponible |
| MinIO | Almacenamiento de objetos futuro | `9000`, `9001` | Contenedor disponible |

## Stack tecnológico

- **Python 3.14** sobre imágenes `python:3.14-slim`.
- **FastAPI** para las APIs de los servicios.
- **Uvicorn** como servidor ASGI.
- **httpx** para las llamadas asíncronas del gateway a servicios internos.
- **Pydantic** para validar eventos de auditoría.
- **Docker Compose** para el entorno local.
- **PostgreSQL 17 Alpine** con una instancia lógica por dominio.
- **RabbitMQ 4 Management Alpine** como broker.
- **MinIO** como almacenamiento compatible con S3.
- **Terraform** y **K3s** como destinos de infraestructura/orquestación, actualmente sin archivos de implementación.

Las dependencias se declaran por servicio en archivos `requirements.txt`. No hay actualmente un `pyproject.toml`, `Makefile`, pipeline CI/CD ni suite automatizada configurada en el repositorio.

## Requisitos

- Git.
- Docker Engine 24+ y Docker Compose v2 (`docker compose`).
- Opcional para ejecución sin contenedores: Python 3.14 y `pip`.
- Puertos locales disponibles: `8000`, `5672`, `15672`, `9000` y `9001`.

## Configuración

1. Clona el repositorio y entra en él:

   ```bash
   git clone https://github.com/Intavega1/devsecops-rbac-platform.git
   cd devsecops-rbac-platform
   ```

2. Crea el archivo de entorno a partir de la plantilla:

   ```bash
   cp .env.example .env
   ```

3. Cambia todas las credenciales `change_me_*` antes de usar el entorno fuera de una máquina local. Las variables disponibles son:

   | Grupo | Variables |
   |---|---|
   | Identity PostgreSQL | `IDENTITY_DB_NAME`, `IDENTITY_DB_USER`, `IDENTITY_DB_PASSWORD` |
   | RBAC PostgreSQL | `RBAC_DB_NAME`, `RBAC_DB_USER`, `RBAC_DB_PASSWORD` |
   | Sync PostgreSQL | `SYNC_DB_NAME`, `SYNC_DB_USER`, `SYNC_DB_PASSWORD` |
   | Audit PostgreSQL | `AUDIT_DB_NAME`, `AUDIT_DB_USER`, `AUDIT_DB_PASSWORD` |
   | RabbitMQ | `RABBITMQ_USER`, `RABBITMQ_PASSWORD` |
   | MinIO | `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` |
   | Aplicación | `JWT_SECRET_KEY` |

> **Nota importante:** `docker-compose.yml` usa las variables de base de datos, RabbitMQ y MinIO para inicializar los contenedores de infraestructura. La lógica de los servicios todavía no carga explícitamente la configuración ni utiliza `JWT_SECRET_KEY`; esa integración debe añadirse junto con la implementación funcional.

## Ejecución local con Docker Compose

Construye las imágenes y arranca toda la plataforma en segundo plano:

```bash
docker compose up --build -d
```

Comprueba el estado de los contenedores:

```bash
docker compose ps
```

Prueba el gateway:

```bash
curl http://localhost:8000/health
```

Consulta la salud de cada servicio a través del gateway:

```bash
curl http://localhost:8000/api/identity/health
curl http://localhost:8000/api/rbac/health
curl http://localhost:8000/api/sync/health
curl http://localhost:8000/api/audit/health
```

Accesos auxiliares:

- RabbitMQ Management: <http://localhost:15672>
- MinIO Console: <http://localhost:9001>
- API Gateway: <http://localhost:8000>
- Documentación OpenAPI del gateway: <http://localhost:8000/docs>

Para ver logs:

```bash
docker compose logs -f
# Un servicio concreto
docker compose logs -f api-gateway
```

Para detener los contenedores conservando los volúmenes:

```bash
docker compose down
```

Para eliminar también los datos persistidos de PostgreSQL, RabbitMQ y MinIO:

```bash
docker compose down -v
```

> El último comando es destructivo para los datos locales.

## Ejecución individual de servicios

Los servicios HTTP pueden iniciarse desde su directorio con Uvicorn:

```bash
cd servicios/api-gateway
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Para iniciar `identity-service`, `rbac-service`, `sync-service` o `audit-service`, repite el procedimiento desde el directorio correspondiente. Por ejemplo:

```bash
cd servicios/audit-service
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

El worker se ejecuta así:

```bash
cd servicios/excel-worker
python app/worker.py
```

Cuando se ejecutan servicios individualmente fuera de Docker, los nombres DNS `identity-service`, `rbac-service`, etc. no estarán disponibles automáticamente; el gateway requerirá una configuración de URLs por entorno antes de realizar llamadas entre procesos locales.

## API disponible

### `GET /health`

Disponible en el gateway y en cada servicio HTTP.

Ejemplo de respuesta:

```json
{
  "service": "api-gateway",
  "status": "healthy"
}
```

### `GET /api/{service}/health`

El gateway acepta los valores `identity`, `rbac`, `sync` y `audit`.

Ejemplo:

```bash
curl http://localhost:8000/api/audit/health
```

Respuesta esperada:

```json
{
  "gateway": "healthy",
  "service": "audit",
  "service_status": {
    "service": "audit-service",
    "status": "healthy"
  }
}
```

Si se solicita un servicio no incluido en el mapa `SERVICES`, el gateway devuelve `404`. Si el servicio interno no responde, devuelve `502`.

### `POST /audit/events`

Recibe un evento validado por Pydantic en `audit-service`.

```bash
curl -X POST http://localhost:8000/audit/events \\
  -H 'Content-Type: application/json' \\
  -d '{
    "user_id": "user-123",
    "action": "role.assignment.requested",
    "service": "rbac-service",
    "status": "accepted",
    "details": "Asignación solicitada desde la consola administrativa"
  }'
```

Modelo de entrada:

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---:|---|
| `user_id` | `string` | Sí | Identificador del usuario que origina el evento |
| `action` | `string` | Sí | Acción auditada |
| `service` | `string` | Sí | Servicio que genera la acción |
| `status` | `string` | Sí | Resultado o estado de la acción |
| `details` | `string \| null` | No | Información adicional |

> En el Compose actual solo se publica el puerto del gateway. Para probar directamente `audit-service`, hay que publicar temporalmente su puerto o acceder desde otro contenedor de la red `backend`. Además, el gateway aún no implementa un proxy para `/audit/events`.

## Persistencia e infraestructura

`docker-compose.yml` define cuatro instancias aisladas de PostgreSQL:

- `identity-db` con volumen `identity_db_data`.
- `rbac-db` con volumen `rbac_db_data`.
- `sync-db` con volumen `sync_db_data`.
- `audit-db` con volumen `audit_db_data`.

También define:

- `rabbitmq` con puertos AMQP `5672` y consola `15672`.
- `minio` con API S3 `9000` y consola `9001`.
- Red bridge compartida `backend`.
- Contenedores de aplicación sin puertos públicos salvo `api-gateway`.

Los directorios `infraestructura/terraform` y `orquestacion/k3s` solo contienen actualmente `.gitkeep`; no existen módulos Terraform, deployments, services, ingress, secrets ni configuración de almacenamiento que puedan aplicarse todavía.

## Seguridad y DevSecOps

Medidas ya presentes:

- `.env` está excluido del control de versiones y `.env.example` sirve como plantilla.
- Claves privadas, certificados, estados Terraform y logs están incluidos en `.gitignore`.
- Los Dockerfiles crean y usan el usuario sin privilegios `appuser`.
- Las bases de datos no publican puertos al host en el Compose actual.
- Los servicios internos están aislados en la red `backend`.
- El gateway usa timeout de cinco segundos y traduce errores de conexión a HTTP `502`.
- La API de auditoría valida el payload antes de aceptarlo.

Antes de considerar el sistema listo para producción, se recomienda implementar:

1. Autenticación real y validación de JWT en el gateway y/o servicios.
2. Autorización multiempresa con aislamiento de tenant en cada operación.
3. Gestión persistente de usuarios, roles, permisos y relaciones usuario-tenant.
4. Rotación y almacenamiento seguro de secretos; nunca reutilizar los valores de `.env.example`.
5. Versionado y fijación de dependencias, escaneo de imágenes y análisis SAST/SCA.
6. TLS, rate limiting, CORS explícito, cabeceras de seguridad y validación de entrada consistente.
7. Auditoría persistente, inmutable y con correlación de solicitudes.
8. Health checks de Docker/Kubernetes, readiness/liveness probes y límites de recursos.
9. CI/CD con pruebas, linting, escaneo de secretos, build reproducible y despliegue controlado.
10. Políticas de backup, recuperación y migraciones de esquema para las cuatro bases.

## Pruebas

El directorio `tests/` está preparado para alojar pruebas, pero actualmente contiene únicamente `.gitkeep`. No hay una suite automatizada configurada ni un comando de test definido.

Como mínimo, la primera suite debería cubrir:

- `/health` de cada servicio.
- Rutas válidas y desconocidas de `/api/{service}/health`.
- Timeout y errores del gateway.
- Validación positiva y negativa de `AuditEvent`.
- Contratos entre gateway y servicios.
- Aislamiento por empresa/tenant cuando se implemente RBAC.
- Integración con PostgreSQL, RabbitMQ y MinIO mediante entornos efímeros.

## Roadmap

### Fase 1 — Base de plataforma

- [ ] Añadir configuración tipada por entorno.
- [ ] Fijar versiones de dependencias e imágenes.
- [ ] Añadir logging estructurado, correlation IDs y manejo global de errores.
- [ ] Crear pruebas unitarias, de contrato e integración.
- [ ] Añadir CI con lint, tests, escaneo de secretos y vulnerabilidades.

### Fase 2 — Identidad y seguridad

- [ ] Implementar registro, inicio de sesión y emisión/validación de JWT.
- [ ] Modelar tenants, usuarios, estados y credenciales.
- [ ] Añadir rotación/revocación de tokens y políticas de contraseña.
- [ ] Integrar el gateway con identity-service.

### Fase 3 — RBAC multiempresa

- [ ] Persistir roles, permisos y asignaciones por tenant.
- [ ] Implementar evaluación de permisos y middleware de autorización.
- [ ] Definir administración delegada y separación de funciones.
- [ ] Publicar contratos OpenAPI versionados.

### Fase 4 — Sincronización y auditoría

- [ ] Implementar carga y validación de matrices Excel.
- [ ] Almacenar archivos en MinIO y publicar trabajos en RabbitMQ.
- [ ] Completar `excel-worker` con reintentos e idempotencia.
- [ ] Persistir eventos de auditoría y exponer consulta segura.

### Fase 5 — Operación

- [ ] Crear módulos Terraform.
- [ ] Crear manifiestos K3s con Secrets, ConfigMaps, probes y políticas de red.
- [ ] Añadir observabilidad, métricas, trazas y alertas.
- [ ] Definir despliegue blue/green o canary, backups y recuperación ante desastres.

## Contribución

1. Crea una rama descriptiva:

   ```bash
   git checkout -b feat/nombre-del-cambio
   ```

2. Mantén los cambios acotados al servicio o componente correspondiente.
3. Añade o actualiza pruebas junto con la funcionalidad.
4. No incluyas `.env`, credenciales, claves privadas, estados Terraform ni logs.
5. Valida localmente:

   ```bash
   docker compose config
   docker compose up --build
   ```

6. Abre un Pull Request explicando el contexto, el diseño, las variables nuevas y cómo verificarlo.

## Licencia

El archivo `LICENSE` existe actualmente vacío. Antes de distribuir o desplegar el proyecto, el propietario debe seleccionar una licencia y completar dicho archivo.

## Estado de documentación

Este README describe el estado observado en la rama `main`: servicios FastAPI mínimos, topología Docker Compose, variables de entorno, infraestructura auxiliar preparada y áreas aún pendientes de implementación. Debe actualizarse junto con la incorporación de endpoints, persistencia, autenticación, consumidores RabbitMQ, módulos Terraform o manifiestos K3s.
