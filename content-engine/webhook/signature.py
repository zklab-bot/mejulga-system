import hashlib
import hmac
import warnings


def verify_signature(payload: bytes, header: str, app_secret: str) -> bool:
    """Valida assinatura HMAC-SHA256 enviada pela Meta no header X-Hub-Signature-256."""
    if not app_secret:
        warnings.warn("META_APP_SECRET não configurado — validação de assinatura desativada", stacklevel=2)
        return True
    if not header or not header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        app_secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, header)
