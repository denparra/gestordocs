"""
Streamlit UI para AutoTramite MVP
Interfaz simple: Form + Ejecución + Resultado
"""
import streamlit as st
import json
import subprocess
import sys
import re
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from src.config import settings, validar_credenciales
from src.models import parsear_texto_contrato, ContratoData
from src.autotramite import crear_contrato_autotramite, LoginFailedError
from src.logging_utils import get_logger

logger = get_logger(__name__, level=settings.log_level)

TAG_DIR = Path(__file__).parent / 'docs' / 'tag'
TAG_TEMPLATE_PDF = TAG_DIR / 'PDF-EJEMPLO.pdf'
TAG_OUTPUT_DIR = TAG_DIR / 'output'

TAG_MONTHS = {
    1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL', 5: 'MAYO', 6: 'JUNIO',
    7: 'JULIO', 8: 'AGOSTO', 9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE'
}

TAG_REQUIRED_FIELDS = [
    'CAMPO1', 'CAMPO2', 'CAMPO3', 'CAMPO4', 'CAMPO5',
    'CAMPO7', 'CAMPO8', 'CAMPO9', 'CAMPO10',
    'CAMPO11', 'CAMPO12', 'CAMPO13', 'CAMPO14', 'CAMPO15'
]

TAG_FIELD_NAME_MAP = {
    'CAMPO1': 'En Santiago  a',
    'CAMPO2': 'de',
    'CAMPO3': 'de_2',
    'CAMPO4': 'dondo\u00f1a',
    'CAMPO5': 'RUT',
    'CAMPO6': 'Giro',
    'CAMPO7': 'domiciliado a en',
    'CAMPO8': 'comuna',
    'CAMPO9': 'ciudad',
    'CAMPO10': 'fono',
    'CAMPO11': 'mail',
    'CAMPO12': 'undefined',
    'CAMPO13': 'Tag asignado',
    'CAMPO14': '1 Que es propietario mero tenedor yo responsable del veh\u00edculo Placa Patente \u00danica',
    'CAMPO15': 'Patente \u00danica',
    'CAMPO16': 'undefined_2',
}


def _upload_pdf_s3(local_path: Path) -> str:
    try:
        import boto3
    except Exception as exc:
        raise RuntimeError('boto3 no esta instalado. Instala con: pip install boto3') from exc

    bucket = os.getenv('S3_BUCKET')
    if not bucket:
        raise RuntimeError('Falta S3_BUCKET para subir PDF.')

    key_prefix = os.getenv('S3_PREFIX', 'pdf')
    key = f"{key_prefix}/{local_path.name}"
    region = os.getenv('S3_REGION')

    session = boto3.session.Session(
        aws_access_key_id=os.getenv('S3_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('S3_SECRET_ACCESS_KEY'),
        region_name=region,
    )
    client = session.client('s3', endpoint_url=os.getenv('S3_ENDPOINT_URL') or None)
    client.upload_file(str(local_path), bucket, key, ExtraArgs={'ContentType': 'application/pdf'})

    presign = os.getenv('S3_PRESIGN', 'true').lower() != 'false'
    if presign:
        expires = int(os.getenv('S3_PRESIGN_SECONDS', '3600'))
        return client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expires,
        )

    base_url = os.getenv('S3_PUBLIC_BASE_URL')
    if base_url:
        return f"{base_url.rstrip('/')}/{key}"
    return f"s3://{bucket}/{key}"


def _upload_pdf_gcs(local_path: Path) -> str:
    try:
        from google.cloud import storage
    except Exception as exc:
        raise RuntimeError('google-cloud-storage no esta instalado. Instala con: pip install google-cloud-storage') from exc

    bucket_name = os.getenv('GCS_BUCKET')
    if not bucket_name:
        raise RuntimeError('Falta GCS_BUCKET para subir PDF.')

    sa_json = os.getenv('GCP_SERVICE_ACCOUNT_JSON')
    if sa_json:
        client = storage.Client.from_service_account_info(json.loads(sa_json))
    else:
        client = storage.Client()

    bucket = client.bucket(bucket_name)
    prefix = os.getenv('GCS_PREFIX', 'pdf')
    blob_name = f"{prefix}/{local_path.name}"
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(str(local_path), content_type='application/pdf')

    sign = os.getenv('GCS_SIGNED_URL', 'true').lower() != 'false'
    if sign:
        expires = int(os.getenv('GCS_SIGNED_URL_SECONDS', '3600'))
        return blob.generate_signed_url(expiration=timedelta(seconds=expires), method='GET')

    base_url = os.getenv('GCS_PUBLIC_BASE_URL')
    if base_url:
        return f"{base_url.rstrip('/')}/{blob_name}"
    return f"gs://{bucket_name}/{blob_name}"


def _upload_pdf_if_configured(local_path: Path) -> str | None:
    backend = os.getenv('PDF_STORAGE_BACKEND', '').strip().lower()
    if not backend:
        return None
    if backend == 's3':
        return _upload_pdf_s3(local_path)
    if backend == 'gcs':
        return _upload_pdf_gcs(local_path)
    raise RuntimeError("PDF_STORAGE_BACKEND debe ser 's3' o 'gcs'.")


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
    if digits.startswith('56'):
        digits = digits[2:]
    if len(digits) > 9:
        digits = digits[-9:]
    return digits


def _tag_normalize_patente(value: str) -> str:
    if not value:
        return ''
    cleaned = re.sub(r'[^A-Za-z0-9]', '', value).upper()
    if len(cleaned) < 2:
        return cleaned
    return f"{cleaned[:-1]}-{cleaned[-1]}"


def _tag_split_email(value: str):
    if not value or '@' not in value:
        return '', ''
    user, domain = value.split('@', 1)
    return user.strip().upper(), domain.strip().upper()


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
        'CAMPO1': dia,
        'CAMPO2': mes,
        'CAMPO3': ano,
        'CAMPO4': nombre,
        'CAMPO5': rut,
        'CAMPO6': '',
        'CAMPO7': direccion_1,
        'CAMPO8': comuna.upper(),
        'CAMPO9': comuna.upper(),
        'CAMPO10': telefono,
        'CAMPO11': email_user,
        'CAMPO12': email_domain,
        'CAMPO13': tag,
        'CAMPO14': patente,
        'CAMPO15': patente,
        'CAMPO16': '',
    }


def _tag_fill_pdf(mapping: dict, template_path: Path, output_path: Path) -> None:
    try:
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import NameObject, BooleanObject
    except Exception:
        raise RuntimeError('pypdf no esta instalado. Instala con: pip install pypdf')

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
        raise RuntimeError(
            f"Campos no encontrados en PDF: {missing_fields}. "
            "Revisa nombres reales con get_fields()."
        )

    pdf_mapping = {TAG_FIELD_NAME_MAP[key]: value for key, value in mapping.items()}

    for page in writer.pages:
        writer.update_page_form_field_values(page, pdf_mapping)

    if writer._root_object.get('/AcroForm'):
        writer._root_object['/AcroForm'].update({
            NameObject('/NeedAppearances'): BooleanObject(True)
        })

    with open(output_path, 'wb') as f:
        writer.write(f)


# Configuración de página
st.set_page_config(
    page_title='AutoTramite - Registro de Contratos',
    page_icon='📄',
    layout='centered'
)

# Estilos base para menú (variables de tema)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600&family=Work+Sans:wght@400;500&display=swap');
    :root {
        --menu-bg: radial-gradient(circle at 20% 20%, #f5f3ef 0%, #f7f7fb 40%, #f2f6f4 100%);
        --menu-card: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
        --menu-border: rgba(20, 30, 40, 0.08);
        --menu-shadow: rgba(15, 23, 42, 0.08);
        --menu-title: #1d2733;
        --menu-text: #5b6067;
        --menu-tag-bg: rgba(242, 143, 44, 0.12);
        --menu-tag-text: #8a4b10;
        --menu-btn: linear-gradient(135deg, #f28f2c, #f05f2c);
        --menu-btn-shadow: rgba(240, 95, 44, 0.22);
    }
    [data-testid="stAppViewContainer"]:has(#menu-mode) .block-container {
        padding-top: 24px;
        padding-bottom: 32px;
    }
    .menu-header {
        font-family: "Space Grotesk", sans-serif;
        letter-spacing: 0.2px;
        font-size: 32px;
        font-weight: 600;
        color: var(--menu-title);
        margin-bottom: 6px;
    }
    .menu-sub {
        color: var(--menu-text);
        font-family: "Work Sans", sans-serif;
        margin-bottom: 18px;
    }
    .menu-card {
        background: var(--menu-card);
        border: 1px solid var(--menu-border);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 10px 24px var(--menu-shadow);
        min-height: 170px;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }
    .menu-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 16px 28px rgba(15, 23, 42, 0.12);
        border-color: rgba(242, 143, 44, 0.35);
    }
    .menu-card h3 {
        margin: 0 0 8px 0;
        font-size: 20px;
        font-family: "Space Grotesk", sans-serif;
        color: var(--menu-title);
    }
    .menu-card p {
        margin: 0 0 12px 0;
        color: var(--menu-text);
        font-family: "Work Sans", sans-serif;
        font-size: 14px;
    }
    .menu-tag {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 12px;
        background: var(--menu-tag-bg);
        color: var(--menu-tag-text);
        font-family: "Work Sans", sans-serif;
    }
    [data-testid="stAppViewContainer"]:has(#menu-mode) [data-testid="stCheckbox"] label,
    [data-testid="stAppViewContainer"]:has(#menu-mode) [data-testid="stCheckbox"] p {
        color: var(--menu-title);
        font-family: "Work Sans", sans-serif;
    }
    [data-testid="stAppViewContainer"]:has(#menu-mode) .stButton>button {
        border-radius: 12px;
        border: 0;
        background: var(--menu-btn);
        color: #ffffff;
        padding: 10px 14px;
        font-weight: 600;
        width: 100%;
        font-family: "Work Sans", sans-serif;
        box-shadow: 0 10px 18px var(--menu-btn-shadow);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    [data-testid="stAppViewContainer"]:has(#menu-mode) .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 14px 22px rgba(240, 95, 44, 0.28);
    }
    .menu-toggle {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        margin-top: 12px;
    }
    @media (max-width: 720px) {
        .menu-page {
            padding: 18px;
            min-height: 0;
        }
        .menu-card {
            min-height: 160px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Navegación simple
if 'view' not in st.session_state:
    st.session_state.view = 'menu'
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

if st.session_state.view == 'menu':
    st.markdown('<div id="menu-mode"></div>', unsafe_allow_html=True)
    # Toggle de tema
    col_title, col_toggle = st.columns([3, 1])
    with col_title:
        st.markdown('<div class="menu-header">Panel de Automatizaciones</div>', unsafe_allow_html=True)
        st.markdown('<div class="menu-sub">Selecciona un módulo para continuar.</div>', unsafe_allow_html=True)
    with col_toggle:
        st.markdown('<div class="menu-toggle">', unsafe_allow_html=True)
        is_dark = st.toggle('Dark mode', value=st.session_state.theme == 'dark')
        st.session_state.theme = 'dark' if is_dark else 'light'
        st.markdown('</div>', unsafe_allow_html=True)

    # CSS por tema
    if st.session_state.theme == 'dark':
        st.markdown(
            """
            <style>
            :root {
                --menu-bg: radial-gradient(circle at 20% 20%, #20232a 0%, #15181f 55%, #0f1117 100%);
                --menu-card: linear-gradient(135deg, #1c212b 0%, #141821 100%);
                --menu-border: rgba(255, 255, 255, 0.08);
                --menu-shadow: rgba(0, 0, 0, 0.35);
                --menu-title: #f2f4f8;
                --menu-text: #a7b0bb;
                --menu-tag-bg: rgba(248, 182, 66, 0.18);
                --menu-tag-text: #f8b642;
                --menu-btn: linear-gradient(135deg, #f28f2c, #f05f2c);
                --menu-btn-shadow: rgba(240, 95, 44, 0.35);
            }
            body:has(#menu-mode) [data-testid="stAppViewContainer"] {
                background: var(--menu-bg);
            }
            body:has(#menu-mode) [data-testid="stHeader"] {
                background: transparent;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            :root {
                --menu-bg: radial-gradient(circle at 20% 20%, #f5f3ef 0%, #f7f7fb 40%, #f2f6f4 100%);
                --menu-card: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
                --menu-border: rgba(20, 30, 40, 0.08);
                --menu-shadow: rgba(15, 23, 42, 0.08);
                --menu-title: #1d2733;
                --menu-text: #5b6067;
                --menu-tag-bg: rgba(242, 143, 44, 0.12);
                --menu-tag-text: #8a4b10;
                --menu-btn: linear-gradient(135deg, #f28f2c, #f05f2c);
                --menu-btn-shadow: rgba(240, 95, 44, 0.22);
            }
            body:has(#menu-mode) [data-testid="stAppViewContainer"] {
                background: var(--menu-bg);
            }
            body:has(#menu-mode) [data-testid="stHeader"] {
                background: transparent;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    col1, col2, col3 = st.columns(3, gap='large')
    with col1:
        st.markdown(
            """
            <div class="menu-card">
                <h3>AutoTramite</h3>
                <p>Registro automatizado de contratos de compraventa.</p>
                <span class="menu-tag">Activo</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button('Abrir AutoTramite', use_container_width=True, key='open_autotramite'):
            st.session_state.view = 'autotramite'
            st.rerun()

    with col2:
        st.markdown(
            """
            <div class="menu-card">
                <h3>Habilitación Tag</h3>
                <p>Flujo para habilitar TAG y gestión documental.</p>
                <span class="menu-tag">En construcción</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button('Abrir Habilitación Tag', use_container_width=True, key='open_tag'):
            st.session_state.view = 'tag'
            st.rerun()

    with col3:
        st.markdown(
            """
            <div class="menu-card">
                <h3>Mail de Cierre</h3>
                <p>Envío automatizado de correos de cierre de negocio.</p>
                <span class="menu-tag">Activo</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button('Abrir Mail de Cierre', use_container_width=True, key='open_mail'):
            st.session_state.view = 'mail'
            st.rerun()

    st.stop()

if st.session_state.view == 'tag':
    if st.button('<- Volver al menu', use_container_width=True):
        st.session_state.view = 'menu'
        st.rerun()
    st.title('Habilitacion Tag')
    st.markdown('---')

    if 'tag_result' not in st.session_state:
        st.session_state.tag_result = None
    if 'tag_error' not in st.session_state:
        st.session_state.tag_error = None
    if 'tag_pdf_path' not in st.session_state:
        st.session_state.tag_pdf_path = None
    if 'tag_mapping' not in st.session_state:
        st.session_state.tag_mapping = None
    if 'tag_pdf_url' not in st.session_state:
        st.session_state.tag_pdf_url = None
    if 'tag_upload_error' not in st.session_state:
        st.session_state.tag_upload_error = None

    example_tag_text = ''
    example_path = TAG_DIR / 'testtag.md'
    if example_path.exists():
        example_tag_text = example_path.read_text(encoding='utf-8')

    with st.form('tag_form'):
        tag_text = st.text_area(
            'Datos para Solicitud TAG',
            height=240,
            placeholder=example_tag_text or 'Nombre: ...\nRUT: ...\nDireccion: ...\nTelefono: ...\nCorreo: ...\nPATENTE: ...\nTAG ...'
        )
        submit_tag = st.form_submit_button('Generar Solicitud TAG', use_container_width=True)

    if submit_tag:
        st.session_state.tag_result = None
        st.session_state.tag_error = None
        st.session_state.tag_pdf_path = None
        st.session_state.tag_mapping = None
        st.session_state.tag_pdf_url = None
        st.session_state.tag_upload_error = None

        if not tag_text.strip():
            st.error('Debe ingresar el texto de la solicitud.')
        elif not TAG_TEMPLATE_PDF.exists():
            st.error(f'No existe la plantilla PDF: {TAG_TEMPLATE_PDF}')
        else:
            with st.spinner('Generando PDF...'):
                try:
                    mapping = _tag_parse_text(tag_text)
                    missing = [k for k in TAG_REQUIRED_FIELDS if not mapping.get(k)]
                    if missing:
                        raise RuntimeError(f'Campos requeridos vacios: {missing}')

                    patente = mapping.get('CAMPO14') or 'SIN-PATENTE'
                    safe_patente = re.sub(r'[^A-Z0-9-]', '', patente.upper())
                    output_pdf = TAG_OUTPUT_DIR / f"Solicitud-Tag-{safe_patente}.pdf"

                    TAG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                    _tag_fill_pdf(mapping, TAG_TEMPLATE_PDF, output_pdf)

                    st.session_state.tag_result = 'ok'
                    st.session_state.tag_pdf_path = str(output_pdf)
                    st.session_state.tag_mapping = mapping
                    try:
                        st.session_state.tag_pdf_url = _upload_pdf_if_configured(output_pdf)
                    except Exception as e:
                        st.session_state.tag_upload_error = str(e)
                except Exception as e:
                    st.session_state.tag_error = str(e)

    if st.session_state.tag_error:
        st.error(f'Error: {st.session_state.tag_error}')

    if st.session_state.tag_result == 'ok' and st.session_state.tag_pdf_path:
        st.success('PDF generado correctamente.')
        st.caption(f'Archivo: {st.session_state.tag_pdf_path}')
        if st.session_state.tag_mapping:
            with st.expander('Ver datos extraidos'):
                st.json(st.session_state.tag_mapping, expanded=False)

        if st.session_state.tag_pdf_url:
            st.markdown(f"Link externo: {st.session_state.tag_pdf_url}")
        elif st.session_state.tag_upload_error:
            st.warning(f"No se pudo subir a storage externo: {st.session_state.tag_upload_error}")

        try:
            pdf_path = Path(st.session_state.tag_pdf_path)
            if pdf_path.exists():
                with open(pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
                st.download_button(
                    'Descargar PDF',
                    data=pdf_bytes,
                    file_name=pdf_path.name,
                    mime='application/pdf',
                    use_container_width=True
                )
        except Exception as e:
            st.warning(f'No se pudo preparar descarga: {e}')

    st.stop()

# Vista Mail de Cierre
if st.session_state.view == 'mail':
    from src.mail_utils import (
        extraer_nombre_cliente,
        generar_email_desde_plantilla,
        validar_datos_mail,
        enviar_email_smtp,
        validar_smtp_config,
        validar_config,
        guardar_historial_envio,
        get_config,
        cargar_cc_predeterminados,
        parsear_ficha_registro,
    )
    from time import time as get_time

    if st.button('← Volver al menú', use_container_width=True):
        st.session_state.view = 'menu'
        st.rerun()

    st.title('📧 Mail de Cierre - Envío de Confirmación')
    st.markdown('---')

    # Inicializar session state
    if 'mail_resultado' not in st.session_state:
        st.session_state.mail_resultado = None
    if 'mail_preview_data' not in st.session_state:
        st.session_state.mail_preview_data = None
    if 'ultimo_envio_mail' not in st.session_state:
        st.session_state.ultimo_envio_mail = None

    # Validar configuración
    smtp_ok, smtp_error = validar_smtp_config()
    if not smtp_ok:
        st.error(f'❌ {smtp_error}')
        st.info('Configura las variables SMTP_* en el archivo .env')
        st.stop()

    config_ok, config_errors = validar_config()
    if not config_ok:
        st.error('❌ Errores en mail_config.yaml:')
        for error in config_errors:
            st.markdown(f'- {error}')
        st.info('Revisa el archivo docs/correo-cierre/mail_config.yaml')
        st.stop()

    # Cargar ejemplo
    example_mail_text = ''
    example_path = Path('docs/autotramite/test.md')
    if example_path.exists():
        example_mail_text = example_path.read_text(encoding='utf-8')

    # Si no hay preview activo, mostrar formulario
    if st.session_state.mail_preview_data is None:
        st.subheader('1. Ingresar Datos del Cliente')

        with st.form('mail_form'):
            ficha_registro = st.text_area(
                'Ficha Registro (pegar bloque completo)',
                height=250,
                placeholder='''Inscripción : FPYK.18-2
DATOS DEL VEHICULO
Tipo Vehículo : AUTOMOVIL Año : 2013
Marca : CHEVROLET
Modelo : SAIL II 1.4
Nro. Motor : LCU130020645
Nro. Chasis : LSGSA58M4DY101211
Color : ROJO
...
DATOS DEL PROPIETARIO
Nombre : CAMILO IGNACIO MENA MALDONADO
R.U.N. : 19.001.667-6
Fec. adquisición: 07-05-2018''',
                help='Pegue el bloque completo con Inscripción, Datos del Vehículo y Datos del Propietario'
            )

            precio_acordado = st.text_input(
                'Precio Acordado',
                placeholder='LIQUIDO A RECIBIR $17.000.000',
                help='Precio acordado con el cliente'
            )

            fecha_pago = st.text_input(
                'Fecha de Pago',
                placeholder='10-02-2026 AL 13-02-2026',
                help='Rango de fechas de pago'
            )

            st.markdown('---')

            email_destino = st.text_input(
                'Email Destino (TO) *',
                placeholder='cliente@ejemplo.cl',
                help='Email del destinatario principal (requerido)'
            )

            # Cargar CC predeterminados desde config
            cc_predeterminados = cargar_cc_predeterminados()
            allow_additional_cc = get_config('cc.allow_additional', True)

            if cc_predeterminados and not allow_additional_cc:
                # Solo mostrar CC predeterminados (no editable)
                st.info(f"📋 CC predeterminados (automáticos): {', '.join(cc_predeterminados)}")
                cc_emails_input = ''
            elif cc_predeterminados and allow_additional_cc:
                # Mostrar CC predeterminados como valor por defecto, permitir agregar más
                default_cc = ', '.join(cc_predeterminados)
                cc_emails_input = st.text_input(
                    'CC - Copias Visibles',
                    value=default_cc,
                    placeholder='Agrega más emails separados por coma',
                    help=f'IMPORTANTE: Estas copias son VISIBLES. Predeterminados: {default_cc}'
                )
            else:
                # No hay CC predeterminados, campo vacío
                cc_emails_input = st.text_input(
                    'CC - Copias Visibles (opcional)',
                    placeholder='gerencia@queirolo.cl, admin@queirolo.cl',
                    help='Emails separados por coma o espacio. IMPORTANTE: Estas copias son VISIBLES para todos los destinatarios.'
                )

            vista_previa = st.checkbox(
                'Vista previa antes de enviar',
                value=get_config('comportamiento.preview_default', False),
                help='Muestra el email generado para edición antes de enviar'
            )

            submit_mail = st.form_submit_button('🚀 Generar Correo', use_container_width=True)

        if submit_mail:
            st.session_state.mail_resultado = None

            # Parsear Ficha Registro para extraer datos
            parsed_ficha = parsear_ficha_registro(ficha_registro)
            if not parsed_ficha:
                st.error('❌ No se pudo parsear la Ficha Registro. Verifique que contenga: Inscripción, Marca, Modelo, Año, Nombre, R.U.N. y Fec. adquisición')
                st.stop()

            # Extraer variables para el resto del flujo (mantiene compatibilidad)
            datos_propietario = parsed_ficha['datos_propietario_bloque']
            vehiculo = parsed_ficha['vehiculo_final']

            # Parsear CC emails
            cc_emails = []

            # Si no se permite adicionales pero hay predeterminados, usar solo predeterminados
            if cc_predeterminados and not allow_additional_cc:
                cc_emails = cc_predeterminados
            elif cc_emails_input.strip():
                # Separar por coma o espacio
                cc_raw = re.split(r'[,\s]+', cc_emails_input.strip())
                cc_emails = [e.strip() for e in cc_raw if e.strip()]
            elif cc_predeterminados:
                # Si el campo está vacío pero hay predeterminados, usarlos
                cc_emails = cc_predeterminados

            # Validar datos
            es_valido, errores = validar_datos_mail(
                datos_propietario,
                email_destino,
                cc_emails,
                vehiculo,
                precio_acordado,
                fecha_pago
            )

            if not es_valido:
                st.error('❌ Errores de validación:')
                for error in errores:
                    st.markdown(f'- {error}')
            else:
                try:
                    # Generar email desde plantilla
                    asunto, email_body = generar_email_desde_plantilla(
                        datos_propietario,
                        vehiculo,
                        precio_acordado,
                        fecha_pago
                    )

                    if vista_previa:
                        # Guardar datos para preview
                        st.session_state.mail_preview_data = {
                            'asunto': asunto,
                            'cuerpo': email_body,
                            'email_destino': email_destino,
                            'cc_emails': cc_emails,
                            'datos_propietario': datos_propietario,
                            'vehiculo': vehiculo,
                            'precio_acordado': precio_acordado,
                            'fecha_pago': fecha_pago,
                        }
                        st.rerun()
                    else:
                        # Enviar directamente
                        # Verificar cooldown
                        cooldown = get_config('comportamiento.cooldown_segundos', 30)
                        if st.session_state.ultimo_envio_mail:
                            delta = (datetime.now() - st.session_state.ultimo_envio_mail).total_seconds()
                            if delta < cooldown:
                                st.warning(f'⏳ Espera {int(cooldown - delta)}s antes de enviar otro correo')
                                st.stop()

                        with st.spinner('Enviando correo...'):
                            inicio = get_time()
                            success, mensaje = enviar_email_smtp(
                                email_destino,
                                asunto,
                                email_body,
                                cc=cc_emails
                            )
                            duracion_ms = int((get_time() - inicio) * 1000)

                            if success:
                                st.session_state.ultimo_envio_mail = datetime.now()
                                st.session_state.mail_resultado = {
                                    'exito': True,
                                    'email': email_destino,
                                    'cc_emails': cc_emails,
                                    'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'mensaje': mensaje
                                }

                                # Guardar historial
                                nombre_cliente = extraer_nombre_cliente(datos_propietario) or 'DESCONOCIDO'
                                # Extraer patente del vehículo (última parte)
                                patente = vehiculo.split()[-1] if vehiculo else 'SIN-PATENTE'

                                guardar_historial_envio(
                                    email_destino=email_destino,
                                    cc_emails=cc_emails,
                                    nombre_cliente=nombre_cliente,
                                    vehiculo=vehiculo,
                                    patente=patente,
                                    asunto=asunto,
                                    cuerpo=email_body,
                                    exito=True,
                                    mensaje=mensaje,
                                    duracion_ms=duracion_ms
                                )
                            else:
                                st.session_state.mail_resultado = {
                                    'exito': False,
                                    'error': mensaje
                                }

                        st.rerun()

                except Exception as e:
                    st.error(f'❌ Error al generar email: {str(e)}')

    # Vista previa y edición
    elif st.session_state.mail_preview_data is not None:
        st.subheader('2. Vista Previa y Edición')

        preview_data = st.session_state.mail_preview_data

        asunto_editado = st.text_input('Asunto', value=preview_data['asunto'])

        email_editado = st.text_area(
            'Cuerpo del correo (editable)',
            value=preview_data['cuerpo'],
            height=400,
            help='Puedes modificar el texto antes de enviar'
        )

        st.caption(f"📧 Destinatario: {preview_data['email_destino']}")
        if preview_data['cc_emails']:
            st.caption(f"📋 CC (copias visibles): {', '.join(preview_data['cc_emails'])}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button('← Editar Datos', use_container_width=True):
                st.session_state.mail_preview_data = None
                st.rerun()

        with col2:
            if st.button('📤 Enviar Correo', use_container_width=True, type='primary'):
                # Verificar cooldown
                cooldown = get_config('comportamiento.cooldown_segundos', 30)
                if st.session_state.ultimo_envio_mail:
                    delta = (datetime.now() - st.session_state.ultimo_envio_mail).total_seconds()
                    if delta < cooldown:
                        st.warning(f'⏳ Espera {int(cooldown - delta)}s antes de enviar otro correo')
                        st.stop()

                with st.spinner('Enviando correo...'):
                    inicio = get_time()
                    success, mensaje = enviar_email_smtp(
                        preview_data['email_destino'],
                        asunto_editado,
                        email_editado,
                        cc=preview_data['cc_emails']
                    )
                    duracion_ms = int((get_time() - inicio) * 1000)

                    if success:
                        st.session_state.ultimo_envio_mail = datetime.now()
                        st.session_state.mail_resultado = {
                            'exito': True,
                            'email': preview_data['email_destino'],
                            'cc_emails': preview_data['cc_emails'],
                            'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'mensaje': mensaje
                        }

                        # Guardar historial
                        nombre_cliente = extraer_nombre_cliente(preview_data['datos_propietario']) or 'DESCONOCIDO'
                        patente = preview_data['vehiculo'].split()[-1] if preview_data['vehiculo'] else 'SIN-PATENTE'

                        guardar_historial_envio(
                            email_destino=preview_data['email_destino'],
                            cc_emails=preview_data['cc_emails'],
                            nombre_cliente=nombre_cliente,
                            vehiculo=preview_data['vehiculo'],
                            patente=patente,
                            asunto=asunto_editado,
                            cuerpo=email_editado,
                            exito=True,
                            mensaje=mensaje,
                            duracion_ms=duracion_ms
                        )
                    else:
                        st.session_state.mail_resultado = {
                            'exito': False,
                            'error': mensaje
                        }

                    st.session_state.mail_preview_data = None
                    st.rerun()

    # Resultado
    if st.session_state.mail_resultado:
        st.markdown('---')
        st.subheader('3. Resultado')

        if st.session_state.mail_resultado['exito']:
            st.success('✅ Correo enviado exitosamente')
            st.metric('📧 Destinatario', st.session_state.mail_resultado['email'])

            if st.session_state.mail_resultado.get('cc_emails'):
                with st.expander('📋 Copias visibles (CC)'):
                    for email in st.session_state.mail_resultado['cc_emails']:
                        st.caption(f'• {email}')

            st.metric('🕐 Fecha', st.session_state.mail_resultado['fecha'])
            st.caption(st.session_state.mail_resultado['mensaje'])

            if st.button('🔄 Enviar Otro Correo', use_container_width=True):
                st.session_state.mail_resultado = None
                st.session_state.mail_preview_data = None
                st.rerun()
        else:
            st.error('❌ Error al enviar correo')
            st.error(st.session_state.mail_resultado['error'])

            if st.button('🔄 Reintentar', use_container_width=True):
                st.session_state.mail_resultado = None
                st.rerun()

    st.stop()

# Vista AutoTramite (actual)
if st.button('← Volver al menú', use_container_width=True):
    st.session_state.view = 'menu'
    st.rerun()

# Título
st.title('📄 AutoTramite - Registro de Contratos de Compraventa')
st.markdown('---')


# Validar credenciales
creds_ok, creds_error = validar_credenciales()

if not creds_ok:
    st.error(f'❌ Configuración inválida: {creds_error}')
    st.info("""
    **Configurar variables de entorno:**
    
    1. Crear archivo `.env` en la raíz del proyecto
    2. Agregar:
       ```
       AUTOTRAMITE_EMAIL=tu_email@ejemplo.com
       AUTOTRAMITE_PASSWORD=tu_contraseña
       ```
    3. Reiniciar la aplicación
    """)
    st.stop()


# Texto de ejemplo
EJEMPLO_TEXTO = """Inscripción : DRLZ.16-3
DATOS DEL VEHICULO
Tipo Vehículo : AUTOMOVIL Año : 2012
Marca : HYUNDAI
Modelo : ELANTRA GLS 1.6
Nro. Motor : G4FGBU380448
Nro. Chasis : KMHDH41CACU327103
Color : ROJO

DATOS DEL VENDEDOR
Nombre : DENNYS EDUARDO PARRA GRANADILLO
R.U.N. : 26.002.284-9
DIRECCION: AV. LAS CONDES 12461, LAS CONDES. SANTIAGO
Telefono: 975400946
Correo: dparra@queirolo.cl

TASACION 10.000.000
VENTA 10.000.000

DATOS COMPRADOR
Nombre: CAROLINA CECILIA CALLES CALLES
RUT: 26033082-9
Direccion: SERRANO, 266. SANTIAGO CENTRO. SANTIAGO
Telefono: 975400946
Correo: comprador@ejemplo.cl"""


# Inicializar session_state
if 'resultado' not in st.session_state:
    st.session_state.resultado = None
if 'errores_validacion' not in st.session_state:
    st.session_state.errores_validacion = None
if 'contrato_parsed' not in st.session_state:
    st.session_state.contrato_parsed = None
if 'pdf_path' not in st.session_state:
    st.session_state.pdf_path = None
if 'cli_error' not in st.session_state:
    st.session_state.cli_error = None
if 'autotramite_pdf_url' not in st.session_state:
    st.session_state.autotramite_pdf_url = None
if 'autotramite_upload_error' not in st.session_state:
    st.session_state.autotramite_upload_error = None


# Formulario principal
st.subheader('1. Ingresar Datos del Contrato')

with st.form('form_contrato'):
    texto_input = st.text_area(
        'Datos del Contrato (CAV + Nota de Venta)',
        height=300,
        placeholder=EJEMPLO_TEXTO,
        help='Pegue los datos del Certificado de Anotaciones Vigentes (CAV) y la Nota de Venta'
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        dry_run = st.checkbox(
            'Modo Dry-Run (solo validar)',
            value=False,
            help='Si está marcado, solo valida los datos sin registrar el contrato'
        )
    
    with col2:
        submit_button = st.form_submit_button('🚀 Registrar Contrato', use_container_width=True, type='primary')


# Botón para mostrar ejemplo
if st.button('📋 Ver Ejemplo de Formato'):
    st.code(EJEMPLO_TEXTO, language='text')


# Procesar formulario
if submit_button:
    if not texto_input.strip():
        st.error('❌ Debe ingresar los datos del contrato')
    else:
        # Limpiar estados previos
        st.session_state.resultado = None
        st.session_state.errores_validacion = None
        st.session_state.contrato_parsed = None
        st.session_state.autotramite_pdf_url = None
        st.session_state.autotramite_upload_error = None
        
        # Paso 1: Parsear texto
        with st.spinner('📝 Parseando datos...'):
            contrato, errores = parsear_texto_contrato(texto_input)
            
            if errores:
                st.session_state.errores_validacion = errores
            else:
                st.session_state.contrato_parsed = contrato


# Mostrar errores de validación
if st.session_state.errores_validacion:
    st.error('❌ Errores de Validación')
    
    for error in st.session_state.errores_validacion:
        st.markdown(f'- **{error.campo}**: {error.mensaje}')
    
    st.info('💡 Revise el formato del texto ingresado y corrija los errores.')


# Mostrar datos parseados y ejecutar
if st.session_state.contrato_parsed and not st.session_state.errores_validacion:
    contrato: ContratoData = st.session_state.contrato_parsed
    
    st.success('✅ Datos validados correctamente')
    
    # Mostrar resumen
    st.subheader('2. Resumen de Datos')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric('Patente', f'{contrato.vehiculo.patente}-{contrato.vehiculo.patente_dv}')
    
    with col2:
        st.metric('Vehículo', f'{contrato.vehiculo.marca} {contrato.vehiculo.modelo}')
    
    with col3:
        st.metric('Año', contrato.vehiculo.ano)
    
    with st.expander('Ver Detalles Completos'):
        st.json(contrato.model_dump(), expanded=False)
    
    # Ejecutar automatización
    if st.session_state.resultado is None:
        st.subheader('3. Ejecutar Registro')
        
        if st.button('▶️ Confirmar y Ejecutar', type='primary', use_container_width=True):
            with st.spinner(f'⚙️ {"Validando datos..." if dry_run else "Registrando contrato en AutoTramite..."}'):
                try:
                    # Preparar PDF local
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    output_dir = Path(__file__).parent / 'screenshots'
                    output_dir.mkdir(parents=True, exist_ok=True)
                    pdf_path = output_dir / f'preview_{contrato.vehiculo.patente}_{timestamp}.pdf'
                    st.session_state.pdf_path = str(pdf_path)

                    # Guardar input para el CLI
                    input_path = output_dir / f'input_{contrato.vehiculo.patente}_{timestamp}.txt'
                    input_path.write_text(texto_input, encoding='utf-8')
                    result_path = output_dir / f'result_{contrato.vehiculo.patente}_{timestamp}.json'

                    cmd = [
                        sys.executable,
                        str(Path(__file__).parent / 'run_autotramite_cli.py'),
                        '--input', str(input_path),
                        '--output', str(pdf_path),
                        '--result', str(result_path),
                    ]
                    if dry_run:
                        cmd.append('--dry-run')

                    proc = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=False,
                    )

                    stdout_raw = proc.stdout or b""
                    stderr_raw = proc.stderr or b""
                    stdout_text = stdout_raw.decode("utf-8", errors="replace").strip()
                    stderr_text = stderr_raw.decode("utf-8", errors="replace").strip()

                    if result_path.exists():
                        try:
                            resultado = json.loads(result_path.read_text(encoding="utf-8").strip())
                        except Exception:
                            resultado = {
                                'success': False,
                                'error': 'Failed to parse CLI result file',
                                'raw_output': stdout_text,
                            }
                    elif stdout_text:
                        # Fallback: try parse last JSON line
                        json_line = None
                        for line in stdout_text.splitlines()[::-1]:
                            if line.strip().startswith('{') and line.strip().endswith('}'):
                                json_line = line.strip()
                                break
                        if json_line:
                            try:
                                resultado = json.loads(json_line)
                            except Exception:
                                resultado = {
                                    'success': False,
                                    'error': 'Failed to parse CLI output',
                                    'raw_output': stdout_text,
                                }
                        else:
                            resultado = {
                                'success': False,
                                'error': 'CLI returned no JSON',
                                'raw_output': stdout_text,
                            }
                    else:
                        resultado = {
                            'success': False,
                            'error': 'CLI returned no output',
                            'raw_error': stderr_text,
                        }

                    st.session_state.resultado = resultado
                    st.session_state.cli_error = stderr_text or None
                    st.rerun()

                except Exception as e:
                    st.error(f'❌ Error inesperado: {str(e)}')
                    logger.error(f'Error en ejecución: {str(e)}')


# Mostrar resultado
if st.session_state.resultado:
    resultado = st.session_state.resultado

    st.markdown('---')
    st.subheader('4. Resultado')

    if st.session_state.cli_error:
        st.caption(f"CLI stderr: {st.session_state.cli_error}")

    if resultado.get('success'):
        st.success('✅ Operación Exitosa')

        col1, col2 = st.columns(2)

        with col1:
            if resultado.get('operacion_id'):
                st.metric('ID Operación', resultado.get('operacion_id'))
            else:
                st.info('ID de operación no disponible')

        with col2:
            if resultado.get('duracion_segundos') is not None:
                st.metric('Duración', f"{resultado.get('duracion_segundos')}s")

        if resultado.get('mensaje'):
            st.info(f"ℹ️ {resultado.get('mensaje')}")

        if resultado.get('pdf_url'):
            st.markdown(f"📄 [Descargar PDF]({resultado.get('pdf_url')})")

        pdf_path = st.session_state.pdf_path
        if pdf_path and Path(pdf_path).exists():
            if st.session_state.autotramite_pdf_url is None and st.session_state.autotramite_upload_error is None:
                try:
                    st.session_state.autotramite_pdf_url = _upload_pdf_if_configured(Path(pdf_path))
                except Exception as e:
                    st.session_state.autotramite_upload_error = str(e)
            if st.session_state.autotramite_pdf_url:
                st.markdown(f"Link externo: {st.session_state.autotramite_pdf_url}")
            elif st.session_state.autotramite_upload_error:
                st.warning(f"No se pudo subir a storage externo: {st.session_state.autotramite_upload_error}")
            try:
                with open(pdf_path, 'rb') as f:
                    pdf_bytes = f.read()
                st.download_button(
                    '⬇️ Descargar PDF generado',
                    data=pdf_bytes,
                    file_name=Path(pdf_path).name,
                    mime='application/pdf',
                    use_container_width=True
                )
                st.caption(f'Archivo local: {pdf_path}')
            except Exception as e:
                st.warning(f'No se pudo preparar descarga local: {str(e)}')
        
        # Botón para registrar otro
        if st.button('🔄 Registrar Otro Contrato', use_container_width=True):
            st.session_state.resultado = None
            st.session_state.errores_validacion = None
            st.session_state.contrato_parsed = None
            st.session_state.autotramite_pdf_url = None
            st.session_state.autotramite_upload_error = None
            st.rerun()
    
    else:
        st.error('❌ Error en la Operación')

        if resultado.get('validation_errors'):
            st.error('❌ Errores de Validación')
            for err in resultado.get('validation_errors', []):
                st.markdown(f"- **{err.get('campo')}**: {err.get('mensaje')}")
        elif resultado.get('error'):
            st.markdown(f"**Error:** {resultado.get('error')}")
            if resultado.get('raw_output'):
                st.code(resultado.get('raw_output'), language='text')
            if resultado.get('raw_error'):
                st.code(resultado.get('raw_error'), language='text')

        if resultado.get('duracion_segundos') is not None:
            st.caption(f"Duración: {resultado.get('duracion_segundos')}s")

        # Botón para reintentar
        if st.button('🔄 Reintentar', use_container_width=True):
            st.session_state.resultado = None
            st.session_state.autotramite_pdf_url = None
            st.session_state.autotramite_upload_error = None
            st.rerun()


# Footer
st.markdown('---')
st.caption(f'AutoTramite MVP v1.0.0 | {datetime.now().strftime("%Y-%m-%d %H:%M")}')
