"""
comment_growth.py
Comenta em posts recentes de hashtags do nicho com a voz da Dra. Julga.

Usa Instagram Hashtag Search API (Graph API oficial) — sem API privada.
Limite: até 30 hashtags únicas por semana por conta.

Uso:
  python -m engagement.comment_growth
  python -m engagement.comment_growth --dry-run
"""
import argparse
import os
import random
import time
from datetime import datetime, timedelta
from engagement.shared import meta_client, claude_client, state

MAX_POR_SESSAO = 3
COOLDOWN_HORAS = 24
MAX_IDADE_POST_HORAS = 12
INTERVALO_MIN_SEG = 5 * 60
INTERVALO_MAX_SEG = 12 * 60

# Hashtags do nicho — rotacionadas por dia da semana para respeitar o limite de 30/semana
HASHTAGS_NICHO = [
    "humorbrasileiro",
    "relacionamento",
    "vidaadulta",
    "memesbrasil",
    "comportamento",
    "psicologia",
    "fofoca",
]


def _account_id() -> str:
    return os.getenv("IG_ACCOUNT_ID") or os.getenv("INSTAGRAM_ACCOUNT_ID", "")


def _buscar_hashtag_id(hashtag: str) -> str | None:
    """Resolve nome de hashtag para ID numérico via Graph API."""
    data = meta_client.get(
        "ig_hashtag_search",
        params={"user_id": _account_id(), "q": hashtag},
    )
    ids = data.get("data", [])
    return ids[0]["id"] if ids else None


def _buscar_posts_hashtag(hashtag_id: str) -> list:
    """Retorna posts recentes da hashtag filtrados por idade."""
    data = meta_client.get(
        f"{hashtag_id}/recent_media",
        params={
            "user_id": _account_id(),
            "fields": "id,caption,timestamp,media_type",
            "limit": "15",
        },
    )
    corte = datetime.now() - timedelta(hours=MAX_IDADE_POST_HORAS)
    posts = []
    for post in data.get("data", []):
        ts_str = post.get("timestamp", "")
        if not ts_str:
            posts.append(post)
            continue
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).replace(tzinfo=None)
        if ts > corte:
            posts.append(post)
    return posts


def _gerar_comentario(caption: str, hashtag: str) -> str:
    return claude_client.generate(
        f'Post recente da hashtag #{hashtag}:\n"{caption[:300]}"\n\n'
        "Escreva UM comentário curto (máximo 2 frases, até 150 caracteres). "
        "Tom: humor, ironia leve, diagnóstico fictício da Dra. Julga. Máximo 2 emojis. "
        "Termine com '— Dra. Julga' ou '📋 Dra. Julga'. "
        "NUNCA ataque pessoas específicas, só comportamentos. "
        "Responda APENAS com o comentário, sem aspas.",
        max_tokens=150,
    )


def executar(dry_run: bool = False) -> None:
    print(f"\n🌱 Comment Growth — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    st = state.load()
    growth_log: list = st.setdefault("growth_comments", [])
    cooldowns: dict = st.setdefault("growth_cooldowns", {})
    total = 0

    # Seleciona hashtags do dia + aleatoriedade para variar
    dia = datetime.now().weekday()
    hashtags_hoje = [HASHTAGS_NICHO[dia % len(HASHTAGS_NICHO)]]
    extras = [h for h in HASHTAGS_NICHO if h not in hashtags_hoje]
    random.shuffle(extras)
    hashtags_hoje += extras[:2]

    for hashtag in hashtags_hoje:
        if total >= MAX_POR_SESSAO:
            break

        # Cooldown por hashtag
        if hashtag in cooldowns:
            ultima = datetime.fromisoformat(cooldowns[hashtag])
            if datetime.now() - ultima < timedelta(hours=COOLDOWN_HORAS):
                horas_rest = COOLDOWN_HORAS - int((datetime.now() - ultima).total_seconds() / 3600)
                print(f"  ⏸️  #{hashtag}: cooldown ~{horas_rest}h")
                continue

        print(f"  🔍 #{hashtag}...")
        hashtag_id = _buscar_hashtag_id(hashtag)
        if not hashtag_id:
            print(f"  ⚠️  Não encontrou ID para #{hashtag}")
            continue

        posts = _buscar_posts_hashtag(hashtag_id)
        if not posts:
            print(f"  📭 Nenhum post recente (<{MAX_IDADE_POST_HORAS}h) em #{hashtag}")
            continue

        # Filtra posts onde já comentamos
        comentados = {c["post_id"] for c in growth_log}
        posts_novos = [p for p in posts if p["id"] not in comentados]
        if not posts_novos:
            print(f"  ♻️  Já comentamos em todos os posts recentes de #{hashtag}")
            continue

        post = random.choice(posts_novos)
        post_id = post["id"]
        caption = post.get("caption", "")

        comentario = _gerar_comentario(caption, hashtag)
        print(f"  💬 {comentario}")

        if dry_run:
            print(f"  [DRY RUN] Comentaria em {post_id} (#{hashtag})\n")
        else:
            result = meta_client.post(f"{post_id}/comments", data={"message": comentario})
            print(f"  ✅ Comentado! id={result.get('id')}\n")

        total += 1
        growth_log.append({
            "data": datetime.now().isoformat(),
            "hashtag": hashtag,
            "post_id": post_id,
            "comentario": comentario,
        })
        cooldowns[hashtag] = datetime.now().isoformat()

        if total < MAX_POR_SESSAO and not dry_run:
            espera = random.randint(INTERVALO_MIN_SEG, INTERVALO_MAX_SEG)
            print(f"  ⏳ Aguardando {espera // 60}min {espera % 60}s...\n")
            time.sleep(espera)

    state.save(st)
    print(f"\n✅ {total} comentário(s) postado(s)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    executar(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
