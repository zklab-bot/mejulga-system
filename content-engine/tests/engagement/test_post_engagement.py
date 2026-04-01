import pytest
from unittest.mock import patch


def test_gerar_comentario_amor():
    from engagement.post_engagement import gerar_comentario_votacao
    texto = gerar_comentario_votacao("amor")
    assert "🔴" in texto
    assert "🟢" in texto


def test_gerar_comentario_dinheiro():
    from engagement.post_engagement import gerar_comentario_votacao
    texto = gerar_comentario_votacao("dinheiro")
    assert "🔴" in texto
    assert "🟢" in texto


def test_gerar_comentario_categoria_desconhecida():
    from engagement.post_engagement import gerar_comentario_votacao
    texto = gerar_comentario_votacao("categoria_inexistente")
    assert "🔴" in texto
    assert "🟢" in texto


def test_postar_comentario_dry_run(capsys):
    from engagement.post_engagement import postar_comentario
    postar_comentario("media_123", "Teste 🔴 / 🟢", dry_run=True)
    out = capsys.readouterr().out
    assert "DRY RUN" in out
    assert "media_123" in out


def test_postar_comentario_real():
    from engagement.post_engagement import postar_comentario
    with patch("engagement.shared.meta_client.post") as mock_post:
        mock_post.return_value = {"id": "comment_999"}
        postar_comentario("media_123", "Votação 🔴 / 🟢", dry_run=False)
    mock_post.assert_called_once_with(
        "media_123/comments", data={"message": "Votação 🔴 / 🟢"}
    )
