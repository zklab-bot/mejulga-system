"""
cena_minimalista.py
Teste 1 — Post minimalista: fundo branco + texto roxo + voz narrando tudo.
Um único frame estático enquanto o áudio narra toda a história.
Uso: python generate_video.py --categoria dinheiro --estilo minimalista
"""

from PIL import Image, ImageDraw, ImageFont
import os

LARGURA = 1080
ALTURA = 1920

# Paleta roxo
BRANCO        = (255, 255, 255)
ROXO_ESCURO   = (45, 16, 96)
ROXO_MEDIO    = (109, 68, 184)
ROXO_CLARO    = (168, 85, 247)
ROXO_ULTRA    = (237, 230, 255)
CINZA_SUAVE   = (245, 243, 255)
CINZA_LINHA   = (220, 210, 245)


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


def quebrar_texto(texto: str, max_chars: int = 18) -> list:
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


def cena_minimalista(roteiro: dict) -> Image.Image:
    """
    Gera um único frame minimalista:
    - Fundo branco puro
    - Marca @dra.julga no topo
    - Veredicto final em roxo escuro, grande, centralizado
    - Linha decorativa roxa
    - Rodapé mejulga.com.br
    """
    img = Image.new("RGB", (LARGURA, ALTURA), BRANCO)
    draw = ImageDraw.Draw(img)

    cx = LARGURA // 2

    # Fundo levemente tingido (quase branco)
    draw.rectangle([0, 0, LARGURA, ALTURA], fill=CINZA_SUAVE)

    # Borda sutil nas laterais
    draw.rectangle([0, 0, 12, ALTURA], fill=ROXO_CLARO)
    draw.rectangle([LARGURA-12, 0, LARGURA, ALTURA], fill=ROXO_CLARO)

    # ── TOPO ──────────────────────────────────────────────────────
    fonte_marca = encontrar_fonte(52)
    fonte_sub   = encontrar_fonte(32, bold=False)

    draw.text((cx, 160), "ME JULGA", font=fonte_marca, fill=ROXO_ESCURO, anchor="mm")
    draw.text((cx, 220), "com a Dra. Julga", font=fonte_sub, fill=ROXO_MEDIO, anchor="mm")

    # Linha decorativa topo
    draw.rectangle([cx-200, 260, cx+200, 263], fill=ROXO_CLARO)

    # ── ÍCONE CENTRAL (círculo com símbolo de justiça) ────────────
    iy = 440
    r = 120
    draw.ellipse([cx-r, iy-r, cx+r, iy+r], fill=ROXO_ESCURO)
    draw.ellipse([cx-r+6, iy-r+6, cx+r-6, iy+r-6], fill=ROXO_ESCURO, outline=ROXO_CLARO, width=3)

    fonte_icone = encontrar_fonte(110)
    draw.text((cx, iy), "⚖", font=fonte_icone, fill=BRANCO, anchor="mm")

    # ── RÓTULO "VEREDICTO FINAL" ──────────────────────────────────
    vy = 630
    fonte_rotulo = encontrar_fonte(36, bold=False)
    draw.text((cx, vy), "─── VEREDICTO FINAL ───", font=fonte_rotulo, fill=ROXO_CLARO, anchor="mm")

    # ── TEXTO PRINCIPAL (veredicto) ───────────────────────────────
    cenas   = roteiro.get("cenas", [])
    # Pega a última cena (diagnóstico final) ou todas se quiser
    conclusao = roteiro.get("conclusao", "")
    if not conclusao:
        # Fallback: usa texto da última cena
        conclusao = cenas[-1]["texto"] if cenas else "Sem defesa possível."

    linhas  = quebrar_texto(conclusao, max_chars=16)
    n       = len(linhas)
    fonte_v = encontrar_fonte(100 if n <= 2 else 78 if n <= 3 else 64)
    altura_bloco = n * 110
    y_inicio = 800 - altura_bloco // 2

    for i, linha in enumerate(linhas):
        y = y_inicio + i * 110
        # Sombra leve
        draw.text((cx+3, y+3), linha, font=fonte_v, fill=ROXO_ULTRA, anchor="mm")
        draw.text((cx, y), linha, font=fonte_v, fill=ROXO_ESCURO, anchor="mm")

    # ── LINHA SEPARADORA ──────────────────────────────────────────
    draw.rectangle([80, 1050, LARGURA-80, 1053], fill=CINZA_LINHA)

    # ── RESUMO DAS CENAS (pequeno, discreto) ──────────────────────
    fonte_resumo = encontrar_fonte(30, bold=False)
    y_res = 1090
    draw.text((cx, y_res), "A história completa está no áudio  ▶", font=fonte_resumo, fill=ROXO_CLARO, anchor="mm")

    # Bullets das cenas
    fonte_bullet = encontrar_fonte(26, bold=False)
    y_bul = 1150
    for cena in cenas[:5]:
        txt = f"· {cena['texto'][:42]}{'…' if len(cena['texto']) > 42 else ''}"
        draw.text((cx, y_bul), txt, font=fonte_bullet, fill=ROXO_MEDIO, anchor="mm")
        y_bul += 50

    # ── BLOCO CTA ROXO ────────────────────────────────────────────
    draw.rounded_rectangle([80, 1530, LARGURA-80, 1720], radius=30, fill=ROXO_ESCURO)
    fonte_cta1 = encontrar_fonte(52)
    fonte_cta2 = encontrar_fonte(40, bold=False)
    draw.text((cx, 1600), "Descobre o seu em", font=fonte_cta1, fill=BRANCO, anchor="mm")
    draw.text((cx, 1670), "mejulga.com.br", font=fonte_cta2, fill=ROXO_CLARO, anchor="mm")

    # ── RODAPÉ ────────────────────────────────────────────────────
    fonte_footer = encontrar_fonte(30, bold=False)
    draw.text((cx, 1820), "@dra.julga  •  ME JULGA", font=fonte_footer, fill=ROXO_MEDIO, anchor="mm")

    return img
