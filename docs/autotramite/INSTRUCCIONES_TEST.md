# Instrucciones para Ejecutar Test de Previsualización

Este documento explica cómo ejecutar el test de previsualización sin registrar contratos.

## 📋 Pre-requisitos

1. **Instalar dependencias:**
```bash
cd projects/gestordocs/autotramite_py_mvp
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
playwright install chromium
```

2. **Configurar credenciales:**
```bash
# Crear archivo .env
cp .env.example .env

# Editar .env y agregar:
AUTOTRAMITE_EMAIL=tu_email@queirolo.cl
AUTOTRAMITE_PASSWORD=tu_contraseña

# Opcional para ver el browser:
PLAYWRIGHT_HEADLESS=False
```

**Nota de formato:** En `docs/test.md`, los RUT deben ir sin puntos y con digito verificador (ej: `26002284-5`).

## 🚀 Ejecutar Test

```bash
python test_preview.py
```

## 📸 Qué hace el test

1. **Lee los datos** de `docs/test.md`
2. **Parsea y valida** los datos (RUT, patente, email, teléfono)
3. **Login** en AutoTramite con tus credenciales
4. **Llena el formulario** con los datos parseados
5. **Previsualiza el PDF** (click en botón "Previsualizar PDF")
6. **Descarga el PDF** y lo guarda en `screenshots/`
7. **NO registra** el contrato (modo dry-run)

Nota: En la vista previa hay un bot?n de descarga PDF (ver `screenshots/ejemplo.png`).

## 📁 Archivos generados

Los PDFs se guardan en:
```
screenshots/preview_PATENTE_TIMESTAMP.pdf
```

Ejemplo:
```
screenshots/preview_DRLZ16_20260204_153045.pdf
```

## ⚙️ Configuración Avanzada

### Ver el browser ejecutándose

En `.env`:
```env
PLAYWRIGHT_HEADLESS=False
PLAYWRIGHT_SLOW_MO=1000  # Delay 1s entre acciones
```

### Cambiar timeout

En `.env`:
```env
TIMEOUT_NAVIGATION=60000  # 60 segundos
TIMEOUT_ELEMENT=20000     # 20 segundos
```

## 🐛 Troubleshooting

### Error: "AUTOTRAMITE_EMAIL no configurado"
**Solución:** Verificar que existe `.env` con las credenciales

### Error: "Login fallido"
**Solución:** Verificar credenciales en `.env`

### Error: "Timeout esperando campo"
**Solución:** Aumentar timeouts o verificar conexión

### PDF no se descarga
**Soluci?n:** Verifica que el bot?n "Previsualizar PDF" se haya ejecutado; en headless no ver?s el visor, pero el PDF debe guardarse en `screenshots/`.

## 📊 Salida Esperada

```
╔══════════════════════════════════════════════════════════════╗
║  AutoTramite Test - Previsualización sin Registro           ║
║                                                              ║
║  Este script realizará:                                     ║
║  1. Parseo de datos desde docs/test.md                      ║
║  2. Login en AutoTramite                                    ║
║  3. Llenado del formulario                                  ║
║  4. Previsualización del PDF                                ║
║  5. Descarga de PDF (guardado en ./screenshots/)      ║
║                                                              ║
║  ⚠️  NO se registrará el contrato (modo dry-run)            ║
╚══════════════════════════════════════════════════════════════╝

============================================================
TEST: Previsualizar Contrato (sin registro)
============================================================

1. Parseando datos de prueba...
✅ Datos parseados correctamente:
  - Patente: DRLZ16-3
  - Vehículo: HYUNDAI ELANTRA GLS 1.6 (2012)
  - Vendedor: DENNYS EDUARDO PARRA
  - Comprador: CAROLINA CECILIA CALLES
  - Valor Venta: $5,000,000

2. Ejecutando automatización (DRY-RUN)...
   > Login en AutoTramite
   > Llenado de formulario
   > Previsualización de PDF
   > PDF: screenshots/preview_DRLZ16_20260204_153045.pdf
   > NO se registrará el contrato

3. Resultado:
✅ Previsualización EXITOSA
  - Duración: 23.4s
  - Mensaje: Previsualización exitosa (modo dry-run, no se registró) - Archivo: ...
  - PDF guardado: screenshots/preview_DRLZ16_20260204_153045.pdf
  - Tamaño: 245.3 KB

============================================================
TEST COMPLETADO
============================================================
```

## ✅ Verificación

Después de ejecutar, verificar:

1. ✅ El script termina sin errores
2. ✅ Se crea el directorio `screenshots/`
3. ? Existe el archivo PDF del contrato
4. ? El PDF abre y muestra el contrato
5. ✅ El log indica "Previsualización EXITOSA"
6. ✅ NO se registró ningún contrato en AutoTramite

## 🔄 Próximos Pasos

Si el test es exitoso, puedes:

1. **Usar la app Streamlit:**
   ```bash
   streamlit run app.py
   ```

2. **Ejecutar sin dry-run** (registrará el contrato):
   - Modificar `test_preview.py` línea 77
   - Cambiar `dry_run=True` a `dry_run=False`
   - **CUIDADO:** Esto REGISTRARÁ el contrato en AutoTramite

3. **Integrar con tu flujo:**
   - Importar `crear_contrato_autotramite` en tu código
   - Llamar con tus datos reales

---

**Última actualización:** 04 Febrero 2026
