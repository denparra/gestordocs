# Plan de Implementacion: Workflow n8n para Contratos de Compraventa en AutoTramite

**Version:** 1.2
**Fecha:** 03 Febrero 2026
**Estado:** PLAN (Pre-implementacion) - LLENADO Y PDF VALIDADOS
**Proyecto:** /projects/gestordocs
**Ultima actualizacion:** Prueba completa de llenado + generacion PDF exitosa

---

## 0. Resumen de Validacion con Playwright (03-Feb-2026)

### ✅ Login Exitoso
- **URL:** `https://autotramite.cl/secciones/login.php`
- **Credenciales:** `[[dparra@queirolo.cl]]` / `[[queirolo#2025.]]`
- **Resultado:** Redireccion exitosa a `index.php`
- **Usuario detectado:** DENNYS EDUARDO PARRA GRANADILLO
- **Empresa:** AUTORECENTE SPA (QUEIROLO)
- **Bloqueos:** Ninguno (sin captcha, sin 2FA, sin rate limiting)

### ✅ Formulario Explorado
- **URL:** `https://autotramite.cl/secciones/vista_personas_empresas.php`
- **Titulo:** "Contratos Personas y/o Empresas - Sistema AutoTrámite"
- **Campos totales:** 70+ (incluyendo opcionales y representantes legales)
- **Campos MVP requeridos:** ~25 campos principales

### 📋 Selectores Clave Validados
```
Vehiculo:    #patenter, #DvPatente, #marca, #modelo, #anhio, #color
             #nchasis, #nmotor, #tipovehiculo, #tasacion, #valor_venta

Vendedor:    #rutv, #nombrev, #apellidopv, #apellidomv
             #direccionv, #comunav, #ciudadv, #telefonov, #correov

Comprador:   #rutc, #nombrec, #apellidopc, #apellidomc
             #direccionc, #comunac, #ciudadc, #telefonoc, #correoc

Config:      #operador (select), #firmaElec (checkbox)
             #Contado (checkbox), #Credito (checkbox)

Acciones:    button "Previsualizar PDF", button "Solicitar Información"
```

### ⚠️ Hallazgos Importantes
1. **Campo año:** El ID es `anhio` (no `ano` ni `year`)
2. **Tipo vehiculo:** Es campo texto, no select (ej: "AUTOMOVIL", "CAMIONETA")
3. **Tasacion:** Campo requerido, con boton "Buscar Opciones" para SII
4. **Representantes legales:** Campos deshabilitados por defecto (solo para empresas)
5. **Carga CAV:** Funcionalidad de upload PDF para auto-completar datos vehiculo

### ✅ Prueba de Llenado Completo (03-Feb-2026)
- **Datos de prueba:** Vehículo HYUNDAI ELANTRA, Patente DRLZ16-3
- **Resultado:** Formulario llenado correctamente
- **PDF generado:** `https://autotramite.cl/pdf/pdf_AutoTramite/contratos/Contrato.php`
- **Estado:** Vista previa exitosa (NO se registró para evitar crear operación real)

---

## 0.1 Formato de Entrada de Datos (Texto Estructurado)

### Fuente de Datos
Los datos provienen de:
- **Certificado de Anotaciones Vigentes (CAV)** del vehículo
- **Nota de venta** generada por la empresa

### Formato de Texto Esperado
```
Inscripción : DRLZ.16-3
DATOS DEL VEHICULO
Tipo Vehículo : AUTOMOVIL Año : 2012
Marca : HYUNDAI
Modelo : ELANTRA GLS 1.6
Nro. Motor : G4FGBU380448
Nro. Chasis : KMHDH41CACU327103
Nro. Vin : KMHDH41CACU327103
Color : ROJO
Combustible : GASOLINA

DATOS DEL VENDEDOR
Nombre : DENNYS EDUARDO PARRA GRANADILLO
R.U.N. : 26.002.284-9
DIRECCION: AV. LAS CONDES 12461, LAS CONDES. SANTIAGO
Telefono: 975400946
Correo: dparra@queirolo.cl

TASACION 10.000.000
VENTA 10.000.000

DATOS COMPRADOR
Nombre: CAROLINA CECILIA CALLES CALLES
RUT: 26033082-9
Direccion: SERRANO, 266. SANTIAGO CENTRO. SANTIAGO
Telefono: 975400946
Correo: dparra@queirolo.cl
```

### Reglas de Parseo

#### 1. Patente (Inscripción/Patente)
```
Entrada:  "Inscripción : DRLZ.16-3" | "Patente : DRLZ16-3" | "AB1234-5"
Separar:  Por guión "-"
Resultado:
  - patente: "DRLZ16" o "AB1234" (quitar punto interno)
  - dv: "3" o "5"
```

#### 2. Separación de Nombres (Vendedor/Comprador)
```
Regla: Últimas 2 palabras = Apellidos, resto = Nombres

Ejemplo 1: "DENNYS EDUARDO PARRA GRANADILLO"
  - Nombres: "DENNYS EDUARDO"
  - Apellido Paterno: "PARRA"
  - Apellido Materno: "GRANADILLO"

Ejemplo 2: "CAROLINA CECILIA CALLES CALLES"
  - Nombres: "CAROLINA CECILIA"
  - Apellido Paterno: "CALLES"
  - Apellido Materno: "CALLES"

Caso especial (solo 2 palabras): "JUAN PEREZ"
  - Nombres: "JUAN"
  - Apellido Paterno: "PEREZ"
  - Apellido Materno: " " (espacio)
```

#### 3. Separación de Dirección
```
Entrada: "AV. LAS CONDES 12461, LAS CONDES. SANTIAGO"
Separar: Primero por coma; si hay 1 coma, separar el resto por punto (evita cortar "AV.").
Resultado:
  - Dirección: "AV. LAS CONDES 12461"
  - Comuna: "LAS CONDES"
  - Ciudad: "SANTIAGO"
```

#### 4. Normalización de RUT
```
Entrada con puntos:    "26.002.284-9" → "26.002.284-9" (sin cambio)
Entrada sin puntos:    "26033082-9"   → "26.033.082-9" (agregar puntos)
```

#### 5. Valores Monetarios
```
Entrada: "10.000.000"
Resultado: "10000000" (quitar puntos de miles)
```

#### 6. Campos Ignorados
- `Nro. Vin`: Usar mismo valor que `Nro. Chasis`
- `Combustible`: No existe en formulario, ignorar

#### 7. Valores por Defecto
- **Generado por:** "AUTORECENTE SPA (QUEIROLO)"
- **Tipo de firma:** Firma Electrónica Avanzada (checkbox `#firmaElec`)
- **Forma de pago:** Contado (checkbox `#Contado` ya viene marcado)

### Algoritmo de Parseo (JavaScript)

```javascript
function parsearTextoContrato(texto) {
  const datos = {};

    // Patente
  const inscripcion = texto.match(/(?:Inscripci(?:o|ó)n|Inscripcion|Patente)\s*:\s*([A-Z0-9.]+)\s*-\s*([0-9K])/i);
  const patenteMatch = inscripcion || texto.match(/([A-Z]{4}\.?[0-9]{2}|[A-Z]{2}\.?[0-9]{4})\s*-\s*([0-9K])/i);
  if (patenteMatch) {
    datos.patente = limpiarPatente(patenteMatch[1]);
    datos.patente_dv = patenteMatch[2].toUpperCase();
  }

  // Vehículo
  datos.tipo_vehiculo = extraer(texto, /Tipo Veh[ií]culo\s*:\s*(\w+)/i);
  datos.ano = extraer(texto, /A[ñn]o\s*:\s*(\d{4})/i);
  datos.marca = extraer(texto, /Marca\s*:\s*(.+?)(?:\n|$)/i);
  datos.modelo = extraer(texto, /Modelo\s*:\s*(.+?)(?:\n|$)/i);
  datos.motor = extraer(texto, /Nro\.\s*Motor\s*:\s*(\S+)/i);
  datos.chasis = extraer(texto, /Nro\.\s*(?:Chasis|Vin)\s*:\s*(\S+)/i);
  datos.color = extraer(texto, /Color\s*:\s*(\w+)/i);

  // Tasación y Venta (quitar puntos de miles)
  datos.tasacion = extraer(texto, /TASACION\s*([0-9.]+)/i)?.replace(/\./g, '');
  datos.venta = extraer(texto, /VENTA\s*([0-9.]+)/i)?.replace(/\./g, '');

  // Vendedor
  const nombreVendedor = extraer(texto, /DATOS DEL VENDEDOR[\s\S]*?Nombre\s*:\s*(.+?)(?:\n|R\.U\.N)/i);
  if (nombreVendedor) {
    const partes = separarNombre(nombreVendedor.trim());
    datos.vendedor_nombres = partes.nombres;
    datos.vendedor_ap_paterno = partes.apellidoPaterno;
    datos.vendedor_ap_materno = partes.apellidoMaterno;
  }
  datos.vendedor_rut = normalizarRUT(extraer(texto, /R\.?U\.?\s*(?:T|N)\.?\s*:\s*([0-9Kk.-]+)/i));

  // Dirección vendedor
  const dirVendedor = extraer(texto, /DIRECCION\s*:\s*(.+?)(?:\n|Telefono)/i);
  if (dirVendedor) {
    const partes = separarDireccion(dirVendedor);
    datos.vendedor_direccion = partes.direccion;
    datos.vendedor_comuna = partes.comuna;
    datos.vendedor_ciudad = partes.ciudad;
  }
  datos.vendedor_telefono = extraer(texto, /Telefono\s*:\s*(\d+)/i);
  datos.vendedor_correo = extraer(texto, /Correo\s*:\s*(\S+@\S+)/i);

  // Comprador (similar lógica)
  const nombreComprador = extraer(texto, /DATOS COMPRADOR[\s\S]*?Nombre\s*:\s*(.+?)(?:\n|RUT)/i);
  if (nombreComprador) {
    const partes = separarNombre(nombreComprador.trim());
    datos.comprador_nombres = partes.nombres;
    datos.comprador_ap_paterno = partes.apellidoPaterno;
    datos.comprador_ap_materno = partes.apellidoMaterno;
  }
  datos.comprador_rut = normalizarRUT(extraer(texto, /DATOS COMPRADOR[\s\S]*?R\.?U\.?\s*(?:T|N)\.?\s*:\s*([0-9Kk.-]+)/i));

  // Dirección comprador
  const dirComprador = extraer(texto, /DATOS COMPRADOR[\s\S]*?Direccion\s*:\s*(.+?)(?:\n|Telefono)/i);
  if (dirComprador) {
    const partes = separarDireccion(dirComprador);
    datos.comprador_direccion = partes.direccion;
    datos.comprador_comuna = partes.comuna;
    datos.comprador_ciudad = partes.ciudad;
  }
  datos.comprador_telefono = extraer(texto, /DATOS COMPRADOR[\s\S]*?Telefono\s*:\s*(\d+)/i);
  datos.comprador_correo = extraer(texto, /DATOS COMPRADOR[\s\S]*?Correo\s*:\s*(\S+@\S+)/i);

  return datos;
}

function extraer(texto, regex) {
  const match = texto.match(regex);
  return match ? match[1].trim() : null;
}

function separarNombre(nombreCompleto) {
  const palabras = nombreCompleto.split(/\s+/);
  if (palabras.length >= 4) {
    return {
      nombres: palabras.slice(0, -2).join(' '),
      apellidoPaterno: palabras[palabras.length - 2],
      apellidoMaterno: palabras[palabras.length - 1]
    };
  } else if (palabras.length === 3) {
    return {
      nombres: palabras[0],
      apellidoPaterno: palabras[1],
      apellidoMaterno: palabras[2]
    };
  } else if (palabras.length === 2) {
    return {
      nombres: palabras[0],
      apellidoPaterno: palabras[1],
      apellidoMaterno: ' '
    };
  }
  return { nombres: nombreCompleto, apellidoPaterno: '', apellidoMaterno: ' ' };
}

function separarDireccion(direccionCompleta) {
  // Patrón: "CALLE NUMERO, COMUNA. CIUDAD"
  // Si hay 1 coma, separar el resto por punto para no cortar abreviaturas (ej: "AV.")
  const partesComa = direccionCompleta.split(/,/)
    .map(p => p.trim())
    .filter(p => p);
  if (partesComa.length >= 3) {
    return { direccion: partesComa[0], comuna: partesComa[1], ciudad: partesComa[2] };
  } else if (partesComa.length === 2) {
    const direccion = partesComa[0];
    const partesPunto = partesComa[1].split(/\./).map(p => p.trim()).filter(p => p);
    if (partesPunto.length >= 2) {
      return { direccion, comuna: partesPunto[0], ciudad: partesPunto[1] };
    }
    return { direccion, comuna: partesPunto[0] || "", ciudad: partesPunto[0] || "" };
  }
  const partes = direccionCompleta.split(/\./).map(p => p.trim()).filter(p => p);
  if (partes.length >= 3) {
    return { direccion: partes[0], comuna: partes[1], ciudad: partes[2] };
  } else if (partes.length === 2) {
    return { direccion: partes[0], comuna: partes[1], ciudad: partes[1] };
  }
  return { direccion: direccionCompleta, comuna: "", ciudad: "" };
}

function normalizarRUT(rut) {
  if (!rut) return "";
  const limpio = rut.replace(/[^0-9Kk]/g, "").toUpperCase();
  if (limpio.length < 2) return "";
  const cuerpo = limpio.slice(0, -1);
  const dv = limpio.slice(-1);
  const formateado = cuerpo.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `${formateado}-${dv}`;
}

function limpiarPatente(patenteRaw) {
  return patenteRaw ? patenteRaw.replace(/[^A-Z0-9]/gi, "").toUpperCase() : "";
}

// Ejecutar con datos de stdin
const datos = JSON.parse(process.argv[2]);
crearContrato(datos)
  .then(result => console.log(JSON.stringify(result)))
  .catch(err => console.error(JSON.stringify({ success: false, error: err.message })));
```

### 5.2 Selectores VALIDADOS (03-Feb-2026)

> **IMPORTANTE:** Todos los selectores fueron validados con login real al sistema.

#### Login (login.php)
| Elemento | ID | Name | Tipo |
|----------|-----|------|------|
| Email/Usuario | `#Correo` | `Correo` | text |
| Contraseña | `#Clave` | `Clave` | password |
| Token CSRF | - | `csrf_token` | hidden |
| Boton Login | - | - | button "Iniciar Sesión" |

#### Datos del Vehiculo (vista_personas_empresas.php)
| Campo | ID | Name | Tipo | Requerido |
|-------|-----|------|------|-----------|
| Patente (busqueda) | `#patente` | `patente` | text | No |
| Patente (principal) | `#patenter` | `patenter` | text | **Si** |
| Digito Verificador | `#DvPatente` | `DvPatente` | text | **Si** |
| Marca | `#marca` | `marca` | text | **Si** |
| Modelo | `#modelo` | `modelo` | text | **Si** |
| Año | `#anhio` | `anhio` | number | **Si** |
| Color | `#color` | `color` | text | **Si** |
| Numero Chasis | `#nchasis` | `nchasis` | text | **Si** |
| Numero Motor | `#nmotor` | `nmotor` | text | **Si** |
| Tipo Vehiculo | `#tipovehiculo` | `tipovehiculo` | text | **Si** |
| Tasacion | `#tasacion` | `tasacion` | number | **Si** |
| Valor Venta | `#valor_venta` | `valor_venta` | number | **Si** |

#### Datos del Vendedor
| Campo | ID | Name | Tipo | Requerido |
|-------|-----|------|------|-----------|
| RUT | `#rutv` | `rutv` | text | **Si** |
| Nombres | `#nombrev` | `nombrev` | text | **Si** |
| Apellido Paterno | `#apellidopv` | `apellidopv` | text | No |
| Apellido Materno | `#apellidomv` | `apellidomv` | text | No |
| Direccion | `#direccionv` | `direccionv` | text | **Si** |
| Comuna | `#comunav` | `comunav` | text | **Si** |
| Ciudad | `#ciudadv` | `ciudadv` | text | **Si** |
| Telefono | `#telefonov` | `telefonov` | tel | **Si** |
| Correo | `#correov` | `correov` | email | **Si** |

#### Datos del Comprador
| Campo | ID | Name | Tipo | Requerido |
|-------|-----|------|------|-----------|
| RUT | `#rutc` | `rutc` | text | **Si** |
| Nombres | `#nombrec` | `nombrec` | text | No |
| Apellido Paterno | `#apellidopc` | `apellidopc` | text | No |
| Apellido Materno | `#apellidomc` | `apellidomc` | text | No |
| Direccion | `#direccionc` | `direccionc` | text | **Si** |
| Comuna | `#comunac` | `comunac` | text | **Si** |
| Ciudad | `#ciudadc` | `ciudadc` | text | **Si** |
| Telefono | `#telefonoc` | `telefonoc` | text | **Si** |
| Correo | `#correoc` | `correoc` | text | **Si** |

#### Configuracion del Contrato
| Campo | ID | Name | Tipo | Opciones/Valor |
|-------|-----|------|------|----------------|
| Pago Contado | `#Contado` | `Contado` | checkbox | checked por defecto |
| Pago Credito | `#Credito` | `Credito` | checkbox | - |
| Detalle Credito | `#detalle_credito` | `detalle_credito` | textarea | disabled si Contado |
| Generado por | `#operador` | `operador` | select | "AUTORECENTE SPA (QUEIROLO)" |
| Firma Electronica | `#firmaElec` | `firmaElec` | checkbox | FEA |

#### Botones de Accion
| Boton | ID | Tipo | Selector Playwright |
|-------|-----|------|---------------------|
| Solicitar Info | `#btnSolicitarInfo` | submit | `button:has-text("Solicitar Información")` |
| Buscar Tasacion | `#btnBuscarTasacion` | button | `button:has-text("Buscar Opciones")` |
| Previsualizar PDF | - | submit | `button:has-text("Previsualizar PDF")` |

#### Funcionalidades Adicionales Descubiertas
| Funcion | Descripcion | Uso en MVP |
|---------|-------------|------------|
| Carga CAV | Upload PDF para extraccion automatica de datos vehiculo | Opcional |
| Rep. Legal Vendedor | Campos habilitados si es empresa | Solo personas naturales MVP |
| Rep. Legal Comprador | Campos habilitados si es empresa | Solo personas naturales MVP |
| Vendedores Adicionales | Agregar multiples vendedores | Excluido MVP |
| Compradores Adicionales | Agregar multiples compradores | Excluido MVP |

### 5.3 Estrategia de Waits

```javascript
// Patron recomendado para cada accion
const TIMEOUTS = {
  navigation: 30000,    // 30s para cargas de pagina
  element: 10000,       // 10s para elementos
  animation: 500        // 0.5s para animaciones UI
};

// Esperar navegacion completa
await page.waitForLoadState('networkidle', { timeout: TIMEOUTS.navigation });

// Esperar elemento visible antes de interactuar
await page.waitForSelector('#campo', { state: 'visible', timeout: TIMEOUTS.element });

// Esperar que desaparezca loader/spinner
await page.waitForSelector('.loading', { state: 'hidden', timeout: TIMEOUTS.navigation });

// Delay entre campos (evitar rate limiting)
await page.waitForTimeout(200);
```

### 5.4 Manejo de Redirects

```javascript
// Detectar y manejar redirects
page.on('response', response => {
  if (response.status() >= 300 && response.status() < 400) {
    console.log(`Redirect detectado: ${response.url()} -> ${response.headers()['location']}`);
  }
});

// Esperar URL especifica despues de submit
await page.waitForURL('**/confirmacion**', { timeout: 30000 });
// o
await page.waitForURL(url => !url.includes('login'), { timeout: 30000 });
```

---

## 6. Salidas/Entrega del PDF/ID Operacion

### 6.1 Opciones de Recuperacion de Resultados

| Opcion | Complejidad | Pros | Contras |
|--------|-------------|------|---------|
| **A: Extraer URL del PDF** | Baja | Simple, rapido | Depende de que AutoTramite exponga URL |
| **B: Descargar PDF via Playwright** | Media | Control total del archivo | Requiere almacenamiento |
| **C: Screenshot de confirmacion** | Baja | Siempre funciona | No es el documento oficial |
| **D: Scraping del ID de operacion** | Baja | Referencia para seguimiento | Solo ID, no documento |

### 6.2 Opcion Recomendada para MVP

**Combinacion A + D**: Extraer URL del PDF (si existe) + ID de operacion.

```javascript
// Extraer resultados de la pagina de confirmacion
async function extraerResultado(page) {
  const resultado = {
    operacion_id: null,
    pdf_url: null,
    mensaje_confirmacion: null
  };

  // Buscar ID de operacion
  const posiblesSelectoresId = [
    '.operacion-id',
    '#numero-operacion',
    'span:has-text("Folio")',
    'td:has-text("ID")'
  ];

  for (const selector of posiblesSelectoresId) {
    try {
      const elemento = await page.$(selector);
      if (elemento) {
        const texto = await elemento.textContent();
        const match = texto.match(/\d+/);
        if (match) {
          resultado.operacion_id = match[0];
          break;
        }
      }
    } catch (e) { /* continuar */ }
  }

  // Buscar link de PDF
  const linkPdf = await page.$('a[href$=".pdf"], a[download], a:has-text("Descargar")');
  if (linkPdf) {
    resultado.pdf_url = await linkPdf.getAttribute('href');
    // Convertir URL relativa a absoluta si es necesario
    if (resultado.pdf_url && !resultado.pdf_url.startsWith('http')) {
      resultado.pdf_url = new URL(resultado.pdf_url, page.url()).href;
    }
  }

  // Mensaje de confirmacion
  const mensajeEl = await page.$('.alert-success, .mensaje-exito, .confirmacion');
  if (mensajeEl) {
    resultado.mensaje_confirmacion = await mensajeEl.textContent();
  }

  return resultado;
}
```

### 6.3 Almacenamiento del PDF (Opciones Avanzadas)

Si se requiere almacenar el PDF:

| Destino | Metodo | Integracion n8n |
|---------|--------|-----------------|
| Google Drive | Upload via API | Nodo Google Drive |
| S3/MinIO | PUT objeto | Nodo AWS S3 |
| Local filesystem | Guardar en servidor | Execute Command |
| Base de datos | BLOB/bytea | Nodo Postgres/MySQL |

```javascript
// Descargar PDF en Playwright
const downloadPromise = page.waitForEvent('download');
await page.click('a:has-text("Descargar PDF")');
const download = await downloadPromise;
const path = await download.path();
const buffer = fs.readFileSync(path);
// buffer puede ser enviado a n8n como base64
return { pdf_base64: buffer.toString('base64') };
```

### 6.4 Email de Confirmacion

**Contenido minimo del email:**

```html
Asunto: [AutoTramite] Contrato Registrado - {{patente}}

Cuerpo:
- Resumen de la operacion (vehiculo, partes, valor)
- ID de operacion (para seguimiento)
- Link al PDF (si disponible)
- Instrucciones de siguiente paso (firma, revision, etc.)
- Contacto de soporte
```

---

## 7. Manejo de Errores y Reintentos

### 7.1 Clasificacion de Errores

| Tipo | Ejemplos | Accion |
|------|----------|--------|
| **Recuperable** | Timeout, red inestable | Reintentar hasta 3 veces |
| **No recuperable** | Credenciales invalidas, captcha | Notificar y detener |
| **Parcial** | Formulario incompleto | Notificar campos faltantes |
| **Sistema externo** | AutoTramite caido | Reintentar con backoff |

### 7.2 Estrategia de Reintentos

```javascript
async function ejecutarConReintentos(fn, maxIntentos = 3, delayBase = 2000) {
  let ultimoError;

  for (let intento = 1; intento <= maxIntentos; intento++) {
    try {
      return await fn();
    } catch (error) {
      ultimoError = error;

      // Errores no recuperables - no reintentar
      if (error.message.includes('LOGIN_FAILED') ||
          error.message.includes('CAPTCHA') ||
          error.message.includes('CUENTA_BLOQUEADA')) {
        throw error;
      }

      // Esperar antes de reintentar (exponential backoff)
      if (intento < maxIntentos) {
        const delay = delayBase * Math.pow(2, intento - 1);
        console.log(`Intento ${intento} fallido. Reintentando en ${delay}ms...`);
        await new Promise(r => setTimeout(r, delay));
      }
    }
  }

  throw new Error(`Fallido despues de ${maxIntentos} intentos: ${ultimoError.message}`);
}
```

### 7.3 Notificaciones de Error

```yaml
errores_a_notificar:
  - tipo: LOGIN_FAILED
    canal: email + slack
    mensaje: "Credenciales AutoTramite invalidas. Verificar configuracion."

  - tipo: CAPTCHA_DETECTED
    canal: email + slack
    mensaje: "Se detecto captcha en login. Requiere intervencion manual."

  - tipo: SESSION_EXPIRED
    canal: log
    mensaje: "Sesion expirada durante operacion. Reintentando login."

  - tipo: FORM_VALIDATION_FAILED
    canal: email (al usuario)
    mensaje: "Datos invalidos: {{errores}}. Corregir y reintentar."

  - tipo: SYSTEM_UNAVAILABLE
    canal: email + slack
    mensaje: "AutoTramite no disponible. Reintentos agotados."
```

### 7.4 Logging y Auditoria

```javascript
// Estructura de log para cada operacion
const logEntry = {
  timestamp: new Date().toISOString(),
  operacion: 'crear_contrato',
  patente: datos.patente,
  vendedor_rut: datos.vendedor_rut.slice(0, 4) + '****', // Ofuscar PII
  comprador_rut: datos.comprador_rut.slice(0, 4) + '****',
  resultado: 'success|error',
  duracion_ms: 0,
  intentos: 1,
  error_mensaje: null,
  operacion_id: null
};

// NO loguear:
// - Credenciales completas
// - RUTs completos
// - Telefonos completos
// - Contenido de emails
```

---

## 8. Plan de Pruebas y Criterios de Aceptacion

### 8.1 Datos de Prueba (Dummy)

```yaml
vehiculo_prueba:
  patente: "ZZZZ99"
  patente_dv: "K"
  marca: "TEST"
  modelo: "PRUEBA"
  ano: 2020
  color: "GRIS"
  num_chasis: "TEST123456789012345"
  num_motor: "TEST123456789"
  tipo_vehiculo: "liviano"
  tasacion: 5000000
  valor_venta: 4500000

vendedor_prueba:
  rut: "11.111.111-1"  # RUT de prueba valido
  nombres: "JUAN PRUEBA"
  ap_paterno: "TEST"
  ap_materno: "DUMMY"
  direccion: "AV. TEST 123"
  comuna: "SANTIAGO"
  ciudad: "SANTIAGO"
  telefono: "912345678"
  email: "test.vendedor@test.cl"

comprador_prueba:
  rut: "22.222.222-2"  # RUT de prueba valido
  nombres: "MARIA PRUEBA"
  ap_paterno: "TEST"
  ap_materno: "DUMMY"
  direccion: "AV. TEST 456"
  comuna: "PROVIDENCIA"
  ciudad: "SANTIAGO"
  telefono: "987654321"
  email: "test.comprador@test.cl"

configuracion_prueba:
  generado_por: "AUTORECENTE SPA (QUEIROLO)"
  tipo_firma: "fea"
```

### 8.2 Casos de Prueba

#### CP-01: Caso Feliz - Flujo Completo
```yaml
id: CP-01
nombre: Crear contrato con datos validos
precondiciones:
  - Credenciales AutoTramite configuradas
  - Sistema AutoTramite disponible
pasos:
  1. Enviar formulario con datos de prueba completos
  2. Verificar validacion exitosa
  3. Verificar login exitoso
  4. Verificar llenado de formulario
  5. Verificar previsualizacion PDF
  6. Verificar registro de operacion
resultado_esperado:
  - Estado: success
  - operacion_id: no null
  - Email enviado a test.vendedor@test.cl y test.comprador@test.cl
criterio_aceptacion: Operacion registrada en menos de 2 minutos
```

#### CP-02: Validacion de Formato - RUT Invalido
```yaml
id: CP-02
nombre: Rechazar RUT con digito verificador incorrecto
pasos:
  1. Enviar formulario con vendedor_rut: "11.111.111-2" (DV incorrecto)
resultado_esperado:
  - Estado: error
  - Mensaje: "RUT vendedor invalido"
  - No se intenta login
```

#### CP-03: Validacion de Formato - Patente Invalida
```yaml
id: CP-03
nombre: Rechazar patente con formato incorrecto
pasos:
  1. Enviar formulario con patente: "123ABC" (formato incorrecto)
resultado_esperado:
  - Estado: error
  - Mensaje: "Formato patente invalido"
```

#### CP-04: Validacion de Formato - Telefono Invalido
```yaml
id: CP-04
nombre: Rechazar telefono con formato incorrecto
pasos:
  1. Enviar formulario con vendedor_telefono: "123" (muy corto)
resultado_esperado:
  - Estado: error
  - Mensaje: "Telefono vendedor invalido"
```

#### CP-05: Error de Login - Credenciales Incorrectas
```yaml
id: CP-05
nombre: Manejar credenciales AutoTramite invalidas
precondiciones:
  - Configurar credenciales incorrectas temporalmente
pasos:
  1. Enviar formulario con datos validos
resultado_esperado:
  - Estado: error
  - Mensaje contiene: "LOGIN_FAILED"
  - Notificacion enviada a administrador
```

#### CP-06: Timeout - Sistema Lento
```yaml
id: CP-06
nombre: Manejar timeout por sistema lento
precondiciones:
  - Simular latencia alta (o sistema real lento)
pasos:
  1. Enviar formulario con datos validos
resultado_esperado:
  - Reintentos automaticos (hasta 3)
  - Si falla: Estado error con mensaje de timeout
```

#### CP-07: Campo Tasacion Opcional
```yaml
id: CP-07
nombre: Crear contrato sin tasacion
pasos:
  1. Enviar formulario con tasacion: null (vacio)
resultado_esperado:
  - Validacion exitosa
  - Formulario se llena sin campo tasacion
  - Operacion registrada
```

### 8.3 Checklist de Validacion Pre-Produccion

```markdown
## Pre-Produccion Checklist

### Configuracion
- [ ] Variables de entorno configuradas (AUTOTRAMITE_EMAIL, AUTOTRAMITE_PASSWORD)
- [ ] Credenciales almacenadas en secret store (no en codigo)
- [ ] Email de notificaciones configurado
- [ ] Workflow importado en n8n

### Pruebas Manuales
- [ ] CP-01: Caso feliz ejecutado exitosamente
- [ ] CP-02 a CP-04: Validaciones de formato funcionan
- [ ] CP-05: Error de login manejado correctamente
- [ ] CP-06: Reintentos funcionan
- [ ] CP-07: Campo opcional funciona

### Seguridad
- [ ] Credenciales no aparecen en logs
- [ ] PII ofuscada en registros
- [ ] HTTPS usado para todas las conexiones
- [ ] Tokens CSRF manejados correctamente

### Operacion
- [ ] Monitoreo configurado (alertas de error)
- [ ] Documentacion de troubleshooting disponible
- [ ] Contacto de soporte definido
- [ ] Procedimiento de rollback documentado

### Aprobaciones
- [ ] Pruebas aprobadas por QA
- [ ] Revision de seguridad completada
- [ ] Aprobacion de stakeholder para produccion
```

---

## 9. Bloqueos Potenciales y Alternativas

### 9.1 Bloqueos Identificados

| Bloqueo | Probabilidad | Impacto | Alternativa |
|---------|--------------|---------|-------------|
| **Captcha en login** | Media | Alto | Paso manual de login; sesion persistente |
| **2FA/MFA obligatorio** | Baja | Alto | Integracion con app 2FA o paso manual |
| **Cambios frecuentes en UI** | Media | Medio | Selectores flexibles; monitoreo de cambios |
| **Rate limiting agresivo** | Baja | Medio | Delays; cola de operaciones |
| **IP bloqueada** | Baja | Alto | Proxy rotativo; IP dedicada |
| **Sesion unica por cuenta** | Media | Medio | Mutex para operaciones; cola FIFO |

### 9.2 Plan de Contingencia

**Si se detecta captcha:**
1. Pausar automatizacion
2. Notificar a operador
3. Operador completa captcha manualmente
4. Automatizacion continua desde punto de pausa

**Si se detecta 2FA:**
1. Evaluar integracion con servicio 2FA (ej: Twilio)
2. O: Operador ingresa codigo manualmente
3. Sesion se mantiene activa por periodo extendido

**Si UI cambia significativamente:**
1. Alertas automaticas cuando selectores fallan
2. Modo degradado: solo validacion, sin submit
3. Actualizacion de selectores por desarrollador

---

## 10. Arquitectura Final Recomendada

```
┌─────────────────────────────────────────────────────────────────┐
│                         n8n Cloud/Self-hosted                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │ Form Trigger │───►│  Validador   │───►│ Execute Command  │  │
│  │  (Entrada)   │    │   (Code)     │    │  (Playwright)    │  │
│  └──────────────┘    └──────────────┘    └────────┬─────────┘  │
│                                                    │            │
│                                                    ▼            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │    Email     │◄───│   IF/Switch  │◄───│ Script Response  │  │
│  │ (Resultado)  │    │  (OK/Error)  │    │   (JSON stdout)  │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Servidor con Playwright                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  playwright_autotramite.js                                │  │
│  │  - Recibe JSON con datos del contrato                     │  │
│  │  - Ejecuta automatizacion browser                         │  │
│  │  - Retorna JSON con resultado                             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Variables de entorno:                                          │
│  - AUTOTRAMITE_EMAIL (secret)                                   │
│  - AUTOTRAMITE_PASSWORD (secret)                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AutoTramite.cl                              │
│               (Sistema externo - no modificable)                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 11. Proximos Pasos

### Fase 1: Validacion (1-2 dias)
- [ ] Obtener acceso de prueba a AutoTramite
- [ ] Validar selectores del formulario real (vista_personas_empresas.php)
- [ ] Confirmar existencia de ID de operacion y URL de PDF
- [ ] Documentar campos exactos del formulario interno

### Fase 2: Desarrollo (3-5 dias)
- [ ] Implementar script Playwright completo
- [ ] Crear workflow n8n con todos los nodos
- [ ] Configurar manejo de errores
- [ ] Implementar logging y notificaciones

### Fase 3: Pruebas (2-3 dias)
- [ ] Ejecutar casos de prueba CP-01 a CP-07
- [ ] Pruebas de carga (multiples operaciones)
- [ ] Pruebas de recuperacion (errores simulados)
- [ ] Revision de seguridad

### Fase 4: Despliegue (1 dia)
- [ ] Configurar variables de produccion
- [ ] Activar workflow en n8n
- [ ] Capacitar a operadores
- [ ] Monitoreo activo primera semana

---

**Documento generado:** 03 Febrero 2026
**Autor:** Analisis automatizado con Claude + Playwright
**Estado:** PLAN - Requiere validacion de formulario interno antes de implementar
