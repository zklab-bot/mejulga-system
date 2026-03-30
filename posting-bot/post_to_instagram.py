"""
post_to_instagram.py
Publica automaticamente os posts gerados no Instagram da Dra. Julga.
Usa a Meta Graph API com imagem gerada via URL de serviço externo.
Uso: python post_to_instagram.py --horario 12
"""

import os
import json
import argparse
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()

ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
GRAPH_API_URL = "https://graph.facebook.com/v19.0"

HORARIO_TIPO = {
    "12": "provocacao",
    "18": "caso_clinico",
    "21": "cta"
}

# Imagem padrão da Dra. Julga hospedada publicamente
# Troque pela URL real quando tiver a imagem definitiva
IMAGE_URL = "https://mejulga.com.br/drajulga-post.jpg"


def criar_container(caption: str) -> str:
    """Cria container de mídia no Instagram."""
    url = f"{GRAPH_API_URL}/{INSTAGRAM_ACCOUNT_ID}/media"
    params = {
        "image_url": IMAGE_URL,
        "caption": caption,
        "access_token": ACCESS_TOKEN
    }
    r = requests.post(url, params=params)
    data = r.json()
    if "id" not in data:
        raise Exception(f"Erro ao criar container: {data}")
    return data["id"]


def publicar_container(container_id: str) -> str:
    """Publica o container no Instagram."""
    url = f"{GRAPH_API_URL}/{INSTAGRAM_ACCOUNT_ID}/media_publish"
    params = {
        "creation_id": container_id,
        "access_token": ACCESS_TOKEN
    }
    r = requests.post(url, params=params)
    data = r.json()
    if "id" not in data:
        raise Exception(f"Erro ao publicar: {data}")
    return data["id"]


def verificar_limite() -> bool:
    """Verifica quota de publicações (limite: 50/dia)."""
    url = f"{GRAPH_API_URL}/{INSTAGRAM_ACCOUNT_ID}/content_publishing_limit"
    params = {"fields": "config,quota_usage", "access_token": ACCESS_TOKEN}
    r = requests.get(url, params=params)
    data = r.json()
    if "data" in data and data["data"]:
        quota = data["data"][0].get("quota_usage", 0)
        total = data["data"][0].get("config", {}).get("quota_total", 50)
        print(f"📊 Publicações hoje: {quota}/{total}")
        return quota < total
    return True


def carregar_post(tipo: str) -> dict:
    """Carrega post do arquivo JSON do dia."""
    hoje = datetime.now().strftime("%Y-%m-%d")
    arquivo = Path(__file__).parent.parent / "content-engine" / "generated" / f"{hoje}.json"
    if not arquivo.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}\nRode generate_posts.py primeiro.")
    with open(arquivo, "r", encoding="utf-8") as f:
        data = json.load(f)
    for post in data.get("posts", []):
        if post.get("tipo") == tipo:
            return post
    raise ValueError(f"Post tipo '{tipo}' não encontrado.")


def registrar(post: dict, post_id: str):
    """Registra publicação no log de analytics."""
    hoje = datetime.now().strftime("%Y-%m-%d")
    pasta = Path(__file__).parent.parent / "analytics"
    pasta.mkdir(exist_ok=True)
    arquivo = pasta / f"{hoje}_publicacoes.json"
    log = {"data": hoje, "publicacoes": []}
    if arquivo.exists():
        with open(arquivo, "r", encoding="utf-8") as f:
            log = json.load(f)
    log["publicacoes"].append({
        "post_id": post_id,
        "tipo": post.get("tipo"),
        "categoria": post.get("categoria"),
        "horario": post.get("horario"),
        "publicado_em": datetime.now().isoformat()
    })
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print(f"📝 Log salvo: {arquivo}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--horario", required=True, choices=["12", "18", "21"])
    args = parser.parse_args()

    tipo = HORARIO_TIPO[args.horario]
    print(f"📱 Publicando post das {args.horario}h — tipo: {tipo}")

    if not ACCESS_TOKEN or not INSTAGRAM_ACCOUNT_ID:
        raise ValueError("Configure META_ACCESS_TOKEN e INSTAGRAM_ACCOUNT_ID no .env")

    if not verificar_limite():
        print("⚠️ Limite diário atingido!")
        return

    post = carregar_post(tipo)
    caption = f"{post.get('texto', '')}\n\n{post.get('hashtags', '')}"

    print(f"📝 Post: {post.get('categoria')} — {len(caption)} chars")
    print("-" * 40)
    print(caption[:200] + "..." if len(caption) > 200 else caption)
    print("-" * 40)

    print("⏳ Criando container...")
    container_id = criar_container(caption)
    print(f"✅ Container: {container_id}")

    print("⏳ Publicando...")
    post_id = publicar_container(container_id)
    print(f"✅ Publicado! Post ID: {post_id}")

    registrar(post, post_id)
    print(f"\n🎉 Post das {args.horario}h publicado no @dra.julga!")


if __name__ == "__main__":
    main()
