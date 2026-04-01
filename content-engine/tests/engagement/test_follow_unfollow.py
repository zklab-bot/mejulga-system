from datetime import datetime, timedelta


def test_candidatos_ja_seguidos_sao_ignorados():
    from engagement.follow_unfollow import _filtrar_candidatos
    following = {"user_1": "2026-04-01T10:00:00", "user_2": "2026-04-01T11:00:00"}
    candidatos = ["user_1", "user_3", "user_4"]
    resultado = _filtrar_candidatos(candidatos, following)
    assert "user_1" not in resultado
    assert "user_3" in resultado
    assert "user_4" in resultado


def test_unfollow_apenas_apos_7_dias():
    from engagement.follow_unfollow import _candidatos_para_unfollow
    agora = datetime.now()
    following = {
        "user_old": (agora - timedelta(days=8)).isoformat(),
        "user_new": (agora - timedelta(days=2)).isoformat(),
    }
    seguidores = set()
    resultado = _candidatos_para_unfollow(following, seguidores)
    assert "user_old" in resultado
    assert "user_new" not in resultado


def test_unfollow_nao_dessegue_quem_seguiu_de_volta():
    from engagement.follow_unfollow import _candidatos_para_unfollow
    agora = datetime.now()
    following = {
        "user_fiel": (agora - timedelta(days=10)).isoformat(),
    }
    seguidores = {"user_fiel"}
    resultado = _candidatos_para_unfollow(following, seguidores)
    assert "user_fiel" not in resultado
