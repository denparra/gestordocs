"""
Tests unitarios para parsing de mail de cierre
"""
import pytest
from src.mail_utils import extraer_nombre_cliente


def test_extraer_nombre_normal():
    """Test con nombre normal"""
    texto = "Nombre : ORIANA ARAYA"
    assert extraer_nombre_cliente(texto) == "ORIANA ARAYA"


def test_extraer_nombre_espacios():
    """Test con espacios extra"""
    texto = "Nombre  :   ORIANA   "
    assert extraer_nombre_cliente(texto) == "ORIANA"


def test_extraer_nombre_minusculas():
    """Test con minúsculas (debe convertir a mayúsculas)"""
    texto = "nombre: oriana araya"
    assert extraer_nombre_cliente(texto) == "ORIANA ARAYA"


def test_extraer_nombre_no_encontrado():
    """Test cuando no se encuentra el campo Nombre"""
    texto = "RUT: 12345678-9"
    assert extraer_nombre_cliente(texto) is None


def test_extraer_nombre_vacio():
    """Test con campo Nombre vacío"""
    texto = "Nombre : \n"
    assert extraer_nombre_cliente(texto) is None


def test_extraer_nombre_caracteres_especiales():
    """Test con caracteres especiales (tildes, ñ)"""
    texto = "Nombre : MARÍA JOSÉ NÚÑEZ"
    assert extraer_nombre_cliente(texto) == "MARÍA JOSÉ NÚÑEZ"


def test_extraer_nombre_completo():
    """Test con nombre completo en bloque de datos"""
    texto = """DATOS DEL PROPIETARIO
Nombre : ORIANA ISOLINA ARAYA AVENDAÑO
R.U.N. : 10.982.440-2
Fec. adquisición: 20-09-2018
Repertorio : RVM CATEDRAL"""
    assert extraer_nombre_cliente(texto) == "ORIANA ISOLINA ARAYA AVENDAÑO"


def test_extraer_nombre_case_insensitive():
    """Test case-insensitive para variaciones de 'Nombre'"""
    assert extraer_nombre_cliente("NOMBRE : JUAN PEREZ") == "JUAN PEREZ"
    assert extraer_nombre_cliente("nombre : JUAN PEREZ") == "JUAN PEREZ"
    assert extraer_nombre_cliente("Nombre : JUAN PEREZ") == "JUAN PEREZ"


def test_extraer_nombre_multilinea():
    """Test con texto multilínea con varios campos"""
    texto = """
    DATOS DEL PROPIETARIO
    Nombre : PEDRO GONZÁLEZ MARTÍNEZ
    RUT : 12.345.678-9
    Dirección : Calle Falsa 123
    """
    assert extraer_nombre_cliente(texto) == "PEDRO GONZÁLEZ MARTÍNEZ"
