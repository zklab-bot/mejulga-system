"""
generate_reels.py
Gera roteiro de Reels + áudio com voz da Dra. Julga via ElevenLabs.
Uso: python generate_reels.py --categoria dinheiro
"""

import anthropic
import os
import json
import argparse
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import random

load_dotenv()

# ─── Configuração ─────────────────────────────────────────────────────────────

claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

CATEGORIAS_INFO = {
    "dinheiro": {"label": "Dinheiro", "emoji": "💸"},
    "amor": {"label": "Amor", "emoji": "💔"},
    "trabalho": {"label": "Trabalho", "emoji": "💼"},
    "dopamina": {"label": "Dopamina", "emoji": "📱"},
    "vida_adulta": {"label": "Vida Adulta", "emoji": "🧠"},
    "social": {"label": "Social", "emoji": "🧍"},
    "saude_mental": {"label": "Saúde Mental", "emoji": "🧘"},
}


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

    # Clamp each weight to minimum 5 after normalization, taking the excess from the largest
    for v in VARIACOES:
        if pesos_norm[v] < 5:
            deficit = 5 - pesos_norm[v]
            pesos_norm[v] = 5
            v_maior = max((x for x in VARIACOES if x != v), key=lambda x: pesos_norm[x])
            pesos_norm[v_maior] -= deficit

    diff = 100 - sum(pesos_norm.values())
    if diff != 0:
        v_maior = max(VARIACOES, key=lambda v: pesos_raw[v])
        pesos_norm[v_maior] += diff

    return [pesos_norm["A"], pesos_norm["B"], pesos_norm["C"]]


def _sorteio_veredicto(post_details: dict = None) -> str:
    """Sorteia o tipo de veredicto com pesos dinâmicos baseados nas notas do dono."""
    pesos = _calcular_pesos_veredicto(post_details or {})
    return random.choices(["A", "B", "C"], weights=pesos)[0]


def _calcular_numero_processo(categoria: str, pasta: Path) -> str:
    """Gera número de processo sequencial por categoria. Ex: AMO-003/26."""
    prefixo = categoria[:3].upper()
    ano = datetime.now().strftime("%y")
    existentes = list(pasta.glob(f"*_{categoria}_reels.json")) if pasta.exists() else []
    numero = len(existentes) + 1
    return f"{prefixo}-{numero:03d}/{ano}"


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


SYSTEM_PROMPT = """Você é a Dra. Julga — juíza fictícia que conduz processos contra comportamentos absurdos do cotidiano brasileiro. Observa, coleta provas e profere veredictos. Voz: fria, forense, levemente entediada de já ter visto tudo. Nunca cruel.

TOM PROIBIDO:
- NUNCA começar com "Gente,"
- NUNCA usar jargão médico: "síndrome", "diagnóstico", "CID", "transtorno", "patologia"
- NUNCA falar como amiga de grupo ou influencer
- NUNCA usar "Sem defesa possível" — só "Sem apelação.", "Improvável." ou "Trânsito em julgado."

VOCABULÁRIO PERMITIDO (usar com parcimônia):
réu/ré, autos, prova, agravante, atenuante negado, reincidência, pena, sentença, culpado, trânsito em julgado, sem apelação, flagrante, dolo

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

REGRA DA ESCALADA — obrigatório:
Cena 3 deve ser mais específica e absurda que Cena 2.
Cena 4 deve contradizer diretamente a desculpa implícita da Cena 2 com prova pior.
Cena 5 deve ser mais curta que Cena 4.

REGRA DO SLIDE AUTOEXPLICATIVO — obrigatório:
texto_slide deve funcionar como acusação completa lida sem áudio. É uma ou duas frases na voz da Dra. Julga — fria, direta — que carregam o humor sozinhas. O leitor do slide não ouve a narração.
NÃO é lista de fatos soltos. É uma sentença acusatória fluida que inclui o contexto da acusação.
❌ slide: "11 vídeos.\n3 comentários em perfis aleatórios." (fragmentos sem contexto — não acusa ninguém)
✅ slide: "Enquanto a mensagem ficava no vácuo:\n11 vídeos. 3 comentários em estranhos." (acusação completa)
❌ slide: "47 minutos.\nSlide que ninguém vai ler." (fragmentos)
✅ slide: "Passou 47 minutos formatando um slide\nque ninguém vai abrir." (sentença fluida)

REGRA DO VEREDICTO PRINTÁVEL — obrigatório:
Cena 5 deve ter no máximo 20 palavras. É a frase que vai virar print e ser mandada no grupo.

ÂNGULOS NARRATIVOS — varie por cena, nunca o mesmo ângulo consecutivo:
- FORENSE: cataloga como perito. "Examinados os registros: 47 mensagens, zero respostas."
- SOCIOLÓGICO: padrão comportamental. "Brasileiro não termina. Ele some até o outro entender."
- COMPARATIVO: absurdo equivalente. "Suficiente para assistir O Urso do início ao fim."
- DOCUMENTAL: lê do processo. "Consta nos autos: 3 stories postados durante o vácuo."
- RETROSPECTIVO: começa no desfecho. "O processo começa na sexta. Ou no mês passado."

REGRA: Responda SOMENTE com JSON válido, sem texto fora dele."""


# ─── Geração do roteiro ───────────────────────────────────────────────────────

def gerar_roteiro(categoria: str, tipo_veredicto: str = None, pasta: Path = None) -> dict:
    """Gera roteiro de Reels em cenas curtas com veredicto jurídico."""

    if tipo_veredicto is None:
        try:
            from engagement.shared import state as _state
            _post_details = _state.load().get("post_details", {})
        except Exception:
            _post_details = {}
        tipo_veredicto = _sorteio_veredicto(_post_details)
    if pasta is None:
        pasta = Path(__file__).parent / "generated" / "reels"

    numero_processo = _calcular_numero_processo(categoria, pasta)
    info = CATEGORIAS_INFO.get(categoria, {"label": categoria, "emoji": "⚖️"})

    # Coleta títulos já usados para esta categoria — evita repetição
    titulos_usados = []
    for arq in sorted(pasta.glob(f"*_{categoria}_reels.json")):
        try:
            with open(arq, encoding="utf-8") as f:
                titulo = json.load(f).get("titulo", "")
            if titulo:
                titulos_usados.append(titulo)
        except Exception:
            pass

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

    aviso_titulos = ""
    if titulos_usados:
        lista = "\n".join(f"- {t}" for t in titulos_usados)
        aviso_titulos = f"\nTÍTULOS JÁ USADOS — não repita nem varie levemente, crie algo completamente diferente:\n{lista}\n"

    prompt = f"""Crie um roteiro de carrossel para a Dra. Julga sobre a categoria "{info['label']}".{aviso_titulos}

EXATAMENTE 6 cenas. Cada cena tem `texto` (narração falada, flui como fala) e `texto_slide` (card visual — frase acusatória completa na voz da Dra. Julga; funciona sozinha sem o áudio. Sem labels, sem títulos, sem "PROVA Nº X").

ESTRUTURA OBRIGATÓRIA:
- Cenas 1, 2, 3 e 4 — ESCALADA: quatro observações sobre o mesmo padrão comportamental, cada uma mais específica e absurda que a anterior. A capa já mostra o processo e o título — NÃO repita "Processo X. Réu: você." aqui. Comece direto na primeira acusação, com dado concreto.
- Cena 5 — VEREDICTO: {instrucao_veredicto}
- Cena 6 — CTA (fixo): texto: "Veja seu processo em mejulga.com.br" | texto_slide: "Veja seu processo.\\nmejulga.com.br"

EXEMPLO CORRETO (categoria: trabalho):
{{
  "cenas": [
    {{"numero": 1, "texto": "Câmera desligada. 4 vídeos do Instagram assistidos durante a call.", "texto_slide": "Câmera desligada na reunião.\\n4 vídeos do Instagram. Ao mesmo tempo."}},
    {{"numero": 2, "texto": "Você estava no feed. Tempo suficiente para assistir O Urso inteiro, se quisesse.", "texto_slide": "Tempo de tela na reunião: zero.\\nTempo no Instagram: suficiente para um episódio inteiro."}},
    {{"numero": 3, "texto": "Passou 47 minutos formatando um slide que ninguém vai ler porque tinha preguiça de começar o relatório.", "texto_slide": "Passou 47 minutos formatando um slide\\nque ninguém vai abrir. O relatório continua em branco."}},
    {{"numero": 4, "texto": "Viu 8 stories depois da call. Não respondeu os 3 pings do gestor. Na mesma janela de tempo.", "texto_slide": "Viu 8 stories depois da call.\\nNão respondeu 3 pings do gestor. Mesma janela."}},
    {{"numero": 5, "texto": "VEREDICTO: Culpado por simulação laboral em ambiente remoto. Reincidente. Sem apelação.", "texto_slide": "VEREDICTO\\nCulpado por simulação laboral.\\nSem apelação."}},
    {{"numero": 6, "texto": "Veja seu processo em mejulga.com.br", "texto_slide": "Veja seu processo.\\nmejulga.com.br"}}
  ]
}}

ANTI-EXEMPLO (não faça isso — categoria: amor):
- ❌ texto cena 1: "Gente, ele não respondeu" (começa com "Gente,")
- ❌ texto cena 5: "Diagnóstico: síndrome do apego ansioso" (jargão médico)
- ❌ texto_slide cena 2 igual ao texto cena 2 com quebra de linha (redundância)
- ❌ texto_slide cena 3: "Domingo.\\nNenhuma mensagem." (fragmentos — não acusam ninguém sozinhos)
- ✅ texto_slide cena 3: "Viu o story às 22h03.\\nNão respondeu 9 mensagens. No mesmo dia." (sentença acusatória completa)

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

    prompt_atual = prompt
    for tentativa in range(1, 3):  # máximo 2 tentativas
        resposta = claude_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt_atual}]
        )

        texto = resposta.content[0].text.strip()
        texto = texto.replace("```json", "").replace("```", "").strip()
        try:
            roteiro = json.loads(texto)
        except json.JSONDecodeError as e:
            erro = f"Resposta não é JSON válido: {e}"
            print(f"⚠️  Tentativa {tentativa}/2 — {erro}")
            if tentativa < 2:
                prompt_atual = (
                    prompt + f"\n\nATENÇÃO — Sua resposta anterior não era JSON válido.\n"
                    "Responda SOMENTE com JSON válido, sem texto antes ou depois."
                )
            roteiro = {}
            continue

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


# ─── Geração de áudio ─────────────────────────────────────────────────────────

def gerar_audio(texto: str, arquivo_saida: Path) -> bool:
    """Gera áudio com a voz da Dra. Julga via ElevenLabs."""

    if not ELEVENLABS_API_KEY or not ELEVENLABS_VOICE_ID:
        print("⚠️  ELEVENLABS_API_KEY ou ELEVENLABS_VOICE_ID não configurados no .env")
        return False

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": texto,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.8,
            "style": 0.3,
            "use_speaker_boost": True
        }
    }

    r = requests.post(url, headers=headers, json=payload)

    if r.status_code == 200:
        with open(arquivo_saida, "wb") as f:
            f.write(r.content)
        return True
    else:
        print(f"❌ Erro ElevenLabs: {r.status_code} — {r.text}")
        return False


# ─── Salvar roteiro ───────────────────────────────────────────────────────────

def salvar_roteiro(roteiro: dict, pasta: Path):
    """Salva o roteiro em JSON e TXT formatado."""

    hoje = datetime.now().strftime("%Y-%m-%d")
    categoria = roteiro.get("categoria", "geral")

    # JSON completo
    arquivo_json = pasta / f"{hoje}_{categoria}_reels.json"
    with open(arquivo_json, "w", encoding="utf-8") as f:
        json.dump(roteiro, f, ensure_ascii=False, indent=2)

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

    return arquivo_json, arquivo_txt


# ─── Glossário da Dra. Julga ──────────────────────────────────────────────────

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


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Gera roteiro e áudio de Reels da Dra. Julga")
    parser.add_argument("--categoria", default="dinheiro",
                        choices=list(CATEGORIAS_INFO.keys()),
                        help="Categoria do Reels")
    parser.add_argument("--sem_audio", action="store_true",
                        help="Gera só o roteiro sem o áudio")
    parser.add_argument("--formato", default="carrossel",
                        choices=["carrossel", "glossario"],
                        help="Tipo de post a gerar")
    args = parser.parse_args()

    # Pasta de saída
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

    print(f"🎬 Gerando roteiro de Reels — categoria: {args.categoria}")

    # Gera roteiro
    print("📝 Gerando roteiro com IA...")
    roteiro = gerar_roteiro(args.categoria)

    # Exibe roteiro
    print("\n" + "=" * 50)
    print(f"🎬 ROTEIRO: {roteiro.get('titulo', '')}")
    print("=" * 50)
    for cena in roteiro.get("cenas", []):
        print(f"\nCENA {cena['numero']} ({cena['duracao_segundos']}s):")
        print(f"  → {cena['texto']}")

    print(f"\n🎵 Música sugerida: {roteiro.get('sugestao_musica', '')}")

    # Salva arquivos
    arquivo_json, arquivo_txt = salvar_roteiro(roteiro, pasta)
    print(f"\n✅ Roteiro salvo em: {arquivo_txt}")

    # Gera áudio
    if not args.sem_audio:
        hoje = datetime.now().strftime("%Y-%m-%d")
        arquivo_audio = pasta / f"{hoje}_{args.categoria}_audio.mp3"
        print(f"\n🎙️ Gerando áudio com ElevenLabs...")
        sucesso = gerar_audio(roteiro.get("texto_completo", ""), arquivo_audio)
        if sucesso:
            print(f"✅ Áudio salvo em: {arquivo_audio}")
        else:
            print("⚠️  Áudio não gerado — verifique as credenciais do ElevenLabs")

    print(f"\n🎬 Roteiro pronto! Importe o áudio e o roteiro no CapCut.")
    print(f"📱 Legenda Instagram gerada e salva no arquivo TXT.")


if __name__ == "__main__":
    main()
