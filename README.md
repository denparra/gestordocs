# AutoTramite + Habilitacion Tag (Streamlit + Playwright)

## 1) Vision general
Este repositorio implementa dos procesos independientes:
- AutoTramite: automatiza la creacion y registro de contratos de compraventa en AutoTramite.cl usando Playwright.
- Habilitacion Tag: genera un PDF editable de Solicitud TAG desde texto libre.

Problemas que resuelve:
- Reduce digitacion manual en el portal de AutoTramite.
- Estandariza validaciones de RUT, patente, email y telefono.
- Acelera la generacion de PDFs de solicitud TAG.

Fuera de alcance:
- No es un backend con API publica.
- No hace OCR ni interpreta PDFs escaneados.
- No persiste resultados en base de datos.
- No ejecuta n8n en runtime (solo referencia de workflow).

## 2) Arquitectura y componentes
Mapa de carpetas (resumen):
```
.
|- app.py
|- src/
|- docs/
|  |- autotramite/
|  |- tag/
|- tests/
|- run_autotramite_cli.py
|- test_preview.py
|- Dockerfile
|- requirements.txt
|- RAILWAY_DEPLOY.md
|- GENERAL.md
```

### Flujo 1: AutoTramite (contratos compraventa)
Entradas:
- Texto CAV + Nota de Venta (textarea en Streamlit).

Proceso:
- Parseo y validaciones.
- Login en AutoTramite.
- Llenado de formulario.
- Previsualizacion PDF o registro.

Salidas:
- PDF de previsualizacion.
- Confirmacion de registro (si dry-run es False).

Scripts principales:
- `app.py` (UI principal).
- `run_autotramite_cli.py` (CLI que se ejecuta en subproceso).
- `test_preview.py` (dry-run con PDF guardado en `screenshots/`).

Referencia n8n:
- `docs/autotramite/ref/autotramite-compraventa-mvp.json`.
- `docs/autotramite/ref/n8n-autotramite-compraventa-workflow-plan.md`.

### Flujo 2: Habilitacion Tag (relleno PDF)
Entradas:
- Texto libre con lineas tipo Nombre, RUT, Direccion, Telefono, Correo, PATENTE, TAG.

Proceso:
- Parseo y normalizacion.
- Mapeo de campos CAMPO1..CAMPO16 a nombres reales del PDF.
- Relleno de AcroForm.

Salidas:
- `docs/tag/output/Solicitud-Tag-[PATENTE].pdf`.

Scripts y docs:
- `docs/tag/test_preview_tag.py`.
- `docs/tag/tag-pdf-autofill-implementation-guide.md`.
- `docs/tag/PDF-EJEMPLO.pdf`.

## 3) Requisitos y setup
### Requisitos de sistema
- Python 3.10+.
- Playwright + Chromium (solo para AutoTramite).
- Node.js y n8n solo si vas a importar/ejecutar el workflow n8n (opcional).

### Instalacion
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### Variables de entorno
Obligatorias:
- `AUTOTRAMITE_EMAIL`
- `AUTOTRAMITE_PASSWORD`

Opcionales (AutoTramite):
- `PLAYWRIGHT_HEADLESS=true`
- `PLAYWRIGHT_SLOW_MO=0`
- `LOG_LEVEL=INFO`
- `TIMEOUT_NAVIGATION`, `TIMEOUT_ELEMENT`, `TIMEOUT_ANIMATION`

Storage externo (opcional):
- `PDF_STORAGE_BACKEND=s3` o `PDF_STORAGE_BACKEND=gcs`
- Ver `RAILWAY_DEPLOY.md` para variables completas.

### Importar workflow en n8n (referencia)
1. Abrir n8n UI.
2. Menu -> Import from file.
3. Seleccionar `docs/autotramite/ref/autotramite-compraventa-mvp.json`.
4. Guardar workflow con nombre propio.

## 4) Como usar (end-to-end)
### AutoTramite (Streamlit)
Cuando usarlo:
- Registrar o previsualizar contratos de compraventa.

Disparo:
- Manual desde la UI: `streamlit run app.py`.

Datos:
- Pegar texto CAV + Nota de Venta.

Resultado:
- PDF de previsualizacion y/o confirmacion de registro.

Ejemplo de entrada (resumido):
```
DATOS DEL VEHICULO
Marca: HYUNDAI
Patente: DRLZ.16-3
...
DATOS DEL VENDEDOR
Nombre: ...
RUT: ...
...
DATOS COMPRADOR
Nombre: ...
RUT: ...
```

Preview local (dry-run):
```
python test_preview.py
```
Nota: `test_preview.py` espera `docs/test.md`. Si no existe, copia el contenido desde `docs/autotramite/test.md` y crea ese archivo.

### Habilitacion Tag (Streamlit)
Cuando usarlo:
- Generar solicitud TAG desde texto libre.

Disparo:
- Menu -> Habilitacion Tag.

Datos:
- Texto con lineas tipo Nombre, RUT, Direccion, Telefono, Correo, PATENTE, TAG.

Resultado:
- `docs/tag/output/Solicitud-Tag-[PATENTE].pdf`.

Ejemplo de entrada:
```
Nombre: MARIO HUMBERTO VERA VALENCIA
RUT: 10759120-6
Direccion: CALLE CHUQUICAMATA 814, LA CALERA.
Telefono: 977583559
Correo: Mario.vera@cencocal.cl
PATENTE: KYTR.55-5
TAG 147258369
```

Test directo (sin UI):
```
python docs/tag/test_preview_tag.py
```

### Endpoints n8n (si existieran)
Este repositorio no expone endpoints HTTP. El JSON n8n es solo referencia.

### Troubleshooting (errores comunes)
- Error de credenciales: validar `.env` y acceso real al portal.
- Timeout esperando elemento: revisar selectores en `src/config.py`.
- PDF Tag no se genera: revisar `docs/tag/tag-pdf-autofill-implementation-guide.md` y dependencias `pypdf`.

## 5) Operacion / mantenimiento
Actualizar selectores (AutoTramite):
- Editar `src/config.py` en `SELECTORS`.
- Probar con `PLAYWRIGHT_HEADLESS=False`.
- Validar con `test_preview.py` antes de produccion.

Versionar cambios del workflow JSON:
- Guardar nuevas versiones en `docs/autotramite/ref/`.
- Documentar cambios en `docs/autotramite/README.md`.

Checklist antes de produccion:
- Credenciales configuradas en `.env` o secrets.
- Playwright instalado y probado.
- Dry-run funcionando.
- Storage externo configurado si se requiere persistencia.
- Logs con PII ofuscada.

Seguridad:
- No commitear `.env`.
- Revisar logs antes de compartir.
- Usar secrets en Railway.

## 6) Roadmap (breve)
- Persistencia de PDFs en storage externo como default.
- UI mas guiada para errores de parsing.
- API REST para integraciones externas.
- Mayor cobertura de tests de parsing.

## 7) FAQ
P: Puedo usar esto sin credenciales de AutoTramite?
R: No, AutoTramite requiere login real para previsualizar/registrar.

P: Donde quedan los PDFs generados?
R: En `screenshots/` (AutoTramite) y `docs/tag/output/` (Tag). En Railway el filesystem es efimero.

P: Puedo usar solo el flujo Tag sin Playwright?
R: Si, Tag no usa Playwright, solo `pypdf`.

P: Como subo PDFs a S3/GCS?
R: Define `PDF_STORAGE_BACKEND` y las variables indicadas en `RAILWAY_DEPLOY.md`.

---

## Documentacion adicional
- `docs/autotramite/README.md`
- `docs/tag/tag-pdf-autofill-implementation-guide.md`
- `GENERAL.md`
- `RAILWAY_DEPLOY.md`
