import pytest
from unittest.mock import patch, Mock


def make_mock_response(json_data, status_code=200):
    mock = Mock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    return mock


def test_get_sucesso():
    import engagement.shared.meta_client as meta_client
    with patch("requests.request") as mock_req:
        mock_req.return_value = make_mock_response({"data": [{"id": "1"}]})
        result = meta_client.get("me/media")
    assert result == {"data": [{"id": "1"}]}


def test_get_rate_limit_levanta_excecao():
    import engagement.shared.meta_client as meta_client
    with patch("requests.request") as mock_req:
        mock_req.return_value = make_mock_response(
            {"error": {"code": 32, "message": "Rate limited"}}, status_code=400
        )
        with pytest.raises(meta_client.MetaRateLimitError):
            meta_client.get("me/media")


def test_get_permissao_negada_levanta_excecao():
    import engagement.shared.meta_client as meta_client
    with patch("requests.request") as mock_req:
        mock_req.return_value = make_mock_response(
            {"error": {"code": 10, "message": "Permission denied"}}, status_code=400
        )
        with pytest.raises(meta_client.MetaPermissionError):
            meta_client.get("me/media")


def test_get_permissao_200_levanta_excecao():
    import engagement.shared.meta_client as meta_client
    with patch("requests.request") as mock_req:
        mock_req.return_value = make_mock_response(
            {"error": {"code": 200, "message": "Not approved"}}, status_code=400
        )
        with pytest.raises(meta_client.MetaPermissionError):
            meta_client.get("me/media")


def test_post_sucesso():
    import engagement.shared.meta_client as meta_client
    with patch("requests.request") as mock_req:
        mock_req.return_value = make_mock_response({"id": "comment_123"})
        result = meta_client.post("media_id/comments", data={"message": "oi"})
    assert result["id"] == "comment_123"
