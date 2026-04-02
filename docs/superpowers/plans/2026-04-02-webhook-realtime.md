# Webhook Real-Time Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar um servidor FastAPI no Railway que recebe webhooks da Meta e responde DMs e comentários em tempo real, substituindo os cron jobs de `reply_dms` e `reply_comments`.

**Architecture:** FastAPI em `content-engine/webhook/`, reutilizando `engagement.shared.meta_client`, `claude_client` e `state`. Dockerfile na raiz do repositório para deploy no Railway. Validação HMAC-SHA256 de cada requisição recebida da Meta.

**Tech Stack:** Python 3.11, FastAPI, uvicorn, Railway, Meta Graph API v19.0, Anthropic SDK

---

## File Structure

```
content-engine/
  webhook/
    __init__.py              ← vazio
    signature.py             ← verify_signature(payload, header, secret) -> bool
    handlers.py              ← handle_dm(value) e handle_comment(value)
    server.py                ← FastAPI app: GET /webhook + POST /webhook
  tests/
    webhook/
      __init__.py
      test_signature.py
      test_handlers.py
      test_server.py
Dockerfile                   ← raiz do repo
railway.json                 ← raiz do repo
.github/workflows/
  engagement.yml             ← remover jobs reply-comments e reply-dms
```

**Não modificar:** `engagement/reply_dms.py`, `engagement/reply_comments.py` (ficam como fallback CLI), `engagement/shared/*`.

---

### Task 1: Validação de assinatura HMAC

**Files:**
- Create: `content-engine/webhook/__init__.py`
- Create: `content-engine/webhook/signature.py`
- Create: `content-engine/tests/webhook/__init__.py`
- Create: `content-engine/tests/webhook/test_signature.py`

- [ ] **Step 1: Criar pastas e arquivos vazios**

```bash
mkdir -p content-engine/webhook
touch content-engine/webhook/__init__.py
mkdir -p content-engine/tests/webhook
touch content-engine/tests/webhook/__init__.py
```

- [ ] **Step 2: Escrever os testes**

Criar `content-engine/tests/webhook/test_signature.py`:

```python
import hashlib
import hmac
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from webhook.signature import verify_signature


def test_assinatura_valida():
    secret = "meu_segredo"
    payload = b'{"entry": []}'
    mac = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    header = f"sha256={mac}"
    assert verify_signature(payload, header, secret) is True


def test_assinatura_invalida():
    assert verify_signature(b"payload", "sha256=errado", "segredo") is False


def test_header_sem_prefixo_sha256():
    assert verify_signature(b"payload", "semprefix", "segredo") is False


def test_secret_vazio_retorna_true():
    # Sem APP_SECRET configurado, deixa passar (ambiente de dev)
    assert verify_signature(b"qualquer", "sha256=qualquer", "") is True
```

- [ ] **Step 3: Rodar testes para confirmar falha**

```bash
cd content-engine && python -m pytest tests/webhook/test_signature.py -v
```

Expected: `ImportError: cannot import name 'verify_signature' from 'webhook.signature'` ou `ModuleNotFoundError`

- [ ] **Step 4: Implementar `signature.py`**

Criar `content-engine/webhook/signature.py`:

```python
import hashlib
import hmac


def verify_signature(payload: bytes, header: str, app_secret: str) -> bool:
    """Valida assinatura HMAC-SHA256 enviada pela Meta no header X-Hub-Signature-256."""
    if not app_secret:
        return True  # Dev sem secret configurado
    if not header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        app_secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, header)
```

- [ ] **Step 5: Rodar testes para confirmar aprovação**

```bash
cd content-engine && python -m pytest tests/webhook/test_signature.py -v
```

Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add content-engine/webhook/__init__.py content-engine/webhook/signature.py \
        content-engine/tests/webhook/__init__.py content-engine/tests/webhook/test_signature.py
git commit -m "feat: webhook signature HMAC-SHA256 validation"
```

---

### Task 2: Handlers de DM e comentário

**Files:**
- Create: `content-engine/webhook/handlers.py`
- Create: `content-engine/tests/webhook/test_handlers.py`

- [ ] **Step 1: Escrever os testes**

Criar `content-engine/tests/webhook/test_handlers.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from unittest.mock import patch, MagicMock


ACCOUNT_ID = "123456"

BASE_STATE = {
    "comments_replied": [],
    "stories_reposted": [],
    "dms_replied": [],
    "following": {},
    "hashtag_report": {},
}


def test_handle_dm_responde_mensagem():
    from webhook.handlers import handle_dm
    value = {
        "sender": {"id": "999"},
        "message": {"text": "me julga!"},
    }
    with patch("engagement.shared.meta_client.post") as mock_post, \
         patch("engagement.shared.claude_client.generate", return_value="Diagnóstico: curioso crônico."), \
         patch("engagement.shared.state.load", return_value=dict(BASE_STATE)), \
         patch("engagement.shared.state.save"), \
         patch.dict(os.environ, {"INSTAGRAM_ACCOUNT_ID": ACCOUNT_ID}):
        handle_dm(value)
    mock_post.assert_called_once()
    args = mock_post.call_args
    assert args[0][0] == f"{ACCOUNT_ID}/messages"
    assert args[1]["data"]["recipient"]["id"] == "999"


def test_handle_dm_ignora_propria_conta():
    from webhook.handlers import handle_dm
    value = {
        "sender": {"id": ACCOUNT_ID},
        "message": {"text": "teste"},
    }
    with patch("engagement.shared.meta_client.post") as mock_post, \
         patch.dict(os.environ, {"INSTAGRAM_ACCOUNT_ID": ACCOUNT_ID}):
        handle_dm(value)
    mock_post.assert_not_called()


def test_handle_dm_ignora_texto_vazio():
    from webhook.handlers import handle_dm
    value = {"sender": {"id": "999"}, "message": {}}
    with patch("engagement.shared.meta_client.post") as mock_post, \
         patch.dict(os.environ, {"INSTAGRAM_ACCOUNT_ID": ACCOUNT_ID}):
        handle_dm(value)
    mock_post.assert_not_called()


def test_handle_dm_deduplica():
    from webhook.handlers import handle_dm
    value = {"sender": {"id": "999"}, "message": {"text": "oi"}}
    state = dict(BASE_STATE)
    state["dms_replied"] = ["999"]
    with patch("engagement.shared.meta_client.post") as mock_post, \
         patch("engagement.shared.state.load", return_value=state), \
         patch("engagement.shared.state.save"), \
         patch.dict(os.environ, {"INSTAGRAM_ACCOUNT_ID": ACCOUNT_ID}):
        handle_dm(value)
    mock_post.assert_not_called()


def test_handle_comment_responde():
    from webhook.handlers import handle_comment
    value = {
        "id": "comment_abc",
        "text": "adorei o post!",
        "from": {"id": "888"},
    }
    with patch("engagement.shared.meta_client.post") as mock_post, \
         patch("engagement.shared.claude_client.generate", return_value="Obrigada!"), \
         patch("engagement.shared.state.load", return_value=dict(BASE_STATE)), \
         patch("engagement.shared.state.save"), \
         patch.dict(os.environ, {"INSTAGRAM_ACCOUNT_ID": ACCOUNT_ID}):
        handle_comment(value)
    mock_post.assert_called_once()
    args = mock_post.call_args
    assert args[0][0] == "comment_abc/replies"


def test_handle_comment_ignora_propria_conta():
    from webhook.handlers import handle_comment
    value = {
        "id": "comment_abc",
        "text": "post meu",
        "from": {"id": ACCOUNT_ID},
    }
    with patch("engagement.shared.meta_client.post") as mock_post, \
         patch.dict(os.environ, {"INSTAGRAM_ACCOUNT_ID": ACCOUNT_ID}):
        handle_comment(value)
    mock_post.assert_not_called()


def test_handle_comment_deduplica():
    from webhook.handlers import handle_comment
    value = {"id": "comment_abc", "text": "oi", "from": {"id": "888"}}
    state = dict(BASE_STATE)
    state["comments_replied"] = ["comment_abc"]
    with patch("engagement.shared.meta_client.post") as mock_post, \
         patch("engagement.shared.state.load", return_value=state), \
         patch("engagement.shared.state.save"), \
         patch.dict(os.environ, {"INSTAGRAM_ACCOUNT_ID": ACCOUNT_ID}):
        handle_comment(value)
    mock_post.assert_not_called()
```

- [ ] **Step 2: Rodar testes para confirmar falha**

```bash
cd content-engine && python -m pytest tests/webhook/test_handlers.py -v
```

Expected: `ImportError: cannot import name 'handle_dm' from 'webhook.handlers'`

- [ ] **Step 3: Implementar `handlers.py`**

Criar `content-engine/webhook/handlers.py`:

```python
import os
from engagement.shared import meta_client, claude_client, state


def _account_id() -> str:
    return os.getenv("IG_ACCOUNT_ID") or os.getenv("INSTAGRAM_ACCOUNT_ID", "")


def handle_dm(value: dict) -> None:
    """Processa evento de DM recebida e responde como Dra. Julga."""
    sender_id = value.get("sender", {}).get("id", "")
    text = value.get("message", {}).get("text", "").strip()

    if not sender_id or not text:
        return
    if sender_id == _account_id():
        return

    st = state.load()
    if sender_id in st.get("dms_replied", []):
        return

    resposta = claude_client.generate(
        f'Um seguidor te mandou uma DM: "{text}"\n\n'
        "Responda como Dra. Julga de forma simpática e curta (máximo 3 frases). "
        "Inclua o link mejulga.com.br para o diagnóstico completo. "
        "Seja engraçada e convidativa. Responda APENAS com o texto da mensagem.",
        max_tokens=200,
    )

    meta_client.post(
        f"{_account_id()}/messages",
        data={"recipient": {"id": sender_id}, "message": {"text": resposta}},
    )
    print(f"  ✅ DM respondida para {sender_id}")

    replied = st.setdefault("dms_replied", [])
    if sender_id not in replied:
        replied.append(sender_id)
    state.save(st)


def handle_comment(value: dict) -> None:
    """Processa evento de comentário novo e responde como Dra. Julga."""
    comment_id = value.get("id", "")
    text = value.get("text", "").strip()
    from_id = value.get("from", {}).get("id", "")

    if not comment_id or not text:
        return
    if from_id == _account_id():
        return

    st = state.load()
    if comment_id in st.get("comments_replied", []):
        return

    resposta = claude_client.generate(
        f'Um seguidor comentou no seu post: "{text}"\n\n'
        "Responda de forma curta (máximo 2 frases, até 150 caracteres). "
        "Seja engraçada e acolhedora. Máximo 2 emojis. "
        "Se mencionar um local (consultório, clínica, etc), use SEMPRE 'Tribunal Me Julga'. "
        "Responda APENAS com o texto da resposta.",
        max_tokens=150,
    )

    meta_client.post(f"{comment_id}/replies", data={"message": resposta})
    print(f"  ✅ Comentário {comment_id} respondido")

    replied = st.setdefault("comments_replied", [])
    if comment_id not in replied:
        replied.append(comment_id)
    state.save(st)
```

- [ ] **Step 4: Rodar testes para confirmar aprovação**

```bash
cd content-engine && python -m pytest tests/webhook/test_handlers.py -v
```

Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add content-engine/webhook/handlers.py content-engine/tests/webhook/test_handlers.py
git commit -m "feat: webhook handlers for DM and comment events"
```

---

### Task 3: Servidor FastAPI

**Files:**
- Create: `content-engine/webhook/server.py`
- Create: `content-engine/tests/webhook/test_server.py`

Dependência: instalar FastAPI e httpx para testes.

```bash
pip install fastapi httpx
```

- [ ] **Step 1: Escrever os testes**

Criar `content-engine/tests/webhook/test_server.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import hashlib, hmac, json
from unittest.mock import patch
from fastapi.testclient import TestClient


os.environ.setdefault("INSTAGRAM_ACCOUNT_ID", "123456")
os.environ.setdefault("WEBHOOK_VERIFY_TOKEN", "token_teste")
os.environ.setdefault("META_APP_SECRET", "")


def get_client():
    from webhook.server import app
    return TestClient(app)


def test_handshake_valido():
    client = get_client()
    resp = client.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "token_teste",
        "hub.challenge": "challenge_abc",
    })
    assert resp.status_code == 200
    assert resp.text == "challenge_abc"


def test_handshake_token_errado():
    client = get_client()
    resp = client.get("/webhook", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "errado",
        "hub.challenge": "challenge_abc",
    })
    assert resp.status_code == 403


def test_post_webhook_retorna_ok():
    client = get_client()
    payload = json.dumps({"entry": []}).encode()
    resp = client.post(
        "/webhook",
        content=payload,
        headers={"content-type": "application/json", "x-hub-signature-256": "sha256=qualquer"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_post_webhook_chama_handle_dm():
    client = get_client()
    payload = {
        "entry": [{
            "changes": [{
                "field": "messages",
                "value": {
                    "sender": {"id": "999"},
                    "message": {"text": "oi"},
                },
            }]
        }]
    }
    raw = json.dumps(payload).encode()
    with patch("webhook.handlers.handle_dm") as mock_dm, \
         patch("webhook.handlers.handle_comment") as mock_comment:
        resp = client.post(
            "/webhook",
            content=raw,
            headers={"content-type": "application/json", "x-hub-signature-256": "sha256=qualquer"},
        )
    assert resp.status_code == 200
    mock_dm.assert_called_once()
    mock_comment.assert_not_called()


def test_post_webhook_chama_handle_comment():
    client = get_client()
    payload = {
        "entry": [{
            "changes": [{
                "field": "comments",
                "value": {"id": "cmt_1", "text": "top!", "from": {"id": "888"}},
            }]
        }]
    }
    raw = json.dumps(payload).encode()
    with patch("webhook.handlers.handle_dm") as mock_dm, \
         patch("webhook.handlers.handle_comment") as mock_comment:
        resp = client.post(
            "/webhook",
            content=raw,
            headers={"content-type": "application/json", "x-hub-signature-256": "sha256=qualquer"},
        )
    assert resp.status_code == 200
    mock_comment.assert_called_once()
    mock_dm.assert_not_called()
```

- [ ] **Step 2: Rodar testes para confirmar falha**

```bash
cd content-engine && python -m pytest tests/webhook/test_server.py -v
```

Expected: `ImportError: cannot import name 'app' from 'webhook.server'`

- [ ] **Step 3: Implementar `server.py`**

Criar `content-engine/webhook/server.py`:

```python
import os
from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
from webhook.signature import verify_signature
from webhook import handlers

load_dotenv()

app = FastAPI()

VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "")
APP_SECRET = os.getenv("META_APP_SECRET", "")


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
        for change in entry.get("changes", []):
            field = change.get("field")
            value = change.get("value", {})
            if field == "messages":
                handlers.handle_dm(value)
            elif field == "comments":
                handlers.handle_comment(value)

    return {"status": "ok"}
```

- [ ] **Step 4: Rodar testes para confirmar aprovação**

```bash
cd content-engine && python -m pytest tests/webhook/test_server.py -v
```

Expected: 5 passed

- [ ] **Step 5: Rodar todos os testes do webhook**

```bash
cd content-engine && python -m pytest tests/webhook/ -v
```

Expected: 16 passed (4 + 7 + 5)

- [ ] **Step 6: Commit**

```bash
git add content-engine/webhook/server.py content-engine/tests/webhook/test_server.py
git commit -m "feat: FastAPI webhook server for Meta Instagram events"
```

---

### Task 4: Dockerfile e railway.json

**Files:**
- Create: `Dockerfile` (raiz do repo)
- Create: `railway.json` (raiz do repo)

Sem testes unitários para esta task — validação é o deploy funcionar.

- [ ] **Step 1: Criar `Dockerfile`**

Na raiz do repositório, criar `Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY content-engine/ ./content-engine/
RUN pip install --no-cache-dir fastapi uvicorn anthropic requests python-dotenv
EXPOSE 8000
CMD ["uvicorn", "content-engine.webhook.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Criar `railway.json`**

Na raiz do repositório, criar `railway.json`:

```json
{
  "build": { "builder": "dockerfile" },
  "deploy": { "restartPolicyType": "ON_FAILURE" }
}
```

- [ ] **Step 3: Verificar build local (opcional)**

Se tiver Docker instalado:

```bash
docker build -t mejulga-webhook .
docker run -p 8000:8000 \
  -e META_ACCESS_TOKEN=fake \
  -e ANTHROPIC_API_KEY=fake \
  -e INSTAGRAM_ACCOUNT_ID=fake \
  -e WEBHOOK_VERIFY_TOKEN=teste \
  mejulga-webhook
```

Expected: servidor sobe em `http://localhost:8000`

- [ ] **Step 4: Commit**

```bash
git add Dockerfile railway.json
git commit -m "feat: Dockerfile e railway.json para deploy do webhook server"
```

---

### Task 5: Remover cron jobs substituídos do engagement.yml

**Files:**
- Modify: `.github/workflows/engagement.yml`

- [ ] **Step 1: Remover job `reply-comments` e job `reply-dms`**

Em `.github/workflows/engagement.yml`, remover os dois jobs inteiros (linhas do `reply-comments:` até o fim do bloco `reply-dms:`).

O arquivo deve ficar com apenas 4 jobs: `comment-growth`, `follow-unfollow`, `hashtag-intel`, e `repost-stories`.

O `workflow_dispatch` deve manter apenas as opções restantes:

```yaml
workflow_dispatch:
  inputs:
    script:
      description: 'Script para rodar manualmente'
      required: true
      default: 'comment_growth'
      type: choice
      options:
        - comment_growth
        - follow_unfollow
        - hashtag_intel
        - repost_stories
```

- [ ] **Step 2: Verificar que o YAML é válido**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/engagement.yml'))"
```

Expected: nenhum erro

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/engagement.yml
git commit -m "chore: remove reply-comments e reply-dms do engagement.yml (substituídos por webhook)"
```

---

### Task 6: Deploy no Railway e configuração da Meta

Esta task é de infraestrutura — sem código a escrever.

- [ ] **Step 1: Criar projeto no Railway**

1. Acesse [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
2. Selecione o repositório `mejulga-system`
3. Railway detecta o `Dockerfile` automaticamente

- [ ] **Step 2: Adicionar variáveis de ambiente no Railway**

Em **Variables**, adicionar:

| Nome | Valor |
|------|-------|
| `META_ACCESS_TOKEN` | (mesmo valor do GitHub Secret) |
| `ANTHROPIC_API_KEY` | (mesmo valor do GitHub Secret) |
| `INSTAGRAM_ACCOUNT_ID` | (ID numérico da conta IG) |
| `META_APP_SECRET` | (App Secret do app Meta — está em Meta for Developers → Configurações → Básico) |
| `WEBHOOK_VERIFY_TOKEN` | qualquer string que você escolher, ex: `drajulga_webhook_2026` |

- [ ] **Step 3: Aguardar deploy e copiar URL**

Aguardar o build terminar. Copiar a URL gerada (ex: `https://mejulga-webhook-production.up.railway.app`).

Testar handshake manualmente:

```
https://<sua-url>/webhook?hub.mode=subscribe&hub.verify_token=drajulga_webhook_2026&hub.challenge=ping
```

Expected: resposta `ping` em texto puro.

- [ ] **Step 4: Configurar webhook na Meta**

1. Meta for Developers → seu app → **Webhooks** → **Editar**
2. URL de callback: `https://<sua-url>/webhook`
3. Token de verificação: o valor de `WEBHOOK_VERIFY_TOKEN`
4. Clicar em **Verificar e salvar**
5. Após verificação, assinar os campos: `messages` e `comments`

- [ ] **Step 5: Confirmar funcionamento**

Enviar uma DM para `@dra.julga` a partir de outra conta. A resposta deve chegar em segundos.

- [ ] **Step 6: Push final**

```bash
git push
```

---

## Ordem de execução

Tasks 1 → 2 → 3 devem ser feitas em sequência (dependência de imports).
Tasks 4 e 5 são independentes entre si e podem ser feitas em qualquer ordem após a Task 3.
Task 6 requer Tasks 4 e 5 completas.
