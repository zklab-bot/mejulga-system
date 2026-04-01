"""
hashtag_intel.py
Analisa performance de hashtags nos últimos 20 posts do @dra.julga.
Gera ranking por score de engajamento e salva no engagement_state.json.

Uso:
  python -m engagement.hashtag_intel
"""
import os
import re
from datetime import datetime
from collections import defaultdict
from engagement.shared import meta_client, state


def _account_id() -> str:
    return os.getenv("IG_ACCOUNT_ID") or os.getenv("INSTAGRAM_ACCOUNT_ID", "")


def extrair_hashtags(caption: str | None) -> list[str]:
    if not caption:
        return []
    return re.findall(r"#(\w+)", caption.lower())


def calcular_score(post: dict) -> float:
    likes = post.get("like_count", 0) or 0
    comentarios = post.get("comments_count", 0) or 0
    return float(likes + (comentarios * 2))


def gerar_relatorio(posts: list) -> dict:
    stats: dict = defaultdict(lambda: {"posts": 0, "score_total": 0.0})

    for post in posts:
        for tag in extrair_hashtags(post.get("caption")):
            stats[tag]["posts"] += 1
            stats[tag]["score_total"] += calcular_score(post)

    ranking = sorted(
        [
            {
                "hashtag": f"#{tag}",
                "posts": s["posts"],
                "score_medio": round(s["score_total"] / s["posts"], 1),
            }
            for tag, s in stats.items()
        ],
        key=lambda x: x["score_medio"],
        reverse=True,
    )

    return {
        "gerado_em": datetime.now().isoformat(),
        "total_posts_analisados": len(posts),
        "ranking": ranking[:20],
    }


def executar() -> None:
    print(f"\n📊 Hashtag Intelligence — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    data = meta_client.get(
        f"{_account_id()}/media",
        params={"fields": "id,caption,like_count,comments_count,timestamp", "limit": "20"},
    )
    posts = data.get("data", [])
    print(f"  📂 {len(posts)} posts analisados")

    relatorio = gerar_relatorio(posts)

    st = state.load()
    st["hashtag_report"] = relatorio
    state.save(st)

    print(f"\n🏆 Top 5 hashtags por engajamento:")
    for i, item in enumerate(relatorio["ranking"][:5], 1):
        print(f"  {i}. {item['hashtag']} — score médio {item['score_medio']} ({item['posts']} post(s))")

    print(f"\n✅ Relatório salvo em engagement_state.json")


def main() -> None:
    executar()


if __name__ == "__main__":
    main()
