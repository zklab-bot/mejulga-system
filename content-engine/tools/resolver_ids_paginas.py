"""
resolver_ids_paginas.py
Resolve usernames do Instagram para IDs numéricos via Meta Graph API.
Uso: python tools/resolver_ids_paginas.py

Resultado: cola os IDs no PAGINAS_ALVO de comment_growth.py
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")

USERNAMES_ALVO = [
    "fofocasbrasil",
    "polemicasbr",
    "gossipbr",
    "memesbr",
    "humorbrasileiro",
    "choquei",
    "colunistas_br",
    "gofofocas",
]


def resolver_id(username: str) -> str | None:
    resp = requests.get(
        f"https://graph.facebook.com/v19.0/{username}",
        params={"fields": "id,username", "access_token": META_ACCESS_TOKEN},
        timeout=10,
    )
    if resp.status_code == 200:
        data = resp.json()
        return data.get("id")
    return None


def main():
    print("Resolvendo IDs de páginas alvo...\n")
    print("# Cole no PAGINAS_ALVO em comment_growth.py:")
    print("PAGINAS_ALVO: list[dict] = [")
    for username in USERNAMES_ALVO:
        uid = resolver_id(username)
        if uid:
            print(f'    {{"id": "{uid}", "nome": "{username}"}},')
        else:
            print(f'    # {username}: não encontrado (verifique permissões ou username)')
    print("]")


if __name__ == "__main__":
    main()
