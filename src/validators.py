"""
Validadores de datos chilenos: RUT, patente, email, teléfono
Basado en reglas de: n8n-autotramite-compraventa-workflow-plan.md
"""
import re
from typing import Optional


def validar_rut(rut: str) -> bool:
    """
    Valida formato básico de RUT chileno (sin validar dígito verificador)
    
    Args:
        rut: RUT con o sin formato (ej: "26.002.284-9" o "260022849")
    
    Returns:
        bool: True si el formato es válido
    
    Examples:
        >>> validar_rut('26.002.284-9')
        True
        >>> validar_rut('26.002.284')
        False
    """
    if not rut:
        return False
    
    # Limpiar: solo números y K
    clean = re.sub(r'[^0-9Kk]', '', rut).upper()
    
    # Formato básico: 6-8 dígitos + DV (0-9 o K)
    return bool(re.match(r'^[0-9]{6,8}[0-9K]$', clean))


def formatear_rut(rut: str) -> str:
    """
    Formatea RUT al formato estándar: XX.XXX.XXX-X
    
    Args:
        rut: RUT sin formato o con formato parcial
    
    Returns:
        str: RUT formateado
    
    Examples:
        >>> formatear_rut('260022849')
        '26.002.284-9'
        >>> formatear_rut('26.002.284-9')
        '26.002.284-9'
    """
    if not rut:
        return ''
    
    # Limpiar
    clean = re.sub(r'[^0-9Kk]', '', rut).upper()
    
    if len(clean) < 2:
        return rut
    
    # Separar cuerpo y DV
    cuerpo = clean[:-1]
    dv = clean[-1]
    
    # Agregar puntos de miles
    formateado = re.sub(r'\B(?=(\d{3})+(?!\d))', '.', cuerpo)
    
    return f'{formateado}-{dv}'


def validar_patente(patente: str, dv: Optional[str] = None) -> bool:
    """
    Valida formato de patente chilena
    
    Formatos válidos:
    - Formato antiguo: XXNN (4 letras + 2 números) ej: DRLZ16
    - Formato nuevo: NNXX (2 letras + 4 números) ej: BB1234
    - Formato viejo: XX00XX (2 letras + 2 números + 2 letras) ej: AB12CD
    
    Args:
        patente: Patente sin DV (ej: "DRLZ16")
        dv: Dígito verificador opcional (ej: "3")
    
    Returns:
        bool: True si el formato es válido
    
    Examples:
        >>> validar_patente('DRLZ16', '3')
        True
        >>> validar_patente('BB1234', 'K')
        True
        >>> validar_patente('123', '0')
        False
    """
    if not patente:
        return False
    
    # Limpiar: solo alfanuméricos mayúsculas
    patente_clean = re.sub(r'[^A-Z0-9]', '', patente.upper())
    
    # Validar formato
    formato_antiguo = re.match(r'^[A-Z]{4}[0-9]{2}$', patente_clean)
    formato_nuevo = re.match(r'^[A-Z]{2}[0-9]{4}$', patente_clean)
    formato_viejo = re.match(r'^[A-Z]{2}[0-9]{2}[A-Z]{2}$', patente_clean)
    
    if not (formato_antiguo or formato_nuevo or formato_viejo):
        return False
    
    # Validar DV si se proporciona
    if dv is not None:
        dv_clean = dv.upper()
        # DV debe ser un dígito o K
        if not re.match(r'^[0-9K]$', dv_clean):
            return False
    
    return True


def limpiar_patente(patente: str) -> str:
    """
    Limpia patente quitando puntos y otros caracteres
    
    Args:
        patente: Patente con o sin formato (ej: "DRLZ.16" o "DRLZ16")
    
    Returns:
        str: Patente limpia en mayúsculas
    
    Examples:
        >>> limpiar_patente('DRLZ.16')
        'DRLZ16'
        >>> limpiar_patente('bb-1234')
        'BB1234'
    """
    return re.sub(r'[^A-Z0-9]', '', patente.upper())


def validar_email(email: str) -> bool:
    """
    Valida formato de email
    
    Args:
        email: Email a validar
    
    Returns:
        bool: True si el formato es válido
    
    Examples:
        >>> validar_email('usuario@ejemplo.cl')
        True
        >>> validar_email('invalido')
        False
    """
    if not email:
        return False
    
    # Regex simple pero efectivo para emails
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validar_telefono(telefono: str) -> bool:
    """
    Valida teléfono nacional o internacional (8-15 dígitos)
    
    Args:
        telefono: Teléfono a validar (ej: "912345678" o "61415264522")
    
    Returns:
        bool: True si tiene entre 8 y 15 dígitos
    
    Examples:
        >>> validar_telefono('912345678')
        True
        >>> validar_telefono('22334455')
        True
        >>> validar_telefono('61415264522')
        True
        >>> validar_telefono('123')
        False
    """
    if not telefono:
        return False
    
    # Limpiar: solo dígitos
    clean = re.sub(r'[^0-9]', '', telefono)
    
    # Debe tener entre 8 y 15 dígitos (E.164 max 15)
    return 8 <= len(clean) <= 15


def formatear_telefono(telefono: str) -> str:
    """
    Limpia teléfono dejando solo dígitos
    
    Args:
        telefono: Teléfono con o sin formato
    
    Returns:
        str: Teléfono solo dígitos
    
    Examples:
        >>> formatear_telefono('+56 9 1234 5678')
        '912345678'
    """
    return re.sub(r'[^0-9]', '', telefono)
