# Plan de Migración: n8n Workflow → Python MVP

**Fecha:** 04 Febrero 2026  
**Objetivo:** Refactorizar el workflow n8n a un proyecto Python standalone manteniendo la misma funcionalidad y practicidad

---

## 1. Correspondencia n8n → Python

### 1.1 Flujo General

| n8n Node | Python Equivalent | Responsabilidad |
|----------|-------------------|-----------------|
| **Form Trigger** | `app.py` (Streamlit) | Interfaz de usuario, captura de datos |
| **Parsear Texto Contrato** | `src/models.py` + métodos de parsing | Extracción de datos del texto CAV + Nota Venta |
| **Validar Datos** | `src/validators.py` | Validación RUT, patente, email, teléfono |
| **Validacion OK?** | Lógica en `app.py` | Control de flujo basado en validación |
| **Preparar Datos Playwright** | `src/models.py` (Pydantic serialization) | Mapeo de datos a estructura AutoTramite |
| **Browserless Cloud** | `src/autotramite.py` (Playwright local) | Automatización browser |
| **Procesar Resultado Playwright** | Return value de `autotramite.py` | Extracción de resultados |
| **Operacion Exitosa?** | Manejo de excepciones + try/except | Control de éxito/error |
| **Responder Exito/Error** | Streamlit UI states (success/error boxes) | Mostrar resultado al usuario |

### 1.2 Datos de Entrada

**n8n Form Field:** Textarea con texto estructurado (CAV + Nota Venta)

**Python Streamlit:** 
- `st.text_area()` para capturar el mismo texto estructurado
- Placeholder con ejemplo idéntico al n8n

### 1.3 Validaciones

**n8n Code Node (JavaScript):**
```javascript
// Validar RUT con módulo 11
function validarRUT(rut) { ... }
// Validar teléfono 8-9 dígitos
const telRegex = /^[0-9]{8,9}$/;
// Validar patente formato
const patenteRegex = /^[A-Z]{2,4}[0-9]{2,4}$/;
```

**Python validators.py:**
```python
def validar_rut(rut: str) -> bool:
    """Validación módulo 11 RUT chileno"""
    
def validar_telefono(telefono: str) -> bool:
    """Validación 8-9 dígitos"""
    
def validar_patente(patente: str, dv: str) -> bool:
    """Validación formato XXNN o NNXX + DV"""
```

### 1.4 Automatización Browser

**n8n:** Browserless Cloud API (POST request con código Playwright incrustado)

**Python:** Playwright local ejecutando el mismo flujo:
1. Login a AutoTramite
2. Navegación a formulario
3. Llenado de campos
4. Previsualización PDF
5. Registro (con opción dry-run)

**Ventajas de Playwright local:**
- Sin dependencia de servicio externo
- Debugging más fácil
- Sin costo por ejecución
- Control total del browser

---

## 2. Decisiones Técnicas

### 2.1 Por qué Playwright (vs Selenium/Requests)

| Criterio | Playwright | Selenium | Requests |
|----------|-----------|----------|----------|
| **Async/Await nativo** | ✅ Si | ❌ No | ✅ Si |
| **Auto-waiting** | ✅ Si | ❌ Manual | N/A |
| **Network interception** | ✅ Si | ⚠️ Limitado | ❌ No |
| **Headless por defecto** | ✅ Si | ⚠️ Requiere config | N/A |
| **Manejo de timeouts** | ✅ Inteligente | ❌ Manual | ❌ Manual |
| **SPAs modernas** | ✅ Excelente | ⚠️ Bueno | ❌ No funciona |
| **Debugging** | ✅ `--headed` + DevTools | ⚠️ Más complejo | N/A |

**Decisión:** Playwright es superior para automatización de SPAs con JavaScript dinámico.

**Alternativa Requests descartada:** AutoTramite tiene:
- CSRF tokens dinámicos
- Validación JavaScript client-side
- Redirects complejos
- Sesiones con cookies múltiples

### 2.2 Por qué Streamlit (vs FastAPI/Flask + HTML)

| Criterio | Streamlit | FastAPI + HTML | Flask + HTML |
|----------|-----------|----------------|--------------|
| **Rapidez desarrollo** | ✅ 10 líneas | ❌ 100+ líneas | ❌ 80+ líneas |
| **UI por defecto** | ✅ Profesional | ❌ Requiere CSS | ❌ Requiere CSS |
| **Estados interactivos** | ✅ `st.session_state` | ❌ Manual | ❌ Manual |
| **Loading spinners** | ✅ `st.spinner()` | ❌ Manual | ❌ Manual |
| **Re-run automático** | ✅ Si | ❌ Manual | ❌ Manual |
| **Deploy simple** | ✅ Streamlit Cloud gratis | ⚠️ Requiere servidor | ⚠️ Requiere servidor |

**Decisión:** Streamlit maximiza productividad para MVP sin sacrificar UX.

**Requisitos del usuario:**
> "form + ejecución + resultado, mantener practicidad de uso"

Streamlit cumple exactamente este requisito con mínimo código.

### 2.3 Pydantic para Modelos de Datos

**Por qué Pydantic:**
- Validación automática de tipos
- Serialización JSON trivial (`.dict()`, `.json()`)
- Documentación auto-generada con tipos
- Integración nativa con FastAPI (si escalamos después)
- Validadores custom para RUT/patente

**Estructura de Modelos:**
```python
class DatosVehiculo(BaseModel):
    patente: str
    patente_dv: str
    marca: str
    modelo: str
    ano: int
    # ...

class DatosPersona(BaseModel):
    rut: str
    nombres: str
    apellido_paterno: str
    apellido_materno: Optional[str] = ' '
    # ...

class ContratoInput(BaseModel):
    texto_raw: str  # Texto ingresado por usuario
    
class ContratoParsed(BaseModel):
    vehiculo: DatosVehiculo
    vendedor: DatosPersona
    comprador: DatosPersona
    tasacion: Optional[int]
    valor_venta: int

class ContratoResult(BaseModel):
    success: bool
    operacion_id: Optional[str]
    pdf_url: Optional[str]
    mensaje: str
    error: Optional[str]
```

---

## 3. Mapeo de Reglas de Negocio

### 3.1 Parsing de Texto (Sección 0.1 del Plan)

**Reglas implementadas en `src/models.py`:**

| Regla | n8n (JS) | Python |
|-------|----------|--------|
| **Separar patente + DV** | `split('-')` | `split('-')` |
| **Separar nombres** | Últimas 2 palabras = apellidos | Mismo algoritmo |
| **Separar dirección** | Split por `,` luego `.` | Mismo algoritmo |
| **Normalizar RUT** | Agregar puntos de miles | `formatear_rut()` |
| **Limpiar patente** | Quitar puntos internos | `re.sub()` |
| **Valores monetarios** | Quitar puntos | `str.replace('.', '')` |

### 3.2 Selectores Playwright (Sección 5.2 del Plan)

**100% de los selectores validados se mantienen idénticos:**

```python
# Vehiculo
await page.fill('#patenter', datos.patente)
await page.fill('#DvPatente', datos.patente_dv)
await page.fill('#marca', datos.marca)
# ... (idénticos a n8n)

# Vendedor
await page.fill('#rutv', datos.vendedor_rut)
# ...

# Comprador
await page.fill('#rutc', datos.comprador_rut)
# ...
```

**Estrategia de waits (Sección 5.3):**
```python
TIMEOUTS = {
    'navigation': 30000,
    'element': 10000,
    'animation': 500
}

await page.wait_for_selector('#campo', state='visible', timeout=TIMEOUTS['element'])
await page.wait_for_load_state('networkidle', timeout=TIMEOUTS['navigation'])
```

### 3.3 Manejo de Errores (Sección 7)

**Reintentos con exponential backoff:**

```python
async def ejecutar_con_reintentos(
    fn: Callable,
    max_intentos: int = 3,
    delay_base: int = 2000
) -> Any:
    for intento in range(1, max_intentos + 1):
        try:
            return await fn()
        except RecoverableError as e:
            if intento < max_intentos:
                delay = delay_base * (2 ** (intento - 1))
                await asyncio.sleep(delay / 1000)
            else:
                raise
        except UnrecoverableError:
            raise  # No reintentar
```

**Clasificación de errores:**
- `RecoverableError`: Timeout, red inestable → Reintentar
- `UnrecoverableError`: Login fallido, CAPTCHA → Detener
- `ValidationError`: Datos inválidos → Mostrar errores

---

## 4. Logging Seguro (Sección 7.4)

**Datos sensibles a ofuscar:**
- Credenciales (NUNCA loguear)
- RUTs completos (solo primeros 4 dígitos)
- Teléfonos completos (solo primeros 3 dígitos)
- Emails completos (solo dominio)

**Implementación:**
```python
def ofuscar_rut(rut: str) -> str:
    return rut[:4] + '****' if len(rut) > 4 else '****'

logger.info(f"Operación exitosa", extra={
    'patente': datos.patente,
    'vendedor_rut': ofuscar_rut(datos.vendedor_rut),
    'operacion_id': result.operacion_id
})
```

---

## 5. Flujo de Ejecución Completo

### Estado: IDLE
```
┌─────────────────────────────┐
│  Streamlit UI               │
│  - Text area (vacía)        │
│  - Botón "Registrar"        │
│  - Checkbox "Dry-run"       │
└─────────────────────────────┘
```

### Estado: RUNNING
```
Usuario pega texto → Click "Registrar"
         ↓
1. Parsear texto (regex + splits)
         ↓
2. Validar datos (RUT/patente/email/tel)
         ↓
   ┌──── Validación FAIL? ───→ Mostrar errores (IDLE)
   └──── Validación OK
         ↓
3. Crear modelos Pydantic
         ↓
4. Playwright: Login + Llenar form + Submit
         ↓
   ┌──── Playwright FAIL? ───→ Mostrar error (IDLE)
   └──── Playwright OK
         ↓
5. Extraer resultado (ID operación + PDF URL)
         ↓
SUCCESS (mostrar confirmación)
```

### Estado: SUCCESS
```
┌─────────────────────────────┐
│  ✅ CONTRATO REGISTRADO     │
│                             │
│  Patente: DRLZ16-3          │
│  Vehículo: HYUNDAI ELANTRA  │
│  ID Operación: 123456       │
│  PDF: [link]                │
│                             │
│  [Registrar Otro]           │
└─────────────────────────────┘
```

### Estado: ERROR
```
┌─────────────────────────────┐
│  ❌ ERROR                   │
│                             │
│  • RUT vendedor inválido    │
│  • Teléfono muy corto       │
│                             │
│  [Corregir]                 │
└─────────────────────────────┘
```

---

## 6. Modo Dry-Run

**Requisito del usuario:**
> "No ejecutar automatización real si requiere credenciales; permitir modo 'dry-run'"

**Implementación:**
```python
if dry_run:
    # Solo validación + preparación
    datos_parsed = parsear_texto(texto)
    errores = validar_datos(datos_parsed)
    if not errores:
        st.success("Validación OK. Datos listos para enviar:")
        st.json(datos_parsed.dict())
else:
    # Validación + Playwright completo
    resultado = await ejecutar_autotramite(datos_parsed)
    st.success(f"Operación ID: {resultado.operacion_id}")
```

---

## 7. Testing

### tests/test_validators.py

```python
def test_validar_rut_valido():
    assert validar_rut('26.002.284-9') == True

def test_validar_rut_invalido():
    assert validar_rut('26.002.284-0') == False

def test_validar_patente_formato_viejo():
    assert validar_patente('DRLZ16', '3') == True

def test_validar_patente_formato_nuevo():
    assert validar_patente('BBBB22', 'K') == True

def test_separar_nombre_completo():
    result = separarNombre('DENNYS EDUARDO PARRA GRANADILLO')
    assert result == {
        'nombres': 'DENNYS EDUARDO',
        'apellido_paterno': 'PARRA',
        'apellido_materno': 'GRANADILLO'
    }
```

---

## 8. Estructura de Archivos Creados

```
autotramite_py_mvp/
├── README.md                     # Instrucciones de instalación/uso
├── requirements.txt              # Dependencias Python
├── .env.example                  # Template para variables de entorno
├── app.py                        # Streamlit UI (entry point)
├── src/
│   ├── __init__.py
│   ├── config.py                 # Settings + env vars
│   ├── models.py                 # Pydantic models + parsing
│   ├── validators.py             # RUT/patente/email/tel validation
│   ├── autotramite.py            # Playwright automation
│   └── logging_utils.py          # Secure logging
└── tests/
    ├── __init__.py
    └── test_validators.py        # Unit tests
```

---

## 9. Ventajas de la Migración

### n8n Workflow
| Ventaja | Desventaja |
|---------|------------|
| ✅ UI visual | ❌ Difícil de versionar (JSON) |
| ✅ Sin infraestructura | ❌ Vendor lock-in (Browserless API) |
| ✅ Rápido prototipo | ❌ Debugging complejo |
|  | ❌ Testing limitado |
|  | ❌ No reutilizable como librería |

### Python Standalone
| Ventaja | Desventaja |
|---------|------------|
| ✅ Versionado Git friendly | ⚠️ Requiere Python runtime |
| ✅ Debugging con IDE | ⚠️ Infraestructura manual |
| ✅ Testing con pytest | |
| ✅ Reusable (CLI, API, Streamlit) | |
| ✅ Sin dependencias cloud | |
| ✅ Type safety (Pydantic) | |

---

## 10. Próximos Pasos Post-Migración

### Mejoras Potenciales (Fuera de MVP)
- [ ] Agregar base de datos SQLite para auditoría local
- [ ] CLI alternativo (`python -m autotramite_py_mvp --file datos.txt`)
- [ ] API REST con FastAPI (reutilizar `src/`)
- [ ] Upload PDF CAV para parsing automático (OCR)
- [ ] Multi-threading para procesar múltiples contratos
- [ ] Docker image para deployment

### Escalabilidad
- [ ] Cola Redis para operaciones asíncronas
- [ ] Monitoreo con Sentry
- [ ] Métricas con Prometheus
- [ ] Deploy en Cloud Run / Fargate

---

**Migración completada:** 04 Febrero 2026  
**Autor:** Refactorización automática n8n → Python  
**Aprobado para producción:** Pendiente testing
