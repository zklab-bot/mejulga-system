"""
instagram_comentarios.py
Comenta automaticamente em posts de páginas específicas (ex: fofoca)
com tom de humor da Dra. Julga — com rate limiting rigoroso para evitar ban.

Estratégia anti-ban:
  - Máximo 3 comentários por sessão
  - Intervalo aleatório entre 8-20 minutos entre comentários
  - Só comenta em posts recentes (< 6 horas)
  - Cooldown de 24h por página alvo
  - Comentários variados via Claude API (nunca repete o mesmo texto)
  - Log completo de ações

Uso:
  python instagram_comentarios.py --dry-run       (simula sem postar)
  python instagram_comentarios.py                  (modo real)
"""

import os
import json
import time
import random
import argparse
import anthropic
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# ─── Configuração de rate limiting ────────────────────────────────────────────

MAX_COMENTARIOS_POR_SESSAO = 3          # nunca mais que isso por execução
INTERVALO_MIN_SEGUNDOS     = 8 * 60     # 8 minutos mínimo entre comentários
INTERVALO_MAX_SEGUNDOS     = 20 * 60    # 20 minutos máximo
COOLDOWN_PAGINA_HORAS      = 24         # horas sem comentar na mesma página
MAX_IDADE_POST_HORAS       = 6          # só comenta em posts com menos de X horas
LOG_FILE = Path(__file__).parent / "generated" / "comentarios_log.json"

# ─── Páginas alvo (Instagram User IDs de contas públicas de fofoca) ───────────
# Preencha com os IDs reais das páginas que quer comentar
# Para descobrir o ID de uma página: GET /{username}?fields=id

PAGINAS_ALVO = [
    # {"id": "INSTAGRAM_USER_ID", "nome": "nome_da_pagina"},
    # Exemplos (substitua pelos IDs reais):
    # {"id": "12345678", "nome": "fofocasbrasil"},
    # {"id": "87654321", "nome": "polemicasbr"},
]


# ─── Carregar/salvar log ──────────────────────────────────────────────────────

def carregar_log() -> dict:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if LOG_FILE.exists():
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"comentarios": [], "cooldowns": {}}


def salvar_log(log: dict):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def pagina_em_cooldown(log: dict, pagina_id: str) -> bool:
    cooldowns = log.get("cooldowns", {})
    if pagina_id not in cooldowns:
        return False
    ultima = datetime.fromisoformat(cooldowns[pagina_id])
    return datetime.now() - ultima < timedelta(hours=COOLDOWN_PAGINA_HORAS)


def registrar_cooldown(log: dict, pagina_id: str):
    log.setdefault("cooldowns", {})[pagina_id] = datetime.now().isoformat()


# ─── Buscar posts recentes de uma página ──────────────────────────────────────

def buscar_posts_recentes(pagina_id: str) -> list:
    """Retorna posts das últimas X horas da página."""
    url = f"https://graph.facebook.com/v19.0/{pagina_id}/media"
    resp = requests.get(url, params={
        "fields": "id,caption,timestamp,media_type",
        "access_token": META_ACCESS_TOKEN,
        "limit": 5,
    })
    if resp.status_code != 200:
        print(f"  ⚠️  Erro ao buscar posts de {pagina_id}: {resp.json()}")
        return []

    posts = resp.json().get("data", [])
    limite = datetime.now() - timedelta(hours=MAX_IDADE_POST_HORAS)
    posts_validos = []
    for post in posts:
        ts = datetime.fromisoformat(post["timestamp"].replace("Z", "+00:00")).replace(tzinfo=None)
        if ts > limite:
            posts_validos.append(post)

    return posts_validos


# ─── Gerar comentário via Claude API ─────────────────────────────────────────

def gerar_comentario(caption: str) -> str:
    """Usa Claude para gerar um comentário humorístico da Dra. Julga."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""Você é a Dra. Julga, psicóloga fictícia e humorística brasileira especialista em 
"julgar" comportamentos de forma cômica e divertida. Você comenta em posts de fofoca 
com diagnósticos engraçados e irônicos, sem ofender ninguém pessoalmente.

Post que você vai comentar:
"{caption[:300]}"

Escreva UM comentário curto (máximo 2 frases, até 150 caracteres) no seu estilo:
- Tom: humor, ironia leve, diagnóstico psicológico fictício
- Sem emojis excessivos (máximo 2)
- Termine com "— Dra. Julga" ou "📋 Dra. Julga"
- NUNCA ataque pessoa específica, só o comportamento
- Deve parecer espontâneo, não robótico

Responda APENAS com o comentário, nada mais."""

    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.content[0].text.strip()


# ─── Postar comentário ────────────────────────────────────────────────────────

def postar_comentario(post_id: str, texto: str, dry_run: bool = False) -> bool:
    if dry_run:
        print(f"  [DRY RUN] Comentaria em post {post_id}: {texto}")
        return True

    url = f"https://graph.facebook.com/v19.0/{post_id}/comments"
    resp = requests.post(url, params={
        "message": texto,
        "access_token": META_ACCESS_TOKEN,
    })

    if resp.status_code == 200:
        comment_id = resp.json().get("id")
        print(f"  ✅ Comentário postado! id={comment_id}")
        return True
    else:
        print(f"  ❌ Erro ao comentar: {resp.json()}")
        return False


# ─── Sessão principal ─────────────────────────────────────────────────────────

def executar_sessao(dry_run: bool = False):
    print(f"\n💬 Sessão de comentários — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   Modo: {'🔵 DRY RUN (sem postar)' if dry_run else '🔴 REAL'}")
    print(f"   Limite: {MAX_COMENTARIOS_POR_SESSAO} comentários/sessão\n")

    if not PAGINAS_ALVO:
        print("⚠️  Nenhuma página alvo configurada.")
        print("   Edite a lista PAGINAS_ALVO no script com os IDs das páginas.")
        return

    log = carregar_log()
    comentarios_feitos = 0

    # Embaralha a ordem das páginas para não ser previsível
    paginas = PAGINAS_ALVO.copy()
    random.shuffle(paginas)

    for pagina in paginas:
        if comentarios_feitos >= MAX_COMENTARIOS_POR_SESSAO:
            print(f"\n🛑 Limite de {MAX_COMENTARIOS_POR_SESSAO} comentários atingido. Encerrando.")
            break

        pagina_id   = pagina["id"]
        pagina_nome = pagina["nome"]

        print(f"📄 Verificando @{pagina_nome}...")

        # Cooldown check
        if pagina_em_cooldown(log, pagina_id):
            ultima = datetime.fromisoformat(log["cooldowns"][pagina_id])
            horas_restantes = COOLDOWN_PAGINA_HORAS - (datetime.now() - ultima).seconds // 3600
            print(f"   ⏸️  Em cooldown — aguardar ~{horas_restantes}h\n")
            continue

        # Buscar posts
        posts = buscar_posts_recentes(pagina_id)
        if not posts:
            print(f"   📭 Nenhum post recente (< {MAX_IDADE_POST_HORAS}h)\n")
            continue

        # Escolhe 1 post aleatório dos recentes
        post = random.choice(posts)
        post_id = post["id"]
        caption = post.get("caption", "")[:300]

        print(f"   📝 Post encontrado: {caption[:60]}...")

        # Verifica se já comentou nesse post
        ja_comentou = any(c["post_id"] == post_id for c in log.get("comentarios", []))
        if ja_comentou:
            print(f"   ♻️  Já comentou nesse post. Pulando.\n")
            continue

        # Gerar comentário
        print(f"   🤖 Gerando comentário da Dra. Julga...")
        try:
            comentario = gerar_comentario(caption)
            print(f"   💬 Comentário: {comentario}")
        except Exception as e:
            print(f"   ❌ Erro ao gerar comentário: {e}")
            continue

        # Postar
        sucesso = postar_comentario(post_id, comentario, dry_run=dry_run)

        if sucesso:
            comentarios_feitos += 1
            log.setdefault("comentarios", []).append({
                "data": datetime.now().isoformat(),
                "pagina_id": pagina_id,
                "pagina_nome": pagina_nome,
                "post_id": post_id,
                "comentario": comentario,
                "dry_run": dry_run,
            })
            registrar_cooldown(log, pagina_id)
            salvar_log(log)

            if comentarios_feitos < MAX_COMENTARIOS_POR_SESSAO:
                espera = random.randint(INTERVALO_MIN_SEGUNDOS, INTERVALO_MAX_SEGUNDOS)
                print(f"\n   ⏳ Aguardando {espera // 60}min {espera % 60}s antes do próximo...\n")
                if not dry_run:
                    time.sleep(espera)
        print()

    print(f"\n✅ Sessão concluída: {comentarios_feitos} comentário(s) postado(s)")
    print(f"📋 Log salvo em: {LOG_FILE}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Simula sem postar de verdade")
    args = parser.parse_args()

    if not META_ACCESS_TOKEN:
        raise EnvironmentError("META_ACCESS_TOKEN não configurado no .env")
    if not ANTHROPIC_API_KEY:
        raise EnvironmentError("ANTHROPIC_API_KEY não configurado no .env")

    executar_sessao(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
