# Webhook Real-Time — Dra. Julga

**Goal:** Substituir o polling de DMs e comentários por um servidor FastAPI no Railway que responde em tempo real via webhooks da Meta.

**Architecture:** FastAPI server em `content-engine/webhook/`, deployado no Railway via Dockerfile. Recebe eventos da Meta (`messages` e `comments`), gera respostas com Claude e envia via Graph API. Reutiliza `meta_client` e `claude_client` existentes.

**Tech Stack:** Python 3.11, FastAPI, uvicorn, Railway, Meta Graph API v19.0, Anthropic SDK

---

## Estrutura de arquivos

```
content-engine/
  webhook/
    __init__.py
    server.py       ← FastAPI app: GET /webhook (handshake) + POST /webhook (eventos)
    handlers.py     ← handle_dm() e handle_comment()
    signature.py    ← validação HMAC-SHA256 da assinatura X-Hub-Signature-256
Dockerfile          ← raiz do repo, expõe porta 8000, roda uvicorn
railway.json        ← { "build": { "builder": "dockerfile" } }
```

Os cron jobs `reply-comments` e `reply-dms` do `engagement.yml` serão removidos. Os demais jobs (`comment_growth`, `follow_unfollow`, `hashtag_intel`, `repost_stories`) permanecem inalterados.

---

## Endpoints

### `GET /webhook`

Verificação de handshake da Meta. Parâmetros query:
- `hub.mode` — deve ser `"subscribe"`
- `hub.verify_token` — deve bater com `WEBHOOK_VERIFY_TOKEN` (env var)
- `hub.challenge` — retornado como plain text se verificação passar

Retorna 403 se o token não bater.

### `POST /webhook`

Recebe todos os eventos. Antes de processar, valida a assinatura HMAC-SHA256 do header `X-Hub-Signature-256` usando `META_APP_SECRET`. Retorna 401 se inválida.

Identifica o tipo pelo campo `entry[*].changes[*].field`:
- `"messages"` → chama `handle_dm()`
- `"comments"` → chama `handle_comment()`
- outros campos → ignora silenciosamente

Sempre retorna `{"status": "ok"}` com HTTP 200 (Meta requer resposta rápida; processamento é síncrono mas leve).

---

## Handler: DM (`handle_dm`)

**Entrada:** objeto `change.value` do payload de `messages`

**Lógica:**
1. Extrai `sender_id` de `value.sender.id` e `text` de `value.message.text`
2. Se `sender_id == INSTAGRAM_ACCOUNT_ID` → ignora (evita loop)
3. Se `text` vazio ou ausente → ignora (sticker, áudio, etc.)
4. Carrega `engagement_state.json`; se `sender_id` já está em `dms_replied` → ignora (deduplicação)
5. Gera resposta com `claude_client.generate()` usando o prompt da Dra. Julga
6. Envia via `POST /{INSTAGRAM_ACCOUNT_ID}/messages` com `{"recipient": {"id": sender_id}, "message": {"text": resposta}}`
7. Adiciona `sender_id` a `dms_replied` e salva state

**Prompt para DMs:**
```
Um seguidor te mandou uma DM: "{texto}"

Responda como Dra. Julga de forma simpática e curta (máximo 3 frases).
Inclua o link mejulga.com.br para o diagnóstico completo.
Seja engraçada e convidativa. Responda APENAS com o texto da mensagem.
```

---

## Handler: Comentário (`handle_comment`)

**Entrada:** objeto `change.value` do payload de `comments`

**Lógica:**
1. Extrai `comment_id` de `value.id` e `text` de `value.text`
2. Se `value.from.id == INSTAGRAM_ACCOUNT_ID` → ignora (evita loop)
3. Carrega `engagement_state.json`; se `comment_id` já está em `comments_replied` → ignora
4. Gera resposta com `claude_client.generate()` usando o prompt da Dra. Julga
5. Envia via `POST /{comment_id}/replies` com `{"message": resposta}`
6. Adiciona `comment_id` a `comments_replied` e salva state

**Prompt para comentários:**
```
Um seguidor comentou no seu post: "{texto}"

Responda de forma curta (máximo 2 frases, até 150 caracteres).
Seja engraçada e acolhedora. Máximo 2 emojis.
Se mencionar um local (consultório, clínica, etc), use SEMPRE 'Tribunal Me Julga'.
Responda APENAS com o texto da resposta.
```

---

## Validação de assinatura (`signature.py`)

A Meta envia o header `X-Hub-Signature-256: sha256=<hash>`. Validação:

```python
import hashlib, hmac

def verify(payload_bytes: bytes, header: str, app_secret: str) -> bool:
    expected = "sha256=" + hmac.new(
        app_secret.encode(), payload_bytes, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, header)
```

Se `META_APP_SECRET` não estiver definido, logar aviso e deixar passar (facilita testes locais).

---

## Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY content-engine/ ./content-engine/
RUN pip install --no-cache-dir fastapi uvicorn anthropic requests python-dotenv
EXPOSE 8000
CMD ["uvicorn", "content-engine.webhook.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## railway.json

```json
{
  "build": { "builder": "dockerfile" },
  "deploy": { "restartPolicyType": "ON_FAILURE" }
}
```

---

## Variáveis de ambiente no Railway

| Variável | Descrição |
|----------|-----------|
| `META_ACCESS_TOKEN` | Token de acesso da Meta (mesmo do GitHub) |
| `ANTHROPIC_API_KEY` | Chave da API Anthropic |
| `INSTAGRAM_ACCOUNT_ID` | ID numérico da conta Instagram |
| `META_APP_SECRET` | App Secret do app Meta (para validar HMAC) |
| `WEBHOOK_VERIFY_TOKEN` | Token de verificação escolhido por você (ex: `drajulga_webhook_2026`) |

---

## Configuração na Meta (pós-deploy)

1. Copiar URL pública do Railway (ex: `https://mejulga.up.railway.app`)
2. Meta for Developers → app → Webhooks → **Editar** → inserir URL + `WEBHOOK_VERIFY_TOKEN`
3. Assinar os campos: `messages` e `comments`
4. Salvar e confirmar que o handshake (`GET /webhook`) passou com status 200

---

## Mudanças no engagement.yml

Remover os jobs `reply-comments` e `reply-dms`. Os 4 jobs restantes não são alterados.
