"""
Script de prueba: Previsualizar contrato y guardar PDF
NO registra el contrato, solo valida + previsualiza + descarga PDF
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.models import parsear_texto_contrato
from src.autotramite import crear_contrato_autotramite
from src.logging_utils import get_logger
from src.config import validar_credenciales

logger = get_logger(__name__, level='INFO')


async def test_previsualizar():
    """
    Test: Previsualizar contrato con datos de prueba
    """
    # Validar credenciales primero
    creds_ok, creds_error = validar_credenciales()
    if not creds_ok:
        logger.error(f'❌ Configuración inválida: {creds_error}')
        logger.error('Por favor configura las variables de entorno AUTOTRAMITE_EMAIL y AUTOTRAMITE_PASSWORD')
        return
    
    # Leer datos de prueba
    test_file = Path(__file__).parent / 'docs' / 'test.md'
    
    if not test_file.exists():
        logger.error(f'Archivo de prueba no encontrado: {test_file}')
        return
    
    with open(test_file, 'r', encoding='utf-8') as f:
        texto_test = f.read()
    
    logger.info('=' * 60)
    logger.info('TEST: Previsualizar Contrato (sin registro)')
    logger.info('=' * 60)
    
    # Paso 1: Parsear texto
    logger.info('\n1. Parseando datos de prueba...')
    contrato, errores = parsear_texto_contrato(texto_test)
    
    if errores:
        logger.error('❌ Errores de validación:')
        for error in errores:
            logger.error(f'  - {error.campo}: {error.mensaje}')
        return
    
    if not contrato:
        logger.error('❌ No se pudo parsear el contrato')
        return
    
    logger.info('✅ Datos parseados correctamente:')
    logger.info(f'  - Patente: {contrato.vehiculo.patente}-{contrato.vehiculo.patente_dv}')
    logger.info(f'  - Vehículo: {contrato.vehiculo.marca} {contrato.vehiculo.modelo} ({contrato.vehiculo.ano})')
    logger.info(f'  - Vendedor: {contrato.vendedor.nombres} {contrato.vendedor.apellido_paterno}')
    logger.info(f'  - Comprador: {contrato.comprador.nombres} {contrato.comprador.apellido_paterno}')
    logger.info(f'  - Valor Venta: ${contrato.valor_venta:,}')
    
    # Paso 2: Preparar salida (PDF)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path(__file__).parent / 'screenshots'
    pdf_path = output_dir / f'preview_{contrato.vehiculo.patente}_{timestamp}.pdf'
    
    # Paso 3: Ejecutar en modo DRY-RUN (solo previsualizar)
    logger.info('\n2. Ejecutando automatización (DRY-RUN)...')
    logger.info('   > Login en AutoTramite')
    logger.info('   > Llenado de formulario')
    logger.info('   > Previsualización de PDF')
    logger.info(f'   > PDF: {pdf_path}')
    logger.info('   > NO se registrará el contrato')
    
    resultado = await crear_contrato_autotramite(
        contrato, 
        dry_run=True,
        screenshot_path=str(pdf_path)
    )
    
    # Paso 4: Mostrar resultado
    logger.info('\n3. Resultado:')
    if resultado.success:
        logger.info('✅ Previsualización EXITOSA')
        logger.info(f'  - Duración: {resultado.duracion_segundos}s')
        logger.info(f'  - Mensaje: {resultado.mensaje}')
        if pdf_path.exists():
            logger.info(f'  - PDF guardado: {pdf_path}')
            logger.info(f'  - Tamaño: {pdf_path.stat().st_size / 1024:.1f} KB')
        if resultado.pdf_url:
            logger.info(f'  - PDF URL: {resultado.pdf_url}')
    else:
        logger.error('❌ Error en previsualización:')
        logger.error(f'  - {resultado.error}')
        logger.error(f'  - Duración: {resultado.duracion_segundos}s')
    
    logger.info('\n' + '=' * 60)
    logger.info('TEST COMPLETADO')
    logger.info('=' * 60)


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════╗
║  AutoTramite Test - Previsualización sin Registro           ║
║                                                              ║
║  Este script realizará:                                     ║
║  1. Parseo de datos desde docs/test.md                      ║
║  2. Login en AutoTramite                                    ║
║  3. Llenado del formulario                                  ║
║  4. Previsualización del PDF                                ║
║  5. Descarga de PDF (guardado en ./screenshots/)      ║
║                                                              ║
║  ⚠️  NO se registrará el contrato (modo dry-run)            ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(test_previsualizar())
