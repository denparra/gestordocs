# Guía de Migración a Emails HTML

**Versión**: 1.0
**Fecha**: 2026-02-05
**Estado**: Planificación futura (NO implementado actualmente)

---

## 📋 Resumen Ejecutivo

Esta guía explica cómo migrar de emails de **texto plano** a **HTML** para obtener mayor personalización visual (logos, colores, negritas, tablas, etc.).

**Factibilidad**: ✅ **ALTA** - El código actual ya está preparado para soportar HTML
**Esfuerzo**: ⏱️ **BAJO** - 1-2 horas de implementación
**Riesgo**: 🟢 **BAJO** - Cambios menores, compatible con sistema actual

---

## 🎯 Ventajas y Desventajas

### ✅ Ventajas de HTML

| Beneficio | Descripción |
|-----------|-------------|
| **Branding** | Incluir logo de Queirolo, colores corporativos |
| **Legibilidad** | Negritas, colores, tamaños de fuente |
| **Organización** | Tablas para datos estructurados |
| **Profesionalidad** | Apariencia más moderna y formal |
| **Llamadas a acción** | Botones visibles, links destacados |
| **Imágenes** | Logo, firma con foto, iconos |

### ❌ Desventajas de HTML

| Desventaja | Descripción | Mitigación |
|------------|-------------|------------|
| **Spam filters** | Emails HTML pueden ir a spam más fácilmente | Usar HTML limpio, evitar muchas imágenes |
| **Compatibilidad** | Algunos clientes de email no soportan CSS avanzado | Usar HTML simple, CSS inline |
| **Tamaño** | Emails más pesados | Optimizar imágenes, código limpio |
| **Complejidad** | Más difícil de editar | Crear template bien documentado |
| **Accesibilidad** | Lectores de pantalla pueden tener problemas | Incluir versión texto alternativa |

### 🔍 Comparativa

**Email Actual (Texto Plano)**:
```
Buenas tardes estimados PEDRO PARRA,

IMPORTANTE
1. UNA VEZ CONFIRMADO FONDOS...
2. ENVIEME POR ESTA VIA DATOS...

Dennys Parra
Ejecutivo de Ventas
```

**Email HTML (Ejemplo)**:
```html
<div style="font-family: Arial, sans-serif;">
  <img src="logo-queirolo.png" width="200" />

  <p style="font-size: 16px;">
    Buenas tardes estimados <strong>PEDRO PARRA</strong>,
  </p>

  <div style="background: #f8f9fa; padding: 15px;">
    <h3 style="color: #f28f2c;">IMPORTANTE</h3>
    <ol>
      <li>UNA VEZ CONFIRMADO FONDOS...</li>
      <li>ENVIEME POR ESTA VIA DATOS...</li>
    </ol>
  </div>

  <table>
    <tr><td><strong>Dennys Parra</strong></td></tr>
    <tr><td>Ejecutivo de Ventas</td></tr>
  </table>
</div>
```

---

## 🔧 Factibilidad Técnica

### ✅ El Código YA Está Preparado

El sistema actual **ya soporta HTML** automáticamente:

**Archivo**: `src/mail_utils.py` (líneas ~330-335)

```python
# Detectar si es HTML o texto plano
if '<html>' in cuerpo.lower() or '<br>' in cuerpo.lower():
    msg.attach(MIMEText(cuerpo, 'html'))  # ✅ HTML
else:
    msg.attach(MIMEText(cuerpo, 'plain'))  # Texto plano
```

**Conclusión**: Solo necesitas cambiar la plantilla de `.md` a `.html` y el sistema lo detectará automáticamente.

### 🔬 Prueba de Concepto (Sin Modificar Código)

Puedes probar HTML **AHORA MISMO** sin modificar código:

1. Edita `docs/correo-cierre/plantilla.md`
2. Agrega tags HTML simples:
   ```html
   <p>Buenas tardes estimados <strong>{NOMBRE_CLIENTE}</strong>,</p>
   <p>la presente es para informarle que ya tenemos cierre de su vehículo <strong>{VEHICULO}</strong></p>
   ```
3. Guarda y prueba

**Resultado**: El sistema lo detectará como HTML y lo enviará correctamente.

---

## 📝 Plan de Implementación

### Fase 1: Preparación (Sin Tocar Código)

#### 1.1 Crear Plantilla HTML

**Archivo nuevo**: `docs/correo-cierre/plantilla.html`

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Cierre de Negocio - Queirolo</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; background-color: #f4f4f4;">

  <!-- Container Principal -->
  <table width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr>
      <td align="center" style="padding: 20px 0;">

        <!-- Email Content -->
        <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">

          <!-- Header con Logo -->
          <tr>
            <td style="padding: 30px; text-align: center; background: linear-gradient(135deg, #f28f2c, #f05f2c); border-radius: 8px 8px 0 0;">
              <!-- Logo aquí (opcional) -->
              <h2 style="color: #ffffff; margin: 0; font-size: 24px;">Queirolo</h2>
              <p style="color: #ffffff; margin: 5px 0 0 0; font-size: 14px;">Más de 60 años en tu camino</p>
            </td>
          </tr>

          <!-- Saludo -->
          <tr>
            <td style="padding: 30px;">
              <p style="font-size: 16px; color: #333333; line-height: 1.6; margin: 0 0 15px 0;">
                Buenas tardes estimados <strong style="color: #f28f2c;">{NOMBRE_CLIENTE}</strong>,
              </p>

              <p style="font-size: 15px; color: #555555; line-height: 1.6; margin: 0 0 20px 0;">
                La presente es para informarle que ya tenemos cierre de su vehículo
                <strong>{VEHICULO}</strong>, según lo conversado con don Mario Queirolo,
                agradecemos la confianza depositada, ante cualquier información que requiera
                no dude en llamarnos.
              </p>
            </td>
          </tr>

          <!-- Precio Destacado -->
          <tr>
            <td style="padding: 0 30px 20px 30px;">
              <div style="background: #f8f9fa; border-left: 4px solid #f28f2c; padding: 15px; border-radius: 4px;">
                <p style="margin: 0; font-size: 16px; color: #333333; font-weight: bold;">
                  {PRECIO_ACORDADO_CLIENTE}
                </p>
              </div>
            </td>
          </tr>

          <!-- Datos del Propietario -->
          <tr>
            <td style="padding: 0 30px 20px 30px;">
              <div style="background: #ffffff; border: 1px solid #e0e0e0; padding: 15px; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 13px; color: #333333; white-space: pre-wrap;">
{DATOS_PROPIETARIO_COMPLETOS}
              </div>
            </td>
          </tr>

          <!-- Fecha de Pago -->
          <tr>
            <td style="padding: 0 30px 20px 30px;">
              <p style="font-size: 14px; color: #555555; text-align: center; margin: 0;">
                EN LOS PRÓXIMOS DÍAS ESTAREMOS FINIQUITANDO NEGOCIO<br>
                <strong style="color: #f28f2c; font-size: 16px;">FECHA DE PAGO: {FECHA_PAGO}</strong>
              </p>
            </td>
          </tr>

          <!-- Sección IMPORTANTE -->
          <tr>
            <td style="padding: 0 30px 30px 30px;">
              <div style="background: #fff9e6; border: 2px solid #f28f2c; padding: 20px; border-radius: 4px;">
                <h3 style="color: #f28f2c; margin: 0 0 15px 0; font-size: 18px;">⚠️ IMPORTANTE</h3>
                <ol style="margin: 0; padding-left: 20px; color: #333333; font-size: 14px; line-height: 1.8;">
                  <li>UNA VEZ CONFIRMADO FONDOS EN CUENTA, PROCEDEMOS A FIRMAR CONTRATOS EL DÍA HÁBIL SIGUIENTE ENTRE 13:30 – 17:00.</li>
                  <li>ENVÍEME POR ESTA VÍA DATOS BANCARIOS PARA PROCEDER A PAGO EL DÍA CORRESPONDIENTE (DATOS BANCARIOS DE DUEÑO DEL AUTO SEGÚN REGISTRO CIVIL).</li>
                  <li>ENVIAR LOS SIGUIENTES DATOS PARA PROCESAR TRANSFERENCIA PREVIA RECEPCIÓN DE PAGO.</li>
                  <li>ENVIAR CARNET AMBAS CARAS.</li>
                </ol>
              </div>
            </td>
          </tr>

          <!-- Despedida -->
          <tr>
            <td style="padding: 0 30px 30px 30px;">
              <p style="font-size: 14px; color: #555555; line-height: 1.6; margin: 0; font-style: italic;">
                De antemano gracias por la confianza depositada al consignar su auto con nosotros.
              </p>
            </td>
          </tr>

          <!-- Firma -->
          <tr>
            <td style="padding: 20px 30px; background: #f8f9fa; border-radius: 0 0 8px 8px;">
              <table cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="padding-right: 20px; vertical-align: top;">
                    <!-- Espacio para foto (opcional) -->
                    <div style="width: 80px; height: 80px; background: #e0e0e0; border-radius: 50%; display: inline-block;"></div>
                  </td>
                  <td style="vertical-align: top;">
                    <p style="margin: 0 0 5px 0; font-size: 16px; font-weight: bold; color: #333333;">Dennys Parra</p>
                    <p style="margin: 0 0 10px 0; font-size: 14px; color: #f28f2c;">Ejecutivo de Ventas</p>
                    <p style="margin: 0; font-size: 13px; color: #666666; line-height: 1.6;">
                      📞 +569 7540 0946<br>
                      📍 Av. Las Condes 12461, Local 4A. Las Condes<br>
                      🌐 <a href="http://www.queirolo.cl" style="color: #f28f2c; text-decoration: none;">www.queirolo.cl</a>
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

        </table>

        <!-- Footer -->
        <p style="margin: 20px 0 0 0; font-size: 12px; color: #999999; text-align: center;">
          © 2026 Queirolo - Más de 60 años en tu camino
        </p>

      </td>
    </tr>
  </table>

</body>
</html>
```

#### 1.2 Actualizar Configuración

**Archivo**: `docs/correo-cierre/mail_config.yaml`

```yaml
# Cambiar formato de plain a html
visual:
  firma:
    incluir: false  # La firma ya está en el HTML
  formato:
    tipo: "html"      # ← Cambiar de "plain" a "html"
    charset: "utf-8"
    line_break: "<br>"  # ← Usar <br> en lugar de \n

plantillas:
  default: "plantilla.html"  # ← Cambiar de .md a .html
```

### Fase 2: Modificación de Código (Opcional - Mejorar Detección)

Si quieres mejorar la detección automática de HTML:

**Archivo**: `src/mail_utils.py`

**Cambio sugerido** (línea ~154):

```python
def generar_email_desde_plantilla(
    datos_propietario: str,
    vehiculo: str,
    precio_acordado: str,
    fecha_pago: str,
    plantilla_path: Path = Path('docs/correo-cierre/plantilla.md')  # ← Cambiar default
) -> tuple[str, str]:
```

**A**:

```python
def generar_email_desde_plantilla(
    datos_propietario: str,
    vehiculo: str,
    precio_acordado: str,
    fecha_pago: str,
    plantilla_path: Path | None = None  # ← Permitir None
) -> tuple[str, str]:
    # Cargar plantilla desde config si no se especifica
    if plantilla_path is None:
        plantilla_name = get_config('plantillas.default', 'plantilla.md')
        plantilla_path = Path(f'docs/correo-cierre/{plantilla_name}')
```

**Beneficio**: Cambiar entre plantillas sin modificar código, solo editando `mail_config.yaml`.

### Fase 3: Testing

#### 3.1 Test Visual en Navegador

Antes de enviar, prueba el HTML en navegador:

1. Abre `plantilla.html` en Chrome/Firefox
2. Verifica que se vea bien
3. Usa herramientas de dev (F12) para ajustar CSS
4. Prueba en modo responsive (diferentes tamaños)

#### 3.2 Test de Email

**Herramientas recomendadas**:

1. **Litmus** (https://litmus.com) - Testing profesional
2. **Email on Acid** (https://www.emailonacid.com) - Compatibilidad
3. **Mail Tester** (https://www.mail-tester.com) - Verificar spam score

**Proceso**:

1. Envía email de prueba a ti mismo
2. Revisa en diferentes clientes:
   - Gmail (web)
   - Outlook (desktop)
   - Apple Mail
   - Gmail (móvil)
3. Verifica que se vea bien en todos

#### 3.3 Checklist de Testing

| Item | ✅/❌ |
|------|-------|
| Logo se muestra correctamente | ⬜ |
| Colores corporativos correctos | ⬜ |
| Negritas/estilos funcionan | ⬜ |
| Placeholders reemplazados | ⬜ |
| Links funcionan (si hay) | ⬜ |
| Se ve bien en móvil | ⬜ |
| Se ve bien en desktop | ⬜ |
| No cae en spam | ⬜ |
| Tiempo de carga < 3 seg | ⬜ |

---

## 🎨 Elementos de Diseño Recomendados

### 1. Paleta de Colores Queirolo

```css
/* Colores principales */
--primary-orange: #f28f2c;
--secondary-orange: #f05f2c;
--dark-text: #333333;
--light-text: #666666;
--background: #f4f4f4;
--white: #ffffff;
```

### 2. Tipografía

```css
/* Fuentes seguras para email */
font-family: Arial, Helvetica, sans-serif;  /* Títulos */
font-family: 'Courier New', monospace;      /* Datos técnicos */
```

### 3. Componentes Útiles

#### 3.1 Botón CTA (Call to Action)

```html
<table cellpadding="0" cellspacing="0" border="0">
  <tr>
    <td style="background: #f28f2c; border-radius: 4px; text-align: center;">
      <a href="https://queirolo.cl/contacto"
         style="display: inline-block; padding: 12px 30px; color: #ffffff;
                text-decoration: none; font-size: 16px; font-weight: bold;">
        Contactar Ejecutivo
      </a>
    </td>
  </tr>
</table>
```

#### 3.2 Tabla de Datos

```html
<table width="100%" cellpadding="10" cellspacing="0" border="0"
       style="border: 1px solid #e0e0e0; border-radius: 4px;">
  <tr style="background: #f8f9fa;">
    <td style="font-weight: bold; color: #333333;">Vehículo</td>
    <td style="color: #555555;">{VEHICULO}</td>
  </tr>
  <tr>
    <td style="font-weight: bold; color: #333333;">Precio</td>
    <td style="color: #555555;">{PRECIO_ACORDADO_CLIENTE}</td>
  </tr>
  <tr style="background: #f8f9fa;">
    <td style="font-weight: bold; color: #333333;">Fecha de Pago</td>
    <td style="color: #555555;">{FECHA_PAGO}</td>
  </tr>
</table>
```

#### 3.3 Banner de Alerta

```html
<div style="background: #fff9e6; border-left: 4px solid #f28f2c;
            padding: 15px; border-radius: 4px; margin: 20px 0;">
  <p style="margin: 0; color: #333333; font-weight: bold;">
    ⚠️ IMPORTANTE: Traer cédula de identidad vigente
  </p>
</div>
```

---

## 📊 Comparativa de Esfuerzo

### Opción A: HTML Básico (Recomendado para Empezar)

**Esfuerzo**: ⏱️ 30 minutos
**Resultado**: Email con estilos básicos (negritas, colores, separadores)

```html
<p>Buenas tardes <strong>{NOMBRE_CLIENTE}</strong>,</p>
<div style="background: #f8f9fa; padding: 10px;">
  <p>{PRECIO_ACORDADO_CLIENTE}</p>
</div>
```

### Opción B: HTML Profesional (Como el ejemplo completo)

**Esfuerzo**: ⏱️ 2-3 horas
**Resultado**: Email corporativo completo con logo, tablas, footer

### Opción C: HTML con Imágenes

**Esfuerzo**: ⏱️ 4-5 horas
**Resultado**: Email con logo, imágenes, firma con foto

**Requisitos adicionales**:
- Hosting para imágenes (no adjuntar al email)
- Optimización de imágenes
- CDN o servidor web

---

## ⚠️ Consideraciones Importantes

### 1. CSS Inline Obligatorio

❌ **NO funciona**:
```html
<style>
  .header { background: #f28f2c; }
</style>
<div class="header">Texto</div>
```

✅ **Funciona**:
```html
<div style="background: #f28f2c;">Texto</div>
```

**Razón**: Muchos clientes de email eliminan `<style>` tags.

### 2. Imágenes Externas

❌ **NO adjuntar** imágenes al email (aumenta tamaño, cae en spam)

✅ **Usar URLs**:
```html
<img src="https://www.queirolo.cl/images/logo.png" width="200" />
```

**Hosting de imágenes**:
- Servidor web de Queirolo
- CDN (Cloudflare, AWS S3)
- Servicio de email marketing (SendGrid, Mailchimp)

### 3. Ancho Máximo

- **Desktop**: 600px de ancho (estándar)
- **Móvil**: 100% con `max-width: 600px`

```html
<table width="600" style="max-width: 600px; width: 100%;">
  <!-- Contenido -->
</table>
```

### 4. Tablas vs Divs

**Recomendación**: Usar `<table>` para layout (compatibilidad)

❌ **Evitar**:
```html
<div style="display: flex;">  <!-- No soportado por todos -->
```

✅ **Usar**:
```html
<table cellpadding="0" cellspacing="0">
  <tr>
    <td>Columna 1</td>
    <td>Columna 2</td>
  </tr>
</table>
```

---

## 🔄 Proceso de Migración Paso a Paso

### Semana 1: Preparación

- [ ] Revisar esta guía completa
- [ ] Definir diseño visual (colores, logo, estructura)
- [ ] Crear plantilla HTML básica
- [ ] Probar en navegador

### Semana 2: Implementación

- [ ] Copiar plantilla completa a `plantilla.html`
- [ ] Reemplazar placeholders
- [ ] Ajustar colores corporativos
- [ ] Agregar logo (si disponible)

### Semana 3: Testing

- [ ] Enviar emails de prueba
- [ ] Verificar en diferentes clientes
- [ ] Ajustar compatibilidad
- [ ] Verificar spam score

### Semana 4: Producción

- [ ] Actualizar `mail_config.yaml`
- [ ] Cambiar plantilla default a `.html`
- [ ] Documentar cambios
- [ ] Entrenar equipo

---

## 📚 Recursos y Referencias

### Herramientas de Desarrollo

1. **Email Builders**:
   - [Bee Free](https://beefree.io) - Editor visual gratuito
   - [MJML](https://mjml.io) - Framework para emails responsive
   - [Foundation for Emails](https://get.foundation/emails.html) - Framework

2. **Testing**:
   - [Litmus](https://litmus.com) - Testing profesional
   - [Mailtrap](https://mailtrap.io) - SMTP de prueba
   - [Mail Tester](https://www.mail-tester.com) - Verificar spam

3. **Plantillas Gratuitas**:
   - [Really Good Emails](https://reallygoodemails.com) - Inspiración
   - [Cerberus](https://github.com/TedGoas/Cerberus) - Templates responsive
   - [Email Templates](https://github.com/forwardemail/email-templates) - Open source

### Guías Técnicas

- [Can I Email](https://www.caniemail.com) - Compatibilidad CSS
- [Email Client Market Share](https://www.litmus.com/email-client-market-share) - Estadísticas
- [HTML Email Best Practices](https://www.campaignmonitor.com/dev-resources/) - Guía

---

## ❓ Preguntas Frecuentes

### ¿Necesito modificar código Python?

**No necesariamente**. El código actual ya soporta HTML. Solo necesitas:
1. Crear `plantilla.html`
2. Actualizar `mail_config.yaml`

### ¿Puedo tener ambas plantillas (texto y HTML)?

**Sí**. Puedes tener:
- `plantilla.md` (texto plano)
- `plantilla.html` (HTML)

Cambias en `mail_config.yaml` cuál usar.

### ¿Qué pasa si el cliente no soporta HTML?

Los clientes de email modernos muestran un fallback de texto plano automáticamente. Puedes mejorar esto agregando:

```python
# En mail_utils.py (modificación futura)
msg_alternative = MIMEMultipart('alternative')
msg_alternative.attach(MIMEText(texto_plano, 'plain'))
msg_alternative.attach(MIMEText(html, 'html'))
```

### ¿Aumentará el spam score?

Solo si abusas de:
- ❌ Demasiadas imágenes
- ❌ Links sospechosos
- ❌ Palabras spam ("gratis", "gana dinero")
- ❌ HTML mal formado

Con HTML limpio y profesional, **no hay problema**.

### ¿Cuánto pesa un email HTML?

- **Texto plano**: ~5-10 KB
- **HTML básico**: ~15-20 KB
- **HTML con imágenes inline**: ~100-500 KB (❌ evitar)
- **HTML con imágenes externas**: ~20-30 KB (✅ recomendado)

Límite recomendado: **< 100 KB**

---

## ✅ Checklist Final de Implementación

### Pre-Implementación

- [ ] Revisar guía completa
- [ ] Definir diseño visual
- [ ] Tener logo disponible (URL o archivo)
- [ ] Backup de plantilla actual (`plantilla.md`)

### Implementación

- [ ] Crear `plantilla.html` con estructura completa
- [ ] Reemplazar todos los placeholders
- [ ] Agregar logo de Queirolo
- [ ] Ajustar colores corporativos (#f28f2c, #f05f2c)
- [ ] Probar en navegador (Chrome, Firefox)

### Testing

- [ ] Enviar email de prueba a 3+ clientes diferentes
- [ ] Verificar en móvil (Gmail app, Apple Mail)
- [ ] Verificar en desktop (Outlook, Gmail web)
- [ ] Comprobar spam score con Mail Tester
- [ ] Validar HTML con [W3C Validator](https://validator.w3.org)

### Producción

- [ ] Actualizar `mail_config.yaml` → `plantilla.html`
- [ ] Documentar cambios en changelog
- [ ] Crear guía de edición HTML (similar a texto plano)
- [ ] Entrenar equipo en edición HTML

### Post-Implementación

- [ ] Monitorear spam reports (primeras 2 semanas)
- [ ] Recopilar feedback de clientes
- [ ] Ajustar diseño según feedback
- [ ] Optimizar performance

---

## 🎯 Recomendación Final

**Para empezar**:
1. ✅ Usa HTML básico (negritas, colores, separadores)
2. ✅ Sin imágenes (evitar problemas de hosting)
3. ✅ Prueba con 10-20 emails reales
4. ✅ Recopila feedback

**Luego evoluciona**:
1. Agregar logo
2. Mejorar diseño
3. Agregar tablas
4. Personalización avanzada

**Esfuerzo total estimado**: 2-4 horas para implementación completa profesional

---

**Última actualización**: 2026-02-05
**Autor**: Claude Code
**Versión**: 1.0
