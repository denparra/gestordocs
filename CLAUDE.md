# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AutoTramite Python MVP** - Automated vehicle purchase contract registration system for AutoTramite.cl, migrated from n8n workflow to Python.

| Attribute | Value |
|-----------|-------|
| Language | Python 3.10+ |
| UI Framework | Streamlit |
| Browser Automation | Playwright (Chromium) |
| Data Validation | Pydantic |
| Testing | pytest |

## Commands

### Setup
```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Configure credentials
cp .env.example .env
# Edit .env with AUTOTRAMITE_EMAIL and AUTOTRAMITE_PASSWORD
```

### Running
```bash
# Main Streamlit application (opens http://localhost:8501)
streamlit run app.py
```

### Testing
```bash
# Run all tests
pytest

# Verbose output
pytest -v

# Specific test file
pytest tests/test_validators.py -v

# With coverage
pytest --cov=src tests/
```

### Debugging Browser Automation
Set in `.env`:
```env
PLAYWRIGHT_HEADLESS=False
PLAYWRIGHT_SLOW_MO=1000
```

## Architecture

```
app.py                    # Streamlit entry point - UI flow and session state
src/
├── config.py             # Pydantic Settings + CSS selectors for AutoTramite form
├── models.py             # Pydantic models + parsear_texto_contrato() parser
├── validators.py         # Chilean-specific: RUT (mod 11), patente, email, phone
├── autotramite.py        # Playwright automation: login → fill form → register
└── logging_utils.py      # PII masking: ofuscar_rut(), ofuscar_email(), etc.
tests/
└── test_validators.py    # Unit tests for validators
```

### Data Flow
```
Text Input (CAV + Nota de Venta)
    → parsear_texto_contrato() [models.py]
    → Validation [validators.py]
    → ContratoData model [models.py]
    → crear_contrato_autotramite() [autotramite.py]
    → ContratoResult
```

### Key Components

**`src/autotramite.py`** - Main automation orchestration:
- `crear_contrato_autotramite(datos, dry_run, screenshot_path)` - Entry point
- `login_autotramite(page)` - Handles login with credential validation
- `llenar_formulario(page, datos)` - Fills all form fields with human-like delays
- `previsualizar_y_registrar(page, dry_run)` - Preview PDF and optionally register
- Custom exceptions: `LoginFailedError` (non-recoverable), `RecoverableError` (retryable)

**`src/models.py`** - Data structures and parsing:
- `ContratoData` - Complete contract with `DatosVehiculo`, `DatosPersona` (seller/buyer)
- `parsear_texto_contrato(texto)` - Returns `(ContratoData | None, list[ValidationError])`
- `separar_nombre()` - Splits full name (last 2 words are surnames)
- `separar_direccion()` - Splits "CALLE, COMUNA. CIUDAD" format

**`src/validators.py`** - Chilean format validation:
- RUT: Modulo 11 algorithm (K for 10, 0 for 11)
- Patente: Old format (XXNN), New format (NNXX), Vintage (XX00XX)
- Phone: 8-9 digits (Chilean standard)

### Async Bridge
Streamlit is synchronous but Playwright is async. Bridge with:
```python
asyncio.run(crear_contrato_autotramite(datos, dry_run))
```

## Configuration

Required `.env` variables:
```env
AUTOTRAMITE_EMAIL=your_email@queirolo.cl      # Required
AUTOTRAMITE_PASSWORD=your_password             # Required
```

Optional `.env` variables:
```env
LOG_LEVEL=INFO                    # DEBUG for troubleshooting
PLAYWRIGHT_HEADLESS=True          # False to see browser
TIMEOUT_NAVIGATION=30000          # Page load timeout (ms)
TIMEOUT_ELEMENT=10000             # Element wait timeout (ms)
MAX_REINTENTOS=3                  # Retry attempts
DELAY_BASE_MS=2000                # Exponential backoff base
```

## Form Selectors

All CSS selectors are centralized in `src/config.py` and validated with live system. Notable quirks:
- Vehicle year field is `#anhio` (not `#ano`)
- Login fields: `#Correo`, `#Clave`
- Default company: 'AUTORECENTE SPA (QUEIROLO)'
- Default signature: 'fea' (Firma Electronica Avanzada)

## Error Handling

The automation uses an exception hierarchy:
- `AutoTramiteError` (base)
  - `LoginFailedError` - Invalid credentials, no retry
  - `FormSubmitError` - Form submission issues
  - `RecoverableError` - Network/timeout, triggers exponential backoff retry
