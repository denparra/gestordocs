"""
Tests unitarios para validadores
"""
import pytest
from src.validators import (
    validar_rut, formatear_rut, validar_patente, limpiar_patente,
    validar_email, validar_telefono, formatear_telefono
)
from src.models import separar_nombre, separar_direccion


class TestValidarRUT:
    def test_rut_valido_con_puntos(self):
        assert validar_rut('26.002.284-9') == True
    
    def test_rut_valido_sin_puntos(self):
        assert validar_rut('260022849') == True
    
    def test_rut_invalido_sin_dv(self):
        assert validar_rut('26.002.284') == False
    
    def test_rut_con_k(self):
        assert validar_rut('11.111.111-K') == True
    
    def test_rut_vacio(self):
        assert validar_rut('') == False
    
    def test_rut_muy_corto(self):
        assert validar_rut('1-9') == False


class TestFormatearRUT:
    def test_formatear_rut_sin_puntos(self):
        assert formatear_rut('260022849') == '26.002.284-9'
    
    def test_formatear_rut_ya_formateado(self):
        assert formatear_rut('26.002.284-9') == '26.002.284-9'
    
    def test_formatear_rut_con_k(self):
        assert formatear_rut('11111111k') == '11.111.111-K'


class TestValidarPatente:
    def test_patente_formato_antiguo(self):
        assert validar_patente('DRLZ16', '3') == True
    
    def test_patente_formato_nuevo(self):
        assert validar_patente('BB1234', 'K') == True
    
    def test_patente_con_punto(self):
        patente_limpia = limpiar_patente('DRLZ.16')
        assert validar_patente(patente_limpia, '3') == True
    
    def test_patente_invalida_muy_corta(self):
        assert validar_patente('AB12', '0') == False
    
    def test_patente_invalida_solo_numeros(self):
        assert validar_patente('123456', '0') == False


class TestLimpiarPatente:
    def test_limpiar_patente_con_punto(self):
        assert limpiar_patente('DRLZ.16') == 'DRLZ16'
    
    def test_limpiar_patente_con_guion(self):
        assert limpiar_patente('BB-1234') == 'BB1234'
    
    def test_limpiar_patente_minusculas(self):
        assert limpiar_patente('drlz16') == 'DRLZ16'


class TestValidarEmail:
    def test_email_valido(self):
        assert validar_email('usuario@ejemplo.cl') == True
    
    def test_email_valido_con_subdomain(self):
        assert validar_email('usuario@mail.ejemplo.com') == True
    
    def test_email_invalido_sin_arroba(self):
        assert validar_email('usuario.ejemplo.cl') == False
    
    def test_email_invalido_sin_dominio(self):
        assert validar_email('usuario@') == False
    
    def test_email_vacio(self):
        assert validar_email('') == False


class TestValidarTelefono:
    def test_telefono_9_digitos(self):
        assert validar_telefono('912345678') == True
    
    def test_telefono_8_digitos(self):
        assert validar_telefono('22334455') == True
    
    def test_telefono_con_espacios(self):
        assert validar_telefono('9 1234 5678') == True

    def test_telefono_whatsapp_extranjero(self):
        assert validar_telefono('61415264522') == True
    
    def test_telefono_muy_corto(self):
        assert validar_telefono('123') == False
    
    def test_telefono_muy_largo(self):
        assert validar_telefono('1234567890123456') == False


class TestFormatearTelefono:
    def test_formatear_con_espacios(self):
        assert formatear_telefono('9 1234 5678') == '912345678'
    
    def test_formatear_con_guiones(self):
        assert formatear_telefono('9-1234-5678') == '912345678'
    
    def test_formatear_con_codigo_pais(self):
        assert formatear_telefono('+56 9 1234 5678') == '56912345678'


class TestSepararNombre:
    def test_nombre_4_palabras(self):
        result = separar_nombre('DENNYS EDUARDO PARRA GRANADILLO')
        assert result == {
            'nombres': 'DENNYS EDUARDO',
            'apellido_paterno': 'PARRA',
            'apellido_materno': 'GRANADILLO'
        }
    
    def test_nombre_3_palabras(self):
        result = separar_nombre('JUAN CARLOS PEREZ')
        assert result == {
            'nombres': 'JUAN',
            'apellido_paterno': 'CARLOS',
            'apellido_materno': 'PEREZ'
        }
    
    def test_nombre_2_palabras(self):
        result = separar_nombre('JUAN PEREZ')
        assert result == {
            'nombres': 'JUAN',
            'apellido_paterno': 'PEREZ',
            'apellido_materno': ' '
        }
    
    def test_apellidos_repetidos(self):
        result = separar_nombre('CAROLINA CECILIA CALLES CALLES')
        assert result == {
            'nombres': 'CAROLINA CECILIA',
            'apellido_paterno': 'CALLES',
            'apellido_materno': 'CALLES'
        }


class TestSepararDireccion:
    def test_direccion_coma_punto(self):
        result = separar_direccion('AV. LAS CONDES 12461, LAS CONDES. SANTIAGO')
        assert result == {
            'direccion': 'AV. LAS CONDES 12461',
            'comuna': 'LAS CONDES',
            'ciudad': 'SANTIAGO'
        }
    
    def test_direccion_solo_puntos(self):
        result = separar_direccion('CALLE 123. PROVIDENCIA. SANTIAGO')
        assert result == {
            'direccion': 'CALLE 123',
            'comuna': 'PROVIDENCIA',
            'ciudad': 'SANTIAGO'
        }
    
    def test_direccion_solo_coma(self):
        result = separar_direccion('CALLE 123, PROVIDENCIA')
        assert result['direccion'] == 'CALLE 123'
        assert result['comuna'] == 'PROVIDENCIA'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
