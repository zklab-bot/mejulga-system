import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


def _mock_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")


def test_store_rating_salva_nota(tmp_path, monkeypatch):
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")

    from engagement import feedback
    monkeypatch.setattr(feedback, "state", state)

    state.save({
        "post_details": {
            "2026-04-07_amor": {
                "media_id": "123",
                "tipo_veredicto": "A",
                "titulo": "O Sumido",
                "crime": "ghosting sazonal",
                "categoria": "amor",
                "nota": None,
            }
        }
    })

    feedback.store_rating("2026-04-07_amor", 4)

    resultado = state.load()
    assert resultado["post_details"]["2026-04-07_amor"]["nota"] == 4


def test_store_rating_chave_inexistente_nao_quebra(tmp_path, monkeypatch):
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    from engagement import feedback
    monkeypatch.setattr(feedback, "state", state)

    # No exception raised for unknown key
    feedback.store_rating("chave_inexistente", 3)
    s = state.load()
    assert "chave_inexistente" not in s.get("post_details", {})


def test_send_rating_request_salva_detalhes(tmp_path, monkeypatch):
    _mock_env(monkeypatch)
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    from engagement import feedback
    monkeypatch.setattr(feedback, "state", state)

    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        feedback.send_rating_request(
            chave="2026-04-07_amor",
            media_id="123456",
            tipo_veredicto="A",
            titulo="O Sumido Saudoso",
            crime="ghosting sazonal com dolo comprovado",
            categoria="amor",
        )

    resultado = state.load()
    post = resultado["post_details"]["2026-04-07_amor"]
    assert post["media_id"] == "123456"
    assert post["tipo_veredicto"] == "A"
    assert post["titulo"] == "O Sumido Saudoso"
    assert post["crime"] == "ghosting sazonal com dolo comprovado"
    assert post["categoria"] == "amor"
    assert post["nota"] is None


def test_send_rating_request_envia_telegram(tmp_path, monkeypatch):
    _mock_env(monkeypatch)
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    from engagement import feedback
    monkeypatch.setattr(feedback, "state", state)

    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        feedback.send_rating_request(
            chave="2026-04-07_amor",
            media_id="123456",
            tipo_veredicto="A",
            titulo="O Sumido Saudoso",
            crime="ghosting sazonal",
            categoria="amor",
        )

    mock_post.assert_called_once()
    payload = mock_post.call_args[1]["json"]
    assert payload["chat_id"] == "999"
    assert "O Sumido Saudoso" in payload["text"]
    assert "Variação A" in payload["text"]
    assert "inline_keyboard" in payload["reply_markup"]
    botoes = payload["reply_markup"]["inline_keyboard"][0]
    assert len(botoes) == 5
    assert botoes[0]["callback_data"] == "rate:2026-04-07_amor:1"
    assert botoes[4]["callback_data"] == "rate:2026-04-07_amor:5"


def test_send_rating_request_sem_token_nao_quebra(tmp_path, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    from engagement import feedback
    monkeypatch.setattr(feedback, "state", state)

    # Should not raise even without token
    with patch("requests.post") as mock_post:
        feedback.send_rating_request(
            chave="2026-04-07_amor",
            media_id="123",
            tipo_veredicto="A",
            titulo="Teste",
            crime="crime de teste",
            categoria="amor",
        )
    mock_post.assert_not_called()
