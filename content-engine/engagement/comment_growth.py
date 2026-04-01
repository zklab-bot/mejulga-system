"""
comment_growth.py
Comenta em posts de páginas de fofoca/humor com a voz da Dra. Julga.
Migrado e refatorado de instagram_comentarios.py.

Uso:
  python -m engagement.comment_growth
  python -m engagement.comment_growth --dry-run

Configurar PAGINAS_ALVO com IDs reais das páginas alvo antes de usar.
Para descobrir o ID de uma conta: GET /{username}?fields=id (com access token)
"""
import argparse
import random
import time
from datetime import datetime, timedelta
from engagement.shared import meta_client, claude_client, state

MAX_POR_SESSAO = 3
COOLDOWN_HORAS = 24
MAX_IDADE_POST_HORAS = 6
INTERVALO_MIN_SEG = 8 * 60
INTERVALO_MAX_SEG = 20 * 60

# Preencher com IDs reais das páginas alvo
PAGINAS_ALVO: list[dict] = [
    # {"id": "INSTAGRAM_USER_ID", "nome": "fofocasbrasil"},
    # {"id": "INSTAGRAM_USER_ID", "nome": "polemicasbr"},
]


def _buscar_posts_recentes(pagina_id: str) -> list:
    data = meta_client.get(
        f"{pagina_id}/media",
        params={"fields": "id,caption,timestamp,media_type", "limit": "5"},
    )
    corte = datetime.now() - timedelta(hours=MAX_IDADE_POST_HORAS)
    posts = []
    for post in data.get("data", []):
        ts = datetime.fromisoformat(post["timestamp"].replace("Z", "+00:00")).replace(tzinfo=None)
        if ts > corte:
            posts.append(post)
    return posts


def _gerar_comentario(caption: str) -> str:
    return claude_client.generate(
        f'Post de fofoca/humor que você vai comentar:\n"{caption[:300]}"\n\n'
        "Escreva UM comentário curto (máximo 2 frases, até 150 caracteres). "
        "Tom: humor, ironia, diagnóstico fictício. Máximo 2 emojis. "
        "Termine com '— Dra. Julga' ou '📋 Dra. Julga'. "
        "NUNCA ataque pessoas específicas, só o comportamento. "
        "Responda APENAS com o comentário.",
        max_tokens=150,
    )


def executar(dry_run: bool = False) -> None:
    print(f"\n🌱 Comment Growth — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    if not PAGINAS_ALVO:
        print("⚠️  PAGINAS_ALVO vazia. Edite o script com os IDs das páginas alvo.")
        return

    st = state.load()
    growth_log: list = st.setdefault("growth_comments", [])
    cooldowns: dict = st.setdefault("growth_cooldowns", {})
    total = 0

    paginas = PAGINAS_ALVO.copy()
    random.shuffle(paginas)

    for pagina in paginas:
        if total >= MAX_POR_SESSAO:
            break
        pid, nome = pagina["id"], pagina["nome"]
        print(f"  📄 @{nome}...")

        if pid in cooldowns:
            ultima = datetime.fromisoformat(cooldowns[pid])
            if datetime.now() - ultima < timedelta(hours=COOLDOWN_HORAS):
                horas = COOLDOWN_HORAS - int((datetime.now() - ultima).total_seconds() / 3600)
                print(f"  ⏸️  Cooldown — aguardar ~{horas}h\n")
                continue

        posts = _buscar_posts_recentes(pid)
        if not posts:
            print(f"  📭 Nenhum post recente (<{MAX_IDADE_POST_HORAS}h)\n")
            continue

        post = random.choice(posts)
        post_id = post["id"]

        if any(c["post_id"] == post_id for c in growth_log):
            print(f"  ♻️  Já comentou nesse post\n")
            continue

        caption = post.get("caption", "")
        comentario = _gerar_comentario(caption)
        print(f"  💬 {comentario}")

        if dry_run:
            print(f"  [DRY RUN] Comentaria em {post_id}\n")
            sucesso = True
        else:
            result = meta_client.post(f"{post_id}/comments", data={"message": comentario})
            print(f"  ✅ Comentado! id={result.get('id')}\n")
            sucesso = True

        if sucesso:
            total += 1
            growth_log.append({
                "data": datetime.now().isoformat(),
                "pagina_id": pid, "pagina_nome": nome,
                "post_id": post_id, "comentario": comentario,
            })
            cooldowns[pid] = datetime.now().isoformat()

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
