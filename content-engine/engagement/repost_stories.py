"""
repost_stories.py
Detecta menções a @dra.julga e reposta como story.

Nota: usa GET /{ig-user-id}/tags para menções em feed e stories.
Menções exclusivas de stories requerem webhook (não disponível neste setup).

Uso:
  python -m engagement.repost_stories
  python -m engagement.repost_stories --dry-run
"""
import argparse
import os
from datetime import datetime
from engagement.shared import meta_client, state

MAX_REPOSTS_PER_RUN = 5


def _account_id() -> str:
    return os.getenv("IG_ACCOUNT_ID") or os.getenv("INSTAGRAM_ACCOUNT_ID", "")


def _buscar_mencoes() -> list:
    """Retorna posts de feed onde @dra.julga foi marcada."""
    data = meta_client.get(
        f"{_account_id()}/tags",
        params={"fields": "id,media_type,timestamp", "limit": "20"},
    )
    return data.get("data", [])


def _repostar(media_id: str, dry_run: bool) -> bool:
    """Reshara uma menção como story usando source_type MENTION_RESHARE."""
    account_id = _account_id()
    if dry_run:
        print(f"  [DRY RUN] Repostaria menção {media_id}")
        return True

    # Cria container de story a partir da menção original (sem precisar de URL)
    container = meta_client.post(
        f"{account_id}/media",
        data={
            "media_type": "STORIES",
            "source_type": "MENTION_RESHARE",
            "original_media_id": media_id,
        },
    )
    container_id = container.get("id")
    if not container_id:
        print(f"  ❌ Falha ao criar container para {media_id}")
        return False

    result = meta_client.post(
        f"{account_id}/media_publish",
        data={"creation_id": container_id},
    )
    print(f"  ✅ Story repostado! id={result.get('id')}")
    return True


def executar(dry_run: bool = False) -> None:
    print(f"\n📲 Repost Stories — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st = state.load()
    repostados = set(st.get("stories_reposted", []))
    total = 0

    mencoes = _buscar_mencoes()
    print(f"  📌 {len(mencoes)} menção(ões) encontrada(s)")

    for mencao in mencoes:
        if total >= MAX_REPOSTS_PER_RUN:
            break
        mid = mencao["id"]
        if mid in repostados:
            continue

        print(f"  🔄 Repostando menção {mid}...")
        if _repostar(mid, dry_run):
            repostados.add(mid)
            total += 1

    st["stories_reposted"] = list(repostados)
    state.save(st)
    print(f"\n✅ {total} story(ies) repostado(s)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    executar(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
