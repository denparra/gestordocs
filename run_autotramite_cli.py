"""
CLI wrapper to run AutoTramite automation in a separate process.
This avoids Streamlit event-loop limitations on Windows.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from src.config import validar_credenciales
from src.models import parsear_texto_contrato
from src.autotramite import crear_contrato_autotramite


def _emit_result(payload: dict, result_path: Path | None) -> None:
    # Use ASCII-safe JSON to avoid Windows console encoding issues.
    output = json.dumps(payload, ensure_ascii=True)
    if result_path:
        try:
            result_path.write_text(output + "\n", encoding="utf-8")
        except Exception:
            pass
    sys.stdout.write(output)
    sys.stdout.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AutoTramite automation.")
    parser.add_argument("--input", required=True, help="Path to input text file.")
    parser.add_argument("--output", required=True, help="Path to output PDF.")
    parser.add_argument("--dry-run", action="store_true", help="Validate only.")
    parser.add_argument("--result", help="Path to write JSON result.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    result_path = Path(args.result) if args.result else None

    if not input_path.exists():
        _emit_result({
            "success": False,
            "error": f"Input file not found: {input_path}",
        }, result_path)
        return 2

    creds_ok, creds_error = validar_credenciales()
    if not creds_ok:
        _emit_result({
            "success": False,
            "error": f"Invalid credentials: {creds_error}",
        }, result_path)
        return 2

    try:
        texto = input_path.read_text(encoding="utf-8")
    except Exception as e:
        _emit_result({
            "success": False,
            "error": f"Failed to read input: {str(e)}",
        }, result_path)
        return 2

    contrato, errores = parsear_texto_contrato(texto)
    if errores:
        _emit_result({
            "success": False,
            "error": "Validation errors",
            "validation_errors": [{"campo": e.campo, "mensaje": e.mensaje} for e in errores],
        }, result_path)
        return 1

    if not contrato:
        _emit_result({
            "success": False,
            "error": "Failed to parse contract",
        }, result_path)
        return 1

    try:
        resultado = asyncio.run(
            crear_contrato_autotramite(
                contrato,
                dry_run=args.dry_run,
                screenshot_path=str(output_path),
            )
        )
    except Exception as e:
        _emit_result({
            "success": False,
            "error": f"Execution error: {str(e)}",
        }, result_path)
        return 1

    payload = {
        "success": bool(resultado.success),
        "operacion_id": resultado.operacion_id,
        "pdf_url": resultado.pdf_url,
        "mensaje": resultado.mensaje,
        "error": resultado.error,
        "duracion_segundos": resultado.duracion_segundos,
        "pdf_path": str(output_path),
    }
    _emit_result(payload, result_path)
    return 0 if resultado.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
