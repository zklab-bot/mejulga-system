import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from unittest.mock import patch, MagicMock


ACCOUNT_ID = "123456"

BASE_STATE = {
    "comments_replied": [],
    "stories_reposted": [],
    "dms_replied": [],
    "following": {},
    "hashtag_report": {},
}


def test_handle_dm_responde_mensagem():
    from webhook.handlers import handle_dm
    value = {
        "sender": {"id": "999"},
        "message": {"text": "me julga!"},
    }
    with patch("engagement.shared.meta_client.post") as mock_post, \
         patch("engagement.shared.claude_client.generate", return_value="Diagnóstico: curioso crônico."), \
         patch("engagement.shared.state.load", return_value=dict(BASE_STATE)), \
         patch("engagement.shared.state.save"), \
         patch.dict(os.environ, {"INSTAGRAM_ACCOUNT_ID": ACCOUNT_ID}):
        handle_dm(value)
    mock_post.assert_called_once()
    args = mock_post.call_args
    assert args[0][0] == f"{ACCOUNT_ID}/messages"
    assert args[1]["data"]["recipient"]["id"] == "999"


def test_handle_dm_ignora_propria_conta():
    from webhook.handlers import handle_dm
    value = {
        "sender": {"id": ACCOUNT_ID},
        "message": {"text": "teste"},
    }
    with patch("engagement.shared.meta_client.post") as mock_post, \
         patch.dict(os.environ, {"INSTAGRAM_ACCOUNT_ID": ACCOUNT_ID}):
        handle_dm(value)
    mock_post.assert_not_called()


def test_handle_dm_ignora_texto_vazio():
    from webhook.handlers import handle_dm
    value = {"sender": {"id": "999"}, "message": {}}
    with patch("engagement.shared.meta_client.post") as mock_post, \
         patch.dict(os.environ, {"INSTAGRAM_ACCOUNT_ID": ACCOUNT_ID}):
        handle_dm(value)
    mock_post.assert_not_called()


def test_handle_dm_deduplica():
    from webhook.handlers import handle_dm
    value = {"sender": {"id": "999"}, "message": {"text": "oi"}}
    state = dict(BASE_STATE)
    state["dms_replied"] = ["999"]
    with patch("engagement.shared.meta_client.post") as mock_post, \
         patch("engagement.shared.state.load", return_value=state), \
         patch("engagement.shared.state.save"), \
         patch.dict(os.environ, {"INSTAGRAM_ACCOUNT_ID": ACCOUNT_ID}):
        handle_dm(value)
    mock_post.assert_not_called()


def test_handle_comment_responde():
    from webhook.handlers import handle_comment
    value = {
        "id": "comment_abc",
        "text": "adorei o post!",
        "from": {"id": "888"},
    }
    with patch("engagement.shared.meta_client.post") as mock_post, \
         patch("engagement.shared.claude_client.generate", return_value="Obrigada!"), \
         patch("engagement.shared.state.load", return_value=dict(BASE_STATE)), \
         patch("engagement.shared.state.save"), \
         patch.dict(os.environ, {"INSTAGRAM_ACCOUNT_ID": ACCOUNT_ID}):
        handle_comment(value)
    mock_post.assert_called_once()
    args = mock_post.call_args
    assert args[0][0] == "comment_abc/replies"


def test_handle_comment_ignora_propria_conta():
    from webhook.handlers import handle_comment
    value = {
        "id": "comment_abc",
        "text": "post meu",
        "from": {"id": ACCOUNT_ID},
    }
    with patch("engagement.shared.meta_client.post") as mock_post, \
         patch.dict(os.environ, {"INSTAGRAM_ACCOUNT_ID": ACCOUNT_ID}):
        handle_comment(value)
    mock_post.assert_not_called()


def test_handle_comment_deduplica():
    from webhook.handlers import handle_comment
    value = {"id": "comment_abc", "text": "oi", "from": {"id": "888"}}
    state = dict(BASE_STATE)
    state["comments_replied"] = ["comment_abc"]
    with patch("engagement.shared.meta_client.post") as mock_post, \
         patch("engagement.shared.state.load", return_value=state), \
         patch("engagement.shared.state.save"), \
         patch.dict(os.environ, {"INSTAGRAM_ACCOUNT_ID": ACCOUNT_ID}):
        handle_comment(value)
    mock_post.assert_not_called()
