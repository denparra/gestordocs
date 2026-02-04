"""
Habilitacion Tag - Test Preview
- Lee docs/tag/testtag.md
- Rellena docs/tag/PDF-EJEMPLO.pdf
- Genera docs/tag/output/PDF-OUTPUT.pdf
"""
import re
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
TEMPLATE_PDF = BASE_DIR / 'PDF-EJEMPLO.pdf'
INPUT_MD = BASE_DIR / 'testtag.md'
OUTPUT_DIR = BASE_DIR / 'output'

MONTHS = {
    1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL', 5: 'MAYO', 6: 'JUNIO',
    7: 'JULIO', 8: 'AGOSTO', 9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE'
}

REQUIRED_FIELDS = [
    'CAMPO1', 'CAMPO2', 'CAMPO3', 'CAMPO4', 'CAMPO5',
    'CAMPO7', 'CAMPO8', 'CAMPO9', 'CAMPO10',
    'CAMPO11', 'CAMPO12', 'CAMPO13', 'CAMPO14', 'CAMPO15'
]

FIELD_NAME_MAP = {
    'CAMPO1': 'En Santiago  a',
    'CAMPO2': 'de',
    'CAMPO3': 'de_2',
    'CAMPO4': 'dondoña',
    'CAMPO5': 'RUT',
    'CAMPO6': 'Giro',
    'CAMPO7': 'domiciliado a en',
    'CAMPO8': 'comuna',
    'CAMPO9': 'ciudad',
    'CAMPO10': 'fono',
    'CAMPO11': 'mail',
    'CAMPO12': 'undefined',
    'CAMPO13': 'Tag asignado',
    'CAMPO14': '1 Que es propietario mero tenedor yo responsable del vehículo Placa Patente Única',
    'CAMPO15': 'Patente Única',
    'CAMPO16': 'undefined_2',
}


def normalize_rut(value: str) -> str:
    if not value:
        return ''
    cleaned = re.sub(r'[^0-9Kk]', '', value).upper()
    if len(cleaned) < 2:
        return cleaned
    return f"{cleaned[:-1]}-{cleaned[-1]}"


def normalize_phone(value: str) -> str:
    if not value:
        return ''
    digits = re.sub(r'\D', '', value)
    if digits.startswith('56'):
        digits = digits[2:]
    if len(digits) > 9:
        digits = digits[-9:]
    return digits


def normalize_patente(value: str) -> str:
    if not value:
        return ''
    cleaned = re.sub(r'[^A-Za-z0-9]', '', value).upper()
    if len(cleaned) < 2:
        return cleaned
    return f"{cleaned[:-1]}-{cleaned[-1]}"


def split_email(value: str):
    if not value or '@' not in value:
        return '', ''
    user, domain = value.split('@', 1)
    return user.strip().upper(), domain.strip().upper()


def parse_text(text: str) -> dict:
    def find(pattern):
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        return match.group(1).strip() if match else ''

    nombre = find(r'^\s*Nombre\s*:\s*(.+)$').upper()
    rut = normalize_rut(find(r'^\s*RUT\s*:\s*(.+)$'))
    direccion_raw = find(r'^\s*Direccion\s*:\s*(.+)$')
    telefono = normalize_phone(find(r'^\s*Telefono\s*:\s*(.+)$'))
    correo = find(r'^\s*Correo\s*:\s*(.+)$')
    patente = normalize_patente(find(r'^\s*PATENTE\s*:\s*(.+)$'))
    tag = find(r'^\s*TAG\s*[:\-]?\s*(.+)$')

    # Direccion
    direccion_raw = direccion_raw.rstrip('.')
    if ',' in direccion_raw:
        direccion_1, comuna = [p.strip() for p in direccion_raw.split(',', 1)]
    else:
        parts = direccion_raw.split()
        direccion_1 = ' '.join(parts[:-1]).strip()
        comuna = parts[-1].strip() if parts else ''

    email_user, email_domain = split_email(correo)

    today = datetime.now()
    dia = f"{today.day:02d}"
    mes = MONTHS[today.month]
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


def fill_pdf(mapping: dict, template_path: Path, output_path: Path) -> None:
    try:
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import NameObject, BooleanObject
    except Exception:
        raise RuntimeError('pypdf no esta instalado. Instala con: pip install pypdf')

    reader = PdfReader(str(template_path))
    writer = PdfWriter()
    if hasattr(writer, "clone_document_from_reader"):
        writer.clone_document_from_reader(reader)
    else:
        writer.append_pages_from_reader(reader)
        acroform = reader.trailer.get("/Root", {}).get("/AcroForm")
        if acroform:
            writer._root_object.update({NameObject("/AcroForm"): acroform})

    fields = reader.get_fields() or {}
    target_fields = list(FIELD_NAME_MAP.values())
    missing_fields = [name for name in target_fields if name not in fields]
    if missing_fields:
        raise RuntimeError(
            f"Campos no encontrados en PDF: {missing_fields}. "
            "Revisa nombres reales con get_fields()."
        )

    pdf_mapping = {FIELD_NAME_MAP[key]: value for key, value in mapping.items()}

    for page in writer.pages:
        writer.update_page_form_field_values(page, pdf_mapping)

    if writer._root_object.get('/AcroForm'):
        writer._root_object['/AcroForm'].update({
            NameObject('/NeedAppearances'): BooleanObject(True)
        })

    with open(output_path, 'wb') as f:
        writer.write(f)


def verify_output(output_path: Path, mapping: dict) -> None:
    if not output_path.exists():
        raise RuntimeError('No se genero el PDF de salida.')
    if output_path.stat().st_size == 0:
        raise RuntimeError('PDF de salida vacio.')

    missing = [k for k in REQUIRED_FIELDS if not mapping.get(k)]
    if missing:
        raise RuntimeError(f'Campos requeridos vacios antes de llenar PDF: {missing}')

    try:
        from pypdf import PdfReader
    except Exception:
        return

    reader = PdfReader(str(output_path))
    fields = reader.get_fields() or {}
    empty = []
    for key in REQUIRED_FIELDS:
        field_name = FIELD_NAME_MAP.get(key)
        val = fields.get(field_name, {}).get('/V') if field_name in fields else None
        if val in (None, ''):
            empty.append(key)
    if empty:
        raise RuntimeError(f'Campos requeridos vacios en el PDF generado: {empty}')


def main() -> int:
    if not TEMPLATE_PDF.exists():
        print(f'ERROR: No existe {TEMPLATE_PDF}')
        return 1
    if not INPUT_MD.exists():
        print(f'ERROR: No existe {INPUT_MD}')
        return 1

    text = INPUT_MD.read_text(encoding='utf-8')
    mapping = parse_text(text)

    patente = mapping.get('CAMPO14') or 'SIN-PATENTE'
    safe_patente = re.sub(r'[^A-Z0-9-]', '', patente.upper())
    output_pdf = OUTPUT_DIR / f"Solicitud-Tag-{safe_patente}.pdf"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fill_pdf(mapping, TEMPLATE_PDF, output_pdf)
    verify_output(output_pdf, mapping)

    print(f'OK: PDF generado en {output_pdf}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
