# Habilitaci?n Tag: PDF Autofill Implementation Guide

## Objetivo
Generar un PDF de habilitaci?n TAG a partir de texto libre, normalizando los datos y rellenando los campos del formulario en `/docs/tag/PDF-EJEMPLO.pdf`.

## Mapeo exacto de campos (CAMPO1..CAMPO16)
(Dejar este bloque tal cual.)
```
CAMPO1  -> DIA (01-31) ej: 04
CAMPO2  -> MES (ENERO..DICIEMBRE en MAYUS) ej: FEBRERO
CAMPO3  -> A?O (YYYY) ej: 2026
CAMPO4  -> NOMBRE COMPLETO (nombre + apellidos) ej: DENNYS EDUARDO PARRA
CAMPO5  -> RUT (acepta XX.XXX.XXX-X o XXXXXXXX-X; normalizar a XXXXXXXX-X para rellenar)
CAMPO6  -> OPCIONAL (puede quedar vac?o si no hay dato)

DIRECCION (se divide en 3):
CAMPO7  -> DIRECCION PARTE 1 (calle + n?mero) ej: Av. las condes 12461
CAMPO8  -> COMUNA ej: las condes
CAMPO9  -> CIUDAD (REPETIR CAMPO8) ej: las condes

TELEFONO:
CAMPO10 -> TELEFONO en formato 9XXXXXXXX
          (acepta +569XXXXXXXX o 9XXXXXXXX; convertir a 9XXXXXXXX)

MAIL (dividido, el '@' queda impl?cito entre ambos campos):
CAMPO11 -> EMAIL PARTE 1 (antes de @) ej: DENNYS744
CAMPO12 -> EMAIL PARTE 2 (despu?s de @) ej: GMAIL.COM

VEHICULO / TAG:
CAMPO13 -> TAG ASIGNADO ej: 123456789
CAMPO14 -> PATENTE NORMALIZADA ej: KRTY11-3
CAMPO15 -> PATENTE NORMALIZADA (misma que CAMPO14) ej: KRTY11-3
CAMPO16 -> FIRMA (NO llenar)
```

## Nombres reales de campos (AcroForm) detectados en el PDF
Estos son los nombres reales de campos en `PDF-EJEMPLO.pdf`. Se usan para rellenar el formulario:
- CAMPO1  -> En Santiago  a
- CAMPO2  -> de
- CAMPO3  -> de_2
- CAMPO4  -> dondo?a
- CAMPO5  -> RUT
- CAMPO6  -> Giro
- CAMPO7  -> domiciliado a en
- CAMPO8  -> comuna
- CAMPO9  -> ciudad
- CAMPO10 -> fono
- CAMPO11 -> mail
- CAMPO12 -> undefined
- CAMPO13 -> Tag asignado
- CAMPO14 -> 1 Que es propietario mero tenedor yo responsable del veh?culo Placa Patente ?nica
- CAMPO15 -> Patente ?nica
- CAMPO16 -> undefined_2

## Parsing y normalizaci?n
- Claves case-insensitive: `Nombre`, `RUT`, `Direccion`, `Telefono`, `Correo`, `PATENTE`, `TAG`.
- RUT: quitar puntos, mantener guion, normalizar a `XXXXXXXX-X`.
- Tel?fono: quitar `+56` y s?mbolos; dejar 9 d?gitos (9XXXXXXXX).
- Email: dividir usuario y dominio (CAMPO11/CAMPO12).
- Direcci?n: separar por coma en `calle + n?mero` y `comuna`. Sin coma, usar el ?ltimo fragmento como comuna (limitaci?n).
- Patente: quitar puntos/guiones, dejar `XXXXX?-DV`.
- Fecha: usar fecha local actual si no viene en el texto.

## Payload ejemplo (desde `/docs/tag/testtag.md`)
```json
{
  "CAMPO1": "04",
  "CAMPO2": "FEBRERO",
  "CAMPO3": "2026",
  "CAMPO4": "MARIO HUMBERTO VERA VALENCIA",
  "CAMPO5": "10759120-6",
  "CAMPO6": "",
  "CAMPO7": "CALLE CHUQUICAMATA 814",
  "CAMPO8": "LA CALERA",
  "CAMPO9": "LA CALERA",
  "CAMPO10": "977583559",
  "CAMPO11": "MARIO.VERA",
  "CAMPO12": "CENCOCAL.CL",
  "CAMPO13": "147258369",
  "CAMPO14": "KYTR55-5",
  "CAMPO15": "KYTR55-5",
  "CAMPO16": ""
}
```

## Flujo propuesto
1. Pegar texto -> extraer datos -> normalizar.
2. Mapear CAMPO1..16 a nombres reales de campos.
3. Rellenar PDF (AcroForm).
4. Guardar salida como `docs/tag/output/Solicitud-Tag-[patente].pdf`.

## Verificaci?n de campos
```python
from pypdf import PdfReader
print(PdfReader('docs/tag/PDF-EJEMPLO.pdf').get_fields().keys())
```

## Flatten
El test rellena campos sin aplanar. Para aplanar, imprimir a PDF o usar una librer?a con flatten real.
