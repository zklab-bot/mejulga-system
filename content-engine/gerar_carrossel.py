"""
gerar_carrossel.py — v2 "Tribunal Pop"
Gera 6 slides PNG para carrossel do Instagram.

Design: Uma (@ux-design-expert) + @oalanicolas
Copy: Copy Chief + Voice DNA da Dra. Julga

Regras do personagem (Voice DNA):
- Frases curtas. Declarativas. Ritmo de 3.
- A Dra. Julga afirma. Ela nunca pergunta.
- Ela fala em terceira pessoa sobre si mesma.
- Nunca emoji. Nunca relativiza. Nunca é fofa.

Uso: python gerar_carrossel.py --categoria amor
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
ALTURA  = 1080

# ─── Paleta "Tribunal Pop" ────────────────────────────────────────────────────
ROXO_PROFUNDO  = (30, 10, 70)       # cabeçalho, rodapé
ROXO_VIBRANTE  = (138, 43, 226)     # texto destaque área clara
ROXO_NEON      = (185, 103, 255)    # acentos, indicadores, rodapé
CINZA_SUAVE    = (245, 243, 250)    # fundo área de conteúdo
DOURADO        = (255, 193, 37)     # labels jurídicos, URL, ornamentos
BRANCO_PURO    = (255, 255, 255)    # texto sobre fundo escuro
ROXO_BORDA     = (100, 50, 170)     # bordas de caixas
ROXO_SOMBRA    = (20, 5, 50)        # sombra da caixa veredicto
VERMELHO_STAMP = (200, 30, 30)      # carimbo CULPADO

# ─── Categorias ───────────────────────────────────────────────────────────────
CATEGORIAS = [
    "dinheiro", "amor", "trabalho",
    "dopamina", "vida_adulta", "social", "saude_mental"
]

# ─── Copy — Voice DNA da Dra. Julga ──────────────────────────────────────────
# Regra: ritmo de 3 (Afirmação. Evidência. Veredicto.)
# Nunca pergunta retórica. A Dra. Julga não pede — ela intima.

INTRO_TEXTOS = {
    "dinheiro":    "A Dra. Julga\nacessou seu extrato.\nO veredicto?\nIndefensável.",
    "amor":        "A Dra. Julga\nleu suas mensagens.\nTodas.\nAté as apagadas.",
    "trabalho":    "A Dra. Julga\nmonitorou sua segunda-feira.\nDe 8h às 18h.\nVocê trabalhou 47 min.",
    "dopamina":    "A Dra. Julga\ncronometrou seu tempo de tela.\nSão 7h14 por dia.\nEla está preocupada. Você, não.",
    "vida_adulta": "A Dra. Julga\nvisitou sua geladeira.\nTinha ketchup,\numa cerveja e arrependimento.",
    "social":      "A Dra. Julga\nviu que você cancelou.\nDe novo.\nTerceiro sábado seguido.",
    "saude_mental":"A Dra. Julga\nacessou seus pensamentos\ndas 3h da manhã.\nO processo precisou de volume 2.",
}

# Labels rotativos — variam por cena para evitar monotonia
LABELS_EVIDENCIA = [
    "PROVA Nº {}",
    "AUTO DE ACUSAÇÃO Nº {}",
    "FLAGRANTE Nº {}",
    "REGISTRO DE OCORRÊNCIA Nº {}",
    "DEPOIMENTO Nº {}",
]

# CTA Veredicto — variação "desafio" (Copy Chief)
VEREDICTO_CTA_L1 = "Esse foi o julgamento dos outros."
VEREDICTO_CTA_L2 = "O seu é pior."
VEREDICTO_CTA_L3 = "mejulga.com.br"


# ─── Tipografia ───────────────────────────────────────────────────────────────

def encontrar_fonte(tamanho: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    if bold:
        fontes = [
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
    else:
        fontes = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    for f in fontes:
        if os.path.exists(f):
            return ImageFont.truetype(f, tamanho)
    return ImageFont.load_default()


# ─── Elementos visuais PIL ────────────────────────────────────────────────────

def desenhar_balanca(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                     tamanho: int = 52, cor=DOURADO):
    """Balança da justiça desenhada com primitivas — substitui emoji quebrado."""
    # Poste central
    draw.rectangle([cx - 3, cy - tamanho, cx + 3, cy + tamanho // 2], fill=cor)
    # Base
    draw.rectangle([cx - 30, cy + tamanho // 2 - 3,
                    cx + 30, cy + tamanho // 2 + 6], fill=cor)
    # Barra horizontal
    draw.rectangle([cx - tamanho, cy - tamanho,
                    cx + tamanho, cy - tamanho + 4], fill=cor)
    # Correntes
    draw.line([cx - tamanho, cy - tamanho + 4,
               cx - tamanho, cy - tamanho + 24], fill=cor, width=2)
    draw.line([cx + tamanho, cy - tamanho + 4,
               cx + tamanho, cy - tamanho + 24], fill=cor, width=2)
    # Pratos (elipses)
    pr = 20
    draw.ellipse([cx - tamanho - pr, cy - tamanho + 24,
                  cx - tamanho + pr, cy - tamanho + 36], fill=cor)
    draw.ellipse([cx + tamanho - pr, cy - tamanho + 24,
                  cx + tamanho + pr, cy - tamanho + 36], fill=cor)


def desenhar_martelo(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                     tamanho: int = 40, cor=DOURADO):
    """Martelo de juiz desenhado com primitivas."""
    # Cabo
    draw.rectangle([cx - 3, cy, cx + 3, cy + tamanho], fill=cor)
    # Cabeça
    draw.rounded_rectangle([cx - tamanho // 2, cy - tamanho // 3,
                             cx + tamanho // 2, cy + tamanho // 5],
                            radius=5, fill=cor)


def _desenhar_dots(draw: ImageDraw.ImageDraw, slide_atual: int, total: int):
    """Indicador de progresso em dots no rodapé escuro."""
    dot_y   = ALTURA - 52
    dot_r   = 5
    dot_gap = 26
    total_w = (total - 1) * dot_gap
    start_x = LARGURA // 2 - total_w // 2
    for i in range(total):
        dx   = start_x + i * dot_gap
        fill = DOURADO if (i + 1 == slide_atual) else ROXO_NEON
        draw.ellipse([dx - dot_r, dot_y - dot_r,
                      dx + dot_r, dot_y + dot_r], fill=fill)


def _desenhar_carimbo(img: Image.Image):
    """Carimbo 'CULPADO' rotacionado — desordem controlada (@oalanicolas)."""
    stamp = Image.new("RGBA", (340, 100), (0, 0, 0, 0))
    sd    = ImageDraw.Draw(stamp)

    fonte_path = "C:/Windows/Fonts/arialbd.ttf"
    if os.path.exists(fonte_path):
        fonte_stamp = ImageFont.truetype(fonte_path, 68)
    else:
        fonte_stamp = ImageFont.load_default()

    # Borda vermelha arredondada
    sd.rounded_rectangle([4, 4, 336, 96], radius=10,
                          fill=None, outline=(*VERMELHO_STAMP, 210), width=5)
    # Texto
    sd.text((170, 50), "CULPADO", font=fonte_stamp,
            fill=(*VERMELHO_STAMP, 195), anchor="mm")

    # Rotacionar 15° — levemente torto (desordem intencional)
    stamp_rot = stamp.rotate(15, expand=True)

    # Posição: sobreposto no canto superior direito da caixa do veredicto
    paste_x = LARGURA - stamp_rot.width - 35
    paste_y = 215
    img.paste(stamp_rot, (paste_x, paste_y), stamp_rot)


# ─── Base ─────────────────────────────────────────────────────────────────────

def base_slide(header_height: int = 180) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """
    Estrutura tripartida:
      [0 → header_height]      fundo escuro (ROXO_PROFUNDO)
      [header_height → -110]   fundo claro  (CINZA_SUAVE)
      [-110 → ALTURA]          fundo escuro (ROXO_PROFUNDO)
    Linhas douradas separam as zonas.
    Sem bordas laterais (oalanicolas: removidas).
    """
    img  = Image.new("RGB", (LARGURA, ALTURA), CINZA_SUAVE)
    draw = ImageDraw.Draw(img)

    # Cabeçalho escuro
    draw.rectangle([0, 0, LARGURA, header_height], fill=ROXO_PROFUNDO)
    # Rodapé escuro
    draw.rectangle([0, ALTURA - 110, LARGURA, ALTURA], fill=ROXO_PROFUNDO)

    # Linhas douradas divisórias
    draw.rectangle([60, header_height,     LARGURA - 60, header_height + 3],     fill=DOURADO)
    draw.rectangle([60, ALTURA - 110,      LARGURA - 60, ALTURA - 107],           fill=DOURADO)

    return img, draw


# ─── Slides ───────────────────────────────────────────────────────────────────

def slide_intro(categoria: str, numero: int, total: int) -> Image.Image:
    img, draw = base_slide(header_height=205)
    cx = LARGURA // 2

    # ── Cabeçalho ──────────────────────────────────────────────────────────────
    fonte_num = encontrar_fonte(24, bold=False)
    draw.text((cx, 32), f"{numero}/{total}", font=fonte_num,
              fill=ROXO_NEON, anchor="mt")

    # Balança PIL (único elemento decorativo do cabeçalho)
    desenhar_balanca(draw, cx, 140, tamanho=52, cor=DOURADO)

    # ── Área de conteúdo ───────────────────────────────────────────────────────
    fonte_marca = encontrar_fonte(84)
    draw.text((cx, 300), "ME JULGA", font=fonte_marca,
              fill=ROXO_PROFUNDO, anchor="mm")

    # Sublinhado dourado
    draw.rectangle([cx - 115, 340, cx + 115, 344], fill=DOURADO)

    # Texto intro (multilinha, Voice DNA)
    intro   = INTRO_TEXTOS.get(categoria, "A Dra. Julga\ntem um recado para você.")
    linhas  = intro.split("\n")
    fonte_t = encontrar_fonte(46, bold=False)
    y = 410
    for linha in linhas:
        draw.text((cx, y), linha, font=fonte_t, fill=ROXO_VIBRANTE, anchor="mm")
        bbox = draw.textbbox((0, 0), linha, font=fonte_t)
        y += (bbox[3] - bbox[1]) + 14

    # ── Badge "Deslize" ────────────────────────────────────────────────────────
    draw.rounded_rectangle([200, 790, LARGURA - 200, 848],
                           radius=28, fill=ROXO_PROFUNDO)
    fonte_badge = encontrar_fonte(28, bold=False)
    draw.text((cx, 819), "Deslize para o veredicto  >>>",
              font=fonte_badge, fill=DOURADO, anchor="mm")

    # ── Rodapé ─────────────────────────────────────────────────────────────────
    fonte_footer = encontrar_fonte(24, bold=False)
    draw.text((cx, ALTURA - 52), "@dra.julga  •  mejulga.com.br",
              font=fonte_footer, fill=ROXO_NEON, anchor="mm")

    return img


def slide_cena(texto: str, numero_cena: int, numero_slide: int, total: int) -> Image.Image:
    img, draw = base_slide(header_height=165)
    cx = LARGURA // 2

    # ── Cabeçalho ──────────────────────────────────────────────────────────────
    fonte_num = encontrar_fonte(24, bold=False)
    draw.text((cx, 30), f"{numero_slide}/{total}", font=fonte_num,
              fill=ROXO_NEON, anchor="mt")

    # Badge carimbo — label rotativo com borda dourada
    label_tmpl = LABELS_EVIDENCIA[(numero_cena - 1) % len(LABELS_EVIDENCIA)]
    label      = label_tmpl.format(numero_cena)
    fonte_lbl  = encontrar_fonte(28, bold=True)
    lbl_bbox   = draw.textbbox((0, 0), label, font=fonte_lbl)
    lbl_w      = lbl_bbox[2] - lbl_bbox[0]
    lbl_h      = lbl_bbox[3] - lbl_bbox[1]
    pad_h, pad_v = 24, 10
    draw.rounded_rectangle(
        [cx - lbl_w // 2 - pad_h, 98 - lbl_h // 2 - pad_v,
         cx + lbl_w // 2 + pad_h, 98 + lbl_h // 2 + pad_v],
        radius=8, fill=None, outline=DOURADO, width=2
    )
    draw.text((cx, 98), label, font=fonte_lbl, fill=DOURADO, anchor="mm")

    # ── Texto da cena — centralizado na área clara ────────────────────────────
    fonte_texto = encontrar_fonte(60)
    palavras    = texto.split()
    linhas      = []
    linha_atual = []

    for palavra in palavras:
        linha_atual.append(palavra)
        linha_teste = " ".join(linha_atual)
        bbox = draw.textbbox((0, 0), linha_teste, font=fonte_texto)
        if (bbox[2] - bbox[0]) > 880:
            if len(linha_atual) > 1:
                linhas.append(" ".join(linha_atual[:-1]))
                linha_atual = [palavra]
            else:
                linhas.append(linha_teste)
                linha_atual = []
    if linha_atual:
        linhas.append(" ".join(linha_atual))

    n           = len(linhas)
    line_h      = 84
    altura_txt  = n * line_h
    # Centrar na zona de conteúdo (165 → 970)
    y = 165 + (805 - altura_txt) // 2

    for linha in linhas:
        draw.text((cx, y), linha, font=fonte_texto,
                  fill=ROXO_PROFUNDO, anchor="mm")
        y += line_h

    # ── Dots de progresso ──────────────────────────────────────────────────────
    _desenhar_dots(draw, numero_slide, total)

    return img


def slide_veredicto(conclusao: str, numero: int, total: int) -> Image.Image:
    img, draw = base_slide(header_height=205)
    cx = LARGURA // 2

    # ── Cabeçalho ──────────────────────────────────────────────────────────────
    fonte_num = encontrar_fonte(24, bold=False)
    draw.text((cx, 32), f"{numero}/{total}", font=fonte_num,
              fill=ROXO_NEON, anchor="mt")

    # Martelo PIL (único elemento decorativo do cabeçalho)
    desenhar_martelo(draw, cx, 88, tamanho=44, cor=DOURADO)

    # Label com ornamentos laterais
    fonte_lbl = encontrar_fonte(30, bold=True)
    label     = "VEREDICTO FINAL"
    lbl_bbox  = draw.textbbox((0, 0), label, font=fonte_lbl)
    lbl_w     = lbl_bbox[2] - lbl_bbox[0]
    draw.text((cx, 168), label, font=fonte_lbl, fill=DOURADO, anchor="mm")
    draw.rectangle([cx - lbl_w // 2 - 70, 168, cx - lbl_w // 2 - 12, 170], fill=DOURADO)
    draw.rectangle([cx + lbl_w // 2 + 12, 168, cx + lbl_w // 2 + 70, 170], fill=DOURADO)

    # ── Caixa do veredicto ────────────────────────────────────────────────────
    # Sombra (deslocamento 4px)
    draw.rounded_rectangle([64, 224, LARGURA - 56, 624],
                           radius=20, fill=ROXO_SOMBRA)
    # Caixa principal
    draw.rounded_rectangle([60, 220, LARGURA - 60, 620],
                           radius=20, fill=BRANCO_PURO, outline=ROXO_BORDA, width=3)

    # Texto do veredicto
    fonte_v  = encontrar_fonte(64)
    palavras = conclusao.split()
    linhas   = []
    linha_a  = []
    for palavra in palavras:
        linha_a.append(palavra)
        linha_t = " ".join(linha_a)
        bbox    = draw.textbbox((0, 0), linha_t, font=fonte_v)
        if (bbox[2] - bbox[0]) > 840:
            if len(linha_a) > 1:
                linhas.append(" ".join(linha_a[:-1]))
                linha_a = [palavra]
            else:
                linhas.append(linha_t)
                linha_a = []
    if linha_a:
        linhas.append(" ".join(linha_a))

    n      = len(linhas)
    line_h = 88
    y      = 220 + (400 - n * line_h) // 2
    for linha in linhas:
        draw.text((cx, y), linha, font=fonte_v,
                  fill=ROXO_PROFUNDO, anchor="mm")
        y += line_h

    # Carimbo CULPADO — desordem controlada (oalanicolas)
    _desenhar_carimbo(img)

    # ── Bloco CTA ─────────────────────────────────────────────────────────────
    draw.rounded_rectangle([60, 645, LARGURA - 60, 875],
                           radius=20, fill=ROXO_PROFUNDO)
    fonte_l1 = encontrar_fonte(34, bold=False)
    fonte_l2 = encontrar_fonte(38, bold=True)
    fonte_l3 = encontrar_fonte(46, bold=True)
    draw.text((cx, 688), VEREDICTO_CTA_L1,
              font=fonte_l1, fill=BRANCO_PURO, anchor="mm")
    draw.text((cx, 735), VEREDICTO_CTA_L2,
              font=fonte_l2, fill=BRANCO_PURO, anchor="mm")
    # Linha dourada separadora
    draw.rectangle([cx - 90, 758, cx + 90, 761], fill=DOURADO)
    draw.text((cx, 822), VEREDICTO_CTA_L3,
              font=fonte_l3, fill=DOURADO, anchor="mm")

    # ── Dots de progresso ──────────────────────────────────────────────────────
    _desenhar_dots(draw, numero, total)

    return img


# ─── Pipeline ─────────────────────────────────────────────────────────────────

def carregar_roteiro(categoria: str, data: str) -> dict:
    pasta   = Path(__file__).parent / "generated" / "reels"
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

    hoje      = args.data or datetime.now().strftime("%Y-%m-%d")
    categoria = args.categoria

    print(f"🎨 Gerando carrossel v2 'Tribunal Pop' — {categoria} — {hoje}")

    roteiro  = carregar_roteiro(categoria, hoje)
    cenas    = roteiro.get("cenas", [])[:4]
    conclusao = roteiro.get("conclusao", "Sem defesa possível.")
    if not conclusao and cenas:
        conclusao = cenas[-1]["texto"]

    total_slides = 6
    pasta_saida  = Path(__file__).parent / "generated" / "reels"
    pasta_saida.mkdir(parents=True, exist_ok=True)
    slides = []

    # Slide 1 — Intro
    print("  📸 Slide 1/6 — Intro")
    s1 = slide_intro(categoria, 1, total_slides)
    p1 = pasta_saida / f"{hoje}_{categoria}_slide_01.png"
    s1.save(str(p1))
    slides.append(p1)

    # Slides 2-5 — Cenas
    for i, cena in enumerate(cenas):
        n = i + 2
        print(f"  📸 Slide {n}/6 — Cena {i + 1}")
        img = slide_cena(cena["texto"], i + 1, n, total_slides)
        p   = pasta_saida / f"{hoje}_{categoria}_slide_0{n}.png"
        img.save(str(p))
        slides.append(p)

    # Preenche slides vazios se menos de 4 cenas
    for i in range(len(cenas), 4):
        n   = i + 2
        img = slide_cena("...", i + 1, n, total_slides)
        p   = pasta_saida / f"{hoje}_{categoria}_slide_0{n}.png"
        img.save(str(p))
        slides.append(p)

    # Slide 6 — Veredicto
    print("  📸 Slide 6/6 — Veredicto")
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
