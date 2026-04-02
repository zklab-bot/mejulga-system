import hashlib
import hmac
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from webhook.signature import verify_signature


def test_assinatura_valida():
    secret = "meu_segredo"
    payload = b'{"entry": []}'
    mac = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    header = f"sha256={mac}"
    assert verify_signature(payload, header, secret) is True


def test_assinatura_invalida():
    assert verify_signature(b"payload", "sha256=errado", "segredo") is False


def test_header_sem_prefixo_sha256():
    assert verify_signature(b"payload", "semprefix", "segredo") is False


def test_secret_vazio_retorna_true():
    # Sem APP_SECRET configurado, deixa passar (ambiente de dev)
    assert verify_signature(b"qualquer", "sha256=qualquer", "") is True


def test_header_none_retorna_false():
    assert verify_signature(b"payload", None, "segredo") is False
