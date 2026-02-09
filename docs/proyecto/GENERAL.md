# Guia General del Proyecto

## Resumen rapido
Este repositorio es una app Streamlit con dos flujos:
- AutoTramite: automatiza login, llenado y registro de contratos usando Playwright.
- Habilitacion Tag: toma texto libre, normaliza datos y rellena un PDF editable.

## Estructura principal
- `app.py`: UI principal y menu de flujos.
- `src/`: logica de AutoTramite, validaciones y utilidades.
- `docs/tag/`: plantilla PDF, test de TAG y guia de mapeo.
- `tests/`: pruebas unitarias y/o de flujo.

## Comandos clave
```
python -m pip install -r requirements.txt
streamlit run app.py
python docs/tag/test_preview_tag.py
```

## Variables de entorno
- `AUTOTRAMITE_EMAIL` y `AUTOTRAMITE_PASSWORD`.
- `PLAYWRIGHT_HEADLESS=true` para produccion.

## Storage externo (implementado)
Se puede subir PDFs a S3 o GCS si defines `PDF_STORAGE_BACKEND`.
Consulta `RAILWAY_DEPLOY.md` para variables completas.

## Despliegue en Railway (listo)
Incluido:
- `Dockerfile` con dependencias de Playwright + Chromium.
- `pypdf`, `boto3` y `google-cloud-storage` en `requirements.txt`.

Start Command recomendado:
```
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

Build/deploy:
- El Dockerfile ejecuta `playwright install --with-deps chromium`.

## Consideraciones
- El filesystem en Railway es efimero. Los PDFs generados en `docs/tag/output/` o `screenshots/` no son persistentes.
- Se recomienda descarga inmediata o storage externo (ya soportado).

## Pendiente (si aplica)
- Persistencia de PDFs con storage externo si se requiere historico.
- Monitoreo/logs centralizados si es necesario.
