"""
feedback.py
Coleta avaliações de posts via Telegram e armazena no state.

CLI:
  python -m engagement.feedback send_rating_request --chave ... --media_id ... \
      --tipo_veredicto A --titulo "..." --crime "..." --categoria amor

  python -m engagement.feedback store_rating --chave ... --nota 4
"""

import argparse
import os

import requests

from engagement.shared import state


def store_rating(chave: str, nota: int) -> None:
    """Registra a nota do dono para um post no engagement_state.json."""
    s = state.load()
    post_details = s.get("post_details", {})
    if chave in post_details:
        post_details[chave]["nota"] = nota
        state.save(s)


def send_rating_request(
    chave: str,
    media_id: str,
    tipo_veredicto: str,
    titulo: str,
    crime: str,
    categoria: str,
) -> None:
    """Salva detalhes do post no state e envia mensagem de votação no Telegram."""
    s = state.load()
    post_details = s.setdefault("post_details", {})
    post_details[chave] = {
        "media_id": media_id,
        "tipo_veredicto": tipo_veredicto,
        "titulo": titulo,
        "crime": crime,
        "categoria": categoria,
        "nota": None,
    }
    state.save(s)

    _enviar_mensagem_telegram(chave, titulo, tipo_veredicto, crime, categoria)


def _enviar_mensagem_telegram(
    chave: str,
    titulo: str,
    tipo_veredicto: str,
    crime: str,
    categoria: str,
) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return

    texto = (
        f"📊 Novo post publicado!\n"
        f'"{titulo}" — {categoria} · Variação {tipo_veredicto}\n'
        f"Crime: {crime}\n\n"
        f"Como foi esse veredicto?"
    )

    keyboard = {
        "inline_keyboard": [[
            {"text": "⭐",         "callback_data": f"rate:{chave}:1"},
            {"text": "⭐⭐",       "callback_data": f"rate:{chave}:2"},
            {"text": "⭐⭐⭐",     "callback_data": f"rate:{chave}:3"},
            {"text": "⭐⭐⭐⭐",   "callback_data": f"rate:{chave}:4"},
            {"text": "⭐⭐⭐⭐⭐", "callback_data": f"rate:{chave}:5"},
        ]]
    }

    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": texto, "reply_markup": keyboard},
            timeout=10,
        )
    except requests.exceptions.RequestException:
        pass  # Non-fatal: Telegram failure should not break the workflow


def _cli():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    p_send = sub.add_parser("send_rating_request")
    p_send.add_argument("--chave", required=True)
    p_send.add_argument("--media_id", required=True)
    p_send.add_argument("--tipo_veredicto", required=True)
    p_send.add_argument("--titulo", required=True)
    p_send.add_argument("--crime", required=True)
    p_send.add_argument("--categoria", required=True)

    p_store = sub.add_parser("store_rating")
    p_store.add_argument("--chave", required=True)
    p_store.add_argument("--nota", required=True, type=int)

    args = parser.parse_args()

    if args.cmd == "send_rating_request":
        send_rating_request(
            chave=args.chave,
            media_id=args.media_id,
            tipo_veredicto=args.tipo_veredicto,
            titulo=args.titulo,
            crime=args.crime,
            categoria=args.categoria,
        )
    elif args.cmd == "store_rating":
        store_rating(chave=args.chave, nota=args.nota)
    else:
        parser.print_help()


if __name__ == "__main__":
    _cli()
