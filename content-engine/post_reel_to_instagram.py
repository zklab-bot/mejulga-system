"""
post_reel_to_instagram.py
Faz upload do vídeo no GitHub Releases e publica como Reel no Instagram.
Uso: python post_reel_to_instagram.py --categoria dinheiro
"""

import os
import time
import argparse
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── Configurações ────────────────────────────────────────────────────────────

META_ACCESS_TOKEN   = os.getenv("META_ACCESS_TOKEN")
IG_ACCOUNT_ID       = os.getenv("IG_ACCOUNT_ID")
GITHUB_TOKEN        = os.getenv("GITHUB_TOKEN")
GITHUB_REPO         = os.getenv("GITHUB_REPO")          # ex: "zklab-bot/mejulga-assets"
GITHUB_RELEASE_TAG  = os.getenv("GITHUB_RELEASE_TAG", "reels-videos")


# ─── 1. Upload para GitHub Releases ──────────────────────────────────────────

def garantir_release_existe(tag: str) -> str:
    """Cria a release no GitHub se não existir. Retorna o upload_url."""
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{tag}"
    resp = requests.get(url, headers=headers)

    if resp.status_code == 200:
        data = resp.json()
        print(f"  ✅ Release '{tag}' já existe (id={data['id']})")
        return data["upload_url"].replace("{?name,label}", "")

    # Cria nova release
    print(f"  📦 Criando release '{tag}'...")
    resp = requests.post(
        f"https://api.github.com/repos/{GITHUB_REPO}/releases",
        headers=headers,
        json={
            "tag_name": tag,
            "name": "Reels Videos — Dra. Julga",
            "body": "Assets de vídeo do pipeline mejulga-system",
            "draft": False,
            "prerelease": False,
        }
    )
    resp.raise_for_status()
    data = resp.json()
    print(f"  ✅ Release criada (id={data['id']})")
    return data["upload_url"].replace("{?name,label}", "")


def upload_github_release(caminho_video: Path) -> str:
    """Faz upload do .mp4 para GitHub Releases. Retorna a URL pública do asset."""
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "video/mp4",
    }

    upload_url = garantir_release_existe(GITHUB_RELEASE_TAG)
    nome_arquivo = caminho_video.name

    # Verifica se asset já existe (evita duplicata)
    list_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{GITHUB_RELEASE_TAG}"
    resp = requests.get(list_url, headers={"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"})
    release_data = resp.json()
    for asset in release_data.get("assets", []):
        if asset["name"] == nome_arquivo:
            print(f"  ♻️  Asset já existe: {asset['browser_download_url']}")
            return asset["browser_download_url"]

    print(f"  ⬆️  Enviando {nome_arquivo} ({caminho_video.stat().st_size // 1024 // 1024}MB) para GitHub...")
    with open(caminho_video, "rb") as f:
        resp = requests.post(
            f"{upload_url}?name={nome_arquivo}",
            headers=headers,
            data=f,
        )
    resp.raise_for_status()
    url_publica = resp.json()["browser_download_url"]
    print(f"  ✅ Upload concluído: {url_publica}")
    return url_publica


# ─── 2. Publicar Reel no Instagram ────────────────────────────────────────────

def publicar_reel(video_url: str, caption: str) -> str:
    """
    Publica um Reel no Instagram Business via Meta Graph API.
    Etapa 1: cria container de mídia
    Etapa 2: aguarda processamento
    Etapa 3: publica
    """
    base = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}"
    params_base = {"access_token": META_ACCESS_TOKEN}

    # Etapa 1 — Criar container
    print("  📤 Criando container de mídia no Instagram...")
    resp = requests.post(
        f"{base}/media",
        params=params_base,
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true",
        }
    )
    resp.raise_for_status()
    container_id = resp.json()["id"]
    print(f"  📦 Container criado: {container_id}")

    # Etapa 2 — Aguardar processamento
    print("  ⏳ Aguardando processamento do vídeo pela Meta...")
    for tentativa in range(20):
        time.sleep(15)
        status_resp = requests.get(
            f"https://graph.facebook.com/v19.0/{container_id}",
            params={**params_base, "fields": "status_code,status"},
        )
        status_resp.raise_for_status()
        status = status_resp.json().get("status_code")
        print(f"     [{tentativa+1}/20] Status: {status}")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise Exception(f"Erro no processamento do vídeo: {status_resp.json()}")
    else:
        raise Exception("Timeout: vídeo não processou em 5 minutos.")

    # Etapa 3 — Publicar
    print("  🚀 Publicando Reel...")
    pub_resp = requests.post(
        f"{base}/media_publish",
        params=params_base,
        data={"creation_id": container_id},
    )
    pub_resp.raise_for_status()
    media_id = pub_resp.json()["id"]
    print(f"  ✅ Reel publicado! media_id={media_id}")
    return media_id


# ─── 3. Caption automática ────────────────────────────────────────────────────

def gerar_caption(categoria: str) -> str:
    captions = {
        "dinheiro": (
            "Dra. Julga analisou sua relação com o dinheiro... e o diagnóstico é grave 💳🩺\n\n"
            "Parcelite crônica estágio avançado. Sem defesa possível.\n\n"
            "Descobre o teu em mejulga.com.br 👇\n\n"
            "#mejulga #drajulga #dinheirobrasileiro #parcelado #virilou #humorbrasileiro "
            "#financaspessoais #endividado #cartaodecredito #reels"
        ),
        "amor": (
            "A Dra. Julga analisou sua vida amorosa... o laudo chegou 💔🩺\n\n"
            "Descobre o teu em mejulga.com.br 👇\n\n"
            "#mejulga #drajulga #amor #relacionamento #humorbrasileiro #reels"
        ),
        "trabalho": (
            "A Dra. Julga analisou sua carreira... prepare-se para a verdade 💼🩺\n\n"
            "Descobre o teu em mejulga.com.br 👇\n\n"
            "#mejulga #drajulga #trabalho #carreira #humorbrasileiro #reels"
        ),
        "dopamina": (
            "A Dra. Julga diagnosticou seu vício em dopamina digital 📱🩺\n\n"
            "Descobre o teu em mejulga.com.br 👇\n\n"
            "#mejulga #drajulga #dopamina #saudemental #humorbrasileiro #reels"
        ),
        "vida_adulta": (
            "A Dra. Julga avaliou sua vida adulta... resultado perturbador 😅🩺\n\n"
            "Descobre o teu em mejulga.com.br 👇\n\n"
            "#mejulga #drajulga #vidaadulta #humorbrasileiro #reels"
        ),
        "social": (
            "A Dra. Julga analisou sua vida social... laudo emitido 👥🩺\n\n"
            "Descobre o teu em mejulga.com.br 👇\n\n"
            "#mejulga #drajulga #vidasocial #humorbrasileiro #reels"
        ),
        "saude_mental": (
            "A Dra. Julga emitiu seu laudo de saúde mental... é sério 🧠🩺\n\n"
            "Descobre o teu em mejulga.com.br 👇\n\n"
            "#mejulga #drajulga #saudemental #humorbrasileiro #reels"
        ),
    }
    return captions.get(categoria, captions["dinheiro"])


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categoria", default="dinheiro")
    parser.add_argument("--data", default=None)
    parser.add_argument("--video", default=None, help="Caminho direto para o .mp4 (opcional)")
    args = parser.parse_args()

    # Validações
    erros = []
    if not META_ACCESS_TOKEN: erros.append("META_ACCESS_TOKEN")
    if not IG_ACCOUNT_ID:     erros.append("IG_ACCOUNT_ID")
    if not GITHUB_TOKEN:      erros.append("GITHUB_TOKEN")
    if not GITHUB_REPO:       erros.append("GITHUB_REPO")
    if erros:
        raise EnvironmentError(f"Variáveis não configuradas no .env: {', '.join(erros)}")

    hoje = args.data or datetime.now().strftime("%Y-%m-%d")
    categoria = args.categoria

    # Localizar vídeo
    if args.video:
        caminho_video = Path(args.video)
    else:
        pasta = Path(__file__).parent / "generated" / "reels"
        caminho_video = pasta / f"{hoje}_{categoria}_reels.mp4"

    if not caminho_video.exists():
        raise FileNotFoundError(f"Vídeo não encontrado: {caminho_video}")

    print(f"\n🎬 Publicando Reel — {categoria} — {hoje}")
    print(f"📁 Arquivo: {caminho_video.name}\n")

    # Passo 1: Upload GitHub
    print("📦 PASSO 1: Upload para GitHub Releases")
    video_url = upload_github_release(caminho_video)

    # Passo 2: Publicar Instagram
    print("\n📸 PASSO 2: Publicando no Instagram @dra.julga")
    caption = gerar_caption(categoria)
    media_id = publicar_reel(video_url, caption)

    print(f"\n✅ Reel publicado com sucesso!")
    print(f"🎉 @dra.julga — media_id: {media_id}")
    print(f"🌐 Confere em: https://www.instagram.com/dra.julga/")


if __name__ == "__main__":
    main()
