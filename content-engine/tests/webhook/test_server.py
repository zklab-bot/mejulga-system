import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import hashlib, hmac, json
from unittest.mock import patch
from fastapi.testclient import TestClient


os.environ.setdefault("INSTAGRAM_ACCOUNT_ID", "123456")
os.environ.setdefault("WEBHOOK_VERIFY_TOKEN", "token_teste")
os.environ.setdefault("META_APP_SECRET", "")


def get_client():
    from webhook.server import app
    return TestClient(app)


def test_handshake_valido():
    client = get_client()
    resp = client.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "token_teste",
        "hub.challenge": "challenge_abc",
    })
    assert resp.status_code == 200
    assert resp.text == "challenge_abc"


def test_handshake_token_errado():
    client = get_client()
    resp = client.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "errado",
        "hub.challenge": "challenge_abc",
    })
    assert resp.status_code == 403


def test_post_webhook_retorna_ok():
    client = get_client()
    payload = json.dumps({"entry": []}).encode()
    resp = client.post(
        "/webhook",
        content=payload,
        headers={"content-type": "application/json", "x-hub-signature-256": "sha256=qualquer"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_post_webhook_chama_handle_dm():
    client = get_client()
    payload = {
        "entry": [{
            "changes": [{
                "field": "messages",
                "value": {
                    "sender": {"id": "999"},
                    "message": {"text": "oi"},
                },
            }]
        }]
    }
    raw = json.dumps(payload).encode()
    with patch("webhook.handlers.handle_dm") as mock_dm, \
         patch("webhook.handlers.handle_comment") as mock_comment:
        resp = client.post(
            "/webhook",
            content=raw,
            headers={"content-type": "application/json", "x-hub-signature-256": "sha256=qualquer"},
        )
    assert resp.status_code == 200
    mock_dm.assert_called_once()
    mock_comment.assert_not_called()


def test_post_webhook_chama_handle_comment():
    client = get_client()
    payload = {
        "entry": [{
            "changes": [{
                "field": "comments",
                "value": {"id": "cmt_1", "text": "top!", "from": {"id": "888"}},
            }]
        }]
    }
    raw = json.dumps(payload).encode()
    with patch("webhook.handlers.handle_dm") as mock_dm, \
         patch("webhook.handlers.handle_comment") as mock_comment:
        resp = client.post(
            "/webhook",
            content=raw,
            headers={"content-type": "application/json", "x-hub-signature-256": "sha256=qualquer"},
        )
    assert resp.status_code == 200
    mock_comment.assert_called_once()
    mock_dm.assert_not_called()
