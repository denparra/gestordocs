# AutoTramite Python MVP 📄

Automatización de contratos de compraventa en [AutoTramite.cl](https://autotramite.cl) usando Python + Playwright + Streamlit.

**Versión:** 1.0.0  
**Fecha:** 04 Febrero 2026  
**Migrado de:** n8n workflow (autotramite-compraventa-mvp.json)

---

## 🎯 Características

- ✅ Parseo automático de texto estructurado (CAV + Nota de Venta)
- ✅ Validación robusta de RUT, patente, email, teléfono
- ✅ Automatización browser con Playwright (login + formulario + registro)
- ✅ Interfaz simple con Streamlit (form + ejecución + resultado)
- ✅ Modo Dry-Run (validación sin registro)
- ✅ Logging seguro (ofuscación de datos sensibles)
- ✅ Reintentos automáticos con exponential backoff
- ✅ Tests unitarios con pytest

---

## 📋 Requisitos Previos

- **Python:** 3.10 o superior
- **Sistema operativo:** Windows, macOS, Linux
- **Credenciales:** Email y contraseña de AutoTramite.cl

---

## 🚀 Instalación

### 1. Clonar/Navegar al Proyecto

```bash
cd projects/gestordocs/autotramite_py_mvp
```

### 2. Crear Entorno Virtual

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Instalar Navegadores de Playwright

```bash
playwright install chromium
```

### 5. Configurar Variables de Entorno

```bash
# Copiar template
cp .env.example .env

# Editar .env con tus credenciales
# Windows: notepad .env
# macOS/Linux: nano .env
```

**Contenido mínimo de `.env`:**

```env
AUTOTRAMITE_EMAIL=tu_email@queirolo.cl
AUTOTRAMITE_PASSWORD=tu_contraseña
```

**⚠️ IMPORTANTE:** 
- NO commitear el archivo `.env` con credenciales reales
- El `.env` ya está en `.gitignore` (si existe)

---

## 💻 Uso

### Ejecutar Aplicación Streamlit

```bash
streamlit run app.py
```

La aplicación se abrirá en tu navegador en: `http://localhost:8501`

### Flujo de Uso

1. **Pegar Datos:** Copiar y pegar el texto del CAV + Nota de Venta en el textarea
2. **Validar:** Click en "Registrar Contrato" para parsear y validar
3. **Revisar:** Ver el resumen de datos parseados
4. **Ejecutar:** Confirmar y ejecutar el registro en AutoTramite
5. **Resultado:** Ver ID de operación y link al PDF (si disponible)

### Ejemplo de Texto de Entrada

```
Inscripción : DRLZ.16-3
DATOS DEL VEHICULO
Tipo Vehículo : AUTOMOVIL Año : 2012
Marca : HYUNDAI
Modelo : ELANTRA GLS 1.6
Nro. Motor : G4FGBU380448
Nro. Chasis : KMHDH41CACU327103
Color : ROJO

DATOS DEL VENDEDOR
Nombre : DENNYS EDUARDO PARRA GRANADILLO
R.U.N. : 26002284-5
DIRECCION: AV. LAS CONDES 12461, LAS CONDES. SANTIAGO
Telefono: 975400946
Correo: dparra@queirolo.cl

TASACION 10.000.000
VENTA 10.000.000

DATOS COMPRADOR
Nombre: CAROLINA CECILIA CALLES CALLES
RUT: 26033082-5
Direccion: SERRANO, 266. SANTIAGO CENTRO. SANTIAGO
Telefono: 975400946
Correo: comprador@ejemplo.cl
```

### Modo Dry-Run

Para solo validar datos sin registrar en AutoTramite:

1. Marcar checkbox "Modo Dry-Run (solo validar)"
2. Ejecutar normalmente

Nota: En la vista previa hay un bot?n de descarga PDF (ver `screenshots/ejemplo.png`).

Esto es útil para:
- Probar parsing sin credenciales
- Validar formato de datos
- Testing local

---

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Con verbose
pytest -v

# Solo tests de validadores
pytest tests/test_validators.py -v

# Con coverage
pytest --cov=src tests/
```

### Tests Incluidos

- ✅ Validación de RUT chileno (módulo 11)
- ✅ Formateo de RUT
- ✅ Validación de patente (formatos antiguo/nuevo)
- ✅ Validación de email
- ✅ Validación de teléfono (8-9 dígitos)
- ✅ Separación de nombres completos
- ✅ Separación de direcciones

---

## 📁 Estructura del Proyecto

```
autotramite_py_mvp/
├── app.py                     # Streamlit UI (entry point)
├── requirements.txt           # Dependencias Python
├── .env.example               # Template de configuración
├── README.md                  # Este archivo
├── MIGRATION_PLAN.md          # Plan de migración n8n→Python
│
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuración + selectores validados
│   ├── models.py              # Pydantic models + parsing
│   ├── validators.py          # Validaciones (RUT/patente/email/tel)
│   ├── autotramite.py         # Playwright automation
│   └── logging_utils.py       # Logging seguro (ofuscación PII)
│
└── tests/
    ├── __init__.py
    └── test_validators.py     # Tests unitarios
```

---

## 🔧 Configuración Avanzada

### Variables de Entorno (Opcionales)

```env
# Logging
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=autotramite.log       # Path del archivo de logs

# Playwright
PLAYWRIGHT_HEADLESS=True       # False para ver el browser
PLAYWRIGHT_SLOW_MO=0           # Delay entre acciones (ms)

# Timeouts (milisegundos)
TIMEOUT_NAVIGATION=30000       # Carga de páginas
TIMEOUT_ELEMENT=10000          # Espera de elementos
TIMEOUT_ANIMATION=500          # Animaciones UI

# Reintentos
MAX_REINTENTOS=3               # Intentos en caso de error
DELAY_BASE_MS=2000             # Base para exponential backoff
```

### Debugging

Para ver el browser ejecutándose:

```env
# En .env
PLAYWRIGHT_HEADLESS=False
PLAYWRIGHT_SLOW_MO=1000
```

---

## 🛡️ Seguridad

### Datos Ofuscados en Logs

Los siguientes datos se ofuscan automáticamente:

- ✅ RUTs completos → `26.0****`
- ✅ Teléfonos → `912****`
- ✅ Emails → `****@dominio.cl`
- ✅ Contraseñas → `***REDACTED***`

### Recomendaciones

- ❌ NO commitear el archivo `.env` con credenciales reales
- ❌ NO compartir logs completos (pueden contener datos sensibles)
- ✅ Usar variables de entorno para credenciales
- ✅ Revisar logs antes de compartir
- ✅ Cambiar contraseñas regularmente

---

## 🐛 Troubleshooting

### Error: "AUTOTRAMITE_EMAIL no configurado"

**Solución:**
1. Verificar que existe el archivo `.env` en la raíz del proyecto
2. Verificar que contiene `AUTOTRAMITE_EMAIL=...`
3. Reiniciar la aplicación Streamlit

### Error: "Credenciales inválidas o login fallido"

**Solución:**
1. Verificar email/password en `.env`
2. Intentar login manual en [AutoTramite.cl](https://autotramite.cl)
3. Revisar si la cuenta está bloqueada
4. Verificar que no haya CAPTCHA en login

### Error: "Timeout esperando campo"

**Solución:**
1. Aumentar `TIMEOUT_ELEMENT` en `.env`
2. Verificar conexión a internet
3. Verificar que AutoTramite.cl está disponible
4. Ejecutar con `PLAYWRIGHT_HEADLESS=False` para debugging

### Error: "playwright not found"

**Solución:**
```bash
playwright install chromium
```

---

## 📊 Comparación con n8n Workflow

| Aspecto | n8n Workflow | Python MVP |
|---------|--------------|------------|
| **Parsing** | Code Node (JS) | `models.py` (Python) |
| **Validación** | Code Node (JS) | `validators.py` (Python) |
| **Automatización** | Browserless API | Playwright local |
| **UI** | Form Trigger | Streamlit |
| **Testing** | Manual | pytest + 30+ tests |
| **Versionado** | JSON difícil | Git-friendly |
| **Debugging** | Complejo | IDE + breakpoints |
| **Costo** | $$ Browserless | Gratis |

---

## 🔄 Próximos Pasos

### Mejoras Potenciales

- [ ] CLI alternativo (`python -m autotramite_py_mvp --file datos.txt`)
- [ ] API REST con FastAPI (reutilizar `src/`)
- [ ] Upload PDF CAV para parsing con OCR
- [ ] Base de datos SQLite para auditoría local
- [ ] Multi-threading para procesar múltiples contratos
- [ ] Docker image para deployment

### Escalabilidad

- [ ] Cola Redis para operaciones asíncronas
- [ ] Monitoreo con Sentry
- [ ] Métricas con Prometheus
- [ ] Deploy en Cloud Run / Fargate
- [ ] Streamlit Cloud para hosting gratis

---

## 📚 Documentación Técnica

### Referencias

- **Plan Original:** [n8n-autotramite-compraventa-workflow-plan.md](../n8n-autotramite-compraventa-workflow-plan.md)
- **Workflow n8n:** [autotramite-compraventa-mvp.json](../autotramite-compraventa-mvp.json)
- **Plan de Migración:** [MIGRATION_PLAN.md](MIGRATION_PLAN.md)

### Selectores CSS Validados

Todos los selectores fueron validados con login real (03-Feb-2026):

```python
# Vehículo
'#patenter', '#DvPatente', '#marca', '#modelo', '#anhio', 
'#color', '#nchasis', '#nmotor', '#tipovehiculo', 
'#tasacion', '#valor_venta'

# Vendedor
'#rutv', '#nombrev', '#apellidopv', '#apellidomv',
'#direccionv', '#comunav', '#ciudadv', '#telefonov', '#correov'

# Comprador
'#rutc', '#nombrec', '#apellidopc', '#apellidomc',
'#direccionc', '#comunac', '#ciudadc', '#telefonoc', '#correoc'

# Config
'#Contado', '#firmaElec', '#operador'
```

---

## 🤝 Contribuir

### Reportar Issues

Si encuentra un bug o tiene una sugerencia:

1. Verificar que no exista un issue similar
2. Crear issue con:
   - Descripción del problema
   - Pasos para reproducir
   - Logs relevantes (ofuscados)
   - Versión de Python y dependencias

### Pull Requests

Bienvenidos! Por favor:

1. Crear branch desde `main`
2. Agregar tests para nueva funcionalidad
3. Verificar que todos los tests pasen (`pytest`)
4. Actualizar README si es necesario

---

## 📄 Licencia

Proyecto interno de AUTORECENTE SPA (QUEIROLO)

---

## 👥 Autores

- **Migración n8n→Python:** Refactorización automática
- **Workflow original:** Basado en plan v1.2 (03-Feb-2026)
- **Empresa:** AUTORECENTE SPA (QUEIROLO)

---

## 📞 Soporte

Para soporte técnico:

- **Email:** dparra@queirolo.cl
- **Documentación:** Ver `MIGRATION_PLAN.md` para detalles técnicos

---

**Última actualización:** 04 Febrero 2026
