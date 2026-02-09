# AutoTramite Python MVP

Sistema de automatizacion de tramites vehiculares para AutoTramite.cl, con generacion de PDF TAG y envio de correos de cierre de negocio.

---

## Vision General

Este repositorio implementa tres procesos independientes bajo una misma interfaz Streamlit:

1. **AutoTramite** - Automatiza la creacion y registro de contratos de compraventa en AutoTramite.cl usando Playwright.
2. **Habilitacion Tag** - Genera un PDF editable de Solicitud TAG desde texto libre, rellenando un formulario AcroForm.
3. **Mail de Cierre** - Envia correos automatizados de cierre de negocio con vista previa, CC visible y registro de historial.

### Problemas que resuelve

- Reduce la digitacion manual en el portal AutoTramite.cl.
- Estandariza validaciones de RUT (modulo 11), patente, email y telefono chilenos.
- Acelera la generacion de PDFs de solicitud TAG.
- Automatiza el envio de emails de confirmacion de venta con trazabilidad.

### Fuera de alcance

- No es un backend con API publica.
- No hace OCR ni interpreta PDFs escaneados.
- No persiste resultados en base de datos (usa JSON local o storage externo).
- No ejecuta n8n en runtime (solo referencia de workflow).

---

## Estructura del Repositorio

```
autotramite_py_mvp/
|
|-- app.py                      # Punto de entrada Streamlit (UI principal)
|-- run_autotramite_cli.py      # CLI alternativo para AutoTramite
|-- test_preview.py             # Dry-run de prevision sin registrar
|
|-- src/
|   |-- __init__.py
|   |-- autotramite.py          # Motor de automatizacion Playwright
|   |-- models.py               # Modelos Pydantic + parser de texto
|   |-- validators.py           # Validaciones chilenas (RUT, patente, email, tel)
|   |-- config.py               # Settings y selectores CSS de AutoTramite
|   |-- logging_utils.py        # Utilidades de logging con ofuscacion PII
|   |-- mail_utils.py           # Generacion y envio de emails SMTP
|
|-- tests/
|   |-- test_validators.py      # Tests unitarios de validadores
|
|-- docs/
|   |-- autotramite/            # Documentacion del flujo AutoTramite
|   |   |-- README.md           # Detalle de la funcionalidad
|   |   |-- INSTRUCCIONES_TEST.md  # Paso a paso para test de previs.
|   |   |-- MIGRATION_PLAN.md   # Plan de migracion n8n -> Python
|   |   |-- test.md             # Datos de prueba para dry-run
|   |   |-- ref/                # Workflow n8n original (referencia)
|   |   |-- screenshots/        # Capturas de ejemplo
|   |
|   |-- tag/                    # Documentacion del flujo Habilitacion Tag
|   |   |-- tag-pdf-autofill-implementation-guide.md  # Guia de implementacion
|   |   |-- PDF-EJEMPLO.pdf     # Plantilla AcroForm de solicitud TAG
|   |   |-- testtag.md          # Datos de prueba para TAG
|   |   |-- test_preview_tag.py # Script de test directo (sin UI)
|   |   |-- output/             # PDFs generados (no versionados)
|   |
|   |-- correo-cierre/          # Documentacion del flujo Mail de Cierre
|   |   |-- mail-de-cierre-implementation-guide.md  # Guia completa
|   |   |-- IMPLEMENTATION_SUMMARY.md  # Resumen de implementacion
|   |   |-- CONFIGURACION_CC.md        # Configuracion de CC
|   |   |-- COMO_EDITAR_PLANTILLA.md   # Edicion de plantillas
|   |   |-- GUIA_MIGRACION_HTML.md     # Migracion a HTML (futuro)
|   |   |-- plantilla.md              # Plantilla del email
|   |   |-- mail_config.yaml          # Configuracion YAML del modulo
|   |   |-- enviados/                 # Historial JSON (no versionado)
|   |
|   |-- deploy/                 # Documentacion de despliegue
|   |   |-- RAILWAY_DEPLOY.md          # Guia rapida Railway
|   |   |-- RAILWAY_DEPLOYMENT.md      # Guia completa Railway (18 pags)
|   |   |-- SOLUCION_RAILWAY.md        # Fix sesiones duplicadas
|   |
|   |-- seguridad/              # Documentacion de seguridad
|   |   |-- ARCHIVOS_PROTEGIDOS.md     # Archivos sensibles y .gitignore
|   |   |-- RECUPERACION_SEGURIDAD.md  # Procedimiento si se filtran creds
|   |   |-- VERIFICAR_LIMPIEZA.bat     # Script verificacion Windows
|   |   |-- VERIFICAR_LIMPIEZA.sh      # Script verificacion Unix
|   |
|   |-- proyecto/               # Documentacion general del proyecto
|       |-- GENERAL.md          # Guia rapida general
|       |-- AGENTS.md           # Guidelines de desarrollo y estilo
|
|-- Dockerfile                  # Imagen Docker para Railway
|-- railway.json                # Config de build/deploy Railway
|-- requirements.txt            # Dependencias Python
|-- .env.example                # Plantilla de variables de entorno
|-- .gitignore                  # Archivos excluidos de Git
|-- CLAUDE.md                   # Guia para Claude Code
```

---

## Requisitos

### Sistema

- Python 3.10 o superior
- Playwright + Chromium (solo para AutoTramite)
- Conexion a internet (AutoTramite y Mail de Cierre requieren acceso a servicios externos)

### Dependencias principales

| Paquete | Uso |
|---------|-----|
| `streamlit` | Interfaz web |
| `playwright` | Automatizacion de browser (AutoTramite) |
| `pydantic` | Modelos de datos y validacion |
| `pypdf` | Lectura/escritura de AcroForm (TAG) |
| `PyYAML` | Configuracion YAML (Mail de Cierre) |
| `boto3` | Storage S3 (opcional) |
| `google-cloud-storage` | Storage GCS (opcional) |

---

## Instalacion

```bash
# 1. Clonar el repositorio
git clone https://github.com/denparra/gestordocs.git
cd gestordocs/autotramite_py_mvp

# 2. Crear y activar entorno virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Instalar navegador Playwright (solo si usaras AutoTramite)
playwright install chromium

# 5. Configurar credenciales
cp .env.example .env
# Editar .env con credenciales reales (ver seccion Configuracion)
```

---

## Configuracion (.env)

Copiar `.env.example` a `.env` y completar con valores reales.

### Variables obligatorias

| Variable | Descripcion | Requerido por |
|----------|-------------|---------------|
| `AUTOTRAMITE_EMAIL` | Email de login en AutoTramite.cl | AutoTramite |
| `AUTOTRAMITE_PASSWORD` | Password de AutoTramite.cl | AutoTramite |
| `SMTP_HOST` | Servidor SMTP (ej: `smtp.gmail.com`) | Mail de Cierre |
| `SMTP_PORT` | Puerto SMTP (ej: `587`) | Mail de Cierre |
| `SMTP_USER` | Usuario SMTP | Mail de Cierre |
| `SMTP_PASS` | Password SMTP | Mail de Cierre |
| `SMTP_SECURE` | Seguridad: `tls`, `ssl` o `none` | Mail de Cierre |

### Variables opcionales

| Variable | Default | Descripcion |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Nivel de logging (`DEBUG` para troubleshooting) |
| `PLAYWRIGHT_HEADLESS` | `True` | `False` para ver el browser |
| `PLAYWRIGHT_SLOW_MO` | `0` | Delay entre acciones (ms, util para debug) |
| `TIMEOUT_NAVIGATION` | `30000` | Timeout carga de pagina (ms) |
| `TIMEOUT_ELEMENT` | `10000` | Timeout espera de elemento (ms) |
| `MAX_REINTENTOS` | `3` | Intentos de reintento por error recuperable |
| `DELAY_BASE_MS` | `2000` | Base de backoff exponencial (ms) |
| `PDF_STORAGE_BACKEND` | *(local)* | `s3` o `gcs` para storage externo |

Para variables de S3/GCS, ver [`docs/deploy/RAILWAY_DEPLOY.md`](docs/deploy/RAILWAY_DEPLOY.md).

---

## Ejecucion

```bash
# Iniciar la aplicacion web (abre en http://localhost:8501)
streamlit run app.py
```

La interfaz presenta un menu principal con 3 tarjetas interactivas, una por cada funcionalidad.

---

## Guia de Uso por Funcionalidad

### 1. AutoTramite (Registro de Contratos)

**Que hace**: Automatiza el login, llenado de formulario y registro/previsualizacion de contratos de compraventa en AutoTramite.cl.

**Entrada**: Texto libre con datos del vehiculo, vendedor y comprador (copiado de CAV + Nota de Venta).

```
DATOS DEL VEHICULO
Marca: HYUNDAI
Patente: DRLZ.16-3
Modelo: ELANTRA GLS 1.6
Ano: 2012
...

DATOS DEL VENDEDOR
Nombre: JUAN CARLOS PEREZ GONZALEZ
RUT: 12.345.678-9
...

DATOS COMPRADOR
Nombre: MARIA ANDREA LOPEZ SILVA
RUT: 11.222.333-4
...
```

**Proceso**:
1. `parsear_texto_contrato()` extrae y valida los datos (RUT mod 11, patente, email, telefono).
2. Playwright abre AutoTramite.cl, hace login automatico.
3. Llena el formulario con delays humanizados.
4. Genera previsualizacion PDF o registra el contrato (segun modo).

**Salida**:
- PDF de previsualizacion descargable.
- Confirmacion de registro (si dry-run esta desactivado).
- PDF guardado en `screenshots/` (local) o storage externo (S3/GCS).

**Documentacion detallada**: [`docs/autotramite/README.md`](docs/autotramite/README.md)

---

### 2. Habilitacion Tag (Generacion PDF)

**Que hace**: Toma texto libre con datos del propietario y genera un PDF editable de Solicitud TAG rellenando una plantilla AcroForm.

**Entrada**: Texto libre con lineas tipo:

```
Nombre: MARIO HUMBERTO VERA VALENCIA
RUT: 10759120-6
Direccion: CALLE CHUQUICAMATA 814, LA CALERA.
Telefono: 977583559
Correo: mario.vera@ejemplo.cl
PATENTE: KYTR.55-5
TAG 147258369
```

**Proceso**:
1. Parseo con regex y normalizacion (RUT, patente, telefono).
2. Mapeo a CAMPO1..CAMPO16 (campos AcroForm del PDF).
3. Relleno de plantilla PDF con `pypdf`.

**Salida**:
- PDF generado en `docs/tag/output/Solicitud-Tag-[PATENTE].pdf`.
- Descargable desde la UI o subido a storage externo.

**No requiere** Playwright ni credenciales de AutoTramite.

**Documentacion detallada**: [`docs/tag/tag-pdf-autofill-implementation-guide.md`](docs/tag/tag-pdf-autofill-implementation-guide.md)

---

### 3. Mail de Cierre (Email de Confirmacion)

**Que hace**: Envia un email automatizado de cierre de negocio con datos del cliente, vehiculo y precio, con soporte para vista previa, CC visible y registro de historial.

**Entrada** (formulario en UI):
- **DATOS_PROPIETARIO**: Texto con datos del propietario (se extrae el nombre automaticamente).
- **Vehiculo**: Descripcion del vehiculo.
- **Precio Acordado**: Monto de la venta.
- **Fecha de Pago**: Rango de fechas.
- **Email Destino (TO)**: Direccion principal del destinatario.
- **CC**: Direcciones de copia visible, separadas por coma.

**Proceso**:
1. Validacion de datos y configuracion SMTP.
2. Generacion de email desde plantilla (`docs/correo-cierre/plantilla.md`).
3. Vista previa editable (opcional): sujeto y cuerpo modificables.
4. Envio via SMTP con CC visible (no BCC).
5. Guardado de historial en JSON con ofuscacion de emails.

**Salida**:
- Email enviado al destinatario y CC.
- Historial guardado en `docs/correo-cierre/enviados/`.
- Cooldown de 30 segundos entre envios.

**Configuracion del modulo**: [`docs/correo-cierre/mail_config.yaml`](docs/correo-cierre/mail_config.yaml)

**Documentacion detallada**:
- [`docs/correo-cierre/mail-de-cierre-implementation-guide.md`](docs/correo-cierre/mail-de-cierre-implementation-guide.md)
- [`docs/correo-cierre/IMPLEMENTATION_SUMMARY.md`](docs/correo-cierre/IMPLEMENTATION_SUMMARY.md)
- [`docs/correo-cierre/CONFIGURACION_CC.md`](docs/correo-cierre/CONFIGURACION_CC.md)
- [`docs/correo-cierre/COMO_EDITAR_PLANTILLA.md`](docs/correo-cierre/COMO_EDITAR_PLANTILLA.md)

---

## Tests y Scripts de Prueba

### Tests unitarios (pytest)

```bash
# Ejecutar todos los tests
pytest

# Verbose
pytest -v

# Test especifico
pytest tests/test_validators.py -v

# Con cobertura
pytest --cov=src tests/
```

### Dry-run de AutoTramite (sin registrar)

```bash
# Ejecuta el flujo completo pero no registra el contrato
python test_preview.py
```

Usa los datos de `docs/autotramite/test.md`. Guarda el PDF en `screenshots/`.
Ver instrucciones completas en [`docs/autotramite/INSTRUCCIONES_TEST.md`](docs/autotramite/INSTRUCCIONES_TEST.md).

### Test de Habilitacion Tag (sin UI)

```bash
python docs/tag/test_preview_tag.py
```

Genera un PDF de prueba en `docs/tag/output/`.

---

## Interacción con n8n

El proyecto incluye capacidades para gestionar workflows de n8n directamente desde la línea de comandos.

### Script de Gestión de Workflows

**Ubicación:** `C:\Users\denny\OneDrive\Documentos\PRACTICAS\PYTHON\Streamlit\BOTH\n8n\scripts\n8n\workflow_manager.js`

Este script Node.js permite crear, actualizar, activar y gestionar workflows mediante la API REST de n8n.

**Requisitos:**
- Node.js instalado
- Variables de entorno en `.env`:
  - `N8N_API_URL` - URL de la API de n8n (ej: `https://n8n-n8n.wqzejs.easypanel.host/api/v1`)
  - `N8N_API_KEY` - API Key de n8n

**Comandos disponibles:**

```bash
# Listar todos los workflows
node C:\Users\denny\OneDrive\Documentos\PRACTICAS\PYTHON\Streamlit\BOTH\n8n\scripts\n8n\workflow_manager.js list

# Ver detalles completos de un workflow
node C:\Users\denny\OneDrive\Documentos\PRACTICAS\PYTHON\Streamlit\BOTH\n8n\scripts\n8n\workflow_manager.js get <workflow_id>

# Crear nuevo workflow desde archivo JSON
node C:\Users\denny\OneDrive\Documentos\PRACTICAS\PYTHON\Streamlit\BOTH\n8n\scripts\n8n\workflow_manager.js create <archivo.json>

# Actualizar workflow existente
node C:\Users\denny\OneDrive\Documentos\PRACTICAS\PYTHON\Streamlit\BOTH\n8n\scripts\n8n\workflow_manager.js update <workflow_id> <archivo.json>

# Activar/desactivar workflow
node C:\Users\denny\OneDrive\Documentos\PRACTICAS\PYTHON\Streamlit\BOTH\n8n\scripts\n8n\workflow_manager.js activate <workflow_id>
node C:\Users\denny\OneDrive\Documentos\PRACTICAS\PYTHON\Streamlit\BOTH\n8n\scripts\n8n\workflow_manager.js deactivate <workflow_id>

# Eliminar workflow
node C:\Users\denny\OneDrive\Documentos\PRACTICAS\PYTHON\Streamlit\BOTH\n8n\scripts\n8n\workflow_manager.js delete <workflow_id>
```

### Documentación de Integración

Para detalles completos sobre la integración n8n + Telegram, ver:
- [`docs/n8n/FLUJO_INTEGRACION_N8N_TELEGRAM.md`](docs/n8n/FLUJO_INTEGRACION_N8N_TELEGRAM.md)

---

## Deployment en Railway

El proyecto incluye `Dockerfile` y `railway.json` para despliegue directo en Railway.

```bash
# Start command recomendado
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

**Importante**: El filesystem de Railway es efimero. Los PDFs generados localmente no persisten entre deploys. Se recomienda descarga inmediata o configurar storage externo (S3/GCS).

**Guias de despliegue**:
- [`docs/deploy/RAILWAY_DEPLOY.md`](docs/deploy/RAILWAY_DEPLOY.md) - Guia rapida
- [`docs/deploy/RAILWAY_DEPLOYMENT.md`](docs/deploy/RAILWAY_DEPLOYMENT.md) - Guia completa
- [`docs/deploy/SOLUCION_RAILWAY.md`](docs/deploy/SOLUCION_RAILWAY.md) - Fix sesiones duplicadas

---

## Troubleshooting

### AutoTramite

| Error | Causa | Solucion |
|-------|-------|----------|
| "AUTOTRAMITE_EMAIL no configurado" | Falta `.env` | Crear `.env` desde `.env.example` |
| "Login fallido" | Credenciales invalidas | Verificar email y password en `.env` |
| "Timeout esperando campo" | Selector obsoleto o conexion lenta | Aumentar timeouts o revisar `src/config.py` |
| 401 Unauthorized | API key expirada | Regenerar clave en AutoTramite.cl |

### Habilitacion Tag

| Error | Causa | Solucion |
|-------|-------|----------|
| PDF no se genera | Plantilla no encontrada | Verificar que `docs/tag/PDF-EJEMPLO.pdf` existe |
| Campos vacios en PDF | Texto de entrada malformado | Revisar formato de entrada (Nombre, RUT, etc.) |

### Mail de Cierre

| Error | Causa | Solucion |
|-------|-------|----------|
| "SMTP no configurado" | Faltan variables SMTP en `.env` | Agregar SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS |
| "Error de autenticacion SMTP" | Credenciales SMTP invalidas | Gmail: usar App Password. Verificar usuario/pass |
| "mail_config.yaml no encontrado" | Falta el archivo de config | Verificar que `docs/correo-cierre/mail_config.yaml` existe |
| CC no recibidos | Emails invalidos o spam | Verificar direcciones CC, revisar carpeta spam |

### General

| Error | Causa | Solucion |
|-------|-------|----------|
| `ModuleNotFoundError` | Dependencias no instaladas | `pip install -r requirements.txt` |
| `playwright._impl._errors.Error` | Chromium no instalado | `playwright install chromium` |

---

## Indice de Documentacion

| Documento | Ubicacion | Descripcion |
|-----------|-----------|-------------|
| **AutoTramite** | | |
| Detalle del flujo | [`docs/autotramite/README.md`](docs/autotramite/README.md) | Arquitectura y componentes |
| Instrucciones de test | [`docs/autotramite/INSTRUCCIONES_TEST.md`](docs/autotramite/INSTRUCCIONES_TEST.md) | Paso a paso para dry-run |
| Plan de migracion | [`docs/autotramite/MIGRATION_PLAN.md`](docs/autotramite/MIGRATION_PLAN.md) | Migracion n8n a Python |
| Datos de prueba | [`docs/autotramite/test.md`](docs/autotramite/test.md) | Input de ejemplo |
| Workflow n8n (ref) | [`docs/autotramite/ref/`](docs/autotramite/ref/) | Workflow original |
| **Habilitacion Tag** | | |
| Guia de implementacion | [`docs/tag/tag-pdf-autofill-implementation-guide.md`](docs/tag/tag-pdf-autofill-implementation-guide.md) | Mapeo de campos y logica |
| Datos de prueba | [`docs/tag/testtag.md`](docs/tag/testtag.md) | Input de ejemplo |
| **Mail de Cierre** | | |
| Guia de implementacion | [`docs/correo-cierre/mail-de-cierre-implementation-guide.md`](docs/correo-cierre/mail-de-cierre-implementation-guide.md) | Guia completa |
| Resumen implementacion | [`docs/correo-cierre/IMPLEMENTATION_SUMMARY.md`](docs/correo-cierre/IMPLEMENTATION_SUMMARY.md) | Que se implemento |
| Configuracion CC | [`docs/correo-cierre/CONFIGURACION_CC.md`](docs/correo-cierre/CONFIGURACION_CC.md) | Como configurar CC |
| Editar plantilla | [`docs/correo-cierre/COMO_EDITAR_PLANTILLA.md`](docs/correo-cierre/COMO_EDITAR_PLANTILLA.md) | Modificar template |
| Migracion HTML | [`docs/correo-cierre/GUIA_MIGRACION_HTML.md`](docs/correo-cierre/GUIA_MIGRACION_HTML.md) | Futuro: emails HTML |
| **Deploy** | | |
| Guia rapida Railway | [`docs/deploy/RAILWAY_DEPLOY.md`](docs/deploy/RAILWAY_DEPLOY.md) | Variables y comandos |
| Guia completa Railway | [`docs/deploy/RAILWAY_DEPLOYMENT.md`](docs/deploy/RAILWAY_DEPLOYMENT.md) | Troubleshooting completo |
| Fix sesiones | [`docs/deploy/SOLUCION_RAILWAY.md`](docs/deploy/SOLUCION_RAILWAY.md) | Error "Session already connected" |
| **Seguridad** | | |
| Archivos protegidos | [`docs/seguridad/ARCHIVOS_PROTEGIDOS.md`](docs/seguridad/ARCHIVOS_PROTEGIDOS.md) | Que protege .gitignore |
| Recuperacion | [`docs/seguridad/RECUPERACION_SEGURIDAD.md`](docs/seguridad/RECUPERACION_SEGURIDAD.md) | Si se filtran credenciales |
| **Proyecto** | | |
| Guia general | [`docs/proyecto/GENERAL.md`](docs/proyecto/GENERAL.md) | Overview rapido |
| Guidelines desarrollo | [`docs/proyecto/AGENTS.md`](docs/proyecto/AGENTS.md) | Estilo, testing, commits |

---

## Seguridad

- **NUNCA** commitear `.env` con credenciales reales.
- Usar `.env.example` como plantilla de referencia.
- Logs con PII ofuscada via `src/logging_utils.py`.
- Historial de emails con ofuscacion automatica.
- Ver [`docs/seguridad/ARCHIVOS_PROTEGIDOS.md`](docs/seguridad/ARCHIVOS_PROTEGIDOS.md) para detalle completo.

---

## Arquitectura de Datos

```
Texto de Entrada (CAV / Nota de Venta / Texto libre)
    |
    v
parsear_texto_contrato() / _tag_parse_text() [src/models.py / app.py]
    |
    v
Validacion [src/validators.py]
  - RUT: Modulo 11 (K para 10, 0 para 11)
  - Patente: Antiguo (XXNN), Nuevo (NNXX), Vintage (XX00XX)
  - Email: Regex basico
  - Telefono: 8-9 digitos (estandar chileno)
    |
    v
Modelo Pydantic [src/models.py]
  - ContratoData (vehiculo + vendedor + comprador)
    |
    v
Accion:
  AutoTramite --> crear_contrato_autotramite() [src/autotramite.py]
  Tag         --> _tag_fill_pdf() [app.py + pypdf]
  Mail        --> enviar_email_smtp() [src/mail_utils.py]
```

---

## Roadmap

- Persistencia de PDFs en storage externo como default.
- UI mas guiada para errores de parsing.
- Emails HTML con imagenes inline.
- API REST para integraciones externas.
- Mayor cobertura de tests.
- Plantillas multiples para Mail de Cierre.

---

## FAQ

**P: Puedo usar esto sin credenciales de AutoTramite?**
R: La funcionalidad AutoTramite requiere login real. Habilitacion Tag y Mail de Cierre funcionan independientemente.

**P: Donde quedan los PDFs generados?**
R: En `screenshots/` (AutoTramite) y `docs/tag/output/` (Tag). En Railway el filesystem es efimero; se recomienda descarga inmediata o storage externo.

**P: Puedo usar solo el flujo Tag sin Playwright?**
R: Si. Tag usa solo `pypdf`, no requiere Playwright ni Chromium.

**P: Como configuro el storage externo (S3/GCS)?**
R: Define `PDF_STORAGE_BACKEND=s3` o `=gcs` y las variables correspondientes. Ver [`docs/deploy/RAILWAY_DEPLOY.md`](docs/deploy/RAILWAY_DEPLOY.md).

**P: Los CC del Mail de Cierre son visibles?**
R: Si. Se usan CC (copias visibles), no BCC, por requerimiento del negocio.

**P: Como edito la plantilla del email?**
R: Ver [`docs/correo-cierre/COMO_EDITAR_PLANTILLA.md`](docs/correo-cierre/COMO_EDITAR_PLANTILLA.md).
