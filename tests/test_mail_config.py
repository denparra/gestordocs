"""
Tests unitarios para configuración YAML de mail de cierre
"""
import pytest
from pathlib import Path
from src.mail_utils import cargar_config, get_config, validar_config


def test_cargar_config():
    """Test que se carga correctamente el archivo YAML"""
    config = cargar_config()
    assert isinstance(config, dict)
    assert 'remitente' in config
    assert 'plantillas' in config
    assert 'historial' in config


def test_get_config_simple():
    """Test obtener configuración simple"""
    remitente_email = get_config('remitente.email')
    assert remitente_email is not None
    assert '@' in remitente_email


def test_get_config_nested():
    """Test obtener configuración anidada"""
    firma_incluir = get_config('visual.firma.incluir')
    assert isinstance(firma_incluir, bool)


def test_get_config_default():
    """Test valor por defecto cuando no existe clave"""
    valor = get_config('clave.inexistente', 'default_value')
    assert valor == 'default_value'


def test_get_config_historial():
    """Test configuración de historial"""
    historial_enabled = get_config('historial.enabled')
    assert isinstance(historial_enabled, bool)

    max_archivos = get_config('historial.max_archivos', 100)
    assert isinstance(max_archivos, int)


def test_validar_config():
    """Test validación de configuración"""
    es_valido, errores = validar_config()
    assert es_valido is True
    assert len(errores) == 0


def test_get_config_comportamiento():
    """Test configuración de comportamiento"""
    cooldown = get_config('comportamiento.cooldown_segundos', 30)
    assert isinstance(cooldown, int)
    assert cooldown > 0

    preview_default = get_config('comportamiento.preview_default', False)
    assert isinstance(preview_default, bool)


def test_cargar_cc_predeterminados():
    """Test carga de CC predeterminados desde configuración"""
    from src.mail_utils import cargar_cc_predeterminados

    cc_list = cargar_cc_predeterminados()
    assert isinstance(cc_list, list)

    # Si está habilitado, debe tener emails
    cc_enabled = get_config('cc.enabled', False)
    if cc_enabled:
        assert len(cc_list) > 0
        # Todos deben ser emails válidos
        for email in cc_list:
            assert '@' in email
