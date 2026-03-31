"""
gerar_imagem_actions.py
Gera imagem PNG minimalista directamente a partir do roteiro JSON.
Não depende de áudio, moviepy ou ffmpeg — funciona no GitHub Actions.

Uso: python gerar_imagem_actions.py --categoria dinheiro
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Adiciona o diretório actual ao path para importar cena_minimalista
sys.path.insert(0, str(Path(__file__).parent))

LARGURA = 1080
ALTURA  = 1920

CATEGORIAS = [
    "dinheiro", "amor", "trabalho",
    "dopamina", "vida_adulta", "social", "saude_mental"
]


def carregar_roteiro(categoria: str, data: str) -> dict:
    pasta = Path(__file__).parent / "generated" / "reels"
    arquivo = pasta / f"{data}_{categoria}_reels.json"
    if not arquivo.exists():
        raise FileNotFoundError(f"Roteiro não encontrado: {arquivo}")
    with open(arquivo, "r", encoding="utf-8") as f:
        return json.load(f)


def gerar_png(roteiro: dict, caminho_saida: Path):
    """Gera PNG usando cena_minimalista sem depender de moviepy/áudio."""
    from cena_minimalista import cena_minimalista
    img = cena_minimalista(roteiro)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(caminho_saida), "PNG")
    tamanho = caminho_saida.stat().st_size // 1024
    print(f"  ✅ PNG gerado: {caminho_saida.name} ({tamanho}KB)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categoria", required=True, choices=CATEGORIAS)
    parser.add_argument("--data", default=None)
    args = parser.parse_args()

    hoje = args.data or datetime.now().strftime("%Y-%m-%d")
    categoria = args.categoria

    print(f"🎨 Gerando imagem PNG — {categoria} — {hoje}")

    roteiro = carregar_roteiro(categoria, hoje)

    pasta = Path(__file__).parent / "generated" / "reels"
    caminho_saida = pasta / f"{hoje}_{categoria}_minimalista_reels.png"

    gerar_png(roteiro, caminho_saida)

    print(f"✅ Imagem pronta: {caminho_saida}")


if __name__ == "__main__":
    main()
