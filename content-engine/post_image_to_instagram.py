"""
post_image_to_instagram.py
Publica imagem PNG no Instagram via Meta Graph API.
Usa servidor HTTP temporário no GitHub Actions para servir a imagem publicamente.
Ou faz upload para ImgBB (gratuito, sem conta necessária via API key).

Uso: python post_image_to_instagram.py --categoria dinheiro
"""

import os
import base64
import argparse
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

META_ACCESS_TOKEN    = os.getenv("META_ACCESS_TOKEN")
IG_ACCOUNT_ID        = os.getenv("IG_ACCOUNT_ID") or os.getenv("INSTAGRAM_ACCOUNT_ID")
IMGBB_API_KEY        = os.getenv("IMGBB_API_KEY", "")  # opcional
GITHUB_TOKEN         = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO          = os.getenv("GITHUB_REPO", "zklab-bot/mejulga-assets")

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


def upload_imgbb(caminho_img: Path) -> str:
    """Faz upload da imagem para ImgBB e retorna URL pública."""
    print("  ⬆️  Enviando imagem para ImgBB...")
    with open(caminho_img, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")

    resp = requests.post(
        "https://api.imgbb.com/1/upload",
        data={
            "key": IMGBB_API_KEY,
            "image": img_base64,
            "name": caminho_img.stem,
            "expiration": 600,  # expira em 10 minutos (só precisa para o upload Meta)
        }
    )
    resp.raise_for_status()
    url = resp.json()["data"]["url"]
    print(f"  ✅ URL pública: {url}")
    return url


def upload_github_contents(caminho_img: Path) -> str:
    """Faz upload da imagem para GitHub via Contents API (não precisa de releases)."""
    print("  ⬆️  Enviando imagem para GitHub Contents API...")

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    nome = caminho_img.name
    path_repo = f"images/{nome}"
    url_api = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path_repo}"

    # Verifica se já existe
    resp_check = requests.get(url_api, headers=headers)
    sha = resp_check.json().get("sha") if resp_check.status_code == 200 else None

    with open(caminho_img, "rb") as f:
        conteudo_b64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "message": f"feat: imagem {nome}",
        "content": conteudo_b64,
        "branch": "main",
    }
    if sha:
        payload["sha"] = sha  # necessário para actualizar ficheiro existente

    resp = requests.put(url_api, headers=headers, json=payload)
    resp.raise_for_status()

    # URL raw pública do GitHub
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{path_repo}"
    print(f"  ✅ URL pública: {url}")
    return url


def publicar_imagem(image_url: str, caption: str) -> str:
    """Publica imagem no Instagram via Meta Graph API."""
    base = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}"
    params = {"access_token": META_ACCESS_TOKEN}

    print("  📤 Criando container de imagem...")
    resp = requests.post(
        f"{base}/media",
        params=params,
        data={"image_url": image_url, "caption": caption}
    )
    resp.raise_for_status()
    container_id = resp.json()["id"]
    print(f"  📦 Container: {container_id}")

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


def localizar_imagem(categoria: str, hoje: str) -> Path:
    pasta = Path(__file__).parent / "generated" / "reels"
    for sufixo in [
        f"_{categoria}_minimalista_reels.png",
        f"_{categoria}_reels.png",
        f"_{categoria}_minimalista_reels.mp4",
    ]:
        caminho = pasta / f"{hoje}{sufixo}"
        if caminho.exists():
            return caminho
    raise FileNotFoundError(
        f"Imagem não encontrada em {pasta} para {hoje}_{categoria}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categoria", required=True,
                        choices=list(CATEGORIAS_CAPTION.keys()))
    parser.add_argument("--data", default=None)
    parser.add_argument("--imagem", default=None)
    args = parser.parse_args()

    for var, val in [("META_ACCESS_TOKEN", META_ACCESS_TOKEN),
                     ("IG_ACCOUNT_ID", IG_ACCOUNT_ID)]:
        if not val:
            raise EnvironmentError(f"{var} não configurado")

    hoje = args.data or datetime.now().strftime("%Y-%m-%d")
    categoria = args.categoria

    caminho_img = Path(args.imagem) if args.imagem else localizar_imagem(categoria, hoje)
    print(f"\n📸 Publicando — {categoria} — {hoje}")
    print(f"📁 Arquivo: {caminho_img.name}\n")

    # Upload da imagem — ImgBB primeiro (Meta aceita), GitHub como fallback
    if IMGBB_API_KEY:
        print("📦 PASSO 1: Upload via ImgBB")
        image_url = upload_imgbb(caminho_img)
    elif GITHUB_TOKEN and GITHUB_REPO:
        print("📦 PASSO 1: Upload via GitHub Contents API")
        image_url = upload_github_contents(caminho_img)
    else:
        raise EnvironmentError(
            "Configure IMGBB_API_KEY ou GITHUB_TOKEN+GITHUB_REPO para hospedar a imagem"
        )

    print("\n📸 PASSO 2: Publicando no Instagram")
    caption = CATEGORIAS_CAPTION[categoria]
    media_id = publicar_imagem(image_url, caption)

    print(f"\n✅ Post publicado! media_id={media_id}")
    print("🌐 https://www.instagram.com/dra.julga/")


if __name__ == "__main__":
    main()
