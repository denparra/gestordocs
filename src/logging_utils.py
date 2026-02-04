"""
Logging seguro con ofuscación de datos sensibles (PII)
Basado en: Sección 7.4 del plan
"""
import logging
import sys
from typing import Any, Dict, Optional
from pathlib import Path


def ofuscar_rut(rut: str) -> str:
    """
    Ofusca RUT mostrando solo primeros 4 dígitos
    
    Args:
        rut: RUT completo (ej: "26.002.284-9")
    
    Returns:
        str: RUT ofuscado (ej: "26.0****")
    
    Examples:
        >>> ofuscar_rut('26.002.284-9')
        '26.0****'
    """
    if not rut or len(rut) < 4:
        return '****'
    
    return rut[:4] + '****'


def ofuscar_telefono(telefono: str) -> str:
    """
    Ofusca teléfono mostrando solo primeros 3 dígitos
    
    Args:
        telefono: Teléfono completo (ej: "912345678")
    
    Returns:
        str: Teléfono ofuscado (ej: "912****")
    
    Examples:
        >>> ofuscar_telefono('912345678')
        '912****'
    """
    if not telefono or len(telefono) < 3:
        return '****'
    
    return telefono[:3] + '****'


def ofuscar_email(email: str) -> str:
    """
    Ofusca email mostrando solo dominio
    
    Args:
        email: Email completo (ej: "usuario@ejemplo.cl")
    
    Returns:
        str: Email ofuscado (ej: "****@ejemplo.cl")
    
    Examples:
        >>> ofuscar_email('usuario@ejemplo.cl')
        '****@ejemplo.cl'
    """
    if not email or '@' not in email:
        return '****'
    
    _, dominio = email.split('@', 1)
    return f'****@{dominio}'


def ofuscar_datos_sensibles(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ofusca todos los datos sensibles en un diccionario
    
    Args:
        data: Diccionario con datos potencialmente sensibles
    
    Returns:
        Dict: Diccionario con datos ofuscados
    """
    data_ofuscada = data.copy()
    
    # Campos que siempre se ofuscan
    campos_rut = ['rut', 'vendedor_rut', 'comprador_rut']
    campos_telefono = ['telefono', 'vendedor_telefono', 'comprador_telefono']
    campos_email = ['email', 'correo', 'vendedor_email', 'comprador_email', 'vendedor_correo', 'comprador_correo']
    campos_credenciales = ['password', 'clave', 'token', 'api_key']
    
    for campo in campos_rut:
        if campo in data_ofuscada:
            data_ofuscada[campo] = ofuscar_rut(str(data_ofuscada[campo]))
    
    for campo in campos_telefono:
        if campo in data_ofuscada:
            data_ofuscada[campo] = ofuscar_telefono(str(data_ofuscada[campo]))
    
    for campo in campos_email:
        if campo in data_ofuscada:
            data_ofuscada[campo] = ofuscar_email(str(data_ofuscada[campo]))
    
    for campo in campos_credenciales:
        if campo in data_ofuscada:
            data_ofuscada[campo] = '***REDACTED***'
    
    return data_ofuscada


class SecureLogger:
    """
    Logger que automáticamente ofusca datos sensibles
    """
    
    def __init__(self, name: str, level: str = 'INFO', log_file: Optional[str] = None):
        """
        Inicializa logger seguro
        
        Args:
            name: Nombre del logger
            level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path opcional para guardar logs en archivo
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Evitar duplicados
        if self.logger.handlers:
            return
        
        # Formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Handler archivo (opcional)
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def _safe_log(self, level: str, msg: str, extra: Optional[Dict[str, Any]] = None):
        """
        Log con ofuscación automática de datos sensibles
        
        Args:
            level: Nivel de log
            msg: Mensaje
            extra: Datos extra (serán ofuscados)
        """
        log_func = getattr(self.logger, level.lower())
        
        if extra:
            extra_ofuscado = ofuscar_datos_sensibles(extra)
            msg_completo = f'{msg} | {extra_ofuscado}'
            log_func(msg_completo)
        else:
            log_func(msg)
    
    def debug(self, msg: str, extra: Optional[Dict[str, Any]] = None):
        """Log nivel DEBUG"""
        self._safe_log('debug', msg, extra)
    
    def info(self, msg: str, extra: Optional[Dict[str, Any]] = None):
        """Log nivel INFO"""
        self._safe_log('info', msg, extra)
    
    def warning(self, msg: str, extra: Optional[Dict[str, Any]] = None):
        """Log nivel WARNING"""
        self._safe_log('warning', msg, extra)
    
    def error(self, msg: str, extra: Optional[Dict[str, Any]] = None):
        """Log nivel ERROR"""
        self._safe_log('error', msg, extra)
    
    def critical(self, msg: str, extra: Optional[Dict[str, Any]] = None):
        """Log nivel CRITICAL"""
        self._safe_log('critical', msg, extra)


def get_logger(name: str, level: str = 'INFO', log_file: Optional[str] = None) -> SecureLogger:
    """
    Factory para crear logger seguro
    
    Args:
        name: Nombre del logger
        level: Nivel de logging
        log_file: Path opcional para archivo de logs
    
    Returns:
        SecureLogger: Instancia de logger seguro
    """
    return SecureLogger(name, level, log_file)
