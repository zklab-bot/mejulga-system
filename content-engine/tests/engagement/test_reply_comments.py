from unittest.mock import patch, MagicMock


def test_ja_respondido_e_ignorado(capsys):
    from engagement.reply_comments import executar
    with patch("engagement.shared.meta_client.get") as mock_get, \
         patch("engagement.shared.state.load") as mock_load, \
         patch("engagement.shared.state.save"):
        mock_load.return_value = {
            "comments_replied": ["comment_111"],
            "stories_reposted": [], "dms_replied": [],
            "following": {}, "hashtag_report": {},
        }
        mock_get.side_effect = [
            {"data": [{"id": "post_1"}]},
            {"data": [{"id": "comment_111", "text": "oi", "replies": {"data": []}}]},
        ]
        executar(dry_run=True)
    out = capsys.readouterr().out
    assert "0 resposta" in out


def test_comentario_sem_replies_e_respondido(capsys):
    from engagement.reply_comments import executar
    with patch("engagement.shared.meta_client.get") as mock_get, \
         patch("engagement.shared.meta_client.post") as mock_post, \
         patch("engagement.shared.claude_client.generate", return_value="Diagnóstico confirmado! — Dra. Julga"), \
         patch("engagement.shared.state.load") as mock_load, \
         patch("engagement.shared.state.save"):
        mock_load.return_value = {
            "comments_replied": [],
            "stories_reposted": [], "dms_replied": [],
            "following": {}, "hashtag_report": {},
        }
        mock_get.side_effect = [
            {"data": [{"id": "post_1"}]},
            {"data": [{"id": "comment_222", "text": "me sinto assim também!", "replies": {"data": []}}]},
        ]
        mock_post.return_value = {"id": "reply_333"}
        executar(dry_run=False)
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[0][0] == "comment_222/replies"


def test_dry_run_nao_posta(capsys):
    from engagement.reply_comments import executar
    with patch("engagement.shared.meta_client.get") as mock_get, \
         patch("engagement.shared.meta_client.post") as mock_post, \
         patch("engagement.shared.claude_client.generate", return_value="Resposta"), \
         patch("engagement.shared.state.load") as mock_load, \
         patch("engagement.shared.state.save"):
        mock_load.return_value = {
            "comments_replied": [], "stories_reposted": [],
            "dms_replied": [], "following": {}, "hashtag_report": {},
        }
        mock_get.side_effect = [
            {"data": [{"id": "post_1"}]},
            {"data": [{"id": "comment_444", "text": "adorei!", "replies": {"data": []}}]},
        ]
        executar(dry_run=True)
    mock_post.assert_not_called()
