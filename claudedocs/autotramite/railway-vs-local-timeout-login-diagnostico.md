# Diagn&oacute;stico: Timeout de Login AutoTramite en Railway vs Local

**Fecha**: 2026-02-10
**Error reportado**: `Error en la Operaci&oacute;n: Error: Timeout durante login (posible problema de red).`
**Entorno afectado**: Railway (producci&oacute;n)
**Entorno funcional**: Local (Windows)

---

## 1. Resumen del Problema

El flujo AutoTramite (creaci&oacute;n autom&aacute;tica de contratos de compraventa via Playwright) funciona correctamente en entorno local pero falla consistentemente en Railway con un timeout durante el paso de login.

### Traza del Error

El error se origina en `src/autotramite.py:148`:

```python
except PlaywrightTimeoutError:
    raise RecoverableError('Timeout durante login (posible problema de red)')
```

Esto significa que **alguna operaci&oacute;n dentro de `login_autotramite()`** excedi&oacute; su timeout. Las operaciones candidatas son:

| L&iacute;nea | Operaci&oacute;n | Timeout | Descripci&oacute;n |
|-------|-----------|---------|-------------|
| `autotramite.py:126` | `page.goto(login_url, wait_until='networkidle')` | 30000ms | Navegaci&oacute;n a login.php |
| `autotramite.py:129` | `fill_field(page, '#Correo', email)` | 10000ms | Esperar y llenar campo email |
| `autotramite.py:130` | `fill_field(page, '#Clave', password)` | 10000ms | Esperar y llenar campo password |
| `autotramite.py:133` | `click_button(page, 'button:has-text("Iniciar")', wait_navigation=True)` | 30000ms | Click login + esperar navegaci&oacute;n |

El `PlaywrightTimeoutError` es capturado como bloque gen&eacute;rico en la l&iacute;nea 147-148, sin distinguir cu&aacute;l de estas operaciones fall&oacute;.

---

## 2. Diferencias de Entorno: LOCAL vs Railway

### 2.1 Modo de Despliegue

| Aspecto | Local (Windows) | Railway |
|---------|----------------|---------|
| **Builder** | Manual (`.venv`, `pip install`) | Nixpacks (`railway.json`) |
| **Start Command** | `streamlit run app.py` | `bash -lc 'unset STREAMLIT_SERVER_PORT; exec streamlit run app.py --server.address 0.0.0.0 --server.port "${PORT}"'` |
| **Build Command** | `playwright install chromium` | `pip install -r requirements.txt && playwright install chromium --with-deps` |
| **Dockerfile** | No usado localmente | Existe pero `railway.json` usa Nixpacks |

**Hallazgo cr&iacute;tico**: `railway.json` usa builder `NIXPACKS`, NO el `Dockerfile`. El Dockerfile instala dependencias de sistema expl&iacute;citamente (libnss3, libatk, etc.), pero Nixpacks depende de `playwright install --with-deps` para resolver dependencias del sistema. Si `--with-deps` no instala todas las libs necesarias en el entorno Nixpacks, Chromium puede fallar silenciosamente.

### 2.2 Chromium y Dependencias del Sistema

| Aspecto | Local | Railway (Nixpacks) |
|---------|-------|---------------------|
| **OS** | Windows 10/11 | Linux (Nixpacks base image) |
| **Chromium** | Playwright-managed (Windows binary) | `playwright install chromium --with-deps` |
| **System libs** | Pre-instaladas con Windows | Depende de `--with-deps` resoluci&oacute;n |
| **Sandboxing** | No aplica (Windows) | Linux requiere `--no-sandbox` o permisos |
| **`/tmp` writable** | S&iacute; | Generalmente s&iacute;, pero l&iacute;mite de espacio |
| **GPU** | Disponible | No disponible (servidor headless) |

**Riesgo**: En contenedores Linux, Chromium necesita `--no-sandbox` o un usuario no-root con permisos adecuados. El c&oacute;digo actual (`autotramite.py:772-773`) NO pasa argumentos de launch:

```python
browser: Browser = await p.chromium.launch(
    headless=settings.playwright_headless,
    slow_mo=settings.playwright_slow_mo
)
```

No hay `args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']`.

### 2.3 Red y Egress

| Aspecto | Local | Railway |
|---------|-------|---------|
| **IP de salida** | IP residencial/oficina Chile | IP de datacenter (US/EU) |
| **Latencia a autotramite.cl** | ~5-30ms (Chile) | ~150-300ms+ (intercontinental) |
| **DNS** | ISP local | Resolver del datacenter |
| **Firewall/WAF** | No aplica | autotramite.cl puede bloquear IPs de datacenter |
| **Rate limiting** | Improbable | Posible por IP no residencial |
| **GeoIP blocking** | No (IP chilena) | Posible (IP no chilena) |

**Riesgo alto**: Si `autotramite.cl` usa protecci&oacute;n CloudFlare, WAF, o bloqueo por GeoIP, las requests desde Railway (datacenter US) pueden ser bloqueadas, redirigidas a un captcha, o simplemente lentas.

### 2.4 Recursos (CPU/RAM)

| Aspecto | Local | Railway |
|---------|-------|---------|
| **RAM** | 8-16 GB t&iacute;pico | ~512MB-1GB (plan b&aacute;sico) |
| **CPU** | Dedicada | Compartida, con throttling |
| **Cold start** | No aplica | S&iacute; (tras inactividad) |
| **Disk** | SSD persistente | Ef&iacute;mero, l&iacute;mite de espacio |

Chromium headless necesita ~200-400MB de RAM. En Railway con plan b&aacute;sico, esto puede ser ajustado.

### 2.5 Variables de Entorno

| Variable | `.env.example` | &iquest;Necesaria en Railway? | Notas |
|----------|---------------|------------------------|-------|
| `AUTOTRAMITE_EMAIL` | S&iacute; | **CR&Iacute;TICA** | Si falta, login falla antes del timeout |
| `AUTOTRAMITE_PASSWORD` | S&iacute; | **CR&Iacute;TICA** | Idem |
| `PLAYWRIGHT_HEADLESS` | `True` | Recomendada | Default ya es `True` en config.py |
| `TIMEOUT_NAVIGATION` | `30000` | Considerar aumentar | 30s puede ser insuficiente desde datacenter |
| `TIMEOUT_ELEMENT` | `10000` | Considerar aumentar | Idem |
| `MAX_REINTENTOS` | `3` | OK | Ya tiene retry con backoff exponencial |
| `LOG_LEVEL` | `INFO` | Cambiar a `DEBUG` para diagn&oacute;stico | Permite ver qu&eacute; paso falla |

---

## 3. Hallazgos en el C&oacute;digo

### 3.1 `wait_until='networkidle'` (autotramite.py:126)

```python
await page.goto(settings.autotramite_login_url, wait_until='networkidle', timeout=settings.timeout_navigation)
```

**`networkidle`** espera hasta que no haya m&aacute;s de 0 conexiones de red durante 500ms. En un servidor con alta latencia o si `autotramite.cl` tiene scripts de analytics/tracking que tardan, esto puede NUNCA resolverse dentro de 30s.

**Comparaci&oacute;n**: Localmente la p&aacute;gina carga en ~2-5s. Desde un datacenter US, la latencia base ya suma ~300ms por request, y si hay 10+ requests para la p&aacute;gina, puede f&aacute;cilmente exceder 30s para alcanzar "networkidle".

### 3.2 `click_button` con `wait_navigation=True` (autotramite.py:133)

```python
await click_button(page, SELECTORS['login_submit'], wait_navigation=True)
```

Esto ejecuta `page.expect_navigation(timeout=30000)` + `page.click()`. Si el login redirige con m&uacute;ltiples hops (302 -> 302 -> 200), la espera puede fallar.

### 3.3 Sin argumentos de Chromium launch

```python
browser = await p.chromium.launch(
    headless=settings.playwright_headless,
    slow_mo=settings.playwright_slow_mo
)
```

Faltan argumentos cr&iacute;ticos para contenedores Linux:
- `--no-sandbox`: Necesario si se ejecuta como root (com&uacute;n en contenedores)
- `--disable-dev-shm-usage`: Evita crashes por `/dev/shm` peque&ntilde;o en containers
- `--disable-gpu`: No hay GPU en servidores

### 3.4 Invocaci&oacute;n v&iacute;a subprocess (app.py:1413-1427)

La automatizaci&oacute;n se ejecuta como un **subprocess separado** (`run_autotramite_cli.py`). Esto es correcto (evita problemas con el event loop de Streamlit), pero agrega overhead de startup.

### 3.5 Retry con backoff (autotramite.py:693-743)

El sistema tiene retry con backoff exponencial (base 2000ms, 3 intentos). Si el primer intento falla por timeout a los 30s, el segundo intento espera 2s y luego intenta de nuevo (otros 30s), y el tercero espera 4s + 30s. Total potencial: **~96s** antes de reportar error.

---

## 4. Hip&oacute;tesis Priorizadas

### P0 - Cr&iacute;ticas (Causa m&aacute;s probable)

#### H1: Chromium no puede iniciar correctamente en el contenedor Nixpacks
- **Evidencia**: No se pasan `--no-sandbox` ni `--disable-dev-shm-usage` al launch. En contenedores Linux ejecutados como root, Chromium requiere `--no-sandbox`.
- **Comportamiento esperado**: Chromium lanza pero crashea o queda colgado al navegar, causando timeout.
- **Prueba**: Agregar logs antes/despu&eacute;s de `p.chromium.launch()` y `page.goto()`. Verificar si el browser siquiera arranca.
- **Fix sugerido**: Agregar `args` al launch:
  ```python
  browser = await p.chromium.launch(
      headless=settings.playwright_headless,
      slow_mo=settings.playwright_slow_mo,
      args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
  )
  ```

#### H2: `wait_until='networkidle'` nunca se resuelve desde Railway
- **Evidencia**: Alta latencia intercontinental + posibles scripts de tracking en autotramite.cl.
- **Comportamiento esperado**: `page.goto()` espera indefinidamente el "networkidle" y alcanza timeout de 30s.
- **Prueba**: Cambiar a `wait_until='domcontentloaded'` y verificar si el login procede.
- **Fix sugerido**: Cambiar `networkidle` por `domcontentloaded` o `load`:
  ```python
  await page.goto(url, wait_until='domcontentloaded', timeout=settings.timeout_navigation)
  ```

#### H3: autotramite.cl bloquea/throttlea IPs de datacenter (GeoIP/WAF)
- **Evidencia**: Railway corre en datacenters US/EU. autotramite.cl es un servicio chileno que podr&iacute;a tener protecci&oacute;n por geo.
- **Comportamiento esperado**: La request nunca llega al servidor real, o recibe un challenge (captcha/403), y la p&aacute;gina nunca carga los selectores esperados.
- **Prueba**: Desde Railway, ejecutar `curl -I https://autotramite.cl/secciones/login.php` y verificar status code y headers (CloudFlare, captcha redirect).
- **Fix sugerido**: Si hay bloqueo geo, se necesita un proxy chileno o ejecutar desde infraestructura en Chile.

### P1 - Importantes (Causa posible)

#### H4: Dependencias de sistema incompletas en Nixpacks
- **Evidencia**: El `Dockerfile` instala expl&iacute;citamente 14+ paquetes de sistema (libnss3, libatk, etc.), pero `railway.json` usa Nixpacks con solo `playwright install chromium --with-deps`. El flag `--with-deps` puede no cubrir todo en el entorno Nixpacks.
- **Prueba**: Verificar logs de build en Railway: buscar warnings de libs faltantes. Alternativamente, cambiar a builder `DOCKERFILE` en `railway.json`.
- **Fix sugerido**: Cambiar `railway.json` para usar el Dockerfile existente:
  ```json
  {
    "build": {
      "builder": "DOCKERFILE",
      "dockerfilePath": "Dockerfile"
    }
  }
  ```

#### H5: Recursos insuficientes (RAM/CPU) para Chromium
- **Evidencia**: Chromium headless necesita ~200-400MB. En planes Railway b&aacute;sicos con cold start, puede haber OOM o throttling.
- **Prueba**: Monitorear uso de memoria en Railway dashboard durante ejecuci&oacute;n. Si el container se reinicia, es OOM.
- **Fix sugerido**: Escalar el plan Railway o optimizar con `--disable-extensions --disable-default-apps --js-flags="--max-old-space-size=256"`.

#### H6: Timeout de 30s insuficiente con latencia intercontinental
- **Evidencia**: `timeout_navigation=30000` ms. Latencia US->Chile puede ser ~200-300ms por request.
- **Prueba**: Aumentar `TIMEOUT_NAVIGATION=60000` y `TIMEOUT_ELEMENT=20000` en Railway env vars.
- **Fix sugerido**: Aumentar timeouts en variables de entorno Railway.

### P2 - Menores (Causa menos probable)

#### H7: Variables de entorno AUTOTRAMITE_EMAIL/PASSWORD no configuradas en Railway
- **Evidencia**: El c&oacute;digo valida credenciales antes de ejecutar (`validar_credenciales()`), y si faltaran, el error ser&iacute;a distinto ("Invalid credentials"). Pero vale verificar.
- **Prueba**: Verificar en Railway dashboard que las variables existen y tienen valores correctos.

#### H8: DNS resolution lenta en Railway
- **Evidencia**: Container Linux puede tener resolvers lentos.
- **Prueba**: Agregar log del tiempo de `page.goto()` por separado.

#### H9: Cold start + timeout combinados
- **Evidencia**: Despu&eacute;s de inactividad, Railway hace cold start (~10-30s). Si se suma al timeout de Playwright, puede parecer timeout de login.
- **Prueba**: Verificar si el error ocurre siempre o solo en primera ejecuci&oacute;n.

---

## 5. Pruebas Realizadas / C&oacute;mo Reproducir

### 5.1 An&aacute;lisis Est&aacute;tico (realizado)

- [x] Revisado `src/autotramite.py`: l&iacute;nea exacta del timeout identificada (148)
- [x] Revisado `src/config.py`: timeouts y configuraci&oacute;n por defecto documentados
- [x] Revisado `railway.json`: usa Nixpacks (no Dockerfile), buildCommand con `playwright install`
- [x] Revisado `Dockerfile`: tiene deps de sistema, pero NO se usa en Railway
- [x] Revisado `start.sh`: dual startup (API + Streamlit)
- [x] Revisado `run_autotramite_cli.py`: subprocess wrapper para evitar event loop conflicts
- [x] Revisado `.env.example`: variables documentadas
- [x] Revisado docs de deploy: no mencionan problemas de login/timeout

### 5.2 Pruebas de Reproducci&oacute;n (pendientes - recomendadas)

#### Test A: Verificar conectividad desde Railway
```bash
# Ejecutar en Railway CLI o agregar como script temporal
curl -sS -o /dev/null -w "HTTP_CODE:%{http_code} TIME_TOTAL:%{time_total}s DNS:%{time_namelookup}s CONNECT:%{time_connect}s" \
  https://autotramite.cl/secciones/login.php
```
**Objetivo**: Verificar si Railway puede alcanzar autotramite.cl y cu&aacute;nto tarda.

#### Test B: Verificar headers de respuesta (WAF/CloudFlare)
```bash
curl -I https://autotramite.cl/secciones/login.php
```
**Objetivo**: Buscar headers de CloudFlare (`cf-ray`, `server: cloudflare`), captchas, o redirects.

#### Test C: Probar Chromium launch en Railway
```python
# Script de prueba temporal
import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        )
        page = await browser.new_page()
        try:
            resp = await page.goto('https://autotramite.cl/secciones/login.php',
                                    wait_until='domcontentloaded', timeout=60000)
            print(f"STATUS: {resp.status}")
            print(f"URL: {page.url}")
            title = await page.title()
            print(f"TITLE: {title}")
            # Verificar si hay captcha o bloqueo
            content = await page.content()
            if 'captcha' in content.lower() or 'challenge' in content.lower():
                print("WARNING: Captcha/challenge detected!")
            if 'cloudflare' in content.lower():
                print("WARNING: CloudFlare challenge page!")
        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            await browser.close()

asyncio.run(test())
```

#### Test D: Verificar con LOG_LEVEL=DEBUG
Cambiar en Railway env vars: `LOG_LEVEL=DEBUG`. Esto activar&aacute; los logs de `fill_field` y `click_button` para ver exactamente d&oacute;nde se detiene.

---

## 6. Recomendaciones y Fixes Sugeridos

### Fix 1 (P0 - Inmediato): Agregar args de Chromium para contenedor

**Archivo**: `src/autotramite.py:772-774`

```python
# ACTUAL
browser: Browser = await p.chromium.launch(
    headless=settings.playwright_headless,
    slow_mo=settings.playwright_slow_mo
)

# SUGERIDO
browser: Browser = await p.chromium.launch(
    headless=settings.playwright_headless,
    slow_mo=settings.playwright_slow_mo,
    args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
)
```

**Riesgo**: Bajo. `--no-sandbox` es est&aacute;ndar en contenedores. No afecta ejecuci&oacute;n local.

### Fix 2 (P0 - Inmediato): Cambiar `wait_until` de `networkidle` a `domcontentloaded`

**Archivo**: `src/autotramite.py:126`

```python
# ACTUAL
await page.goto(settings.autotramite_login_url, wait_until='networkidle', timeout=settings.timeout_navigation)

# SUGERIDO
await page.goto(settings.autotramite_login_url, wait_until='domcontentloaded', timeout=settings.timeout_navigation)
```

**Tambi&eacute;n en l&iacute;nea 173** (formulario):
```python
await page.goto(settings.autotramite_form_url, wait_until='domcontentloaded', timeout=settings.timeout_navigation)
```

**Riesgo**: Bajo. Los campos del formulario se esperan con `wait_for_selector` despu&eacute;s, que es m&aacute;s robusto.

### Fix 3 (P1 - Recomendado): Aumentar timeouts para Railway

**En Railway environment variables**:
```
TIMEOUT_NAVIGATION=60000
TIMEOUT_ELEMENT=20000
```

**Riesgo**: Nulo. Solo afecta tiempos de espera.

### Fix 4 (P1 - Recomendado): Usar Dockerfile en lugar de Nixpacks

**Archivo**: `railway.json`

```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "bash -lc 'unset STREAMLIT_SERVER_PORT; exec streamlit run app.py --server.address 0.0.0.0 --server.port \"${PORT}\" --server.headless true'",
    "healthcheckPath": "/",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

**Riesgo**: Medio. El Dockerfile ya existe y est&aacute; probado. Requiere rebuild completo.

### Fix 5 (P1 - Diagn&oacute;stico): Agregar logging granular al login

**Archivo**: `src/autotramite.py`, funci&oacute;n `login_autotramite()`

Agregar logs antes de cada operaci&oacute;n:

```python
async def login_autotramite(page: Page) -> None:
    logger.info('Iniciando login en AutoTramite')

    try:
        logger.info(f'Navegando a {settings.autotramite_login_url}...')
        await page.goto(settings.autotramite_login_url, wait_until='domcontentloaded', timeout=settings.timeout_navigation)
        logger.info(f'Pagina cargada. URL: {page.url}, Status: OK')

        logger.info('Llenando campo email...')
        await fill_field(page, SELECTORS['login_email'], settings.autotramite_email)
        logger.info('Email llenado OK')

        logger.info('Llenando campo password...')
        await fill_field(page, SELECTORS['login_password'], settings.autotramite_password)
        logger.info('Password llenado OK')

        logger.info('Clickeando boton login...')
        await click_button(page, SELECTORS['login_submit'], wait_navigation=True)
        logger.info(f'Click OK. URL actual: {page.url}')

        # ... resto igual
```

**Riesgo**: Nulo. Solo agrega informaci&oacute;n de diagn&oacute;stico.

### Fix 6 (P2 - Opcional): Agregar logging al launch del browser

**Archivo**: `src/autotramite.py`, funci&oacute;n `crear_contrato_autotramite()`

```python
logger.info('Lanzando Chromium...', extra={
    'headless': settings.playwright_headless,
    'slow_mo': settings.playwright_slow_mo
})
browser: Browser = await p.chromium.launch(...)
logger.info('Chromium lanzado exitosamente')

page: Page = await browser.new_page()
logger.info('Nueva pagina creada')
```

---

## 7. Plan de Acci&oacute;n Recomendado

### Paso 1: Diagn&oacute;stico r&aacute;pido (sin cambios de c&oacute;digo)
1. Verificar que `AUTOTRAMITE_EMAIL` y `AUTOTRAMITE_PASSWORD` est&aacute;n en Railway env vars
2. Agregar `LOG_LEVEL=DEBUG` en Railway env vars
3. Ejecutar y revisar logs para ver exactamente d&oacute;nde se detiene

### Paso 2: Fix m&iacute;nimo (cambios de c&oacute;digo m&iacute;nimos)
1. Agregar `args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']` al browser launch
2. Cambiar `wait_until='networkidle'` a `wait_until='domcontentloaded'` en login y formulario
3. Deploy y probar

### Paso 3: Si persiste
1. Agregar logging granular (Fix 5)
2. Aumentar timeouts v&iacute;a env vars (Fix 3)
3. Considerar cambiar a Dockerfile builder (Fix 4)

### Paso 4: Si es bloqueo geogr&aacute;fico
1. Ejecutar Test B (curl headers) desde Railway
2. Si se confirma bloqueo, evaluar opciones:
   - Proxy/VPN chileno en Railway
   - Deploy en infraestructura en Chile
   - Contactar autotramite.cl para whitelist de IP

---

## Ap&eacute;ndice A: Archivos Relevantes

| Archivo | L&iacute;neas Clave | Rol |
|---------|--------------|-----|
| `src/autotramite.py` | 111-151 (login), 746-813 (main), 693-743 (retry) | L&oacute;gica de automatizaci&oacute;n |
| `src/config.py` | 22-25 (timeouts), 36-37 (playwright config) | Configuraci&oacute;n y selectores |
| `run_autotramite_cli.py` | 82-89 (asyncio.run) | CLI wrapper para subprocess |
| `app.py` | 1413-1427 (subprocess call) | Invocaci&oacute;n desde UI |
| `railway.json` | 4-6 (build), 7-13 (deploy) | Config Railway |
| `Dockerfile` | 10-33 (system deps), 36-37 (playwright install) | Container build (NO usado actualmente) |
| `start.sh` | 1-21 (dual startup) | Referenciado en Dockerfile CMD |

## Ap&eacute;ndice B: Flujo de Ejecuci&oacute;n Completo

```
[Usuario en Streamlit UI]
    |
    v
[app.py:1413] subprocess.run(run_autotramite_cli.py)
    |
    v
[run_autotramite_cli.py:83] asyncio.run(crear_contrato_autotramite())
    |
    v
[autotramite.py:771] async_playwright() -> chromium.launch()   <-- H1: puede fallar aqui sin --no-sandbox
    |
    v
[autotramite.py:781] ejecutar_con_reintentos(login_autotramite)
    |
    v
[autotramite.py:126] page.goto(login_url, wait_until='networkidle')  <-- H2: puede colgar aqui
    |
    v
[autotramite.py:129-130] fill_field(email), fill_field(password)
    |
    v
[autotramite.py:133] click_button(login_submit, wait_navigation=True)
    |
    v
[autotramite.py:136-140] Verificar URL (login exitoso o fallido)
```
