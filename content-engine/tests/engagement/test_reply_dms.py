def test_contem_keyword_verdadeiro():
    from engagement.reply_dms import _contem_keyword
    assert _contem_keyword("me julga por favor")
    assert _contem_keyword("quero meu diagnóstico")
    assert _contem_keyword("como funciona o mejulga")
    assert _contem_keyword("Me Julga!")  # case insensitive


def test_contem_keyword_falso():
    from engagement.reply_dms import _contem_keyword
    assert not _contem_keyword("oi tudo bem")
    assert not _contem_keyword("adorei o post")
    assert not _contem_keyword("")


def test_dry_run_nao_envia(capsys):
    from engagement.reply_dms import executar
    from unittest.mock import patch

    with patch("engagement.shared.meta_client.get") as mock_get, \
         patch("engagement.shared.meta_client.post") as mock_post, \
         patch("engagement.shared.claude_client.generate", return_value="Olá! mejulga.com.br"), \
         patch("engagement.shared.state.load") as mock_load, \
         patch("engagement.shared.state.save"):
        mock_load.return_value = {
            "comments_replied": [], "stories_reposted": [],
            "dms_replied": [], "following": {}, "hashtag_report": {},
        }
        mock_get.return_value = {
            "data": [{
                "id": "conv_1",
                "messages": {"data": [{"id": "msg_1", "message": "me julga!", "from": {"id": "user_99"}}]},
            }]
        }
        executar(dry_run=True)
    mock_post.assert_not_called()


def test_sem_keyword_nao_responde():
    from engagement.reply_dms import executar
    from unittest.mock import patch

    with patch("engagement.shared.meta_client.get") as mock_get, \
         patch("engagement.shared.meta_client.post") as mock_post, \
         patch("engagement.shared.state.load") as mock_load, \
         patch("engagement.shared.state.save"):
        mock_load.return_value = {
            "comments_replied": [], "stories_reposted": [],
            "dms_replied": [], "following": {}, "hashtag_report": {},
        }
        mock_get.return_value = {
            "data": [{
                "id": "conv_2",
                "messages": {"data": [{"id": "msg_2", "message": "oi tudo bem?", "from": {"id": "user_88"}}]},
            }]
        }
        executar(dry_run=False)
    mock_post.assert_not_called()
