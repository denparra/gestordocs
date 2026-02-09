# 🚂 Guía de Deployment en Railway

## 🔍 Problema: "Session is already connected"

### Diagnóstico

El error:
```
Session with id XXX is already connected! Connecting to a new session.
```

**Causa**: Railway hace healthchecks constantes que crean múltiples sesiones WebSocket de Streamlit.

**Impacto**: No afecta funcionalidad, pero genera ruido en logs.

---

## ✅ SOLUCIONES

### Solución 1: Deshabilitar Healthcheck de Railway (Recomendada)

Railway hace ping constante a tu app para verificar que está viva, pero esto crea sesiones nuevas cada vez.

#### Pasos en Railway Dashboard:

```
1. Ir a tu proyecto en Railway
2. Click en tu servicio → Settings
3. Buscar sección "Health Check"
4. DESHABILITAR: "Enable Health Checks"
5. Click "Save"
6. Redeploy el servicio
```

**Resultado**: Las conexiones duplicadas desaparecen.

---

### Solución 2: Configurar Variables de Entorno

Railway necesita variables de entorno adicionales para Streamlit.

#### Variables Requeridas en Railway:

```env
# === CREDENCIALES AUTOTRAMITE ===
AUTOTRAMITE_EMAIL=dparra@queirolo.cl
AUTOTRAMITE_PASSWORD=tu_password_aqui

# === SMTP CONFIGURATION ===
SMTP_HOST=mail.queirolo.cl
SMTP_PORT=25
SMTP_USER=dparra@queirolo.cl
SMTP_PASS=tu_password_smtp_aqui
SMTP_SECURE=false

# === STREAMLIT CONFIGURATION ===
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_PORT=8501
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# === COOKIE SECRET (Genera con comando abajo) ===
STREAMLIT_SERVER_COOKIE_SECRET=tu_secret_token_de_64_caracteres_aqui

# === LOGGING ===
LOG_LEVEL=INFO

# === PLAYWRIGHT (Opcional) ===
PLAYWRIGHT_HEADLESS=true
```

#### ¿Cómo agregar variables en Railway?

```
1. Railway Dashboard → Tu Proyecto
2. Click en servicio → Variables
3. Click "+ New Variable"
4. Agregar cada variable (nombre + valor)
5. Click "Save" después de todas
6. Redeploy automático
```

---

### Solución 3: Generar Cookie Secret

El `STREAMLIT_SERVER_COOKIE_SECRET` previene sesiones duplicadas.

#### Opción A: Desde Python
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

#### Opción B: Desde OpenSSL
```bash
openssl rand -hex 32
```

Copia el resultado y agrégalo como variable de entorno en Railway:
```
STREAMLIT_SERVER_COOKIE_SECRET=abc123def456...
```

---

### Solución 4: Optimizar Comando de Inicio

Railway debe usar este comando para iniciar Streamlit:

#### En railway.json (ya creado):
```json
{
  "deploy": {
    "startCommand": "streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true"
  }
}
```

#### O manualmente en Railway:
```
Railway → Settings → Deploy → Start Command:

streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

---

## 📋 CHECKLIST DE DEPLOYMENT

### Pre-Deployment

```
✅ Archivo .streamlit/config.toml creado
✅ Archivo railway.json creado
✅ Variables de entorno configuradas en Railway
✅ STREAMLIT_SERVER_COOKIE_SECRET generado
✅ Credenciales de producción verificadas
✅ Health Check deshabilitado en Railway
```

### Post-Deployment

```
✅ App se despliega sin errores
✅ Logs no muestran "Session already connected"
✅ AutoTramite funciona correctamente
✅ Mail de Cierre funciona correctamente
✅ Tags funciona correctamente
```

---

## 🛠️ TROUBLESHOOTING

### Error: "Application failed to respond"

**Causa**: Puerto incorrecto o app no inicia.

**Solución**:
```bash
# Verificar que app.py inicia localmente
streamlit run app.py --server.port=8501 --server.address=0.0.0.0

# Si funciona local, verificar en Railway:
# - Variable PORT está configurada ($PORT en startCommand)
# - No hay errores en Build Logs
```

---

### Error: "ModuleNotFoundError"

**Causa**: Dependencias no instaladas.

**Solución**:
```bash
# Verificar requirements.txt tiene todas las dependencias
cat requirements.txt

# Debe incluir:
streamlit>=1.28.0
playwright>=1.40.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
PyYAML>=6.0
python-dotenv>=1.0.0

# En Railway, rebuild:
Railway → Settings → Redeploy
```

---

### Error: "Playwright chromium not found"

**Causa**: Playwright browser no instalado en build.

**Solución**:
```json
// Verificar railway.json tiene:
{
  "build": {
    "buildCommand": "pip install -r requirements.txt && playwright install chromium --with-deps"
  }
}
```

O configurar en Railway:
```
Settings → Build Command:
pip install -r requirements.txt && playwright install chromium --with-deps
```

---

### Logs muestran "Session already connected" constantemente

**Solución definitiva**:

1. **Opción A**: Deshabilitar Health Checks (Recomendado)
   ```
   Railway → Settings → Health Check → OFF
   ```

2. **Opción B**: Configurar Cookie Secret
   ```bash
   # Generar
   python -c "import secrets; print(secrets.token_hex(32))"

   # Agregar a Railway Variables:
   STREAMLIT_SERVER_COOKIE_SECRET=resultado_del_comando
   ```

3. **Opción C**: Ignorar (no afecta funcionalidad)
   - Los logs son solo informativos
   - La app funciona normalmente
   - Filtrar logs en Railway si molesta

---

## 📊 MONITOREO

### Ver Logs en Railway

```
1. Railway Dashboard → Tu Proyecto
2. Click en servicio
3. Tab "Deployments"
4. Click en deployment activo
5. Ver "Build Logs" y "Deploy Logs"
```

### Filtrar Logs de Sesión

```bash
# Si quieres filtrar estos logs localmente
grep -v "Session with id" logs.txt
```

### Logs Importantes

```
✅ BUENO:
- "Streamlit is running on port 8501"
- "You can now view your Streamlit app in your browser"
- "Email enviado exitosamente"

⚠️ ADVERTENCIA:
- "Session with id XXX is already connected"  # No crítico
- "Retrying login after timeout"              # Normal

❌ ERROR:
- "LoginFailedError: Credenciales inválidas"
- "ModuleNotFoundError"
- "Application failed to respond"
```

---

## 🔐 SEGURIDAD EN RAILWAY

### Variables de Entorno

```
✅ HACER:
- Usar variables de entorno para credenciales
- Generar cookie secret único
- No hardcodear passwords en código

❌ NO HACER:
- Subir .env a Git (ya está en .gitignore)
- Compartir cookie secret públicamente
- Usar credenciales de desarrollo en producción
```

### Secrets Management

Railway encripta automáticamente las variables de entorno.

```
Verificar:
1. Railway → Settings → Variables
2. Valores están ocultos (*****)
3. Solo se muestran completos al editar
```

---

## 🚀 PROCESO DE DEPLOYMENT

### Deployment Automático (Recomendado)

```
1. Hacer push a GitHub:
   git add .
   git commit -m "feat: configuración Railway"
   git push origin main

2. Railway detecta cambios automáticamente
3. Inicia build y deploy
4. App actualizada en ~3-5 minutos
```

### Deployment Manual

```
1. Railway Dashboard → Tu Proyecto
2. Click "Deploy Now"
3. Esperar build (2-4 min)
4. Verificar logs
```

---

## 📈 OPTIMIZACIONES

### 1. Cachear Dependencias

Railway cachea automáticamente, pero puedes optimizar:

```dockerfile
# railway.json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install --cache-dir=/tmp/pip-cache -r requirements.txt && playwright install chromium --with-deps"
  }
}
```

### 2. Reducir Tamaño de Build

```bash
# En requirements.txt, especificar versiones exactas:
streamlit==1.28.0  # No >=1.28.0
playwright==1.40.0
```

### 3. Optimizar Playwright

```bash
# Solo instalar Chromium (no Firefox, WebKit)
playwright install chromium --with-deps
```

---

## 🆘 SOPORTE

### Logs de Error Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| Session already connected | Healthcheck activo | Deshabilitar healthcheck |
| Port already in use | Puerto hardcodeado | Usar $PORT variable |
| Chromium not found | Playwright no instalado | Agregar a buildCommand |
| Invalid credentials | .env no configurado | Configurar variables Railway |
| Module not found | requirements.txt incompleto | Agregar dependencia faltante |

### Links Útiles

- **Railway Docs**: https://docs.railway.app/
- **Streamlit Docs**: https://docs.streamlit.io/
- **Playwright Docs**: https://playwright.dev/python/

---

## 📝 CHANGELOG

### 2026-02-05
- Configuración inicial de Railway
- Solución para sesiones duplicadas
- Documentación completa de deployment

---

**Autor**: Claude Code
**Última actualización**: 2026-02-05
