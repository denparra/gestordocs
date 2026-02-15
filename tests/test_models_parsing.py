from src.models import parsear_texto_contrato


def _texto_base(tipo_vehiculo: str = 'AUTOMOVIL') -> str:
    return f"""Inscripcion : DRLZ.16-3
DATOS DEL VEHICULO
Tipo Vehiculo : {tipo_vehiculo} Ano : 2012
Marca : HYUNDAI
Modelo : ELANTRA GLS 1.6
Nro. Motor : G4FGBU380448
Nro. Chasis : KMHDH41CACU327103
Color : ROJO

DATOS DEL VENDEDOR
Nombre : DENNYS EDUARDO PARRA GRANADILLO
R.U.N. : 26.002.284-9
Direccion: AV LAS CONDES 12461, LAS CONDES. SANTIAGO
Telefono: 975400946
Correo: dparra@queirolo.cl

DATOS COMPRADOR
Nombre: CAROLINA CECILIA CALLES CALLES
RUT: 26033082-9
Direccion: SERRANO 266, SANTIAGO CENTRO. SANTIAGO
Telefono: 975400946
Correo: comprador@ejemplo.cl

TASACION 10.000.000
VENTA 9.500.000"""


def test_parsea_tipo_vehiculo_dos_palabras():
    contrato, errores = parsear_texto_contrato(_texto_base('STATION WAGON'))
    assert not errores
    assert contrato is not None
    assert contrato.vehiculo.tipo_vehiculo == 'STATION WAGON'


def test_parsea_con_orden_de_secciones_diferente():
    texto = """Inscripcion : DRLZ.16-3
VENTA 8.500.000
TASACION 9.000.000

DATOS DEL COMPRADOR
Nombre: CAROLINA CECILIA CALLES CALLES
RUT: 26033082-9
Direccion: SERRANO 266, SANTIAGO CENTRO. SANTIAGO
Telefono: 975400946
Correo: comprador@ejemplo.cl

DATOS DEL VEHICULO
Tipo Vehiculo : AUTOMOVIL Ano : 2012
Marca : HYUNDAI
Modelo : ELANTRA GLS 1.6
Nro. Motor : G4FGBU380448
Nro. Chasis : KMHDH41CACU327103
Color : ROJO

DATOS DEL VENDEDOR
Nombre : DENNYS EDUARDO PARRA GRANADILLO
R.U.N. : 26.002.284-9
Direccion: AV LAS CONDES 12461, LAS CONDES. SANTIAGO
Telefono: 975400946
Correo: dparra@queirolo.cl"""

    contrato, errores = parsear_texto_contrato(texto)
    assert not errores
    assert contrato is not None
    assert contrato.valor_venta == 8500000
    assert contrato.tasacion == 9000000


def test_overrides_tasacion_y_venta_tienen_prioridad():
    texto = _texto_base()
    contrato, errores = parsear_texto_contrato(
        texto,
        tasacion_override='11.100.000',
        venta_override='11.000.000',
    )

    assert not errores
    assert contrato is not None
    assert contrato.tasacion == 11100000
    assert contrato.valor_venta == 11000000


def test_venta_desde_override_cuando_no_viene_en_texto():
    texto = _texto_base().replace('VENTA 9.500.000', '')
    contrato, errores = parsear_texto_contrato(texto, venta_override='9.400.000')

    assert not errores
    assert contrato is not None
    assert contrato.valor_venta == 9400000
