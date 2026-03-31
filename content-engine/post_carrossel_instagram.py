"""
post_carrossel_instagram.py
Publica carrossel de 6 imagens no Instagram via Meta Graph API.

Uso: python post_carrossel_instagram.py --categoria dinheiro
"""

import os
import io
import argparse
import requests
from datetime import datetime
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
IG_ACCOUNT_ID     = os.getenv("IG_ACCOUNT_ID") or os.getenv("INSTAGRAM_ACCOUNT_ID")

CATEGORIAS_CAPTION = {
    "dinheiro": (
        "A Dra. Julga analisou sua relação com o dinheiro... 💳🩺\n\n"
        "Desliza para ver o diagnóstico completo 👉\n\n"
        "Descobre o teu em mejulga.com.br 👇\n\n"
        "#mejulga #drajulga #dinheirobrasileiro #parcelado #humorbrasileiro "
        "#financaspessoais #endividado #cartaodecredito"
    ),
    "amor": (
        "A Dra. Julga analisou sua vida amorosa... 💔🩺\n\n"
        "Desliza para ver o diagnóstico completo 👉\n\n"
        "Descobre o teu em mejulga.com.br 👇\n\n"
        "#mejulga #drajulga #amor #relacionamento #humorbrasileiro"
    ),
    "trabalho": (
        "A Dra. Julga analisou sua carreira... 💼🩺\n\n"
        "Desliza para ver o diagnóstico completo 👉\n\n"
        "Descobre o teu em mejulga.com.br 👇\n\n"
        "#mejulga #drajulga #trabalho #carreira #humorbrasileiro"
    ),
    "dopamina": (
        "A Dra. Julga diagnosticou seu vício em dopamina digital 📱🩺\n\n"
        "Desliza para ver o diagnóstico completo 👉\n\n"
        "Descobre o teu em mejulga.com.br 👇\n\n"
        "#mejulga #drajulga #dopamina #saudemental #humorbrasileiro"
    ),
    "vida_adulta": (
        "A Dra. Julga avaliou sua vida adulta... 😅🩺\n\n"
        "Desliza para ver o diagnóstico completo 👉\n\n"
        "Descobre o teu em mejulga.com.br 👇\n\n"
        "#mejulga #drajulga #vidaadulta #humorbrasileiro"
    ),
    "social": (
        "A Dra. Julga analisou sua vida social... 👥🩺\n\n"
        "Desliza para ver o diagnóstico completo 👉\n\n"
        "Descobre o teu em mejulga.com.br 👇\n\n"
        "#mejulga #drajulga #vidasocial #humorbrasileiro"
    ),
    "saude_mental": (
        "A Dra. Julga emitiu seu laudo de saúde mental 🧠🩺\n\n"
        "Desliza para ver o diagnóstico completo 👉\n\n"
        "Descobre o teu em mejulga.com.br 👇\n\n"
        "#mejulga #drajulga #saudemental #humorbrasileiro"
    ),
}


def upload_catbox(caminho_img: Path) -> str:
    """Converte para JPEG, faz upload para catbox.moe e retorna URL pública."""
    img = Image.open(caminho_img).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    buf.seek(0)
    resp = requests.post(
        "https://catbox.moe/user/api.php",
        data={"reqtype": "fileupload"},
        files={"fileToUpload": (caminho_img.stem + ".jpg", buf, "image/jpeg")},
        timeout=30,
    )
    resp.raise_for_status()
    url = resp.text.strip()
    if not url.startswith("https://"):
        raise RuntimeError(f"Catbox retornou resposta inesperada: {url}")
    return url


def criar_container_imagem(image_url: str) -> str:
    """Cria container de imagem para carrossel. Retorna container_id."""
    resp = requests.post(
        f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media",
        params={"access_token": META_ACCESS_TOKEN},
        data={
            "image_url": image_url,
            "is_carousel_item": "true",
        }
    )
    resp.raise_for_status()
    return resp.json()["id"]


def criar_carrossel(container_ids: list, caption: str) -> str:
    """Cria container do carrossel com todos os slides. Retorna carrossel_id."""
    resp = requests.post(
        f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media",
        params={"access_token": META_ACCESS_TOKEN},
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(container_ids),
            "caption": caption,
        }
    )
    resp.raise_for_status()
    return resp.json()["id"]


def publicar_carrossel(carrossel_id: str) -> str:
    """Publica o carrossel. Retorna media_id."""
    resp = requests.post(
        f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish",
        params={"access_token": META_ACCESS_TOKEN},
        data={"creation_id": carrossel_id}
    )
    resp.raise_for_status()
    return resp.json()["id"]


def localizar_slides(categoria: str, hoje: str) -> list:
    """Localiza os 6 slides gerados."""
    pasta = Path(__file__).parent / "generated" / "reels"
    slides = sorted(pasta.glob(f"{hoje}_{categoria}_slide_*.png"))
    if not slides:
        raise FileNotFoundError(
            f"Nenhum slide encontrado em {pasta} para {hoje}_{categoria}"
        )
    return slides


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categoria", required=True,
                        choices=list(CATEGORIAS_CAPTION.keys()))
    parser.add_argument("--data", default=None)
    args = parser.parse_args()

    for var, val in [("META_ACCESS_TOKEN", META_ACCESS_TOKEN),
                     ("IG_ACCOUNT_ID", IG_ACCOUNT_ID)]:
        if not val:
            raise EnvironmentError(f"{var} não configurado no .env")

    hoje = args.data or datetime.now().strftime("%Y-%m-%d")
    categoria = args.categoria

    print(f"\n🎠 Publicando carrossel — {categoria} — {hoje}\n")

    # Localiza slides
    slides = localizar_slides(categoria, hoje)
    print(f"  📂 {len(slides)} slides encontrados")

    # Upload de cada slide para catbox.moe
    print("\n📦 PASSO 1: Upload dos slides para catbox.moe")
    image_urls = []
    for i, slide in enumerate(slides):
        print(f"  ⬆️  Slide {i+1}/{len(slides)}: {slide.name}")
        url = upload_catbox(slide)
        image_urls.append(url)
        print(f"       ✅ {url}")

    # Criar containers individuais
    print("\n📦 PASSO 2: Criando containers de imagem")
    container_ids = []
    for i, url in enumerate(image_urls):
        print(f"  📸 Container {i+1}/{len(image_urls)}...")
        cid = criar_container_imagem(url)
        container_ids.append(cid)
        print(f"       ✅ {cid}")

    # Criar carrossel
    print("\n📦 PASSO 3: Criando carrossel")
    caption = CATEGORIAS_CAPTION[categoria]
    carrossel_id = criar_carrossel(container_ids, caption)
    print(f"  ✅ Carrossel ID: {carrossel_id}")

    # Publicar
    print("\n🚀 PASSO 4: Publicando no @dra.julga")
    media_id = publicar_carrossel(carrossel_id)
    print(f"  ✅ Publicado! media_id={media_id}")

    print(f"\n🎉 Carrossel publicado com sucesso!")
    print(f"🌐 https://www.instagram.com/dra.julga/")


if __name__ == "__main__":
    main()
