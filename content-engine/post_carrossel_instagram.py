"""
post_carrossel_instagram.py
Publica carrossel de 6 imagens no Instagram via Meta Graph API.

Uso: python post_carrossel_instagram.py --categoria dinheiro
"""

import os
import io
import sys
import json
import time
import base64
import argparse
import requests
from datetime import datetime
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
IG_ACCOUNT_ID     = os.getenv("IG_ACCOUNT_ID") or os.getenv("INSTAGRAM_ACCOUNT_ID")
GITHUB_TOKEN      = os.getenv("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY", "zklab-bot/mejulga-system")

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


def upload_imagem(caminho_img: Path, max_tentativas: int = 3) -> str:
    """Faz commit da imagem na pasta cdn/ do repo público e retorna URL via raw.githubusercontent.com."""
    if not GITHUB_TOKEN:
        raise EnvironmentError("GITHUB_TOKEN não disponível")

    img = Image.open(caminho_img).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    content_b64 = base64.b64encode(buf.getvalue()).decode()

    filename = f"cdn/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{caminho_img.stem}.jpg"

    ultimo_erro = None
    for tentativa in range(1, max_tentativas + 1):
        try:
            resp = requests.put(
                f"https://api.github.com/repos/{GITHUB_REPOSITORY}/contents/{filename}",
                headers={
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                json={"message": f"cdn: {caminho_img.stem}", "content": content_b64},
                timeout=30,
            )
            resp.raise_for_status()
            return f"https://raw.githubusercontent.com/{GITHUB_REPOSITORY}/main/{filename}"
        except Exception as e:
            ultimo_erro = str(e)

        if tentativa < max_tentativas:
            print(f"  ⚠️  Tentativa {tentativa}/{max_tentativas} falhou: {ultimo_erro} — aguardando 5s...")
            time.sleep(5)

    raise RuntimeError(f"Upload falhou após {max_tentativas} tentativas. Último erro: {ultimo_erro}")


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


_RETRY_STATUS = {500, 502, 503, 504}


def _post_com_retry(url: str, max_tentativas: int = 3, **kwargs) -> requests.Response:
    """requests.post com retry automático em erros 5xx da Meta."""
    for tentativa in range(1, max_tentativas + 1):
        resp = requests.post(url, **kwargs)
        if resp.status_code not in _RETRY_STATUS:
            return resp
        espera = 2 ** tentativa  # 2s, 4s, 8s
        print(f"  ⚠️  Meta API {resp.status_code} — tentativa {tentativa}/{max_tentativas}, aguardando {espera}s...")
        if tentativa < max_tentativas:
            time.sleep(espera)
    return resp


def criar_container_imagem(image_url: str) -> str:
    """Cria container de imagem para carrossel. Retorna container_id."""
    resp = _post_com_retry(
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
    resp = _post_com_retry(
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
    """Publica o carrossel. Retorna media_id.

    A Meta pode retornar status HTTP 4xx mas ainda incluir o 'id' no corpo
    quando a publicação foi processada com sucesso internamente.
    Por isso verificamos o body antes de chamar raise_for_status.
    """
    resp = _post_com_retry(
        f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish",
        params={"access_token": META_ACCESS_TOKEN},
        data={"creation_id": carrossel_id}
    )
    data = resp.json()
    if "id" in data:
        return data["id"]
    resp.raise_for_status()
    raise RuntimeError(f"media_publish sem id na resposta: {data}")


def localizar_slides(categoria: str, hoje: str, formato: str = "carrossel") -> list:
    """Localiza os 6 slides gerados."""
    pasta = Path(__file__).parent / "generated" / "reels"
    if formato == "glossario":
        slides = sorted(pasta.glob(f"{hoje}_{categoria}_glossario_slide_*.png"))
    else:
        slides = sorted(pasta.glob(f"{hoje}_{categoria}_slide_*.png"))
    if not slides:
        raise FileNotFoundError(
            f"Nenhum slide encontrado em {pasta} para {hoje}_{categoria} [{formato}]"
        )
    return slides


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categoria", required=True,
                        choices=list(CATEGORIAS_CAPTION.keys()))
    parser.add_argument("--data", default=None)
    parser.add_argument("--output-id", action="store_true",
                        help="Imprime apenas o media_id e encerra")
    parser.add_argument("--formato", default="carrossel",
                        choices=["carrossel", "glossario"],
                        help="Tipo de post a publicar")
    args = parser.parse_args()

    for var, val in [("META_ACCESS_TOKEN", META_ACCESS_TOKEN),
                     ("IG_ACCOUNT_ID", IG_ACCOUNT_ID)]:
        if not val:
            raise EnvironmentError(f"{var} não configurado no .env")

    hoje = args.data or datetime.now().strftime("%Y-%m-%d")
    categoria = args.categoria

    # Em modo --output-id, redireciona todos os logs para stderr
    # para que apenas o media_id seja capturado pelo bash.
    # O try/finally garante que stdout seja restaurado mesmo em caso de erro.
    if args.output_id:
        sys.stdout = sys.stderr
    try:
        print(f"\n🎠 Publicando carrossel — {categoria} — {hoje}\n")

        slides = localizar_slides(categoria, hoje, args.formato)
        print(f"  📂 {len(slides)} slides encontrados")

        print("\n📦 PASSO 1: Upload dos slides para GitHub CDN")
        image_urls = []
        for i, slide in enumerate(slides):
            print(f"  ⬆️  Slide {i+1}/{len(slides)}: {slide.name}")
            url = upload_imagem(slide)
            image_urls.append(url)
            print(f"       ✅ {url}")

        print("\n📦 PASSO 2: Criando containers de imagem")
        container_ids = []
        for i, url in enumerate(image_urls):
            print(f"  📸 Container {i+1}/{len(image_urls)}...")
            cid = criar_container_imagem(url)
            print(f"       ID: {cid} — aguardando FINISHED...")
            aguardar_container_pronto(cid)
            container_ids.append(cid)
            print(f"       ✅ pronto")

        print("\n📦 PASSO 3: Criando carrossel")
        if args.formato == "glossario":
            pasta_json = Path(__file__).parent / "generated" / "reels"
            arq = pasta_json / f"{hoje}_{categoria}_glossario.json"
            if arq.exists():
                with open(arq, encoding="utf-8") as f:
                    glossario = json.load(f)
            else:
                glossario = {}
            caption = glossario.get("legenda_instagram") or CATEGORIAS_CAPTION.get(categoria, "")
        else:
            caption = CATEGORIAS_CAPTION[categoria]
        carrossel_id = criar_carrossel(container_ids, caption)
        print(f"  Carrossel ID: {carrossel_id} — aguardando FINISHED...")
        aguardar_container_pronto(carrossel_id)
        print(f"  ✅ Carrossel pronto")

        print("\n🚀 PASSO 4: Publicando no @dra.julga")
        media_id = publicar_carrossel(carrossel_id)
    finally:
        if args.output_id:
            sys.stdout = sys.__stdout__  # restaura stdout real

    if args.output_id:
        print(media_id)
        return

    print(f"  ✅ Publicado! media_id={media_id}")
    print(f"\n🎉 Carrossel publicado com sucesso!")
    print(f"🌐 https://www.instagram.com/dra.julga/")


if __name__ == "__main__":
    main()
