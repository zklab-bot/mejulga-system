def test_extrair_hashtags_simples():
    from engagement.hashtag_intel import extrair_hashtags
    tags = extrair_hashtags("Oi #DraJulga #humor estou aqui #Brasil")
    assert "drajulga" in tags
    assert "humor" in tags
    assert "brasil" in tags


def test_extrair_hashtags_caption_vazia():
    from engagement.hashtag_intel import extrair_hashtags
    assert extrair_hashtags("") == []
    assert extrair_hashtags(None) == []


def test_calcular_score():
    from engagement.hashtag_intel import calcular_score
    post = {"like_count": 100, "comments_count": 20}
    assert calcular_score(post) == 140.0


def test_calcular_score_sem_dados():
    from engagement.hashtag_intel import calcular_score
    assert calcular_score({}) == 0.0


def test_gerar_relatorio_ranking():
    from engagement.hashtag_intel import gerar_relatorio
    posts = [
        {"caption": "#humor #brasil", "like_count": 100, "comments_count": 10},
        {"caption": "#humor #meme", "like_count": 200, "comments_count": 20},
        {"caption": "#brasil", "like_count": 10, "comments_count": 1},
    ]
    rel = gerar_relatorio(posts)
    assert rel["total_posts_analisados"] == 3
    ranking_tags = [r["hashtag"] for r in rel["ranking"]]
    assert ranking_tags.index("#humor") < ranking_tags.index("#brasil")


def test_gerar_relatorio_sem_posts():
    from engagement.hashtag_intel import gerar_relatorio
    rel = gerar_relatorio([])
    assert rel["total_posts_analisados"] == 0
    assert rel["ranking"] == []
