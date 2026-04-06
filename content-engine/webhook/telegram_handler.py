"""
telegram_handler.py
Processa comandos recebidos via webhook do Telegram.

Comandos disponíveis:
  /help, /status, /relatorio, /forcar_post [cat], /proximos,
  /ultimo, /pausar, /retomar, /preview [cat], /erros
"""

import os
from datetime import datetime, timezone, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()

_TOKEN = lambda: os.getenv("TELEGRAM_BOT_TOKEN", "")
_OWNER_CHAT_ID = lambda: int(os.getenv("TELEGRAM_CHAT_ID", "0"))
_PAT = lambda: os.getenv("GITHUB_PAT", "")
_REPO = lambda: os.getenv("GITHUB_REPO", "owner/mejulga-system")

# Slots em UTC
_CRON_SLOTS_UTC = [12, 15, 21, 23, 1]
_CRON_LABELS_BRT = ["09h", "12h", "18h", "20h", "22h"]

HELP_TEXT = (
    "🤖 *Dra. Julga Monitor*\n\n"
    "Comandos disponíveis:\n"
    "/status — estado atual e próximo post\n"
    "/relatorio — posts dos últimos 7 dias\n"
    "/forcar\\_post categoria — força post agora\n"
    "/proximos — próximos horários do dia\n"
    "/ultimo — último post publicado\n"
    "/pausar — pausa os posts automáticos\n"
    "/retomar — retoma os posts automáticos\n"
    "/preview categoria — gera preview sem postar\n"
    "/erros — últimos erros registrados\n"
    "/help — esta mensagem"
)


def handle(update: dict) -> None:
    """Entry point — chamado pelo endpoint /telegram."""
    msg = update.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text = (msg.get("text") or "").strip()

    if chat_id != _OWNER_CHAT_ID():
        return  # silenciosamente ignorar

    parts = text.split(maxsplit=1)
    cmd = parts[0].lower() if parts else ""
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd == "/help":
        _reply(chat_id, HELP_TEXT)
    elif cmd == "/status":
        _cmd_status(chat_id)
    elif cmd == "/relatorio":
        _cmd_relatorio(chat_id)
    elif cmd == "/forcar_post":
        _cmd_forcar_post(chat_id, arg)
    elif cmd == "/proximos":
        _cmd_proximos(chat_id)
    elif cmd == "/ultimo":
        _cmd_ultimo(chat_id)
    elif cmd == "/pausar":
        _cmd_pausar(chat_id)
    elif cmd == "/retomar":
        _cmd_retomar(chat_id)
    elif cmd == "/preview":
        _cmd_preview(chat_id, arg)
    elif cmd == "/erros":
        _cmd_erros(chat_id)
    else:
        _reply(chat_id, f"Comando não reconhecido: `{cmd}`\nUse /help para ver os comandos.")


# ── Comandos ──────────────────────────────────────────────────────────────────

def _cmd_status(chat_id: int) -> None:
    state = _fetch_state()
    published = state.get("posts_published", [])
    errors = state.get("errors", [])
    hoje = _hoje_str()
    hoje_posts = [p for p in published if p.startswith(hoje)]

    proximo = _proximo_slot_brt()
    erros_count = len([e for e in errors if e.get("timestamp", "").startswith(hoje)])

    linhas = [f"  ✅ {p.split('_', 1)[1]}" for p in hoje_posts] or ["  (nenhum ainda)"]
    msg = (
        f"📊 *Status — {_hoje_fmt()}*\n\n"
        f"📸 Posts hoje: {len(hoje_posts)}/5\n"
        + "\n".join(linhas)
        + f"\n\n🕐 Próximo slot: *{proximo}*"
        + (f"\n⚠️ Erros hoje: {erros_count}" if erros_count else "")
    )
    _reply(chat_id, msg)


def _cmd_relatorio(chat_id: int) -> None:
    state = _fetch_state()
    published = state.get("posts_published", [])
    hoje = datetime.now(timezone.utc).date()
    linhas = []
    for delta in range(7):
        d = (hoje - timedelta(days=delta)).strftime("%Y-%m-%d")
        d_fmt = (hoje - timedelta(days=delta)).strftime("%d/%m")
        posts_dia = [p for p in published if p.startswith(d)]
        cats = ", ".join(p.split("_", 1)[1] for p in posts_dia) or "nenhum"
        linhas.append(f"  {d_fmt}: {len(posts_dia)} ({cats})")
    msg = "📊 *Relatório — 7 dias*\n\n" + "\n".join(linhas)
    _reply(chat_id, msg)


def _cmd_forcar_post(chat_id: int, categoria: str) -> None:
    cat = categoria or _categoria_do_dia()
    _reply(chat_id, f"🚀 Forçando post da categoria *{cat}*...")
    try:
        _dispatch_workflow("daily_post.yml", inputs={"categoria": cat})
        _reply(chat_id, f"✅ Workflow acionado para *{cat}*")
    except Exception as e:
        _reply(chat_id, f"❌ Erro ao acionar workflow: {e}")


def _cmd_proximos(chat_id: int) -> None:
    agora_utc = datetime.now(timezone.utc)
    hoje = agora_utc.date()
    slots = []
    for h_utc, label_brt in zip(_CRON_SLOTS_UTC, _CRON_LABELS_BRT):
        slot_dt = datetime(hoje.year, hoje.month, hoje.day, h_utc, 0, tzinfo=timezone.utc)
        if slot_dt < agora_utc:
            slot_dt += timedelta(days=1)
        diff = slot_dt - agora_utc
        horas = int(diff.total_seconds() // 3600)
        mins = int((diff.total_seconds() % 3600) // 60)
        slots.append(f"  🕐 {label_brt} BRT — em {horas}h{mins:02d}m")
    msg = "📅 *Próximos posts*\n\n" + "\n".join(slots)
    _reply(chat_id, msg)


def _cmd_ultimo(chat_id: int) -> None:
    state = _fetch_state()
    published = state.get("posts_published", [])
    if not published:
        _reply(chat_id, "📭 Nenhum post publicado ainda.")
        return
    ultimo = published[-1]
    parts = ultimo.split("_", 1)
    data, cat = parts[0], parts[1] if len(parts) > 1 else ultimo
    _reply(chat_id, f"📸 *Último post*\nCategoria: {cat}\nData: {data}")


def _cmd_pausar(chat_id: int) -> None:
    try:
        _set_workflow_state("daily_post.yml", enabled=False)
        _reply(chat_id, "⏸️ Posts automáticos *pausados*.\nUse /retomar para reativar.")
    except Exception as e:
        _reply(chat_id, f"❌ Erro ao pausar: {e}")


def _cmd_retomar(chat_id: int) -> None:
    try:
        _set_workflow_state("daily_post.yml", enabled=True)
        _reply(chat_id, "▶️ Posts automáticos *retomados*.")
    except Exception as e:
        _reply(chat_id, f"❌ Erro ao retomar: {e}")


def _cmd_preview(chat_id: int, categoria: str) -> None:
    cat = categoria or _categoria_do_dia()
    _reply(chat_id, f"👁️ Gerando preview para *{cat}* (sem postar)...")
    try:
        _dispatch_workflow("preview_post.yml", inputs={"categoria": cat})
        _reply(chat_id, f"✅ Preview workflow acionado para *{cat}*\nAcompanhe no GitHub Actions.")
    except Exception as e:
        _reply(chat_id, f"❌ Erro ao acionar preview: {e}")


def _cmd_erros(chat_id: int) -> None:
    state = _fetch_state()
    errors = state.get("errors", [])
    if not errors:
        _reply(chat_id, "✅ Nenhum erro registrado.")
        return
    linhas = []
    for e in errors[-10:]:
        ts = e.get("timestamp", "")[:16].replace("T", " ")
        linhas.append(f"  • {ts} [{e.get('context')}] {e.get('message')}")
    msg = f"⚠️ *Últimos {len(linhas)} erros*\n\n" + "\n".join(linhas)
    _reply(chat_id, msg)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _reply(chat_id: int, text: str) -> None:
    token = _TOKEN()
    if not token:
        return
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        timeout=10,
    )


def _fetch_state() -> dict:
    """Lê engagement_state.json via GitHub Raw API."""
    pat = _PAT()
    repo = _REPO()
    url = f"https://raw.githubusercontent.com/{repo}/main/content-engine/generated/engagement_state.json"
    headers = {"Authorization": f"token {pat}"} if pat else {}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}


def _dispatch_workflow(workflow: str, inputs: dict = None) -> None:
    repo = _REPO()
    pat = _PAT()
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches"
    resp = requests.post(
        url,
        headers={"Authorization": f"token {pat}", "Accept": "application/vnd.github+json"},
        json={"ref": "main", "inputs": inputs or {}},
        timeout=15,
    )
    if resp.status_code not in (204, 200):
        raise RuntimeError(f"GitHub API {resp.status_code}: {resp.text}")


def _set_workflow_state(workflow: str, enabled: bool) -> None:
    repo = _REPO()
    pat = _PAT()
    action = "enable" if enabled else "disable"
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/{action}"
    resp = requests.put(
        url,
        headers={"Authorization": f"token {pat}", "Accept": "application/vnd.github+json"},
        timeout=15,
    )
    if resp.status_code not in (204, 200):
        raise RuntimeError(f"GitHub API {resp.status_code}: {resp.text}")


def _hoje_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _hoje_fmt() -> str:
    return datetime.now(timezone.utc).strftime("%d/%m/%Y")


def _proximo_slot_brt() -> str:
    agora_utc = datetime.now(timezone.utc)
    hoje = agora_utc.date()
    for h_utc, label_brt in zip(_CRON_SLOTS_UTC, _CRON_LABELS_BRT):
        slot_dt = datetime(hoje.year, hoje.month, hoje.day, h_utc, 0, tzinfo=timezone.utc)
        if slot_dt > agora_utc:
            return label_brt
    return _CRON_LABELS_BRT[0] + " (amanhã)"


def _categoria_do_dia() -> str:
    """Retorna a categoria do próximo slot baseada na rotação do daily_post.yml."""
    agora_utc = datetime.now(timezone.utc)
    dia_semana = agora_utc.isoweekday()  # 1=seg ... 7=dom
    idx = (dia_semana - 1) % 7
    hora_utc = agora_utc.hour
    slots_categorias = [
        ["dinheiro", "amor", "trabalho", "dopamina", "vida_adulta", "social", "saude_mental"],
        ["amor", "trabalho", "dopamina", "vida_adulta", "social", "saude_mental", "dinheiro"],
        ["trabalho", "dopamina", "vida_adulta", "social", "saude_mental", "dinheiro", "amor"],
        ["dopamina", "vida_adulta", "social", "saude_mental", "dinheiro", "amor", "trabalho"],
        ["vida_adulta", "social", "saude_mental", "dinheiro", "amor", "trabalho", "dopamina"],
    ]
    slot_map = {12: 0, 15: 1, 21: 2, 23: 3, 1: 4}
    slot_idx = slot_map.get(hora_utc, 0)
    return slots_categorias[slot_idx][idx]
