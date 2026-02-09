# Flujo de Integración n8n + Telegram
## AutoTramite MVP - Especificación Técnica

---

## 1. Visión General

### Objetivo
Habilitar el acceso a los 3 flujos principales del sistema (AutoTramite, Habilitación TAG, Mail de Cierre) a través de un bot de Telegram orquestado por n8n, manteniendo toda la lógica de validación y automatización existente en Python.

### Principios Guía
- **Practicidad**: Soluciones funcionales y directas
- **Reutilización**: Aprovechar toda la lógica Python existente
- **Simplicidad**: Arquitectura mínima viable sin complejidad innecesaria
- **No Invasivo**: Desarrollo en paralelo sin afectar funcionalidad actual

### ⚠️ IMPORTANTE: Implementación 100% en Paralelo (Sin Modificar Lo Existente)

**Esta integración NO modifica ningún código funcional actual.**

#### ✅ Archivos que NO se tocan (0% de cambios):

```
✅ app.py                    - Streamlit UI sigue intacto
✅ src/autotramite.py        - Motor Playwright sin cambios
✅ src/models.py             - Modelos Pydantic sin cambios
✅ src/validators.py         - Validadores sin cambios
✅ src/mail_utils.py         - Lógica de email sin cambios
✅ src/logging_utils.py      - Logging sin cambios
✅ src/config.py             - Configuración sin cambios
✅ tests/*                   - Tests existentes sin cambios
✅ .env                      - Variables actuales sin cambios
```

#### 📝 Archivos NUEVOS (adición pura):

```
📝 api.py                    - Nuevo: API FastAPI para n8n
📝 start.sh                  - Nuevo: Script de arranque dual
📝 docs/n8n/*.md             - Nuevo: Documentación
```

#### 🔧 Archivos con modificación MÍNIMA:

```
🔧 Dockerfile               - Solo agrega CMD para arranque dual
🔧 requirements.txt         - Solo agrega: fastapi, uvicorn
```

#### 🔄 Arquitectura de Doble Canal (Canales Independientes):

```
┌──────────────────────────────────────────────────────┐
│         CÓDIGO COMPARTIDO (sin modificar)            │
│   src/autotramite.py | models.py | validators.py    │
│   mail_utils.py | logging_utils.py | config.py      │
└──────────────┬───────────────────────┬───────────────┘
               │                       │
               │                       │
    ┌──────────▼─────────┐   ┌────────▼──────────┐
    │ CANAL 1: STREAMLIT │   │ CANAL 2: TELEGRAM │
    │                    │   │                   │
    │ app.py (intacto)   │   │ api.py (nuevo)    │
    │ Puerto 8501        │   │ Puerto 8000       │
    │ ← Usuarios Web     │   │ ← n8n Bot         │
    └────────────────────┘   └───────────────────┘
```

**Ambos canales funcionan simultáneamente sin interferencia.**

#### 🛡️ Garantías de No Impacto:

| Aspecto | Garantía |
|---------|----------|
| **Streamlit actual** | ✅ Sigue funcionando exactamente igual |
| **Tests existentes** | ✅ Siguen pasando sin modificaciones |
| **Deploy actual** | ✅ Compatible (solo agrega API en background) |
| **Credenciales** | ✅ Reutiliza mismas variables de `.env` |
| **Logs** | ✅ Mismo sistema con `logging_utils.py` |
| **Rollback** | ✅ Trivial: eliminar `api.py` y `start.sh` |

#### 🚀 Estrategia de Desarrollo Seguro:

```bash
# FASE 1: Desarrollo local (sin riesgo)
# Terminal 1 - Streamlit sigue funcionando
streamlit run app.py

# Terminal 2 - Nueva API para testing
uvicorn api:app --reload --port 8000

# FASE 2: Deploy en rama separada
git checkout -b feature/telegram-integration
# Agregar: api.py, start.sh
# Modificar: Dockerfile (1 línea), requirements.txt (2 líneas)

# FASE 3: Testing paralelo
# - Streamlit en producción: https://gestordocs-production.up.railway.app/
# - API interna: http://localhost:8000 (solo n8n accede)

# FASE 4: Merge solo si todo OK
# Si hay problema: git revert (instantáneo)
```

#### 📊 Impacto Estimado en Código Base:

| Métrica | Cantidad |
|---------|----------|
| Archivos modificados | 2 (Dockerfile, requirements.txt) |
| Líneas modificadas en código existente | 0 |
| Líneas agregadas en archivos existentes | ~5 |
| Archivos nuevos | 2-3 (api.py, start.sh, docs) |
| Tests a modificar | 0 |
| Riesgo de regresión | **Mínimo** (canales independientes) |

---

## 2. Arquitectura del Sistema

### 2.1 Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                         USUARIO ADMIN                            │
│                    (Telegram @usuario_admin)                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Mensajes de texto / Comandos
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      N8N (VPS Hostinger)                         │
│            https://n8n-n8n.wqzejs.easypanel.host                │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Workflow: Bot Telegram Principal                        │  │
│  │  - Autenticación (whitelist Telegram ID)                │  │
│  │  - Menú interactivo con botones                         │  │
│  │  - Gestión de estado de conversación                    │  │
│  │  - Manejo de errores y reintentos                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                         │                                        │
│                         │ HTTP POST                              │
│                         ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Nodo HTTP Request: Llama a Python Backend              │  │
│  │  - POST /api/autotramite                                │  │
│  │  - POST /api/tag                                        │  │
│  │  - POST /api/mail-cierre                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTP Request/Response
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              PYTHON BACKEND (Railway)                            │
│         https://gestordocs-production.up.railway.app             │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI / Flask API                                     │  │
│  │  - Endpoints REST                                        │  │
│  │  - Validación de tokens                                 │  │
│  │  - Ejecución de lógica existente                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                         │                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Módulos Existentes (reutilizados)                      │  │
│  │  - src/autotramite.py                                   │  │
│  │  - src/models.py                                        │  │
│  │  - src/validators.py                                    │  │
│  │  - src/mail_utils.py                                    │  │
│  │  - src/logging_utils.py                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Decisiones Arquitectónicas

| Aspecto | Decisión | Razón |
|---------|----------|-------|
| **Comunicación n8n-Python** | HTTP REST API (FastAPI) | Estándar, debuggeable, compatible con hosting separado |
| **Estado de conversación** | n8n workflow state (efímero) | Sin DB adicional, suficiente para MVP |
| **Código compartido** | Módulos Python centralizados | Evita duplicación, única fuente de verdad |
| **Credenciales** | `.env` compartido en Railway | Simplifica gestión, mismas credenciales para ambos canales |
| **PDFs** | Filesystem local Railway + descarga inmediata | Consistente con flujo Streamlit actual |
| **Logs** | `logging_utils.py` + correlationID | Trazabilidad completa end-to-end |

---

## 3. Flujo de Usuario (UX Telegram)

### 3.1 Inicio y Autenticación

```
Usuario: /start

Bot: ¡Hola ADMIN! 👋
     Soy el asistente AutoTramite.
     
     ¿Qué operación deseas realizar?
     
     [AutoTramite]  [Habilitación TAG]  [Mail de Cierre]
```

**Validación de acceso**:
- n8n verifica `telegram_user_id` contra whitelist
- Whitelist almacenada en variables de entorno n8n: `ADMIN_TELEGRAM_IDS=123456789,987654321`
- Si ID no autorizado: mensaje ignorado silenciosamente (sin respuesta)

### 3.2 Flujo AutoTramite

```
Usuario: [AutoTramite] (botón)

Bot: 📋 AutoTramite - Registro de Contrato
     
     Envía los datos del contrato en el siguiente formato:
     
     DATOS DEL VEHICULO
     Marca: HYUNDAI
     Patente: DRLZ.16-3
     Modelo: ELANTRA GLS 1.6
     Año: 2012
     ...
     
     (Puedes copiar y pegar desde tu fuente)
     
     Comandos: /cancel para cancelar

Usuario: [Pega texto del contrato]

Bot: ⏳ Validando datos...

Bot: ✅ Datos validados correctamente:
     
     🚗 VEHÍCULO
     • Marca: HYUNDAI
     • Patente: DRLZ16-3
     • Modelo: ELANTRA GLS 1.6
     • Año: 2012
     
     👤 VENDEDOR
     • Nombre: JUAN CARLOS PEREZ GONZALEZ
     • RUT: 12.345.678-9
     • Teléfono: +569 1234 5678
     
     👤 COMPRADOR
     • Nombre: MARIA ANDREA LOPEZ SILVA
     • RUT: 11.222.333-4
     
     ¿Confirmas el registro?
     
     [✅ Confirmar]  [❌ Cancelar]

Usuario: [✅ Confirmar]

Bot: ⏳ Procesando contrato...
     • Conectando a AutoTramite.cl
     
Bot: ⏳ Procesando contrato...
     • Iniciando sesión
     
Bot: ⏳ Procesando contrato...
     • Llenando formulario
     
Bot: ⏳ Procesando contrato...
     • Generando PDF

Bot: ✅ ¡Contrato registrado exitosamente!
     
     📄 PDF: Contrato_DRLZ163_20260206.pdf
     
     [Descargar PDF]
     
     ¿Deseas realizar otra operación?
     [Volver al menú]
```

### 3.3 Flujo Habilitación TAG

```
Usuario: [Habilitación TAG]

Bot: 🏷️ Habilitación TAG - Generar PDF
     
     Envía los datos del propietario:
     
     Nombre: MARIO HUMBERTO VERA VALENCIA
     RUT: 10759120-6
     Dirección: CALLE CHUQUICAMATA 814, LA CALERA
     Teléfono: 977583559
     Correo: mario.vera@ejemplo.cl
     PATENTE: KYTR.55-5
     TAG 147258369
     
     /cancel para cancelar

Usuario: [Pega datos]

Bot: ⏳ Generando PDF TAG...

Bot: ✅ PDF TAG generado exitosamente!
     
     📄 Solicitud-Tag-KYTR555.pdf
     
     [Descargar PDF]
     
     [Volver al menú]
```

### 3.4 Flujo Mail de Cierre

```
Usuario: [Mail de Cierre]

Bot: 📧 Mail de Cierre - Envío de confirmación
     
     Envía los datos en este formato:
     
     DATOS_PROPIETARIO: [texto con datos]
     VEHICULO: Toyota Corolla 2015
     PRECIO: $8.500.000
     FECHA_PAGO: 10-15 de febrero
     EMAIL: cliente@ejemplo.cl
     CC: ventas@queirolo.cl, gerencia@queirolo.cl

Usuario: [Pega datos]

Bot: 📝 Vista previa del email:
     
     ━━━━━━━━━━━━━━━━━━
     Para: cliente@ejemplo.cl
     CC: ventas@queirolo.cl, gerencia@queirolo.cl
     Asunto: Confirmación de Compra - Toyota Corolla 2015
     
     Estimado/a [NOMBRE],
     
     Confirmamos la compra de:
     🚗 Toyota Corolla 2015
     💰 Precio: $8.500.000
     📅 Fecha de pago: 10-15 de febrero
     
     [... resto del mensaje ...]
     ━━━━━━━━━━━━━━━━━━
     
     ¿Enviar este email?
     
     [✅ Enviar]  [✏️ Editar]  [❌ Cancelar]

Usuario: [✅ Enviar]

Bot: ⏳ Enviando email...

Bot: ✅ Email enviado exitosamente!
     
     📧 Destinatarios:
     • cliente@ejemplo.cl
     • ventas@queirolo.cl (CC)
     • gerencia@queirolo.cl (CC)
     
     [Volver al menú]
```

### 3.5 Manejo de Errores

**Validación fallida (ejemplo: RUT inválido)**
```
Bot: ❌ Error de validación:
     
     • RUT inválido: "12.345.678-0" (dígito verificador incorrecto)
     
     Por favor corrige el dato y reenvía.
     
     Intentos restantes: 2/3
     
     /cancel para cancelar
```

**Timeout de inactividad (10 minutos sin respuesta)**
```
Bot: ⏱️ Operación cancelada por inactividad.
     
     Usa /start para comenzar de nuevo.
```

**Error del sistema (AutoTramite.cl no responde)**
```
Bot: ⚠️ Error temporal del sistema.
     
     Reintentando... (2/3)

[Si falla tras 3 intentos]

Bot: ❌ No se pudo completar la operación.
     
     Detalles: Timeout conectando a AutoTramite.cl
     ID de error: TG-20260206-1423-abc123
     
     Por favor intenta más tarde o contacta soporte.
     
     [Volver al menú]
```

### 3.6 Operación Concurrente (bloqueo)

```
Usuario: [AutoTramite] (mientras hay otra operación en curso)

Bot: ⚠️ Tienes una operación en curso:
     
     📋 AutoTramite - Esperando datos
     
     Por favor complétala o cancélala con /cancel
```

---

## 4. Especificación Técnica n8n

### 4.1 Workflow Principal: `Bot_Telegram_Autotramite`

**Nodos del workflow:**

```
[1] Telegram Trigger
    ↓
[2] Whitelist Validation (Function)
    ↓
[3] Command Router (Switch)
    ├─ /start → [4] Menu Principal
    ├─ /cancel → [5] Cancel Handler
    └─ mensaje texto → [6] State Router
                        ↓
[7] Data Validator (Function + HTTP Request a Python)
    ↓
[8] Confirmation Message
    ↓
[9] Await User Confirmation (Webhook Wait)
    ↓
[10] Execute Operation (HTTP Request a Python)
    ↓
[11] Send Result (Telegram + File Upload)
```

### 4.2 Nodo por Nodo

#### [1] Telegram Trigger
```javascript
// Configuración
{
  "updates": ["message", "callback_query"],
  "messageTypes": ["text", "command"]
}
```

#### [2] Whitelist Validation
```javascript
// Function Node
const userId = $json.message.from.id;
const allowedIds = $env.ADMIN_TELEGRAM_IDS.split(',').map(Number);

if (!allowedIds.includes(userId)) {
  // Ignora silenciosamente
  return [];
}

return { json: $json };
```

#### [3] Command Router
```javascript
// Switch Node
const text = $json.message?.text || $json.callback_query?.data;

switch(true) {
  case text === '/start':
    return [0]; // Ruta Menu Principal
  case text === '/cancel':
    return [1]; // Ruta Cancel
  case text?.startsWith('/'): 
    return []; // Ignora comandos desconocidos
  default:
    return [2]; // Ruta procesamiento de datos
}
```

#### [6] State Router
```javascript
// Recupera estado de la conversación (workflow context)
const state = $workflow.state || { step: 'idle' };
const chatId = $json.message.chat.id;

switch(state.step) {
  case 'awaiting_autotramite_data':
    return [0]; // Procesar datos AutoTramite
  case 'awaiting_tag_data':
    return [1]; // Procesar datos TAG
  case 'awaiting_mail_data':
    return [2]; // Procesar datos Mail
  default:
    // No hay operación activa, muestra error
    return [3];
}
```

#### [7] Data Validator
```javascript
// HTTP Request Node
{
  "method": "POST",
  "url": "{{ $env.PYTHON_BACKEND_URL }}/api/validate",
  "authentication": "predefinedCredentialType",
  "nodeCredentialType": "httpHeaderAuth",
  "body": {
    "tipo": "{{ $workflow.state.tipo }}",
    "datos_raw": "{{ $json.message.text }}",
    "correlation_id": "TG-{{ $now.format('YYYYMMDDHHmmss') }}-{{ $json.message.message_id }}"
  },
  "options": {
    "timeout": 30000,
    "retry": {
      "maxRetries": 2,
      "retryInterval": 2000
    }
  }
}
```

**Respuesta esperada de Python:**
```json
{
  "valido": true,
  "datos_parseados": {
    "vehiculo": {...},
    "vendedor": {...},
    "comprador": {...}
  },
  "errores": [],
  "correlation_id": "TG-20260206142300-12345"
}
```

**Si hay errores:**
```json
{
  "valido": false,
  "errores": [
    {
      "campo": "vendedor.rut",
      "mensaje": "RUT inválido: dígito verificador incorrecto"
    }
  ],
  "intentos_restantes": 2,
  "correlation_id": "TG-20260206142300-12345"
}
```

#### [10] Execute Operation
```javascript
// HTTP Request Node - AutoTramite
{
  "method": "POST",
  "url": "{{ $env.PYTHON_BACKEND_URL }}/api/autotramite/ejecutar",
  "authentication": "predefinedCredentialType",
  "body": {
    "datos": "{{ $json.datos_parseados }}",
    "modo": "registro", // o "preview"
    "correlation_id": "{{ $json.correlation_id }}"
  },
  "options": {
    "timeout": 120000, // 2 minutos para Playwright
    "downloadFile": true,
    "downloadFileName": "contrato_{{ $json.datos_parseados.vehiculo.patente }}.pdf"
  }
}
```

**Respuesta esperada:**
```json
{
  "exito": true,
  "pdf_path": "/tmp/Contrato_DRLZ163_20260206.pdf",
  "pdf_url": "https://...", // opcional
  "mensaje": "Contrato registrado exitosamente",
  "correlation_id": "TG-20260206142300-12345",
  "metadata": {
    "patente": "DRLZ163",
    "timestamp": "2026-02-06T14:25:00Z"
  }
}
```

#### [11] Send Result
```javascript
// Telegram Node - Send Document
{
  "chatId": "{{ $json.message.chat.id }}",
  "file": "{{ $binary.data }}",
  "caption": "✅ {{ $('Execute Operation').item.json.mensaje }}\n\n📄 PDF: {{ $('Execute Operation').item.json.metadata.filename }}",
  "replyMarkup": {
    "inline_keyboard": [[
      { "text": "Volver al menú", "callback_data": "/start" }
    ]]
  }
}
```

### 4.3 Gestión de Estado

**Variables de workflow context:**
```javascript
$workflow.state = {
  step: 'awaiting_autotramite_data', // idle | awaiting_* | processing
  tipo: 'autotramite', // autotramite | tag | mail
  intentos: 0,
  max_intentos: 3,
  timestamp_inicio: '2026-02-06T14:20:00Z',
  correlation_id: 'TG-20260206142000-12345',
  datos_temporales: {} // cache temporal de datos parseados
}
```

**Limpieza de estado:**
- Al completar operación exitosamente
- Al ejecutar `/cancel`
- Tras 10 minutos de inactividad (cron n8n)

### 4.4 Manejo de Timeout

**Workflow separado: `Telegram_Timeout_Cleaner`**
```
[Schedule Trigger: cada 5 minutos]
    ↓
[Function: Detecta conversaciones inactivas]
    ↓
[Telegram: Envía mensaje de timeout]
    ↓
[Function: Limpia estado]
```

---

## 5. Especificación Backend Python

### 5.1 Estructura de la API (FastAPI)

**Nuevo archivo: `api.py`**

```python
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from src.models import parsear_texto_contrato
from src.autotramite import crear_contrato_autotramite
from src.validators import validar_rut, validar_patente, validar_email, validar_telefono
from src.logging_utils import setup_logger
from src.mail_utils import enviar_email_smtp

app = FastAPI(title="AutoTramite API", version="1.0.0")
logger = setup_logger(__name__)

# Autenticación simple por token
API_TOKEN = os.getenv("API_TOKEN", "changeme")

def verificar_token(authorization: str = Header(None)):
    if authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="Token inválido")
    return True

# ============================================================================
# ENDPOINTS
# ============================================================================

class ValidarRequest(BaseModel):
    tipo: str  # "autotramite" | "tag" | "mail"
    datos_raw: str
    correlation_id: str

class ValidarResponse(BaseModel):
    valido: bool
    datos_parseados: Optional[Dict[str, Any]] = None
    errores: list[Dict[str, str]] = []
    intentos_restantes: Optional[int] = None
    correlation_id: str

@app.post("/api/validate", response_model=ValidarResponse, dependencies=[Depends(verificar_token)])
async def validar_datos(request: ValidarRequest):
    """Valida y parsea datos de entrada según el tipo de operación."""
    
    logger.info(f"[{request.correlation_id}] Validando datos tipo={request.tipo}")
    
    try:
        if request.tipo == "autotramite":
            # Usa el parser existente
            contrato = parsear_texto_contrato(request.datos_raw)
            
            return ValidarResponse(
                valido=True,
                datos_parseados=contrato.dict(),
                errores=[],
                correlation_id=request.correlation_id
            )
            
        elif request.tipo == "tag":
            # Similar a _tag_parse_text() de app.py
            datos = _parse_tag_telegram(request.datos_raw)
            
            return ValidarResponse(
                valido=True,
                datos_parseados=datos,
                errores=[],
                correlation_id=request.correlation_id
            )
            
        elif request.tipo == "mail":
            datos = _parse_mail_telegram(request.datos_raw)
            
            return ValidarResponse(
                valido=True,
                datos_parseados=datos,
                errores=[],
                correlation_id=request.correlation_id
            )
            
        else:
            raise HTTPException(status_code=400, detail=f"Tipo inválido: {request.tipo}")
    
    except ValueError as e:
        # Errores de validación
        logger.warning(f"[{request.correlation_id}] Validación fallida: {str(e)}")
        
        return ValidarResponse(
            valido=False,
            errores=[{"campo": "general", "mensaje": str(e)}],
            correlation_id=request.correlation_id
        )

# ----------------------------------------------------------------------------

class EjecutarAutoTramiteRequest(BaseModel):
    datos: dict
    modo: str = "registro"  # "registro" | "preview"
    correlation_id: str

class EjecutarResponse(BaseModel):
    exito: bool
    pdf_path: Optional[str] = None
    pdf_url: Optional[str] = None
    mensaje: str
    correlation_id: str
    metadata: Optional[Dict[str, Any]] = None

@app.post("/api/autotramite/ejecutar", response_model=EjecutarResponse, dependencies=[Depends(verificar_token)])
async def ejecutar_autotramite(request: EjecutarAutoTramiteRequest):
    """Ejecuta el flujo AutoTramite (registro o preview)."""
    
    logger.info(f"[{request.correlation_id}] Ejecutando AutoTramite modo={request.modo}")
    
    try:
        from src.models import ContratoData
        
        # Reconstruye el objeto Pydantic
        contrato = ContratoData(**request.datos)
        
        # Ejecuta la automatización
        resultado = crear_contrato_autotramite(
            contrato=contrato,
            registrar=(request.modo == "registro")
        )
        
        if resultado["exito"]:
            return EjecutarResponse(
                exito=True,
                pdf_path=resultado.get("pdf_path"),
                mensaje="Contrato registrado exitosamente" if request.modo == "registro" else "Preview generado",
                correlation_id=request.correlation_id,
                metadata={
                    "patente": contrato.vehiculo.patente,
                    "timestamp": datetime.now().isoformat()
                }
            )
        else:
            return EjecutarResponse(
                exito=False,
                mensaje=resultado.get("error", "Error desconocido"),
                correlation_id=request.correlation_id
            )
    
    except Exception as e:
        logger.error(f"[{request.correlation_id}] Error ejecutando AutoTramite: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------------------------------

@app.post("/api/tag/generar", dependencies=[Depends(verificar_token)])
async def generar_tag(request: dict):
    """Genera PDF de Habilitación TAG."""
    
    correlation_id = request.get("correlation_id", "unknown")
    logger.info(f"[{correlation_id}] Generando PDF TAG")
    
    try:
        # Reutiliza lógica existente de app.py
        pdf_path = _tag_fill_pdf(request["datos"])
        
        return EjecutarResponse(
            exito=True,
            pdf_path=pdf_path,
            mensaje="PDF TAG generado exitosamente",
            correlation_id=correlation_id
        )
    
    except Exception as e:
        logger.error(f"[{correlation_id}] Error generando TAG: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------------------------------

@app.post("/api/mail/enviar", dependencies=[Depends(verificar_token)])
async def enviar_mail(request: dict):
    """Envía email de cierre de negocio."""
    
    correlation_id = request.get("correlation_id", "unknown")
    logger.info(f"[{correlation_id}] Enviando mail de cierre")
    
    try:
        datos = request["datos"]
        
        # Reutiliza lógica existente
        resultado = enviar_email_smtp(
            destinatario=datos["email"],
            cc=datos.get("cc", []),
            vehiculo=datos["vehiculo"],
            precio=datos["precio"],
            fecha_pago=datos["fecha_pago"],
            nombre_propietario=datos["nombre_propietario"]
        )
        
        if resultado["exito"]:
            return EjecutarResponse(
                exito=True,
                mensaje="Email enviado exitosamente",
                correlation_id=correlation_id,
                metadata={"destinatarios": [datos["email"]] + datos.get("cc", [])}
            )
        else:
            raise Exception(resultado.get("error"))
    
    except Exception as e:
        logger.error(f"[{correlation_id}] Error enviando mail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------------------------------

@app.get("/api/download/{filename}", dependencies=[Depends(verificar_token)])
async def download_pdf(filename: str):
    """Descarga un PDF generado."""
    
    # Busca en screenshots/ o docs/tag/output/
    pdf_path = None
    for base_dir in ["screenshots", "docs/tag/output"]:
        candidate = os.path.join(base_dir, filename)
        if os.path.exists(candidate):
            pdf_path = candidate
            break
    
    if not pdf_path:
        raise HTTPException(status_code=404, detail="PDF no encontrado")
    
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=filename
    )

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}
```

### 5.2 Integración con Código Existente

**No hay duplicación**: La API simplemente:
1. Recibe requests HTTP
2. Llama a funciones existentes (`parsear_texto_contrato`, `crear_contrato_autotramite`, etc.)
3. Devuelve respuestas JSON

**Ventajas:**
- ✅ Misma lógica de validación para Streamlit y Telegram
- ✅ Mismos logs con ofuscación PII
- ✅ Mismos reintentos y backoff exponencial
- ✅ Sin código duplicado

### 5.3 Deployment

**Actualización de `requirements.txt`:**
```
# Existentes
streamlit
playwright
pydantic
pypdf
PyYAML
boto3
google-cloud-storage

# Nuevos para API
fastapi
uvicorn[standard]
```

**Actualización de `Dockerfile`:**
```dockerfile
# ... (mantener todo lo existente)

# Exponer puerto API además de Streamlit
EXPOSE 8501 8000

# Script de arranque dual
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
```

**Nuevo archivo `start.sh`:**
```bash
#!/bin/bash

# Arranca API en background
uvicorn api:app --host 0.0.0.0 --port 8000 &

# Arranca Streamlit en foreground
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

**Variables de entorno en Railway:**
- `API_TOKEN`: Token secreto para autenticar requests de n8n
- (Mantener todas las existentes)

### 5.4 Deployment Dual: Streamlit + API en Paralelo

#### Arquitectura de Procesos en Railway

```
Railway Container (puerto público $PORT = 8501)
├── Proceso Principal: Streamlit (foreground)
│   ├── Puerto: $PORT (8501)
│   ├── URL Pública: https://gestordocs-production.up.railway.app/
│   └── Acceso: Usuarios web (navegador)
│
└── Proceso Background: FastAPI
    ├── Puerto: 8000 (interno)
    ├── URL: http://localhost:8000 (solo interno)
    └── Acceso: Solo n8n (via HTTP desde VPS)
```

#### Flujo de Arranque (start.sh)

```bash
#!/bin/bash

# 1. Inicia API en background (&)
echo "🚀 Iniciando FastAPI en puerto 8000..."
uvicorn api:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# 2. Espera a que API esté lista
sleep 2
echo "✅ API iniciada (PID: $API_PID)"

# 3. Inicia Streamlit en foreground (Railway monitorea este proceso)
echo "🚀 Iniciando Streamlit en puerto $PORT..."
streamlit run app.py --server.port $PORT --server.address 0.0.0.0

# Si Streamlit termina, mata el proceso API
kill $API_PID 2>/dev/null
```

#### Verificación Post-Deploy

**1. Verificar Streamlit (público):**
```bash
curl https://gestordocs-production.up.railway.app/_stcore/health
# Esperado: {"status": "ok"}
```

**2. Verificar API (desde Railway logs):**
```bash
# En Railway Dashboard → Logs
# Buscar líneas:
# ✅ API iniciada (PID: ...)
# ✅ Iniciando Streamlit en puerto ...
```

**3. Verificar API desde n8n (VPS):**
```bash
# En n8n Code Node o terminal VPS
curl -H "Authorization: Bearer TU_API_TOKEN" \
     https://gestordocs-production.up.railway.app:8000/health

# ⚠️ NOTA: Railway puede no exponer puerto 8000 externamente
# Solución: n8n debe conectar via URL interna de Railway
```

#### Configuración de Conexión n8n → API

**Opción A: URL Pública (si Railway expone puerto 8000):**
```javascript
// En n8n workflow
$env.PYTHON_BACKEND_URL = "https://gestordocs-production.up.railway.app:8000"
```

**Opción B: URL Interna Railway (recomendada):**
```javascript
// Railway provee variable interna RAILWAY_PRIVATE_DOMAIN
$env.PYTHON_BACKEND_URL = "http://autotramite-api.railway.internal:8000"
```

**Opción C: Proxy via Streamlit (alternativa):**
```python
# En app.py agregar endpoint proxy
@st.cache_resource
def proxy_to_api(endpoint, data):
    import requests
    return requests.post(f"http://localhost:8000{endpoint}", json=data)
```

#### Rollback en Caso de Problemas

**Rollback Instantáneo (sin downtime):**

1. **Revertir Dockerfile:**
```dockerfile
# Cambiar última línea de:
CMD ["/start.sh"]

# A versión original:
CMD ["/bin/sh", "-c", "streamlit run app.py --server.port ${PORT:-8080} --server.address 0.0.0.0"]
```

2. **Railway auto-redeploy:**
```bash
git revert HEAD  # Si ya hiciste commit
git push origin main
# Railway detecta cambio y redeploya versión anterior
```

**Resultado:** Streamlit vuelve a funcionar en <2 minutos sin API.

#### Testing Local del Deployment Dual

**Simular Railway localmente:**
```bash
# Terminal 1 - Simula start.sh
chmod +x start.sh
PORT=8501 ./start.sh

# Terminal 2 - Verifica Streamlit
curl http://localhost:8501/_stcore/health

# Terminal 3 - Verifica API
curl http://localhost:8000/health

# Terminal 4 - Test endpoint con auth
curl -H "Authorization: Bearer test_token" \
     -H "Content-Type: application/json" \
     -d '{"tipo":"autotramite","datos_raw":"test","correlation_id":"test-123"}' \
     http://localhost:8000/api/validate
```

#### Monitoreo de Ambos Procesos

**Logs en Railway Dashboard:**
```
[Streamlit] 2026-02-06 14:23:00 - You can now view your Streamlit app in your browser.
[FastAPI]   2026-02-06 14:23:02 - INFO: Uvicorn running on http://0.0.0.0:8000
[Streamlit] 2026-02-06 14:25:15 - GET /_stcore/health 200 OK
[FastAPI]   2026-02-06 14:25:30 - INFO: [TG-123] Validando datos tipo=autotramite
```

#### Troubleshooting Deployment Dual

| Síntoma | Causa Probable | Solución |
|---------|----------------|----------|
| Streamlit funciona, API no responde | Puerto 8000 no expuesto externamente | Usar URL interna Railway o proxy |
| Ambos procesos terminan inmediatamente | Error en `start.sh` (permisos) | Verificar `chmod +x start.sh` en Dockerfile |
| API responde 401 en todos los requests | `API_TOKEN` no configurado en Railway | Agregar variable en Railway settings |
| Proceso API mata a Streamlit | API corriendo en foreground | Verificar `&` en línea de uvicorn |

---

## 6. Configuración n8n

### 6.1 Variables de Entorno

En el panel de n8n (VPS Hostinger):

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_TELEGRAM_IDS=123456789,987654321

# Python Backend
PYTHON_BACKEND_URL=https://gestordocs-production.up.railway.app
API_TOKEN=tu_token_secreto_aqui  # Mismo que en Railway

# Timeouts
CONVERSATION_TIMEOUT_MINUTES=10
RETRY_MAX_ATTEMPTS=3
RETRY_BASE_DELAY_MS=2000
```

### 6.2 Credentials

**HTTP Header Auth (para llamadas a Python):**
```
Name: Authorization
Value: Bearer {{ $env.API_TOKEN }}
```

---

## 7. Seguridad y Compliance

### 7.1 Autenticación en Múltiples Capas

```
Usuario Telegram
    ↓
[1] Whitelist de Telegram IDs (n8n)
    ↓
[2] Token Bearer en HTTP Request (n8n → Python)
    ↓
[3] Credenciales AutoTramite.cl (Python .env)
```

### 7.2 Manejo de PII

**En logs:**
- ✅ Reutilizar `logging_utils.py` con ofuscación existente
- ✅ Agregar `correlation_id` en todos los logs

**En mensajes Telegram:**
- ⚠️ Telegram tiene cifrado E2E, pero evitar enviar datos completos innecesariamente
- ✅ Mensajes de confirmación muestran solo campos clave (patente, nombre)
- ✅ No loggear contenido de mensajes en n8n (solo metadata)

**Ejemplo de log seguro:**
```
[TG-20260206142300-12345] Validando datos tipo=autotramite
[TG-20260206142300-12345] RUT vendedor: 12.XXX.XXX-9 (válido)
[TG-20260206142300-12345] Email comprador: m***@ejemplo.cl (válido)
```

### 7.3 Gestión de Tokens

| Token | Almacenamiento | Rotación |
|-------|----------------|----------|
| Telegram Bot Token | Variable entorno n8n (encriptada) | Manual (solo si comprometido) |
| API Token Python | Variables entorno n8n + Railway | Mensual (recomendado) |
| Credenciales AutoTramite | `.env` Railway (encriptado) | Según política empresa |

---

## 8. Observabilidad

### 8.1 Trazabilidad End-to-End

**Correlation ID:**
```
Formato: TG-{timestamp}-{message_id}
Ejemplo: TG-20260206142300-12345

Aparece en:
1. Mensaje inicial de Telegram (metadata)
2. Request n8n → Python (body.correlation_id)
3. Logs Python (todas las líneas)
4. Nombre de archivo PDF (opcional)
5. Historial de emails (metadata)
```

### 8.2 Logs Centralizados

**Python (Railway):**
```python
# En cada endpoint
logger.info(f"[{correlation_id}] Operación iniciada", extra={
    "correlation_id": correlation_id,
    "tipo": "autotramite",
    "telegram_user_id": "***",  # ofuscado
    "timestamp": datetime.now().isoformat()
})
```

**n8n:**
- Ejecuciones visibles en UI de n8n
- Cada ejecución muestra:
  - Input/output de cada nodo
  - Tiempos de ejecución
  - Errores capturados

**Acceso:**
- n8n logs: https://n8n-n8n.wqzejs.easypanel.host/executions
- Python logs: Railway dashboard → Logs

### 8.3 Métricas Simples

**Manual (vía n8n UI):**
- Total de mensajes procesados (cuenta de ejecuciones)
- Tasa de éxito/fallo por flujo
- Tiempo promedio de respuesta

**Futuro (opcional):**
- Webhook a servicio de métricas (Prometheus, Datadog)
- Dashboard Grafana

---

## 9. Testing

### 9.1 Test Plan

| Fase | Qué testear | Herramienta |
|------|-------------|-------------|
| **1. Unit Tests** | Validadores, parsers | `pytest tests/` |
| **2. API Tests** | Endpoints FastAPI | `pytest` + `requests` |
| **3. n8n Integration** | Workflow completo en n8n | Manual en n8n UI |
| **4. E2E Telegram** | Flujo real con bot | Manual desde Telegram |

### 9.2 Casos de Test Prioritarios

**AutoTramite:**
- ✅ Datos válidos → Registro exitoso
- ✅ RUT inválido → Error específico
- ✅ Timeout AutoTramite.cl → Reintento automático
- ✅ /cancel durante procesamiento → Limpia estado

**TAG:**
- ✅ Datos completos → PDF generado
- ✅ Patente vintage → Formato correcto

**Mail:**
- ✅ Email con CC → Todos reciben
- ✅ Email inválido → Validación previa
- ✅ Vista previa → Usuario puede editar

**General:**
- ✅ Usuario no autorizado → Ignorado silenciosamente
- ✅ Operación concurrente → Rechazo con mensaje claro
- ✅ Timeout inactividad → Limpieza automática

### 9.3 Test de Carga (opcional)

```bash
# Simular 10 usuarios concurrentes
# (No prioritario para MVP - un proceso a la vez por diseño)
```

---

## 10. Plan de Implementación

### 10.1 Fases

**FASE 1: Backend API (Railway)** ✅ COMPLETADA (2026-02-06)
- [ ] Crear `api.py` con endpoints básicos → `api.py` (raíz)
- [ ] Endpoint `/api/validate` (reutiliza parsers) → soporta tipos: autotramite, tag, mail
- [ ] Endpoint `/api/autotramite/ejecutar` → llama a `crear_contrato_autotramite()` via async
- [ ] Endpoint `/api/tag/generar` → parsea texto + genera PDF con `_tag_fill_pdf()`
- [ ] Endpoint `/api/mail/enviar` → valida SMTP, genera email desde plantilla, envía con CC
- [ ] Endpoint `/api/download/{filename}` → busca en screenshots/ y docs/tag/output/
- [ ] Actualizar `Dockerfile` y `start.sh` → `start.sh` (raíz), Dockerfile actualizado con CMD dual
- [ ] Deploy a Railway y verificar health check *(pendiente: requiere push a Railway)*
- [ ] Test con `curl` o Postman → health 200, auth 401, validate 200 verificados localmente

> **Evidencia**: `api.py` compila OK, 6 endpoints registrados, auth Bearer funcional, health check OK en localhost:8000. Archivos creados: `api.py`, `start.sh`. Archivos modificados: `Dockerfile` (+4 líneas), `requirements.txt` (+3 líneas: fastapi, uvicorn).

**FASE 2: Workflow n8n Base** ✅ COMPLETADA (2026-02-07)
- [x] ✅ Crear workflow `Bot_Telegram_Autotramite`
- [x] ✅ Configurar Telegram Trigger
- [x] ✅ Implementar whitelist validation
- [x] ✅ Menú principal con botones
- [x] ✅ Comando `/start` y `/cancel`
- [x] ✅ Test de chat básico (sin ejecutar Python aún)

> **Evidencia**: Workflow `Bot_Telegram_Autotramite` creado e importado en n8n (ID: IaK6J5CKBTkLoHTj) desde `docs/n8n/Bot_Telegram_Autotramite.json` usando `workflow_manager.js create`. Nodos: Telegram Trigger, Whitelist Validation, Menu Principal, AutoTramite Instructions, Parse Datos, Resumen y Confirmacion, Confirmo?, Procesando, Resultado Placeholder, Command /cancel?.
- Prueba rapida: /start -> menu -> AutoTramite -> enviar datos -> resumen -> "confirmo" -> "Procesando..." -> "Listo para ejecutar".

**FASE 3: Integración AutoTramite** ⏱️ 4-5 horas — **NEXT**
- [ ] Flujo completo AutoTramite en n8n
- [ ] Validación de datos (HTTP → Python)
- [ ] Confirmación con botones
- [ ] Ejecución (HTTP → Python + Playwright)
- [ ] Envío de PDF al usuario
- [ ] Manejo de errores y reintentos
- [ ] Test E2E desde Telegram


**FASE 4: TAG y Mail** ⏱️ 3-4 horas
- [ ] Duplicar flujo para TAG (más simple, sin Playwright)
- [ ] Duplicar flujo para Mail (sin PDF, solo confirmación)
- [ ] Test E2E de ambos flujos

**FASE 5: Robustez y Observabilidad** ⏱️ 2-3 horas
- [ ] Workflow de timeout cleaner
- [ ] Manejo de operación concurrente
- [ ] Logs con correlation_id en todos los puntos
- [ ] Documentación final
- [ ] Test de carga ligero

**FASE 6: Producción** ⏱️ 1-2 horas
- [ ] Credenciales reales en n8n
- [ ] Telegram Bot Token de producción
- [ ] Whitelist de usuarios reales
- [ ] Deploy final y smoke test
- [ ] Capacitación a usuario ADMIN

**TOTAL ESTIMADO: 17-24 horas**

### 10.2 Rollback Plan

Si hay problemas críticos:
1. **n8n**: Desactivar workflow (pausa en UI)
2. **Python**: Revertir deploy en Railway a versión anterior
3. **Telegram**: Deshabilitar bot (vía BotFather)

**Streamlit sigue funcionando** independientemente (canal primario no afectado).

---

## 11. Limitaciones Conocidas

### 11.1 Concurrencia

**Limitación Playwright:**
- Solo 1 proceso AutoTramite a la vez (mismo usuario/credenciales)
- **Solución aplicada**: Bloqueo a nivel workflow (estado `processing`)

### 11.2 Tamaño de Mensajes

**Límite Telegram:**
- Texto: 4096 caracteres por mensaje
- Archivos: 50 MB
- **Solución**: Si datos > 4096 chars, rechazar con mensaje de error

### 11.3 Filesystem Efímero (Railway)

- PDFs se borran en cada deploy
- **Solución**: Descarga inmediata por usuario o storage externo (S3/GCS)

### 11.4 Timeout Playwright

- AutoTramite.cl puede tardar 30-60 segundos
- Telegram tiene timeout de 60 segundos para respuestas
- **Solución**: Mensajes de progreso cada 10 segundos

---

## 12. Roadmap Futuro

### Mejoras Post-MVP

**UX:**
- [ ] Edición inline de campos (sin reenviar todo)
- [ ] Historial de operaciones por usuario
- [ ] Notificaciones proactivas (ej: "tu contrato fue procesado")

**Técnico:**
- [ ] Queue system (Bull/Redis) para procesar múltiples requests
- [ ] Webhooks de AutoTramite.cl (si API lo soporta)
- [ ] Storage permanente de PDFs (S3/GCS por defecto)
- [ ] Multi-tenant (múltiples empresas/credenciales)

**Observabilidad:**
- [ ] Dashboard de métricas (Grafana)
- [ ] Alertas automáticas (fallos consecutivos)
- [ ] Reportes semanales automatizados

---

## 13. Referencias

### Documentación Técnica

| Recurso | URL |
|---------|-----|
| Telegram Bot API | https://core.telegram.org/bots/api |
| n8n Telegram Node | https://docs.n8n.io/integrations/builtin/trigger-nodes/n8n-nodes-base.telegramtrigger/ |
| FastAPI Docs | https://fastapi.tiangolo.com/ |
| Playwright Python | https://playwright.dev/python/ |

### Archivos del Proyecto

| Archivo | Descripción |
|---------|-------------|
| `README.md` | Documentación general del proyecto |
| `docs/autotramite/README.md` | Detalle del flujo AutoTramite |
| `docs/tag/tag-pdf-autofill-implementation-guide.md` | Implementación TAG |
| `docs/correo-cierre/mail-de-cierre-implementation-guide.md` | Implementación Mail |
| `src/models.py` | Modelos Pydantic y parsers |
| `src/validators.py` | Validadores chilenos |
| `src/logging_utils.py` | Logging con ofuscación PII |

---

## 14. Decisiones de Diseño - Justificación

### ¿Por qué FastAPI y no Flask?

- **Async nativo**: Mejor para I/O intensivo (Playwright, SMTP)
- **Validación automática**: Pydantic integrado (ya lo usamos)
- **Documentación auto-generada**: Swagger UI gratis
- **Tipo hints**: Mejor DX y detección de errores

### ¿Por qué no ejecutar Python directo desde n8n?

**Opción descartada**: `Execute Command` node con script Python

**Problemas:**
- Requiere instalar Playwright en servidor n8n
- Difícil debuggear
- No reutiliza código de Railway
- Credenciales duplicadas

**Solución elegida**: HTTP API

**Ventajas:**
- ✅ Separación de concerns
- ✅ Mismo código para Streamlit y Telegram
- ✅ Fácil testear (endpoints REST)
- ✅ Hosting independiente (n8n puede caer, Python sigue)

### ¿Por qué no DB para estado de conversación?

**MVP no justifica complejidad:**
- Solo 1 usuario activo a la vez (ADMIN)
- Timeout de 10 minutos es aceptable
- Estado efímero suficiente

**Futuro**: Si múltiples usuarios concurrentes → Redis/PostgreSQL

---

## 15. Checklist Pre-Producción

### Backend (Railway)

- [ ] `.env` con todas las variables configuradas
- [ ] `API_TOKEN` generado (mínimo 32 caracteres aleatorios)
- [ ] Health check respondiendo: `curl https://gestordocs-production.up.railway.app/health`
- [ ] Endpoints testeados con Postman/curl
- [ ] Logs configurados en nivel INFO
- [ ] CORS deshabilitado (solo acepta requests de n8n)

### n8n (VPS Hostinger)

- [ ] Telegram Bot Token de producción configurado
- [ ] `ADMIN_TELEGRAM_IDS` con IDs reales
- [ ] `PYTHON_BACKEND_URL` apuntando a Railway
- [ ] `API_TOKEN` coincide con Railway
- [ ] Workflow pausado durante configuración
- [ ] Test de ejecución manual exitoso

### Telegram

- [ ] Bot creado vía BotFather
- [ ] Comandos configurados: `/start`, `/cancel`
- [ ] Bot iniciado (no pausado)
- [ ] Telegram IDs de admins verificados (enviar mensaje a @userinfobot)

### Seguridad

- [ ] API Token no expuesto en código (solo en variables entorno)
- [ ] `.env` en `.gitignore`
- [ ] Logs sin PII (verificar ofuscación)
- [ ] Railway sin acceso público a puerto 8000 (solo Streamlit en $PORT)

### Testing

- [ ] Test E2E de AutoTramite (con datos de `docs/autotramite/test.md`)
- [ ] Test E2E de TAG
- [ ] Test E2E de Mail
- [ ] Test de `/cancel` interrumpiendo operación
- [ ] Test de timeout de inactividad
- [ ] Test de usuario no autorizado (debe ignorar)
- [ ] Test de error de validación (ej: RUT inválido)

---

## 16. Soporte y Troubleshooting

### Logs en Tiempo Real

**Python (Railway):**
```bash
# En Railway Dashboard → Logs (live tail)
# Filtrar por correlation_id:
[TG-20260206142300-12345]
```

**n8n:**
```
# En n8n UI → Executions
# Click en ejecución → Ver detalle de cada nodo
```

### Comandos de Debug

**Test API desde n8n:**
```bash
# En n8n Code Node
const response = await $http.request({
  method: 'POST',
  url: $env.PYTHON_BACKEND_URL + '/health',
  headers: {
    'Authorization': 'Bearer ' + $env.API_TOKEN
  }
});
return [{ json: response }];
```

**Test bot localmente:**
```bash
# Instalar CLI de Telegram
npm install -g telegram-bot-cli

# Enviar mensaje de prueba
telegram-bot-cli send --token "TU_BOT_TOKEN" --chat "TU_CHAT_ID" --message "/start"
```

### Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `401 Unauthorized` (n8n → Python) | Token inválido | Verificar `API_TOKEN` coincide en ambos lados |
| `Telegram webhook failed` | n8n no responde en 60s | Reducir timeout Playwright o enviar mensajes de progreso |
| `Session already connected` (Playwright) | Proceso anterior no terminó | Reiniciar servicio Railway, verificar cleanup |
| `pdf_path not found` | PDF no se guardó | Verificar permisos de filesystem, revisar logs Playwright |

---

**FIN DEL DOCUMENTO**

Versión: 1.0  
Fecha: 6 de febrero de 2026  
Autor: Basado en cuestionario respondido y arquitectura AutoTramite MVP  
Mantenedor: Equipo Queirolo Dev
