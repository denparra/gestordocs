Batería de Preguntas: Integración n8n + Telegram
A. Usuarios y Permisos (5 preguntas)
A1. ¿Quiénes serán los usuarios autorizados para operar estos flujos vía Telegram?
- C) Solo un rol específico (¿cuál?) R: ADMIN
A2. ¿Cómo autenticarás/validarás usuarios en Telegram?
R: DEFINIR LA MEJOR OPCION
A3. ¿Diferentes usuarios tendrán diferentes permisos por flujo?
- Ejemplo: vendedores solo AutoTramite, admin puede todo
- ¿Necesitas matriz de permisos Usuario×Flujo? R: NO
A4. ¿Qué sucede si un usuario no autorizado intenta usar el bot?
- A) Ignora silenciosamente
A5. ¿Necesitas auditar quién ejecutó qué operación?
- ¿Guardar: usuario, timestamp, flujo, datos enviados, resultado?
- ¿Dónde: logs, DB, ambos? R: EN LOGS UNA ARCHIVO SIMILAR
---


B. Operación/UX Telegram (7 preguntas)
B1. ¿Prefieres comandos explícitos o menú interactivo?
- C) Híbrido: comandos + botones en cada paso
R: LO MAS FACIL
B2. Formato de entrada de datos - ¿cómo lo prefieres?
- A) Mensaje único multilinea (como ahora en Streamlit)

B3. ¿Cómo maneja el bot errores de validación?
- Ejemplo: RUT inválido, patente mal formateada
- A) Responde error ESPECIFICANDO CUAL ES EL ERROR PARA SOLUCIONAR + permite 3 reintentos, luego cancela

B4. ¿Usuario puede cancelar operación en cualquier momento?
- ¿Comando específico como /cancel?
- ¿Timeout de inactividad (ej. 10 min sin respuesta = cancela)?
R: SI AMBAS, SIEMPRE BUSCANDO LO MAS FACIL Y PRACTICO

B5. Confirmación antes de ejecutar - ¿qué nivel de detalle mostrar?

- B) Todos los campos parseados formateados

B6. ¿Qué pasa si usuario envía datos mientras otro proceso está corriendo?

- B) Rechazo: "tienes operación en curso, complétala o cancela"

B7. ¿Mensajes de progreso durante ejecución?
- Ejemplo: "Logueando...", "Llenando formulario...", "Generando PDF..."
- ¿Actualizas mismo mensaje (edit) o envías múltiples?
R: DEFINELO TU
---

C. Integración Técnica (6 preguntas)
C1. ¿Arquitectura preferida para ejecutar Python desde n8n?
- A) n8n llama HTTP endpoint Flask/FastAPI que ejecuta lógica Python
- B) n8n ejecuta Execute Command con script Python directo
- C) n8n solo orquesta, Python corre como servicio independiente (webhooks mutuos)
R: ESCOJAMOS LA OPCION MAS PRACTICA/FACIL FUNCIONAL

C2. ¿Dónde hostearás n8n y el bot?

R - TENGO UN VPS CON HOSTINGER [ https://n8n-n8n.wqzejs.easypanel.host/home/workflows ]

C3. ¿Cómo manejarás credenciales AutoTramite en flujo Telegram?
- A) Usa mismas credenciales hardcodeadas (.env Python)

C4. ¿Necesitas que n8n guarde estado de conversaciones?

- ¿O suficiente con memoria efímera de workflow n8n? me parece esta, pero decidelo tu. siempre buscando lo mas practico.
C5. ¿Cómo compartirás código de validadores entre Streamlit y Telegram?
- A) Ambos llaman mismos módulos Python (validators.py, models.py)
- B) Duplicar lógica en n8n (funciones JavaScript)
- C) API Python centralizada que ambos consumen
R: TU DECIDELO, SIEMPRE ENOCADO EN HACERLO FUNCIONAL, PRACTICO Y FACIL.

C6. ¿Reintentos automáticos en caso de fallo?
- ¿Misma lógica exponencial backoff actual (MAX_REINTENTOS=3)?
- ¿Usuario recibe notificación de cada reintento?
R: TU DECIDELO, SIEMPRE ENOCADO EN HACERLO FUNCIONAL, PRACTICO Y FACIL.

---
D. Seguridad y Compliance (3 preguntas)
D1. ¿Cómo protegerás PII en mensajes Telegram?
- A) Telegram es canal "suficientemente seguro" (cifrado E2E)
R: TU DECIDELO, SIEMPRE ENOCADO EN HACERLO FUNCIONAL, PRACTICO Y FACIL.

D2. ¿Logs de Telegram bot también deben ofuscar PII?
- Usar misma lógica ofuscar_rut(), ofuscar_email() de logging_utils.py?
R: TU DECIDELO, SIEMPRE ENOCADO EN HACERLO FUNCIONAL, PRACTICO Y FACIL.

D3. ¿Token de Telegram bot cómo se gestiona?
- ¿Variable entorno en n8n?
- ¿Credential encriptada en n8n?
R: TU DECIDELO, SIEMPRE ENOCADO EN HACERLO FUNCIONAL, PRACTICO Y FACIL.
---
E. PDF/Outputs (4 preguntas)
E1. ¿Cómo entrega el bot el PDF generado (AutoTramite/Tag)?
- C) Ambos: adjunto + link backup
R: TU DECIDELO, SIEMPRE ENOCADO EN HACERLO FUNCIONAL, PRACTICO Y FACIL.

E2. ¿Dónde se almacenan PDFs generados?
- A) Filesystem local Python (misma carpeta actual)
R: TU DECIDELO, SIEMPRE ENOCADO EN HACERLO FUNCIONAL, PRACTICO Y FACIL.

E3. Mail de Cierre - ¿qué entrega el bot?
- A) Confirmación "email enviado a X"

E4. ¿Tamaño máximo de datos esperado por mensaje?
- Para validar límites Telegram (4096 chars por mensaje)
R: TEXTO MENOS DE 4096 chars
---
F. Observabilidad (3 preguntas)
F1. ¿Métricas que necesitas trackear?
- A) Solo éxito/fallo por flujo

F2. ¿Dónde visualizas métricas?
- A) Logs Python + n8n execution logs (manual)
R: TU DECIDELO, SIEMPRE ENOCADO EN HACERLO FUNCIONAL, PRACTICO Y FACIL.

F3. ¿Trazabilidad entre mensaje Telegram y ejecución Python?
- ¿Quieres correlation ID que aparezca en:
  - Mensaje Telegram → log n8n → log Python → PDF filename?
R: TU DECIDELO, SIEMPRE ENOCADO EN HACERLO FUNCIONAL, PRACTICO Y FACIL.
---
Resumen de Supuestos Iniciales
Asumo lo siguiente hasta recibir tus respuestas (corrige si difieren):
1. Usuarios internos: Solo equipo Queirolo usará bot (no clientes externos)
2. Autenticación básica: Lista blanca de Telegram IDs suficiente para MVP
3. Arquitectura híbrida: n8n orquesta Telegram + llama Python vía HTTP (Flask/FastAPI)
4. Hosting: n8n y Python en mismo servidor/entorno local actual (ACTUALMENTE EL PROYECTO ESTA EN RAILWAY "https://gestordocs-production.up.railway.app/" Y N8N ESTARA EN "https://n8n-n8n.wqzejs.easypanel.host/home/workflows" )
5. Credenciales compartidas: Mismas credenciales .env para Streamlit y Telegram
6. PDFs adjuntos: Bot envía PDF directo (no links), almacenamiento local temporal
7. Logs unificados: Reusa logging_utils.py con ofuscación PII existente
8. Single-thread: Un proceso a la vez por usuario (evitar colisiones Playwright)