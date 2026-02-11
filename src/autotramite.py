"""
Automatización de AutoTramite con Playwright
Basado en: Sección 5 del plan (selectores validados + estrategia de waits)
"""
import asyncio
import re
import time
from typing import Optional
from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeoutError

from .config import settings, SELECTORS
from .models import ContratoData, ContratoResult
from .logging_utils import get_logger

logger = get_logger(__name__, level=settings.log_level, log_file=settings.log_file)


class AutoTramiteError(Exception):
    """Error base para operaciones de AutoTramite"""
    pass


class LoginFailedError(AutoTramiteError):
    """Error de login (no recuperable)"""
    pass


class FormSubmitError(AutoTramiteError):
    """Error al enviar formulario (potencialmente recuperable)"""
    pass


class RecoverableError(AutoTramiteError):
    """Error recuperable (reintentar)"""
    pass


async def fill_field(page: Page, selector: str, value: Optional[str], required: bool = True) -> None:
    """
    Llena un campo del formulario con espera inteligente
    
    Args:
        page: Página de Playwright
        selector: Selector CSS/ID del campo
        value: Valor a ingresar
        required: Si es requerido (lanzar error si falla)
    
    Raises:
        RecoverableError: Si el campo requerido no se puede llenar
    """
    if value is None or value == '':
        if required:
            raise RecoverableError(f'Valor requerido vacío para: {selector}')
        return
    
    try:
        # Esperar que el elemento esté visible
        await page.wait_for_selector(selector, state='visible', timeout=settings.timeout_element)
        
        # Limpiar campo (triple click + backspace)
        await page.click(selector, click_count=3)
        await page.keyboard.press('Backspace')
        
        # Ingresar valor
        await page.type(selector, str(value), delay=50)  # 50ms entre teclas para simular humano
        
        logger.debug(f'Campo llenado: {selector[:30]}... = {str(value)[:30]}...')
    
    except PlaywrightTimeoutError:
        msg = f'Timeout esperando campo: {selector}'
        logger.error(msg)
        if required:
            raise RecoverableError(msg)
    
    except Exception as e:
        msg = f'Error llenando campo {selector}: {str(e)}'
        logger.error(msg)
        if required:
            raise RecoverableError(msg)


async def click_button(page: Page, selector: str, wait_navigation: bool = False) -> None:
    """
    Click en botón con espera inteligente
    
    Args:
        page: Página de Playwright
        selector: Selector del botón
        wait_navigation: Si debe esperar navegación después del click
    
    Raises:
        RecoverableError: Si el botón no se encuentra o no se puede clickear
    """
    try:
        await page.wait_for_selector(selector, state='visible', timeout=settings.timeout_element)
        
        if wait_navigation:
            async with page.expect_navigation(timeout=settings.timeout_navigation):
                await page.click(selector)
        else:
            await page.click(selector)
        
        logger.debug(f'Click en: {selector[:50]}...')
    
    except PlaywrightTimeoutError:
        raise RecoverableError(f'Timeout esperando botón: {selector}')
    
    except Exception as e:
        raise RecoverableError(f'Error clickeando botón {selector}: {str(e)}')


async def login_autotramite(page: Page) -> None:
    """
    Login en AutoTramite
    
    Args:
        page: Página de Playwright
    
    Raises:
        LoginFailedError: Si las credenciales son inválidas (NO recuperable)
        RecoverableError: Si hay problema de red/timeout (recuperable)
    """
    logger.info('Iniciando login en AutoTramite')

    try:
        # Navegar a login
        _t0 = time.time()
        logger.info(f'Navegando a {settings.autotramite_login_url}...')
        await page.goto(settings.autotramite_login_url, wait_until='domcontentloaded', timeout=settings.timeout_navigation)
        logger.info(f'Pagina login cargada en {time.time()-_t0:.2f}s. URL: {page.url}')

        # Llenar credenciales
        logger.info('Llenando campo email...')
        await fill_field(page, SELECTORS['login_email'], settings.autotramite_email)
        logger.info('Email OK. Llenando campo password...')
        await fill_field(page, SELECTORS['login_password'], settings.autotramite_password)
        logger.info('Password OK.')

        # Click login
        logger.info('Click en boton login...')
        await click_button(page, SELECTORS['login_submit'], wait_navigation=True)

        # Verificar que NO estamos en login.php (significa login exitoso)
        url_actual = page.url
        logger.info(f'Post-login URL: {url_actual}')

        if 'login.php' in url_actual:
            logger.error('Login fallido: aún en página de login')
            raise LoginFailedError('Credenciales inválidas o login fallido')
        
        logger.info('Login exitoso', extra={'url_destino': url_actual})
    
    except LoginFailedError:
        raise  # No recuperable
    
    except PlaywrightTimeoutError:
        raise RecoverableError('Timeout durante login (posible problema de red)')
    
    except Exception as e:
        raise RecoverableError(f'Error inesperado durante login: {str(e)}')


async def llenar_formulario(page: Page, datos: ContratoData) -> None:
    """
    Llena formulario de contrato en AutoTramite
    
    Args:
        page: Página de Playwright
        datos: Datos del contrato
    
    Raises:
        RecoverableError: Si hay problemas llenando el formulario
    """
    logger.info('Llenando formulario de contrato', extra={
        'patente': datos.vehiculo.patente,
        'vendedor_rut': datos.vendedor.rut,
        'comprador_rut': datos.comprador.rut
    })
    
    try:
        # Navegar al formulario
        logger.info(f'Navegando al formulario: {settings.autotramite_form_url}...')
        await page.goto(settings.autotramite_form_url, wait_until='domcontentloaded', timeout=settings.timeout_navigation)
        logger.info(f'Formulario cargado. URL: {page.url}')
        
        # VEHICULO
        await fill_field(page, SELECTORS['vehiculo_patente'], datos.vehiculo.patente)
        await fill_field(page, SELECTORS['vehiculo_dv'], datos.vehiculo.patente_dv)
        await fill_field(page, SELECTORS['vehiculo_marca'], datos.vehiculo.marca)
        await fill_field(page, SELECTORS['vehiculo_modelo'], datos.vehiculo.modelo)
        await fill_field(page, SELECTORS['vehiculo_ano'], str(datos.vehiculo.ano))
        await fill_field(page, SELECTORS['vehiculo_color'], datos.vehiculo.color)
        await fill_field(page, SELECTORS['vehiculo_chasis'], datos.vehiculo.chasis)
        await fill_field(page, SELECTORS['vehiculo_motor'], datos.vehiculo.motor)
        await fill_field(page, SELECTORS['vehiculo_tipo'], datos.vehiculo.tipo_vehiculo)
        
        # Tasación y Valor Venta
        if datos.tasacion:
            await fill_field(page, SELECTORS['vehiculo_tasacion'], str(datos.tasacion), required=False)
        await fill_field(page, SELECTORS['vehiculo_valor_venta'], str(datos.valor_venta))
        
        # VENDEDOR
        await fill_field(page, SELECTORS['vendedor_rut'], datos.vendedor.rut)
        await fill_field(page, SELECTORS['vendedor_nombres'], datos.vendedor.nombres)
        await fill_field(page, SELECTORS['vendedor_ap_paterno'], datos.vendedor.apellido_paterno)
        await fill_field(page, SELECTORS['vendedor_ap_materno'], datos.vendedor.apellido_materno, required=False)
        await fill_field(page, SELECTORS['vendedor_direccion'], datos.vendedor.direccion)
        await fill_field(page, SELECTORS['vendedor_comuna'], datos.vendedor.comuna)
        await fill_field(page, SELECTORS['vendedor_ciudad'], datos.vendedor.ciudad)
        await fill_field(page, SELECTORS['vendedor_telefono'], datos.vendedor.telefono)
        await fill_field(page, SELECTORS['vendedor_email'], datos.vendedor.email)
        
        # COMPRADOR
        await fill_field(page, SELECTORS['comprador_rut'], datos.comprador.rut)
        await fill_field(page, SELECTORS['comprador_nombres'], datos.comprador.nombres)
        await fill_field(page, SELECTORS['comprador_ap_paterno'], datos.comprador.apellido_paterno)
        await fill_field(page, SELECTORS['comprador_ap_materno'], datos.comprador.apellido_materno, required=False)
        await fill_field(page, SELECTORS['comprador_direccion'], datos.comprador.direccion)
        await fill_field(page, SELECTORS['comprador_comuna'], datos.comprador.comuna)
        await fill_field(page, SELECTORS['comprador_ciudad'], datos.comprador.ciudad)
        await fill_field(page, SELECTORS['comprador_telefono'], datos.comprador.telefono)
        await fill_field(page, SELECTORS['comprador_email'], datos.comprador.email)
        
        # CONFIGURACION
        # Pago contado (ya viene marcado por defecto según plan)
        # Firma electrónica
        await page.check(SELECTORS['config_firma_electronica'])
        
        # Seleccionar operador/generado por
        await page.select_option(SELECTORS['config_operador'], label=datos.generado_por)
        
        logger.info('Formulario llenado completamente')
    
    except RecoverableError:
        raise
    
    except Exception as e:
        raise RecoverableError(f'Error inesperado llenando formulario: {str(e)}')


async def previsualizar_y_registrar(page: Page, dry_run: bool = False, screenshot_path: Optional[str] = None) -> ContratoResult:
    """
    Previsualiza PDF y opcionalmente registra el contrato

    Args:
        page: Pagina de Playwright
        dry_run: Si True, solo previsualiza sin registrar
        screenshot_path: Path opcional para guardar screenshot o PDF

    Returns:
        ContratoResult: Resultado de la operacion

    Raises:
        RecoverableError: Si hay problemas en la operacion
    """
    logger.info(f'Previsualizando contrato (dry_run={dry_run})')

    try:
        pdf_response = None
        pdf_url: Optional[str] = None
        archivo_guardado: Optional[str] = None
        pdf_guardado = False

        def normalizar_url(url: Optional[str], base_url: str) -> Optional[str]:
            if not url:
                return None
            url = url.strip()
            if not url:
                return None
            lower = url.lower()
            if lower.startswith(('about:', 'blob:', 'data:', 'javascript:', 'chrome-extension:', 'devtools:')):
                return None
            # Extraer file=... desde visor PDF
            try:
                from urllib.parse import urlparse, parse_qs, unquote
                parsed = urlparse(url)
                query = parse_qs(parsed.query)
                if 'file' in query and query['file']:
                    file_url = unquote(query['file'][0])
                    return normalizar_url(file_url, base_url)
            except Exception:
                pass
            if lower.startswith('//'):
                url = 'https:' + url
            if lower.startswith(('http://', 'https://')):
                return url
            # Relative URL
            from urllib.parse import urljoin
            return urljoin(base_url, url)

        def es_pdf_bytes(data: Optional[bytes]) -> bool:
            if not data:
                return False
            return data.lstrip().startswith(b'%PDF')

        async def extraer_pdf_base64(target_page: Page) -> Optional[str]:
            # 1) Embed src data:application/pdf;base64,...
            try:
                embed = await target_page.query_selector("embed[type='application/pdf']")
                if embed:
                    src = await embed.get_attribute('src')
                    if src and src.startswith('data:application/pdf;base64,'):
                        return src.split(',', 1)[1]
            except Exception:
                pass

            # 2) Hidden input with base64
            try:
                hidden = await target_page.query_selector("input[name='pdfbase64']")
                if hidden:
                    value = await hidden.get_attribute('value')
                    if value:
                        return value
            except Exception:
                pass

            # 3) HTML fallback
            try:
                html = await target_page.content()
                match = re.search(r'data:application/pdf;base64,([^"\\s>]+)', html, re.IGNORECASE)
                if match:
                    return match.group(1)
                match = re.search(r'name=[\"\\\']pdfbase64[\"\\\']\\s+value=[\"\\\']([^\"\\\']+)[\"\\\']', html, re.IGNORECASE)
                if match:
                    return match.group(1)
            except Exception:
                pass

            return None

        async def dump_preview_debug(target_page: Page, pdf_path, candidatos: Optional[list[str]] = None) -> None:
            try:
                from pathlib import Path
                debug_html = Path(str(pdf_path)).with_suffix('.html')
                debug_urls = Path(str(pdf_path)).with_suffix('.urls.txt')

                html = await target_page.content()
                debug_html.write_text(html, encoding='utf-8')

                urls: list[str] = []
                if candidatos:
                    urls.extend(candidatos)
                try:
                    urls.append(f'PAGE_URL: {target_page.url}')
                    for frame in target_page.frames:
                        if frame.url:
                            urls.append(f'FRAME_URL: {frame.url}')
                except Exception:
                    pass

                debug_urls.write_text('\n'.join(urls) + '\n', encoding='utf-8')
                logger.warning(f'Debug preview guardado: {debug_html} / {debug_urls}')
            except Exception as e:
                logger.warning(f'No se pudo guardar debug preview: {str(e)}')

        async def buscar_url_pdf_en_pagina(target_page: Page) -> Optional[str]:
            candidatos: list[str] = []

            # Elements in DOM
            selectores = [
                ("embed[type='application/pdf']", 'src'),
                ("embed[src]", 'src'),
                ("iframe[src]", 'src'),
                ("object[data]", 'data'),
                ("a[href*='.pdf']", 'href'),
                ("a[href*='download']", 'href'),
                ("a[href*='descargar']", 'href'),
                ("a[download]", 'href'),
            ]
            for selector, attr in selectores:
                try:
                    elementos = await target_page.query_selector_all(selector)
                    for elemento in elementos:
                        valor = await elemento.get_attribute(attr)
                        if valor:
                            candidatos.append(valor)
                except Exception:
                    continue

            # Frame URLs
            try:
                for frame in target_page.frames:
                    if frame.url:
                        candidatos.append(frame.url)
            except Exception:
                pass

            # HTML fallback
            try:
                html = await target_page.content()
                # file=... en visor (pdf.js / chrome viewer)
                for match in re.findall(r'file=([^"\'\\s]+)', html, re.IGNORECASE):
                    candidatos.append(match)
                for match in re.findall(r'(https?://[^"\\s]+|/[^"\\s]+|\\.{1,2}/[^"\\s]+)', html, re.IGNORECASE):
                    if any(token in match.lower() for token in ['.pdf', 'generacontrato.php', 'contrato.php', 'pdf_autotramite', 'descargar', 'download']):
                        candidatos.append(match)
            except Exception:
                pass

            if target_page.url:
                candidatos.append(target_page.url)

            base_url = target_page.url
            normalizados: list[str] = []
            for candidato in candidatos:
                url = normalizar_url(candidato, base_url)
                if url:
                    normalizados.append(url)

            prioridades = [
                lambda u: '.pdf' in u,
                lambda u: 'generacontrato.php' in u,
                lambda u: 'pdf_autotramite' in u,
                lambda u: 'contrato.php' in u,
            ]

            for criterio in prioridades:
                for url in normalizados:
                    if criterio(url.lower()):
                        return url
            return None

        def es_respuesta_pdf(response) -> bool:
            try:
                content_type = response.headers.get('content-type', '').lower()
                url = response.url.lower()
                if url.startswith('chrome-extension://'):
                    return False
                return 'application/pdf' in content_type or url.endswith('.pdf')
            except Exception:
                return False

        # Preparar listener global para respuestas PDF (incluye popups)
        loop = asyncio.get_running_loop()
        pdf_future = loop.create_future()

        def manejar_respuesta(response) -> None:
            if pdf_future.done():
                return
            try:
                content_type = response.headers.get('content-type', '').lower()
                url = response.url.lower()
                if url.startswith('chrome-extension://'):
                    return
                if 'application/pdf' in content_type or url.endswith('.pdf') or 'pdf_' in url:
                    pdf_future.set_result(response)
            except Exception:
                pass

        page.context.on('response', manejar_respuesta)

        # Click en previsualizar PDF
        preview_page = page
        if screenshot_path:
            try:
                async with page.expect_popup(timeout=5000) as popup_info:
                    try:
                        async with page.expect_response(
                            es_respuesta_pdf,
                            timeout=settings.timeout_navigation
                        ) as response_info:
                            await click_button(page, SELECTORS['btn_previsualizar'])
                        pdf_response = await response_info.value
                    except PlaywrightTimeoutError:
                        logger.warning('No se detecto respuesta PDF en la previsualizacion')
                preview_page = await popup_info.value
            except PlaywrightTimeoutError:
                # No popup; el click ya fue ejecutado
                pass
            except Exception:
                raise
        else:
            await click_button(page, SELECTORS['btn_previsualizar'])

        # Esperar que cargue la previsualizacion (mas tiempo para asegurar que el PDF se genera)
        logger.info('Esperando generacion del PDF...')
        await asyncio.sleep(5)

        # Intentar capturar respuesta PDF global si no se obtuvo antes
        if pdf_response is None:
            try:
                pdf_response = await asyncio.wait_for(pdf_future, timeout=5)
            except Exception:
                pass

        # Liberar listener
        try:
            page.context.off('response', manejar_respuesta)
        except Exception:
            pass

        # Guardar PDF o screenshot si se especifica
        if screenshot_path:
            from pathlib import Path
            output_path = Path(screenshot_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            pdf_path = output_path if output_path.suffix.lower() == '.pdf' else output_path.with_suffix('.pdf')

            if pdf_response:
                try:
                    pdf_bytes = await pdf_response.body()
                    if es_pdf_bytes(pdf_bytes):
                        pdf_path.write_bytes(pdf_bytes)
                        pdf_url = pdf_response.url
                        archivo_guardado = str(pdf_path)
                        pdf_guardado = True
                        logger.info(f'PDF guardado: {pdf_path}')
                    else:
                        logger.warning('Respuesta PDF no valida (no inicia con %PDF)')
                except Exception as e:
                    logger.warning(f'No se pudo guardar PDF desde respuesta: {str(e)}')

            if not pdf_path.exists():
                # Usar la misma lógica de búsqueda y dejar trazas si falla
                pdf_url_dom = await buscar_url_pdf_en_pagina(preview_page)

                if pdf_url_dom:
                    try:
                        resp = await page.context.request.get(
                            pdf_url_dom,
                            headers={
                                'Accept': 'application/pdf',
                                'Referer': preview_page.url or page.url,
                            },
                        )
                        if resp.ok:
                            body = await resp.body()
                            content_type = resp.headers.get('content-type', '').lower()
                            if es_pdf_bytes(body) or ('application/pdf' in content_type and body):
                                pdf_path.write_bytes(body)
                                pdf_url = pdf_url_dom
                                archivo_guardado = str(pdf_path)
                                pdf_guardado = True
                                logger.info(f'PDF guardado: {pdf_path}')
                            else:
                                logger.warning(f"Respuesta no es PDF (content-type={content_type or 'n/a'})")

                                # Intentar extraer otra URL desde HTML
                                try:
                                    html_text = body.decode('utf-8', errors='ignore')
                                    matches: list[str] = []
                                    for match in re.findall(r'file=([^"\'\\s]+)', html_text, re.IGNORECASE):
                                        matches.append(match)
                                    for match in re.findall(r'(https?://[^\"\\s]+|/[^\"\\s]+|\\.{1,2}/[^\"\\s]+)', html_text, re.IGNORECASE):
                                        if any(token in match.lower() for token in ['.pdf', 'generacontrato.php', 'pdf_autotramite', 'contrato.php']):
                                            matches.append(match)

                                    for match in matches:
                                        url2 = normalizar_url(match, pdf_url_dom)
                                        if not url2:
                                            continue
                                        resp2 = await page.context.request.get(
                                            url2,
                                            headers={
                                                'Accept': 'application/pdf',
                                                'Referer': preview_page.url or page.url,
                                            },
                                        )
                                        if resp2.ok:
                                            body2 = await resp2.body()
                                            content_type2 = resp2.headers.get('content-type', '').lower()
                                            if es_pdf_bytes(body2) or ('application/pdf' in content_type2 and body2):
                                                pdf_path.write_bytes(body2)
                                                pdf_url = url2
                                                archivo_guardado = str(pdf_path)
                                                pdf_guardado = True
                                                logger.info(f'PDF guardado: {pdf_path}')
                                                break
                                except Exception:
                                    pass
                        else:
                            logger.warning(f'No se pudo descargar PDF (status {resp.status})')
                    except Exception as e:
                        logger.warning(f'Error descargando PDF: {str(e)}')
                # Si no se pudo guardar, dejar debug
                if not pdf_guardado:
                    # Intentar extraer PDF base64 embebido en el HTML
                    try:
                        import base64
                        pdf_b64 = await extraer_pdf_base64(preview_page)
                        if pdf_b64:
                            pdf_bytes = base64.b64decode(pdf_b64, validate=False)
                            if es_pdf_bytes(pdf_bytes):
                                pdf_path.write_bytes(pdf_bytes)
                                pdf_url = preview_page.url
                                archivo_guardado = str(pdf_path)
                                pdf_guardado = True
                                logger.info(f'PDF guardado desde base64: {pdf_path}')
                    except Exception as e:
                        logger.warning(f'Error guardando PDF base64: {str(e)}')

                if not pdf_guardado:
                    await dump_preview_debug(preview_page, pdf_path)

            if output_path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}:
                await page.screenshot(path=str(output_path), full_page=True)
                archivo_guardado = archivo_guardado or str(output_path)
                logger.info(f'Screenshot guardado: {output_path}')
            elif pdf_path.exists() and pdf_path.stat().st_size < 10240:
                logger.warning(f'PDF muy pequeno ({pdf_path.stat().st_size} bytes). Revisa el contenido.')

        if dry_run:
            logger.info('Modo dry-run: NO se registrara el contrato')
            return ContratoResult(
                success=True,
                operacion_id=None,
                pdf_url=pdf_url,
                mensaje=f'Previsualizacion exitosa (modo dry-run, no se registro){f" - Archivo: {archivo_guardado}" if archivo_guardado else ""}',
                error=None,
                duracion_segundos=0.0
            )

        # Registrar operacion (clic en boton)
        logger.info('Registrando operacion...')
        registro_clickado = False
        selectores_registro = [
            SELECTORS.get('btn_registrar_operacion'),
            'button:has-text("Registrar Operación")',
            'button:has-text("Registrar Operacion")',
            "button[name='accion'][value='guardar_contrato']",
            "form#formulario_guardar_contrato button[type='submit']",
            "form#formulario_guardar_contrato button",
        ]
        for selector in selectores_registro:
            if not selector:
                continue
            try:
                await preview_page.wait_for_selector(selector, state='visible', timeout=settings.timeout_element)
                locator = preview_page.locator(selector).first
                try:
                    await locator.scroll_into_view_if_needed()
                except Exception:
                    pass
                await locator.click()
                registro_clickado = True
                break
            except PlaywrightTimeoutError:
                continue
            except Exception:
                continue

        if not registro_clickado:
            raise RecoverableError('No se encontro boton "Registrar Operacion" en la vista previa')

        # Esperar posible navegacion o procesamiento
        try:
            await preview_page.wait_for_load_state('networkidle', timeout=settings.timeout_navigation)
        except Exception:
            pass
        await asyncio.sleep(2)

        # Buscar link de PDF en la pagina (solo si no se capturo antes)
        if not pdf_url:
            try:
                pdf_link = await preview_page.wait_for_selector('a[href*=".pdf"], a[download]', timeout=5000, state='visible')
                if pdf_link:
                    pdf_url = await pdf_link.get_attribute('href')
                    if pdf_url and not pdf_url.startswith('http'):
                        pdf_url = settings.autotramite_base_url + pdf_url
            except Exception:
                logger.warning('No se encontro link de PDF en la pagina')

        # Buscar ID de operacion (si existe)
        operacion_id = None
        try:
            # Intentar varios selectores posibles
            for selector in ['.operacion-id', '#numero-operacion', 'span:has-text("Folio")', 'td:has-text("ID")']:
                try:
                    elemento = await preview_page.wait_for_selector(selector, timeout=2000, state='visible')
                    if elemento:
                        texto = await elemento.text_content()
                        if texto:
                            match = re.search(r'\d+', texto)
                            if match:
                                operacion_id = match.group(0)
                                break
                except Exception:
                    continue
        except Exception:
            logger.warning('No se encontro ID de operacion en la pagina')

        logger.info('Contrato procesado exitosamente', extra={
            'operacion_id': operacion_id,
            'pdf_url': pdf_url[:50] if pdf_url else None
        })

        return ContratoResult(
            success=True,
            operacion_id=operacion_id,
            pdf_url=pdf_url,
            mensaje='Contrato registrado exitosamente',
            error=None,
            duracion_segundos=0.0
        )

    except RecoverableError:
        raise

    except Exception as e:
        raise RecoverableError(f'Error en previsualizacion/registro: {str(e)}')


async def ejecutar_con_reintentos(
    fn,
    max_intentos: Optional[int] = None,
    delay_base_ms: Optional[int] = None
):
    """
    Ejecuta función con reintentos exponenciales
    
    Args:
        fn: Función async a ejecutar
        max_intentos: Máximo de intentos (usa config si None)
        delay_base_ms: Delay base en ms (usa config si None)
    
    Returns:
        Resultado de fn()
    
    Raises:
        Exception: Si todos los intentos fallan o error no recuperable
    """
    max_intentos = max_intentos if max_intentos is not None else settings.max_reintentos
    delay_base_ms = delay_base_ms if delay_base_ms is not None else settings.delay_base_ms
    
    ultimo_error: Optional[Exception] = None
    
    for intento in range(1, max_intentos + 1):
        try:
            return await fn()
        
        except LoginFailedError as e:
            # Error no recuperable
            logger.error(f'Error no recuperable: {str(e)}')
            raise
        
        except RecoverableError as e:
            ultimo_error = e
            
            if intento < max_intentos:
                delay_ms = delay_base_ms * (2 ** (intento - 1))
                logger.warning(f'Intento {intento}/{max_intentos} fallido. Reintentando en {delay_ms}ms...')
                await asyncio.sleep(delay_ms / 1000)
            else:
                logger.error(f'Todos los intentos agotados ({max_intentos})')
                raise
        
        except Exception as e:
            logger.error(f'Error inesperado (no recuperable): {str(e)}')
            raise
    
    if ultimo_error:
        raise ultimo_error
    raise Exception('Error desconocido en reintentos')


async def crear_contrato_autotramite(datos: ContratoData, dry_run: bool = False, screenshot_path: Optional[str] = None) -> ContratoResult:
    """
    Función principal: crea contrato en AutoTramite
    
    Args:
        datos: Datos del contrato
        dry_run: Si True, solo valida sin registrar
        screenshot_path: Path opcional para guardar screenshot del PDF
    
    Returns:
        ContratoResult: Resultado de la operación
    
    Raises:
        LoginFailedError: Si las credenciales son inválidas
        RecoverableError: Si hay problemas de red/timeouts
        AutoTramiteError: Otros errores
    """
    inicio = time.time()
    
    logger.info('Iniciando creación de contrato', extra={
        'patente': datos.vehiculo.patente,
        'dry_run': dry_run
    })
    
    async with async_playwright() as p:
        logger.info('Lanzando Chromium...', extra={
            'headless': settings.playwright_headless,
            'slow_mo': settings.playwright_slow_mo
        })
        browser: Browser = await p.chromium.launch(
            headless=settings.playwright_headless,
            slow_mo=settings.playwright_slow_mo,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
        )
        logger.info('Chromium lanzado exitosamente')

        try:
            page: Page = await browser.new_page()
            logger.info('Nueva pagina creada')
            
            # Login
            await ejecutar_con_reintentos(lambda: login_autotramite(page))
            
            # Llenar formulario
            await ejecutar_con_reintentos(lambda: llenar_formulario(page, datos))
            
            # Previsualizar y registrar
            resultado = await ejecutar_con_reintentos(lambda: previsualizar_y_registrar(page, dry_run, screenshot_path))
            
            duracion = time.time() - inicio
            resultado.duracion_segundos = round(duracion, 2)
            
            logger.info('Operación completada exitosamente', extra={
                'duracion_segundos': resultado.duracion_segundos,
                'operacion_id': resultado.operacion_id
            })
            
            return resultado
        
        except Exception as e:
            duracion = time.time() - inicio
            logger.error(f'Error en operación: {str(e)}', extra={'duracion_segundos': round(duracion, 2)})
            
            return ContratoResult(
                success=False,
                operacion_id=None,
                pdf_url=None,
                mensaje='Error al registrar contrato',
                error=str(e),
                duracion_segundos=round(duracion, 2)
            )
        
        finally:
            await browser.close()
