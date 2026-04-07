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


SYSTEM_PROMPT = """Você é a Dra. Julga — psicóloga fictícia sarcástica que diagnostica situações absurdas da vida brasileira com precisão clínica e humor cortante.

Tom: sarcástico, engraçado, identificável, nunca cruel.
Linguagem: português brasileiro informal, frases curtas e impactantes.

ESTRATÉGIAS DE VIRALIZAÇÃO:

1. ARQUÉTIPO RECONHECÍVEL — o caso deve descrever um tipo específico de pessoa que todo mundo conhece. Não "quem fica no celular" mas "quem diz que vai dormir às 22h e dorme às 2h no 14º vídeo de cachorro".

2. ESPECIFICIDADE DEVASTADORA — números, horários e detalhes concretos são mais engraçados que generalizações:
   ❌ "fica muito tempo no celular"
   ✅ "23h47. Você disse que ia dormir cedo. Está no 14º vídeo de um cachorro que não conhece."

3. SLIDE 4 = A PROVA CONTRADITÓRIA — o agravante deve ser a evidência mais absurda e irônica do caso. A virada que transforma "triste" em "ridículo". Deve ser um comportamento que contradiz diretamente a desculpa usada.

4. DIAGNÓSTICO CLÍNICO ABSURDO — fórmula obrigatória: [adjetivo clínico inventado] + [comportamento trivial] + [detalhe temporal/frequência]:
   ❌ "Diagnóstico: viciado em celular."
   ✅ "Diagnóstico: dopaminergência digital com recaída noturna compulsiva."
   ✅ "Diagnóstico: síndrome do cancelamento periódico com remissão falsa às sextas."

5. MECÂNICA DE TAG — o caso deve ter um arquétipo tão claro que a pessoa pensa imediatamente em alguém e taga. Cada slide precisa funcionar como prova num processo judicial: frio, específico, devastador.

PRINCÍPIOS PARA texto_slide (cards visuais):
- Frase COMPLETA e autossuficiente — funciona sem ver os outros slides
- PROIBIDO começar com conectores: "Aí", "Mas", "Pior:", "E então", "Por isso"
- Máx 2 linhas, 80 caracteres por linha
- Segunda pessoa direta ("Você", "Sua") — acusação, não narração
- Estrutura ideal: FATO FRIO.\nDETALHE ABSURDO. (duas sentenças, quebra de linha)

REGRA: Responda SOMENTE com JSON válido, sem texto fora dele."""


# ─── Geração do roteiro ───────────────────────────────────────────────────────

def gerar_roteiro(categoria: str) -> dict:
    """Gera roteiro de Reels em cenas curtas."""

    info = CATEGORIAS_INFO.get(categoria, {"label": categoria, "emoji": "⚖️"})

    prompt = f"""Crie um roteiro de Reels de 20-25 segundos para a Dra. Julga sobre "{info['label']}".

O roteiro deve ter EXATAMENTE 6 cenas curtas, cada uma com 3-4 segundos de fala.

Estrutura obrigatória:
- Cena 1: Hook — frase de abertura chocante ou curiosa (direto ao ponto)
- Cena 2: Apresentação do caso (situação identificável, específica)
- Cena 3: Detalhe engraçado do caso (o absurdo que piora tudo)
- Cena 4: Agravante (a prova definitiva da culpa)
- Cena 5: Veredicto — diagnóstico específico e criativo + "Sem defesa possível."
- Cena 6: CTA — "Descobre o seu em mejulga.com.br"

Para cada cena gere DOIS textos:
1. `texto`: narração falada para o vídeo (pode ter conectores, flui como fala)
2. `texto_slide`: versão para card visual — frase completa e autossuficiente, sem conectores no início, máx 2 linhas, segunda pessoa direta, específica e devastadora

A Cena 5 vira o `conclusao` (veredicto do slide final) — deve ter diagnóstico inventivo e específico.

Responda SOMENTE com este JSON:
{{
  "categoria": "{categoria}",
  "titulo": "título curto do caso",
  "cenas": [
    {{"numero": 1, "duracao_segundos": 3, "texto": "frase narrada cena 1", "texto_slide": "versão visual cena 1"}},
    {{"numero": 2, "duracao_segundos": 4, "texto": "frase narrada cena 2", "texto_slide": "versão visual cena 2"}},
    {{"numero": 3, "duracao_segundos": 4, "texto": "frase narrada cena 3", "texto_slide": "versão visual cena 3"}},
    {{"numero": 4, "duracao_segundos": 4, "texto": "frase narrada cena 4", "texto_slide": "versão visual cena 4"}},
    {{"numero": 5, "duracao_segundos": 4, "texto": "frase narrada cena 5", "texto_slide": "versão visual cena 5"}},
    {{"numero": 6, "duracao_segundos": 3, "texto": "frase narrada cena 6", "texto_slide": "versão visual cena 6"}}
  ],
  "conclusao": "diagnóstico específico da Cena 5. Sem defesa possível.",
  "texto_completo": "texto corrido de todas as cenas unidas para o áudio",
  "legenda_instagram": "legenda completa para o post do Reels com hashtags",
  "sugestao_musica": "sugestão de estilo musical de fundo (ex: lo-fi calmo, dramático orquestral)"
}}"""

    resposta = claude_client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    texto = resposta.content[0].text.strip()
    texto = texto.replace("```json", "").replace("```", "").strip()
    return json.loads(texto)


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
        f.write(f"ROTEIRO REELS — DRA. JULGA\n")
        f.write(f"Categoria: {categoria.upper()}\n")
        f.write(f"Título: {roteiro.get('titulo', '')}\n")
        f.write(f"Data: {hoje}\n")
        f.write("=" * 50 + "\n\n")

        f.write("CENAS:\n\n")
        for cena in roteiro.get("cenas", []):
            f.write(f"CENA {cena['numero']} ({cena['duracao_segundos']}s)\n")
            f.write(f"  → {cena['texto']}\n\n")

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
