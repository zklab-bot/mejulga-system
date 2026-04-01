"""
post_carrossel_instagram.py
Publica carrossel de 6 imagens no Instagram via Meta Graph API.

Uso: python post_carrossel_instagram.py --categoria dinheiro
"""

import os
import io
import sys
import time
import argparse
import requests
from datetime import datetime
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
IG_ACCOUNT_ID     = os.getenv("IG_ACCOUNT_ID") or os.getenv("INSTAGRAM_ACCOUNT_ID")

# Captions com Voice DNA da Dra. Julga.
# Regras: frases curtas, declarativas, sem emoji no texto principal.
# Ela não pede — ela intima. Ela não sugere — ela afirma.
CATEGORIAS_CAPTION = {
    "dinheiro": (
        "A Dra. Julga acessou seu extrato bancário.\n"
        "O veredicto? Indefensável.\n\n"
        "Você está intimado(a) a encaminhar esta prova para seu cúmplice.\n\n"
        "Diagnóstico completo gratuito em mejulga.com.br\n\n"
        "#MeJulga #DraJulga #FinancasPessoais #HumorBrasileiro "
        "#Parcelado #Gastei #VidaAdulta #Identificacao"
    ),
    "amor": (
        "A Dra. Julga leu suas mensagens.\n"
        "Todas. Até as apagadas.\n\n"
        "O julgamento já começou.\n\n"
        "Manda no grupo da família sem contexto nenhum.\n\n"
        "Diagnóstico completo em mejulga.com.br\n\n"
        "#MeJulga #DraJulga #Amor #Relacionamento #HumorBrasileiro "
        "#RelacionamentoToxico #Crush #Identificacao"
    ),
    "trabalho": (
        "A Dra. Julga monitorou sua segunda-feira.\n"
        "De 8h às 18h. Você trabalhou 47 minutos.\n\n"
        "Manda pra quem acha que é produtivo.\n\n"
        "Diagnóstico completo em mejulga.com.br\n\n"
        "#MeJulga #DraJulga #Trabalho #HomeOffice #HumorBrasileiro "
        "#Procrastinacao #SegundaFeira #Identificacao"
    ),
    "dopamina": (
        "A Dra. Julga cronometrou seu tempo de tela.\n"
        "São 7h14 por dia.\n"
        "Ela está preocupada. Você, não.\n\n"
        "Manda pra quem tá no celular enquanto lê isso.\n\n"
        "Diagnóstico completo em mejulga.com.br\n\n"
        "#MeJulga #DraJulga #TempoDeAntena #VicioemCelular "
        "#HumorBrasileiro #ScrollInfinito #Identificacao"
    ),
    "vida_adulta": (
        "A Dra. Julga visitou sua geladeira.\n"
        "Tinha ketchup, uma cerveja e arrependimento.\n\n"
        "Manda no grupo da família sem contexto nenhum.\n\n"
        "Diagnóstico completo em mejulga.com.br\n\n"
        "#MeJulga #DraJulga #VidaAdulta #AdultingIsHard "
        "#HumorBrasileiro #NinguemMePreparou #Identificacao"
    ),
    "social": (
        "A Dra. Julga viu que você cancelou planos.\n"
        "De novo. Terceiro sábado seguido.\n\n"
        "Manda pra quem cancelou você semana passada.\n\n"
        "Diagnóstico completo em mejulga.com.br\n\n"
        "#MeJulga #DraJulga #CancelarPlanos #Introvertido "
        "#HumorBrasileiro #AnguloSocial #Identificacao"
    ),
    "saude_mental": (
        "A Dra. Julga acessou seus pensamentos das 3h da manhã.\n"
        "O processo precisou de volume 2.\n\n"
        "Manda pra quem você sabe que precisa ver isso.\n\n"
        "Diagnóstico completo em mejulga.com.br\n\n"
        "#MeJulga #DraJulga #SaudeMental #AutoCuidado "
        "#HumorBrasileiro #Terapia #Identificacao"
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


def aguardar_container_pronto(container_id: str, max_tentativas: int = 20, intervalo: int = 5) -> None:
    """Aguarda até o container estar no status FINISHED antes de publicar."""
    for tentativa in range(1, max_tentativas + 1):
        resp = requests.get(
            f"https://graph.facebook.com/v19.0/{container_id}",
            params={"fields": "status_code", "access_token": META_ACCESS_TOKEN},
            timeout=15,
        )
        resp.raise_for_status()
        status = resp.json().get("status_code", "UNKNOWN")
        print(f"       [{tentativa}/{max_tentativas}] status: {status}")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError(f"Container {container_id} retornou ERROR no processamento")
        time.sleep(intervalo)
    raise TimeoutError(f"Container {container_id} não ficou FINISHED após {max_tentativas} tentativas")


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
    parser.add_argument("--output-id", action="store_true",
                        help="Imprime apenas o media_id e encerra")
    args = parser.parse_args()

    # Em modo --output-id, redireciona todos os logs para stderr
    # para que apenas o media_id seja capturado pelo bash
    if args.output_id:
        sys.stdout = sys.stderr

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
        print(f"       ID: {cid} — aguardando FINISHED...")
        aguardar_container_pronto(cid)
        container_ids.append(cid)
        print(f"       ✅ pronto")

    # Criar carrossel
    print("\n📦 PASSO 3: Criando carrossel")
    caption = CATEGORIAS_CAPTION[categoria]
    carrossel_id = criar_carrossel(container_ids, caption)
    print(f"  Carrossel ID: {carrossel_id} — aguardando FINISHED...")
    aguardar_container_pronto(carrossel_id)
    print(f"  ✅ Carrossel pronto")

    # Publicar
    print("\n🚀 PASSO 4: Publicando no @dra.julga")
    media_id = publicar_carrossel(carrossel_id)

    if args.output_id:
        sys.stdout = sys.__stdout__  # restaura stdout real
        print(media_id)
        return

    print(f"  ✅ Publicado! media_id={media_id}")

    print(f"\n🎉 Carrossel publicado com sucesso!")
    print(f"🌐 https://www.instagram.com/dra.julga/")


if __name__ == "__main__":
    main()
