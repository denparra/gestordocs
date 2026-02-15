"""
Modelos Pydantic para datos de contratos + funciones de parsing
Basado en: Sección 0.1 del plan (parsing de texto estructurado)
"""
import re
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from .validators import (
    validar_rut, formatear_rut, validar_patente, limpiar_patente,
    validar_email, validar_telefono, formatear_telefono
)


class DatosPersona(BaseModel):
    """Datos de una persona (vendedor o comprador)"""
    rut: str = Field(..., description='RUT con formato XX.XXX.XXX-X')
    nombres: str = Field(..., description='Nombres de la persona')
    apellido_paterno: str = Field(..., description='Apellido paterno')
    apellido_materno: str = Field(default=' ', description='Apellido materno (opcional)')
    direccion: str = Field(..., description='Dirección completa')
    comuna: str = Field(..., description='Comuna')
    ciudad: str = Field(..., description='Ciudad')
    telefono: str = Field(..., description='Teléfono 8-9 dígitos')
    email: str = Field(..., description='Email válido')
    
    @field_validator('rut')
    @classmethod
    def validar_rut_formato(cls, v: str) -> str:
        if not validar_rut(v):
            raise ValueError(
                f'RUT con formato inválido (ej: 26002284-5): {v}'
            )
        return formatear_rut(v)
    
    @field_validator('telefono')
    @classmethod
    def validar_telefono_formato(cls, v: str) -> str:
        if not validar_telefono(v):
            raise ValueError(f'Teléfono inválido: {v}')
        return formatear_telefono(v)
    
    @field_validator('email')
    @classmethod
    def validar_email_formato(cls, v: str) -> str:
        if not validar_email(v):
            raise ValueError(f'Email inválido: {v}')
        return v.lower().strip()


class DatosVehiculo(BaseModel):
    """Datos del vehículo"""
    patente: str = Field(..., description='Patente sin DV (ej: DRLZ16)')
    patente_dv: str = Field(..., description='Dígito verificador (ej: 3)')
    marca: str = Field(..., description='Marca del vehículo')
    modelo: str = Field(..., description='Modelo del vehículo')
    ano: int = Field(..., description='Año de fabricación', ge=1900, le=2100)
    color: str = Field(default='SIN ESPECIFICAR', description='Color del vehículo')
    chasis: str = Field(..., description='Número de chasis')
    motor: str = Field(..., description='Número de motor')
    tipo_vehiculo: str = Field(default='AUTOMOVIL', description='Tipo de vehículo')
    
    @field_validator('patente')
    @classmethod
    def validar_patente_formato(cls, v: str) -> str:
        patente_limpia = limpiar_patente(v)
        if not validar_patente(patente_limpia):
            raise ValueError(f'Patente con formato inválido: {v}')
        return patente_limpia
    
    @field_validator('patente_dv')
    @classmethod
    def validar_dv_formato(cls, v: str) -> str:
        v_clean = v.upper().strip()
        if not re.match(r'^[0-9K]$', v_clean):
            raise ValueError(f'Dígito verificador inválido: {v}')
        return v_clean


class ContratoData(BaseModel):
    """Datos completos de un contrato de compraventa"""
    vehiculo: DatosVehiculo
    vendedor: DatosPersona
    comprador: DatosPersona
    tasacion: Optional[int] = Field(None, description='Tasación del vehículo', ge=0)
    valor_venta: int = Field(..., description='Valor de venta', ge=0)
    generado_por: str = Field(default='AUTORECENTE SPA (QUEIROLO)', description='Empresa generadora')
    tipo_firma: str = Field(default='fea', description='Tipo de firma (fea = Firma Electrónica Avanzada)')


class ContratoResult(BaseModel):
    """Resultado de la operación de registro de contrato"""
    success: bool = Field(..., description='Si la operación fue exitosa')
    operacion_id: Optional[str] = Field(None, description='ID de operación en AutoTramite')
    pdf_url: Optional[str] = Field(None, description='URL del PDF generado')
    mensaje: str = Field(..., description='Mensaje descriptivo del resultado')
    error: Optional[str] = Field(None, description='Mensaje de error si hubo fallo')
    duracion_segundos: Optional[float] = Field(None, description='Duración de la operación')


class ValidationError(BaseModel):
    """Error de validación de un campo"""
    campo: str = Field(..., description='Nombre del campo con error')
    mensaje: str = Field(..., description='Descripción del error')


# ============================================================================
# FUNCIONES DE PARSING DE TEXTO ESTRUCTURADO
# ============================================================================

def extraer(texto: str, regex: str, flags: int = re.IGNORECASE) -> Optional[str]:
    """
    Extrae valor usando regex
    
    Args:
        texto: Texto fuente
        regex: Expresión regular (debe tener 1 grupo de captura)
        flags: Flags de regex
    
    Returns:
        str: Valor extraído o None
    """
    match = re.search(regex, texto, flags)
    return match.group(1).strip() if match else None


def separar_nombre(nombre_completo: str) -> dict[str, str]:
    """
    Separa nombre completo en nombres y apellidos
    
    Regla: Últimas 2 palabras = apellidos, resto = nombres
    
    Args:
        nombre_completo: Nombre completo (ej: "DENNYS EDUARDO PARRA GRANADILLO")
    
    Returns:
        dict: {'nombres', 'apellido_paterno', 'apellido_materno'}
    
    Examples:
        >>> separar_nombre('DENNYS EDUARDO PARRA GRANADILLO')
        {'nombres': 'DENNYS EDUARDO', 'apellido_paterno': 'PARRA', 'apellido_materno': 'GRANADILLO'}
    """
    palabras = nombre_completo.split()
    
    if len(palabras) >= 4:
        return {
            'nombres': ' '.join(palabras[:-2]),
            'apellido_paterno': palabras[-2],
            'apellido_materno': palabras[-1]
        }
    elif len(palabras) == 3:
        return {
            'nombres': palabras[0],
            'apellido_paterno': palabras[1],
            'apellido_materno': palabras[2]
        }
    elif len(palabras) == 2:
        return {
            'nombres': palabras[0],
            'apellido_paterno': palabras[1],
            'apellido_materno': ' '
        }
    else:
        return {
            'nombres': nombre_completo,
            'apellido_paterno': '',
            'apellido_materno': ' '
        }


def separar_direccion(direccion_completa: str) -> dict[str, str]:
    """
    Separa dirección en: dirección, comuna, ciudad
    
    Formatos soportados:
    - "CALLE 123, COMUNA. CIUDAD"
    - "CALLE 123. COMUNA. CIUDAD"
    
    Args:
        direccion_completa: Dirección completa
    
    Returns:
        dict: {'direccion', 'comuna', 'ciudad'}
    
    Examples:
        >>> separar_direccion('AV. LAS CONDES 12461, LAS CONDES. SANTIAGO')
        {'direccion': 'AV. LAS CONDES 12461', 'comuna': 'LAS CONDES', 'ciudad': 'SANTIAGO'}
    """
    if not direccion_completa:
        return {'direccion': '', 'comuna': '', 'ciudad': ''}
    
    # Intentar separar por coma primero
    partes_coma = [p.strip() for p in direccion_completa.split(',') if p.strip()]
    
    if len(partes_coma) >= 3:
        return {
            'direccion': partes_coma[0],
            'comuna': partes_coma[1],
            'ciudad': partes_coma[2]
        }
    elif len(partes_coma) == 2:
        # Separar resto por punto
        direccion = partes_coma[0]
        resto = partes_coma[1]
        partes_punto = [p.strip() for p in resto.split('.') if p.strip()]
        
        if len(partes_punto) >= 2:
            return {
                'direccion': direccion,
                'comuna': partes_punto[0],
                'ciudad': partes_punto[1]
            }
        elif len(partes_punto) == 1:
            return {
                'direccion': direccion,
                'comuna': partes_punto[0],
                'ciudad': partes_punto[0]
            }
    
    # Fallback: separar por punto
    partes = [p.strip() for p in direccion_completa.split('.') if p.strip()]
    
    if len(partes) >= 3:
        return {
            'direccion': partes[0],
            'comuna': partes[1],
            'ciudad': partes[2]
        }
    elif len(partes) == 2:
        return {
            'direccion': partes[0],
            'comuna': partes[1],
            'ciudad': partes[1]
        }
    
    return {
        'direccion': direccion_completa,
        'comuna': '',
        'ciudad': ''
    }


def _normalizar_monto(valor: Optional[str | int]) -> Optional[int]:
    if valor is None:
        return None
    if isinstance(valor, int):
        return valor

    limpio = re.sub(r'[^0-9]', '', str(valor))
    if not limpio:
        return None
    return int(limpio)


def _extraer_bloque(texto: str, encabezados: list[str], todos_encabezados: list[str]) -> Optional[str]:
    union_encabezados = '|'.join(f'(?:{h})' for h in todos_encabezados)

    for encabezado in encabezados:
        match = re.search(fr'(?im)^\s*(?:{encabezado})\b', texto)
        if not match:
            continue

        inicio = match.end()
        resto = texto[inicio:]
        siguiente = re.search(fr'(?im)^\s*(?:{union_encabezados})\b', resto)
        if siguiente:
            return resto[:siguiente.start()].strip()
        return resto.strip()

    return None


def _extraer_monto(texto: str, etiqueta: str) -> Optional[int]:
    valor = extraer(texto, fr'(?im)^\s*{etiqueta}\s*:?\s*\$?\s*([0-9.]+)\s*$')
    if valor is None:
        valor = extraer(texto, fr'\b{etiqueta}\b\s*:?\s*\$?\s*([0-9.]+)')
    return _normalizar_monto(valor)


def parsear_texto_contrato(
    texto: str,
    tasacion_override: Optional[str | int] = None,
    venta_override: Optional[str | int] = None,
) -> tuple[Optional[ContratoData], List[ValidationError]]:
    """
    Parsea texto estructurado de CAV + Nota de Venta
    
    Args:
        texto: Texto con formato estructurado (ver ejemplo en plan)
    
    Returns:
        tuple: (ContratoData o None, lista de errores)
    """
    errores: List[ValidationError] = []
    
    try:
        # ============ PATENTE ============
        inscripcion_match = re.search(
            r'(?:Inscripci(?:o|ó)n|Inscripcion|Patente)\s*:\s*([A-Z0-9.]+)\s*-\s*([0-9K])',
            texto,
            re.IGNORECASE
        )
        
        if not inscripcion_match:
            errores.append(ValidationError(
                campo='patente',
                mensaje='No se encontró patente en el texto (buscar formato: XXXX00-0)'
            ))
            return None, errores
        
        patente_raw = inscripcion_match.group(1)
        patente_dv = inscripcion_match.group(2).upper()
        patente = limpiar_patente(patente_raw)
        
        # ============ BLOQUES (orden flexible) ============
        encabezados_vehiculo = [r'DATOS\s+(?:DEL\s+)?VEH[IÍ]CULO']
        encabezados_vendedor = [r'DATOS\s+(?:DEL\s+)?VENDEDOR', r'DATOS\s+PROPIETARIO']
        encabezados_comprador = [r'DATOS\s+(?:DEL\s+)?COMPRADOR', r'DATOS\s+COMPRADOR']
        todos_encabezados = encabezados_vehiculo + encabezados_vendedor + encabezados_comprador

        bloque_vehiculo = _extraer_bloque(texto, encabezados_vehiculo, todos_encabezados)
        bloque_vendedor = _extraer_bloque(texto, encabezados_vendedor, todos_encabezados)
        bloque_comprador = _extraer_bloque(texto, encabezados_comprador, todos_encabezados)

        if not bloque_vehiculo:
            errores.append(ValidationError(campo='vehiculo', mensaje='Bloque DATOS DEL VEHICULO no encontrado'))
            return None, errores
        if not bloque_vendedor:
            errores.append(ValidationError(campo='vendedor', mensaje='Bloque DATOS DEL VENDEDOR no encontrado'))
            return None, errores
        if not bloque_comprador:
            errores.append(ValidationError(campo='comprador', mensaje='Bloque DATOS DEL COMPRADOR no encontrado'))
            return None, errores

        # ============ VEHICULO ============
        tipo_vehiculo = extraer(
            bloque_vehiculo,
            r'Tipo\s+Veh[ií]culo\s*:\s*(.+?)(?=\s+A[ñn]o\s*:|\n|$)'
        ) or 'AUTOMOVIL'
        ano_str = extraer(bloque_vehiculo, r'A[ñn]o\s*:\s*(\d{4})')
        marca = extraer(bloque_vehiculo, r'Marca\s*:\s*(.+?)(?:\n|$)')
        modelo = extraer(bloque_vehiculo, r'Modelo\s*:\s*(.+?)(?:\n|$)')
        motor = extraer(bloque_vehiculo, r'Nro\.\s*Motor\s*:\s*(\S+)')
        chasis = extraer(bloque_vehiculo, r'Nro\.\s*(?:Chasis|Vin)\s*:\s*(\S+)')
        color = extraer(bloque_vehiculo, r'Color\s*:\s*(.+?)(?:\n|$)') or 'SIN ESPECIFICAR'
        
        # Validar campos requeridos vehículo
        if not ano_str:
            errores.append(ValidationError(campo='ano', mensaje='Año del vehículo no encontrado'))
        if not marca:
            errores.append(ValidationError(campo='marca', mensaje='Marca no encontrada'))
        if not modelo:
            errores.append(ValidationError(campo='modelo', mensaje='Modelo no encontrado'))
        if not motor:
            errores.append(ValidationError(campo='motor', mensaje='Número de motor no encontrado'))
        if not chasis:
            errores.append(ValidationError(campo='chasis', mensaje='Número de chasis no encontrado'))
        
        if errores:
            return None, errores
        
        # Type assertions after validation
        assert ano_str is not None
        assert marca is not None
        assert modelo is not None
        assert motor is not None
        assert chasis is not None
        
        ano = int(ano_str)
        
        # ============ TASACION Y VENTA ============
        tasacion = _normalizar_monto(tasacion_override)
        if tasacion is None:
            tasacion = _extraer_monto(texto, r'TASACI(?:O|Ó)N')

        valor_venta = _normalizar_monto(venta_override)
        if valor_venta is None:
            valor_venta = _extraer_monto(texto, r'VENTA')

        if valor_venta is None:
            errores.append(ValidationError(campo='venta', mensaje='Valor de venta no encontrado'))
            return None, errores

        # ============ VENDEDOR ============
        nombre_vendedor = extraer(
            bloque_vendedor,
            r'Nombre\s*:\s*(.+?)(?:\n|R\.?U\.?(?:T|N)\.?)'
        )
        if not nombre_vendedor:
            errores.append(ValidationError(campo='vendedor_nombre', mensaje='Nombre del vendedor no encontrado'))
            return None, errores
        
        partes_vendedor = separar_nombre(nombre_vendedor.strip())
        
        rut_vendedor_raw = extraer(
            bloque_vendedor,
            r'R\.?U\.?(?:T|N)\.?\s*:\s*([0-9Kk.-]+)'
        )
        if not rut_vendedor_raw:
            errores.append(ValidationError(campo='vendedor_rut', mensaje='RUT del vendedor no encontrado'))
            return None, errores
        
        rut_vendedor = formatear_rut(rut_vendedor_raw)
        
        dir_vendedor_raw = extraer(
            bloque_vendedor,
            r'Direcci[oó]n\s*:\s*(.+?)(?:\n|Tel[eé]fono|Correo|Email|$)'
        )
        if not dir_vendedor_raw:
            errores.append(ValidationError(campo='vendedor_direccion', mensaje='Dirección del vendedor no encontrada'))
            return None, errores
        
        dir_vendedor = separar_direccion(dir_vendedor_raw)
        
        tel_vendedor = extraer(
            bloque_vendedor,
            r'Tel[eé]fono\s*:\s*(\d+)'
        )
        if not tel_vendedor:
            errores.append(ValidationError(campo='vendedor_telefono', mensaje='Teléfono del vendedor no encontrado'))
            return None, errores
        
        email_vendedor = extraer(
            bloque_vendedor,
            r'(?:Correo|Email)\s*:\s*(\S+@\S+)'
        )
        if not email_vendedor:
            errores.append(ValidationError(campo='vendedor_email', mensaje='Email del vendedor no encontrado'))
            return None, errores
        
        # ============ COMPRADOR ============
        nombre_comprador = extraer(
            bloque_comprador,
            r'Nombre\s*:\s*(.+?)(?:\n|R\.?U\.?(?:T|N)\.?)'
        )
        if not nombre_comprador:
            errores.append(ValidationError(campo='comprador_nombre', mensaje='Nombre del comprador no encontrado'))
            return None, errores
        
        partes_comprador = separar_nombre(nombre_comprador.strip())
        
        rut_comprador_raw = extraer(
            bloque_comprador,
            r'R\.?U\.?(?:T|N)\.?\s*:\s*([0-9Kk.-]+)'
        )
        if not rut_comprador_raw:
            errores.append(ValidationError(campo='comprador_rut', mensaje='RUT del comprador no encontrado'))
            return None, errores
        
        rut_comprador = formatear_rut(rut_comprador_raw)
        
        dir_comprador_raw = extraer(
            bloque_comprador,
            r'Direcci[oó]n\s*:\s*(.+?)(?:\n|Tel[eé]fono|Correo|Email|$)'
        )
        if not dir_comprador_raw:
            errores.append(ValidationError(campo='comprador_direccion', mensaje='Dirección del comprador no encontrada'))
            return None, errores
        
        dir_comprador = separar_direccion(dir_comprador_raw)
        
        tel_comprador = extraer(
            bloque_comprador,
            r'Tel[eé]fono\s*:\s*(\d+)'
        )
        if not tel_comprador:
            errores.append(ValidationError(campo='comprador_telefono', mensaje='Teléfono del comprador no encontrado'))
            return None, errores
        
        email_comprador = extraer(
            bloque_comprador,
            r'(?:Correo|Email)\s*:\s*(\S+@\S+)'
        )
        if not email_comprador:
            errores.append(ValidationError(campo='comprador_email', mensaje='Email del comprador no encontrado'))
            return None, errores
        
        # ============ CREAR MODELOS ============
        vehiculo = DatosVehiculo(
            patente=patente,
            patente_dv=patente_dv,
            marca=marca,
            modelo=modelo,
            ano=ano,
            color=color,
            chasis=chasis,
            motor=motor,
            tipo_vehiculo=tipo_vehiculo
        )
        
        vendedor = DatosPersona(
            rut=rut_vendedor,
            nombres=partes_vendedor['nombres'],
            apellido_paterno=partes_vendedor['apellido_paterno'],
            apellido_materno=partes_vendedor['apellido_materno'],
            direccion=dir_vendedor['direccion'],
            comuna=dir_vendedor['comuna'],
            ciudad=dir_vendedor['ciudad'],
            telefono=tel_vendedor,
            email=email_vendedor
        )
        
        comprador = DatosPersona(
            rut=rut_comprador,
            nombres=partes_comprador['nombres'],
            apellido_paterno=partes_comprador['apellido_paterno'],
            apellido_materno=partes_comprador['apellido_materno'],
            direccion=dir_comprador['direccion'],
            comuna=dir_comprador['comuna'],
            ciudad=dir_comprador['ciudad'],
            telefono=tel_comprador,
            email=email_comprador
        )
        
        contrato = ContratoData(
            vehiculo=vehiculo,
            vendedor=vendedor,
            comprador=comprador,
            tasacion=tasacion,
            valor_venta=valor_venta
        )
        
        return contrato, []
    
    except ValueError as e:
        # Errores de validación de Pydantic
        errores.append(ValidationError(
            campo='general',
            mensaje=f'Error de validación: {str(e)}'
        ))
        return None, errores
    
    except Exception as e:
        errores.append(ValidationError(
            campo='general',
            mensaje=f'Error inesperado al parsear: {str(e)}'
        ))
        return None, errores
