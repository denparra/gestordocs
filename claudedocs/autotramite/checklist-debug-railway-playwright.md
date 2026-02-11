# Checklist: Debug Playwright/AutoTramite en Railway

**Uso**: Ejecutar paso a paso para diagnosticar y resolver el timeout de login en Railway.
**Fecha**: 2026-02-10

---

## Fase 1: Verificaci&oacute;n de Variables de Entorno

- [ ] **1.1** Verificar en Railway Dashboard > Variables que existen:
  - `AUTOTRAMITE_EMAIL` (con valor correcto, incluyendo `@`)
  - `AUTOTRAMITE_PASSWORD` (con valor correcto)
- [ ] **1.2** Agregar/verificar estas variables adicionales:
  - `PLAYWRIGHT_HEADLESS=True`
  - `LOG_LEVEL=DEBUG` (temporal, para diagn&oacute;stico)
- [ ] **1.3** Verificar que NO existe `PLAYWRIGHT_HEADLESS=False` (esto intentar&iacute;a abrir GUI en servidor)

---

## Fase 2: Verificaci&oacute;n del Build

- [ ] **2.1** Revisar Railway Build Logs para confirmar:
  - `playwright install chromium --with-deps` ejecut&oacute; sin errores
  - No hay warnings de libs faltantes (`libnss3`, `libatk`, `libgbm`, etc.)
- [ ] **2.2** Verificar builder actual en `railway.json`:
  - Si es `NIXPACKS`: considerar cambiar a `DOCKERFILE` (ver Fase 5)
  - Si es `DOCKERFILE`: verificar que instala todas las system deps
- [ ] **2.3** Verificar que Chromium binary est&aacute; disponible:
  ```bash
  # En Railway CLI o shell
  npx playwright install --dry-run chromium
  # o
  python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); print(p.chromium.executable_path); p.stop()"
  ```

---

## Fase 3: Verificaci&oacute;n de Conectividad

- [ ] **3.1** Probar conectividad HTTP desde Railway:
  ```bash
  curl -sS -o /dev/null -w "HTTP:%{http_code} DNS:%{time_namelookup}s CONNECT:%{time_connect}s TOTAL:%{time_total}s\n" \
    https://autotramite.cl/secciones/login.php
  ```
  - **Esperado**: HTTP:200, TOTAL < 5s
  - **Problema si**: HTTP:403/503, TOTAL > 10s, o connection refused
- [ ] **3.2** Verificar headers de respuesta (WAF/CloudFlare):
  ```bash
  curl -I https://autotramite.cl/secciones/login.php
  ```
  - **Buscar**: `server: cloudflare`, `cf-ray`, `cf-chl-bypass`, redirects a challenge
- [ ] **3.3** Verificar DNS:
  ```bash
  nslookup autotramite.cl
  dig autotramite.cl
  ```

---

## Fase 4: Verificaci&oacute;n de Chromium Launch

- [ ] **4.1** Probar launch b&aacute;sico de Chromium en Railway:
  ```python
  import asyncio
  from playwright.async_api import async_playwright

  async def test_launch():
      print("Launching browser...")
      async with async_playwright() as p:
          browser = await p.chromium.launch(
              headless=True,
              args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
          )
          print(f"Browser launched: {browser.version}")
          page = await browser.new_page()
          print("Page created")

          print("Navigating to autotramite.cl...")
          try:
              resp = await page.goto(
                  'https://autotramite.cl/secciones/login.php',
                  wait_until='domcontentloaded',
                  timeout=60000
              )
              print(f"Status: {resp.status}")
              print(f"URL: {page.url}")

              # Check for blocking
              content = await page.content()
              for keyword in ['captcha', 'challenge', 'cloudflare', 'blocked', 'forbidden']:
                  if keyword in content.lower():
                      print(f"WARNING: Found '{keyword}' in page content!")

              # Check login form exists
              email_field = await page.query_selector('#Correo')
              print(f"Email field found: {email_field is not None}")

          except Exception as e:
              print(f"Navigation error: {e}")
          finally:
              await browser.close()
              print("Browser closed")

  asyncio.run(test_launch())
  ```
- [ ] **4.2** Si el test anterior falla con sandbox error, confirmar que `--no-sandbox` es necesario
- [ ] **4.3** Verificar `/dev/shm` size:
  ```bash
  df -h /dev/shm
  ```
  - **Problema si**: < 64MB (Chromium necesita m&aacute;s)

---

## Fase 5: Fixes Progresivos

### Fix A: Browser Launch Args (Riesgo: Bajo)

**Archivo**: `src/autotramite.py:772-774`

Cambiar:
```python
browser = await p.chromium.launch(
    headless=settings.playwright_headless,
    slow_mo=settings.playwright_slow_mo,
    args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
)
```

- [ ] **5.1** Aplicar Fix A
- [ ] **5.2** Deploy y probar

### Fix B: Cambiar wait_until (Riesgo: Bajo)

**Archivo**: `src/autotramite.py:126` y `src/autotramite.py:173`

Cambiar `wait_until='networkidle'` a `wait_until='domcontentloaded'`

- [ ] **5.3** Aplicar Fix B
- [ ] **5.4** Deploy y probar

### Fix C: Aumentar Timeouts (Riesgo: Nulo)

**En Railway env vars**:
```
TIMEOUT_NAVIGATION=60000
TIMEOUT_ELEMENT=20000
```

- [ ] **5.5** Aplicar Fix C
- [ ] **5.6** Deploy y probar

### Fix D: Cambiar a Dockerfile (Riesgo: Medio)

**Archivo**: `railway.json`

```json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  }
}
```

- [ ] **5.7** Aplicar Fix D (solo si A+B+C no resuelven)
- [ ] **5.8** Rebuild completo y probar

---

## Fase 6: Logging Mejorado (si persiste)

- [ ] **6.1** Agregar logs antes/despu&eacute;s de cada operaci&oacute;n en `login_autotramite()`:
  ```
  [INFO] Navegando a login.php...
  [INFO] Pagina cargada (Xms). URL: ...
  [INFO] Llenando email...
  [INFO] Email OK. Llenando password...
  [INFO] Password OK. Click login...
  [INFO] Login click OK. URL final: ...
  ```
- [ ] **6.2** Agregar log de tiempo transcurrido:
  ```python
  import time
  t0 = time.time()
  await page.goto(...)
  logger.info(f'goto completed in {time.time()-t0:.2f}s')
  ```
- [ ] **6.3** Revisar Railway Deploy Logs para el nuevo output

---

## Fase 7: Si es Bloqueo Geogr&aacute;fico

- [ ] **7.1** Confirmar bloqueo con Test B (Fase 3.2)
- [ ] **7.2** Opciones:
  - Contactar autotramite.cl para whitelist de IP Railway
  - Configurar proxy SOCKS5 chileno
  - Desplegar en VPS en Chile (DigitalOcean/Linode Santiago)
  - Usar Railway con proxy configurado:
    ```python
    browser = await p.chromium.launch(
        proxy={'server': 'socks5://proxy-chile:1080'}
    )
    ```

---

## Tabla R&aacute;pida de Referencia

| S&iacute;ntoma | Causa Probable | Fix |
|----------|---------------|-----|
| Timeout en `page.goto()` | `networkidle` + alta latencia | Fix B |
| Chromium crash silencioso | Falta `--no-sandbox` | Fix A |
| Timeout en `fill_field()` | Chromium no carg&oacute; la p&aacute;gina | Fix A + B |
| HTTP 403 desde curl | WAF/GeoIP blocking | Fase 7 |
| OOM kill en Railway | Chromium sin mem | Fix A (`--disable-dev-shm-usage`) + escalar plan |
| Build fails Playwright | Libs faltantes | Fix D (Dockerfile) |

---

## Resultado Esperado

Tras aplicar Fix A + Fix B + Fix C:
- Chromium lanza correctamente en contenedor Linux
- La navegaci&oacute;n no espera `networkidle` innecesariamente
- Los timeouts dan margen suficiente para latencia intercontinental
- Los logs con `LOG_LEVEL=DEBUG` muestran exactamente d&oacute;nde ocurre cualquier problema residual
