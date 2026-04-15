# Content Quality — Dra. Julga Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reescrever o sistema de geração de carrosseis para eliminar repetição texto/slide, estabelecer escalada narrativa real entre cenas, e substituir o "diagnóstico clínico" por um veredicto jurídico com estrutura fixa.

**Architecture:** Um único arquivo é modificado (`generate_reels.py`). Três funções helper puras são extraídas para permitir testes unitários (`_validar_roteiro`, `_calcular_numero_processo`, `_sorteio_veredicto`). A função `gerar_roteiro` ganha loop de validação com até 2 tentativas antes de propagar o erro.

**Tech Stack:** Python 3.11, anthropic SDK, pytest, unittest.mock — sem novas dependências.

---

## File Structure

```
content-engine/
  generate_reels.py          ← modificar (único arquivo de produção)
  tests/
    test_generate_reels.py   ← criar (novo arquivo de testes)
```

---

### Task 1: Criar testes para as funções helper puras

**Files:**
- Create: `content-engine/tests/test_generate_reels.py`

- [ ] **Step 1: Criar o arquivo de testes com imports e fixture**

```python
# content-engine/tests/test_generate_reels.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import generate_reels as gr


def _roteiro_valido():
    """Fixture: roteiro mínimo válido para testes."""
    return {
        "categoria": "amor",
        "titulo": "O Sumido Saudoso",
        "numero_processo": "AMO-001/26",
        "crime": "ghosting sazonal com dolo comprovado",
        "tipo_veredicto": "A",
        "frase_printavel": "Culpado por ghosting sazonal. Sem apelação.",
        "cenas": [
            {"numero": 1, "duracao_segundos": 3,
             "texto": "3 meses sem dar um pio. Agora voltou com 'oi sumida'.",
             "texto_slide": "3 meses de silêncio.\n'Oi sumida' às 23h."},
            {"numero": 2, "duracao_segundos": 4,
             "texto": "O réu deixou 47 mensagens no vácuo entre abril e julho.",
             "texto_slide": "47 mensagens.\nTodas lidas. Zero respostas."},
            {"numero": 3, "duracao_segundos": 4,
             "texto": "Enquanto isso, curtiu 12 stories seus. Sem responder nenhum.",
             "texto_slide": "12 stories curtidos.\nNenhuma palavra."},
            {"numero": 4, "duracao_segundos": 4,
             "texto": "Agravante: ele voltou numa sexta às 23h47. Clássico.",
             "texto_slide": "Sexta, 23h47.\nAgravante confirmado."},
            {"numero": 5, "duracao_segundos": 4,
             "texto": "VEREDICTO: Culpado por ghosting sazonal com dolo comprovado. Sem apelação.",
             "texto_slide": "VEREDICTO\nCulpado por ghosting sazonal.\nSem apelação."},
            {"numero": 6, "duracao_segundos": 3,
             "texto": "Veja seu processo em mejulga.com.br",
             "texto_slide": "Veja seu processo.\nmejulga.com.br"},
        ],
        "texto_completo": "3 meses sem dar um pio...",
        "legenda_instagram": "#draJulga",
        "sugestao_musica": "lo-fi tenso",
    }
```

- [ ] **Step 2: Adicionar testes para `_validar_roteiro` — caso válido**

```python
def test_validar_roteiro_valido_retorna_none():
    assert gr._validar_roteiro(_roteiro_valido()) is None
```

- [ ] **Step 3: Adicionar testes para `_validar_roteiro` — rejeita slide == texto**

```python
def test_validar_roteiro_rejeita_slide_igual_texto():
    r = _roteiro_valido()
    r["cenas"][1]["texto_slide"] = r["cenas"][1]["texto"]
    resultado = gr._validar_roteiro(r)
    assert resultado is not None
    assert "redundante" in resultado.lower()
```

- [ ] **Step 4: Adicionar testes para `_validar_roteiro` — rejeita "Gente,"**

```python
def test_validar_roteiro_rejeita_abertura_gente():
    r = _roteiro_valido()
    r["cenas"][0]["texto"] = "Gente, vocês fazem isso?"
    resultado = gr._validar_roteiro(r)
    assert resultado is not None
    assert "gente" in resultado.lower()
```

- [ ] **Step 5: Adicionar testes para `_validar_roteiro` — rejeita "diagnóstico"**

```python
def test_validar_roteiro_rejeita_diagnostico():
    r = _roteiro_valido()
    r["cenas"][4]["texto"] = "Diagnóstico: síndrome do amor ausente."
    resultado = gr._validar_roteiro(r)
    assert resultado is not None
    assert "diagnóstico" in resultado.lower()
```

- [ ] **Step 6: Adicionar testes para `_validar_roteiro` — rejeita veredicto longo**

```python
def test_validar_roteiro_rejeita_veredicto_longo():
    r = _roteiro_valido()
    # cena 5 com mais de 20 palavras
    r["cenas"][4]["texto"] = (
        "VEREDICTO: Culpado por uma série de comportamentos extremamente duvidosos "
        "e questionáveis que demonstram total desrespeito pelas outras pessoas. Sem apelação."
    )
    resultado = gr._validar_roteiro(r)
    assert resultado is not None
    assert "veredicto" in resultado.lower()
```

- [ ] **Step 7: Adicionar testes para `_calcular_numero_processo`**

```python
def test_calcular_numero_processo_sem_arquivos(tmp_path):
    resultado = gr._calcular_numero_processo("amor", tmp_path)
    assert resultado == "AMO-001/26"


def test_calcular_numero_processo_com_arquivos_existentes(tmp_path):
    # Simula 2 posts anteriores de amor
    (tmp_path / "2026-04-01_amor_reels.json").write_text("{}")
    (tmp_path / "2026-04-03_amor_reels.json").write_text("{}")
    resultado = gr._calcular_numero_processo("amor", tmp_path)
    assert resultado == "AMO-003/26"


def test_calcular_numero_processo_nao_conta_outras_categorias(tmp_path):
    (tmp_path / "2026-04-01_amor_reels.json").write_text("{}")
    (tmp_path / "2026-04-02_trabalho_reels.json").write_text("{}")
    resultado = gr._calcular_numero_processo("amor", tmp_path)
    assert resultado == "AMO-002/26"
```

- [ ] **Step 8: Adicionar testes para `_sorteio_veredicto`**

```python
def test_sorteio_veredicto_retorna_valor_valido():
    for _ in range(20):
        resultado = gr._sorteio_veredicto()
        assert resultado in ("A", "B", "C")
```

- [ ] **Step 9: Rodar testes — esperar FALHA pois as funções não existem ainda**

```bash
cd content-engine && python -m pytest tests/test_generate_reels.py -v 2>&1 | head -30
```

Expected: `ImportError` ou `AttributeError: module 'generate_reels' has no attribute '_validar_roteiro'`

- [ ] **Step 10: Commit dos testes**

```bash
git add content-engine/tests/test_generate_reels.py
git commit -m "test: testes para helpers de validacao do generate_reels"
```

---

### Task 2: Extrair funções helper puras

**Files:**
- Modify: `content-engine/generate_reels.py` (adicionar 3 funções antes de `gerar_roteiro`)

- [ ] **Step 1: Adicionar import `random` no topo do arquivo**

No topo de `generate_reels.py`, após os imports existentes, adicionar:
```python
import random
```

- [ ] **Step 2: Adicionar `_sorteio_veredicto` após as constantes (após linha 32)**

Inserir após o bloco `CATEGORIAS_INFO`:

```python
def _sorteio_veredicto() -> str:
    """Sorteia o tipo de veredicto com pesos 60/25/15."""
    return random.choices(["A", "B", "C"], weights=[60, 25, 15])[0]
```

- [ ] **Step 3: Adicionar `_calcular_numero_processo` logo após**

```python
def _calcular_numero_processo(categoria: str, pasta: Path) -> str:
    """Gera número de processo sequencial por categoria. Ex: AMO-003/26."""
    prefixo = categoria[:3].upper()
    ano = datetime.now().strftime("%y")
    existentes = list(pasta.glob(f"*_{categoria}_reels.json"))
    numero = len(existentes) + 1
    return f"{prefixo}-{numero:03d}/{ano}"
```

- [ ] **Step 4: Adicionar `_validar_roteiro` logo após**

```python
def _validar_roteiro(roteiro: dict) -> str | None:
    """Valida o roteiro gerado. Retorna None se válido, mensagem de erro se inválido."""
    cenas = roteiro.get("cenas", [])

    for cena in cenas:
        texto = (cena.get("texto") or "").strip()
        slide = (cena.get("texto_slide") or "").strip()

        # Rejeita se slide é cópia do texto (normalizado)
        if texto and slide:
            texto_norm = " ".join(texto.lower().split())
            slide_norm = " ".join(slide.lower().replace("\n", " ").split())
            if texto_norm == slide_norm or slide_norm in texto_norm:
                return (
                    f"Cena {cena.get('numero')}: texto_slide redundante — "
                    f"é cópia ou subconjunto do texto narrado."
                )

        # Rejeita abertura "Gente,"
        if texto.lower().startswith("gente,"):
            return f"Cena {cena.get('numero')}: texto começa com 'Gente,' — proibido."

        # Rejeita jargão médico
        for palavra in ("diagnóstico", "síndrome", "transtorno"):
            if palavra in texto.lower() or palavra in slide.lower():
                return (
                    f"Cena {cena.get('numero')}: contém '{palavra}' — "
                    f"usar vocabulário jurídico, não médico."
                )

    # Veredicto conciso — cena 5
    cena5 = next((c for c in cenas if c.get("numero") == 5), None)
    if cena5:
        palavras = len((cena5.get("texto") or "").split())
        if palavras > 20:
            return (
                f"Veredicto (cena 5) tem {palavras} palavras — máximo é 20. "
                f"Encurtar para ficar printável."
            )

    return None
```

- [ ] **Step 5: Rodar testes novamente**

```bash
cd content-engine && python -m pytest tests/test_generate_reels.py -v
```

Expected: todos os testes PASSAM.

- [ ] **Step 6: Commit**

```bash
git add content-engine/generate_reels.py
git commit -m "feat: extrai helpers _validar_roteiro, _calcular_numero_processo, _sorteio_veredicto"
```

---

### Task 3: Reescrever SYSTEM_PROMPT

**Files:**
- Modify: `content-engine/generate_reels.py` — substituir a constante `SYSTEM_PROMPT` (linhas 34-63)

- [ ] **Step 1: Substituir o SYSTEM_PROMPT completo**

Substituir o bloco `SYSTEM_PROMPT = """..."""` por:

```python
SYSTEM_PROMPT = """Você é a Dra. Julga — juíza fictícia que conduz processos contra comportamentos absurdos do cotidiano brasileiro. Observa, coleta provas e profere veredictos. Voz: fria, forense, levemente entediada de já ter visto tudo. Nunca cruel.

TOM PROIBIDO:
- NUNCA começar com "Gente,"
- NUNCA usar jargão médico: "síndrome", "diagnóstico", "CID", "transtorno", "patologia"
- NUNCA falar como amiga de grupo ou influencer
- NUNCA usar "Sem defesa possível" — só "Sem apelação.", "Improvável." ou "Trânsito em julgado."

VOCABULÁRIO PERMITIDO (usar com parcimônia):
réu/ré, autos, prova, agravante, atenuante negado, reincidência, pena, sentença, culpado, trânsito em julgado, sem apelação, flagrante, dolo

REGRA DA ESPECIFICIDADE — obrigatório:
Toda cena precisa de pelo menos UM número, horário, nome de app/plataforma, ou dado concreto.
❌ "fica muito tempo no celular"
✅ "23h47. Décimo quarto vídeo de um cachorro que você não conhece."

REGRA DA ESCALADA — obrigatório:
Cena 3 deve ser mais específica e absurda que Cena 2.
Cena 4 deve contradizer diretamente a desculpa implícita da Cena 2 com prova pior.
Cena 5 deve ser mais curta que Cena 4.

REGRA ANTI-REDUNDÂNCIA — obrigatório:
texto_slide NÃO é o texto narrado com quebras de linha. É um ângulo diferente do mesmo momento.
O texto narra. O slide acusa com os fatos-prova, sem verbos de ligação.
❌ texto: "Quarta, 14h37, câmera desligada na reunião" → slide: "14h37\nCâmera desligada"
✅ texto: "Quarta, 14h37. Câmera desligada. Você estava no quarto vídeo do feed."
   slide: "Reunião do Teams.\nQuarto vídeo do Instagram."

REGRA DO VEREDICTO PRINTÁVEL — obrigatório:
Cena 5 deve ter no máximo 20 palavras. É a frase que vai virar print e ser mandada no grupo.

REGRA: Responda SOMENTE com JSON válido, sem texto fora dele."""
```

- [ ] **Step 2: Verificar que o arquivo ainda é Python válido**

```bash
cd content-engine && python -c "import generate_reels; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add content-engine/generate_reels.py
git commit -m "refactor: reescreve SYSTEM_PROMPT — Dra. Julga é juíza, não psicóloga"
```

---

### Task 4: Reescrever user prompt em `gerar_roteiro`

**Files:**
- Modify: `content-engine/generate_reels.py` — função `gerar_roteiro` (linha 68 em diante)

- [ ] **Step 1: Substituir assinatura da função e início**

Substituir:
```python
def gerar_roteiro(categoria: str) -> dict:
    """Gera roteiro de Reels em cenas curtas."""

    info = CATEGORIAS_INFO.get(categoria, {"label": categoria, "emoji": "⚖️"})

    prompt = f"""Crie um roteiro de Reels de 20-25 segundos para a Dra. Julga sobre "{info['label']}"."""
```

Por:
```python
def gerar_roteiro(categoria: str, tipo_veredicto: str = None, pasta: Path = None) -> dict:
    """Gera roteiro de Reels em cenas curtas com veredicto jurídico."""

    if tipo_veredicto is None:
        tipo_veredicto = _sorteio_veredicto()
    if pasta is None:
        pasta = Path(__file__).parent / "generated" / "reels"

    numero_processo = _calcular_numero_processo(categoria, pasta)
    info = CATEGORIAS_INFO.get(categoria, {"label": categoria, "emoji": "⚖️"})
```

- [ ] **Step 2: Substituir o bloco de instrução de veredicto por variação dinâmica**

Após o bloco anterior, adicionar:

```python
    _INSTRUCOES_VEREDICTO = {
        "A": (
            'Cena 5 — SENTENÇA CURTA (Variação A):\n'
            'texto: "VEREDICTO: Culpado por [crime específico e engraçado]. '
            '[Reincidente. / Atenuante negado.] Sem apelação."\n'
            'texto_slide: "VEREDICTO\\n[crime em 4-6 palavras].\\nSem apelação."\n'
            'Exemplo: "VEREDICTO: Culpado por simulação laboral em ambiente remoto. '
            'Reincidente. Sem apelação."'
        ),
        "B": (
            'Cena 5 — PENA ABSURDA (Variação B):\n'
            'texto: "VEREDICTO: Condenado a [pena criativa e específica]. '
            'Pena suspensa se [condição impossível de cumprir]. Improvável."\n'
            'texto_slide: "VEREDICTO\\nCondenado a [pena em 4-5 palavras].\\nImprovável."\n'
            'Exemplo: "VEREDICTO: Condenado a pagar em dinheiro por 90 dias. '
            'Pena suspensa se resistir à promoção. Improvável."'
        ),
        "C": (
            'Cena 5 — AUTOS DO PROCESSO (Variação C):\n'
            f'texto: "Processo {numero_processo}. Réu: você. Crime: [nome do crime]. '
            'Provas: [2 itens das cenas anteriores]. Decisão: CULPADO."\n'
            f'texto_slide: "Processo {numero_processo}\\nCrime: [crime]\\nDecisão: CULPADO."\n'
            f'Exemplo: "Processo {numero_processo}. Réu: você. Crime: ghosting sazonal. '
            'Provas: 3 meses de silêncio, volta às 23h47. Decisão: CULPADO."'
        ),
    }
    instrucao_veredicto = _INSTRUCOES_VEREDICTO[tipo_veredicto]
```

- [ ] **Step 3: Substituir o bloco do prompt principal**

Substituir todo o `prompt = f"""..."""` existente (linhas 73-107) por:

```python
    prompt = f"""Crie um roteiro de carrossel para a Dra. Julga sobre a categoria "{info['label']}".

EXATAMENTE 6 cenas. Cada cena tem `texto` (narração falada, flui como fala, pode ter conectores) e `texto_slide` (card visual — ângulo DIFERENTE do texto, não um resumo).

ESTRUTURA OBRIGATÓRIA:
- Cena 1 — ABERTURA DO PROCESSO: flagrante direto ou "Processo {numero_processo}. Réu: você." Nunca "Gente,". Começa com dado concreto.
- Cena 2 — INTIMAÇÃO: conduta fria com número, horário ou dado específico.
- Cena 3 — PRIMEIRA PROVA: detalhe mais absurdo e específico que a Cena 2. Sem conectores no slide.
- Cena 4 — AGRAVANTE: comportamento que contradiz a desculpa implícita da Cena 2. O texto começa com "Agravante:" ou "Pior:".
- Cena 5 — VEREDICTO: {instrucao_veredicto}
- Cena 6 — CTA (fixo): texto: "Veja seu processo em mejulga.com.br" | texto_slide: "Veja seu processo.\\nmejulga.com.br"

EXEMPLO CORRETO (categoria: trabalho):
{{
  "cenas": [
    {{"numero": 1, "texto": "Processo TRA-007/26. Réu: você. Alegação: trabalha demais.", "texto_slide": "Processo TRA-007/26.\\nRéu: você."}},
    {{"numero": 2, "texto": "Quarta-feira, 14h37. Reunião do Teams. Câmera desligada.", "texto_slide": "Reunião do Teams.\\nQuarto vídeo do Instagram."}},
    {{"numero": 3, "texto": "Você estava no quarto vídeo do feed falando 'tô aqui' a cada 8 minutos.", "texto_slide": "'Tô aqui, tô aqui.'\\nA cada 8 minutos."}},
    {{"numero": 4, "texto": "Agravante: passou 47 minutos formatando um slide que ninguém vai ler porque tinha preguiça de começar o relatório.", "texto_slide": "47 minutos.\\nSlide que ninguém vai ler."}},
    {{"numero": 5, "texto": "VEREDICTO: Culpado por simulação laboral em ambiente remoto. Reincidente. Sem apelação.", "texto_slide": "VEREDICTO\\nCulpado por simulação laboral.\\nSem apelação."}},
    {{"numero": 6, "texto": "Veja seu processo em mejulga.com.br", "texto_slide": "Veja seu processo.\\nmejulga.com.br"}}
  ]
}}

ANTI-EXEMPLO (não faça isso — categoria: dinheiro):
- ❌ texto cena 1: "Gente, ele parcelou a pizza" (começa com "Gente,")
- ❌ texto cena 5: "Diagnóstico: síndrome do endividamento crônico" (jargão médico)
- ❌ texto_slide cena 2 igual ao texto cena 2 com quebra de linha (redundância)

Responda SOMENTE com este JSON:
{{
  "categoria": "{categoria}",
  "titulo": "título curto do caso (O/A + arquétipo, ex: 'O Ocupado Profissional')",
  "numero_processo": "{numero_processo}",
  "crime": "nome curto do crime em 4-7 palavras (para print)",
  "tipo_veredicto": "{tipo_veredicto}",
  "frase_printavel": "o veredicto em ≤14 palavras, sem 'VEREDICTO:' na frente",
  "cenas": [
    {{"numero": 1, "duracao_segundos": 3, "texto": "...", "texto_slide": "..."}},
    {{"numero": 2, "duracao_segundos": 4, "texto": "...", "texto_slide": "..."}},
    {{"numero": 3, "duracao_segundos": 4, "texto": "...", "texto_slide": "..."}},
    {{"numero": 4, "duracao_segundos": 4, "texto": "...", "texto_slide": "..."}},
    {{"numero": 5, "duracao_segundos": 4, "texto": "...", "texto_slide": "..."}},
    {{"numero": 6, "duracao_segundos": 3, "texto": "...", "texto_slide": "..."}}
  ],
  "texto_completo": "texto corrido de todas as cenas unidas para o áudio",
  "legenda_instagram": "legenda completa com hashtags relevantes",
  "sugestao_musica": "estilo musical sugerido"
}}"""
```

- [ ] **Step 4: Verificar sintaxe**

```bash
cd content-engine && python -c "import generate_reels; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add content-engine/generate_reels.py
git commit -m "feat: reescreve user prompt com few-shot, estrutura forense e variações de veredicto"
```

---

### Task 5: Adicionar loop de validação em `gerar_roteiro`

**Files:**
- Modify: `content-engine/generate_reels.py` — fim da função `gerar_roteiro`

- [ ] **Step 1: Substituir o bloco de chamada ao Claude e retorno**

Substituir:
```python
    resposta = claude_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    texto = resposta.content[0].text.strip()
    texto = texto.replace("```json", "").replace("```", "").strip()
    return json.loads(texto)
```

Por:
```python
    prompt_atual = prompt
    for tentativa in range(1, 3):  # máximo 2 tentativas
        resposta = claude_client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt_atual}]
        )

        texto = resposta.content[0].text.strip()
        texto = texto.replace("```json", "").replace("```", "").strip()
        roteiro = json.loads(texto)

        erro = _validar_roteiro(roteiro)
        if erro is None:
            return roteiro

        print(f"⚠️  Tentativa {tentativa}/2 — roteiro rejeitado: {erro}")
        if tentativa < 2:
            prompt_atual = (
                prompt + f"\n\nATENÇÃO — Sua resposta anterior foi rejeitada:\n{erro}\n"
                "Corrija e responda novamente com JSON válido."
            )

    # Retorna o último gerado mesmo com erro (evita travar o workflow)
    print("⚠️  Usando roteiro da tentativa 2 sem aprovação — verificar manualmente.")
    return roteiro
```

- [ ] **Step 2: Adicionar teste de integração para o loop de validação**

Em `content-engine/tests/test_generate_reels.py`, adicionar:

```python
def test_gerar_roteiro_retenta_quando_invalido(monkeypatch, tmp_path):
    """Verifica que gerar_roteiro tenta novamente quando a validação falha."""
    roteiro_ruim = _roteiro_valido()
    roteiro_ruim["cenas"][0]["texto"] = "Gente, isso é um teste."  # inválido

    roteiro_bom = _roteiro_valido()

    chamadas = []

    def mock_create(**kwargs):
        chamadas.append(kwargs)
        r = roteiro_ruim if len(chamadas) == 1 else roteiro_bom
        mock_resp = MagicMock()
        mock_resp.content[0].text = json.dumps(r)
        return mock_resp

    monkeypatch.setattr(gr.claude_client.messages, "create", mock_create)

    resultado = gr.gerar_roteiro("amor", tipo_veredicto="A", pasta=tmp_path)

    assert len(chamadas) == 2  # tentou 2 vezes
    assert resultado["cenas"][0]["texto"] == roteiro_bom["cenas"][0]["texto"]


def test_gerar_roteiro_retorna_mesmo_invalido_apos_2_tentativas(monkeypatch, tmp_path):
    """Após 2 falhas, retorna o último roteiro sem travar."""
    roteiro_ruim = _roteiro_valido()
    roteiro_ruim["cenas"][0]["texto"] = "Gente, sempre inválido."

    def mock_create(**kwargs):
        mock_resp = MagicMock()
        mock_resp.content[0].text = json.dumps(roteiro_ruim)
        return mock_resp

    monkeypatch.setattr(gr.claude_client.messages, "create", mock_create)

    resultado = gr.gerar_roteiro("amor", tipo_veredicto="A", pasta=tmp_path)
    # Não levanta exceção — retorna o roteiro mesmo inválido
    assert resultado is not None
```

- [ ] **Step 3: Rodar todos os testes**

```bash
cd content-engine && python -m pytest tests/test_generate_reels.py -v
```

Expected: todos PASSAM.

- [ ] **Step 4: Commit**

```bash
git add content-engine/generate_reels.py content-engine/tests/test_generate_reels.py
git commit -m "feat: adiciona loop de validação com até 2 tentativas em gerar_roteiro"
```

---

### Task 6: Atualizar `salvar_roteiro` para novos campos

**Files:**
- Modify: `content-engine/generate_reels.py` — função `salvar_roteiro` (linha ~159)

- [ ] **Step 1: Atualizar o bloco TXT para incluir novos campos e remover `conclusao`**

Substituir o bloco dentro de `salvar_roteiro` que escreve no arquivo TXT:

```python
    # TXT formatado para usar no CapCut
    arquivo_txt = pasta / f"{hoje}_{categoria}_roteiro_capcut.txt"
    with open(arquivo_txt, "w", encoding="utf-8") as f:
        f.write("=" * 50 + "\n")
        f.write(f"ROTEIRO — DRA. JULGA\n")
        f.write(f"Categoria: {categoria.upper()}\n")
        f.write(f"Título: {roteiro.get('titulo', '')}\n")
        f.write(f"Processo: {roteiro.get('numero_processo', '')}\n")
        f.write(f"Crime: {roteiro.get('crime', '')}\n")
        f.write(f"Veredicto: {roteiro.get('frase_printavel', '')}\n")
        f.write(f"Tipo veredicto: {roteiro.get('tipo_veredicto', '')}\n")
        f.write(f"Data: {hoje}\n")
        f.write("=" * 50 + "\n\n")

        f.write("CENAS:\n\n")
        for cena in roteiro.get("cenas", []):
            f.write(f"CENA {cena['numero']} ({cena['duracao_segundos']}s)\n")
            f.write(f"  NARRAÇÃO: {cena['texto']}\n")
            f.write(f"  SLIDE:    {cena.get('texto_slide', '').replace(chr(10), ' | ')}\n\n")

        f.write("-" * 50 + "\n")
        f.write("LEGENDA INSTAGRAM:\n\n")
        f.write(roteiro.get("legenda_instagram", "") + "\n\n")

        f.write("-" * 50 + "\n")
        f.write(f"SUGESTÃO DE MÚSICA: {roteiro.get('sugestao_musica', '')}\n")
```

- [ ] **Step 2: Verificar sintaxe**

```bash
cd content-engine && python -c "import generate_reels; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add content-engine/generate_reels.py
git commit -m "feat: atualiza salvar_roteiro com campos numero_processo, crime, frase_printavel"
```

---

### Task 7: Teste de fumaça end-to-end

**Files:**
- Nenhum arquivo novo — apenas execução manual

- [ ] **Step 1: Rodar suite completa de testes**

```bash
cd content-engine && python -m pytest tests/test_generate_reels.py -v
```

Expected: todos os testes PASSAM, zero falhas.

- [ ] **Step 2: Gerar um roteiro real de teste (requer ANTHROPIC_API_KEY no .env)**

```bash
cd content-engine && python generate_reels.py --categoria amor --sem_audio
```

Expected:
- Arquivo JSON criado em `generated/reels/YYYY-MM-DD_amor_reels.json`
- JSON contém campos `numero_processo`, `crime`, `tipo_veredicto`, `frase_printavel`
- Cena 5 contém "VEREDICTO:" e NÃO contém "Diagnóstico:" ou "síndrome"
- Nenhum `texto_slide` é cópia do `texto`

- [ ] **Step 3: Verificar o JSON gerado**

```bash
cd content-engine && python3 -c "
import json, glob
from datetime import datetime
hoje = datetime.now().strftime('%Y-%m-%d')
f = glob.glob(f'generated/reels/{hoje}_amor_reels.json')[0]
d = json.load(open(f))
print('Processo:', d.get('numero_processo'))
print('Crime:', d.get('crime'))
print('Veredicto:', d.get('frase_printavel'))
print('Tipo:', d.get('tipo_veredicto'))
print()
for c in d['cenas']:
    print(f'Cena {c[\"numero\"]}:')
    print(f'  texto: {c[\"texto\"]}')
    print(f'  slide: {c.get(\"texto_slide\",\"\")}')
    print()
"
```

Expected: saída com veredicto jurídico, slides distintos do texto, sem "Gente," ou "diagnóstico".

- [ ] **Step 4: Commit final de limpeza**

```bash
git add content-engine/generate_reels.py content-engine/tests/test_generate_reels.py
git commit -m "feat: qualidade de conteudo Dra. Julga — veredicto juridico + few-shot + validacao"
```

---

## Referência rápida — funções novas/modificadas

| Função | Status | Assinatura |
|--------|--------|-----------|
| `_sorteio_veredicto` | Nova | `() -> str` |
| `_calcular_numero_processo` | Nova | `(categoria: str, pasta: Path) -> str` |
| `_validar_roteiro` | Nova | `(roteiro: dict) -> str \| None` |
| `gerar_roteiro` | Modificada | `(categoria: str, tipo_veredicto: str = None, pasta: Path = None) -> dict` |
| `salvar_roteiro` | Modificada | `(roteiro: dict, pasta: Path) -> tuple[Path, Path]` |
