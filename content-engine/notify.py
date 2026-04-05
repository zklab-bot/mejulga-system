"""
notify.py
Envia notificações ao Telegram. Usado pelo GitHub Actions.

Uso:
  python -m notify send_post_published --categoria amor --titulo "O Título" --hora 09h04 --media_id 123
  python -m notify send_post_failed --categoria trabalho --hora 12h01 --erro "403 Forbidden"
  python -m notify send_post_skipped --categoria social
  python -m notify send_voting_comment --media_id 123
  python -m notify send_daily_report --state-file content-engine/generated/engagement_state.json
"""

import argparse
import json
import os
import sys
from datetime import date

import requests
from dotenv import load_dotenv

load_dotenv()


def send(text: str) -> None:
    """Envia mensagem de texto ao Telegram."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("⚠️  TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID não configurados — pulando notificação")
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }, timeout=10)
    if resp.status_code != 200:
        print(f"⚠️  Telegram API erro {resp.status_code}: {resp.text}")


def send_post_published(categoria: str, titulo: str, hora: str, media_id: str) -> None:
    send(f"✅ *{titulo}* postado!\n📂 {categoria} • 🕘 {hora}\n🆔 `{media_id}`")


def send_post_failed(categoria: str, hora: str, erro: str) -> None:
    send(f"❌ Falha ao postar\n📂 {categoria} • 🕛 {hora}\n⚠️ {erro}")


def send_post_skipped(categoria: str) -> None:
    send(f"⏭️ Post pulado — *{categoria}* já publicado hoje")


def send_voting_comment(media_id: str) -> None:
    send(f"💬 Votação postada em `{media_id}`")


def send_daily_report(state: dict) -> None:
    hoje = date.today().strftime("%Y-%m-%d")
    hoje_fmt = date.today().strftime("%d/%m/%Y")
    published = state.get("posts_published", [])
    errors = state.get("errors", [])

    hoje_posts = [p for p in published if p.startswith(hoje)]
    linhas = []
    for p in hoje_posts:
        parts = p.split("_", 1)
        cat = parts[1] if len(parts) > 1 else p
        linhas.append(f"  ✅ {cat}")

    posts_str = "\n".join(linhas) if linhas else "  (nenhum)"

    erros_hoje = [e for e in errors if e.get("timestamp", "").startswith(hoje)]
    erros_str = ""
    if erros_hoje:
        erros_linhas = [f"  • {e['context']}: {e['message']}" for e in erros_hoje]
        erros_str = f"\n\n⚠️ Erros hoje: {len(erros_hoje)}\n" + "\n".join(erros_linhas)

    msg = (
        f"📊 *RELATÓRIO — {hoje_fmt}*\n\n"
        f"📸 Posts publicados hoje: {len(hoje_posts)}\n"
        f"{posts_str}"
        f"{erros_str}"
    )
    send(msg)


def _main():
    parser = argparse.ArgumentParser(description="Notificações Telegram da Dra. Julga")
    sub = parser.add_subparsers(dest="cmd")

    p_pub = sub.add_parser("send_post_published")
    p_pub.add_argument("--categoria", required=True)
    p_pub.add_argument("--titulo", required=True)
    p_pub.add_argument("--hora", required=True)
    p_pub.add_argument("--media_id", required=True)

    p_fail = sub.add_parser("send_post_failed")
    p_fail.add_argument("--categoria", required=True)
    p_fail.add_argument("--hora", required=True)
    p_fail.add_argument("--erro", required=True)

    p_skip = sub.add_parser("send_post_skipped")
    p_skip.add_argument("--categoria", required=True)

    p_vote = sub.add_parser("send_voting_comment")
    p_vote.add_argument("--media_id", required=True)

    p_rep = sub.add_parser("send_daily_report")
    p_rep.add_argument("--state-file", required=True)

    p_send = sub.add_parser("send")
    p_send.add_argument("text")

    args = parser.parse_args()

    if args.cmd == "send":
        send(args.text)
    elif args.cmd == "send_post_published":
        send_post_published(args.categoria, args.titulo, args.hora, args.media_id)
    elif args.cmd == "send_post_failed":
        send_post_failed(args.categoria, args.hora, args.erro)
    elif args.cmd == "send_post_skipped":
        send_post_skipped(args.categoria)
    elif args.cmd == "send_voting_comment":
        send_voting_comment(args.media_id)
    elif args.cmd == "send_daily_report":
        with open(args.state_file, encoding="utf-8") as f:
            state = json.load(f)
        send_daily_report(state)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    _main()
