"""
generate_posts.py
Gera 3 posts diários para o Instagram da Dra. Julga usando a Claude API.
Uso: python generate_posts.py
"""

import anthropic
import json
import os
import re
import random
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

CATEGORIAS = ["dinheiro", "amor", "trabalho", "dopamina", "vida_adulta", "social", "saude_mental"]

HASHTAGS = {
    "grupo_a": "#MeJulga #DraJulga #PsicologiaReal #VidaAdulta #Identificação",
    "grupo_b": "#HumorBrasileiro #Viral #RelacionavelDemais #Brasileirices #Cotidiano",
    "grupo_c": "#Autoconhecimento #Psicologia #QuizOnline #JulgamentoGratuito #MeJulgaCom",
}

SYSTEM_PROMPT = """Você é a Dra. Julga — uma psicóloga fictícia sarcástica que diagnostica situações absurdas da vida brasileira cotidiana com linguagem de autoajuda virada do avesso.

SEU TOM:
- Sarcástico mas nunca cruel. A piada é com a situação, não com a pessoa.
- Humor reconhecível, brasileiro, das coisas que todo mundo faz mas ninguém admite.
- Tuteamento, linguagem informal, gírias naturais do português brasileiro.
- Frases curtas. Quebras de linha para ritmo.

REGRA CRÍTICA DE RESPOSTA:
Você deve responder SOMENTE com um objeto JSON válido.
Sem texto antes, sem texto depois, sem explicações, sem markdown, sem blocos de código.
Apenas o JSON puro começando com { e terminando com }.
"""

def extrair_json(texto: str) -> dict:
    texto = texto.strip()
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        pass
    texto_limpo = re.sub(r'```(?:json)?\s*', '', texto).replace('```', '').strip()
    try:
        return json.loads(texto_limpo)
    except json.JSONDecodeError:
        pass
    match = re.search(r'\{.*\}', texto_limpo, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Não foi possível extrair JSON:\n{texto[:300]}")


def gerar_post_tipo1(categoria: str) -> dict:
    prompt = f"""Gere um post de Instagram para a Dra. Julga sobre a categoria "{categoria}".

TIPO: Provocação com pergunta no final
ESTRUTURA:
- 1ª linha: hook forte
- 2-3 linhas: situação identificável
- 1 linha: diagnóstico irônico
- Última linha: pergunta provocadora + emoji

Responda SOMENTE com este JSON sem nenhum texto fora dele:
{{
  "texto": "texto completo do post aqui",
  "hashtags": "{HASHTAGS['grupo_a']} {HASHTAGS['grupo_b']}",
  "tipo": "provocacao",
  "categoria": "{categoria}",
  "horario": "12:00"
}}"""

    r = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )
    return extrair_json(r.content[0].text)


def gerar_post_tipo2(categoria: str, numero_caso: int) -> dict:
    prompt = f"""Gere um post de Instagram para a Dra. Julga sobre a categoria "{categoria}".

TIPO: Caso Clínico número {numero_caso}
ESTRUTURA OBRIGATÓRIA:
- "CASO CLÍNICO Nº {numero_caso}" como primeira linha
- "Paciente, XX anos."
- 3 comportamentos identificáveis
- "Diagnóstico da Dra. Julga:" + diagnóstico irônico
- CTA: "Quer saber o que a Dra. Julga falaria sobre a SUA vida? Link na bio. Se tiver coragem. ⚖️"

Responda SOMENTE com este JSON sem nenhum texto fora dele:
{{
  "texto": "texto completo do post aqui",
  "hashtags": "{HASHTAGS['grupo_a']} {HASHTAGS['grupo_c']}",
  "tipo": "caso_clinico",
  "categoria": "{categoria}",
  "horario": "18:00"
}}"""

    r = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )
    return extrair_json(r.content[0].text)


def gerar_post_tipo3(categoria: str) -> dict:
    prompt = f"""Gere um post de Instagram para a Dra. Julga sobre a categoria "{categoria}".

TIPO: CTA para o site mejulga.com.br
ESTRUTURA OBRIGATÓRIA (use exatamente estas frases na ordem):
1. Situação do dia a dia identificável (1-2 linhas)
2. "Isso diz muito sobre você."
3. "A Dra. Julga tem um diagnóstico completo esperando."
4. "É de graça. É preciso. É constrangedor."
5. "mejulga.com.br — link na bio 🧠"

Responda SOMENTE com este JSON sem nenhum texto fora dele:
{{
  "texto": "texto completo do post aqui",
  "hashtags": "{HASHTAGS['grupo_a']} {HASHTAGS['grupo_c']}",
  "tipo": "cta",
  "categoria": "{categoria}",
  "horario": "21:00"
}}"""

    r = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )
    return extrair_json(r.content[0].text)


def salvar_posts(posts: list) -> str:
    hoje = datetime.now().strftime("%Y-%m-%d")
    pasta = Path("generated")
    pasta.mkdir(exist_ok=True)
    arquivo = pasta / f"{hoje}.json"
    output = {"data": hoje, "gerado_em": datetime.now().isoformat(), "posts": posts}
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    return str(arquivo)


def imprimir_posts(posts: list):
    print("\n" + "="*60)
    print("📱 POSTS DO DIA — DRA. JULGA")
    print("="*60)
    for i, post in enumerate(posts, 1):
        print(f"\n🕐 POST {i} — {post.get('horario')} | {post.get('tipo','').upper()} | #{post.get('categoria')}")
        print("-"*60)
        print(post["texto"])
        print()
        print(post["hashtags"])
        print("-"*60)


def main():
    print("🧠 Gerando posts da Dra. Julga...")
    categorias_hoje = random.sample(CATEGORIAS, 3)
    numero_caso = datetime.now().timetuple().tm_yday
    posts = []

    try:
        print(f"📝 Post 1 (12h) — Provocação [{categorias_hoje[0]}]...")
        posts.append(gerar_post_tipo1(categorias_hoje[0]))
        print("   ✅ OK")

        print(f"📝 Post 2 (18h) — Caso Clínico Nº{numero_caso} [{categorias_hoje[1]}]...")
        posts.append(gerar_post_tipo2(categorias_hoje[1], numero_caso))
        print("   ✅ OK")

        print(f"📝 Post 3 (21h) — CTA [{categorias_hoje[2]}]...")
        posts.append(gerar_post_tipo3(categorias_hoje[2]))
        print("   ✅ OK")

        arquivo = salvar_posts(posts)
        print(f"\n✅ Posts salvos em: {arquivo}")
        imprimir_posts(posts)

    except ValueError as e:
        print(f"❌ Erro ao processar resposta: {e}")
        raise
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        raise


if __name__ == "__main__":
    main()
