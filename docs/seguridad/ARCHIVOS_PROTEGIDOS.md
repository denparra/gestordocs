# 🛡️ Archivos Protegidos por .gitignore

Este documento explica qué archivos están protegidos y **por qué NO deben subirse a Git**.

---

## 🚨 ARCHIVOS CRÍTICOS (Seguridad)

### 1. `.env`
**Riesgo**: ⚠️ **CRÍTICO**

**Contiene**:
```ini
AUTOTRAMITE_EMAIL=dparra@queirolo.cl
AUTOTRAMITE_PASSWORD=*********
SMTP_HOST=mail.queirolo.cl
SMTP_USER=dparra@queirolo.cl
SMTP_PASS=*********
```

**Por qué está protegido**:
- Credenciales de acceso a AutoTramite.cl
- Credenciales SMTP (servidor de correo)
- Si se filtra, cualquiera puede acceder al sistema

**Qué hacer**:
- ✅ Usar `.env.example` como plantilla (sin credenciales reales)
- ✅ Cada desarrollador crea su propio `.env` local
- ❌ NUNCA hacer commit de `.env`

---

## 📧 DATOS DE CLIENTES

### 2. `docs/correo-cierre/enviados/`
**Riesgo**: ⚠️ **ALTO**

**Contiene**:
```json
{
  "email_destinatario": "cliente@email.com",
  "cc_addresses": ["dparra@queirolo.cl"],
  "datos_propietario": "Nombre: JUAN PEREZ...",
  "vehiculo": "HYUNDAI GRAND I10...",
  "precio": "$5.000.000"
}
```

**Por qué está protegido**:
- Datos personales de clientes (nombres, emails, RUTs)
- Información comercial sensible (precios acordados)
- Ley de Protección de Datos Personales (Ley 19.628)

**Qué hacer**:
- ✅ Mantener en servidor de producción únicamente
- ✅ Hacer backups encriptados si es necesario
- ❌ NUNCA subir a repositorio público o privado

---

## 📸 SCREENSHOTS

### 3. `screenshots/` y `docs/autotramite/screenshots/`
**Riesgo**: ⚠️ **MEDIO**

**Contiene**:
- Screenshots del sistema con datos de prueba
- PDFs de contratos de ejemplo
- Archivos de resultado con patentes y RUTs

**Por qué está protegido**:
- Pueden contener datos reales accidentalmente
- Ocupan espacio innecesario en el repositorio
- Información técnica que puede ser sensible

**Qué hacer**:
- ✅ Usar screenshots genéricos en documentación
- ✅ Ofuscar datos sensibles antes de compartir
- ❌ No incluir screenshots con datos reales

---

## 📝 LOGS

### 4. `*.log` y `autotramite.log`
**Riesgo**: ⚠️ **MEDIO**

**Contiene**:
```
[2026-02-05 20:11:34] Email enviado a: cliente@email.com
[2026-02-05 20:11:34] RUT ofuscado: 12.XXX.XXX-X
[2026-02-05 20:11:34] Vehículo: HYUNDAI GRAND I10 KLCV.24-0
```

**Por qué está protegido**:
- Puede contener emails, RUTs, patentes
- Stack traces con rutas del sistema
- Información de debugging con datos reales

**Qué hacer**:
- ✅ Revisar logs localmente para debugging
- ✅ Limpiar logs periódicamente
- ❌ No subir logs a Git

---

## 🐍 ARCHIVOS TÉCNICOS

### 5. `.venv/`, `__pycache__/`, `.pytest_cache/`
**Riesgo**: ✅ **BAJO** (No sensibles, pero innecesarios)

**Por qué están protegidos**:
- Virtual environment (`.venv/`) es específico de cada máquina
- Cache de Python (`__pycache__/`) se regenera automáticamente
- Cache de pytest se regenera al ejecutar tests
- Ocupan mucho espacio en el repositorio

**Qué hacer**:
- ✅ Cada desarrollador crea su propio `.venv`
- ✅ Python regenera cache automáticamente
- ❌ No versionar archivos generados

---

## 💻 IDE Y SISTEMA

### 6. `.vscode/`, `.idea/`, `.DS_Store`
**Riesgo**: ✅ **BAJO**

**Por qué están protegidos**:
- Configuraciones personales de cada desarrollador
- Pueden contener rutas absolutas del sistema
- No son necesarios para el proyecto

---

## ⚠️ ARCHIVOS YA TRACKEADOS (Requieren Acción)

Los siguientes archivos **ya están en Git** y deben ser removidos:

```
.env                                                    # ⚠️ CRÍTICO
autotramite.log                                         # ⚠️ MEDIO
docs/correo-cierre/enviados/*.json                      # ⚠️ ALTO
docs/autotramite/screenshots/*                          # ⚠️ MEDIO
screenshots/*.png                                       # ⚠️ BAJO
```

### 🔧 Cómo removerlos del historial de Git

**Opción 1: Remover solo del índice** (los archivos quedan en disco)
```bash
# Remover archivos sensibles del staging
git rm --cached .env
git rm --cached autotramite.log
git rm --cached -r docs/correo-cierre/enviados/
git rm --cached -r docs/autotramite/screenshots/
git rm --cached -r screenshots/

# Hacer commit
git add .gitignore
git commit -m "🔒 Agregar .gitignore y remover archivos sensibles

- Proteger credenciales (.env)
- Proteger historial de emails (enviados/)
- Proteger logs con datos sensibles
- Proteger screenshots con información técnica
- Mantener .env.example como referencia"
```

**Opción 2: Limpiar historial completo** (si ya se hizo push)
```bash
# ⚠️ CUIDADO: Esto reescribe el historial de Git
# Solo usar si el .env ya se subió al repositorio remoto

# Instalar BFG Repo-Cleaner
# https://rtyley.github.io/bfg-repo-cleaner/

# Remover .env del historial
bfg --delete-files .env

# Limpiar y hacer push forzado
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

---

## ✅ Checklist de Seguridad

Antes de hacer commit, verifica:

- [ ] `.env` NO está en staging (`git status` no debe mostrarlo)
- [ ] `docs/correo-cierre/enviados/` NO está en staging
- [ ] No hay archivos `.log` en staging
- [ ] Screenshots con datos reales NO están incluidos
- [ ] `.gitignore` está presente y actualizado

---

## 📚 Referencias

- **Ley 19.628** - Protección de Datos Personales (Chile)
- **OWASP** - Secrets Management Best Practices
- **Git Security** - https://git-scm.com/book/en/v2/Git-Tools-Credential-Storage

---

## 🆘 Si Accidentalmente Subes Archivos Sensibles

1. **NO HAGAS PANIC** - El daño es reversible si actúas rápido
2. **Revoca credenciales** - Cambia todas las contraseñas del `.env` inmediatamente
3. **Remueve del historial** - Usa BFG o `git filter-branch`
4. **Notifica al equipo** - Informa a todos que deben cambiar credenciales
5. **Haz force push** - Reescribe el historial remoto (solo si tienes permisos)

---

**Última actualización**: 2026-02-05
**Responsable**: Dennys Parra (dparra@queirolo.cl)
