"""
Configuración y variables de entorno
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación desde variables de entorno"""
    
    # Credenciales AutoTramite (REQUERIDAS)
    autotramite_email: str = ''
    autotramite_password: str = ''
    
    # URLs
    autotramite_base_url: str = 'https://autotramite.cl'
    autotramite_login_url: str = 'https://autotramite.cl/secciones/login.php'
    autotramite_form_url: str = 'https://autotramite.cl/secciones/vista_personas_empresas.php'
    
    # Timeouts (milisegundos)
    timeout_navigation: int = 30000
    timeout_element: int = 10000
    timeout_animation: int = 500
    
    # Reintentos
    max_reintentos: int = 3
    delay_base_ms: int = 2000
    
    # Logging
    log_level: str = 'INFO'
    log_file: Optional[str] = None
    
    # Playwright
    playwright_headless: bool = True
    playwright_slow_mo: int = 0  # ms de delay entre acciones (útil para debugging)
    
    # SMTP Configuration (para envío de emails)
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_pass: Optional[str] = None
    smtp_secure: Optional[str] = 'none'  # 'tls', 'ssl', 'none', 'false'
    
    # Valores por defecto del contrato
    generado_por_default: str = 'AUTORECENTE SPA (QUEIROLO)'
    tipo_firma_default: str = 'fea'  # Firma Electrónica Avanzada
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False


# Instancia global de configuración
settings = Settings()


# Validar que credenciales estén configuradas
def validar_credenciales() -> tuple[bool, str]:
    """
    Valida que las credenciales de AutoTramite estén configuradas
    
    Returns:
        tuple[bool, str]: (is_valid, mensaje_error)
    """
    if not settings.autotramite_email:
        return False, 'AUTOTRAMITE_EMAIL no configurado en variables de entorno'
    
    if not settings.autotramite_password:
        return False, 'AUTOTRAMITE_PASSWORD no configurado en variables de entorno'
    
    if '@' not in settings.autotramite_email:
        return False, 'AUTOTRAMITE_EMAIL tiene formato inválido'
    
    return True, ''


# Selectores CSS/ID validados (Sección 5.2 del plan)
SELECTORS = {
    # Login
    'login_email': '#Correo',
    'login_password': '#Clave',
    'login_submit': 'button:has-text("Iniciar")',
    
    # Vehículo
    'vehiculo_patente': '#patenter',
    'vehiculo_dv': '#DvPatente',
    'vehiculo_marca': '#marca',
    'vehiculo_modelo': '#modelo',
    'vehiculo_ano': '#anhio',  # IMPORTANTE: "anhio" no "ano"
    'vehiculo_color': '#color',
    'vehiculo_chasis': '#nchasis',
    'vehiculo_motor': '#nmotor',
    'vehiculo_tipo': '#tipovehiculo',
    'vehiculo_tasacion': '#tasacion',
    'vehiculo_valor_venta': '#valor_venta',
    
    # Vendedor
    'vendedor_rut': '#rutv',
    'vendedor_nombres': '#nombrev',
    'vendedor_ap_paterno': '#apellidopv',
    'vendedor_ap_materno': '#apellidomv',
    'vendedor_direccion': '#direccionv',
    'vendedor_comuna': '#comunav',
    'vendedor_ciudad': '#ciudadv',
    'vendedor_telefono': '#telefonov',
    'vendedor_email': '#correov',
    
    # Comprador
    'comprador_rut': '#rutc',
    'comprador_nombres': '#nombrec',
    'comprador_ap_paterno': '#apellidopc',
    'comprador_ap_materno': '#apellidomc',
    'comprador_direccion': '#direccionc',
    'comprador_comuna': '#comunac',
    'comprador_ciudad': '#ciudadc',
    'comprador_telefono': '#telefonoc',
    'comprador_email': '#correoc',
    
    # Configuración
    'config_pago_contado': '#Contado',
    'config_pago_credito': '#Credito',
    'config_operador': '#operador',
    'config_firma_electronica': '#firmaElec',
    
    # Botones
    'btn_previsualizar': 'button:has-text("Previsualizar PDF")',
    'btn_solicitar_info': 'button:has-text("Solicitar Información")',
    'btn_registrar_operacion': 'button:has-text("Registrar Operacion")',
}
