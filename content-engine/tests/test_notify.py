import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import patch, MagicMock
import notify


def _mock_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")


def test_send_faz_post_correto(monkeypatch):
    _mock_env(monkeypatch)
    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        notify.send("Teste de mensagem")
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "123:ABC" in args[0]
    assert kwargs["json"]["chat_id"] == "999"
    assert kwargs["json"]["text"] == "Teste de mensagem"


def test_send_post_published_formata_mensagem(monkeypatch):
    _mock_env(monkeypatch)
    with patch("notify.send") as mock_send:
        notify.send_post_published("amor", "O Ciumento Silencioso", "09h04", "123456")
    mock_send.assert_called_once()
    msg = mock_send.call_args[0][0]
    assert "09h04" in msg
    assert "amor" in msg
    assert "O Ciumento Silencioso" in msg


def test_send_post_failed_formata_mensagem(monkeypatch):
    _mock_env(monkeypatch)
    with patch("notify.send") as mock_send:
        notify.send_post_failed("trabalho", "12h01", "403 Forbidden")
    msg = mock_send.call_args[0][0]
    assert "trabalho" in msg
    assert "403 Forbidden" in msg


def test_send_post_skipped_formata_mensagem(monkeypatch):
    _mock_env(monkeypatch)
    with patch("notify.send") as mock_send:
        notify.send_post_skipped("social")
    msg = mock_send.call_args[0][0]
    assert "social" in msg


def test_send_daily_report_formata_estado(monkeypatch):
    _mock_env(monkeypatch)
    from datetime import date
    hoje = date.today().strftime("%Y-%m-%d")
    state = {
        "posts_published": [f"{hoje}_amor", f"{hoje}_trabalho"],
        "errors": [],
    }
    with patch("notify.send") as mock_send:
        notify.send_daily_report(state)
    msg = mock_send.call_args[0][0]
    assert "amor" in msg
    assert "trabalho" in msg


def test_send_voting_comment_formata_mensagem(monkeypatch):
    _mock_env(monkeypatch)
    with patch("notify.send") as mock_send:
        notify.send_voting_comment("987654")
    msg = mock_send.call_args[0][0]
    assert "987654" in msg
