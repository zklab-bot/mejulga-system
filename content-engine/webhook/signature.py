import hashlib
import hmac


def verify_signature(payload: bytes, header: str, app_secret: str) -> bool:
    """Valida assinatura HMAC-SHA256 enviada pela Meta no header X-Hub-Signature-256."""
    if not app_secret:
        return True  # Dev sem secret configurado
    if not header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        app_secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, header)
