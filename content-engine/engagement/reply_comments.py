"""
reply_comments.py
Responde comentários novos nos posts do @dra.julga.

Uso:
  python -m engagement.reply_comments
  python -m engagement.reply_comments --dry-run
"""
import argparse
import os
from datetime import datetime
from engagement.shared import meta_client, claude_client, state

MAX_REPLIES_PER_RUN = 10


def _account_id() -> str:
    return os.getenv("IG_ACCOUNT_ID") or os.getenv("INSTAGRAM_ACCOUNT_ID", "")


def _buscar_posts() -> list:
    data = meta_client.get(
        f"{_account_id()}/media",
        params={"fields": "id,caption,timestamp", "limit": "10"},
    )
    return data.get("data", [])


def _buscar_comentarios(media_id: str) -> list:
    data = meta_client.get(
        f"{media_id}/comments",
        params={"fields": "id,text,timestamp,replies{id}", "limit": "50"},
    )
    return data.get("data", [])


def _gerar_resposta(texto: str) -> str:
    return claude_client.generate(
        f'Um seguidor comentou no seu post: "{texto}"\n\n'
        "Responda de forma curta (máximo 2 frases, até 150 caracteres). "
        "Seja engraçada e acolhedora. Máximo 2 emojis. "
        "Responda APENAS com o texto da resposta.",
        max_tokens=150,
    )


def executar(dry_run: bool = False) -> None:
    print(f"\n💬 Reply Comments — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st = state.load()
    replied = set(st.get("comments_replied", []))
    total = 0

    for post in _buscar_posts():
        if total >= MAX_REPLIES_PER_RUN:
            break
        for comentario in _buscar_comentarios(post["id"]):
            if total >= MAX_REPLIES_PER_RUN:
                break
            cid = comentario["id"]
            texto = comentario.get("text", "").strip()
            if not texto or cid in replied:
                continue
            if comentario.get("replies", {}).get("data"):
                continue  # já tem reply

            print(f"  💬 {texto[:60]}...")
            resposta = _gerar_resposta(texto)
            print(f"  🤖 {resposta}")

            if dry_run:
                print(f"  [DRY RUN] Responderia comentário {cid}")
            else:
                result = meta_client.post(f"{cid}/replies", data={"message": resposta})
                print(f"  ✅ Resposta postada! id={result.get('id')}")

            replied.add(cid)
            total += 1

    st["comments_replied"] = list(replied)
    state.save(st)
    print(f"\n✅ {total} resposta(s) postada(s)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    executar(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
