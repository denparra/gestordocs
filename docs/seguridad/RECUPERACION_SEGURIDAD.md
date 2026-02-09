# 🚨 Procedimiento de Recuperación de Seguridad

## Situación

El archivo `.env` con credenciales fue subido accidentalmente a Git y GitHub.

**Repositorio**: https://github.com/denparra/gestordocs.git
**Commits afectados**: 78d3f9e, e2d993d
**Credenciales expuestas**:
- Email: dparra@queirolo.cl
- Contraseña AutoTramite
- Contraseña SMTP (mail.queirolo.cl)

---

## ⚠️ NIVEL DE URGENCIA

| Tipo de Repositorio | Gravedad | Acción Requerida |
|---------------------|----------|------------------|
| **Público** | 🔴 CRÍTICA | Cambiar credenciales INMEDIATAMENTE |
| **Privado** | 🟡 ALTA | Cambiar credenciales en 24 horas |

---

## 📋 PLAN DE ACCIÓN (5 pasos)

### PASO 1: CAMBIAR CREDENCIALES (URGENTE) ⏰ 30 minutos

**NO CONTINÚES sin cambiar las contraseñas primero**

#### 1.1 Contraseña de AutoTramite

```
✅ Ir a: https://autotramite.cl
✅ Login con: dparra@queirolo.cl
✅ Menú → Configuración → Cambiar Contraseña
✅ Nueva contraseña: [GENERAR CONTRASEÑA FUERTE]
✅ Anotar nueva contraseña en lugar seguro
```

#### 1.2 Contraseña SMTP

```
Opción A: Panel de Control de Email
✅ Ir a: Panel de administración de mail.queirolo.cl
✅ Buscar cuenta: dparra@queirolo.cl
✅ Cambiar contraseña

Opción B: Contactar Administrador
✅ Contactar a: [Administrador de IT de Queirolo]
✅ Solicitar: "Cambio de contraseña SMTP para dparra@queirolo.cl"
✅ Motivo: "Exposición accidental en repositorio Git"
```

#### 1.3 Actualizar .env Local

```bash
# Editar .env con las NUEVAS credenciales
notepad .env

# Debe contener:
AUTOTRAMITE_EMAIL=dparra@queirolo.cl
AUTOTRAMITE_PASSWORD=[NUEVA_CONTRASEÑA_AUTOTRAMITE]
SMTP_HOST=mail.queirolo.cl
SMTP_PORT=25
SMTP_USER=dparra@queirolo.cl
SMTP_PASS=[NUEVA_CONTRASEÑA_SMTP]
SMTP_SECURE=false
```

**✅ Verificar que el archivo .env ya NO está en Git:**
```bash
git status
# .env NO debe aparecer en la lista
```

---

### PASO 2: LIMPIAR HISTORIAL LOCAL ⏰ 15 minutos

#### Método Recomendado: git filter-branch

```bash
# 1. Hacer backup por seguridad
cd ..
xcopy /E /I autotramite_py_mvp autotramite_py_mvp_BACKUP
cd autotramite_py_mvp

# 2. Limpiar .env del historial
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch .env" --prune-empty --tag-name-filter cat -- --all

# Verás algo como:
# Rewrite 78d3f9e... (1/2)
# Rewrite e2d993d... (2/2)
# Ref 'refs/heads/main' was rewritten

# 3. Limpiar referencias viejas
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 4. Verificar que funcionó
git log --all --oneline -- .env
# ⬆️ Debe estar VACÍO (no mostrar nada)
```

**¿Salió error?** Ver sección de Troubleshooting abajo.

---

### PASO 3: LIMPIAR HISTORIAL REMOTO (GitHub) ⏰ 10 minutos

```bash
# Force push para reescribir el historial en GitHub
git push origin --force --all

# También limpia los tags si hay
git push origin --force --tags
```

**⚠️ ADVERTENCIA**: Esto reescribe el historial de GitHub. Si alguien más tiene el repo clonado, deberá hacer:
```bash
git fetch --all
git reset --hard origin/main
```

---

### PASO 4: VERIFICAR LIMPIEZA ⏰ 5 minutos

#### Opción A: Script Automático (Windows)
```bash
docs/seguridad/VERIFICAR_LIMPIEZA.bat
```

#### Opción B: Manual

```bash
# 1. Verificar historial local
git log --all --oneline -- .env
# ⬆️ Debe estar VACÍO

# 2. Verificar historial remoto
git log origin/main --oneline -- .env
# ⬆️ Debe estar VACÍO

# 3. Verificar que .env existe en disco
ls -la .env
# ⬆️ Debe existir (archivo local)

# 4. Verificar .gitignore
cat .gitignore | grep "^\.env$"
# ⬆️ Debe mostrar: .env

# 5. Verificar git status
git status
# ⬆️ .env NO debe aparecer
```

**✅ Si todos los pasos pasan: LIMPIEZA EXITOSA**

---

### PASO 5: VERIFICAR EN GITHUB ⏰ 5 minutos

```
1. Ir a: https://github.com/denparra/gestordocs
2. Buscar: Presionar "t" y escribir ".env"
3. Resultado esperado: "No matches found"
4. Verificar commits: Ver historial de commits
5. Buscar en commits: .env NO debe aparecer
```

**Si aún aparece .env en GitHub:**
- Espera 5-10 minutos (caché de GitHub)
- Refresca la página con Ctrl+F5
- Si persiste, repite PASO 3

---

## 🛠️ TROUBLESHOOTING

### Error: "Cannot rewrite branch"
```bash
# Solución: Quitar protección de branch
git config --unset branch.main.remote
git filter-branch --force ...
```

### Error: "fatal: ambiguous argument 'origin/main'"
```bash
# Solución: Crear referencia remota
git fetch origin
git branch --set-upstream-to=origin/main main
```

### Error: "refusing to allow an OAuth App to create or update workflow"
```bash
# Solución: Usar token de acceso personal
# 1. GitHub → Settings → Developer settings → Personal access tokens
# 2. Generar nuevo token con scope "repo"
# 3. Usar token en push:
git push https://[TOKEN]@github.com/denparra/gestordocs.git --force --all
```

### .env sigue apareciendo en GitHub después de 30 minutos
```bash
# GitHub puede tener caché agresivo
# Solución: Contactar GitHub Support
# https://support.github.com/contact
# Explicar: "Accidentally pushed credentials, need cache purge"
```

---

## 📊 CHECKLIST DE SEGURIDAD POST-RECUPERACIÓN

```
✅ Contraseña de AutoTramite cambiada
✅ Contraseña SMTP cambiada
✅ .env actualizado con nuevas credenciales
✅ .env removido del historial local (git log vacío)
✅ .env removido de GitHub (búsqueda sin resultados)
✅ .gitignore contiene .env
✅ git status no muestra .env
✅ Script de verificación pasa todos los tests
✅ Otros desarrolladores notificados (si aplica)
✅ Backup del repo limpio guardado
```

---

## 🔐 PREVENCIÓN FUTURA

### 1. Pre-commit Hook

Crea `.git/hooks/pre-commit`:
```bash
#!/bin/bash
if git diff --cached --name-only | grep -q "^\.env$"; then
    echo "❌ ERROR: Intentaste hacer commit de .env"
    echo "🛑 COMMIT BLOQUEADO"
    exit 1
fi
```

```bash
# Hacer ejecutable
chmod +x .git/hooks/pre-commit
```

### 2. Git Secrets

```bash
# Instalar git-secrets
# Windows: choco install git-secrets
# Linux: apt-get install git-secrets

# Configurar
git secrets --install
git secrets --add '.env'
```

### 3. Revisar antes de commit

```bash
# Siempre verificar antes de commit
git status
git diff --cached

# Si ves .env, cancelar con:
git reset HEAD .env
```

---

## 📞 CONTACTOS DE EMERGENCIA

| Situación | Contacto |
|-----------|----------|
| Cambio de contraseña SMTP | Admin IT Queirolo |
| Repositorio comprometido | GitHub Support |
| Consultas de seguridad | [Responsable de Seguridad] |

---

## 📝 REGISTRO DE INCIDENTE

**Fecha del incidente**: 2026-02-05
**Archivo afectado**: `.env`
**Commits afectados**: 78d3f9e, e2d993d
**Repositorio**: https://github.com/denparra/gestordocs.git
**Acción tomada**: [COMPLETAR DESPUÉS DE EJECUTAR]
**Credenciales cambiadas**: [COMPLETAR]
**Historial limpiado**: [COMPLETAR]
**Responsable**: Dennys Parra (dparra@queirolo.cl)

---

## ✅ CONFIRMACIÓN FINAL

Después de completar todos los pasos:

```
YO, [TU NOMBRE], CONFIRMO QUE:

✅ He cambiado todas las credenciales expuestas
✅ He limpiado el historial local de Git
✅ He limpiado el historial remoto en GitHub
✅ He verificado que .env ya no aparece en ningún commit
✅ He actualizado .env local con nuevas credenciales
✅ He instalado protecciones para prevenir futuros incidentes

Fecha: _________________
Firma: _________________
```

---

**Última actualización**: 2026-02-05
**Autor**: Claude Code
**Versión**: 1.0
