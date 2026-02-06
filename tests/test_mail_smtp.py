"""
Tests unitarios para envío SMTP (mocked)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.mail_utils import enviar_email_smtp, validar_smtp_config, validar_datos_mail


@patch('src.mail_utils.settings')
def test_validar_smtp_config_ok(mock_settings):
    """Test validación SMTP con configuración correcta"""
    mock_settings.smtp_host = 'smtp.test.com'
    mock_settings.smtp_port = 587
    mock_settings.smtp_user = 'test@test.com'
    mock_settings.smtp_pass = 'testpass'

    es_valido, mensaje = validar_smtp_config()
    assert es_valido is True
    assert mensaje == ''


@patch('src.mail_utils.settings')
def test_validar_smtp_config_faltante(mock_settings):
    """Test validación SMTP con configuración incompleta"""
    mock_settings.smtp_host = 'smtp.test.com'
    mock_settings.smtp_port = None
    mock_settings.smtp_user = None
    mock_settings.smtp_pass = None

    es_valido, mensaje = validar_smtp_config()
    assert es_valido is False
    assert 'SMTP_USER' in mensaje or 'SMTP_PASS' in mensaje


@patch('src.mail_utils.settings')
@patch('smtplib.SMTP')
def test_enviar_email_smtp_success(mock_smtp, mock_settings):
    """Test envío de email exitoso"""
    # Mock settings
    mock_settings.smtp_host = 'smtp.test.com'
    mock_settings.smtp_port = 587
    mock_settings.smtp_user = 'test@test.com'
    mock_settings.smtp_pass = 'testpass'
    mock_settings.smtp_secure = 'tls'

    # Mock SMTP server
    mock_server = MagicMock()
    mock_smtp.return_value = mock_server

    success, mensaje = enviar_email_smtp(
        'cliente@test.com',
        'Test Subject',
        'Test Body'
    )

    assert success is True
    assert 'exitosamente' in mensaje
    assert mock_server.starttls.called
    assert mock_server.login.called
    assert mock_server.sendmail.called
    assert mock_server.quit.called


@patch('src.mail_utils.settings')
@patch('smtplib.SMTP')
def test_enviar_email_smtp_con_cc(mock_smtp, mock_settings):
    """Test envío de email con CC"""
    # Mock settings
    mock_settings.smtp_host = 'smtp.test.com'
    mock_settings.smtp_port = 587
    mock_settings.smtp_user = 'test@test.com'
    mock_settings.smtp_pass = 'testpass'
    mock_settings.smtp_secure = 'tls'

    mock_server = MagicMock()
    mock_smtp.return_value = mock_server

    cc_emails = ['gerencia@test.com', 'admin@test.com']

    success, mensaje = enviar_email_smtp(
        'cliente@test.com',
        'Test Subject',
        'Test Body',
        cc=cc_emails
    )

    assert success is True
    assert '+2 CC' in mensaje
    assert mock_server.sendmail.called


@patch('src.mail_utils.settings')
def test_enviar_email_smtp_email_invalido(mock_settings):
    """Test envío con email inválido"""
    # Mock settings
    mock_settings.smtp_host = 'smtp.test.com'
    mock_settings.smtp_port = 587
    mock_settings.smtp_user = 'test@test.com'
    mock_settings.smtp_pass = 'testpass'
    mock_settings.smtp_secure = 'tls'

    success, mensaje = enviar_email_smtp(
        'email_invalido',
        'Test Subject',
        'Test Body'
    )

    assert success is False
    assert 'inválido' in mensaje


@patch('src.mail_utils.settings')
def test_validar_datos_mail_ok(mock_settings):
    """Test validación de datos completos y correctos"""
    mock_settings.smtp_host = 'smtp.test.com'
    mock_settings.smtp_user = 'test@test.com'

    datos_prop = "Nombre : ORIANA ARAYA\nRUT : 12345678-9"
    email_to = "cliente@test.com"
    cc_emails = ["admin@test.com"]
    vehiculo = "JEEP GRAND CHEROKEE"
    precio = "LIQUIDO $17.000.000"
    fecha = "10-02-2026"

    es_valido, errores = validar_datos_mail(
        datos_prop, email_to, cc_emails, vehiculo, precio, fecha
    )

    assert es_valido is True
    assert len(errores) == 0


@patch('src.mail_utils.settings')
def test_validar_datos_mail_email_invalido(mock_settings):
    """Test validación con email inválido"""
    mock_settings.smtp_host = 'smtp.test.com'
    mock_settings.smtp_user = 'test@test.com'

    datos_prop = "Nombre : ORIANA ARAYA"
    email_to = "email_invalido"
    cc_emails = []
    vehiculo = "JEEP"
    precio = "10000"
    fecha = "10-02-2026"

    es_valido, errores = validar_datos_mail(
        datos_prop, email_to, cc_emails, vehiculo, precio, fecha
    )

    assert es_valido is False
    assert any('Email destino' in e for e in errores)


@patch('src.mail_utils.settings')
def test_validar_datos_mail_sin_nombre(mock_settings):
    """Test validación sin campo Nombre"""
    mock_settings.smtp_host = 'smtp.test.com'
    mock_settings.smtp_user = 'test@test.com'

    datos_prop = "RUT : 12345678-9"
    email_to = "cliente@test.com"
    cc_emails = []
    vehiculo = "JEEP"
    precio = "10000"
    fecha = "10-02-2026"

    es_valido, errores = validar_datos_mail(
        datos_prop, email_to, cc_emails, vehiculo, precio, fecha
    )

    assert es_valido is False
    assert any('Nombre' in e for e in errores)


@patch('src.mail_utils.settings')
def test_validar_datos_mail_cc_invalido(mock_settings):
    """Test validación con CC inválido"""
    mock_settings.smtp_host = 'smtp.test.com'
    mock_settings.smtp_user = 'test@test.com'

    datos_prop = "Nombre : ORIANA ARAYA"
    email_to = "cliente@test.com"
    cc_emails = ["email_invalido"]
    vehiculo = "JEEP"
    precio = "10000"
    fecha = "10-02-2026"

    es_valido, errores = validar_datos_mail(
        datos_prop, email_to, cc_emails, vehiculo, precio, fecha
    )

    assert es_valido is False
    assert any('CC inválido' in e for e in errores)
