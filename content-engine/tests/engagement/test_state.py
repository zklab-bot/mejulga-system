from pathlib import Path


def test_load_retorna_default_quando_arquivo_nao_existe(tmp_path, monkeypatch):
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    result = state.load()
    assert result["comments_replied"] == []
    assert result["stories_reposted"] == []
    assert result["dms_replied"] == []
    assert result["following"] == {}
    assert result["hashtag_report"] == {}


def test_save_e_load_roundtrip(tmp_path, monkeypatch):
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    data = {
        "comments_replied": ["abc123"],
        "stories_reposted": [],
        "dms_replied": ["dm1"],
        "following": {"user1": "2026-04-01T10:00:00"},
        "hashtag_report": {"ranking": []},
    }
    state.save(data)
    result = state.load()
    assert result == data


def test_load_cria_pasta_se_nao_existir(tmp_path, monkeypatch):
    import engagement.shared.state as state
    pasta = tmp_path / "sub" / "pasta"
    monkeypatch.setattr(state, "STATE_FILE", pasta / "state.json")
    state.load()
    assert pasta.exists()


def test_default_state_tem_errors(tmp_path, monkeypatch):
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    result = state.load()
    assert result["errors"] == []


def test_log_error_adiciona_e_limita_20(tmp_path, monkeypatch):
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    for i in range(25):
        state.log_error("ctx", f"erro {i}")
    s = state.load()
    assert len(s["errors"]) == 20
    assert s["errors"][-1]["message"] == "erro 24"
    assert s["errors"][0]["message"] == "erro 5"


def test_log_error_estrutura(tmp_path, monkeypatch):
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    state.log_error("post_carrossel", "403 Forbidden")
    s = state.load()
    err = s["errors"][0]
    assert err["context"] == "post_carrossel"
    assert err["message"] == "403 Forbidden"
    assert "timestamp" in err


def test_default_state_tem_post_details(tmp_path, monkeypatch):
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    result = state.load()
    assert result["post_details"] == {}
