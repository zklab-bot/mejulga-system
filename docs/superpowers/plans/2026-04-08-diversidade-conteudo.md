# Diversidade de Conteúdo — Prompt + Formato Glossário

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Quebrar o padrão formulaic do Me Julga em duas frentes: (1) reescrever as regras do SYSTEM_PROMPT para forçar variedade nos slides existentes; (2) implementar o formato "Glossário da Dra. Julga" como novo tipo de post com pipeline completo.

**Architecture:** O SYSTEM_PROMPT recebe novas regras de variação (REGRA DA ESPECIFICIDADE reformulada + ÂNGULOS NARRATIVOS) que afetam todos os posts existentes sem mudar código. O Glossário é um novo `tipo_post` com prompt próprio, validador próprio, e renderização própria — totalmente paralelo ao carrossel atual, sem alterar o fluxo existente.

**Tech Stack:** Python, Pillow (PIL), Anthropic SDK, pytest

---

## Mapa de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `content-engine/generate_reels.py` | Modificar | Reescrever SYSTEM_PROMPT; adicionar `gerar_glossario()`, `_validar_glossario()`, `salvar_glossario()` |
| `content-engine/gerar_carrossel.py` | Modificar | Adicionar `gerar_slides_glossario()`, `carregar_glossario()`; atualizar `main()` com flag `--formato` |
| `content-engine/tests/test_generate_reels.py` | Modificar | Testes para novas regras do SYSTEM_PROMPT + `gerar_glossario()` + `_validar_glossario()` |
| `content-engine/tests/test_gerar_carrossel.py` | Criar | Testes para `gerar_slides_glossario()` |

---

## Task 1: Reescrever SYSTEM_PROMPT — variedade de ancoragem e ângulos

**Files:**
- Modify: `content-engine/generate_reels.py:156-177` (SYSTEM_PROMPT)
- Test: `content-engine/tests/test_generate_reels.py`

### Contexto

O SYSTEM_PROMPT atual tem uma `REGRA DA ESPECIFICIDADE` com exemplo único de horário ("23h47") — o modelo âncora nele e usa timestamps em TODA cena. A correção é ampliar os tipos de ancoragem válidos e proibir dois do mesmo tipo consecutivos. Adicionalmente, inserir `ÂNGULOS NARRATIVOS` que instrui o modelo a variar a perspectiva narrativa por cena.

- [ ] **Step 1: Escrever os testes de contrato do SYSTEM_PROMPT**

Adicionar ao final de `content-engine/tests/test_generate_reels.py`:

```python
def test_system_prompt_contem_tipos_de_ancoragem():
    """SYSTEM_PROMPT deve listar os 6 tipos de ancoragem."""
    for tipo in ["HORÁRIO", "QUANTIDADE", "PLATAFORMA", "CITAÇÃO", "COMPARAÇÃO", "COMPORTAMENTO"]:
        assert tipo in gr.SYSTEM_PROMPT, f"SYSTEM_PROMPT não contém tipo de ancoragem: {tipo}"


def test_system_prompt_proibe_ancoragem_consecutiva():
    """SYSTEM_PROMPT deve mencionar a proibição de tipos consecutivos."""
    assert "consecutiv" in gr.SYSTEM_PROMPT.lower() or "duas cenas seguidas" in gr.SYSTEM_PROMPT


def test_system_prompt_contem_angulos_narrativos():
    """SYSTEM_PROMPT deve conter a seção de ângulos narrativos."""
    assert "ÂNGULOS NARRATIVOS" in gr.SYSTEM_PROMPT


def test_system_prompt_angulos_tem_exemplos():
    """ÂNGULOS NARRATIVOS deve listar pelo menos FORENSE e SOCIOLÓGICO."""
    assert "FORENSE" in gr.SYSTEM_PROMPT
    assert "SOCIOLÓGICO" in gr.SYSTEM_PROMPT
```

- [ ] **Step 2: Rodar os testes para confirmar que falham**

```
cd content-engine
pytest tests/test_generate_reels.py::test_system_prompt_contem_tipos_de_ancoragem tests/test_generate_reels.py::test_system_prompt_proibe_ancoragem_consecutiva tests/test_generate_reels.py::test_system_prompt_contem_angulos_narrativos tests/test_generate_reels.py::test_system_prompt_angulos_tem_exemplos -v
```

Esperado: 4 FAILs (SYSTEM_PROMPT atual não tem esses elementos)

- [ ] **Step 3: Reescrever REGRA DA ESPECIFICIDADE no SYSTEM_PROMPT**

Em `content-engine/generate_reels.py`, substituir o bloco (linhas 156–159):

```python
# ANTES:
REGRA DA ESPECIFICIDADE — obrigatório:
Toda cena precisa de pelo menos UM número, horário, nome de app/plataforma, ou dado concreto.
❌ "fica muito tempo no celular"
✅ "23h47. Décimo quarto vídeo de um cachorro que você não conhece."
```

pelo bloco:

```python
REGRA DA ESPECIFICIDADE — obrigatório:
Toda cena precisa de pelo menos UM dado de ancoragem. Varie o TIPO — nunca o mesmo tipo em duas cenas seguidas:
- HORÁRIO: "23h47", "terça às 14h37"
- QUANTIDADE: "14 vezes", "R$ 47,90", "3 semanas"
- PLATAFORMA/OBJETO: "no Stories", "Google Sheets", "grupo do trabalho"
- CITAÇÃO EXATA (fictícia): "'tô chegando' — quarta vez seguida"
- COMPARAÇÃO ABSURDA: "tempo suficiente para assistir O Urso inteiro"
- COMPORTAMENTO MENSURADO: "viu stories de 8 pessoas, respondeu zero"
❌ Cena 2: horário | Cena 3: horário | Cena 4: horário  (monotonia proibida)
✅ Cena 2: horário | Cena 3: quantidade | Cena 4: comportamento mensurado
```

- [ ] **Step 4: Adicionar ÂNGULOS NARRATIVOS ao SYSTEM_PROMPT**

Após a `REGRA DO VEREDICTO PRINTÁVEL` (linha 175, antes da `REGRA: Responda SOMENTE com JSON`), inserir:

```python
ÂNGULOS NARRATIVOS — varie por cena, nunca o mesmo ângulo consecutivo:
- FORENSE: cataloga como perito. "Examinados os registros: 47 mensagens, zero respostas."
- SOCIOLÓGICO: padrão comportamental. "Brasileiro não termina. Ele some até o outro entender."
- COMPARATIVO: absurdo equivalente. "Suficiente para assistir O Urso do início ao fim."
- DOCUMENTAL: lê do processo. "Consta nos autos: 3 stories postados durante o vácuo."
- RETROSPECTIVO: começa no desfecho. "O processo começa na sexta. Ou no mês passado."
```

- [ ] **Step 5: Atualizar o exemplo no prompt do usuário**

No `gerar_roteiro()`, substituir a cena 2 do EXEMPLO CORRETO (linha 242) por um exemplo que usa QUANTIDADE em vez de horário, para não reforçar horário como padrão:

```python
# ANTES (cena 2 do exemplo):
{{"numero": 2, "texto": "Quarta-feira, 14h37. Reunião do Teams. Câmera desligada.", "texto_slide": "Na reunião do Teams, câmera desligada.\\nVocê estava no quarto vídeo do Instagram."}},

# DEPOIS:
{{"numero": 2, "texto": "Quarta-feira, reunião do Teams. Câmera desligada. Quarto vídeo do Instagram.", "texto_slide": "Na reunião do Teams, câmera desligada.\\nVocê estava no quarto vídeo do Instagram."}},
```

E atualizar a cena 3 do exemplo para usar COMPARAÇÃO ABSURDA:

```python
# ANTES:
{{"numero": 3, "texto": "Você estava no quarto vídeo do feed falando 'tô aqui' a cada 8 minutos.", "texto_slide": "Enquanto fingia trabalhar,\\ndigitou 'tô aqui' 11 vezes. O feed não perdoou."}},

# DEPOIS:
{{"numero": 3, "texto": "Você estava no quarto vídeo do feed. Tempo suficiente para assistir O Urso inteiro, se quisesse.", "texto_slide": "Tempo de tela na reunião: zero.\\nTempo no Instagram: suficiente para um episódio inteiro."}},
```

- [ ] **Step 6: Rodar os testes novamente**

```
cd content-engine
pytest tests/test_generate_reels.py -v --ignore=tests/webhook/test_server.py
```

Esperado: todos passando (incluindo os 4 novos)

- [ ] **Step 7: Commit**

```bash
git add content-engine/generate_reels.py content-engine/tests/test_generate_reels.py
git commit -m "feat: reescrever REGRA DA ESPECIFICIDADE + adicionar ÂNGULOS NARRATIVOS ao SYSTEM_PROMPT"
```

---

## Task 2: Implementar gerar_glossario() em generate_reels.py

**Files:**
- Modify: `content-engine/generate_reels.py`
- Test: `content-engine/tests/test_generate_reels.py`

### Contexto

O "Glossário da Dra. Julga" é um novo tipo de post: a Dra. define um termo inventado sobre comportamentos relacionais (ex: "afetofobia seletiva"). O JSON resultante tem estrutura completamente diferente do carrossel — sem `cenas`, com campos semânticos próprios. A geração usa o mesmo `claude_client` e o mesmo `SYSTEM_PROMPT`, mas com um `prompt` de usuário inteiramente diferente. Salva em `YYYY-MM-DD_<cat>_glossario.json`.

**JSON de saída esperado:**
```json
{
  "formato_post": "glossario",
  "categoria": "amor",
  "termo": "afetofobia seletiva",
  "pronuncia": "a·fe·to·fo·bi·a  se·le·ti·va",
  "classe_gramatical": "substantivo feminino",
  "definicao": "Incapacidade de demonstrar afeto — mas só com quem gosta de verdade.",
  "manifestacao": "Sumiços estratégicos. Mensagens frias logo depois de noites boas.",
  "nao_confundir": "Não confundir com timidez. Tímido não some. Tímido demora.",
  "frase_exemplo": "Ele só é assim comigo. Com os outros ele é super carinhoso.",
  "veredicto": "Culpado de fugir do que mais quer. Pena: ficar com quem não teme.",
  "legenda_instagram": "...",
  "sugestao_musica": "..."
}
```

- [ ] **Step 1: Escrever os testes**

Adicionar ao final de `content-engine/tests/test_generate_reels.py`:

```python
# ── Glossário ──────────────────────────────────────────────────────────────────

def _glossario_valido():
    """Fixture: glossário mínimo válido para testes."""
    return {
        "formato_post": "glossario",
        "categoria": "amor",
        "termo": "afetofobia seletiva",
        "pronuncia": "a·fe·to·fo·bi·a  se·le·ti·va",
        "classe_gramatical": "substantivo feminino",
        "definicao": "Incapacidade de demonstrar afeto — mas só com quem gosta de verdade.",
        "manifestacao": "Sumiços estratégicos. Mensagens frias logo depois de noites boas.",
        "nao_confundir": "Não confundir com timidez. Tímido não some. Tímido demora.",
        "frase_exemplo": "Ele só é assim comigo. Com os outros ele é super carinhoso.",
        "veredicto": "Culpado de fugir do que mais quer. Pena: ficar com quem não teme.",
        "legenda_instagram": "#draJulga #glossario",
        "sugestao_musica": "lo-fi introspectivo",
    }


def test_validar_glossario_valido_retorna_none():
    assert gr._validar_glossario(_glossario_valido()) is None


def test_validar_glossario_rejeita_campo_ausente():
    g = _glossario_valido()
    del g["definicao"]
    resultado = gr._validar_glossario(g)
    assert resultado is not None
    assert "definicao" in resultado


def test_validar_glossario_rejeita_jargao_medico():
    g = _glossario_valido()
    g["definicao"] = "Síndrome do abandono afetivo crônico."
    resultado = gr._validar_glossario(g)
    assert resultado is not None
    assert "síndrome" in resultado.lower()


def test_validar_glossario_rejeita_veredicto_longo():
    g = _glossario_valido()
    g["veredicto"] = "Culpado de uma série de comportamentos extremamente duvidosos que demonstram total falta de capacidade de amar alguém de verdade sem fugir."
    resultado = gr._validar_glossario(g)
    assert resultado is not None
    assert "veredicto" in resultado.lower()


def test_gerar_glossario_chama_api_e_retorna_dict(monkeypatch, tmp_path):
    glossario_mock = _glossario_valido()

    def mock_create(**kwargs):
        mock_resp = MagicMock()
        mock_resp.content[0].text = json.dumps(glossario_mock)
        return mock_resp

    monkeypatch.setattr(gr.claude_client.messages, "create", mock_create)
    resultado = gr.gerar_glossario("amor", pasta=tmp_path)

    assert resultado["formato_post"] == "glossario"
    assert resultado["termo"] == "afetofobia seletiva"


def test_salvar_glossario_cria_json(tmp_path):
    g = _glossario_valido()
    arquivo = gr.salvar_glossario(g, tmp_path)
    assert arquivo.exists()
    with open(arquivo, encoding="utf-8") as f:
        data = json.load(f)
    assert data["termo"] == g["termo"]
```

- [ ] **Step 2: Rodar para confirmar que falham**

```
cd content-engine
pytest tests/test_generate_reels.py::test_validar_glossario_valido_retorna_none tests/test_generate_reels.py::test_gerar_glossario_chama_api_e_retorna_dict -v
```

Esperado: FAIL com `AttributeError: module 'generate_reels' has no attribute '_validar_glossario'`

- [ ] **Step 3: Implementar _validar_glossario()**

Adicionar em `content-engine/generate_reels.py`, logo após `_validar_roteiro()` (depois da linha 142):

```python
_CAMPOS_GLOSSARIO = [
    "formato_post", "categoria", "termo", "pronuncia", "classe_gramatical",
    "definicao", "manifestacao", "nao_confundir", "frase_exemplo", "veredicto",
]


def _validar_glossario(glossario: dict) -> str | None:
    """Valida glossário gerado. Retorna None se válido, mensagem de erro se inválido."""
    for campo in _CAMPOS_GLOSSARIO:
        if not glossario.get(campo):
            return f"Campo '{campo}' ausente ou vazio no glossário."

    for palavra in ("diagnóstico", "síndrome", "transtorno", "patologia"):
        for campo in ("definicao", "manifestacao", "nao_confundir"):
            if palavra in glossario.get(campo, "").lower():
                return f"Campo '{campo}' contém '{palavra}' — usar vocabulário jurídico, não médico."

    palavras_veredicto = len(glossario.get("veredicto", "").split())
    if palavras_veredicto > 25:
        return (
            f"Veredicto tem {palavras_veredicto} palavras — máximo é 25. "
            "Encurtar para ficar printável."
        )

    return None
```

- [ ] **Step 4: Implementar gerar_glossario()**

Adicionar após `salvar_roteiro()` em `content-engine/generate_reels.py`:

```python
_GLOSSARIO_USER_PROMPT = """Crie uma entrada do Glossário da Dra. Julga para a categoria "{label}".

Invente um termo em português que nomeia um comportamento relacionalmente problemático mas muito comum nessa categoria.
O termo deve soar "técnico" mas ser completamente fictício — combine palavras reais de forma absurda (ex: "afetofobia seletiva", "procrastinação afetiva crônica", "ghosting por osmose").

Responda SOMENTE com este JSON:
{{
  "formato_post": "glossario",
  "categoria": "{categoria}",
  "termo": "o termo inventado em letras minúsculas",
  "pronuncia": "sí·la·bas  se·pa·ra·das  por  ponto·médio  (use espaço duplo entre palavras)",
  "classe_gramatical": "substantivo feminino | substantivo masculino | adjetivo",
  "definicao": "definição de 1-2 frases: o que é, com ironia fria. Máx 30 palavras.",
  "manifestacao": "como se manifesta na prática: 2-3 comportamentos específicos em frases curtas. Máx 35 palavras.",
  "nao_confundir": "com o que não confundir: diferença afiada em 2 frases. Máx 25 palavras.",
  "frase_exemplo": "uma frase que alguém diria quando sofre isso. Em primeira pessoa. Máx 20 palavras.",
  "veredicto": "veredicto da Dra. Julga em 1-2 frases. Máx 25 palavras. Inclui 'pena:' com punição irônica.",
  "legenda_instagram": "legenda com o termo + definição resumida + hashtags (máx 150 chars)",
  "sugestao_musica": "estilo musical sugerido"
}}"""


def gerar_glossario(categoria: str, pasta: Path = None) -> dict:
    """Gera entrada do Glossário da Dra. Julga para uma categoria."""
    if pasta is None:
        pasta = Path(__file__).parent / "generated" / "reels"

    info = CATEGORIAS_INFO.get(categoria, {"label": categoria, "emoji": "⚖️"})
    prompt = _GLOSSARIO_USER_PROMPT.format(categoria=categoria, label=info["label"])

    prompt_atual = prompt
    for tentativa in range(1, 3):
        resposta = claude_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt_atual}]
        )

        texto = resposta.content[0].text.strip()
        texto = texto.replace("```json", "").replace("```", "").strip()
        try:
            glossario = json.loads(texto)
        except json.JSONDecodeError as e:
            print(f"⚠️  Tentativa {tentativa}/2 — JSON inválido: {e}")
            if tentativa < 2:
                prompt_atual = prompt + "\n\nATENÇÃO — resposta anterior não era JSON válido. Responda SOMENTE com JSON."
            glossario = {}
            continue

        erro = _validar_glossario(glossario)
        if erro is None:
            return glossario

        print(f"⚠️  Tentativa {tentativa}/2 — glossário rejeitado: {erro}")
        if tentativa < 2:
            prompt_atual = prompt + f"\n\nATENÇÃO — resposta anterior foi rejeitada:\n{erro}\nCorrija e responda com JSON válido."

    print("⚠️  Usando glossário da tentativa 2 sem aprovação — verificar manualmente.")
    return glossario


def salvar_glossario(glossario: dict, pasta: Path) -> Path:
    """Salva glossário em JSON. Retorna o Path do arquivo."""
    hoje = datetime.now().strftime("%Y-%m-%d")
    categoria = glossario.get("categoria", "geral")
    arquivo = pasta / f"{hoje}_{categoria}_glossario.json"
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(glossario, f, ensure_ascii=False, indent=2)
    return arquivo
```

- [ ] **Step 5: Rodar todos os testes**

```
cd content-engine
pytest tests/test_generate_reels.py -v --ignore=tests/webhook/test_server.py
```

Esperado: todos passando

- [ ] **Step 6: Commit**

```bash
git add content-engine/generate_reels.py content-engine/tests/test_generate_reels.py
git commit -m "feat: adicionar gerar_glossario() e _validar_glossario() em generate_reels"
```

---

## Task 3: Renderização dos slides do Glossário em gerar_carrossel.py

**Files:**
- Modify: `content-engine/gerar_carrossel.py`
- Create: `content-engine/tests/test_gerar_carrossel.py`

### Contexto

O Glossário precisa de 6 slides com layout diferente do carrossel:
- Slide 1 (capa): "GLOSSÁRIO" badge + termo grande + pronuncia + classe gramatical
- Slide 2: "DEFINIÇÃO" badge + texto da definição
- Slide 3: "COMO SE MANIFESTA" badge + texto da manifestação  
- Slide 4: "NÃO CONFUNDIR COM" badge + texto
- Slide 5: "USADO EM FRASE" badge + frase em aspas (estilo citação)
- Slide 6: veredicto da Dra. Julga + CTA (igual ao slide de veredicto atual)

Os slides usam `base_slide()` e o mesmo design system (cores, fontes, `_desenhar_dots()`). Salvam em `YYYY-MM-DD_<cat>_glossario_slide_0N.png`.

- [ ] **Step 1: Criar o arquivo de testes**

Criar `content-engine/tests/test_gerar_carrossel.py`:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from pathlib import Path
import gerar_carrossel as gc


def _glossario_valido():
    return {
        "formato_post": "glossario",
        "categoria": "amor",
        "termo": "afetofobia seletiva",
        "pronuncia": "a·fe·to·fo·bi·a  se·le·ti·va",
        "classe_gramatical": "substantivo feminino",
        "definicao": "Incapacidade de demonstrar afeto — mas só com quem gosta de verdade.",
        "manifestacao": "Sumiços estratégicos. Mensagens frias logo depois de noites boas.",
        "nao_confundir": "Não confundir com timidez. Tímido não some. Tímido demora.",
        "frase_exemplo": "Ele só é assim comigo. Com os outros ele é super carinhoso.",
        "veredicto": "Culpado de fugir do que mais quer. Pena: ficar com quem não teme.",
        "legenda_instagram": "#draJulga #glossario",
        "sugestao_musica": "lo-fi",
    }


def test_gerar_slides_glossario_cria_6_arquivos(tmp_path):
    glossario = _glossario_valido()
    slides = gc.gerar_slides_glossario(glossario, tmp_path, "2026-04-08")
    assert len(slides) == 6
    for p in slides:
        assert p.exists(), f"Slide não criado: {p}"


def test_gerar_slides_glossario_nomenclatura_correta(tmp_path):
    glossario = _glossario_valido()
    slides = gc.gerar_slides_glossario(glossario, tmp_path, "2026-04-08")
    nomes = [p.name for p in slides]
    assert "2026-04-08_amor_glossario_slide_01.png" in nomes
    assert "2026-04-08_amor_glossario_slide_06.png" in nomes


def test_slide_glossario_capa_retorna_imagem():
    from PIL import Image
    glossario = _glossario_valido()
    img = gc.slide_glossario_capa(glossario, 1, 6)
    assert isinstance(img, Image.Image)
    assert img.size == (1080, 1080)


def test_slide_glossario_conteudo_retorna_imagem():
    from PIL import Image
    img = gc.slide_glossario_conteudo("DEFINIÇÃO", "Texto de teste.", 2, 6)
    assert isinstance(img, Image.Image)
    assert img.size == (1080, 1080)
```

- [ ] **Step 2: Rodar para confirmar que falham**

```
cd content-engine
pytest tests/test_gerar_carrossel.py -v
```

Esperado: FAIL com `AttributeError: module 'gerar_carrossel' has no attribute 'gerar_slides_glossario'`

- [ ] **Step 3: Implementar slide_glossario_capa()**

Adicionar em `content-engine/gerar_carrossel.py`, após a função `slide_veredicto()` (após linha 483):

```python
def slide_glossario_capa(glossario: dict, numero: int, total: int) -> Image.Image:
    """Slide 1 do Glossário: capa com o termo em destaque."""
    img, draw = base_slide()
    cx = LARGURA // 2

    # Contador sutil
    fonte_num = encontrar_fonte(22, bold=False)
    draw.text((cx, 30), f"{numero}/{total}", font=fonte_num,
              fill=CINZA_MEDIO, anchor="mt")

    # Badge "GLOSSÁRIO DA DRA. JULGA"
    fonte_badge = encontrar_fonte(28, bold=True)
    badge_txt = "GLOSSÁRIO DA DRA. JULGA"
    badge_bbox = draw.textbbox((0, 0), badge_txt, font=fonte_badge)
    bw = badge_bbox[2] - badge_bbox[0]
    bh = badge_bbox[3] - badge_bbox[1]
    pad_h, pad_v = 28, 12
    draw.rounded_rectangle(
        [cx - bw // 2 - pad_h, 110 - bh // 2 - pad_v,
         cx + bw // 2 + pad_h, 110 + bh // 2 + pad_v],
        radius=24, fill=ROXO_VIBRANTE
    )
    draw.text((cx, 110), badge_txt, font=fonte_badge,
              fill=BRANCO_PURO, anchor="mm")

    # Linha dourada
    draw.rectangle([cx - 140, 160, cx + 140, 165], fill=DOURADO)

    # Termo em destaque — auto-reduz se muito longo
    termo = glossario.get("termo", "")
    fonte_termo = encontrar_fonte(36, bold=True)
    for sz in range(80, 32, -4):
        f = encontrar_fonte(sz, bold=True)
        bbox = draw.textbbox((0, 0), termo, font=f)
        if (bbox[2] - bbox[0]) <= 960:
            fonte_termo = f
            break

    draw.text((cx, 480), termo, font=fonte_termo,
              fill=ROXO_PROFUNDO, anchor="mm")

    # Linha dourada abaixo do termo
    draw.rectangle([cx - 100, 535, cx + 100, 539], fill=DOURADO)

    # Pronúncia
    pronuncia = glossario.get("pronuncia", "")
    if pronuncia:
        fonte_pron = encontrar_fonte(30, bold=False)
        draw.text((cx, 590), pronuncia, font=fonte_pron,
                  fill=CINZA_MEDIO, anchor="mm")

    # Classe gramatical
    classe = glossario.get("classe_gramatical", "")
    if classe:
        fonte_classe = encontrar_fonte(28, bold=False)
        draw.text((cx, 640), classe, font=fonte_classe,
                  fill=ROXO_BORDA, anchor="mm")

    # Badge "Deslize"
    fonte_deslize = encontrar_fonte(28, bold=False)
    draw.rounded_rectangle([180, 800, LARGURA - 180, 858],
                            radius=30, fill=None,
                            outline=ROXO_VIBRANTE, width=2)
    draw.text((cx, 829), "Deslize para a definição  >>>",
              font=fonte_deslize, fill=ROXO_VIBRANTE, anchor="mm")

    # Rodapé
    fonte_footer = encontrar_fonte(22, bold=False)
    draw.text((cx, ALTURA - 28), "@dra.julga  •  mejulga.com.br",
              font=fonte_footer, fill=CINZA_MEDIO, anchor="mm")

    _desenhar_dots(draw, numero, total)
    return img
```

- [ ] **Step 4: Implementar slide_glossario_conteudo()**

Adicionar após `slide_glossario_capa()`:

```python
def slide_glossario_conteudo(label: str, texto: str,
                              numero: int, total: int) -> Image.Image:
    """Slides 2-5 do Glossário: label badge + texto centralizado."""
    img, draw = base_slide()
    cx = LARGURA // 2

    # Contador sutil
    fonte_num = encontrar_fonte(22, bold=False)
    draw.text((cx, 28), f"{numero}/{total}", font=fonte_num,
              fill=CINZA_MEDIO, anchor="mt")

    # Label badge
    fonte_lbl = encontrar_fonte(30, bold=True)
    lbl_bbox = draw.textbbox((0, 0), label, font=fonte_lbl)
    lbl_w = lbl_bbox[2] - lbl_bbox[0]
    lbl_h = lbl_bbox[3] - lbl_bbox[1]
    pad_h, pad_v = 28, 12
    draw.rounded_rectangle(
        [cx - lbl_w // 2 - pad_h, 78 - lbl_h // 2 - pad_v,
         cx + lbl_w // 2 + pad_h, 78 + lbl_h // 2 + pad_v],
        radius=24, fill=CINZA_SUAVE, outline=ROXO_VIBRANTE, width=2
    )
    draw.text((cx, 78), label, font=fonte_lbl, fill=ROXO_VIBRANTE, anchor="mm")

    # Linha divisória
    draw.rectangle([80, 122, LARGURA - 80, 124], fill=CINZA_SUAVE)

    # Texto — word-wrap centralizado com fonte auto-reduzida
    max_w = 900
    zona_top, zona_bot = 150, ALTURA - 120

    for sz in range(68, 28, -4):
        fonte_txt = encontrar_fonte(sz, bold=False)
        palavras = texto.split()
        linhas = []
        linha_atual = []
        for palavra in palavras:
            linha_atual.append(palavra)
            bbox = draw.textbbox((0, 0), " ".join(linha_atual), font=fonte_txt)
            if (bbox[2] - bbox[0]) > max_w and len(linha_atual) > 1:
                linhas.append(" ".join(linha_atual[:-1]))
                linha_atual = [palavra]
        if linha_atual:
            linhas.append(" ".join(linha_atual))

        bbox_s = draw.textbbox((0, 0), "Ag", font=fonte_txt)
        line_h = int((bbox_s[3] - bbox_s[1]) * 1.5)
        total_h = len(linhas) * line_h
        if total_h <= (zona_bot - zona_top):
            break

    y = zona_top + (zona_bot - zona_top - total_h) // 2
    for linha in linhas:
        draw.text((cx, y), linha, font=fonte_txt,
                  fill=ROXO_PROFUNDO, anchor="mm")
        y += line_h

    _desenhar_dots(draw, numero, total)

    fonte_footer = encontrar_fonte(20, bold=False)
    draw.text((cx, ALTURA - 16), "@dra.julga",
              font=fonte_footer, fill=CINZA_MEDIO, anchor="mm")

    return img
```

- [ ] **Step 5: Implementar gerar_slides_glossario()**

Adicionar após `slide_glossario_conteudo()`:

```python
def gerar_slides_glossario(glossario: dict, pasta: Path, hoje: str) -> list[Path]:
    """Gera 6 slides PNG para o Glossário. Retorna lista de Paths."""
    categoria = glossario.get("categoria", "geral")
    total = 6
    slides = []

    def salvar(img: Image.Image, n: int) -> Path:
        p = pasta / f"{hoje}_{categoria}_glossario_slide_0{n}.png"
        img.save(str(p))
        slides.append(p)
        return p

    print(f"  Slide 1/6 — capa ({glossario.get('termo', '')})")
    salvar(slide_glossario_capa(glossario, 1, total), 1)

    conteudos = [
        ("DEFINIÇÃO",        glossario.get("definicao", "")),
        ("COMO SE MANIFESTA", glossario.get("manifestacao", "")),
        ("NÃO CONFUNDIR COM", glossario.get("nao_confundir", "")),
        ("USADO EM FRASE",   f'"{glossario.get("frase_exemplo", "")}"'),
    ]
    for i, (label, texto) in enumerate(conteudos, start=2):
        print(f"  Slide {i}/6 — {label.lower()}")
        salvar(slide_glossario_conteudo(label, texto, i, total), i)

    print("  Slide 6/6 — veredicto")
    veredicto = glossario.get("veredicto", "Sem apelação.")
    salvar(slide_veredicto(veredicto, 6, total), 6)

    return slides
```

- [ ] **Step 6: Adicionar carregar_glossario() e atualizar main()**

Adicionar após `carregar_roteiro()` em `content-engine/gerar_carrossel.py`:

```python
def carregar_glossario(categoria: str, data: str) -> dict:
    pasta = Path(__file__).parent / "generated" / "reels"
    arquivo = pasta / f"{data}_{categoria}_glossario.json"
    if not arquivo.exists():
        raise FileNotFoundError(f"Glossário não encontrado: {arquivo}")
    with open(arquivo, "r", encoding="utf-8") as f:
        return json.load(f)
```

Atualizar `main()` em `gerar_carrossel.py` para suportar `--formato`:

```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categoria", required=True, choices=CATEGORIAS)
    parser.add_argument("--data", default=None)
    parser.add_argument("--formato", default="carrossel",
                        choices=["carrossel", "glossario"],
                        help="Tipo de post a renderizar")
    args = parser.parse_args()

    hoje = args.data or datetime.now().strftime("%Y-%m-%d")
    pasta_saida = Path(__file__).parent / "generated" / "reels"
    pasta_saida.mkdir(parents=True, exist_ok=True)

    if args.formato == "glossario":
        print(f"Glossário — {args.categoria} — {hoje}")
        glossario = carregar_glossario(args.categoria, hoje)
        slides = gerar_slides_glossario(glossario, pasta_saida, hoje)
        print(f"\nSlides gerados em {pasta_saida}")
        for s in slides:
            print(f"   {s.name}")
        return slides

    # ... resto do main() atual (carrossel) inalterado ...
```

> **Nota:** O corpo do `main()` existente (carrossel) permanece intacto abaixo do bloco `if args.formato == "glossario"`. Apenas adicionar o parâmetro `--formato` ao parser e o bloco `if` antes do código existente.

- [ ] **Step 7: Rodar todos os testes**

```
cd content-engine
pytest tests/test_gerar_carrossel.py tests/test_generate_reels.py -v --ignore=tests/webhook/test_server.py
```

Esperado: todos passando

- [ ] **Step 8: Commit**

```bash
git add content-engine/gerar_carrossel.py content-engine/tests/test_gerar_carrossel.py
git commit -m "feat: adicionar gerar_slides_glossario() e suporte a --formato glossario no carrossel"
```

---

## Task 4: Expor gerar_glossario via CLI e smoke test manual

**Files:**
- Modify: `content-engine/generate_reels.py` (função `main()`)

### Contexto

O `gerar_glossario()` precisa ser chamável via linha de comando (`python generate_reels.py --formato glossario --categoria amor`) para que o workflow do GitHub Actions possa usá-lo futuramente. Adicionar a flag `--formato` ao `main()` existente.

- [ ] **Step 1: Adicionar --formato ao main() de generate_reels.py**

Localizar `main()` em `generate_reels.py` (linha 399) e atualizar:

```python
def main():
    parser = argparse.ArgumentParser(description="Gera roteiro e áudio de Reels da Dra. Julga")
    parser.add_argument("--categoria", default="dinheiro",
                        choices=list(CATEGORIAS_INFO.keys()),
                        help="Categoria do post")
    parser.add_argument("--formato", default="carrossel",
                        choices=["carrossel", "glossario"],
                        help="Tipo de post a gerar")
    parser.add_argument("--sem_audio", action="store_true",
                        help="Gera só o roteiro sem o áudio")
    args = parser.parse_args()

    pasta = Path(__file__).parent / "generated" / "reels"
    pasta.mkdir(parents=True, exist_ok=True)

    if args.formato == "glossario":
        print(f"📖 Gerando Glossário — categoria: {args.categoria}")
        glossario = gerar_glossario(args.categoria, pasta=pasta)
        arquivo = salvar_glossario(glossario, pasta)
        print(f"\n✅ Glossário salvo em: {arquivo}")
        print(f"   Termo: {glossario.get('termo', '')}")
        print(f"   Veredicto: {glossario.get('veredicto', '')}")
        return

    # Fluxo original do carrossel
    print(f"🎬 Gerando roteiro de Reels — categoria: {args.categoria}")
    # ... resto do main() existente inalterado ...
```

> **Nota:** O bloco `if args.formato == "glossario"` vai ANTES do `print("🎬 Gerando roteiro...")` existente. Todo o resto do `main()` fica intacto.

- [ ] **Step 2: Rodar todos os testes da suite**

```
cd content-engine
pytest tests/test_generate_reels.py tests/test_gerar_carrossel.py -v --ignore=tests/webhook/test_server.py
```

Esperado: todos passando

- [ ] **Step 3: Smoke test manual (requer ANTHROPIC_API_KEY)**

```bash
cd content-engine
python generate_reels.py --formato glossario --categoria amor
```

Esperado: arquivo `generated/reels/YYYY-MM-DD_amor_glossario.json` criado com termo inventado.

```bash
python gerar_carrossel.py --categoria amor --formato glossario
```

Esperado: 6 arquivos `YYYY-MM-DD_amor_glossario_slide_0N.png` criados.

- [ ] **Step 4: Commit final**

```bash
git add content-engine/generate_reels.py
git commit -m "feat: expor --formato glossario no CLI de generate_reels"
```
