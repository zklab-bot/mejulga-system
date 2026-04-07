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
    assert "forcar" in msg and "post" in msg


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


def _make_callback(chave: str, nota: int, chat_id: int = 999, message_id: int = 42) -> dict:
    return {
        "callback_query": {
            "id": "cq_id_123",
            "data": f"rate:{chave}:{nota}",
            "message": {
                "message_id": message_id,
                "chat": {"id": chat_id},
            },
        }
    }


def test_callback_query_chama_store_rating(monkeypatch):
    _mock_env(monkeypatch)
    with patch("webhook.telegram_handler.feedback") as mock_fb, \
         patch("requests.post"):
        th.handle(_make_callback("2026-04-07_amor", 4))
    mock_fb.store_rating.assert_called_once_with("2026-04-07_amor", 4)


def test_callback_query_edita_mensagem(monkeypatch):
    _mock_env(monkeypatch)
    state = {"post_details": {"2026-04-07_amor": {"titulo": "O Sumido", "nota": None}}}
    with patch("webhook.telegram_handler.feedback"), \
         patch("webhook.telegram_handler._fetch_state", return_value=state), \
         patch("requests.post") as mock_post:
        th.handle(_make_callback("2026-04-07_amor", 4))

    calls = [str(c) for c in mock_post.call_args_list]
    assert any("editMessageText" in c for c in calls)
    assert any("answerCallbackQuery" in c for c in calls)


def test_callback_query_mensagem_contem_estrelas(monkeypatch):
    _mock_env(monkeypatch)
    state = {"post_details": {"2026-04-07_amor": {"titulo": "O Sumido", "nota": None}}}
    with patch("webhook.telegram_handler.feedback"), \
         patch("webhook.telegram_handler._fetch_state", return_value=state), \
         patch("requests.post") as mock_post:
        th.handle(_make_callback("2026-04-07_amor", 3))

    edit_call = next(
        c for c in mock_post.call_args_list
        if "editMessageText" in str(c)
    )
    texto = edit_call[1]["json"]["text"]
    assert "⭐⭐⭐" in texto
    assert "O Sumido" in texto


def test_callback_query_chat_id_errado_ignorado(monkeypatch):
    _mock_env(monkeypatch)
    with patch("webhook.telegram_handler.feedback") as mock_fb:
        th.handle(_make_callback("2026-04-07_amor", 4, chat_id=888))
    mock_fb.store_rating.assert_not_called()


def test_callback_query_formato_invalido_ignorado(monkeypatch):
    _mock_env(monkeypatch)
    with patch("webhook.telegram_handler.feedback") as mock_fb, \
         patch("requests.post"):
        th.handle({
            "callback_query": {
                "id": "x",
                "data": "nao_e_rate",
                "message": {"message_id": 1, "chat": {"id": 999}},
            }
        })
    mock_fb.store_rating.assert_not_called()
