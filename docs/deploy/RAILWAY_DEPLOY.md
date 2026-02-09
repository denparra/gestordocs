# Railway Deploy Guide

## Requisitos
- Usar el `Dockerfile` incluido.
- Variables de entorno configuradas en Railway.

## Variables obligatorias
AutoTramite:
- `AUTOTRAMITE_EMAIL`
- `AUTOTRAMITE_PASSWORD`

Opcional (Playwright):
- `PLAYWRIGHT_HEADLESS=true`

## Storage externo (opcional)
Selecciona backend con `PDF_STORAGE_BACKEND`:
- `s3` o `gcs`

### S3
- `PDF_STORAGE_BACKEND=s3`
- `S3_BUCKET`
- `S3_REGION`
- `S3_ACCESS_KEY_ID`
- `S3_SECRET_ACCESS_KEY`

Opcional:
- `S3_PREFIX` (default: `pdf`)
- `S3_ENDPOINT_URL` (para S3 compatible)
- `S3_PRESIGN=true` (default)
- `S3_PRESIGN_SECONDS=3600`
- `S3_PUBLIC_BASE_URL` (si bucket publico)

### GCS
- `PDF_STORAGE_BACKEND=gcs`
- `GCS_BUCKET`
- `GCP_SERVICE_ACCOUNT_JSON` (contenido JSON completo)

Opcional:
- `GCS_PREFIX` (default: `pdf`)
- `GCS_SIGNED_URL=true` (default)
- `GCS_SIGNED_URL_SECONDS=3600`
- `GCS_PUBLIC_BASE_URL` (si bucket publico)

## Comandos Railway
Start command recomendado:
```
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

Build:
- El Dockerfile ejecuta `playwright install --with-deps chromium`.

## Notas
- El filesystem en Railway es efimero: los PDFs locales no persisten.
- Por eso se recomienda descarga inmediata o storage externo.
