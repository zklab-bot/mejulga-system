# Engagement Bot — Dra. Julga — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir sistema de engajamento automático para @dra.julga com 7 scripts independentes: reply comments, repost stories, engagement comment, reply DMs, comment growth, follow/unfollow e hashtag intelligence.

**Architecture:** Scripts independentes em `content-engine/engagement/`, cada um importando de `engagement/shared/` (meta_client, claude_client, state). Estado persistido em `engagement_state.json` commitado ao repo após cada execução. Orchestração via GitHub Actions (`engagement.yml`) com jobs separados por schedule.

**Tech Stack:** Python 3.11, Meta Graph API v19.0, Anthropic SDK (claude-sonnet-4-6), instagrapi (follow/unfollow), pytest, requests, python-dotenv.

---

## File Map

**Criar:**
- `content-engine/engagement/__init__.py`
- `content-engine/engagement/shared/__init__.py`
- `content-engine/engagement/shared/state.py`
- `content-engine/engagement/shared/meta_client.py`
- `content-engine/engagement/shared/claude_client.py`
- `content-engine/engagement/post_engagement.py`
- `content-engine/engagement/reply_comments.py`
- `content-engine/engagement/repost_stories.py`
- `content-engine/engagement/reply_dms.py`
- `content-engine/engagement/comment_growth.py`
- `content-engine/engagement/follow_unfollow.py`
- `content-engine/engagement/hashtag_intel.py`
- `content-engine/tests/__init__.py`
- `content-engine/tests/engagement/__init__.py`
- `content-engine/tests/engagement/test_state.py`
- `content-engine/tests/engagement/test_meta_client.py`
- `content-engine/tests/engagement/test_post_engagement.py`
- `content-engine/tests/engagement/test_reply_comments.py`
- `content-engine/tests/engagement/test_reply_dms.py`
- `content-engine/tests/engagement/test_hashtag_intel.py`
- `content-engine/tests/engagement/test_follow_unfollow.py`
- `.github/workflows/engagement.yml`

**Modificar:**
- `.github/workflows/daily_post.yml` — exportar `media_id` + chamar `post_engagement.py`

---

## Task 1: Package structure + shared/state.py

**Files:**
- Create: `content-engine/engagement/__init__.py`
- Create: `content-engine/engagement/shared/__init__.py`
- Create: `content-engine/engagement/shared/state.py`
- Create: `content-engine/tests/__init__.py`
- Create: `content-engine/tests/engagement/__init__.py`
- Create: `content-engine/tests/engagement/test_state.py`

- [ ] **Step 1: Criar estrutura de pastas e arquivos vazios**

```bash
cd content-engine
mkdir -p engagement/shared tests/engagement
touch engagement/__init__.py engagement/shared/__init__.py
touch tests/__init__.py tests/engagement/__init__.py
```

- [ ] **Step 2: Escrever o teste para state.py**

`content-engine/tests/engagement/test_state.py`:
```python
import json
import pytest
from pathlib import Path


def test_load_retorna_default_quando_arquivo_nao_existe(tmp_path, monkeypatch):
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    result = state.load()
    assert result["comments_replied"] == []
    assert result["stories_reposted"] == []
    assert result["dms_replied"] == []
    assert result["following"] == {}
    assert result["hashtag_report"] == {}


def test_save_e_load_roundtrip(tmp_path, monkeypatch):
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    data = {
        "comments_replied": ["abc123"],
        "stories_reposted": [],
        "dms_replied": ["dm1"],
        "following": {"user1": "2026-04-01T10:00:00"},
        "hashtag_report": {"ranking": []},
    }
    state.save(data)
    result = state.load()
    assert result == data


def test_load_cria_pasta_se_nao_existir(tmp_path, monkeypatch):
    import engagement.shared.state as state
    pasta = tmp_path / "sub" / "pasta"
    monkeypatch.setattr(state, "STATE_FILE", pasta / "state.json")
    result = state.load()
    assert result["comments_replied"] == []
```

- [ ] **Step 3: Rodar testes para confirmar que falham**

```bash
cd content-engine
python -m pytest tests/engagement/test_state.py -v
```
Esperado: `ModuleNotFoundError: No module named 'engagement'`

- [ ] **Step 4: Implementar state.py**

`content-engine/engagement/shared/state.py`:
```python
import json
from pathlib import Path

STATE_FILE = Path(__file__).parent.parent.parent / "generated" / "engagement_state.json"

DEFAULT_STATE: dict = {
    "comments_replied": [],
    "stories_reposted": [],
    "dms_replied": [],
    "following": {},
    "hashtag_report": {},
}


def load() -> dict:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.exists():
        return {k: (v.copy() if isinstance(v, (list, dict)) else v)
                for k, v in DEFAULT_STATE.items()}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
```

- [ ] **Step 5: Rodar testes para confirmar que passam**

```bash
cd content-engine
python -m pytest tests/engagement/test_state.py -v
```
Esperado: 3 testes `PASSED`

- [ ] **Step 6: Commit**

```bash
cd content-engine
git add engagement/__init__.py engagement/shared/__init__.py engagement/shared/state.py \
        tests/__init__.py tests/engagement/__init__.py tests/engagement/test_state.py
git commit -m "feat: engagement package + shared/state.py com testes"
```

---

## Task 2: shared/meta_client.py

**Files:**
- Create: `content-engine/engagement/shared/meta_client.py`
- Create: `content-engine/tests/engagement/test_meta_client.py`

- [ ] **Step 1: Escrever testes para meta_client.py**

`content-engine/tests/engagement/test_meta_client.py`:
```python
import pytest
from unittest.mock import patch, Mock


def make_mock_response(json_data, status_code=200):
    mock = Mock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    return mock


def test_get_sucesso():
    import engagement.shared.meta_client as meta_client
    with patch("requests.request") as mock_req:
        mock_req.return_value = make_mock_response({"data": [{"id": "1"}]})
        result = meta_client.get("me/media")
    assert result == {"data": [{"id": "1"}]}


def test_get_rate_limit_levanta_excecao():
    import engagement.shared.meta_client as meta_client
    with patch("requests.request") as mock_req:
        mock_req.return_value = make_mock_response(
            {"error": {"code": 32, "message": "Rate limited"}}, status_code=400
        )
        with pytest.raises(meta_client.MetaRateLimitError):
            meta_client.get("me/media")


def test_get_permissao_negada_levanta_excecao():
    import engagement.shared.meta_client as meta_client
    with patch("requests.request") as mock_req:
        mock_req.return_value = make_mock_response(
            {"error": {"code": 10, "message": "Permission denied"}}, status_code=400
        )
        with pytest.raises(meta_client.MetaPermissionError):
            meta_client.get("me/media")


def test_get_permissao_200_levanta_excecao():
    import engagement.shared.meta_client as meta_client
    with patch("requests.request") as mock_req:
        mock_req.return_value = make_mock_response(
            {"error": {"code": 200, "message": "Not approved"}}, status_code=400
        )
        with pytest.raises(meta_client.MetaPermissionError):
            meta_client.get("me/media")


def test_post_sucesso():
    import engagement.shared.meta_client as meta_client
    with patch("requests.request") as mock_req:
        mock_req.return_value = make_mock_response({"id": "comment_123"})
        result = meta_client.post("media_id/comments", data={"message": "oi"})
    assert result["id"] == "comment_123"
```

- [ ] **Step 2: Rodar testes para confirmar que falham**

```bash
cd content-engine
python -m pytest tests/engagement/test_meta_client.py -v
```
Esperado: `ImportError` ou `ModuleNotFoundError`

- [ ] **Step 3: Implementar meta_client.py**

`content-engine/engagement/shared/meta_client.py`:
```python
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://graph.facebook.com/v19.0"
_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
MAX_RETRIES = 3
BACKOFF_BASE = 2


class MetaAPIError(Exception):
    pass


class MetaPermissionError(MetaAPIError):
    pass


class MetaRateLimitError(MetaAPIError):
    pass


def _request(method: str, endpoint: str, params: dict = None, data: dict = None) -> dict:
    url = f"{BASE_URL}/{endpoint}"
    p = dict(params or {})
    p["access_token"] = os.getenv("META_ACCESS_TOKEN") or _ACCESS_TOKEN

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.request(method, url, params=p, data=data, timeout=30)
            body = resp.json()

            if resp.status_code == 200:
                return body

            error = body.get("error", {})
            code = error.get("code")

            if code == 32:
                raise MetaRateLimitError(
                    f"Rate limit atingido: {error.get('message')}"
                )
            if code in (10, 200):
                raise MetaPermissionError(
                    f"Permissão negada (code={code}). "
                    f"Verifique o App Review da Meta. Mensagem: {error.get('message')}"
                )

            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF_BASE ** attempt)
                continue

            raise MetaAPIError(f"Erro {resp.status_code}: {body}")

        except (MetaRateLimitError, MetaPermissionError):
            raise
        except MetaAPIError:
            if attempt == MAX_RETRIES - 1:
                raise
        except requests.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                raise MetaAPIError(f"Erro de rede: {e}") from e
            time.sleep(BACKOFF_BASE ** attempt)

    raise MetaAPIError("Máximo de tentativas atingido")


def get(endpoint: str, params: dict = None) -> dict:
    return _request("GET", endpoint, params=params)


def post(endpoint: str, data: dict = None) -> dict:
    return _request("POST", endpoint, data=data)
```

- [ ] **Step 4: Rodar testes para confirmar que passam**

```bash
cd content-engine
python -m pytest tests/engagement/test_meta_client.py -v
```
Esperado: 5 testes `PASSED`

- [ ] **Step 5: Commit**

```bash
git add content-engine/engagement/shared/meta_client.py \
        content-engine/tests/engagement/test_meta_client.py
git commit -m "feat: shared/meta_client.py com retry e tratamento de erros Meta API"
```

---

## Task 3: shared/claude_client.py

**Files:**
- Create: `content-engine/engagement/shared/claude_client.py`

> Nota: sem testes unitários para o Claude client pois ele só faz proxy para a API externa. O comportamento é testado indiretamente nos testes de integração de cada script.

- [ ] **Step 1: Implementar claude_client.py**

`content-engine/engagement/shared/claude_client.py`:
```python
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """Você é a Dra. Julga, psicóloga fictícia e humorística brasileira especialista em julgar comportamentos de forma cômica e divertida.
Tom: humor, ironia leve, diagnósticos psicológicos fictícios.
Escreva sempre em português brasileiro informal.
Nunca ataque pessoas específicas — só o comportamento.
Seja espontânea e divertida, nunca robótica ou genérica."""


def generate(prompt: str, max_tokens: int = 300) -> str:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()
```

- [ ] **Step 2: Commit**

```bash
git add content-engine/engagement/shared/claude_client.py
git commit -m "feat: shared/claude_client.py com system prompt da Dra. Julga"
```

---

## Task 4: post_engagement.py + integração com daily_post.yml

**Files:**
- Create: `content-engine/engagement/post_engagement.py`
- Create: `content-engine/tests/engagement/test_post_engagement.py`
- Modify: `.github/workflows/daily_post.yml`

- [ ] **Step 1: Escrever testes para post_engagement.py**

`content-engine/tests/engagement/test_post_engagement.py`:
```python
import pytest
from unittest.mock import patch


def test_gerar_comentario_amor():
    from engagement.post_engagement import gerar_comentario_votacao
    texto = gerar_comentario_votacao("amor")
    assert "🔴" in texto
    assert "🟢" in texto


def test_gerar_comentario_dinheiro():
    from engagement.post_engagement import gerar_comentario_votacao
    texto = gerar_comentario_votacao("dinheiro")
    assert "🔴" in texto
    assert "🟢" in texto


def test_gerar_comentario_categoria_desconhecida():
    from engagement.post_engagement import gerar_comentario_votacao
    texto = gerar_comentario_votacao("categoria_inexistente")
    assert "🔴" in texto
    assert "🟢" in texto


def test_postar_comentario_dry_run(capsys):
    from engagement.post_engagement import postar_comentario
    postar_comentario("media_123", "Teste 🔴 / 🟢", dry_run=True)
    out = capsys.readouterr().out
    assert "DRY RUN" in out
    assert "media_123" in out


def test_postar_comentario_real():
    from engagement.post_engagement import postar_comentario
    with patch("engagement.shared.meta_client.post") as mock_post:
        mock_post.return_value = {"id": "comment_999"}
        postar_comentario("media_123", "Votação 🔴 / 🟢", dry_run=False)
    mock_post.assert_called_once_with(
        "media_123/comments", data={"message": "Votação 🔴 / 🟢"}
    )
```

- [ ] **Step 2: Rodar testes para confirmar que falham**

```bash
cd content-engine
python -m pytest tests/engagement/test_post_engagement.py -v
```
Esperado: `ImportError`

- [ ] **Step 3: Implementar post_engagement.py**

`content-engine/engagement/post_engagement.py`:
```python
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
```

- [ ] **Step 4: Rodar testes para confirmar que passam**

```bash
cd content-engine
python -m pytest tests/engagement/test_post_engagement.py -v
```
Esperado: 5 testes `PASSED`

- [ ] **Step 5: Modificar daily_post.yml para exportar media_id e chamar post_engagement.py**

No arquivo `.github/workflows/daily_post.yml`, substituir o step `Publicar carrossel no Instagram` e adicionar o step de engajamento:

```yaml
      - name: Publicar carrossel no Instagram
        id: publicar
        run: |
          cd content-engine
          MEDIA_ID=$(python post_carrossel_instagram.py \
            --categoria ${{ steps.categoria.outputs.categoria }} \
            --output-id)
          echo "media_id=$MEDIA_ID" >> $GITHUB_OUTPUT
        env:
          META_ACCESS_TOKEN: ${{ secrets.META_ACCESS_TOKEN }}
          IG_ACCOUNT_ID: ${{ secrets.INSTAGRAM_ACCOUNT_ID }}

      - name: Postar comentário de engajamento
        run: |
          cd content-engine
          python -m engagement.post_engagement \
            --media_id ${{ steps.publicar.outputs.media_id }} \
            --categoria ${{ steps.categoria.outputs.categoria }}
        env:
          META_ACCESS_TOKEN: ${{ secrets.META_ACCESS_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          IG_ACCOUNT_ID: ${{ secrets.INSTAGRAM_ACCOUNT_ID }}
```

- [ ] **Step 6: Modificar post_carrossel_instagram.py para suportar --output-id**

Adicionar ao `main()` em `content-engine/post_carrossel_instagram.py`:

```python
    # No parser, adicionar:
    parser.add_argument("--output-id", action="store_true",
                        help="Imprime apenas o media_id (para captura no GitHub Actions)")
    
    # No final do main(), antes do print de sucesso:
    if args.output_id:
        print(media_id)  # única linha impressa — capturada pelo $()
        return
```

- [ ] **Step 7: Commit**

```bash
git add content-engine/engagement/post_engagement.py \
        content-engine/tests/engagement/test_post_engagement.py \
        content-engine/post_carrossel_instagram.py \
        .github/workflows/daily_post.yml
git commit -m "feat: post_engagement.py + integração com daily_post.yml"
```

---

## Task 5: reply_comments.py

**Files:**
- Create: `content-engine/engagement/reply_comments.py`
- Create: `content-engine/tests/engagement/test_reply_comments.py`

- [ ] **Step 1: Escrever testes para reply_comments.py**

`content-engine/tests/engagement/test_reply_comments.py`:
```python
from unittest.mock import patch, MagicMock


def test_ja_respondido_e_ignorado(capsys):
    from engagement.reply_comments import executar
    with patch("engagement.shared.meta_client.get") as mock_get, \
         patch("engagement.shared.state.load") as mock_load, \
         patch("engagement.shared.state.save"):
        mock_load.return_value = {
            "comments_replied": ["comment_111"],
            "stories_reposted": [], "dms_replied": [],
            "following": {}, "hashtag_report": {},
        }
        mock_get.side_effect = [
            {"data": [{"id": "post_1"}]},
            {"data": [{"id": "comment_111", "text": "oi", "replies": {"data": []}}]},
        ]
        executar(dry_run=True)
    out = capsys.readouterr().out
    assert "0 resposta" in out


def test_comentario_sem_replies_e_respondido(capsys):
    from engagement.reply_comments import executar
    with patch("engagement.shared.meta_client.get") as mock_get, \
         patch("engagement.shared.meta_client.post") as mock_post, \
         patch("engagement.shared.claude_client.generate", return_value="Diagnóstico confirmado! — Dra. Julga"), \
         patch("engagement.shared.state.load") as mock_load, \
         patch("engagement.shared.state.save"):
        mock_load.return_value = {
            "comments_replied": [],
            "stories_reposted": [], "dms_replied": [],
            "following": {}, "hashtag_report": {},
        }
        mock_get.side_effect = [
            {"data": [{"id": "post_1"}]},
            {"data": [{"id": "comment_222", "text": "me sinto assim também!", "replies": {"data": []}}]},
        ]
        mock_post.return_value = {"id": "reply_333"}
        executar(dry_run=False)
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[0][0] == "comment_222/replies"


def test_dry_run_nao_posta(capsys):
    from engagement.reply_comments import executar
    with patch("engagement.shared.meta_client.get") as mock_get, \
         patch("engagement.shared.meta_client.post") as mock_post, \
         patch("engagement.shared.claude_client.generate", return_value="Resposta"), \
         patch("engagement.shared.state.load") as mock_load, \
         patch("engagement.shared.state.save"):
        mock_load.return_value = {
            "comments_replied": [], "stories_reposted": [],
            "dms_replied": [], "following": {}, "hashtag_report": {},
        }
        mock_get.side_effect = [
            {"data": [{"id": "post_1"}]},
            {"data": [{"id": "comment_444", "text": "adorei!", "replies": {"data": []}}]},
        ]
        executar(dry_run=True)
    mock_post.assert_not_called()
```

- [ ] **Step 2: Rodar testes para confirmar que falham**

```bash
cd content-engine
python -m pytest tests/engagement/test_reply_comments.py -v
```
Esperado: `ImportError`

- [ ] **Step 3: Implementar reply_comments.py**

`content-engine/engagement/reply_comments.py`:
```python
"""
reply_comments.py
Responde comentários novos nos posts do @dra.julga.

Uso:
  python -m engagement.reply_comments
  python -m engagement.reply_comments --dry-run
"""
import argparse
import os
from datetime import datetime
from engagement.shared import meta_client, claude_client, state

MAX_REPLIES_PER_RUN = 10


def _account_id() -> str:
    return os.getenv("IG_ACCOUNT_ID") or os.getenv("INSTAGRAM_ACCOUNT_ID", "")


def _buscar_posts() -> list:
    data = meta_client.get(
        f"{_account_id()}/media",
        params={"fields": "id,caption,timestamp", "limit": "10"},
    )
    return data.get("data", [])


def _buscar_comentarios(media_id: str) -> list:
    data = meta_client.get(
        f"{media_id}/comments",
        params={"fields": "id,text,timestamp,replies{id}", "limit": "50"},
    )
    return data.get("data", [])


def _gerar_resposta(texto: str) -> str:
    return claude_client.generate(
        f'Um seguidor comentou no seu post: "{texto}"\n\n'
        "Responda de forma curta (máximo 2 frases, até 150 caracteres). "
        "Seja engraçada e acolhedora. Máximo 2 emojis. "
        "Responda APENAS com o texto da resposta.",
        max_tokens=150,
    )


def executar(dry_run: bool = False) -> None:
    print(f"\n💬 Reply Comments — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st = state.load()
    replied = set(st.get("comments_replied", []))
    total = 0

    for post in _buscar_posts():
        if total >= MAX_REPLIES_PER_RUN:
            break
        for comentario in _buscar_comentarios(post["id"]):
            if total >= MAX_REPLIES_PER_RUN:
                break
            cid = comentario["id"]
            texto = comentario.get("text", "").strip()
            if not texto or cid in replied:
                continue
            if comentario.get("replies", {}).get("data"):
                continue  # já tem reply

            print(f"  💬 {texto[:60]}...")
            resposta = _gerar_resposta(texto)
            print(f"  🤖 {resposta}")

            if dry_run:
                print(f"  [DRY RUN] Responderia comentário {cid}")
            else:
                result = meta_client.post(f"{cid}/replies", data={"message": resposta})
                print(f"  ✅ Resposta postada! id={result.get('id')}")

            replied.add(cid)
            total += 1

    st["comments_replied"] = list(replied)
    state.save(st)
    print(f"\n✅ {total} resposta(s) postada(s)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    executar(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Rodar testes para confirmar que passam**

```bash
cd content-engine
python -m pytest tests/engagement/test_reply_comments.py -v
```
Esperado: 3 testes `PASSED`

- [ ] **Step 5: Commit**

```bash
git add content-engine/engagement/reply_comments.py \
        content-engine/tests/engagement/test_reply_comments.py
git commit -m "feat: reply_comments.py — responde comentários nos posts da Dra. Julga"
```

---

## Task 6: repost_stories.py

**Files:**
- Create: `content-engine/engagement/repost_stories.py`

> Nota: repost_stories usa `GET /{ig-user-id}/tags` (menções em feed e stories). A Meta API não oferece endpoint de polling para menções exclusivamente em stories sem webhooks — o script reposta qualquer mídia onde @dra.julga for mencionada. Testes de integração cobertos manualmente via `--dry-run`.

- [ ] **Step 1: Implementar repost_stories.py**

`content-engine/engagement/repost_stories.py`:
```python
"""
repost_stories.py
Detecta menções a @dra.julga e reposta como story.

Nota: usa GET /{ig-user-id}/tags para menções em feed e stories.
Menções exclusivas de stories requerem webhook (não disponível neste setup).

Uso:
  python -m engagement.repost_stories
  python -m engagement.repost_stories --dry-run
"""
import argparse
import os
from datetime import datetime
from engagement.shared import meta_client, state

MAX_REPOSTS_PER_RUN = 5


def _account_id() -> str:
    return os.getenv("IG_ACCOUNT_ID") or os.getenv("INSTAGRAM_ACCOUNT_ID", "")


def _buscar_mencoes() -> list:
    data = meta_client.get(
        f"{_account_id()}/tags",
        params={"fields": "id,media_type,timestamp,media_url", "limit": "20"},
    )
    return data.get("data", [])


def _buscar_media_url(media_id: str) -> str:
    data = meta_client.get(media_id, params={"fields": "media_url,media_type"})
    return data.get("media_url", "")


def _repostar(media_url: str, source_id: str, dry_run: bool) -> bool:
    account_id = _account_id()
    if dry_run:
        print(f"  [DRY RUN] Repostaria menção {source_id}: {media_url}")
        return True

    container = meta_client.post(
        f"{account_id}/media",
        data={"media_type": "STORIES", "image_url": media_url},
    )
    container_id = container.get("id")
    if not container_id:
        print(f"  ❌ Falha ao criar container para {source_id}")
        return False

    result = meta_client.post(
        f"{account_id}/media_publish",
        data={"creation_id": container_id},
    )
    print(f"  ✅ Story repostado! id={result.get('id')}")
    return True


def executar(dry_run: bool = False) -> None:
    print(f"\n📲 Repost Stories — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st = state.load()
    repostados = set(st.get("stories_reposted", []))
    total = 0

    mencoes = _buscar_mencoes()
    print(f"  📌 {len(mencoes)} menção(ões) encontrada(s)")

    for mencao in mencoes:
        if total >= MAX_REPOSTS_PER_RUN:
            break
        mid = mencao["id"]
        if mid in repostados:
            continue

        media_url = mencao.get("media_url") or _buscar_media_url(mid)
        if not media_url:
            print(f"  ⚠️  URL não encontrada para {mid}")
            continue

        print(f"  🔄 Repostando {mid}...")
        if _repostar(media_url, mid, dry_run):
            repostados.add(mid)
            total += 1

    st["stories_reposted"] = list(repostados)
    state.save(st)
    print(f"\n✅ {total} story(ies) repostado(s)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    executar(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Testar manualmente com dry-run**

```bash
cd content-engine
META_ACCESS_TOKEN=xxx INSTAGRAM_ACCOUNT_ID=yyy python -m engagement.repost_stories --dry-run
```
Esperado: lista menções ou `0 story(ies) repostado(s)`

- [ ] **Step 3: Commit**

```bash
git add content-engine/engagement/repost_stories.py
git commit -m "feat: repost_stories.py — reposta menções a @dra.julga"
```

---

## Task 7: reply_dms.py

**Files:**
- Create: `content-engine/engagement/reply_dms.py`
- Create: `content-engine/tests/engagement/test_reply_dms.py`

- [ ] **Step 1: Escrever testes para reply_dms.py**

`content-engine/tests/engagement/test_reply_dms.py`:
```python
def test_contem_keyword_verdadeiro():
    from engagement.reply_dms import _contem_keyword
    assert _contem_keyword("me julga por favor")
    assert _contem_keyword("quero meu diagnóstico")
    assert _contem_keyword("como funciona o mejulga")
    assert _contem_keyword("Me Julga!")  # case insensitive


def test_contem_keyword_falso():
    from engagement.reply_dms import _contem_keyword
    assert not _contem_keyword("oi tudo bem")
    assert not _contem_keyword("adorei o post")
    assert not _contem_keyword("")


def test_dry_run_nao_envia(capsys):
    from engagement.reply_dms import executar
    from unittest.mock import patch

    with patch("engagement.shared.meta_client.get") as mock_get, \
         patch("engagement.shared.meta_client.post") as mock_post, \
         patch("engagement.shared.claude_client.generate", return_value="Olá! mejulga.com.br"), \
         patch("engagement.shared.state.load") as mock_load, \
         patch("engagement.shared.state.save"):
        mock_load.return_value = {
            "comments_replied": [], "stories_reposted": [],
            "dms_replied": [], "following": {}, "hashtag_report": {},
        }
        mock_get.return_value = {
            "data": [{
                "id": "conv_1",
                "messages": {"data": [{"id": "msg_1", "message": "me julga!", "from": {"id": "user_99"}}]},
            }]
        }
        executar(dry_run=True)
    mock_post.assert_not_called()


def test_sem_keyword_nao_responde():
    from engagement.reply_dms import executar
    from unittest.mock import patch

    with patch("engagement.shared.meta_client.get") as mock_get, \
         patch("engagement.shared.meta_client.post") as mock_post, \
         patch("engagement.shared.state.load") as mock_load, \
         patch("engagement.shared.state.save"):
        mock_load.return_value = {
            "comments_replied": [], "stories_reposted": [],
            "dms_replied": [], "following": {}, "hashtag_report": {},
        }
        mock_get.return_value = {
            "data": [{
                "id": "conv_2",
                "messages": {"data": [{"id": "msg_2", "message": "oi tudo bem?", "from": {"id": "user_88"}}]},
            }]
        }
        executar(dry_run=False)
    mock_post.assert_not_called()
```

- [ ] **Step 2: Rodar testes para confirmar que falham**

```bash
cd content-engine
python -m pytest tests/engagement/test_reply_dms.py -v
```
Esperado: `ImportError`

- [ ] **Step 3: Implementar reply_dms.py**

`content-engine/engagement/reply_dms.py`:
```python
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
```

- [ ] **Step 4: Rodar testes para confirmar que passam**

```bash
cd content-engine
python -m pytest tests/engagement/test_reply_dms.py -v
```
Esperado: 4 testes `PASSED`

- [ ] **Step 5: Commit**

```bash
git add content-engine/engagement/reply_dms.py \
        content-engine/tests/engagement/test_reply_dms.py
git commit -m "feat: reply_dms.py — responde DMs com palavras-chave"
```

---

## Task 8: comment_growth.py (migração)

**Files:**
- Create: `content-engine/engagement/comment_growth.py`

- [ ] **Step 1: Implementar comment_growth.py**

`content-engine/engagement/comment_growth.py`:
```python
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
```

- [ ] **Step 2: Testar manualmente com dry-run**

```bash
cd content-engine
python -m engagement.comment_growth --dry-run
```
Esperado: `⚠️  PAGINAS_ALVO vazia.` (até preencher a lista)

- [ ] **Step 3: Commit**

```bash
git add content-engine/engagement/comment_growth.py
git commit -m "feat: comment_growth.py — comenta em páginas alvo (migração de instagram_comentarios.py)"
```

---

## Task 9: follow_unfollow.py

**Files:**
- Create: `content-engine/engagement/follow_unfollow.py`
- Create: `content-engine/tests/engagement/test_follow_unfollow.py`

> **AVISO:** Este script usa `instagrapi`, que acessa a API privada do Instagram (mesma que o app mobile). Viola os ToS se detectado como automação. Use limites conservadores e apenas em horários de uso humano normal. Requer os secrets `IG_USERNAME` e `IG_PASSWORD` no GitHub.

- [ ] **Step 1: Escrever testes para follow_unfollow.py**

`content-engine/tests/engagement/test_follow_unfollow.py`:
```python
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


def test_candidatos_ja_seguidos_sao_ignorados():
    from engagement.follow_unfollow import _filtrar_candidatos
    following = {"user_1": "2026-04-01T10:00:00", "user_2": "2026-04-01T11:00:00"}
    candidatos = ["user_1", "user_3", "user_4"]
    resultado = _filtrar_candidatos(candidatos, following)
    assert "user_1" not in resultado
    assert "user_3" in resultado
    assert "user_4" in resultado


def test_unfollow_apenas_apos_7_dias():
    from engagement.follow_unfollow import _candidatos_para_unfollow
    agora = datetime.now()
    following = {
        "user_old": (agora - timedelta(days=8)).isoformat(),
        "user_new": (agora - timedelta(days=2)).isoformat(),
    }
    seguidores = set()  # nenhum seguiu de volta
    resultado = _candidatos_para_unfollow(following, seguidores)
    assert "user_old" in resultado
    assert "user_new" not in resultado


def test_unfollow_nao_dessegue_quem_seguiu_de_volta():
    from engagement.follow_unfollow import _candidatos_para_unfollow
    agora = datetime.now()
    following = {
        "user_fiel": (agora - timedelta(days=10)).isoformat(),
    }
    seguidores = {"user_fiel"}
    resultado = _candidatos_para_unfollow(following, seguidores)
    assert "user_fiel" not in resultado
```

- [ ] **Step 2: Rodar testes para confirmar que falham**

```bash
cd content-engine
python -m pytest tests/engagement/test_follow_unfollow.py -v
```
Esperado: `ImportError`

- [ ] **Step 3: Implementar follow_unfollow.py**

`content-engine/engagement/follow_unfollow.py`:
```python
"""
follow_unfollow.py
Segue contas do nicho e dessegue quem não retribuiu após 7 dias.

AVISO: Usa instagrapi (API privada do Instagram). Use com moderação.
Requer IG_USERNAME e IG_PASSWORD como variáveis de ambiente.

Uso:
  python -m engagement.follow_unfollow
  python -m engagement.follow_unfollow --dry-run
"""
import argparse
import os
from datetime import datetime, timedelta
from engagement.shared import state

MAX_FOLLOWS = 20
MAX_UNFOLLOWS = 20
UNFOLLOW_AFTER_DAYS = 7

HASHTAGS_NICHO = [
    "humorbrasileiro",
    "relacionamento",
    "terapia",
    "psicologia",
    "vidaadulta",
    "memesbrasil",
    "comportamento",
]


def _filtrar_candidatos(candidatos: list, following: dict) -> list:
    """Remove candidatos que já estão sendo seguidos."""
    return [uid for uid in candidatos if uid not in following]


def _candidatos_para_unfollow(following: dict, seguidores: set) -> list:
    """Retorna IDs seguidos há mais de UNFOLLOW_AFTER_DAYS que não seguiram de volta."""
    corte = datetime.now() - timedelta(days=UNFOLLOW_AFTER_DAYS)
    return [
        uid for uid, ts in following.items()
        if datetime.fromisoformat(ts) < corte and uid not in seguidores
    ]


def executar(dry_run: bool = False) -> None:
    print(f"\n👥 Follow/Unfollow — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("⚠️  Usa API privada — execute com moderação\n")

    try:
        from instagrapi import Client
    except ImportError:
        print("❌ instagrapi não instalado. Execute: pip install instagrapi")
        return

    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")
    if not username or not password:
        print("❌ IG_USERNAME e IG_PASSWORD não configurados")
        return

    st = state.load()
    following: dict = st.setdefault("following", {})

    # Login
    cl = None
    if not dry_run:
        cl = Client()
        cl.login(username, password)
        print(f"  ✅ Login como @{username}")

    # --- Fase FOLLOW ---
    hashtag = HASHTAGS_NICHO[datetime.now().weekday() % len(HASHTAGS_NICHO)]
    print(f"  🔍 Buscando candidatos em #{hashtag}...")

    candidatos_raw: list[str] = []
    if not dry_run and cl:
        medias = cl.hashtag_medias_recent(hashtag, amount=60)
        candidatos_raw = [str(m.user.pk) for m in medias]
    else:
        print(f"  [DRY RUN] Buscaria em #{hashtag}")
        candidatos_raw = ["fake_user_1", "fake_user_2"]

    candidatos = _filtrar_candidatos(candidatos_raw, following)[:MAX_FOLLOWS]
    follows = 0
    for uid in candidatos:
        if follows >= MAX_FOLLOWS:
            break
        if dry_run:
            print(f"  [DRY RUN] Seguiria {uid}")
        else:
            cl.user_follow(int(uid))
            print(f"  ✅ Seguiu {uid}")
        following[uid] = datetime.now().isoformat()
        follows += 1

    # --- Fase UNFOLLOW ---
    print(f"\n  🔍 Verificando quem não seguiu de volta...")
    seguidores: set = set()
    if not dry_run and cl:
        meu_id = cl.user_id
        seguidores = {str(u.pk) for u in cl.user_followers(meu_id).values()}

    para_desseguir = _candidatos_para_unfollow(following, seguidores)[:MAX_UNFOLLOWS]
    unfollows = 0
    for uid in para_desseguir:
        if unfollows >= MAX_UNFOLLOWS:
            break
        if dry_run:
            print(f"  [DRY RUN] Desseguiria {uid}")
        else:
            cl.user_unfollow(int(uid))
            print(f"  ✅ Desseguiu {uid}")
        del following[uid]
        unfollows += 1

    st["following"] = following
    state.save(st)
    print(f"\n✅ {follows} follow(s), {unfollows} unfollow(s)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    executar(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Rodar testes para confirmar que passam**

```bash
cd content-engine
python -m pytest tests/engagement/test_follow_unfollow.py -v
```
Esperado: 3 testes `PASSED`

- [ ] **Step 5: Commit**

```bash
git add content-engine/engagement/follow_unfollow.py \
        content-engine/tests/engagement/test_follow_unfollow.py
git commit -m "feat: follow_unfollow.py — cresce audiência no nicho via instagrapi"
```

---

## Task 10: hashtag_intel.py

**Files:**
- Create: `content-engine/engagement/hashtag_intel.py`
- Create: `content-engine/tests/engagement/test_hashtag_intel.py`

- [ ] **Step 1: Escrever testes para hashtag_intel.py**

`content-engine/tests/engagement/test_hashtag_intel.py`:
```python
def test_extrair_hashtags_simples():
    from engagement.hashtag_intel import extrair_hashtags
    tags = extrair_hashtags("Oi #DraJulga #humor estou aqui #Brasil")
    assert "drajulga" in tags
    assert "humor" in tags
    assert "brasil" in tags


def test_extrair_hashtags_caption_vazia():
    from engagement.hashtag_intel import extrair_hashtags
    assert extrair_hashtags("") == []
    assert extrair_hashtags(None) == []


def test_calcular_score():
    from engagement.hashtag_intel import calcular_score
    post = {"like_count": 100, "comments_count": 20}
    assert calcular_score(post) == 140.0  # 100 + (20 * 2)


def test_calcular_score_sem_dados():
    from engagement.hashtag_intel import calcular_score
    assert calcular_score({}) == 0.0


def test_gerar_relatorio_ranking():
    from engagement.hashtag_intel import gerar_relatorio
    posts = [
        {"caption": "#humor #brasil", "like_count": 100, "comments_count": 10},
        {"caption": "#humor #meme", "like_count": 200, "comments_count": 20},
        {"caption": "#brasil", "like_count": 10, "comments_count": 1},
    ]
    rel = gerar_relatorio(posts)
    assert rel["total_posts_analisados"] == 3
    # #humor aparece em 2 posts com score total (120 + 240) = 360, média = 180
    # #brasil aparece em 2 posts com score total (120 + 12) = 132, média = 66
    ranking_tags = [r["hashtag"] for r in rel["ranking"]]
    assert ranking_tags.index("#humor") < ranking_tags.index("#brasil")


def test_gerar_relatorio_sem_posts():
    from engagement.hashtag_intel import gerar_relatorio
    rel = gerar_relatorio([])
    assert rel["total_posts_analisados"] == 0
    assert rel["ranking"] == []
```

- [ ] **Step 2: Rodar testes para confirmar que falham**

```bash
cd content-engine
python -m pytest tests/engagement/test_hashtag_intel.py -v
```
Esperado: `ImportError`

- [ ] **Step 3: Implementar hashtag_intel.py**

`content-engine/engagement/hashtag_intel.py`:
```python
"""
hashtag_intel.py
Analisa performance de hashtags nos últimos 20 posts do @dra.julga.
Gera ranking por score de engajamento e salva no engagement_state.json.

Uso:
  python -m engagement.hashtag_intel
"""
import os
import re
from datetime import datetime
from collections import defaultdict
from engagement.shared import meta_client, state


def _account_id() -> str:
    return os.getenv("IG_ACCOUNT_ID") or os.getenv("INSTAGRAM_ACCOUNT_ID", "")


def extrair_hashtags(caption: str | None) -> list[str]:
    if not caption:
        return []
    return re.findall(r"#(\w+)", caption.lower())


def calcular_score(post: dict) -> float:
    likes = post.get("like_count", 0) or 0
    comentarios = post.get("comments_count", 0) or 0
    return float(likes + (comentarios * 2))


def gerar_relatorio(posts: list) -> dict:
    stats: dict = defaultdict(lambda: {"posts": 0, "score_total": 0.0})

    for post in posts:
        for tag in extrair_hashtags(post.get("caption")):
            stats[tag]["posts"] += 1
            stats[tag]["score_total"] += calcular_score(post)

    ranking = sorted(
        [
            {
                "hashtag": f"#{tag}",
                "posts": s["posts"],
                "score_medio": round(s["score_total"] / s["posts"], 1),
            }
            for tag, s in stats.items()
        ],
        key=lambda x: x["score_medio"],
        reverse=True,
    )

    return {
        "gerado_em": datetime.now().isoformat(),
        "total_posts_analisados": len(posts),
        "ranking": ranking[:20],
    }


def executar() -> None:
    print(f"\n📊 Hashtag Intelligence — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    data = meta_client.get(
        f"{_account_id()}/media",
        params={"fields": "id,caption,like_count,comments_count,timestamp", "limit": "20"},
    )
    posts = data.get("data", [])
    print(f"  📂 {len(posts)} posts analisados")

    relatorio = gerar_relatorio(posts)

    st = state.load()
    st["hashtag_report"] = relatorio
    state.save(st)

    print(f"\n🏆 Top 5 hashtags por engajamento:")
    for i, item in enumerate(relatorio["ranking"][:5], 1):
        print(f"  {i}. {item['hashtag']} — score médio {item['score_medio']} ({item['posts']} post(s))")

    print(f"\n✅ Relatório salvo em engagement_state.json")


def main() -> None:
    executar()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Rodar testes para confirmar que passam**

```bash
cd content-engine
python -m pytest tests/engagement/test_hashtag_intel.py -v
```
Esperado: 5 testes `PASSED`

- [ ] **Step 5: Commit**

```bash
git add content-engine/engagement/hashtag_intel.py \
        content-engine/tests/engagement/test_hashtag_intel.py
git commit -m "feat: hashtag_intel.py — ranking de hashtags por engajamento"
```

---

## Task 11: engagement.yml — workflow GitHub Actions

**Files:**
- Create: `.github/workflows/engagement.yml`

- [ ] **Step 1: Criar engagement.yml**

`.github/workflows/engagement.yml`:
```yaml
name: Engagement Bot — Dra. Julga

on:
  schedule:
    - cron: '0 11 * * *'    # 08h BRT
    - cron: '0 13 * * *'    # 10h BRT
    - cron: '0 14 * * *'    # 11h BRT
    - cron: '0 15 * * *'    # 12h BRT
    - cron: '0 17 * * *'    # 14h BRT
    - cron: '0 19 * * *'    # 16h BRT
    - cron: '0 21 * * *'    # 18h BRT
    - cron: '0 23 * * *'    # 20h BRT
    - cron: '0 1  * * *'    # 22h BRT
  workflow_dispatch:
    inputs:
      script:
        description: 'Script para rodar manualmente'
        required: true
        default: 'reply_comments'
        type: choice
        options:
          - reply_comments
          - repost_stories
          - reply_dms
          - comment_growth
          - follow_unfollow
          - hashtag_intel

env:
  META_ACCESS_TOKEN: ${{ secrets.META_ACCESS_TOKEN }}
  INSTAGRAM_ACCOUNT_ID: ${{ secrets.INSTAGRAM_ACCOUNT_ID }}
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  IG_USERNAME: ${{ secrets.IG_USERNAME }}
  IG_PASSWORD: ${{ secrets.IG_PASSWORD }}

jobs:

  reply-comments:
    name: Reply Comments (a cada 2h, 08h–22h BRT)
    runs-on: ubuntu-latest
    if: |
      github.event_name == 'workflow_dispatch' && github.event.inputs.script == 'reply_comments' ||
      github.event_name == 'schedule'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Verificar horário (roda a cada 2h)
        id: check
        run: |
          HOUR=$(date -u +"%H" | sed 's/^0//')
          # Horas UTC para 08h-22h BRT (11-01 UTC) a cada 2h: 11,13,15,17,19,21,23,1
          if echo "11 13 15 17 19 21 23 1" | grep -wq "$HOUR"; then
            echo "run=true" >> $GITHUB_OUTPUT
          else
            echo "run=false" >> $GITHUB_OUTPUT
          fi
      - if: steps.check.outputs.run == 'true' || github.event_name == 'workflow_dispatch'
        run: pip install anthropic python-dotenv requests
      - if: steps.check.outputs.run == 'true' || github.event_name == 'workflow_dispatch'
        run: cd content-engine && python -m engagement.reply_comments
      - if: steps.check.outputs.run == 'true' || github.event_name == 'workflow_dispatch'
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: engagement state reply-comments [skip ci]"
          file_pattern: content-engine/generated/engagement_state.json

  repost-stories:
    name: Repost Stories (a cada 4h, 08h–22h BRT)
    runs-on: ubuntu-latest
    if: |
      github.event_name == 'workflow_dispatch' && github.event.inputs.script == 'repost_stories' ||
      github.event_name == 'schedule'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Verificar horário (roda a cada 4h)
        id: check
        run: |
          HOUR=$(date -u +"%H" | sed 's/^0//')
          if echo "11 15 19 23" | grep -wq "$HOUR"; then
            echo "run=true" >> $GITHUB_OUTPUT
          else
            echo "run=false" >> $GITHUB_OUTPUT
          fi
      - if: steps.check.outputs.run == 'true' || github.event_name == 'workflow_dispatch'
        run: pip install python-dotenv requests
      - if: steps.check.outputs.run == 'true' || github.event_name == 'workflow_dispatch'
        run: cd content-engine && python -m engagement.repost_stories
      - if: steps.check.outputs.run == 'true' || github.event_name == 'workflow_dispatch'
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: engagement state repost-stories [skip ci]"
          file_pattern: content-engine/generated/engagement_state.json

  reply-dms:
    name: Reply DMs (a cada 3h, 08h–22h BRT)
    runs-on: ubuntu-latest
    if: |
      github.event_name == 'workflow_dispatch' && github.event.inputs.script == 'reply_dms' ||
      github.event_name == 'schedule'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Verificar horário (roda a cada 3h)
        id: check
        run: |
          HOUR=$(date -u +"%H" | sed 's/^0//')
          if echo "11 14 17 20 23" | grep -wq "$HOUR"; then
            echo "run=true" >> $GITHUB_OUTPUT
          else
            echo "run=false" >> $GITHUB_OUTPUT
          fi
      - if: steps.check.outputs.run == 'true' || github.event_name == 'workflow_dispatch'
        run: pip install anthropic python-dotenv requests
      - if: steps.check.outputs.run == 'true' || github.event_name == 'workflow_dispatch'
        run: cd content-engine && python -m engagement.reply_dms
      - if: steps.check.outputs.run == 'true' || github.event_name == 'workflow_dispatch'
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: engagement state reply-dms [skip ci]"
          file_pattern: content-engine/generated/engagement_state.json

  comment-growth:
    name: Comment Growth (1x/dia, 14h BRT)
    runs-on: ubuntu-latest
    if: |
      github.event_name == 'workflow_dispatch' && github.event.inputs.script == 'comment_growth' ||
      github.event_name == 'schedule'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Verificar horário (roda às 14h BRT = 17h UTC)
        id: check
        run: |
          HOUR=$(date -u +"%H" | sed 's/^0//')
          if [ "$HOUR" = "17" ]; then echo "run=true" >> $GITHUB_OUTPUT
          else echo "run=false" >> $GITHUB_OUTPUT; fi
      - if: steps.check.outputs.run == 'true' || github.event_name == 'workflow_dispatch'
        run: pip install anthropic python-dotenv requests
      - if: steps.check.outputs.run == 'true' || github.event_name == 'workflow_dispatch'
        run: cd content-engine && python -m engagement.comment_growth
      - if: steps.check.outputs.run == 'true' || github.event_name == 'workflow_dispatch'
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: engagement state comment-growth [skip ci]"
          file_pattern: content-engine/generated/engagement_state.json

  follow-unfollow:
    name: Follow/Unfollow (1x/dia, 10h BRT)
    runs-on: ubuntu-latest
    if: |
      github.event_name == 'workflow_dispatch' && github.event.inputs.script == 'follow_unfollow' ||
      github.event_name == 'schedule'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Verificar horário (roda às 10h BRT = 13h UTC)
        id: check
        run: |
          HOUR=$(date -u +"%H" | sed 's/^0//')
          if [ "$HOUR" = "13" ]; then echo "run=true" >> $GITHUB_OUTPUT
          else echo "run=false" >> $GITHUB_OUTPUT; fi
      - if: steps.check.outputs.run == 'true' || github.event_name == 'workflow_dispatch'
        run: pip install instagrapi python-dotenv
      - if: steps.check.outputs.run == 'true' || github.event_name == 'workflow_dispatch'
        run: cd content-engine && python -m engagement.follow_unfollow
      - if: steps.check.outputs.run == 'true' || github.event_name == 'workflow_dispatch'
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: engagement state follow-unfollow [skip ci]"
          file_pattern: content-engine/generated/engagement_state.json

  hashtag-intel:
    name: Hashtag Intelligence (domingo, 11h BRT)
    runs-on: ubuntu-latest
    if: |
      github.event_name == 'workflow_dispatch' && github.event.inputs.script == 'hashtag_intel' ||
      github.event_name == 'schedule'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Verificar horário (domingo 11h BRT = domingo 14h UTC)
        id: check
        run: |
          HOUR=$(date -u +"%H" | sed 's/^0//')
          DAY=$(date -u +"%u")  # 7 = domingo
          if [ "$DAY" = "7" ] && [ "$HOUR" = "14" ]; then
            echo "run=true" >> $GITHUB_OUTPUT
          else
            echo "run=false" >> $GITHUB_OUTPUT
          fi
      - if: steps.check.outputs.run == 'true' || github.event_name == 'workflow_dispatch'
        run: pip install python-dotenv requests
      - if: steps.check.outputs.run == 'true' || github.event_name == 'workflow_dispatch'
        run: cd content-engine && python -m engagement.hashtag_intel
      - if: steps.check.outputs.run == 'true' || github.event_name == 'workflow_dispatch'
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: hashtag intel report [skip ci]"
          file_pattern: content-engine/generated/engagement_state.json
```

- [ ] **Step 2: Adicionar secret IG_USERNAME e IG_PASSWORD no GitHub**

No repositório: Settings → Secrets and variables → Actions → New repository secret:
- `IG_USERNAME` = username do @dra.julga sem o @
- `IG_PASSWORD` = senha da conta

- [ ] **Step 3: Rodar testes completos antes de commitar**

```bash
cd content-engine
python -m pytest tests/engagement/ -v
```
Esperado: todos os testes `PASSED` (nenhum falho)

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/engagement.yml
git commit -m "feat: engagement.yml — orquestra 6 scripts de engajamento com schedules independentes"
```

---

## Task 12: Rodar suite completa de testes + verificação final

- [ ] **Step 1: Instalar dependências de teste**

```bash
cd content-engine
pip install pytest anthropic python-dotenv requests
```

- [ ] **Step 2: Rodar todos os testes**

```bash
cd content-engine
python -m pytest tests/ -v --tb=short
```
Esperado: todos os testes `PASSED`

- [ ] **Step 3: Verificar imports de cada script manualmente**

```bash
cd content-engine
python -c "from engagement.post_engagement import gerar_comentario_votacao; print(gerar_comentario_votacao('amor'))"
python -c "from engagement.reply_dms import _contem_keyword; print(_contem_keyword('me julga'))"
python -c "from engagement.hashtag_intel import calcular_score; print(calcular_score({'like_count': 100, 'comments_count': 10}))"
```
Esperado: saída sem erros para cada comando

- [ ] **Step 4: Commit final**

```bash
git add .
git commit -m "feat: sistema de engajamento completo — 7 scripts + workflow + testes

- shared/state.py, meta_client.py, claude_client.py
- post_engagement.py, reply_comments.py, repost_stories.py
- reply_dms.py, comment_growth.py, follow_unfollow.py, hashtag_intel.py
- engagement.yml com 6 jobs independentes
- Integração com daily_post.yml

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```
