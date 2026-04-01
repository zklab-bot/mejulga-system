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
