"""
Utilidades para el módulo Mail de Cierre
Incluye parsing, generación de emails, envío SMTP y gestión de historial
"""
import os
import re
import json
import smtplib
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.validators import validar_email
from src.config import settings


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

CONFIG_PATH = Path('docs/correo-cierre/mail_config.yaml')
_config_cache: dict | None = None


def cargar_config() -> dict:
    """
    Carga configuración desde mail_config.yaml con cache.

    Returns:
        dict: Configuración completa

    Raises:
        FileNotFoundError: Si no existe mail_config.yaml
        yaml.YAMLError: Si el archivo tiene sintaxis inválida
    """
    global _config_cache

    if _config_cache is not None:
        return _config_cache

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f'Archivo de configuración no encontrado: {CONFIG_PATH}\n'
            'Crea mail_config.yaml desde la plantilla en la documentación.'
        )

    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        _config_cache = yaml.safe_load(f)

    return _config_cache


def get_config(key: str, default: Any = None) -> Any:
    """
    Obtiene valor de configuración por clave con notación de punto.

    Args:
        key: Clave en formato "seccion.subseccion.valor"
        default: Valor por defecto si no existe

    Returns:
        Any: Valor de configuración

    Examples:
        >>> get_config('bcc.enabled')
        True
        >>> get_config('visual.firma.incluir', False)
        True
    """
    config = cargar_config()
    keys = key.split('.')
    value = config

    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default

    return value


def reload_config():
    """
    Recarga configuración desde archivo (útil después de editar YAML).
    """
    global _config_cache
    _config_cache = None
    return cargar_config()


def validar_config() -> tuple[bool, list[str]]:
    """
    Valida que mail_config.yaml esté bien formado.

    Returns:
        tuple[bool, list[str]]: (es_valido, lista_de_errores)
    """
    errores = []

    try:
        config = cargar_config()
    except FileNotFoundError:
        return False, ['Archivo mail_config.yaml no encontrado']
    except yaml.YAMLError as e:
        return False, [f'Error de sintaxis YAML: {str(e)}']

    # Validar secciones requeridas
    required_sections = ['remitente', 'plantillas', 'historial']
    for section in required_sections:
        if section not in config:
            errores.append(f'Sección requerida faltante: {section}')

    # Validar remitente
    remitente_email = config.get('remitente', {}).get('email')
    if not remitente_email or not validar_email(remitente_email):
        errores.append('Email de remitente inválido o faltante')

    return (len(errores) == 0, errores)


# ============================================================================
# PARSING
# ============================================================================

def extraer_nombre_cliente(texto: str) -> str | None:
    """
    Extrae nombre del cliente desde bloque DATOS DEL PROPIETARIO.

    Regla:
    - Buscar línea que contenga "Nombre :" (case-insensitive)
    - Capturar todo lo que sigue después de ":"
    - Normalizar: strip() + upper()

    Args:
        texto: Bloque de texto multilínea

    Returns:
        str | None: Nombre en MAYÚSCULAS o None si no se encuentra

    Examples:
        >>> texto = '''
        ... DATOS DEL PROPIETARIO
        ... Nombre : ORIANA ISOLINA ARAYA AVENDAÑO
        ... R.U.N. : 10.982.440-2
        ... '''
        >>> extraer_nombre_cliente(texto)
        'ORIANA ISOLINA ARAYA AVENDAÑO'
    """
    # Regex: busca "Nombre :" seguido de cualquier texto hasta fin de línea
    match = re.search(
        r'^\s*Nombre\s*:\s*(.+)$',
        texto,
        flags=re.IGNORECASE | re.MULTILINE
    )

    if match:
        nombre = match.group(1).strip().upper()
        return nombre if nombre else None

    return None


def parsear_ficha_registro(texto: str) -> dict | None:
    """
    Parsea bloque 'Ficha Registro' y extrae datos de vehículo y propietario.

    Formato de entrada esperado:
        Inscripción : FPYK.18-2
        DATOS DEL VEHICULO
        Tipo Vehículo : AUTOMOVIL Año : 2013
        Marca : CHEVROLET
        Modelo : SAIL II 1.4
        ...
        DATOS DEL PROPIETARIO
        Nombre : CAMILO IGNACIO MENA MALDONADO
        R.U.N. : 19.001.667-6
        Fec. adquisición: 07-05-2018

    Args:
        texto: Bloque de texto completo pegado por el usuario

    Returns:
        dict con keys:
            - vehiculo_final: 'CHEVROLET SAIL II 1.4 2013 FPYK.18-2'
            - datos_propietario_bloque: texto formateado para template
            - nombre_cliente: 'CAMILO IGNACIO MENA MALDONADO'
        None si faltan campos obligatorios
    """
    if not texto or not texto.strip():
        return None

    # Regex tolerantes a espacios y variaciones
    def buscar(pattern: str) -> str | None:
        match = re.search(pattern, texto, flags=re.IGNORECASE | re.MULTILINE)
        return match.group(1).strip() if match else None

    # Extraer campos
    inscripcion = buscar(r'Inscripci[oó]n\s*:\s*(.+?)(?:\r?\n|$)')
    marca = buscar(r'Marca\s*:\s*(.+?)(?:\r?\n|$)')
    modelo = buscar(r'Modelo\s*:\s*(.+?)(?:\r?\n|$)')
    anio = buscar(r'A[ñn]o\s*:\s*(\d{4})')
    nombre = buscar(r'Nombre\s*:\s*(.+?)(?:\r?\n|$)')
    run = buscar(r'R\.?U\.?(?:N|T)\.?\s*:\s*(.+?)(?:\r?\n|$)')
    fec_adquisicion = buscar(r'Fec\.?\s*adquisici[oó]n\s*:?\s*(.+?)(?:\r?\n|$)')

    # Validar campos obligatorios
    campos_faltantes = []
    if not inscripcion:
        campos_faltantes.append('Inscripción')
    if not marca:
        campos_faltantes.append('Marca')
    if not modelo:
        campos_faltantes.append('Modelo')
    if not anio:
        campos_faltantes.append('Año')
    if not nombre:
        campos_faltantes.append('Nombre')
    if not run:
        campos_faltantes.append('R.U.N.')
    if not fec_adquisicion:
        campos_faltantes.append('Fec. adquisición')

    if campos_faltantes:
        return None

    # Construir vehículo final: MARCA MODELO AÑO INSCRIPCION
    vehiculo_final = f"{marca} {modelo} {anio} {inscripcion}".upper()

    # Construir bloque DATOS DEL PROPIETARIO para template
    datos_propietario_bloque = f"""DATOS DEL PROPIETARIO
Nombre : {nombre.upper()}
R.U.N. : {run}
Fec. adquisición: {fec_adquisicion}"""

    return {
        'vehiculo_final': vehiculo_final,
        'datos_propietario_bloque': datos_propietario_bloque,
        'nombre_cliente': nombre.upper(),
        'inscripcion': inscripcion.upper(),
        'marca': marca.upper(),
        'modelo': modelo.upper(),
        'anio': anio,
        'run': run,
        'fec_adquisicion': fec_adquisicion
    }


# ============================================================================
# GENERACIÓN DE EMAIL
# ============================================================================

def generar_email_desde_plantilla(
    datos_propietario: str,
    vehiculo: str,
    precio_acordado: str,
    fecha_pago: str,
    plantilla_path: Path = Path('docs/correo-cierre/plantilla.md')
) -> tuple[str, str]:
    """
    Genera email desde plantilla con reemplazo de placeholders.

    Args:
        datos_propietario: Bloque DATOS DEL PROPIETARIO
        vehiculo: Descripción del vehículo
        precio_acordado: Precio acordado con cliente
        fecha_pago: Rango de fechas de pago
        plantilla_path: Ruta a plantilla.md

    Returns:
        tuple[str, str]: (asunto, cuerpo_email)

    Raises:
        FileNotFoundError: Si no existe plantilla.md
        ValueError: Si no se puede extraer nombre del cliente
    """
    if not plantilla_path.exists():
        raise FileNotFoundError(f'Plantilla no encontrada: {plantilla_path}')

    # 1. Cargar plantilla
    plantilla = plantilla_path.read_text(encoding='utf-8')

    # 2. Extraer nombre del cliente
    nombre_cliente = extraer_nombre_cliente(datos_propietario)
    if not nombre_cliente:
        raise ValueError('No se pudo extraer nombre del cliente')

    # 3. Reemplazar placeholders
    email_body = plantilla
    email_body = email_body.replace('{NOMBRE_CLIENTE}', nombre_cliente)
    email_body = email_body.replace('{VEHICULO}', vehiculo)
    email_body = email_body.replace('{PRECIO_ACORDADO_CLIENTE}', precio_acordado)
    email_body = email_body.replace('{FECHA_PAGO}', fecha_pago)
    email_body = email_body.replace('{DATOS_PROPIETARIO_COMPLETOS}', datos_propietario)

    # 4. Generar asunto con vehículo completo
    asunto = f'Confirmación de Cierre de Negocio – {vehiculo}'

    return asunto, email_body


# ============================================================================
# VALIDACIÓN
# ============================================================================

def validar_datos_mail(
    datos_prop: str,
    email_to: str,
    cc_emails: list[str],
    vehiculo: str,
    precio: str,
    fecha: str
) -> tuple[bool, list[str]]:
    """
    Valida datos del formulario de mail de cierre.

    Returns:
        tuple: (es_valido, lista_de_errores)
    """
    errores = []

    # 1. Email destino (TO)
    if not validar_email(email_to):
        errores.append('Email destino (TO) inválido')

    # 2. CC emails (opcional, pero si se proporcionan deben ser válidos)
    for cc_email in cc_emails:
        if cc_email.strip() and not validar_email(cc_email.strip()):
            errores.append(f'Email CC inválido: {cc_email}')

    # 3. Parsing de nombre
    nombre_cliente = extraer_nombre_cliente(datos_prop)
    if not nombre_cliente:
        errores.append('Campo "Nombre :" no encontrado en DATOS DEL PROPIETARIO')

    # 4. Campos obligatorios
    if not datos_prop.strip():
        errores.append('DATOS DEL PROPIETARIO es obligatorio')
    if not vehiculo.strip():
        errores.append('Vehículo es obligatorio')
    if not precio.strip():
        errores.append('Precio acordado es obligatorio')
    if not fecha.strip():
        errores.append('Fecha de pago es obligatoria')

    # 5. SMTP config
    if not (settings.smtp_host and settings.smtp_user):
        errores.append('SMTP no configurado en .env (falta SMTP_HOST o SMTP_USER)')

    return (len(errores) == 0, errores)


def validar_smtp_config() -> tuple[bool, str]:
    """
    Valida que SMTP esté configurado.

    Returns:
        tuple[bool, str]: (es_valido, mensaje_error)
    """
    missing = []

    if not settings.smtp_host:
        missing.append('SMTP_HOST')
    if not settings.smtp_port:
        missing.append('SMTP_PORT')
    if not settings.smtp_user:
        missing.append('SMTP_USER')
    if not settings.smtp_pass:
        missing.append('SMTP_PASS')

    if missing:
        return False, f'SMTP no configurado: faltan {", ".join(missing)}'

    return True, ''


def cargar_cc_predeterminados() -> list[str]:
    """
    Carga lista de emails CC predeterminados desde configuración.

    Returns:
        list[str]: Lista de emails para CC predeterminados
    """
    if not get_config('cc.enabled', False):
        return []

    cc_addresses = get_config('cc.addresses', [])

    # Validar que todos los emails sean válidos
    valid_cc = []
    for email in cc_addresses:
        if validar_email(email):
            valid_cc.append(email)

    return valid_cc


# ============================================================================
# ENVÍO SMTP (CON CC VISIBLE)
# ============================================================================

def enviar_email_smtp(
    destinatario: str,
    asunto: str,
    cuerpo: str,
    cc: Optional[list[str]] = None,
    remitente: Optional[str] = None
) -> tuple[bool, str]:
    """
    Envía email via SMTP con soporte para CC (copias visibles).

    IMPORTANTE: A diferencia de BCC, las copias CC son VISIBLES para todos los destinatarios.

    Args:
        destinatario: Email del destinatario principal (TO)
        asunto: Asunto del correo
        cuerpo: Cuerpo del correo (puede ser HTML o texto plano)
        cc: Lista de emails para CC (copias visibles) - opcional
        remitente: Email del remitente (default: SMTP_USER)

    Returns:
        tuple[bool, str]: (exito, mensaje_error_o_confirmacion)

    Example:
        >>> success, msg = enviar_email_smtp(
        ...     'cliente@ejemplo.cl',
        ...     'Cierre de negocio',
        ...     'Buenas tardes...',
        ...     cc=['gerencia@queirolo.cl', 'admin@queirolo.cl']
        ... )
    """
    try:
        # 1. Obtener configuración desde settings
        host = settings.smtp_host
        port = settings.smtp_port or 587
        user = settings.smtp_user
        password = settings.smtp_pass
        secure = (settings.smtp_secure or 'none').lower()

        if not all([host, user, password]):
            return False, 'SMTP no configurado correctamente'

        remitente = remitente or user
        cc = cc or []

        # 2. Validar todos los emails (destinatario + cc)
        if not validar_email(destinatario):
            return False, f'Email destinatario inválido: {destinatario}'

        for email in cc:
            if email.strip() and not validar_email(email.strip()):
                return False, f'Email CC inválido: {email}'

        # 3. Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = remitente
        msg['To'] = destinatario
        msg['Subject'] = asunto

        # IMPORTANTE: CC es VISIBLE (aparece en los headers del email)
        if cc:
            cc_clean = [e.strip() for e in cc if e.strip()]
            if cc_clean:
                msg['Cc'] = ', '.join(cc_clean)

        # Detectar si es HTML o texto plano
        if '<html>' in cuerpo.lower() or '<br>' in cuerpo.lower():
            msg.attach(MIMEText(cuerpo, 'html'))
        else:
            msg.attach(MIMEText(cuerpo, 'plain'))

        # 4. Conectar y enviar
        if secure == 'ssl':
            server = smtplib.SMTP_SSL(host, port)
        else:
            server = smtplib.SMTP(host, port)
            if secure == 'tls':
                server.starttls()

        server.login(user, password)

        # Enviar a destinatario principal + CC
        all_recipients = [destinatario] + [e.strip() for e in cc if e.strip()]
        server.sendmail(msg['From'], all_recipients, msg.as_string())
        server.quit()

        cc_info = f" (+{len([e for e in cc if e.strip()])} CC)" if cc else ""
        return True, f'Email enviado exitosamente a {destinatario}{cc_info}'

    except smtplib.SMTPAuthenticationError:
        return False, 'Error de autenticación SMTP (verifica SMTP_USER y SMTP_PASS)'
    except smtplib.SMTPException as e:
        return False, f'Error SMTP: {str(e)}'
    except Exception as e:
        return False, f'Error inesperado: {str(e)}'


# ============================================================================
# HISTORIAL
# ============================================================================

def ofuscar_email(email: str) -> str:
    """
    Ofusca email para privacidad en logs.

    Examples:
        >>> ofuscar_email('cliente@ejemplo.cl')
        'cl****@****.cl'
    """
    if '@' not in email:
        return email

    user, domain = email.split('@', 1)
    user_ofuscado = user[:2] + '***' if len(user) > 2 else '***'
    domain_parts = domain.split('.')
    domain_ofuscado = '****.' + domain_parts[-1] if len(domain_parts) > 1 else '****'

    return f"{user_ofuscado}@{domain_ofuscado}"


def guardar_historial_envio(
    email_destino: str,
    cc_emails: list[str],
    nombre_cliente: str,
    vehiculo: str,
    patente: str,
    asunto: str,
    cuerpo: str,
    exito: bool,
    mensaje: str,
    duracion_ms: int
) -> Path | None:
    """
    Guarda registro de email enviado en formato JSON liviano.

    Args:
        email_destino: Email del cliente (TO)
        cc_emails: Lista de emails CC
        nombre_cliente: Nombre del cliente (sin ofuscar)
        vehiculo: Descripción del vehículo
        patente: Patente del vehículo
        asunto: Asunto del email
        cuerpo: Cuerpo completo del email
        exito: Si el envío fue exitoso
        mensaje: Mensaje de resultado
        duracion_ms: Duración del envío en milisegundos

    Returns:
        Path: Ruta al archivo JSON creado o None si historial deshabilitado
    """
    # 1. Validar que historial esté habilitado
    if not get_config('historial.enabled', True):
        return None

    # 2. Crear directorio si no existe
    historial_dir = Path(get_config('historial.directorio', 'docs/correo-cierre/enviados'))
    historial_dir.mkdir(parents=True, exist_ok=True)

    # 3. Generar timestamp y nombre de archivo
    timestamp = datetime.now()
    timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
    patente_safe = patente.replace('.', '').replace('-', '')
    filename = f"{timestamp_str}_{patente_safe}.json"
    filepath = historial_dir / filename

    # 4. Ofuscar email si está configurado
    incluir_cuerpo = get_config('historial.incluir_cuerpo', True)
    campos_ofuscados = get_config('historial.campos_ofuscados', ['email_destinatario'])

    email_display = email_destino
    if 'email_destinatario' in campos_ofuscados:
        email_display = ofuscar_email(email_destino)

    cc_display = cc_emails
    if 'cc_addresses' in campos_ofuscados:
        cc_display = [ofuscar_email(e) for e in cc_emails]

    # 5. Construir objeto JSON
    historial_data = {
        'metadata': {
            'timestamp': timestamp.isoformat(),
            'usuario': settings.smtp_user or 'desconocido',
            'version_app': '1.0.0'
        },
        'destinatario': {
            'email': email_display,
            'nombre_cliente': nombre_cliente
        },
        'cc': {
            'count': len([e for e in cc_emails if e.strip()]),
            'addresses': cc_display
        },
        'vehiculo': {
            'descripcion': vehiculo,
            'patente': patente
        },
        'email': {
            'asunto': asunto,
            'cuerpo_preview': cuerpo[:100] + '...' if len(cuerpo) > 100 else cuerpo,
            'cuerpo_completo': cuerpo if incluir_cuerpo else '[omitido por config]'
        },
        'resultado': {
            'exito': exito,
            'mensaje': mensaje,
            'duracion_ms': duracion_ms
        }
    }

    # 6. Guardar archivo
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(historial_data, f, indent=2, ensure_ascii=False)

    # 7. Rotar archivos si excede límite
    rotar_historial(historial_dir)

    return filepath


def rotar_historial(directorio: Path):
    """
    Elimina archivos viejos si excede el límite configurado.

    Args:
        directorio: Directorio de historial
    """
    max_archivos = get_config('historial.max_archivos', 100)
    archivos = sorted(directorio.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)

    if len(archivos) > max_archivos:
        for archivo in archivos[max_archivos:]:
            archivo.unlink()
