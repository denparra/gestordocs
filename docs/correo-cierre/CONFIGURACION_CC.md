# Configuración de CC (Copias Visibles) Predeterminados

## Ubicación de la Configuración

**Archivo**: `docs/correo-cierre/mail_config.yaml`

**Sección**: `cc`

## Opciones de Configuración

### Opción 1: CC Predeterminados FIJOS (Recomendado)

Los emails en CC se agregan **automáticamente** a cada correo enviado. El usuario NO puede modificarlos.

```yaml
cc:
  enabled: true                    # Activar CC predeterminados
  addresses:
    - dparra@queirolo.cl           # ← EDITA AQUÍ tus emails
    - dennys7411@gmail.com
    #- contabilidad@queirolo.cl
  allow_additional: false          # NO permitir agregar más CC en la UI
```

**Resultado en UI**:
```
📋 CC predeterminados (automáticos): admin@queirolo.cl, gerencia@queirolo.cl, contabilidad@queirolo.cl
```

### Opción 2: CC Predeterminados + Permitir Agregar Más

Los emails en CC aparecen pre-llenados en el formulario, pero el usuario puede **agregar más** o **modificarlos**.

```yaml
cc:
  enabled: true                    # Activar CC predeterminados
  addresses:
    - admin@queirolo.cl           # ← EDITA AQUÍ tus emails predeterminados
    - gerencia@queirolo.cl
  allow_additional: true           # Permitir agregar más CC en la UI
```

**Resultado en UI**:
```
CC - Copias Visibles
[admin@queirolo.cl, gerencia@queirolo.cl] ← Usuario puede editar/agregar
```

### Opción 3: Sin CC Predeterminados (Usuario decide)

No hay CC predeterminados. El usuario ingresa manualmente los emails en cada envío.

```yaml
cc:
  enabled: false                   # Desactivar CC predeterminados
  addresses: []
  allow_additional: true
```

**Resultado en UI**:
```
CC - Copias Visibles (opcional)
[                                 ] ← Campo vacío, usuario ingresa
```

## Cómo Editar la Configuración

### 1. Abre el Archivo

```bash
# En VS Code, Notepad++, o cualquier editor de texto
notepad docs/correo-cierre/mail_config.yaml
```

### 2. Encuentra la Sección `cc`

```yaml
# ============================================================================
# COPIAS VISIBLES (CC) - Predeterminados
# ============================================================================
cc:
  enabled: true              # ← Cambiar a true/false
  addresses:
    - admin@queirolo.cl     # ← Editar emails aquí
    - gerencia@queirolo.cl
  allow_additional: true     # ← Cambiar a true/false
```

### 3. Edita los Emails

**Agregar email:**
```yaml
addresses:
  - admin@queirolo.cl
  - gerencia@queirolo.cl
  - ventas@queirolo.cl      # ← Nuevo email
```

**Quitar email:**
```yaml
addresses:
  - admin@queirolo.cl
  # - gerencia@queirolo.cl  ← Comentado (o borrar la línea)
```

**Cambiar email:**
```yaml
addresses:
  - nuevoadmin@queirolo.cl  # ← Email actualizado
  - gerencia@queirolo.cl
```

### 4. Guarda el Archivo

Ctrl+S (guardar) y cierra el editor.

### 5. Reinicia Streamlit

Para que los cambios surtan efecto:

```bash
# En la terminal donde está corriendo Streamlit:
Ctrl+C  (detener)
streamlit run app.py  (reiniciar)
```

## Validación Automática

El sistema valida automáticamente:
- ✅ Formato de email correcto (debe contener @)
- ✅ Emails inválidos son ignorados
- ✅ Duplicados son removidos al enviar

## Ejemplos de Uso

### Ejemplo 1: Gerencia + Administración

Siempre enviar copia a gerencia y admin, sin excepciones:

```yaml
cc:
  enabled: true
  addresses:
    - gerencia@queirolo.cl
    - admin@queirolo.cl
  allow_additional: false    # Usuario NO puede cambiar
```

### Ejemplo 2: Flexible con Predeterminados

Sugerir gerencia, pero permitir agregar otros:

```yaml
cc:
  enabled: true
  addresses:
    - gerencia@queirolo.cl
  allow_additional: true     # Usuario puede agregar ventas@, etc.
```

### Ejemplo 3: Sin Predeterminados

Cada correo decide sus propios CC:

```yaml
cc:
  enabled: false
  addresses: []
  allow_additional: true
```

## Verificar Configuración Actual

### En el Código

```python
from src.mail_utils import cargar_cc_predeterminados, get_config

# Ver CC predeterminados
cc_list = cargar_cc_predeterminados()
print(f"CC predeterminados: {cc_list}")

# Ver si se permite agregar más
allow_add = get_config('cc.allow_additional', True)
print(f"Permitir agregar más: {allow_add}")
```

### En Streamlit UI

Al abrir la card "Mail de Cierre":
- Si hay CC predeterminados fijos: verás un mensaje azul `📋 CC predeterminados (automáticos): ...`
- Si hay CC predeterminados editables: verás el campo pre-llenado con los emails
- Si no hay predeterminados: verás el campo vacío

## Diferencias: CC vs BCC

| Característica | CC (Visible) | BCC (Oculto) |
|----------------|--------------|--------------|
| **Visibilidad** | ✅ Todos ven quién recibió copia | ❌ Nadie ve quién recibió copia |
| **En este sistema** | ✅ Implementado | ❌ Deshabilitado (por diseño) |
| **Uso recomendado** | Copias transparentes (equipo interno) | Copias privadas (auditoría oculta) |
| **Configuración** | `cc.addresses` | `bcc.addresses` (deshabilitado) |

**Decisión de diseño**: Este sistema usa **CC visible** porque:
1. Transparencia con el cliente
2. El equipo interno ve quién más está informado
3. Cumplimiento y auditoría clara

## Troubleshooting

### "Los CC no aparecen en el formulario"

**Verificar**:
1. ¿Está `cc.enabled: true`?
2. ¿Hay emails en `cc.addresses`?
3. ¿Reiniciaste Streamlit después de editar el YAML?

**Solución**:
```bash
# Verificar sintaxis YAML
python -c "import yaml; yaml.safe_load(open('docs/correo-cierre/mail_config.yaml'))"

# Si no hay errores, reiniciar Streamlit
streamlit run app.py
```

### "Email CC inválido: xyz"

**Causa**: Algún email en `cc.addresses` tiene formato incorrecto.

**Solución**: Verificar que todos los emails tengan formato `usuario@dominio.com`

```yaml
# ✅ Correcto
addresses:
  - admin@queirolo.cl

# ❌ Incorrecto
addresses:
  - admin  # Falta @dominio
  - @queirolo.cl  # Falta usuario
```

### "Los cambios no se aplican"

**Causa**: Cache de configuración no se recargó.

**Solución**: Reiniciar Streamlit completamente (Ctrl+C → streamlit run app.py)

## Recomendaciones

✅ **Para empresas**: Usar CC fijos con `allow_additional: false`
✅ **Para flexibilidad**: Usar CC predeterminados con `allow_additional: true`
✅ **Para control total**: Deshabilitar CC predeterminados (`enabled: false`)

⚠️ **IMPORTANTE**: Los emails en CC son **VISIBLES** para todos los destinatarios. Si necesitas copias ocultas, considera implementar BCC (actualmente deshabilitado).

---

**Última actualización**: 2026-02-05
