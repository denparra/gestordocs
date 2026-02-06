# Cómo Editar el Email de Cierre

## 📍 Ubicación del Archivo

**Archivo a editar**: `docs/correo-cierre/plantilla.md`

Este archivo contiene el texto del email que se envía a los clientes.

## 🔧 Cómo Editar

### 1. Abre el archivo

```bash
# Con Notepad
notepad docs/correo-cierre/plantilla.md

# Con VS Code
code docs/correo-cierre/plantilla.md

# O cualquier editor de texto
```

### 2. Edita el texto que quieras

**IMPORTANTE**: No toques las palabras entre llaves `{...}` - son placeholders que se reemplazan automáticamente:

| Placeholder | Se reemplaza con |
|-------------|------------------|
| `{NOMBRE_CLIENTE}` | Nombre del cliente (extraído automáticamente) |
| `{VEHICULO}` | Descripción del vehículo |
| `{PRECIO_ACORDADO_CLIENTE}` | Precio acordado |
| `{FECHA_PAGO}` | Rango de fechas de pago |
| `{DATOS_PROPIETARIO_COMPLETOS}` | Bloque completo de datos del propietario |

### 3. Ejemplos de Modificaciones

#### Ejemplo 1: Cambiar el saludo

**Antes**:
```
Buenas tardes estimados {NOMBRE_CLIENTE}, la presente es para informarle...
```

**Después**:
```
Estimado/a {NOMBRE_CLIENTE}, nos complace informarle...
```

#### Ejemplo 2: Modificar párrafos

**Antes**:
```
según lo conversado con don mario queirolo, agradecemos la confianza depositada
```

**Después**:
```
según lo acordado, agradecemos la confianza en nuestros servicios
```

#### Ejemplo 3: Cambiar instrucciones

**Antes**:
```
1. UNA VEZ CONFIRMADO FONDOS EN CUENTA, PROCEDEMOS A FIRMAR CONTRATOS...
```

**Después**:
```
1. Una vez confirmado el pago, procederemos a firmar los contratos...
```

#### Ejemplo 4: Agregar nuevos párrafos

Puedes agregar texto en cualquier parte:

```
Buenas tardes estimados {NOMBRE_CLIENTE}, la presente es para informarle...

RECORDATORIO: Por favor traer su cédula de identidad vigente.  ← NUEVO

{PRECIO_ACORDADO_CLIENTE}
```

### 4. Guarda el archivo

- **Ctrl+S** en el editor
- Cierra el archivo

### 5. Reinicia Streamlit (IMPORTANTE)

Para que los cambios surtan efecto:

```bash
# En la terminal donde está corriendo Streamlit:
Ctrl+C

# Reiniciar
streamlit run app.py
```

## ⚠️ Qué NO Hacer

### ❌ NO modifiques los placeholders

**MAL**:
```
Buenas tardes {nombre_cliente}  ← Incorrecto (minúsculas)
```

**BIEN**:
```
Buenas tardes {NOMBRE_CLIENTE}  ← Correcto (mayúsculas)
```

### ❌ NO agregues ejemplos entre corchetes

**MAL**:
```
{NOMBRE_CLIENTE} [EJEMPLO: "JUAN PEREZ"]  ← Se enviará en el email!
```

**BIEN**:
```
{NOMBRE_CLIENTE}  ← Solo el placeholder
```

### ❌ NO uses etiquetas HTML

**MAL**:
```
<b>IMPORTANTE</b>  ← No funciona, es texto plano
```

**BIEN**:
```
IMPORTANTE  ← Texto plano
```

## 📝 Formato del Email

El email se envía como **texto plano**, por lo que:

- ✅ Saltos de línea se respetan
- ✅ Mayúsculas/minúsculas se respetan
- ✅ Espacios y tabulaciones se respetan
- ❌ HTML NO funciona (sin negritas, colores, etc.)

## 🎨 Personalización de la Firma

La firma está al final del archivo:

```
Dennys Parra
Ejecutivo de Ventas
+569 7540 0946
Av. Las condes 12461, Local 4A. Las condes
www.queirolo.cl

Mas de 60 años en tu camino.
```

Puedes cambiar:
- Nombre
- Cargo
- Teléfono
- Dirección
- Sitio web
- Eslogan final

## 🔄 Plantillas Múltiples (Futuro)

Si necesitas **diferentes versiones** del email (ej: clientes premium, clientes estándar):

1. Crea copias de `plantilla.md`:
   - `plantilla_premium.md`
   - `plantilla_estandar.md`

2. Edita `mail_config.yaml`:
   ```yaml
   plantillas:
     default: "plantilla.md"
     alternativas:
       - nombre: "Premium"
         archivo: "plantilla_premium.md"
       - nombre: "Estándar"
         archivo: "plantilla_estandar.md"
   ```

*(Nota: Esta funcionalidad requiere modificación del código - actualmente solo usa `plantilla.md`)*

## ✅ Checklist de Edición

Después de editar, verifica:

1. ✅ Los placeholders `{NOMBRE_CLIENTE}`, `{VEHICULO}`, etc. están intactos
2. ✅ No hay ejemplos entre corchetes `[EJEMPLO "..."]`
3. ✅ El texto se lee correctamente
4. ✅ La firma tiene tu información correcta
5. ✅ Guardaste el archivo (Ctrl+S)
6. ✅ Reiniciaste Streamlit

## 🧪 Probar los Cambios

1. Reinicia Streamlit
2. Ve a "Mail de Cierre"
3. Llena el formulario con datos de prueba
4. ✅ Marca "Vista previa antes de enviar"
5. Verifica que el email generado tenga los cambios
6. Si todo está bien, envía el correo de prueba a ti mismo

## 📋 Plantilla Actual (Referencia)

Tu plantilla actual tiene esta estructura:

```
1. Saludo con {NOMBRE_CLIENTE}
2. Información del vehículo con {VEHICULO}
3. Precio con {PRECIO_ACORDADO_CLIENTE}
4. Datos completos con {DATOS_PROPIETARIO_COMPLETOS}
5. Fechas con {FECHA_PAGO}
6. Instrucciones importantes (4 puntos)
7. Despedida
8. Firma
```

Puedes modificar cualquier parte excepto los placeholders.

## 🆘 Si Algo Sale Mal

Si después de editar el email no se genera correctamente:

1. **Revisa la consola de Streamlit** - mostrará errores
2. **Verifica los placeholders** - deben estar exactos: `{NOMBRE_CLIENTE}` no `{nombre_cliente}`
3. **Restaura la versión original** - está en este documento más abajo

### Plantilla Original de Respaldo

Si necesitas restaurar, copia esto a `plantilla.md`:

```
Buenas tardes estimados {NOMBRE_CLIENTE}, la presente es para informarle que ya tenemos cierre de su vehículo {VEHICULO}, según lo conversado con don mario queirolo, agradecemos la confianza depositada, ante cualquier información que requiera no dude en llamarnos.

{PRECIO_ACORDADO_CLIENTE}

{DATOS_PROPIETARIO_COMPLETOS}

EN LOS PROXIMOS DIAS ESTAREMOS FINIQUITADO NEGOCIO, FECHA DE PAGO ENTRE {FECHA_PAGO}

IMPORTANTE
1. UNA VEZ CONFIRMADO FONDOS EN CUENTA, PROCEDEMOS A FIRMAR CONTRATOS EL DIA HABIL SIGUIENTE ENTRE 13:30 – 17:00.
2. ENVIEME POR ESTA VIA DATOS BANCARIOS PARA PROCEDER A PAGO EL DIA CORRESPONDIENTE (DATOS BANCARIOS DE DUEÑO DEL AUTO SEGÚN REGISTRO CIVIL).
3. ENVIAR LO SIGUIENTES DATOS PARA PROCESAR TRANSFERENCIA PREVIA RECEPCION DE PAGO.
4. ENVIAR CARNET AMBAS CARAS

De antemano gracias por la confianza depositada al consignar su auto con nosotros.

Dennys Parra
Ejecutivo de Ventas
+569 7540 0946
Av. Las condes 12461, Local 4A. Las condes
www.queirolo.cl

Mas de 60 años en tu camino.
```

---

**¡Listo!** Ahora puedes personalizar el email según tus necesidades. 🎉
