"""
Utilidades de autenticación para Streamlit.
"""
from __future__ import annotations

import base64
import hashlib
import hmac


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verifica password contra hash PBKDF2 en formato:
    pbkdf2_sha256$<iterations>$<salt_b64>$<hash_b64>
    """
    if not password or not stored_hash:
        return False

    parts = stored_hash.split('$')
    if len(parts) != 4 or parts[0] != 'pbkdf2_sha256':
        return False

    try:
        iterations = int(parts[1])
        salt = base64.b64decode(parts[2])
        expected_hash = base64.b64decode(parts[3])
    except Exception:
        return False

    computed_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations,
    )

    return hmac.compare_digest(computed_hash, expected_hash)
