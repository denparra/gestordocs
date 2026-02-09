"""
AutoTramite API - FastAPI backend for n8n/Telegram integration.

Canal 2 (Telegram) - runs alongside Canal 1 (Streamlit) without modifying
any existing code. Reutilizes src/ modules directly.
"""
import os
import re
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from src.models import (
    ContratoData, ContratoResult, ValidationError as VError,
    parsear_texto_contrato
)
from src.autotramite import crear_contrato_autotramite
from src.mail_utils import (
    generar_email_desde_plantilla, enviar_email_smtp,
    validar_datos_mail, validar_smtp_config
)
from src.logging_utils import get_logger

# ---------------------------------------------------------------------------
# App & Logger
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AutoTramite API",
    version="1.0.0",
    description="Backend REST para integracion n8n/Telegram"
)
logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
API_TOKEN = os.getenv("API_TOKEN", "changeme")
security = HTTPBearer()


def verificar_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Token invalido")
    return True


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class ValidarRequest(BaseModel):
    tipo: str  # "autotramite" | "tag" | "mail"
    datos_raw: str
    correlation_id: str


class ValidarResponse(BaseModel):
    valido: bool
    datos_parseados: Optional[dict] = None
    errores: list[dict] = []
    intentos_restantes: Optional[int] = None
    correlation_id: str


class EjecutarAutoTramiteRequest(BaseModel):
    datos: dict
    modo: str = "preview"  # "registro" | "preview"
    correlation_id: str


class EjecutarResponse(BaseModel):
    exito: bool
    pdf_path: Optional[str] = None
    pdf_url: Optional[str] = None
    mensaje: str
    correlation_id: str
    metadata: Optional[dict] = None


class TagRequest(BaseModel):
    datos_raw: str
    correlation_id: str


class MailRequest(BaseModel):
    datos_propietario: str
    vehiculo: str
    precio_acordado: str
    fecha_pago: str
    email_to: str
    cc: list[str] = []
    correlation_id: str


# ---------------------------------------------------------------------------
# TAG helpers (mirror of app.py logic, no import needed)
# ---------------------------------------------------------------------------
TAG_DIR = Path(__file__).parent / 'docs' / 'tag'
TAG_TEMPLATE_PDF = TAG_DIR / 'PDF-EJEMPLO.pdf'
TAG_OUTPUT_DIR = TAG_DIR / 'output'
TAG_MONTHS = {
    1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL',
    5: 'MAYO', 6: 'JUNIO', 7: 'JULIO', 8: 'AGOSTO',
    9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE'
}
TAG_FIELD_NAME_MAP = {
    'CAMPO1': 'En Santiago  a', 'CAMPO2': 'de', 'CAMPO3': 'de_2',
    'CAMPO4': 'Sres  Administradora de TAG', 'CAMPO5': 'RUT',
    'CAMPO6': 'Representante Legal', 'CAMPO7': 'Domicilio',
    'CAMPO8': 'comuna', 'CAMPO9': 'Ciudad', 'CAMPO10': 'Fono',
    'CAMPO11': 'Email', 'CAMPO12': 'Email2', 'CAMPO13': 'TAG Nundefined',
    'CAMPO14': 'PPU', 'CAMPO15': 'PPU2', 'CAMPO16': 'Obs',
}


def _tag_normalize_rut(value: str) -> str:
    if not value:
        return ''
    cleaned = re.sub(r'[^0-9Kk]', '', value).upper()
    if len(cleaned) < 2:
        return cleaned
    return f"{cleaned[:-1]}-{cleaned[-1]}"


def _tag_normalize_phone(value: str) -> str:
    if not value:
        return ''
    digits = re.sub(r'\D', '', value)
    if len(digits) > 9:
        digits = digits[-9:]
    return digits


def _tag_normalize_patente(value: str) -> str:
    if not value:
        return ''
    cleaned = re.sub(r'[^A-Za-z0-9]', '', value).upper()
    return cleaned


def _tag_split_email(email: str) -> tuple[str, str]:
    if '@' in email:
        parts = email.split('@', 1)
        return parts[0], parts[1]
    return email, ''


def _tag_parse_text(text: str) -> dict:
    def find(pattern):
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        return match.group(1).strip() if match else ''

    nombre = find(r'^\s*Nombre\s*:\s*(.+)$').upper()
    rut = _tag_normalize_rut(find(r'^\s*RUT\s*:\s*(.+)$'))
    direccion_raw = find(r'^\s*Direccion\s*:\s*(.+)$')
    telefono = _tag_normalize_phone(find(r'^\s*Telefono\s*:\s*(.+)$'))
    correo = find(r'^\s*Correo\s*:\s*(.+)$')
    patente = _tag_normalize_patente(find(r'^\s*PATENTE\s*:\s*(.+)$'))
    tag = find(r'^\s*TAG\s*[:\-]?\s*(.+)$')

    direccion_raw = direccion_raw.rstrip('.')
    if ',' in direccion_raw:
        direccion_1, comuna = [p.strip() for p in direccion_raw.split(',', 1)]
    else:
        parts = direccion_raw.split()
        direccion_1 = ' '.join(parts[:-1]).strip()
        comuna = parts[-1].strip() if parts else ''

    email_user, email_domain = _tag_split_email(correo)

    today = datetime.now()
    dia = f"{today.day:02d}"
    mes = TAG_MONTHS[today.month]
    ano = f"{today.year}"

    return {
        'CAMPO1': dia, 'CAMPO2': mes, 'CAMPO3': ano,
        'CAMPO4': nombre, 'CAMPO5': rut, 'CAMPO6': '',
        'CAMPO7': direccion_1, 'CAMPO8': comuna.upper(),
        'CAMPO9': comuna.upper(), 'CAMPO10': telefono,
        'CAMPO11': email_user, 'CAMPO12': email_domain,
        'CAMPO13': tag, 'CAMPO14': patente,
        'CAMPO15': patente, 'CAMPO16': '',
    }


def _tag_fill_pdf(mapping: dict, template_path: Path, output_path: Path) -> None:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import NameObject, BooleanObject

    reader = PdfReader(str(template_path))
    writer = PdfWriter()
    if hasattr(writer, 'clone_document_from_reader'):
        writer.clone_document_from_reader(reader)
    else:
        writer.append_pages_from_reader(reader)
        acroform = reader.trailer.get('/Root', {}).get('/AcroForm')
        if acroform:
            writer._root_object.update({NameObject('/AcroForm'): acroform})

    fields = reader.get_fields() or {}
    target_fields = list(TAG_FIELD_NAME_MAP.values())
    missing_fields = [name for name in target_fields if name not in fields]
    if missing_fields:
        raise RuntimeError(f"Campos no encontrados en PDF: {missing_fields}")

    pdf_mapping = {TAG_FIELD_NAME_MAP[key]: value for key, value in mapping.items()}

    for page in writer.pages:
        writer.update_page_form_field_values(page, pdf_mapping)

    if writer._root_object.get('/AcroForm'):
        writer._root_object['/AcroForm'].update({
            NameObject('/NeedAppearances'): BooleanObject(True)
        })

    with open(output_path, 'wb') as f:
        writer.write(f)


# ===========================================================================
# ENDPOINTS
# ===========================================================================

@app.get("/health")
async def health_check():
    """Health check (no auth required)."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ---------------------------------------------------------------------------
# /api/validate
# ---------------------------------------------------------------------------
@app.post("/api/validate", response_model=ValidarResponse)
async def validar_datos(
    request: ValidarRequest,
    _auth: bool = Depends(verificar_token)
):
    """Valida y parsea datos de entrada segun el tipo de operacion."""

    logger.info(f"[{request.correlation_id}] Validando datos tipo={request.tipo}")

    if request.tipo == "autotramite":
        contrato, errores = parsear_texto_contrato(request.datos_raw)

        if errores:
            return ValidarResponse(
                valido=False,
                errores=[{"campo": e.campo, "mensaje": e.mensaje} for e in errores],
                correlation_id=request.correlation_id
            )

        return ValidarResponse(
            valido=True,
            datos_parseados=contrato.model_dump() if contrato else None,
            errores=[],
            correlation_id=request.correlation_id
        )

    elif request.tipo == "tag":
        try:
            datos = _tag_parse_text(request.datos_raw)
            return ValidarResponse(
                valido=True,
                datos_parseados=datos,
                errores=[],
                correlation_id=request.correlation_id
            )
        except Exception as e:
            return ValidarResponse(
                valido=False,
                errores=[{"campo": "general", "mensaje": str(e)}],
                correlation_id=request.correlation_id
            )

    elif request.tipo == "mail":
        try:
            # Parse mail fields from raw text
            datos = _parse_mail_from_raw(request.datos_raw)
            return ValidarResponse(
                valido=True,
                datos_parseados=datos,
                errores=[],
                correlation_id=request.correlation_id
            )
        except ValueError as e:
            return ValidarResponse(
                valido=False,
                errores=[{"campo": "general", "mensaje": str(e)}],
                correlation_id=request.correlation_id
            )

    else:
        raise HTTPException(status_code=400, detail=f"Tipo invalido: {request.tipo}")


def _parse_mail_from_raw(text: str) -> dict:
    """Parse mail fields from Telegram raw text format."""
    def find(pattern):
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        return match.group(1).strip() if match else ''

    datos_prop = find(r'DATOS_PROPIETARIO\s*:\s*(.+?)(?=\n[A-Z]|\Z)')
    if not datos_prop:
        # Try multiline: everything before VEHICULO line
        match = re.search(
            r'DATOS_PROPIETARIO\s*:\s*(.+?)(?=\nVEHICULO)',
            text, re.IGNORECASE | re.DOTALL
        )
        datos_prop = match.group(1).strip() if match else text

    vehiculo = find(r'VEHICULO\s*:\s*(.+)$')
    precio = find(r'PRECIO\s*:\s*(.+)$')
    fecha = find(r'FECHA_PAGO\s*:\s*(.+)$')
    email_to = find(r'EMAIL\s*:\s*(.+)$')
    cc_raw = find(r'CC\s*:\s*(.+)$')

    cc_list = [e.strip() for e in re.split(r'[,;\s]+', cc_raw) if e.strip() and '@' in e]

    if not email_to:
        raise ValueError("Campo EMAIL es requerido")

    return {
        'datos_propietario': datos_prop,
        'vehiculo': vehiculo,
        'precio_acordado': precio,
        'fecha_pago': fecha,
        'email_to': email_to,
        'cc': cc_list,
    }


# ---------------------------------------------------------------------------
# /api/autotramite/ejecutar
# ---------------------------------------------------------------------------
@app.post("/api/autotramite/ejecutar", response_model=EjecutarResponse)
async def ejecutar_autotramite(
    request: EjecutarAutoTramiteRequest,
    _auth: bool = Depends(verificar_token)
):
    """Ejecuta el flujo AutoTramite (registro o preview)."""

    logger.info(f"[{request.correlation_id}] Ejecutando AutoTramite modo={request.modo}")

    try:
        contrato = ContratoData(**request.datos)

        dry_run = request.modo != "registro"
        screenshot_dir = Path("screenshots")
        screenshot_dir.mkdir(exist_ok=True)

        resultado: ContratoResult = await crear_contrato_autotramite(
            datos=contrato,
            dry_run=dry_run,
            screenshot_path=str(screenshot_dir)
        )

        if resultado.success:
            return EjecutarResponse(
                exito=True,
                pdf_path=resultado.pdf_url,
                mensaje=resultado.mensaje,
                correlation_id=request.correlation_id,
                metadata={
                    "patente": contrato.vehiculo.patente,
                    "timestamp": datetime.now().isoformat()
                }
            )
        else:
            return EjecutarResponse(
                exito=False,
                mensaje=resultado.error or resultado.mensaje,
                correlation_id=request.correlation_id
            )

    except Exception as e:
        logger.error(f"[{request.correlation_id}] Error ejecutando AutoTramite: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# /api/tag/generar
# ---------------------------------------------------------------------------
@app.post("/api/tag/generar", response_model=EjecutarResponse)
async def generar_tag(
    request: TagRequest,
    _auth: bool = Depends(verificar_token)
):
    """Genera PDF de Habilitacion TAG."""

    logger.info(f"[{request.correlation_id}] Generando PDF TAG")

    try:
        mapping = _tag_parse_text(request.datos_raw)
        patente = mapping.get('CAMPO14', 'UNKNOWN')

        TAG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        safe_patente = re.sub(r'[^A-Za-z0-9\-]', '', patente)
        output_path = TAG_OUTPUT_DIR / f"Solicitud-Tag-{safe_patente}.pdf"

        _tag_fill_pdf(mapping, TAG_TEMPLATE_PDF, output_path)

        return EjecutarResponse(
            exito=True,
            pdf_path=str(output_path),
            mensaje="PDF TAG generado exitosamente",
            correlation_id=request.correlation_id,
            metadata={"patente": patente, "filename": output_path.name}
        )

    except Exception as e:
        logger.error(f"[{request.correlation_id}] Error generando TAG: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# /api/mail/enviar
# ---------------------------------------------------------------------------
@app.post("/api/mail/enviar", response_model=EjecutarResponse)
async def enviar_mail(
    request: MailRequest,
    _auth: bool = Depends(verificar_token)
):
    """Envia email de cierre de negocio."""

    logger.info(f"[{request.correlation_id}] Enviando mail de cierre")

    try:
        # Validate SMTP config
        smtp_ok, smtp_msg = validar_smtp_config()
        if not smtp_ok:
            return EjecutarResponse(
                exito=False,
                mensaje=f"SMTP no configurado: {smtp_msg}",
                correlation_id=request.correlation_id
            )

        # Validate mail data
        is_valid, errors = validar_datos_mail(
            datos_prop=request.datos_propietario,
            email_to=request.email_to,
            cc_emails=request.cc,
            vehiculo=request.vehiculo,
            precio=request.precio_acordado,
            fecha=request.fecha_pago
        )
        if not is_valid:
            return EjecutarResponse(
                exito=False,
                mensaje="Validacion fallida: " + "; ".join(errors),
                correlation_id=request.correlation_id
            )

        # Generate email content
        asunto, cuerpo = generar_email_desde_plantilla(
            datos_propietario=request.datos_propietario,
            vehiculo=request.vehiculo,
            precio_acordado=request.precio_acordado,
            fecha_pago=request.fecha_pago
        )

        # Send
        exito, msg = enviar_email_smtp(
            destinatario=request.email_to,
            asunto=asunto,
            cuerpo=cuerpo,
            cc=request.cc if request.cc else None
        )

        if exito:
            return EjecutarResponse(
                exito=True,
                mensaje="Email enviado exitosamente",
                correlation_id=request.correlation_id,
                metadata={
                    "destinatarios": [request.email_to] + request.cc,
                    "timestamp": datetime.now().isoformat()
                }
            )
        else:
            return EjecutarResponse(
                exito=False,
                mensaje=f"Error SMTP: {msg}",
                correlation_id=request.correlation_id
            )

    except Exception as e:
        logger.error(f"[{request.correlation_id}] Error enviando mail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# /api/download/{filename}
# ---------------------------------------------------------------------------
@app.get("/api/download/{filename}")
async def download_pdf(
    filename: str,
    _auth: bool = Depends(verificar_token)
):
    """Descarga un PDF generado."""

    # Sanitize filename to prevent path traversal
    safe_name = Path(filename).name
    if safe_name != filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo invalido")

    for base_dir in ["screenshots", "docs/tag/output"]:
        candidate = Path(base_dir) / safe_name
        if candidate.exists():
            return FileResponse(
                path=str(candidate),
                media_type="application/pdf",
                filename=safe_name
            )

    raise HTTPException(status_code=404, detail="PDF no encontrado")
