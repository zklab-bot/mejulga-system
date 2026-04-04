"""
post_engagement.py
Posta comentário de votação imediatamente após publicação de carrossel.

Uso:
  python -m engagement.post_engagement --media_id 123 --categoria amor
  python -m engagement.post_engagement --media_id 123 --categoria amor --dry-run
"""
import argparse
from engagement.shared import meta_client

TEMPLATES: dict[str, str] = {
    "dinheiro": (
        "Você é culpado com o dinheiro? Vota aqui 👇\n\n"
        "🔴 SIM — gastei tudo, sem defesa\n"
        "🟢 NÃO — sou financeiramente responsável\n\n"
        "Comenta o emoji!"
    ),
    "amor": (
        "Você já fez isso? Vota aqui 👇\n\n"
        "🔴 SIM — me reconheço completamente\n"
        "🟢 NÃO — sou inocente, juro\n\n"
        "Comenta o emoji!"
    ),
    "trabalho": (
        "No trabalho você é? Vota aqui 👇\n\n"
        "🔴 Procrastinador(a) assumido(a)\n"
        "🟢 Produtivo(a) de verdade\n\n"
        "Comenta o emoji!"
    ),
    "dopamina": (
        "Seu celular te domina? Vota aqui 👇\n\n"
        "🔴 SIM — não consigo largar\n"
        "🟢 NÃO — tenho controle total\n\n"
        "Comenta o emoji!"
    ),
    "vida_adulta": (
        "Você se reconhece? Vota aqui 👇\n\n"
        "🔴 SIM — totalmente eu isso aí\n"
        "🟢 NÃO — tenho tudo organizado\n\n"
        "Comenta o emoji!"
    ),
    "social": (
        "Você cancela planos? Vota aqui 👇\n\n"
        "🔴 SIM — sou cancelador(a) crônico(a)\n"
        "🟢 NÃO — apareço sempre que marco\n\n"
        "Comenta o emoji!"
    ),
    "saude_mental": (
        "Esses pensamentos te visitam? Vota aqui 👇\n\n"
        "🔴 SIM — especialmente às 3h da manhã\n"
        "🟢 NÃO — durmo tranquilo(a)\n\n"
        "Comenta o emoji!"
    ),
}

_FALLBACK = (
    "Você se identificou? Vota aqui 👇\n\n"
    "🔴 SIM — sou culpado(a), sem defesa\n"
    "🟢 NÃO — sou completamente inocente\n\n"
    "Comenta o emoji!"
)


def gerar_comentario_votacao(categoria: str) -> str:
    return TEMPLATES.get(categoria, _FALLBACK)


def postar_comentario(media_id: str, texto: str, dry_run: bool = False) -> None:
    if dry_run:
        print(f"[DRY RUN] Comentaria em {media_id}: {texto}")
        return
    result = meta_client.post(f"{media_id}/comments", data={"message": texto})
    print(f"✅ Comentário de votação postado! id={result.get('id')}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--media_id", required=True, help="ID do post publicado")
    parser.add_argument("--categoria", required=True, choices=list(TEMPLATES.keys()))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    texto = gerar_comentario_votacao(args.categoria)
    print(f"\n💬 Comentário de votação: {texto}")
    postar_comentario(args.media_id, texto, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
