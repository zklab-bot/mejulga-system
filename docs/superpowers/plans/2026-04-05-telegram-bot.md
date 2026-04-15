# Telegram Bot — Canal de Comando e Relatórios — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Canal bidirecional via Telegram para monitorar e controlar o bot da Dra. Julga — notificações automáticas de cada evento do sistema + 10 comandos remotos.

**Architecture:** GitHub Actions chama `notify.py` para enviar mensagens ao Telegram. O Telegram envia comandos via webhook para o Railway FastAPI (`/telegram` endpoint), onde `telegram_handler.py` processa e responde. O estado do sistema é lido via GitHub Raw API (o arquivo `engagement_state.json` vive no repositório).

**Tech Stack:** Python `requests` (Telegram API), FastAPI (endpoint), GitHub REST API (workflow dispatch + raw file read), GitHub Actions (cron + notify steps).

---

## File Map

| Ação | Arquivo | Responsabilidade |
|------|---------|-----------------|
| Criar | `content-engine/notify.py` | Envia notificações ao Telegram. CLI para GitHub Actions. |
| Criar | `content-engine/webhook/telegram_handler.py` | Processa 10 comandos do Telegram. |
| Modificar | `content-engine/webhook/server.py` | Adiciona endpoint `POST /telegram`. |
| Modificar | `content-engine/engagement/shared/state.py` | Adiciona `errors` ao DEFAULT_STATE + `log_error()`. |
| Modificar | `.github/workflows/daily_post.yml` | Steps de notificação + log de erros. |
| Criar | `.github/workflows/daily_report.yml` | Relatório diário às 22h BRT. |
| Criar | `.github/workflows/preview_post.yml` | Gera preview sem postar (acionado por /preview). |
| Criar | `content-engine/tests/test_notify.py` | Testes para notify.py. |
| Criar | `content-engine/tests/webhook/test_telegram.py` | Testes para handler + endpoint. |

---

### Task 1: state.py — suporte a errors

**Files:**
- Modify: `content-engine/engagement/shared/state.py`
- Test: `content-engine/tests/engagement/test_state.py`

- [ ] **Step 1: Escrever os testes que vão falhar**

Adicionar ao final de `content-engine/tests/engagement/test_state.py`:

```python
def test_default_state_tem_errors(tmp_path, monkeypatch):
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    result = state.load()
    assert result["errors"] == []


def test_log_error_adiciona_e_limita_20(tmp_path, monkeypatch):
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    for i in range(25):
        state.log_error("ctx", f"erro {i}")
    s = state.load()
    assert len(s["errors"]) == 20
    assert s["errors"][-1]["message"] == "erro 24"
    assert s["errors"][0]["message"] == "erro 5"


def test_log_error_estrutura(tmp_path, monkeypatch):
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    state.log_error("post_carrossel", "403 Forbidden")
    s = state.load()
    err = s["errors"][0]
    assert err["context"] == "post_carrossel"
    assert err["message"] == "403 Forbidden"
    assert "timestamp" in err
```

- [ ] **Step 2: Rodar para confirmar que falham**

```bash
cd content-engine && python -m pytest tests/engagement/test_state.py -v
```

Esperado: FAIL com `KeyError: 'errors'` e `AttributeError: module has no attribute 'log_error'`

- [ ] **Step 3: Implementar no state.py**

Substituir o conteúdo de `content-engine/engagement/shared/state.py`:

```python
import copy
import json
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = Path(__file__).parent.parent.parent / "generated" / "engagement_state.json"

DEFAULT_STATE: dict = {
    "comments_replied": [],
    "stories_reposted": [],
    "dms_replied": [],
    "following": {},
    "hashtag_report": {},
    "errors": [],
}


def load() -> dict:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.exists():
        return copy.deepcopy(DEFAULT_STATE)
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def log_error(context: str, message: str) -> None:
    """Appends error to state errors list (keeps last 20)."""
    state = load()
    errors = state.setdefault("errors", [])
    errors.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "context": context,
        "message": message,
    })
    state["errors"] = errors[-20:]
    save(state)
```

- [ ] **Step 4: Rodar testes — devem passar**

```bash
cd content-engine && python -m pytest tests/engagement/test_state.py -v
```

Esperado: PASS em todos os testes

- [ ] **Step 5: Commit**

```bash
git add content-engine/engagement/shared/state.py content-engine/tests/engagement/test_state.py
git commit -m "feat: add errors list and log_error() to state"
```

---

### Task 2: notify.py — notificações do Telegram para GitHub Actions

**Files:**
- Create: `content-engine/notify.py`
- Create: `content-engine/tests/test_notify.py`

- [ ] **Step 1: Escrever os testes que vão falhar**

Criar `content-engine/tests/test_notify.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import patch, MagicMock
import notify


def _mock_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")


def test_send_faz_post_correto(monkeypatch):
    _mock_env(monkeypatch)
    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        notify.send("Teste de mensagem")
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "123:ABC" in args[0]
    assert kwargs["json"]["chat_id"] == "999"
    assert kwargs["json"]["text"] == "Teste de mensagem"


def test_send_post_published_formata_mensagem(monkeypatch):
    _mock_env(monkeypatch)
    with patch("notify.send") as mock_send:
        notify.send_post_published("amor", "O Ciumento Silencioso", "09h04", "123456")
    mock_send.assert_called_once()
    msg = mock_send.call_args[0][0]
    assert "09h04" in msg
    assert "amor" in msg
    assert "O Ciumento Silencioso" in msg


def test_send_post_failed_formata_mensagem(monkeypatch):
    _mock_env(monkeypatch)
    with patch("notify.send") as mock_send:
        notify.send_post_failed("trabalho", "12h01", "403 Forbidden")
    msg = mock_send.call_args[0][0]
    assert "trabalho" in msg
    assert "403 Forbidden" in msg


def test_send_post_skipped_formata_mensagem(monkeypatch):
    _mock_env(monkeypatch)
    with patch("notify.send") as mock_send:
        notify.send_post_skipped("social")
    msg = mock_send.call_args[0][0]
    assert "social" in msg


def test_send_daily_report_formata_estado(monkeypatch):
    _mock_env(monkeypatch)
    from datetime import date
    hoje = date.today().strftime("%Y-%m-%d")
    state = {
        "posts_published": [f"{hoje}_amor", f"{hoje}_trabalho"],
        "errors": [],
    }
    with patch("notify.send") as mock_send:
        notify.send_daily_report(state)
    msg = mock_send.call_args[0][0]
    assert "amor" in msg
    assert "trabalho" in msg
```

- [ ] **Step 2: Rodar para confirmar que falham**

```bash
cd content-engine && python -m pytest tests/test_notify.py -v
```

Esperado: FAIL com `ModuleNotFoundError: No module named 'notify'`

- [ ] **Step 3: Implementar notify.py**

Criar `content-engine/notify.py`:

```python
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

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def send(text: str) -> None:
    """Envia mensagem de texto ao Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID não configurados — pulando notificação")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
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

    args = parser.parse_args()

    if args.cmd == "send_post_published":
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
```

- [ ] **Step 4: Rodar testes — devem passar**

```bash
cd content-engine && python -m pytest tests/test_notify.py -v
```

Esperado: PASS em todos os testes

- [ ] **Step 5: Commit**

```bash
git add content-engine/notify.py content-engine/tests/test_notify.py
git commit -m "feat: add notify.py for Telegram notifications from GitHub Actions"
```

---

### Task 3: telegram_handler.py — 10 comandos

**Files:**
- Create: `content-engine/webhook/telegram_handler.py`
- Create: `content-engine/tests/webhook/test_telegram.py` (parcial — testes do handler)

Os comandos que leem estado vão ler `engagement_state.json` via GitHub Raw API usando `GITHUB_PAT`. Comandos que acionam workflows usam GitHub Actions API.

- [ ] **Step 1: Escrever os testes que vão falhar**

Criar `content-engine/tests/webhook/test_telegram.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import json
from unittest.mock import patch, MagicMock
from webhook import telegram_handler as th


def _make_update(text: str, chat_id: int = 999) -> dict:
    return {
        "message": {
            "chat": {"id": chat_id},
            "text": text,
        }
    }


def _mock_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")
    monkeypatch.setenv("TELEGRAM_SECRET", "secret")
    monkeypatch.setenv("GITHUB_PAT", "ghp_test")
    monkeypatch.setenv("GITHUB_REPO", "owner/mejulga-system")


def test_handle_ignora_chat_id_errado(monkeypatch):
    _mock_env(monkeypatch)
    with patch("webhook.telegram_handler._reply") as mock_reply:
        th.handle({"message": {"chat": {"id": 888}, "text": "/help"}})
    mock_reply.assert_not_called()


def test_help_retorna_texto(monkeypatch):
    _mock_env(monkeypatch)
    with patch("webhook.telegram_handler._reply") as mock_reply:
        th.handle(_make_update("/help"))
    mock_reply.assert_called_once()
    msg = mock_reply.call_args[0][1]
    assert "/status" in msg
    assert "/forcar_post" in msg


def test_comando_desconhecido_responde_help(monkeypatch):
    _mock_env(monkeypatch)
    with patch("webhook.telegram_handler._reply") as mock_reply:
        th.handle(_make_update("/xyzzy"))
    mock_reply.assert_called_once()
    msg = mock_reply.call_args[0][1]
    assert "/help" in msg


def test_erros_le_state(monkeypatch):
    _mock_env(monkeypatch)
    state = {
        "errors": [
            {"timestamp": "2026-04-05T12:00:00", "context": "post_carrossel", "message": "403"}
        ]
    }
    with patch("webhook.telegram_handler._fetch_state", return_value=state), \
         patch("webhook.telegram_handler._reply") as mock_reply:
        th.handle(_make_update("/erros"))
    msg = mock_reply.call_args[0][1]
    assert "403" in msg
    assert "post_carrossel" in msg


def test_ultimo_sem_posts(monkeypatch):
    _mock_env(monkeypatch)
    state = {"posts_published": []}
    with patch("webhook.telegram_handler._fetch_state", return_value=state), \
         patch("webhook.telegram_handler._reply") as mock_reply:
        th.handle(_make_update("/ultimo"))
    msg = mock_reply.call_args[0][1]
    assert "nenhum" in msg.lower()


def test_forcar_post_sem_arg_usa_categoria_do_dia(monkeypatch):
    _mock_env(monkeypatch)
    with patch("webhook.telegram_handler._dispatch_workflow") as mock_disp, \
         patch("webhook.telegram_handler._reply"):
        th.handle(_make_update("/forcar_post"))
    mock_disp.assert_called_once()


def test_forcar_post_com_categoria(monkeypatch):
    _mock_env(monkeypatch)
    with patch("webhook.telegram_handler._dispatch_workflow") as mock_disp, \
         patch("webhook.telegram_handler._reply"):
        th.handle(_make_update("/forcar_post amor"))
    _, kwargs = mock_disp.call_args
    assert kwargs.get("inputs", {}).get("categoria") == "amor"
```

- [ ] **Step 2: Rodar para confirmar que falham**

```bash
cd content-engine && python -m pytest tests/webhook/test_telegram.py -v
```

Esperado: FAIL com `ImportError`

- [ ] **Step 3: Implementar telegram_handler.py**

Criar `content-engine/webhook/telegram_handler.py`:

```python
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

CATEGORIAS = ["dinheiro", "amor", "trabalho", "dopamina", "vida_adulta", "social", "saude_mental"]

HELP_TEXT = """\
🤖 *Dra. Julga Monitor*

Comandos disponíveis:
/status — estado atual e próximo post
/relatorio — posts dos últimos 7 dias
/forcar\_post \[cat\] — força post agora
/proximos — próximos horários do dia
/ultimo — último post publicado
/pausar — pausa os posts automáticos
/retomar — retoma os posts automáticos
/preview \[cat\] — gera preview sem postar
/erros — últimos erros registrados
/help — esta mensagem"""


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
```

- [ ] **Step 4: Rodar testes — devem passar**

```bash
cd content-engine && python -m pytest tests/webhook/test_telegram.py -v
```

Esperado: PASS em todos os testes

- [ ] **Step 5: Commit**

```bash
git add content-engine/webhook/telegram_handler.py content-engine/tests/webhook/test_telegram.py
git commit -m "feat: add telegram_handler.py with 10 commands"
```

---

### Task 4: server.py — endpoint /telegram

**Files:**
- Modify: `content-engine/webhook/server.py`
- Test: `content-engine/tests/webhook/test_server.py` (adicionar testes)

- [ ] **Step 1: Escrever testes que vão falhar**

Adicionar ao final de `content-engine/tests/webhook/test_server.py`:

```python
def test_telegram_sem_secret_retorna_403():
    os.environ.setdefault("TELEGRAM_SECRET", "meu_secret")
    client = get_client()
    resp = client.post("/telegram", json={"message": {"chat": {"id": 1}, "text": "/help"}})
    assert resp.status_code == 403


def test_telegram_secret_errado_retorna_403():
    os.environ["TELEGRAM_SECRET"] = "meu_secret"
    client = get_client()
    resp = client.post(
        "/telegram",
        json={"message": {"chat": {"id": 1}, "text": "/help"}},
        headers={"X-Telegram-Bot-Api-Secret-Token": "errado"},
    )
    assert resp.status_code == 403


def test_telegram_secret_correto_retorna_ok():
    os.environ["TELEGRAM_SECRET"] = "meu_secret"
    os.environ["TELEGRAM_CHAT_ID"] = "999"
    client = get_client()
    with patch("webhook.handlers.handle_dm"), \
         patch("webhook.telegram_handler.handle") as mock_handle:
        resp = client.post(
            "/telegram",
            json={"message": {"chat": {"id": 999}, "text": "/help"}},
            headers={"X-Telegram-Bot-Api-Secret-Token": "meu_secret"},
        )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    mock_handle.assert_called_once()
```

- [ ] **Step 2: Rodar para confirmar que falham**

```bash
cd content-engine && python -m pytest tests/webhook/test_server.py::test_telegram_sem_secret_retorna_403 -v
```

Esperado: FAIL com `404 Not Found` (endpoint não existe ainda)

- [ ] **Step 3: Adicionar endpoint ao server.py**

Substituir o conteúdo de `content-engine/webhook/server.py`:

```python
import os
from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
from webhook.signature import verify_signature
from webhook import handlers
from webhook import telegram_handler

load_dotenv()

app = FastAPI()

VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "")
APP_SECRET = os.getenv("META_APP_SECRET", "")
TELEGRAM_SECRET = os.getenv("TELEGRAM_SECRET", "")


@app.get("/webhook")
async def handshake(request: Request):
    params = dict(request.query_params)
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return PlainTextResponse(params.get("hub.challenge", ""))
    return Response(status_code=403)


@app.post("/webhook")
async def receive(request: Request):
    body = await request.body()
    sig = request.headers.get("x-hub-signature-256", "")

    if not verify_signature(body, sig, APP_SECRET):
        return Response(status_code=401)

    try:
        payload = await request.json()
    except Exception:
        return {"status": "ok"}

    for entry in payload.get("entry", []):
        for msg_event in entry.get("messaging", []):
            handlers.handle_dm(msg_event)

        for change in entry.get("changes", []):
            field = change.get("field")
            value = change.get("value", {})
            if field == "messages":
                handlers.handle_dm(value)
            elif field == "comments":
                handlers.handle_comment(value)

    return {"status": "ok"}


@app.post("/telegram")
async def telegram(request: Request):
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not TELEGRAM_SECRET or secret != TELEGRAM_SECRET:
        return Response(status_code=403)

    try:
        update = await request.json()
    except Exception:
        return {"ok": True}

    telegram_handler.handle(update)
    return {"ok": True}
```

- [ ] **Step 4: Rodar testes — devem passar**

```bash
cd content-engine && python -m pytest tests/webhook/test_server.py -v
```

Esperado: PASS em todos os testes (incluindo os novos)

- [ ] **Step 5: Commit**

```bash
git add content-engine/webhook/server.py content-engine/tests/webhook/test_server.py
git commit -m "feat: add /telegram endpoint with secret validation"
```

---

### Task 5: daily_post.yml — notificações e log de erros

**Files:**
- Modify: `.github/workflows/daily_post.yml`

Adicionar steps após cada evento: publicação, falha, dedup, comentário de votação. Também logar erros no `engagement_state.json` quando um step falha.

- [ ] **Step 1: Adicionar steps de notificação ao daily_post.yml**

Substituir o conteúdo de `.github/workflows/daily_post.yml` pelo arquivo completo abaixo:

```yaml
name: Daily Posts — Dra. Julga

on:
  schedule:
    - cron: '0 12 * * *'   # 09h BRT — manhã
    - cron: '0 15 * * *'   # 12h BRT — almoço (pico)
    - cron: '0 21 * * *'   # 18h BRT — saída do trabalho
    - cron: '0 23 * * *'   # 20h BRT — após jantar (prime time)
    - cron: '0 1  * * *'   # 22h BRT — scroll pré-sono
  workflow_dispatch:
    inputs:
      categoria:
        description: 'Categoria do post'
        required: false
        default: ''

concurrency:
  group: daily-post
  cancel-in-progress: false

env:
  META_ACCESS_TOKEN: ${{ secrets.META_ACCESS_TOKEN }}
  IG_ACCOUNT_ID: ${{ secrets.INSTAGRAM_ACCOUNT_ID }}
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
  TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}

jobs:
  publicar:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Instalar dependências
        run: pip install pillow anthropic python-dotenv requests

      - name: Definir categoria
        id: categoria
        run: |
          HORA=$(date -u +"%H" | sed 's/^0//')
          DIA=$(date -u +"%u")
          IDX=$(( (DIA - 1) % 7 ))

          MANUAL="${{ github.event.inputs.categoria }}"
          if [ -n "$MANUAL" ]; then
            echo "categoria=$MANUAL" >> $GITHUB_OUTPUT
            echo "Categoria (manual): $MANUAL"
            exit 0
          fi

          declare -a SLOT_A=("dinheiro"  "amor"      "trabalho"   "dopamina"   "vida_adulta" "social"     "saude_mental")
          declare -a SLOT_B=("amor"      "trabalho"  "dopamina"   "vida_adulta" "social"     "saude_mental" "dinheiro")
          declare -a SLOT_C=("trabalho"  "dopamina"  "vida_adulta" "social"    "saude_mental" "dinheiro"   "amor")
          declare -a SLOT_D=("dopamina"  "vida_adulta" "social"   "saude_mental" "dinheiro"  "amor"       "trabalho")
          declare -a SLOT_E=("vida_adulta" "social"  "saude_mental" "dinheiro" "amor"       "trabalho"   "dopamina")

          if   [ "$HORA" = "12" ]; then CATEGORIA="${SLOT_A[$IDX]}"
          elif [ "$HORA" = "15" ]; then CATEGORIA="${SLOT_B[$IDX]}"
          elif [ "$HORA" = "21" ]; then CATEGORIA="${SLOT_C[$IDX]}"
          elif [ "$HORA" = "23" ]; then CATEGORIA="${SLOT_D[$IDX]}"
          else                          CATEGORIA="${SLOT_E[$IDX]}"
          fi

          echo "categoria=$CATEGORIA" >> $GITHUB_OUTPUT
          echo "Categoria (slot ${HORA}h UTC): $CATEGORIA"

      - name: Verificar duplicata
        id: dedup
        run: |
          HOJE=$(date -u +"%Y-%m-%d")
          CHAVE="${HOJE}_${{ steps.categoria.outputs.categoria }}"
          STATE="content-engine/generated/engagement_state.json"

          if [ ! -f "$STATE" ]; then
            echo "skip=false" >> $GITHUB_OUTPUT
            exit 0
          fi

          JA_PUBLICADO=$(python3 -c "
import json
state_file = 'content-engine/generated/engagement_state.json'
with open(state_file) as f:
    state = json.load(f)
print('true' if '${CHAVE}' in state.get('posts_published', []) else 'false')
")
          echo "skip=$JA_PUBLICADO" >> $GITHUB_OUTPUT
          if [ "$JA_PUBLICADO" = "true" ]; then
            echo "⏭️  Post '$CHAVE' já publicado hoje — pulando."
          fi

      - name: Notificar post pulado
        if: steps.dedup.outputs.skip == 'true'
        run: |
          cd content-engine
          python -m notify send_post_skipped --categoria ${{ steps.categoria.outputs.categoria }}

      - name: Gerar roteiro
        if: steps.dedup.outputs.skip != 'true'
        run: cd content-engine && python generate_reels.py --categoria ${{ steps.categoria.outputs.categoria }} --sem_audio

      - name: Gerar slides do carrossel
        if: steps.dedup.outputs.skip != 'true'
        run: cd content-engine && python gerar_carrossel.py --categoria ${{ steps.categoria.outputs.categoria }}

      - name: Publicar carrossel no Instagram
        if: steps.dedup.outputs.skip != 'true'
        id: publicar
        run: |
          cd content-engine
          HORA=$(date -u +"%Hh%M")
          MEDIA_ID=$(python post_carrossel_instagram.py \
            --categoria ${{ steps.categoria.outputs.categoria }} \
            --output-id)
          echo "media_id=$MEDIA_ID" >> $GITHUB_OUTPUT
          echo "hora=$HORA" >> $GITHUB_OUTPUT

      - name: Notificar falha na publicação
        if: steps.dedup.outputs.skip != 'true' && failure() && steps.publicar.outcome == 'failure'
        run: |
          cd content-engine
          python3 -c "
import sys
sys.path.insert(0, '.')
from engagement.shared import state
state.log_error('post_carrossel', 'Falha no step de publicação')
"
          HORA=$(date -u +"%Hh%M")
          python -m notify send_post_failed \
            --categoria ${{ steps.categoria.outputs.categoria }} \
            --hora "${HORA}" \
            --erro "Falha ao publicar carrossel — verifique GitHub Actions"

      - name: Registrar post publicado
        if: steps.dedup.outputs.skip != 'true' && steps.publicar.outputs.media_id != ''
        run: |
          HOJE=$(date -u +"%Y-%m-%d")
          CHAVE="${HOJE}_${{ steps.categoria.outputs.categoria }}"
          python3 -c "
import json
state_file = 'content-engine/generated/engagement_state.json'
try:
    with open(state_file) as f:
        state = json.load(f)
except Exception:
    state = {}
published = state.setdefault('posts_published', [])
if '${CHAVE}' not in published:
    published.append('${CHAVE}')
with open(state_file, 'w') as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
print('Registrado: ${CHAVE}')
"

      - name: Notificar post publicado
        if: steps.dedup.outputs.skip != 'true' && steps.publicar.outputs.media_id != ''
        run: |
          cd content-engine
          TITULO=$(python3 -c "
import json, glob, os
from datetime import datetime
hoje = datetime.utcnow().strftime('%Y-%m-%d')
cat = '${{ steps.categoria.outputs.categoria }}'
pattern = f'generated/reels/{hoje}_{cat}_reels.json'
files = glob.glob(pattern)
if files:
    with open(files[0]) as f:
        d = json.load(f)
    print(d.get('titulo', cat))
else:
    print(cat)
")
          python -m notify send_post_published \
            --categoria ${{ steps.categoria.outputs.categoria }} \
            --titulo "$TITULO" \
            --hora "${{ steps.publicar.outputs.hora }}" \
            --media_id ${{ steps.publicar.outputs.media_id }}

      - name: Postar comentário de engajamento
        if: steps.dedup.outputs.skip != 'true' && steps.publicar.outputs.media_id != ''
        run: |
          cd content-engine
          python -m engagement.post_engagement \
            --media_id ${{ steps.publicar.outputs.media_id }} \
            --categoria ${{ steps.categoria.outputs.categoria }}

      - name: Notificar comentário de votação
        if: steps.dedup.outputs.skip != 'true' && steps.publicar.outputs.media_id != ''
        run: |
          cd content-engine
          python -m notify send_voting_comment --media_id ${{ steps.publicar.outputs.media_id }}

      - name: Commit do estado e slides gerados
        if: steps.dedup.outputs.skip != 'true'
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: post ${{ steps.categoria.outputs.categoria }} publicado [skip ci]"
          file_pattern: |
            content-engine/generated/engagement_state.json
            content-engine/generated/reels/
```

- [ ] **Step 2: Verificar sintaxe YAML**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/daily_post.yml'))" && echo "YAML OK"
```

Esperado: `YAML OK`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/daily_post.yml
git commit -m "feat: add Telegram notifications to daily_post.yml"
```

---

### Task 6: daily_report.yml — relatório diário às 22h BRT

**Files:**
- Create: `.github/workflows/daily_report.yml`

- [ ] **Step 1: Criar o workflow**

Criar `.github/workflows/daily_report.yml`:

```yaml
name: Relatório Diário — Dra. Julga

on:
  schedule:
    - cron: '0 1 * * *'   # 22h BRT
  workflow_dispatch:

env:
  TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
  TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}

jobs:
  relatorio:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Instalar dependências
        run: pip install python-dotenv requests

      - name: Enviar relatório diário
        run: |
          STATE="content-engine/generated/engagement_state.json"
          if [ ! -f "$STATE" ]; then
            echo "engagement_state.json não encontrado — pulando relatório"
            exit 0
          fi
          cd content-engine
          python -m notify send_daily_report --state-file "generated/engagement_state.json"
```

- [ ] **Step 2: Verificar sintaxe YAML**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/daily_report.yml'))" && echo "YAML OK"
```

Esperado: `YAML OK`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/daily_report.yml
git commit -m "feat: add daily_report.yml workflow for 22h BRT Telegram report"
```

---

### Task 7: preview_post.yml — gera preview sem postar

**Files:**
- Create: `.github/workflows/preview_post.yml`

Acionado pelo comando `/preview [cat]` via `/forcar_post` no telegram_handler. Gera roteiro + slides, commita, notifica via Telegram com o texto do roteiro (sem postar no Instagram).

- [ ] **Step 1: Criar o workflow**

Criar `.github/workflows/preview_post.yml`:

```yaml
name: Preview Post — Dra. Julga

on:
  workflow_dispatch:
    inputs:
      categoria:
        description: 'Categoria do preview'
        required: false
        default: 'amor'

permissions:
  contents: write

env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
  TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}

jobs:
  preview:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Instalar dependências
        run: pip install pillow anthropic python-dotenv requests

      - name: Gerar roteiro (sem áudio)
        run: |
          cd content-engine
          python generate_reels.py --categoria ${{ github.event.inputs.categoria }} --sem_audio

      - name: Gerar slides do carrossel
        run: |
          cd content-engine
          python gerar_carrossel.py --categoria ${{ github.event.inputs.categoria }}

      - name: Notificar preview gerado
        run: |
          cd content-engine
          TITULO=$(python3 -c "
import json, glob
from datetime import datetime
hoje = datetime.utcnow().strftime('%Y-%m-%d')
cat = '${{ github.event.inputs.categoria }}'
files = glob.glob(f'generated/reels/{hoje}_{cat}_reels.json')
if files:
    with open(files[0]) as f:
        d = json.load(f)
    print(d.get('titulo', cat))
else:
    print(cat)
")
          ROTEIRO=$(python3 -c "
import json, glob
from datetime import datetime
hoje = datetime.utcnow().strftime('%Y-%m-%d')
cat = '${{ github.event.inputs.categoria }}'
files = glob.glob(f'generated/reels/{hoje}_{cat}_reels.json')
if files:
    with open(files[0]) as f:
        d = json.load(f)
    cenas = d.get('cenas', [])
    linhas = [f\"Cena {c['numero']}: {c.get('texto_slide') or c['texto']}\" for c in cenas]
    print('\n'.join(linhas[:6]))
else:
    print('roteiro não encontrado')
")
          python -m notify send "👁️ *Preview gerado — ${{ github.event.inputs.categoria }}*

*$TITULO*

$ROTEIRO

_(slides commitados em generated/reels/)_"

      - name: Commit dos slides de preview
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "preview: ${{ github.event.inputs.categoria }} [skip ci]"
          file_pattern: |
            content-engine/generated/reels/
```

- [ ] **Step 2: Verificar sintaxe YAML**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/preview_post.yml'))" && echo "YAML OK"
```

Esperado: `YAML OK`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/preview_post.yml
git commit -m "feat: add preview_post.yml workflow triggered by /preview command"
```

---

### Task 8: Rodar todos os testes e push final

- [ ] **Step 1: Rodar suite completa de testes**

```bash
cd content-engine && python -m pytest tests/ -v
```

Esperado: PASS em todos os testes (incluindo os testes pré-existentes de state, server, handlers, etc.)

- [ ] **Step 2: Push para o GitHub**

```bash
git push origin main
```

- [ ] **Step 3: Registrar o webhook do Telegram (manual — pós-deploy Railway)**

Após o Railway fazer o deploy com as novas variáveis `TELEGRAM_SECRET` e `GITHUB_PAT`, abrir no navegador:

```
https://api.telegram.org/bot{SEU_TOKEN}/setWebhook?url=https://mejulga-system-production.up.railway.app/telegram&secret_token={TELEGRAM_SECRET}
```

Substituir `{SEU_TOKEN}` e `{TELEGRAM_SECRET}` pelos valores reais.

Resposta esperada: `{"ok":true,"result":true,"description":"Webhook was set"}`

- [ ] **Step 4: Testar o bot**

Enviar `/help` no Telegram para o bot. Deve responder com a lista de comandos em ~5 segundos.

---

## Self-Review

### Spec coverage
- ✅ `notify.py` com todas as 6 funções especificadas
- ✅ `telegram_handler.py` com os 10 comandos
- ✅ `POST /telegram` com validação de secret e chat_id
- ✅ `daily_post.yml` com steps de notificação após publicação, falha e dedup
- ✅ `daily_report.yml` cron 22h BRT
- ✅ `preview_post.yml` para comando `/preview`
- ✅ `errors` no state + `log_error()`
- ✅ Segurança: secret token + chat_id guard

### Pendências de setup manual (fora do código)
- Criar bot no BotFather *(usuário já fez)*
- Descobrir chat_id *(usuário já fez)*
- Adicionar secrets no GitHub e Railway *(usuário já fez)*
- Registrar webhook após deploy *(Task 8, Step 3)*
