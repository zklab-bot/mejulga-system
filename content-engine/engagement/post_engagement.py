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
    "dinheiro": "Você é culpado com o dinheiro? 🔴 SIM, gastei tudo / 🟢 NÃO, sou responsável — vota aqui embaixo",
    "amor": "Você já fez isso? 🔴 SIM, me reconheço / 🟢 NÃO, sou inocente — julga aqui embaixo",
    "trabalho": "No trabalho você é? 🔴 Procrastinador assumido / 🟢 Produtivo de verdade — vota aqui",
    "dopamina": "Seu celular te domina? 🔴 SIM, não consigo largar / 🟢 NÃO, tenho controle — responde aqui",
    "vida_adulta": "Você se reconhece? 🔴 SIM, totalmente eu / 🟢 NÃO, tenho tudo organizado — vota",
    "social": "Você cancela planos? 🔴 SIM, sou cancelador(a) / 🟢 NÃO, apareço sempre — responde",
    "saude_mental": "Esses pensamentos te visitam? 🔴 SIM, especialmente de madrugada / 🟢 NÃO, durmo bem — vota",
}

_FALLBACK = "Você se identificou? 🔴 SIM, sou culpado(a) / 🟢 NÃO, sou inocente — vota aqui embaixo"


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
