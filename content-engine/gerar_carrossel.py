"""
gerar_carrossel.py
Gera 6 slides PNG para carrossel do Instagram:
  Slide 1 — Intro (convocação da Dra. Julga)
  Slides 2-5 — Uma cena por slide
  Slide 6 — Veredicto final + CTA

Uso: python gerar_carrossel.py --categoria dinheiro
"""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

LARGURA = 1080
ALTURA  = 1080  # quadrado — funciona melhor em carrossel

# Paleta
BRANCO       = (255, 255, 255)
ROXO_ESCURO  = (45, 16, 96)
ROXO_MEDIO   = (109, 68, 184)
ROXO_CLARO   = (168, 85, 247)
ROXO_BG      = (250, 248, 255)
ROXO_LINHA   = (233, 213, 255)

CATEGORIAS = [
    "dinheiro", "amor", "trabalho",
    "dopamina", "vida_adulta", "social", "saude_mental"
]

INTRO_TEXTOS = {
    "dinheiro":    "A Dra. Julga\nanalisou sua\nrelação com\no dinheiro...",
    "amor":        "A Dra. Julga\nanalisou sua\nvida amorosa...",
    "trabalho":    "A Dra. Julga\nanalisou sua\ncarreira...",
    "dopamina":    "A Dra. Julga\ndiagnosticou\nseu vício em\ndopamina digital...",
    "vida_adulta": "A Dra. Julga\navaliou sua\nvida adulta...",
    "social":      "A Dra. Julga\nanalisou sua\nvida social...",
    "saude_mental":"A Dra. Julga\nemitiu seu\nlaudo de\nsaúde mental...",
}


def encontrar_fonte(tamanho: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    fontes = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for f in fontes:
        if os.path.exists(f):
            return ImageFont.truetype(f, tamanho)
    return ImageFont.load_default()


def base_slide() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Cria imagem base com fundo e bordas."""
    img = Image.new("RGB", (LARGURA, ALTURA), ROXO_BG)
    draw = ImageDraw.Draw(img)
    # Borda lateral esquerda
    draw.rectangle([0, 0, 10, ALTURA], fill=ROXO_CLARO)
    # Borda lateral direita
    draw.rectangle([LARGURA-10, 0, LARGURA, ALTURA], fill=ROXO_CLARO)
    return img, draw


def texto_centrado(draw, texto: str, y: int, fonte, cor=None, max_largura: int = 920):
    """Desenha texto multilinha centrado."""
    if cor is None:
        cor = ROXO_ESCURO
    cx = LARGURA // 2
    linhas = texto.split("\n")
    for linha in linhas:
        draw.text((cx, y), linha, font=fonte, fill=cor, anchor="mm")
        bbox = draw.textbbox((0, 0), linha, font=fonte)
        y += (bbox[3] - bbox[1]) + 20
    return y


def slide_intro(categoria: str, numero: int, total: int) -> Image.Image:
    img, draw = base_slide()
    cx = LARGURA // 2

    # Número do slide
    fonte_num = encontrar_fonte(28, bold=False)
    draw.text((cx, 60), f"{numero} / {total}", font=fonte_num,
              fill=ROXO_CLARO, anchor="mm")

    # Ícone
    fonte_icone = encontrar_fonte(120)
    draw.text((cx, 230), "⚖", font=fonte_icone, fill=ROXO_ESCURO, anchor="mm")

    # Linha
    draw.rectangle([200, 290, LARGURA-200, 293], fill=ROXO_LINHA)

    # Título ME JULGA
    fonte_marca = encontrar_fonte(64)
    draw.text((cx, 360), "ME JULGA", font=fonte_marca,
              fill=ROXO_ESCURO, anchor="mm")

    # Texto intro
    fonte_txt = encontrar_fonte(52, bold=False)
    intro = INTRO_TEXTOS.get(categoria, "A Dra. Julga\ntem um recado\npara você...")
    texto_centrado(draw, intro, 460, fonte_txt, ROXO_MEDIO)

    # Rodapé
    fonte_footer = encontrar_fonte(30, bold=False)
    draw.text((cx, ALTURA-50), "@dra.julga  •  mejulga.com.br",
              font=fonte_footer, fill=ROXO_CLARO, anchor="mm")

    return img


def slide_cena(texto: str, numero_cena: int, numero_slide: int, total: int) -> Image.Image:
    img, draw = base_slide()
    cx = LARGURA // 2

    # Número do slide
    fonte_num = encontrar_fonte(28, bold=False)
    draw.text((cx, 60), f"{numero_slide} / {total}", font=fonte_num,
              fill=ROXO_CLARO, anchor="mm")

    # Label CENA
    fonte_label = encontrar_fonte(32, bold=False)
    draw.text((cx, 130), f"EVIDÊNCIA Nº {numero_cena}", font=fonte_label,
              fill=ROXO_CLARO, anchor="mm")

    # Linha
    draw.rectangle([80, 160, LARGURA-80, 163], fill=ROXO_LINHA)

    # Texto da cena — grande e central
    # Quebra automática
    palavras = texto.split()
    linhas = []
    linha_atual = []
    fonte_texto = encontrar_fonte(62)

    for palavra in palavras:
        linha_atual.append(palavra)
        linha_teste = " ".join(linha_atual)
        bbox = draw.textbbox((0, 0), linha_teste, font=fonte_texto)
        if bbox[2] > 900:
            if len(linha_atual) > 1:
                linhas.append(" ".join(linha_atual[:-1]))
                linha_atual = [palavra]
            else:
                linhas.append(linha_teste)
                linha_atual = []
    if linha_atual:
        linhas.append(" ".join(linha_atual))

    # Centrar verticalmente
    n = len(linhas)
    altura_total = n * 85
    y = (ALTURA - altura_total) // 2

    for linha in linhas:
        draw.text((cx, y), linha, font=fonte_texto,
                  fill=ROXO_ESCURO, anchor="mm")
        y += 85

    # Rodapé
    fonte_footer = encontrar_fonte(30, bold=False)
    draw.text((cx, ALTURA-50), "@dra.julga  •  mejulga.com.br",
              font=fonte_footer, fill=ROXO_CLARO, anchor="mm")

    return img


def slide_veredicto(conclusao: str, numero: int, total: int) -> Image.Image:
    img, draw = base_slide()
    cx = LARGURA // 2

    # Número do slide
    fonte_num = encontrar_fonte(28, bold=False)
    draw.text((cx, 60), f"{numero} / {total}", font=fonte_num,
              fill=ROXO_CLARO, anchor="mm")

    # Label VEREDICTO
    fonte_label = encontrar_fonte(36, bold=False)
    draw.text((cx, 130), "─── VEREDICTO FINAL ───", font=fonte_label,
              fill=ROXO_CLARO, anchor="mm")

    # Caixa branca
    draw.rounded_rectangle([60, 180, LARGURA-60, 700],
                           radius=24, fill=BRANCO, outline=ROXO_LINHA, width=3)

    # Conclusão
    palavras = conclusao.split()
    linhas = []
    linha_atual = []
    fonte_texto = encontrar_fonte(72)

    for palavra in palavras:
        linha_atual.append(palavra)
        linha_teste = " ".join(linha_atual)
        bbox = draw.textbbox((0, 0), linha_teste, font=fonte_texto)
        if bbox[2] > 860:
            if len(linha_atual) > 1:
                linhas.append(" ".join(linha_atual[:-1]))
                linha_atual = [palavra]
            else:
                linhas.append(linha_teste)
                linha_atual = []
    if linha_atual:
        linhas.append(" ".join(linha_atual))

    n = len(linhas)
    altura_bloco = n * 90
    y = 190 + (510 - altura_bloco) // 2

    for linha in linhas:
        draw.text((cx, y), linha, font=fonte_texto,
                  fill=ROXO_ESCURO, anchor="mm")
        y += 90

    # CTA roxo
    draw.rounded_rectangle([60, 730, LARGURA-60, 920],
                           radius=24, fill=ROXO_ESCURO)
    fonte_cta1 = encontrar_fonte(44)
    fonte_cta2 = encontrar_fonte(36, bold=False)
    draw.text((cx, 795), "Descobre o seu em", font=fonte_cta1,
              fill=BRANCO, anchor="mm")
    draw.text((cx, 860), "mejulga.com.br", font=fonte_cta2,
              fill=ROXO_CLARO, anchor="mm")

    # Rodapé
    fonte_footer = encontrar_fonte(30, bold=False)
    draw.text((cx, ALTURA-50), "@dra.julga  •  ME JULGA",
              font=fonte_footer, fill=ROXO_MEDIO, anchor="mm")

    return img


def carregar_roteiro(categoria: str, data: str) -> dict:
    pasta = Path(__file__).parent / "generated" / "reels"
    arquivo = pasta / f"{data}_{categoria}_reels.json"
    if not arquivo.exists():
        raise FileNotFoundError(f"Roteiro não encontrado: {arquivo}")
    with open(arquivo, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categoria", required=True, choices=CATEGORIAS)
    parser.add_argument("--data", default=None)
    args = parser.parse_args()

    hoje = args.data or datetime.now().strftime("%Y-%m-%d")
    categoria = args.categoria

    print(f"🎨 Gerando carrossel — {categoria} — {hoje}")

    roteiro = carregar_roteiro(categoria, hoje)
    cenas = roteiro.get("cenas", [])[:4]  # máximo 4 cenas
    conclusao = roteiro.get("conclusao", "Sem defesa possível.")
    if not conclusao and cenas:
        conclusao = cenas[-1]["texto"]

    total_slides = 6
    pasta_saida = Path(__file__).parent / "generated" / "reels"
    pasta_saida.mkdir(parents=True, exist_ok=True)

    slides = []

    # Slide 1 — Intro
    print(f"  📸 Slide 1/6 — Intro")
    s1 = slide_intro(categoria, 1, total_slides)
    p1 = pasta_saida / f"{hoje}_{categoria}_slide_01.png"
    s1.save(str(p1))
    slides.append(p1)

    # Slides 2-5 — Cenas
    for i, cena in enumerate(cenas):
        n = i + 2
        print(f"  📸 Slide {n}/6 — Cena {i+1}")
        img = slide_cena(cena["texto"], i+1, n, total_slides)
        p = pasta_saida / f"{hoje}_{categoria}_slide_0{n}.png"
        img.save(str(p))
        slides.append(p)

    # Preenche slides vazios se menos de 4 cenas
    for i in range(len(cenas), 4):
        n = i + 2
        img = slide_cena("...", i+1, n, total_slides)
        p = pasta_saida / f"{hoje}_{categoria}_slide_0{n}.png"
        img.save(str(p))
        slides.append(p)

    # Slide 6 — Veredicto
    print(f"  📸 Slide 6/6 — Veredicto")
    s6 = slide_veredicto(conclusao, 6, total_slides)
    p6 = pasta_saida / f"{hoje}_{categoria}_slide_06.png"
    s6.save(str(p6))
    slides.append(p6)

    print(f"\n✅ {len(slides)} slides gerados em {pasta_saida}")
    for s in slides:
        print(f"   {s.name}")

    return slides


if __name__ == "__main__":
    main()
