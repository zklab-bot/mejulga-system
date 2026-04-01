"""
reply_dms.py
Responde DMs com palavras-chave relacionadas ao diagnóstico da Dra. Julga.

Uso:
  python -m engagement.reply_dms
  python -m engagement.reply_dms --dry-run
"""
import argparse
import os
from datetime import datetime
from engagement.shared import meta_client, claude_client, state

MAX_REPLIES_PER_RUN = 20

KEYWORDS = [
    "me julga",
    "mejulga",
    "diagnóstico",
    "diagnostico",
    "teste",
    "como funciona",
    "quero saber",
    "me avalia",
]


def _account_id() -> str:
    return os.getenv("IG_ACCOUNT_ID") or os.getenv("INSTAGRAM_ACCOUNT_ID", "")


def _contem_keyword(texto: str) -> bool:
    t = texto.lower()
    return any(kw in t for kw in KEYWORDS)


def _buscar_conversas() -> list:
    data = meta_client.get(
        f"{_account_id()}/conversations",
        params={
            "fields": "id,messages{id,message,from,created_time}",
            "limit": "20",
        },
    )
    return data.get("data", [])


def _gerar_resposta(mensagem: str) -> str:
    return claude_client.generate(
        f'Um seguidor te mandou uma DM: "{mensagem}"\n\n'
        "Responda como Dra. Julga de forma simpática e curta (máximo 3 frases). "
        "Inclua o link mejulga.com.br para o diagnóstico completo. "
        "Seja engraçada e convidativa. Responda APENAS com o texto da mensagem.",
        max_tokens=200,
    )


def executar(dry_run: bool = False) -> None:
    print(f"\n📩 Reply DMs — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st = state.load()
    respondidas = set(st.get("dms_replied", []))
    total = 0

    conversas = _buscar_conversas()
    print(f"  📬 {len(conversas)} conversa(s) encontrada(s)")

    for conversa in conversas:
        if total >= MAX_REPLIES_PER_RUN:
            break
        cid = conversa["id"]
        if cid in respondidas:
            continue

        mensagens = conversa.get("messages", {}).get("data", [])
        if not mensagens:
            continue

        ultima = mensagens[0]
        texto = ultima.get("message", "")
        if not _contem_keyword(texto):
            continue

        print(f"  📨 Keyword: {texto[:60]}...")
        resposta = _gerar_resposta(texto)
        print(f"  🤖 {resposta}")

        if dry_run:
            print(f"  [DRY RUN] Responderia conversa {cid}")
        else:
            meta_client.post(
                f"{_account_id()}/messages",
                data={"recipient": {"id": cid}, "message": {"text": resposta}},
            )
            print(f"  ✅ DM enviada!")

        respondidas.add(cid)
        total += 1

    st["dms_replied"] = list(respondidas)
    state.save(st)
    print(f"\n✅ {total} DM(s) respondida(s)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    executar(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
