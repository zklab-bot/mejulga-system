"""
post_image_to_instagram.py
Publica imagem PNG diretamente no Instagram via Meta Graph API.
Não precisa de hospedagem externa — usa upload direto via API.

Uso:
  python post_image_to_instagram.py --categoria dinheiro
  python post_image_to_instagram.py --categoria amor --data 2026-03-31
"""

import os
import argparse
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
IG_ACCOUNT_ID     = os.getenv("IG_ACCOUNT_ID")
GITHUB_TOKEN      = os.getenv("GITHUB_TOKEN")
GITHUB_REPO       = os.getenv("GITHUB_REPO", "zklab-bot/mejulga-assets")
GITHUB_RELEASE_TAG = os.getenv("GITHUB_RELEASE_TAG", "imagens-diarias")

CATEGORIAS_CAPTION = {
    "dinheiro": (
        "A Dra. Julga analisou sua relação com o dinheiro... e o diagnóstico é grave 💳🩺\n\n"
        "Parcelite crônica estágio avançado. Sem defesa possível.\n\n"
        "Descobre o teu em mejulga.com.br 👇\n\n"
        "#mejulga #drajulga #dinheirobrasileiro #parcelado #humorbrasileiro "
        "#financaspessoais #endividado #cartaodecredito"
    ),
    "amor": (
        "A Dra. Julga analisou sua vida amorosa... o laudo chegou 💔🩺\n\n"
        "Sem defesa possível.\n\n"
        "Descobre o teu em mejulga.com.br 👇\n\n"
        "#mejulga #drajulga #amor #relacionamento #humorbrasileiro"
    ),
    "trabalho": (
        "A Dra. Julga analisou sua carreira... prepare-se 💼🩺\n\n"
        "Sem defesa possível.\n\n"
        "Descobre o teu em mejulga.com.br 👇\n\n"
        "#mejulga #drajulga #trabalho #carreira #humorbrasileiro"
    ),
    "dopamina": (
        "A Dra. Julga diagnosticou seu vício em dopamina digital 📱🩺\n\n"
        "Sem defesa possível.\n\n"
        "Descobre o teu em mejulga.com.br 👇\n\n"
        "#mejulga #drajulga #dopamina #saudemental #humorbrasileiro"
    ),
    "vida_adulta": (
        "A Dra. Julga avaliou sua vida adulta... resultado perturbador 😅🩺\n\n"
        "Sem defesa possível.\n\n"
        "Descobre o teu em mejulga.com.br 👇\n\n"
        "#mejulga #drajulga #vidaadulta #humorbrasileiro"
    ),
    "social": (
        "A Dra. Julga analisou sua vida social... laudo emitido 👥🩺\n\n"
        "Sem defesa possível.\n\n"
        "Descobre o teu em mejulga.com.br 👇\n\n"
        "#mejulga #drajulga #vidasocial #humorbrasileiro"
    ),
    "saude_mental": (
        "A Dra. Julga emitiu seu laudo de saúde mental 🧠🩺\n\n"
        "Sem defesa possível.\n\n"
        "Descobre o teu em mejulga.com.br 👇\n\n"
        "#mejulga #drajulga #saudemental #humorbrasileiro"
    ),
}


# ─── 1. Upload imagem para GitHub Releases (URL pública) ──────────────────────

def garantir_release(tag: str) -> str:
    """Garante que a release existe e retorna o upload_url."""
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    resp = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{tag}",
        headers=headers
    )
    if resp.status_code == 200:
        return resp.json()["upload_url"].replace("{?name,label}", "")

    print(f"  📦 Criando release '{tag}'...")
    resp = requests.post(
        f"https://api.github.com/repos/{GITHUB_REPO}/releases",
        headers=headers,
        json={
            "tag_name": tag,
            "name": "Imagens Diárias — Dra. Julga",
            "body": "Imagens geradas pelo pipeline mejulga-system",
            "draft": False,
            "prerelease": False,
        }
    )
    resp.raise_for_status()
    return resp.json()["upload_url"].replace("{?name,label}", "")


def upload_imagem_github(caminho_img: Path) -> str:
    """Faz upload da imagem para GitHub Releases e retorna URL pública."""
    headers_gh = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    upload_url = garantir_release(GITHUB_RELEASE_TAG)
    nome = caminho_img.name

    # Verifica se já existe
    resp = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{GITHUB_RELEASE_TAG}",
        headers=headers_gh
    )
    for asset in resp.json().get("assets", []):
        if asset["name"] == nome:
            print(f"  ♻️  Imagem já existe: {asset['browser_download_url']}")
            return asset["browser_download_url"]

    print(f"  ⬆️  Enviando {nome} para GitHub Releases...")
    with open(caminho_img, "rb") as f:
        resp = requests.post(
            f"{upload_url}?name={nome}",
            headers={**headers_gh, "Content-Type": "image/png"},
            data=f,
        )
    resp.raise_for_status()
    url = resp.json()["browser_download_url"]
    print(f"  ✅ URL pública: {url}")
    return url


# ─── 2. Publicar imagem no Instagram ──────────────────────────────────────────

def publicar_imagem(image_url: str, caption: str) -> str:
    """Publica imagem no Instagram via Meta Graph API. Retorna media_id."""
    base = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}"
    params = {"access_token": META_ACCESS_TOKEN}

    # Etapa 1: criar container
    print("  📤 Criando container de imagem...")
    resp = requests.post(
        f"{base}/media",
        params=params,
        data={
            "image_url": image_url,
            "caption": caption,
        }
    )
    resp.raise_for_status()
    container_id = resp.json()["id"]
    print(f"  📦 Container: {container_id}")

    # Etapa 2: publicar
    print("  🚀 Publicando no Instagram...")
    resp = requests.post(
        f"{base}/media_publish",
        params=params,
        data={"creation_id": container_id}
    )
    resp.raise_for_status()
    media_id = resp.json()["id"]
    print(f"  ✅ Publicado! media_id={media_id}")
    return media_id


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categoria", required=True,
                        choices=list(CATEGORIAS_CAPTION.keys()))
    parser.add_argument("--data", default=None)
    parser.add_argument("--imagem", default=None,
                        help="Caminho direto para a imagem PNG")
    args = parser.parse_args()

    # Validações
    for var in ["META_ACCESS_TOKEN", "IG_ACCOUNT_ID", "GITHUB_TOKEN"]:
        if not os.getenv(var):
            raise EnvironmentError(f"{var} não configurado no .env")

    hoje = args.data or datetime.now().strftime("%Y-%m-%d")
    categoria = args.categoria

    # Localizar imagem
    if args.imagem:
        caminho_img = Path(args.imagem)
    else:
        pasta = Path(__file__).parent / "generated" / "reels"
        # Tenta minimalista primeiro, depois padrão
        for sufixo in ["_minimalista_reels.png", "_reels.png", "_minimalista_reels.mp4"]:
            caminho_img = pasta / f"{hoje}_{categoria}{sufixo}"
            if caminho_img.exists():
                break

    if not caminho_img.exists():
        raise FileNotFoundError(f"Imagem não encontrada: {caminho_img}")

    print(f"\n📸 Publicando imagem — {categoria} — {hoje}")
    print(f"📁 Arquivo: {caminho_img.name}\n")

    # Passo 1: Upload GitHub
    print("📦 PASSO 1: Upload para GitHub Releases")
    image_url = upload_imagem_github(caminho_img)

    # Passo 2: Publicar Instagram
    print("\n📸 PASSO 2: Publicando no @dra.julga")
    caption = CATEGORIAS_CAPTION[categoria]
    media_id = publicar_imagem(image_url, caption)

    print(f"\n✅ Post publicado com sucesso!")
    print(f"🎉 @dra.julga — media_id: {media_id}")
    print(f"🌐 https://www.instagram.com/dra.julga/")


if __name__ == "__main__":
    main()
