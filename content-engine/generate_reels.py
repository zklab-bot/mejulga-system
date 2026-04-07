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


def _sorteio_veredicto() -> str:
    """Sorteia o tipo de veredicto com pesos 60/25/15."""
    return random.choices(["A", "B", "C"], weights=[60, 25, 15])[0]


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


# ─── Geração do roteiro ───────────────────────────────────────────────────────

def gerar_roteiro(categoria: str, tipo_veredicto: str = None, pasta: Path = None) -> dict:
    """Gera roteiro de Reels em cenas curtas com veredicto jurídico."""

    if tipo_veredicto is None:
        tipo_veredicto = _sorteio_veredicto()
    if pasta is None:
        pasta = Path(__file__).parent / "generated" / "reels"

    numero_processo = _calcular_numero_processo(categoria, pasta)
    info = CATEGORIAS_INFO.get(categoria, {"label": categoria, "emoji": "⚖️"})

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


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Gera roteiro e áudio de Reels da Dra. Julga")
    parser.add_argument("--categoria", default="dinheiro",
                        choices=list(CATEGORIAS_INFO.keys()),
                        help="Categoria do Reels")
    parser.add_argument("--sem_audio", action="store_true",
                        help="Gera só o roteiro sem o áudio")
    args = parser.parse_args()

    print(f"🎬 Gerando roteiro de Reels — categoria: {args.categoria}")

    # Pasta de saída
    pasta = Path(__file__).parent / "generated" / "reels"
    pasta.mkdir(parents=True, exist_ok=True)

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
