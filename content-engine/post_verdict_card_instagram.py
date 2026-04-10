"""
post_verdict_card_instagram.py
Publica o verdict card (imagem única) no Instagram via Meta Graph API.

Uso: python post_verdict_card_instagram.py --categoria amor
"""

import os
import io
import sys
import json
import base64
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
GITHUB_TOKEN      = os.getenv("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY", "zklab-bot/mejulga-system")

_RETRY_STATUS = {500, 502, 503, 504}


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


def _post_com_retry(url: str, max_tentativas: int = 3, **kwargs) -> requests.Response:
    for tentativa in range(1, max_tentativas + 1):
        resp = requests.post(url, **kwargs)
        if resp.status_code not in _RETRY_STATUS:
            return resp
        espera = 2 ** tentativa
        print(f"  ⚠️  Meta API {resp.status_code} — tentativa {tentativa}/{max_tentativas}, aguardando {espera}s...")
        if tentativa < max_tentativas:
            time.sleep(espera)
    return resp


def publicar_imagem(image_url: str, caption: str) -> str:
    """Cria container e publica imagem única. Retorna media_id."""
    # Criar container
    resp = _post_com_retry(
        f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media",
        params={"access_token": META_ACCESS_TOKEN},
        data={"image_url": image_url, "caption": caption},
    )
    resp.raise_for_status()
    container_id = resp.json()["id"]

    # Aguardar FINISHED
    print(f"  Container {container_id} — aguardando FINISHED...")
    for i in range(1, 21):
        r = requests.get(
            f"https://graph.facebook.com/v19.0/{container_id}",
            params={"fields": "status_code", "access_token": META_ACCESS_TOKEN},
            timeout=15,
        )
        r.raise_for_status()
        status = r.json().get("status_code", "UNKNOWN")
        print(f"    [{i}/20] {status}")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise RuntimeError(f"Container {container_id} retornou ERROR")
        time.sleep(5)

    # Publicar
    resp2 = _post_com_retry(
        f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish",
        params={"access_token": META_ACCESS_TOKEN},
        data={"creation_id": container_id},
    )
    data = resp2.json()
    if "id" in data:
        return data["id"]
    resp2.raise_for_status()
    raise RuntimeError(f"media_publish sem id: {data}")


def build_caption(roteiro: dict) -> str:
    crime = roteiro.get("crime", "")
    categoria = roteiro.get("categoria", "")
    frase = roteiro.get("frase_printavel", "")

    hashtags = {
        "dinheiro":    "#MeJulga #DraJulga #FinancasPessoais #HumorBrasileiro #Veredicto #Identificacao",
        "amor":        "#MeJulga #DraJulga #Amor #Relacionamento #HumorBrasileiro #Veredicto #Identificacao",
        "trabalho":    "#MeJulga #DraJulga #Trabalho #HomeOffice #HumorBrasileiro #Veredicto #Identificacao",
        "dopamina":    "#MeJulga #DraJulga #VicioemCelular #HumorBrasileiro #Veredicto #Identificacao",
        "vida_adulta": "#MeJulga #DraJulga #VidaAdulta #HumorBrasileiro #Veredicto #Identificacao",
        "social":      "#MeJulga #DraJulga #Introvertido #HumorBrasileiro #Veredicto #Identificacao",
        "saude_mental":"#MeJulga #DraJulga #SaudeMental #HumorBrasileiro #Veredicto #Identificacao",
    }.get(categoria, "#MeJulga #DraJulga #HumorBrasileiro")

    return (
        f"O veredicto chegou.\n\n"
        f"Culpado(a) por {crime}.\n\n"
        f'"{frase}"\n\n'
        f"Veja o processo completo no perfil ☝️\n\n"
        f"mejulga.com.br\n\n"
        f"{hashtags}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categoria", required=True)
    parser.add_argument("--data", default=None)
    parser.add_argument("--output-id", action="store_true")
    args = parser.parse_args()

    for var, val in [("META_ACCESS_TOKEN", META_ACCESS_TOKEN),
                     ("IG_ACCOUNT_ID", IG_ACCOUNT_ID)]:
        if not val:
            raise EnvironmentError(f"{var} não configurado")

    hoje = args.data or datetime.now().strftime("%Y-%m-%d")
    pasta = Path(__file__).parent / "generated" / "reels"

    # Carrega roteiro
    arq_json = pasta / f"{hoje}_{args.categoria}_reels.json"
    if not arq_json.exists():
        raise FileNotFoundError(f"Roteiro não encontrado: {arq_json}")
    with open(arq_json, encoding="utf-8") as f:
        roteiro = json.load(f)

    # Localiza verdict card gerado
    arq_img = pasta / f"{hoje}_{args.categoria}_verdict_card.png"
    if not arq_img.exists():
        raise FileNotFoundError(f"Verdict card não encontrado: {arq_img}")

    if args.output_id:
        sys.stdout = sys.stderr
    try:
        print(f"\n⚖️  Publicando verdict card — {args.categoria} — {hoje}\n")

        print("📦 PASSO 1: Upload para GitHub CDN")
        url = upload_imagem(arq_img)
        print(f"  ✅ {url}")

        print("\n🚀 PASSO 2: Publicando no @dra.julga")
        caption = build_caption(roteiro)
        media_id = publicar_imagem(url, caption)
    finally:
        if args.output_id:
            sys.stdout = sys.__stdout__

    if args.output_id:
        print(media_id)
        return

    print(f"  ✅ Publicado! media_id={media_id}")
    print(f"\n🎉 Verdict card publicado com sucesso!")
    print(f"🌐 https://www.instagram.com/dra.julga/")


if __name__ == "__main__":
    main()
