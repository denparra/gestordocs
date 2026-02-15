# Incidente Produccion: Timeout Login AutoTramite

**Fecha:** 2026-02-15  
**Modulo:** AutoTramite  
**Entorno afectado:** Railway (produccion)  
**Estado:** Mitigado

---

## 1) Resumen Ejecutivo

En produccion, el flujo de AutoTramite fallaba con:

`Timeout durante login (posible problema de red)`

La operacion quedaba intermitente o fallaba antes de completar login.  
La mitigacion aplicada fue aumentar timeouts:

- `TIMEOUT_NAVIGATION=60000`
- `TIMEOUT_ELEMENT=20000`

Tras ese cambio, el flujo volvio a funcionar en produccion.

---

## 2) Sintoma Observado

- En UI: proceso quedaba en "validando datos" y luego error de timeout.
- En backend: timeout capturado en el bloque de login de Playwright.
- Local en `.venv`: funciona.
- Local fuera de `.venv`: comportamiento inestable/fallas por diferencias de entorno.

---

## 3) Analisis Tecnico (Estado actual)

### 3.1 Donde ocurre el timeout

El mensaje se genera en `src/autotramite.py` cuando Playwright excede tiempo en login (navegacion/espera de elementos).

### 3.2 Cambios recientes

El commit reciente de mejoras funcionales no modifico `src/autotramite.py` (motor de login), por lo que no hay evidencia de regresion directa de negocio.

### 3.3 Hallazgos de entorno

- Diferencias entre entorno global y `.venv` (versiones de Playwright/Streamlit distintas).
- `requirements.txt` con rangos (`>=`) puede introducir drift entre deploys.
- Produccion (Railway) tiene mayor latencia/variabilidad que local.
- Timeouts previos (30s/10s) eran ajustados para red de datacenter.

---

## 4) Causa Raiz Probable

**Principal:** timeout operativo por latencia/variabilidad de entorno en produccion.  
**Contribuyentes:**

- Timeouts iniciales demasiado estrictos para Railway.
- Diferencia de versiones/entorno entre ejecuciones (local global vs `.venv`, deploys variables).
- Posible intermitencia externa del sitio objetivo.

---

## 5) Mitigacion Aplicada (Exitosa)

Se ajustaron variables de entorno en produccion:

- `TIMEOUT_NAVIGATION=60000`
- `TIMEOUT_ELEMENT=20000`

**Resultado:** flujo estable nuevamente en produccion.

---

## 6) Riesgo Residual

- Puede reaparecer en picos de latencia extrema.
- Puede haber nuevas variaciones en deploy si dependencias no se fijan.
- Dependencia de tercero (`autotramite.cl`) sigue siendo factor externo.

---

## 7) Plan de Implementacion Futura (Hardening)

### Fase A - Estabilidad de entorno (bajo riesgo, alto impacto)

1. Fijar versiones criticas en `requirements.txt` (especialmente `playwright`, `streamlit`, `pydantic`, `pydantic-settings`).
2. Documentar version objetivo de Python para prod/local.
3. Verificar en cada deploy que `playwright install chromium --with-deps` termine sin errores.

### Fase B - Observabilidad operativa

1. Registrar tiempos por etapa: login, carga formulario, previsualizacion, registro.
2. Exponer en UI estado por etapas (ya implementado visualmente).
3. Guardar ultimo stage alcanzado en error para soporte.

### Fase C - Monitoreo y alertas

1. Definir umbral de warning por etapa (ej. login > 25s).
2. Detectar recurrencia de timeout por ventana (ej. 3 fallos en 10 minutos).
3. Checklist de verificacion post-deploy.

---

## 8) Validaciones Recomendadas en cada Deploy

- Smoke test login AutoTramite en prod (dry-run).
- Confirmar variables:
  - `TIMEOUT_NAVIGATION`
  - `TIMEOUT_ELEMENT`
  - `AUTOTRAMITE_EMAIL`
  - `AUTOTRAMITE_PASSWORD`
- Revisar logs de build y runtime en Railway.
- Verificar version efectiva de Playwright en runtime.

---

## 9) Lecciones Aprendidas

1. Local exitoso fuera de `.venv` no es referencia confiable.
2. En automatizaciones web contra terceros, timeout conservador evita falsos negativos.
3. Pin de dependencias reduce regresiones silenciosas por redeploy.

---

## 10) Acciones Pendientes

- [ ] Definir y aplicar pin de dependencias.
- [ ] Agregar checklist post-deploy formal.
- [ ] Revisar periodicidad de errores de login en 7 dias.
- [ ] Evaluar documentar runbook de incidente en `docs/deploy/`.
