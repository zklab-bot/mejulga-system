"""
gerar_verdict_card.py
Gera imagem 1080x1080 com o veredicto para post isolado no Instagram.

Uso: python gerar_verdict_card.py --categoria amor
"""

import json
import argparse
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

LARGURA = 1080
ALTURA  = 1080

ROXO_PROFUNDO  = (30, 10, 70)
DOURADO        = (255, 193, 37)
BRANCO_PURO    = (255, 255, 255)
CINZA_MEDIO    = (150, 140, 165)
VERMELHO_STAMP = (200, 30, 30)


def encontrar_fonte(tamanho: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    fontes_bold = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    fontes_regular = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for caminho in (fontes_bold if bold else fontes_regular):
        try:
            return ImageFont.truetype(caminho, tamanho)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def wrap_text(texto: str, fonte: ImageFont.FreeTypeFont, largura_max: int,
              draw: ImageDraw.ImageDraw) -> list:
    palavras = texto.split()
    linhas = []
    linha_atual = ""
    for palavra in palavras:
        teste = (linha_atual + " " + palavra).strip()
        bbox = draw.textbbox((0, 0), teste, font=fonte)
        if bbox[2] <= largura_max:
            linha_atual = teste
        else:
            if linha_atual:
                linhas.append(linha_atual)
            linha_atual = palavra
    if linha_atual:
        linhas.append(linha_atual)
    return linhas


def gerar_verdict_card(roteiro: dict, pasta: Path) -> Path:
    hoje = datetime.now().strftime("%Y-%m-%d")
    categoria = roteiro.get("categoria", "geral")
    frase = roteiro.get("frase_printavel", "")
    crime = roteiro.get("crime", "")
    numero_processo = roteiro.get("numero_processo", "")

    img = Image.new("RGB", (LARGURA, ALTURA), ROXO_PROFUNDO)
    draw = ImageDraw.Draw(img)
    cx = LARGURA // 2

    # Linha dourada topo
    draw.rectangle([(80, 90), (LARGURA - 80, 94)], fill=DOURADO)

    # "TRIBUNAL POP" + processo
    fonte_label = encontrar_fonte(24, bold=False)
    draw.text((cx, 118), "TRIBUNAL POP", font=fonte_label, fill=DOURADO, anchor="mt")
    fonte_proc = encontrar_fonte(20, bold=False)
    draw.text((cx, 154), numero_processo, font=fonte_proc, fill=CINZA_MEDIO, anchor="mt")

    # Crime
    fonte_crime = encontrar_fonte(28, bold=False)
    draw.text((cx, 210), crime.upper(), font=fonte_crime, fill=CINZA_MEDIO, anchor="mt")

    # Carimbo VEREDICTO
    fonte_stamp = encontrar_fonte(52, bold=True)
    draw.text((cx, 295), "VEREDICTO", font=fonte_stamp, fill=VERMELHO_STAMP, anchor="mt")

    # Separador
    draw.rectangle([(80, 372), (LARGURA - 80, 375)], fill=CINZA_MEDIO)

    # Frase principal
    fonte_frase = encontrar_fonte(66, bold=True)
    margem = 90
    linhas = wrap_text(frase, fonte_frase, LARGURA - 2 * margem, draw)
    altura_bloco = len(linhas) * 82
    y = max(410, (ALTURA // 2) - (altura_bloco // 2) + 40)
    for linha in linhas:
        draw.text((cx, y), linha, font=fonte_frase, fill=BRANCO_PURO, anchor="mt")
        y += 82

    # Linha dourada inferior
    draw.rectangle([(80, ALTURA - 190), (LARGURA - 80, ALTURA - 186)], fill=DOURADO)

    # Assinatura
    fonte_assin = encontrar_fonte(30, bold=True)
    draw.text((cx, ALTURA - 168), "Dra. Julga", font=fonte_assin, fill=DOURADO, anchor="mt")
    fonte_url = encontrar_fonte(22, bold=False)
    draw.text((cx, ALTURA - 126), "mejulga.com.br", font=fonte_url, fill=CINZA_MEDIO, anchor="mt")

    # Linha final
    draw.rectangle([(80, ALTURA - 90), (LARGURA - 80, ALTURA - 86)], fill=DOURADO)

    caminho = pasta / f"{hoje}_{categoria}_verdict_card.png"
    img.save(caminho, "PNG")
    return caminho


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categoria", required=True)
    parser.add_argument("--data", default=None)
    args = parser.parse_args()

    hoje = args.data or datetime.now().strftime("%Y-%m-%d")
    pasta = Path(__file__).parent / "generated" / "reels"

    arq_json = pasta / f"{hoje}_{args.categoria}_reels.json"
    if not arq_json.exists():
        raise FileNotFoundError(f"Roteiro não encontrado: {arq_json}")

    with open(arq_json, encoding="utf-8") as f:
        roteiro = json.load(f)

    caminho = gerar_verdict_card(roteiro, pasta)
    print(f"✅ Verdict card gerado: {caminho}")


if __name__ == "__main__":
    main()
