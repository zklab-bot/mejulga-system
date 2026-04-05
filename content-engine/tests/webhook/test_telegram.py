import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import json
from unittest.mock import patch, MagicMock
from webhook import telegram_handler as th


def _make_update(text: str, chat_id: int = 999) -> dict:
    return {
        "message": {
            "chat": {"id": chat_id},
            "text": text,
        }
    }


def _mock_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")
    monkeypatch.setenv("TELEGRAM_SECRET", "secret")
    monkeypatch.setenv("GITHUB_PAT", "ghp_test")
    monkeypatch.setenv("GITHUB_REPO", "owner/mejulga-system")


def test_handle_ignora_chat_id_errado(monkeypatch):
    _mock_env(monkeypatch)
    with patch("webhook.telegram_handler._reply") as mock_reply:
        th.handle({"message": {"chat": {"id": 888}, "text": "/help"}})
    mock_reply.assert_not_called()


def test_help_retorna_texto(monkeypatch):
    _mock_env(monkeypatch)
    with patch("webhook.telegram_handler._reply") as mock_reply:
        th.handle(_make_update("/help"))
    mock_reply.assert_called_once()
    msg = mock_reply.call_args[0][1]
    assert "/status" in msg
    assert "/forcar_post" in msg


def test_comando_desconhecido_responde_help(monkeypatch):
    _mock_env(monkeypatch)
    with patch("webhook.telegram_handler._reply") as mock_reply:
        th.handle(_make_update("/xyzzy"))
    mock_reply.assert_called_once()
    msg = mock_reply.call_args[0][1]
    assert "/help" in msg


def test_erros_le_state(monkeypatch):
    _mock_env(monkeypatch)
    state = {
        "errors": [
            {"timestamp": "2026-04-05T12:00:00", "context": "post_carrossel", "message": "403"}
        ]
    }
    with patch("webhook.telegram_handler._fetch_state", return_value=state), \
         patch("webhook.telegram_handler._reply") as mock_reply:
        th.handle(_make_update("/erros"))
    msg = mock_reply.call_args[0][1]
    assert "403" in msg
    assert "post_carrossel" in msg


def test_ultimo_sem_posts(monkeypatch):
    _mock_env(monkeypatch)
    state = {"posts_published": []}
    with patch("webhook.telegram_handler._fetch_state", return_value=state), \
         patch("webhook.telegram_handler._reply") as mock_reply:
        th.handle(_make_update("/ultimo"))
    msg = mock_reply.call_args[0][1]
    assert "nenhum" in msg.lower()


def test_forcar_post_sem_arg_usa_categoria_do_dia(monkeypatch):
    _mock_env(monkeypatch)
    with patch("webhook.telegram_handler._dispatch_workflow") as mock_disp, \
         patch("webhook.telegram_handler._reply"):
        th.handle(_make_update("/forcar_post"))
    mock_disp.assert_called_once()


def test_forcar_post_com_categoria(monkeypatch):
    _mock_env(monkeypatch)
    with patch("webhook.telegram_handler._dispatch_workflow") as mock_disp, \
         patch("webhook.telegram_handler._reply"):
        th.handle(_make_update("/forcar_post amor"))
    _, kwargs = mock_disp.call_args
    assert kwargs.get("inputs", {}).get("categoria") == "amor"
