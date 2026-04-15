# Feedback Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After each post, send a 5-star Telegram poll to the owner; use ratings to auto-adjust veredicto variation weights (A/B/C) at generation time.

**Architecture:** New `feedback.py` module handles state writes and Telegram messaging. `telegram_handler.py` gains a `callback_query` router that calls `feedback.store_rating`. `generate_reels.py` gains a pure `_calcular_pesos_veredicto()` that reads `post_details` from state. A new `daily_post.yml` step fires the rating request after every publish (non-fatal on Telegram failure).

**Tech Stack:** Python 3.11, `requests`, `engagement.shared.state` (existing), Telegram Bot API (sendMessage / answerCallbackQuery / editMessageText), pytest/monkeypatch.

---

## File Map

| Action   | File                                                         | Responsibility                                      |
|----------|--------------------------------------------------------------|-----------------------------------------------------|
| Modify   | `content-engine/engagement/shared/state.py`                  | Add `"post_details": {}` to DEFAULT_STATE           |
| Create   | `content-engine/engagement/feedback.py`                      | `send_rating_request()` + `store_rating()` CLI      |
| Create   | `content-engine/tests/engagement/test_feedback.py`           | Unit tests for feedback module                      |
| Modify   | `content-engine/generate_reels.py`                           | `_calcular_pesos_veredicto()` + update `_sorteio_veredicto()` |
| Modify   | `content-engine/tests/test_generate_reels.py`                | Tests for `_calcular_pesos_veredicto`               |
| Modify   | `content-engine/webhook/telegram_handler.py`                 | `callback_query` router + `handle_callback()`       |
| Modify   | `content-engine/tests/webhook/test_telegram.py`              | Tests for `handle_callback`                         |
| Modify   | `.github/workflows/daily_post.yml`                           | New step "Enviar votacao no Telegram"               |

---

### Task 1: Add `post_details` to DEFAULT_STATE

**Files:**
- Modify: `content-engine/engagement/shared/state.py`
- Modify: `content-engine/tests/engagement/test_state.py`

- [ ] **Step 1: Write the failing test**

Add at the end of `content-engine/tests/engagement/test_state.py`:

```python
def test_default_state_tem_post_details(tmp_path, monkeypatch):
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    result = state.load()
    assert result["post_details"] == {}
```

- [ ] **Step 2: Run to confirm it fails**

```bash
cd content-engine && python -m pytest tests/engagement/test_state.py::test_default_state_tem_post_details -v
```

Expected: `FAILED — KeyError: 'post_details'`

- [ ] **Step 3: Add `"post_details": {}` to DEFAULT_STATE**

In `content-engine/engagement/shared/state.py`, change:

```python
DEFAULT_STATE: dict = {
    "comments_replied": [],
    "stories_reposted": [],
    "dms_replied": [],
    "following": {},
    "hashtag_report": {},
    "errors": [],
}
```

To:

```python
DEFAULT_STATE: dict = {
    "comments_replied": [],
    "stories_reposted": [],
    "dms_replied": [],
    "following": {},
    "hashtag_report": {},
    "errors": [],
    "post_details": {},
}
```

- [ ] **Step 4: Run all state tests**

```bash
cd content-engine && python -m pytest tests/engagement/test_state.py -v
```

Expected: all PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add content-engine/engagement/shared/state.py content-engine/tests/engagement/test_state.py
git commit -m "feat: add post_details to DEFAULT_STATE"
```

---

### Task 2: Create `feedback.py`

**Files:**
- Create: `content-engine/engagement/feedback.py`
- Create: `content-engine/tests/engagement/test_feedback.py`

- [ ] **Step 1: Write failing tests**

Create `content-engine/tests/engagement/test_feedback.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from unittest.mock import patch, MagicMock, call
from pathlib import Path


def _mock_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "999")


def test_store_rating_salva_nota(tmp_path, monkeypatch):
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")

    from engagement import feedback
    monkeypatch.setattr(feedback, "state", state)

    state.save({
        "post_details": {
            "2026-04-07_amor": {
                "media_id": "123",
                "tipo_veredicto": "A",
                "titulo": "O Sumido",
                "crime": "ghosting sazonal",
                "categoria": "amor",
                "nota": None,
            }
        }
    })

    feedback.store_rating("2026-04-07_amor", 4)

    resultado = state.load()
    assert resultado["post_details"]["2026-04-07_amor"]["nota"] == 4


def test_store_rating_chave_inexistente_nao_quebra(tmp_path, monkeypatch):
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    from engagement import feedback
    monkeypatch.setattr(feedback, "state", state)

    # No exception raised for unknown key
    feedback.store_rating("chave_inexistente", 3)


def test_send_rating_request_salva_detalhes(tmp_path, monkeypatch):
    _mock_env(monkeypatch)
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    from engagement import feedback
    monkeypatch.setattr(feedback, "state", state)

    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        feedback.send_rating_request(
            chave="2026-04-07_amor",
            media_id="123456",
            tipo_veredicto="A",
            titulo="O Sumido Saudoso",
            crime="ghosting sazonal com dolo comprovado",
            categoria="amor",
        )

    resultado = state.load()
    post = resultado["post_details"]["2026-04-07_amor"]
    assert post["media_id"] == "123456"
    assert post["tipo_veredicto"] == "A"
    assert post["titulo"] == "O Sumido Saudoso"
    assert post["crime"] == "ghosting sazonal com dolo comprovado"
    assert post["categoria"] == "amor"
    assert post["nota"] is None


def test_send_rating_request_envia_telegram(tmp_path, monkeypatch):
    _mock_env(monkeypatch)
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    from engagement import feedback
    monkeypatch.setattr(feedback, "state", state)

    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        feedback.send_rating_request(
            chave="2026-04-07_amor",
            media_id="123456",
            tipo_veredicto="A",
            titulo="O Sumido Saudoso",
            crime="ghosting sazonal",
            categoria="amor",
        )

    mock_post.assert_called_once()
    payload = mock_post.call_args[1]["json"]
    assert payload["chat_id"] == "999"
    assert "O Sumido Saudoso" in payload["text"]
    assert "Variação A" in payload["text"]
    assert "inline_keyboard" in payload["reply_markup"]
    botoes = payload["reply_markup"]["inline_keyboard"][0]
    assert len(botoes) == 5
    assert botoes[0]["callback_data"] == "rate:2026-04-07_amor:1"
    assert botoes[4]["callback_data"] == "rate:2026-04-07_amor:5"


def test_send_rating_request_sem_token_nao_quebra(tmp_path, monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    import engagement.shared.state as state
    monkeypatch.setattr(state, "STATE_FILE", tmp_path / "state.json")
    from engagement import feedback
    monkeypatch.setattr(feedback, "state", state)

    # Should not raise even without token
    with patch("requests.post") as mock_post:
        feedback.send_rating_request(
            chave="2026-04-07_amor",
            media_id="123",
            tipo_veredicto="A",
            titulo="Teste",
            crime="crime de teste",
            categoria="amor",
        )
    mock_post.assert_not_called()
```

- [ ] **Step 2: Run to confirm all fail**

```bash
cd content-engine && python -m pytest tests/engagement/test_feedback.py -v
```

Expected: `ModuleNotFoundError: No module named 'engagement.feedback'`

- [ ] **Step 3: Create `feedback.py`**

Create `content-engine/engagement/feedback.py`:

```python
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
            {"text": "⭐",       "callback_data": f"rate:{chave}:1"},
            {"text": "⭐⭐",     "callback_data": f"rate:{chave}:2"},
            {"text": "⭐⭐⭐",   "callback_data": f"rate:{chave}:3"},
            {"text": "⭐⭐⭐⭐", "callback_data": f"rate:{chave}:4"},
            {"text": "⭐⭐⭐⭐⭐", "callback_data": f"rate:{chave}:5"},
        ]]
    }

    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": texto, "reply_markup": keyboard},
            timeout=10,
        )
    except Exception:
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
```

- [ ] **Step 4: Run tests**

```bash
cd content-engine && python -m pytest tests/engagement/test_feedback.py -v
```

Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add content-engine/engagement/feedback.py content-engine/tests/engagement/test_feedback.py
git commit -m "feat: add feedback module with send_rating_request and store_rating"
```

---

### Task 3: Add `_calcular_pesos_veredicto` to `generate_reels.py`

**Files:**
- Modify: `content-engine/generate_reels.py`
- Modify: `content-engine/tests/test_generate_reels.py`

- [ ] **Step 1: Write failing tests**

Append to `content-engine/tests/test_generate_reels.py`:

```python
def _post_details_com_notas(notas_a, notas_b, notas_c):
    """Cria post_details com notas sintéticas por variação."""
    details = {}
    for i, nota in enumerate(notas_a):
        details[f"data_a_{i}_amor"] = {"tipo_veredicto": "A", "nota": nota}
    for i, nota in enumerate(notas_b):
        details[f"data_b_{i}_amor"] = {"tipo_veredicto": "B", "nota": nota}
    for i, nota in enumerate(notas_c):
        details[f"data_c_{i}_amor"] = {"tipo_veredicto": "C", "nota": nota}
    return details


def test_calcular_pesos_retorna_base_sem_dados():
    assert gr._calcular_pesos_veredicto({}) == [60, 25, 15]


def test_calcular_pesos_retorna_base_com_dados_insuficientes():
    # Variação B com apenas 2 notas — não ativa ajuste
    details = _post_details_com_notas([4, 5, 4], [3, 3], [3, 3, 3])
    assert gr._calcular_pesos_veredicto(details) == [60, 25, 15]


def test_calcular_pesos_ajustados_soma_100():
    details = _post_details_com_notas([4, 5, 4], [2, 2, 3], [3, 3, 3])
    pesos = gr._calcular_pesos_veredicto(details)
    assert sum(pesos) == 100


def test_calcular_pesos_a_favorecida_quando_notas_altas():
    # A muito melhor que B e C
    details = _post_details_com_notas([5, 5, 5], [1, 1, 1], [1, 1, 1])
    pesos = gr._calcular_pesos_veredicto(details)
    assert pesos[0] > pesos[1]
    assert pesos[0] > pesos[2]


def test_calcular_pesos_nenhuma_variacao_abaixo_de_5():
    # Variação C com notas muito baixas
    details = _post_details_com_notas([5, 5, 5], [5, 5, 5], [1, 1, 1])
    pesos = gr._calcular_pesos_veredicto(details)
    assert all(p >= 5 for p in pesos)


def test_calcular_pesos_usa_apenas_ultimas_10_notas():
    # A tem 12 notas: 9 ruins + últimas 3 boas
    notas_a = [1, 1, 1, 1, 1, 1, 1, 1, 1, 5, 5, 5]
    notas_b = [3, 3, 3]
    notas_c = [3, 3, 3]
    details_12 = _post_details_com_notas(notas_a, notas_b, notas_c)
    pesos_12 = gr._calcular_pesos_veredicto(details_12)

    # A com exatamente as últimas 10 notas: [1,1,1,1,1,1,1,5,5,5] → média 2.7
    notas_a_10 = [1, 1, 1, 1, 1, 1, 1, 5, 5, 5]
    details_10 = _post_details_com_notas(notas_a_10, notas_b, notas_c)
    pesos_10 = gr._calcular_pesos_veredicto(details_10)

    assert pesos_12 == pesos_10


def test_calcular_pesos_exemplo_do_spec():
    # Spec: A=[4,5,4] B=[2,2,3] C=[3,3,3] → A=72, B=16, C=12
    details = _post_details_com_notas([4, 5, 4], [2, 2, 3], [3, 3, 3])
    pesos = gr._calcular_pesos_veredicto(details)
    assert pesos == [72, 16, 12]


def test_sorteio_veredicto_usa_post_details(monkeypatch):
    # Com A dominante, A deve ser sorteado na maioria das vezes
    details = _post_details_com_notas([5, 5, 5], [1, 1, 1], [1, 1, 1])
    resultados = [gr._sorteio_veredicto(details) for _ in range(50)]
    assert resultados.count("A") > 30  # alta concentração em A
```

- [ ] **Step 2: Run to confirm failures**

```bash
cd content-engine && python -m pytest tests/test_generate_reels.py -k "calcular_pesos or sorteio_veredicto_usa" -v
```

Expected: `AttributeError: module 'generate_reels' has no attribute '_calcular_pesos_veredicto'`

- [ ] **Step 3: Add `_calcular_pesos_veredicto` and update `_sorteio_veredicto`**

In `content-engine/generate_reels.py`, replace:

```python
def _sorteio_veredicto() -> str:
    """Sorteia o tipo de veredicto com pesos 60/25/15."""
    return random.choices(["A", "B", "C"], weights=[60, 25, 15])[0]
```

With:

```python
def _calcular_pesos_veredicto(post_details: dict) -> list:
    """Calcula pesos dinâmicos baseados nas notas do dono.

    Retorna [peso_A, peso_B, peso_C]. Soma sempre 100.
    Usa pesos base [60, 25, 15] quando dados são insuficientes (< 3 notas por variação).
    """
    PESOS_BASE = {"A": 60, "B": 25, "C": 15}
    VARIACOES = ["A", "B", "C"]
    MIN_NOTAS = 3
    MAX_NOTAS = 10

    notas_por_variacao = {"A": [], "B": [], "C": []}
    for detalhes in post_details.values():
        nota = detalhes.get("nota")
        tipo = detalhes.get("tipo_veredicto")
        if nota is not None and tipo in notas_por_variacao:
            notas_por_variacao[tipo].append(nota)

    if any(len(notas_por_variacao[v]) < MIN_NOTAS for v in VARIACOES):
        return [60, 25, 15]

    medias = {}
    for v in VARIACOES:
        ultimas = notas_por_variacao[v][-MAX_NOTAS:]
        medias[v] = sum(ultimas) / len(ultimas)

    todas_notas = []
    for v in VARIACOES:
        todas_notas.extend(notas_por_variacao[v][-MAX_NOTAS:])
    media_global = sum(todas_notas) / len(todas_notas)

    pesos_raw = {v: max(5, round(PESOS_BASE[v] * medias[v] / media_global)) for v in VARIACOES}
    soma = sum(pesos_raw.values())
    pesos_norm = {v: round(pesos_raw[v] * 100 / soma) for v in VARIACOES}

    diff = 100 - sum(pesos_norm.values())
    if diff != 0:
        v_maior = max(VARIACOES, key=lambda v: pesos_raw[v])
        pesos_norm[v_maior] += diff

    return [pesos_norm["A"], pesos_norm["B"], pesos_norm["C"]]


def _sorteio_veredicto(post_details: dict = None) -> str:
    """Sorteia o tipo de veredicto com pesos dinâmicos baseados nas notas do dono."""
    pesos = _calcular_pesos_veredicto(post_details or {})
    return random.choices(["A", "B", "C"], weights=pesos)[0]
```

Also update `gerar_roteiro` to load `post_details` from state when `tipo_veredicto` is None. Replace:

```python
    if tipo_veredicto is None:
        tipo_veredicto = _sorteio_veredicto()
```

With:

```python
    if tipo_veredicto is None:
        try:
            from engagement.shared import state as _state
            _post_details = _state.load().get("post_details", {})
        except Exception:
            _post_details = {}
        tipo_veredicto = _sorteio_veredicto(_post_details)
```

- [ ] **Step 4: Run all `test_generate_reels` tests**

```bash
cd content-engine && python -m pytest tests/test_generate_reels.py -v
```

Expected: all PASS (existing 11 + new 8 = 19 tests)

- [ ] **Step 5: Commit**

```bash
git add content-engine/generate_reels.py content-engine/tests/test_generate_reels.py
git commit -m "feat: add _calcular_pesos_veredicto and dynamic sorteio_veredicto"
```

---

### Task 4: Add `callback_query` handler to `telegram_handler.py`

**Files:**
- Modify: `content-engine/webhook/telegram_handler.py`
- Modify: `content-engine/tests/webhook/test_telegram.py`

- [ ] **Step 1: Write failing tests**

Append to `content-engine/tests/webhook/test_telegram.py`:

```python
def _make_callback(chave: str, nota: int, chat_id: int = 999, message_id: int = 42) -> dict:
    return {
        "callback_query": {
            "id": "cq_id_123",
            "data": f"rate:{chave}:{nota}",
            "message": {
                "message_id": message_id,
                "chat": {"id": chat_id},
            },
        }
    }


def test_callback_query_chama_store_rating(monkeypatch):
    _mock_env(monkeypatch)
    with patch("webhook.telegram_handler.feedback") as mock_fb, \
         patch("requests.post"):
        th.handle(_make_callback("2026-04-07_amor", 4))
    mock_fb.store_rating.assert_called_once_with("2026-04-07_amor", 4)


def test_callback_query_edita_mensagem(monkeypatch):
    _mock_env(monkeypatch)
    state = {"post_details": {"2026-04-07_amor": {"titulo": "O Sumido", "nota": None}}}
    with patch("webhook.telegram_handler.feedback"), \
         patch("webhook.telegram_handler._fetch_state", return_value=state), \
         patch("requests.post") as mock_post:
        th.handle(_make_callback("2026-04-07_amor", 4))

    calls = [str(c) for c in mock_post.call_args_list]
    assert any("editMessageText" in c for c in calls)
    assert any("answerCallbackQuery" in c for c in calls)


def test_callback_query_mensagem_contem_estrelas(monkeypatch):
    _mock_env(monkeypatch)
    state = {"post_details": {"2026-04-07_amor": {"titulo": "O Sumido", "nota": None}}}
    with patch("webhook.telegram_handler.feedback"), \
         patch("webhook.telegram_handler._fetch_state", return_value=state), \
         patch("requests.post") as mock_post:
        th.handle(_make_callback("2026-04-07_amor", 3))

    edit_call = next(
        c for c in mock_post.call_args_list
        if "editMessageText" in str(c)
    )
    texto = edit_call[1]["json"]["text"]
    assert "⭐⭐⭐" in texto
    assert "O Sumido" in texto


def test_callback_query_chat_id_errado_ignorado(monkeypatch):
    _mock_env(monkeypatch)
    with patch("webhook.telegram_handler.feedback") as mock_fb:
        th.handle(_make_callback("2026-04-07_amor", 4, chat_id=888))
    mock_fb.store_rating.assert_not_called()


def test_callback_query_formato_invalido_ignorado(monkeypatch):
    _mock_env(monkeypatch)
    with patch("webhook.telegram_handler.feedback") as mock_fb, \
         patch("requests.post"):
        th.handle({
            "callback_query": {
                "id": "x",
                "data": "nao_e_rate",
                "message": {"message_id": 1, "chat": {"id": 999}},
            }
        })
    mock_fb.store_rating.assert_not_called()
```

- [ ] **Step 2: Run to confirm failures**

```bash
cd content-engine && python -m pytest tests/webhook/test_telegram.py -k "callback" -v
```

Expected: errors about missing `feedback` import and `handle_callback`

- [ ] **Step 3: Modify `telegram_handler.py`**

At the top of `content-engine/webhook/telegram_handler.py`, add the import after existing imports:

```python
from engagement import feedback
```

In the `handle()` function, add the callback_query check at the **very beginning**, before the existing `msg = update.get(...)` lines:

```python
def handle(update: dict) -> None:
    """Entry point — chamado pelo endpoint /telegram."""
    callback = update.get("callback_query", {})
    if callback:
        _handle_callback(callback)
        return

    msg = update.get("message", {})
    # ... (rest unchanged)
```

Add the new `_handle_callback` function after the `handle()` function, before the command functions:

```python
def _handle_callback(callback: dict) -> None:
    """Processa callback_query de botões inline (ex: votação de rating)."""
    data = callback.get("data", "")
    callback_id = callback.get("id", "")
    message = callback.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")

    if chat_id != _OWNER_CHAT_ID():
        return

    if not data.startswith("rate:"):
        return

    parts = data.split(":")
    if len(parts) != 3:
        return

    _, chave, nota_str = parts
    try:
        nota = int(nota_str)
    except ValueError:
        return

    if nota < 1 or nota > 5:
        return

    feedback.store_rating(chave, nota)

    state = _fetch_state()
    post = state.get("post_details", {}).get(chave, {})
    titulo = post.get("titulo", chave)

    estrelas = "⭐" * nota
    texto_confirmacao = f'✅ Nota registrada: {estrelas} para "{titulo}"'

    token = _TOKEN()
    if not token:
        return

    requests.post(
        f"https://api.telegram.org/bot{token}/answerCallbackQuery",
        json={"callback_query_id": callback_id},
        timeout=10,
    )
    requests.post(
        f"https://api.telegram.org/bot{token}/editMessageText",
        json={"chat_id": chat_id, "message_id": message_id, "text": texto_confirmacao},
        timeout=10,
    )
```

- [ ] **Step 4: Run all telegram tests**

```bash
cd content-engine && python -m pytest tests/webhook/test_telegram.py -v
```

Expected: all PASS (existing 7 + new 5 = 12 tests)

- [ ] **Step 5: Commit**

```bash
git add content-engine/webhook/telegram_handler.py content-engine/tests/webhook/test_telegram.py
git commit -m "feat: add callback_query handler for Telegram rating votes"
```

---

### Task 5: Add "Enviar votacao no Telegram" step to `daily_post.yml`

**Files:**
- Modify: `.github/workflows/daily_post.yml`

- [ ] **Step 1: Add the step after "Notificar post publicado"**

In `.github/workflows/daily_post.yml`, after the block:

```yaml
      - name: Notificar post publicado
        if: steps.dedup.outputs.skip != 'true' && steps.publicar.outputs.media_id != ''
        run: |
          cd content-engine
          TITULO=$(CAT="${{ steps.categoria.outputs.categoria }}" python3 -c "import json,glob,os; from datetime import datetime; h=datetime.utcnow().strftime('%Y-%m-%d'); c=os.environ['CAT']; f=glob.glob('generated/reels/'+h+'_'+c+'_reels.json'); print(json.load(open(f[0])).get('titulo',c) if f else c)")
          python -m notify send_post_published \
            --categoria ${{ steps.categoria.outputs.categoria }} \
            --titulo "$TITULO" \
            --hora "${{ steps.publicar.outputs.hora }}" \
            --media_id ${{ steps.publicar.outputs.media_id }}
```

Add the new step:

```yaml
      - name: Enviar votacao no Telegram
        if: steps.dedup.outputs.skip != 'true' && steps.publicar.outputs.media_id != ''
        continue-on-error: true
        run: |
          cd content-engine
          HOJE=$(date -u +"%Y-%m-%d")
          CAT="${{ steps.categoria.outputs.categoria }}"
          CHAVE="${HOJE}_${CAT}"
          TIPO=$(CAT="$CAT" python3 -c "import json,glob,os; from datetime import datetime; h=datetime.utcnow().strftime('%Y-%m-%d'); c=os.environ['CAT']; f=glob.glob('generated/reels/'+h+'_'+c+'_reels.json'); print(json.load(open(f[0])).get('tipo_veredicto','A') if f else 'A')")
          TITULO=$(CAT="$CAT" python3 -c "import json,glob,os; from datetime import datetime; h=datetime.utcnow().strftime('%Y-%m-%d'); c=os.environ['CAT']; f=glob.glob('generated/reels/'+h+'_'+c+'_reels.json'); print(json.load(open(f[0])).get('titulo',c) if f else c)")
          CRIME=$(CAT="$CAT" python3 -c "import json,glob,os; from datetime import datetime; h=datetime.utcnow().strftime('%Y-%m-%d'); c=os.environ['CAT']; f=glob.glob('generated/reels/'+h+'_'+c+'_reels.json'); print(json.load(open(f[0])).get('crime','') if f else '')")
          python -m engagement.feedback send_rating_request \
            --chave "$CHAVE" \
            --media_id ${{ steps.publicar.outputs.media_id }} \
            --tipo_veredicto "$TIPO" \
            --titulo "$TITULO" \
            --crime "$CRIME" \
            --categoria "$CAT"
```

- [ ] **Step 2: Verify YAML is valid**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/daily_post.yml'))" && echo "YAML OK"
```

Expected: `YAML OK`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/daily_post.yml
git commit -m "feat: send Telegram rating request after each published post"
```

---

### Task 6: Run full test suite and push

- [ ] **Step 1: Run all tests**

```bash
cd content-engine && python -m pytest tests/ -v
```

Expected: all pass (no failures)

- [ ] **Step 2: Push**

```bash
git push origin main
```

- [ ] **Step 3: Verify flow manually**

Use `/forcar_post amor` in Telegram. After publish confirm:
1. A Telegram message arrives with 5 ⭐ buttons
2. Tapping a button edits the message with `✅ Nota registrada: ⭐⭐⭐`
3. `content-engine/generated/engagement_state.json` has the `post_details` entry with the rating

---

## Success Criteria

1. After post published → Telegram message with 5 inline buttons arrives
2. Tapping a button → message edited with `✅ Nota registrada: ⭐⭐⭐⭐` and note saved in state
3. With ≥ 3 notes per variation → `_sorteio_veredicto()` uses adjusted weights
4. `_calcular_pesos_veredicto` is unit-testable with no I/O (pure function)
5. If Telegram fails (no token, timeout) → workflow continues without error
