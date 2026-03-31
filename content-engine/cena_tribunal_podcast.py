"""
cena_tribunal_podcast.py
Teste 2 — Cenário tribunal + podcast: mesa, microfone, martelo, iluminação dramática.
A Dra. Julga olhando para câmera dando o julgamento final.
"""

import math
from PIL import Image, ImageDraw, ImageFont
import os

LARGURA = 1080
ALTURA  = 1920

# Paleta
PRETO         = (5, 3, 12)
ROXO_ESCURO   = (15, 8, 40)
ROXO_PROFUNDO = (28, 12, 68)
ROXO_MEDIO    = (80, 40, 160)
ROXO_VIBRANTE = (124, 58, 237)
ROXO_CLARO    = (168, 85, 247)
ROXO_NEON     = (200, 130, 255)
DOURADO       = (212, 175, 55)
DOURADO_ESCURO= (140, 110, 20)
BRANCO        = (255, 255, 255)
VERMELHO      = (220, 50, 50)
CINZA_ESCURO  = (40, 35, 60)
BEGE          = (245, 235, 210)
MADEIRA       = (90, 55, 25)
MADEIRA_ESCURA= (55, 30, 10)


def encontrar_fonte(tamanho: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    fontes = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/verdanab.ttf" if bold else "C:/Windows/Fonts/verdana.ttf",
    ]
    for f in fontes:
        if os.path.exists(f):
            return ImageFont.truetype(f, tamanho)
    return ImageFont.load_default()


def quebrar_texto(texto: str, max_chars: int = 20) -> list:
    palavras = texto.split()
    linhas, linha = [], []
    for p in palavras:
        linha.append(p)
        if len(" ".join(linha)) > max_chars:
            if len(linha) > 1:
                linhas.append(" ".join(linha[:-1]))
                linha = [p]
            else:
                linhas.append(" ".join(linha))
                linha = []
    if linha:
        linhas.append(" ".join(linha))
    return linhas


def desenhar_halo(draw, cx, cy, r_max, cor, steps=6):
    """Halo de luz ao redor da silhueta."""
    for i in range(steps):
        alpha_frac = (steps - i) / steps
        r = r_max - i * 12
        opacity = int(30 * alpha_frac)
        cor_alpha = cor + (opacity,)
        # Simula com ellipse transparente (PIL RGB, só fill sólido)
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=cor, width=1)


def cena_tribunal_podcast(roteiro: dict) -> Image.Image:
    """
    Cenário tribunal/podcast:
    - Fundo escuro dramático com gradiente roxo
    - Holofote vindo de cima (triângulo de luz)
    - Mesa de madeira com detalhes dourados
    - Microfone de podcast na mesa
    - Martelo de juíza
    - Silhueta frontal da Dra. Julga (olhando para a câmera)
    - Toga e peruca estilizadas
    - Texto do julgamento em destaque
    - Elementos decorativos: colunas, bandeira, emblema
    """
    img = Image.new("RGB", (LARGURA, ALTURA), ROXO_ESCURO)
    draw = ImageDraw.Draw(img)
    cx = LARGURA // 2

    # ── FUNDO: parede com textura de painéis ─────────────────────
    for i in range(0, LARGURA, 80):
        draw.line([i, 0, i, 1100], fill=(20, 12, 50), width=1)
    for j in range(0, 1100, 120):
        draw.line([0, j, LARGURA, j], fill=(20, 12, 50), width=1)

    # Gradiente de fundo (simulado com retângulos)
    for y in range(0, 1100, 4):
        frac = y / 1100
        r = int(15 + frac * 10)
        g = int(8 + frac * 5)
        b = int(40 + frac * 20)
        draw.rectangle([0, y, LARGURA, y+4], fill=(r, g, b))

    # ── HOLOFOTE (feixe de luz vindo do topo) ────────────────────
    # Triângulo de luz levemente amarelado
    for camada in range(8):
        opacity = 18 - camada * 2
        largura_feixe = 300 + camada * 60
        draw.polygon([
            (cx, -30),
            (cx - largura_feixe, 900 + camada * 20),
            (cx + largura_feixe, 900 + camada * 20)
        ], fill=(255, 250, 220))
        # Cobre com roxo para simular fade
        draw.polygon([
            (cx, -30),
            (cx - largura_feixe, 900 + camada * 20),
            (cx + largura_feixe, 900 + camada * 20)
        ], fill=(15, 8, 40))

    # Feixe real (mais visível)
    draw.polygon([
        (cx, 0),
        (cx - 200, 950),
        (cx + 200, 950)
    ], fill=(255, 252, 230))
    # Reaplica fundo por cima com transparência simulada
    for y in range(0, 950, 6):
        frac = y / 950
        alpha = int(180 * (1 - frac * 0.3))
        r = int(15 + frac * 10)
        g = int(8 + frac * 5)
        b = int(40 + frac * 20)
        largura_em_y = int(200 * (y / 950))
        draw.rectangle([0, y, cx - largura_em_y - 1, y + 6], fill=(r, g, b))
        draw.rectangle([cx + largura_em_y + 1, y, LARGURA, y + 6], fill=(r, g, b))

    # ── COLUNAS LATERAIS ─────────────────────────────────────────
    for col_x in [60, LARGURA - 100]:
        draw.rectangle([col_x, 100, col_x + 40, 950], fill=(30, 18, 65))
        draw.rectangle([col_x - 10, 95, col_x + 50, 115], fill=DOURADO_ESCURO)
        draw.rectangle([col_x - 10, 945, col_x + 50, 965], fill=DOURADO_ESCURO)
        # Estrias da coluna
        for yc in range(150, 940, 40):
            draw.rectangle([col_x + 5, yc, col_x + 35, yc + 2], fill=(45, 28, 90))

    # ── EMBLEMA/BRASÃO no topo ────────────────────────────────────
    ey, er = 120, 70
    draw.ellipse([cx - er, ey - er, cx + er, ey + er], fill=ROXO_PROFUNDO, outline=DOURADO, width=3)
    draw.ellipse([cx - er + 8, ey - er + 8, cx + er - 8, ey + er - 8], outline=DOURADO_ESCURO, width=1)
    fonte_brasao = encontrar_fonte(60)
    draw.text((cx, ey), "⚖", font=fonte_brasao, fill=DOURADO, anchor="mm")

    # ── SILHUETA DA DRA. JULGA ────────────────────────────────────
    # Posição central, olhando para a câmera (vista frontal)
    sx, sy = cx, 580

    # Toga (corpo) — forma trapezoidal larga
    toga_pontos = [
        (sx - 240, sy + 350),   # base esquerda
        (sx + 240, sy + 350),   # base direita
        (sx + 160, sy - 120),   # ombro direito
        (sx - 160, sy - 120),   # ombro esquerdo
    ]
    draw.polygon(toga_pontos, fill=(18, 10, 45))
    # Borda da toga
    draw.line([
        (sx - 160, sy - 120), (sx - 240, sy + 350)
    ], fill=ROXO_MEDIO, width=4)
    draw.line([
        (sx + 160, sy - 120), (sx + 240, sy + 350)
    ], fill=ROXO_MEDIO, width=4)

    # Detalhes da toga: faixa roxa no meio
    draw.polygon([
        (sx - 25, sy - 120),
        (sx + 25, sy - 120),
        (sx + 40, sy + 350),
        (sx - 40, sy + 350),
    ], fill=ROXO_MEDIO)

    # Gola/colarinho branco
    draw.polygon([
        (sx - 70, sy - 115),
        (sx + 70, sy - 115),
        (sx + 50, sy - 50),
        (sx - 50, sy - 50),
    ], fill=(230, 225, 240))
    draw.polygon([
        (sx - 30, sy - 115),
        (sx + 30, sy - 115),
        (sx + 20, sy - 50),
        (sx - 20, sy - 50),
    ], fill=BRANCO)

    # Pescoço
    draw.rectangle([sx - 28, sy - 200, sx + 28, sy - 110], fill=(180, 140, 110))

    # Cabeça
    draw.ellipse([sx - 90, sy - 370, sx + 90, sy - 195], fill=(185, 145, 112))

    # ── PERUCA (estilo juíza clássica) ────────────────────────────
    # Base da peruca (cobre toda a cabeça)
    draw.ellipse([sx - 105, sy - 380, sx + 105, sy - 200], fill=(240, 235, 220))
    # Encaracolados laterais
    for lado in [-1, 1]:
        px = sx + lado * 95
        for i in range(4):
            py = sy - 340 + i * 38
            draw.ellipse([px - 25, py - 18, px + 25, py + 18], fill=(235, 230, 215))
            draw.ellipse([px - 20, py - 14, px + 20, py + 14], outline=(200, 195, 180), width=2)
    # Topo da peruca (bun)
    draw.ellipse([sx - 50, sy - 410, sx + 50, sy - 340], fill=(240, 235, 220))

    # ── ROSTO (frontal, expressão séria) ─────────────────────────
    # Olhos
    for ex in [sx - 32, sx + 32]:
        draw.ellipse([ex - 14, sy - 305, ex + 14, sy - 275], fill=(50, 35, 20))
        draw.ellipse([ex - 10, sy - 300, ex + 10, sy - 280], fill=(25, 15, 5))
        draw.ellipse([ex + 4, sy - 298, ex + 8, sy - 294], fill=BRANCO)

    # Sobrancelhas arqueadas (sérias)
    for ex in [sx - 32, sx + 32]:
        draw.arc([ex - 18, sy - 325, ex + 18, sy - 295], start=200, end=340, fill=(60, 40, 20), width=4)

    # Nariz
    draw.polygon([
        (sx, sy - 275),
        (sx - 10, sy - 245),
        (sx + 10, sy - 245),
    ], fill=(160, 120, 90))

    # Boca (leve sorriso irônico)
    draw.arc([sx - 22, sy - 245, sx + 22, sy - 220], start=10, end=170, fill=(120, 70, 60), width=3)

    # ── ÓCULOS DA DRA. JULGA ─────────────────────────────────────
    for ex in [sx - 32, sx + 32]:
        draw.ellipse([ex - 22, sy - 312, ex + 22, sy - 272], outline=DOURADO, width=3)
    draw.line([sx - 10, sy - 292, sx + 10, sy - 292], fill=DOURADO, width=3)
    # Hastes
    draw.line([sx - 54, sy - 292, sx - 90, sy - 285], fill=DOURADO, width=2)
    draw.line([sx + 54, sy - 292, sx + 90, sy - 285], fill=DOURADO, width=2)

    # ── MESA DE MADEIRA ──────────────────────────────────────────
    my = 940
    # Superfície da mesa
    draw.rounded_rectangle([40, my, LARGURA - 40, my + 90], radius=8, fill=MADEIRA)
    draw.rounded_rectangle([40, my, LARGURA - 40, my + 12], radius=8, fill=(110, 70, 30))
    # Pés da mesa (visíveis)
    for px in [120, LARGURA - 160]:
        draw.rectangle([px, my + 90, px + 40, my + 200], fill=MADEIRA_ESCURA)

    # Borda dourada da mesa
    draw.rounded_rectangle([40, my, LARGURA - 40, my + 90], radius=8, outline=DOURADO_ESCURO, width=3)

    # ── MICROFONE DE PODCAST ─────────────────────────────────────
    mic_x, mic_y = cx - 180, my - 10

    # Braço do mic
    draw.line([mic_x, mic_y, mic_x, mic_y - 180], fill=CINZA_ESCURO, width=8)
    draw.line([mic_x, mic_y - 180, mic_x + 60, mic_y - 180], fill=CINZA_ESCURO, width=8)
    draw.line([mic_x + 60, mic_y - 180, mic_x + 60, mic_y - 80], fill=CINZA_ESCURO, width=8)

    # Cabeça do microfone
    draw.ellipse([mic_x + 30, mic_y - 140, mic_x + 90, mic_y - 40], fill=(45, 45, 55))
    draw.ellipse([mic_x + 35, mic_y - 135, mic_x + 85, mic_y - 45], fill=(60, 60, 70))
    # Grade do mic
    for yi in range(mic_y - 125, mic_y - 55, 12):
        draw.line([mic_x + 40, yi, mic_x + 80, yi], fill=(80, 80, 90), width=1)

    # LED vermelho (ON AIR)
    draw.ellipse([mic_x + 52, mic_y - 155, mic_x + 68, mic_y - 145], fill=VERMELHO)

    # ── MARTELO DE JUÍZA ─────────────────────────────────────────
    ham_x, ham_y = cx + 160, my - 20

    # Cabo
    draw.rounded_rectangle([ham_x - 8, ham_y - 130, ham_x + 8, ham_y + 20], radius=4, fill=MADEIRA)

    # Cabeça do martelo
    draw.rounded_rectangle([ham_x - 55, ham_y - 160, ham_x + 55, ham_y - 105], radius=8, fill=(50, 45, 55))
    draw.rounded_rectangle([ham_x - 50, ham_y - 157, ham_x + 50, ham_y - 108], radius=6, outline=DOURADO_ESCURO, width=2)

    # Base do martelo (bloquinho de madeira)
    draw.rounded_rectangle([ham_x - 40, ham_y - 20, ham_x + 40, ham_y], radius=4, fill=MADEIRA_ESCURA)

    # ── PLACA "ON AIR" ────────────────────────────────────────────
    fonte_onair = encontrar_fonte(28, bold=False)
    draw.rounded_rectangle([cx + 260, my - 80, cx + 400, my - 40], radius=6, fill=VERMELHO)
    draw.text((cx + 330, my - 60), "● ON AIR", font=fonte_onair, fill=BRANCO, anchor="mm")

    # ── TEXTO: PROGRAMA ──────────────────────────────────────────
    fonte_prog = encontrar_fonte(34, bold=False)
    draw.text((cx, my + 120), "TRIBUNAL DA DRA. JULGA", font=fonte_prog, fill=DOURADO, anchor="mm")

    # ── FAIXA DE TEXTO PRINCIPAL ─────────────────────────────────
    # Pega o veredicto final do roteiro
    cenas = roteiro.get("cenas", [])
    conclusao = roteiro.get("conclusao", "")
    if not conclusao and cenas:
        conclusao = cenas[-1]["texto"]
    if not conclusao:
        conclusao = "Sem defesa possível."

    # Caixa de veredicto
    draw.rounded_rectangle([40, 1200, LARGURA - 40, 1520], radius=20,
                            fill=(12, 6, 30), outline=ROXO_VIBRANTE, width=3)

    fonte_rotulo = encontrar_fonte(32, bold=False)
    draw.text((cx, 1240), "▸  VEREDICTO FINAL  ◂", font=fonte_rotulo, fill=ROXO_NEON, anchor="mm")
    draw.line([80, 1265, LARGURA - 80, 1266], fill=ROXO_MEDIO, width=1)

    linhas = quebrar_texto(conclusao, max_chars=18)
    fonte_v = encontrar_fonte(88 if len(linhas) <= 2 else 68 if len(linhas) <= 3 else 56)
    y_txt = 1310
    for linha in linhas:
        draw.text((cx, y_txt), linha, font=fonte_v, fill=BRANCO, anchor="mm")
        y_txt += 95

    # ── RODAPÉ CTA ───────────────────────────────────────────────
    draw.rounded_rectangle([80, 1600, LARGURA - 80, 1770], radius=25, fill=ROXO_VIBRANTE)
    fonte_cta = encontrar_fonte(52)
    draw.text((cx, 1665), "Descobre o seu", font=fonte_cta, fill=BRANCO, anchor="mm")
    draw.text((cx, 1725), "mejulga.com.br", font=encontrar_fonte(42, bold=False), fill=(230, 210, 255), anchor="mm")

    fonte_footer = encontrar_fonte(30, bold=False)
    draw.text((cx, 1850), "@dra.julga  •  ME JULGA", font=fonte_footer, fill=ROXO_CLARO, anchor="mm")

    return img
