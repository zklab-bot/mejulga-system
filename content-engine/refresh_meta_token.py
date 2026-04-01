"""
refresh_meta_token.py
Renova o META_ACCESS_TOKEN (long-lived, 60 dias) e atualiza o GitHub Secret.

Pré-requisitos (GitHub Secrets necessários):
  META_ACCESS_TOKEN   — token atual (será renovado)
  META_APP_ID         — ID do app no Meta for Developers
  META_APP_SECRET     — Secret do app no Meta for Developers
  GH_PAT              — Personal Access Token com permissão secrets:write
  GH_REPO             — ex: "meuusuario/mejulga-system"

Uso: python refresh_meta_token.py
"""

import os
import sys
import base64
import json
import requests
from dotenv import load_dotenv

load_dotenv()

META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
META_APP_ID       = os.getenv("META_APP_ID")
META_APP_SECRET   = os.getenv("META_APP_SECRET")
GH_PAT            = os.getenv("GH_PAT")
GH_REPO           = os.getenv("GH_REPO")  # ex: "user/repo"


def renovar_token() -> str:
    """Troca o token atual por um novo long-lived token (60 dias)."""
    print("🔄 Renovando META_ACCESS_TOKEN...")
    resp = requests.get(
        "https://graph.facebook.com/v19.0/oauth/access_token",
        params={
            "grant_type":        "fb_exchange_token",
            "client_id":         META_APP_ID,
            "client_secret":     META_APP_SECRET,
            "fb_exchange_token": META_ACCESS_TOKEN,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        raise RuntimeError(f"Meta API erro: {data['error']['message']}")

    novo_token = data.get("access_token")
    expira_em  = data.get("expires_in", "desconhecido")
    print(f"✅ Novo token obtido. Expira em: {expira_em}s (~{int(expira_em or 0) // 86400} dias)")
    return novo_token


def obter_public_key_repo() -> tuple[str, int]:
    """Obtém a chave pública do repositório para cifrar o secret."""
    url  = f"https://api.github.com/repos/{GH_REPO}/actions/secrets/public-key"
    resp = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {GH_PAT}",
            "Accept":        "application/vnd.github+json",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["key"], data["key_id"]


def cifrar_secret(public_key_b64: str, valor: str) -> str:
    """Cifra o valor com a chave pública do repositório (libsodium/PyNaCl)."""
    try:
        from nacl import encoding, public
    except ImportError:
        raise ImportError(
            "PyNaCl não instalado. Execute: pip install PyNaCl"
        )

    chave_publica = public.PublicKey(
        public_key_b64.encode("utf-8"),
        encoding.Base64Encoder,
    )
    caixa_selada  = public.SealedBox(chave_publica)
    cifrado       = caixa_selada.encrypt(valor.encode("utf-8"))
    return base64.b64encode(cifrado).decode("utf-8")


def atualizar_github_secret(nome_secret: str, novo_valor: str):
    """Atualiza o secret no GitHub Actions via API."""
    print(f"🔑 Atualizando GitHub Secret: {nome_secret}...")

    pub_key, key_id = obter_public_key_repo()
    valor_cifrado   = cifrar_secret(pub_key, novo_valor)

    url  = f"https://api.github.com/repos/{GH_REPO}/actions/secrets/{nome_secret}"
    resp = requests.put(
        url,
        headers={
            "Authorization": f"Bearer {GH_PAT}",
            "Accept":        "application/vnd.github+json",
        },
        json={
            "encrypted_value": valor_cifrado,
            "key_id":          key_id,
        },
        timeout=10,
    )

    if resp.status_code in (201, 204):
        print(f"✅ {nome_secret} atualizado no GitHub.")
    else:
        raise RuntimeError(
            f"Erro ao atualizar secret: {resp.status_code} — {resp.text}"
        )


def validar_env():
    faltando = [
        v for v in ["META_ACCESS_TOKEN", "META_APP_ID", "META_APP_SECRET",
                    "GH_PAT", "GH_REPO"]
        if not os.getenv(v)
    ]
    if faltando:
        print(f"❌ Variáveis ausentes: {', '.join(faltando)}")
        sys.exit(1)


def main():
    validar_env()

    novo_token = renovar_token()
    atualizar_github_secret("META_ACCESS_TOKEN", novo_token)

    print("\n🎉 Token renovado e GitHub Secret atualizado com sucesso.")
    print("   Próxima renovação automática em ~50 dias.")


if __name__ == "__main__":
    main()
