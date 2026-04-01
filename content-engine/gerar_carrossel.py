"""
gerar_carrossel.py — v3 "Tribunal Editorial"
Gera 6 slides PNG para carrossel do Instagram.

Design padrão: clean editorial — fundo branco, tipografia forte.
Template Canva: se existirem arquivos em templates/carrossel/, são usados como fundo.

Uso: python gerar_carrossel.py --categoria amor
"""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

LARGURA      = 1080
ALTURA       = 1080
TEMPLATES_DIR = Path(__file__).parent / "templates" / "carrossel"

# ─── Paleta ───────────────────────────────────────────────────────────────────
ROXO_PROFUNDO  = (30, 10, 70)       # texto principal, âncoras escuras
ROXO_VIBRANTE  = (138, 43, 226)     # labels, bordas de destaque, badges
CINZA_SUAVE    = (245, 243, 250)    # fundo de pills, caixa de veredicto
DOURADO        = (255, 193, 37)     # ícones decorativos, URL, ornamentos
BRANCO_PURO    = (255, 255, 255)    # fundo de todos os slides
ROXO_BORDA     = (100, 50, 170)     # bordas de caixas, dots inativos
CINZA_MEDIO    = (150, 140, 165)    # contadores, rodapé sutil
VERMELHO_STAMP = (200, 30, 30)      # carimbo CULPADO

# ─── Categorias ───────────────────────────────────────────────────────────────
CATEGORIAS = [
    "dinheiro", "amor", "trabalho",
    "dopamina", "vida_adulta", "social", "saude_mental"
]

# ─── Copy — Voice DNA da Dra. Julga ──────────────────────────────────────────
INTRO_TEXTOS = {
    "dinheiro":    "A Dra. Julga\nacessou seu extrato.\nO veredicto?\nIndefensável.",
    "amor":        "A Dra. Julga\nleu suas mensagens.\nTodas.\nAté as apagadas.",
    "trabalho":    "A Dra. Julga\nmonitorou sua segunda-feira.\nDe 8h às 18h.\nVocê trabalhou 47 min.",
    "dopamina":    "A Dra. Julga\ncronometrou seu tempo de tela.\nSão 7h14 por dia.\nEla está preocupada. Você, não.",
    "vida_adulta": "A Dra. Julga\nvisitou sua geladeira.\nTinha ketchup,\numa cerveja e arrependimento.",
    "social":      "A Dra. Julga\nviu que você cancelou.\nDe novo.\nTerceiro sábado seguido.",
    "saude_mental":"A Dra. Julga\nacessou seus pensamentos\ndas 3h da manhã.\nO processo precisou de volume 2.",
}

LABELS_EVIDENCIA = [
    "PROVA Nº {}",
    "AUTO DE ACUSAÇÃO Nº {}",
    "FLAGRANTE Nº {}",
    "REGISTRO DE OCORRÊNCIA Nº {}",
    "DEPOIMENTO Nº {}",
]

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
    draw.rectangle([cx - 3, cy - tamanho, cx + 3, cy + tamanho // 2], fill=cor)
    draw.rectangle([cx - 30, cy + tamanho // 2 - 3,
                    cx + 30, cy + tamanho // 2 + 6], fill=cor)
    draw.rectangle([cx - tamanho, cy - tamanho,
                    cx + tamanho, cy - tamanho + 4], fill=cor)
    draw.line([cx - tamanho, cy - tamanho + 4,
               cx - tamanho, cy - tamanho + 24], fill=cor, width=2)
    draw.line([cx + tamanho, cy - tamanho + 4,
               cx + tamanho, cy - tamanho + 24], fill=cor, width=2)
    pr = 20
    draw.ellipse([cx - tamanho - pr, cy - tamanho + 24,
                  cx - tamanho + pr, cy - tamanho + 36], fill=cor)
    draw.ellipse([cx + tamanho - pr, cy - tamanho + 24,
                  cx + tamanho + pr, cy - tamanho + 36], fill=cor)


def desenhar_martelo(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                     tamanho: int = 40, cor=DOURADO):
    draw.rectangle([cx - 3, cy, cx + 3, cy + tamanho], fill=cor)
    draw.rounded_rectangle([cx - tamanho // 2, cy - tamanho // 3,
                             cx + tamanho // 2, cy + tamanho // 5],
                            radius=5, fill=cor)


def _desenhar_dots(draw: ImageDraw.ImageDraw, slide_atual: int, total: int):
    """Indicador de progresso — sobre fundo branco."""
    dot_y   = ALTURA - 48
    dot_r   = 7
    dot_gap = 30
    total_w = (total - 1) * dot_gap
    start_x = LARGURA // 2 - total_w // 2
    for i in range(total):
        dx = start_x + i * dot_gap
        if i + 1 == slide_atual:
            draw.ellipse([dx - dot_r, dot_y - dot_r,
                          dx + dot_r, dot_y + dot_r], fill=ROXO_VIBRANTE)
        else:
            draw.ellipse([dx - dot_r, dot_y - dot_r,
                          dx + dot_r, dot_y + dot_r],
                         fill=CINZA_SUAVE, outline=ROXO_BORDA, width=2)


def _desenhar_carimbo(img: Image.Image):
    """Carimbo 'CULPADO' rotacionado — desordem controlada."""
    stamp = Image.new("RGBA", (340, 100), (0, 0, 0, 0))
    sd    = ImageDraw.Draw(stamp)

    fonte_path = "C:/Windows/Fonts/arialbd.ttf"
    if os.path.exists(fonte_path):
        fonte_stamp = ImageFont.truetype(fonte_path, 68)
    else:
        fonte_stamp = ImageFont.load_default()

    sd.rounded_rectangle([4, 4, 336, 96], radius=10,
                          fill=None, outline=(*VERMELHO_STAMP, 210), width=5)
    sd.text((170, 50), "CULPADO", font=fonte_stamp,
            fill=(*VERMELHO_STAMP, 195), anchor="mm")

    stamp_rot = stamp.rotate(15, expand=True)
    paste_x = LARGURA - stamp_rot.width - 35
    paste_y = 215
    img.paste(stamp_rot, (paste_x, paste_y), stamp_rot)


# ─── Templates Canva ──────────────────────────────────────────────────────────

# Zonas de texto como fração da imagem (top, bottom, left, right)
# Calibradas para templates 1080×1350 (4:5 Instagram portrait)
# Define onde o conteúdo dinâmico é apagado e reescrito
TEMPLATE_ZONAS = {
    "intro":     (0.17, 0.68, 0.04, 0.96),   # texto intro — y=229-918 cobre y=485-870
    "cena":      (0.32, 0.61, 0.04, 0.96),   # abaixo do label (y≈380-405) — cobre texto y=600-796
    "veredicto": (0.39, 0.49, 0.04, 0.96),   # texto veredicto — y=527-662 cobre y=565-615
}

# Faixa limpa (entre header e labels) para amostrar textura do fundo
FUNDO_SAMPLE = (0.09, 0.13, 0.30, 0.70)


def _sample_bg(img: Image.Image) -> tuple[np.ndarray, np.ndarray]:
    """Retorna média e desvio da cor do fundo em região limpa."""
    W, H = img.size
    y0, y1 = int(FUNDO_SAMPLE[0] * H), int(FUNDO_SAMPLE[1] * H)
    x0, x1 = int(FUNDO_SAMPLE[2] * W), int(FUNDO_SAMPLE[3] * W)
    region = np.array(img.crop((x0, y0, x1, y1)), dtype=np.float32)
    mean = region.mean(axis=(0, 1))
    std  = region.std(axis=(0, 1)).clip(0, 5)
    return mean, std


def _apagar_zona(img: Image.Image, zona: str) -> Image.Image:
    """Apaga a zona de texto replicando a textura do fundo."""
    W, H = img.size
    top, bot, left, right = TEMPLATE_ZONAS[zona]
    x0, y0 = int(left * W), int(top * H)
    x1, y1 = int(right * W), int(bot * H)
    bg_mean, bg_std = _sample_bg(img)
    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, bg_std, (y1 - y0, x1 - x0, 3))
    arr[y0:y1, x0:x1] = np.clip(bg_mean + noise, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def _quebrar_com_newlines(draw: ImageDraw.ImageDraw,
                          texto: str, fonte, max_w: int) -> list[str]:
    """Respeita \\n e aplica word-wrap em cada parágrafo."""
    linhas = []
    for paragrafo in texto.split("\n"):
        if not paragrafo.strip():
            continue
        atual = []
        for palavra in paragrafo.split():
            atual.append(palavra)
            w = draw.textbbox((0, 0), " ".join(atual), font=fonte)[2]
            if w > max_w and len(atual) > 1:
                linhas.append(" ".join(atual[:-1]))
                atual = [palavra]
        if atual:
            linhas.append(" ".join(atual))
    return linhas


def _fonte_maxima(draw, linhas, zona, img_size, max_sz=80, min_sz=28):
    """Encontra o maior tamanho de fonte que cabe na zona."""
    W, H = img_size
    _, _, left, right = TEMPLATE_ZONAS[zona]
    max_w = int((right - left) * W)
    for sz in range(max_sz, min_sz - 1, -2):
        fonte = encontrar_fonte(sz, bold=False)
        if all(draw.textbbox((0, 0), l, font=fonte)[2] <= max_w for l in linhas):
            return fonte
    return encontrar_fonte(min_sz, bold=False)


def _processar_template(path: Path, zona: str, texto: str,
                        cor=None) -> Image.Image:
    """
    Pipeline de template:
      1. Carrega template Canva
      2. Apaga zona de texto replicando textura do fundo
      3. Calcula fonte máxima que cabe
      4. Redesenha texto centralizado na zona
    """
    if cor is None:
        cor = ROXO_VIBRANTE
    img  = Image.open(path).convert("RGB")
    img  = _apagar_zona(img, zona)
    draw = ImageDraw.Draw(img)
    W, H = img.size
    top, bot, left, right = TEMPLATE_ZONAS[zona]
    zona_w = int((right - left) * W)
    cx     = W // 2

    # Quebra texto respeitando \n
    linhas_tmp = _quebrar_com_newlines(draw, texto,
                                       encontrar_fonte(80, bold=False), zona_w)
    fonte  = _fonte_maxima(draw, linhas_tmp, zona, (W, H))
    linhas = _quebrar_com_newlines(draw, texto, fonte, zona_w)

    bbox_s = draw.textbbox((0, 0), "Ag", font=fonte)
    line_h = int((bbox_s[3] - bbox_s[1]) * 1.45)
    total_h = len(linhas) * line_h

    y_start = int(top * H)
    y_end   = int(bot * H)
    y = y_start + (y_end - y_start - total_h) // 2

    for linha in linhas:
        draw.text((cx, y), linha, font=fonte, fill=cor, anchor="mt")
        y += line_h

    return img


def _carregar_template(nome_arquivo: str) -> Image.Image | None:
    """Carrega template PNG do Canva se disponível na pasta templates/carrossel/."""
    path = TEMPLATES_DIR / nome_arquivo
    if path.exists():
        return Image.open(path).convert("RGB").resize((LARGURA, ALTURA), Image.LANCZOS)
    return None


def _templates_completos() -> bool:
    """Retorna True se os 6 slides numerados (1.png–6.png) existirem — uso direto, sem PIL."""
    return all((TEMPLATES_DIR / f"{i}.png").exists() for i in range(1, 7))


def _templates_ativos() -> bool:
    """Retorna True se os 3 fundos de background existirem — modo overlay de texto."""
    return all(
        (TEMPLATES_DIR / f).exists()
        for f in ["intro_bg.png", "cena_bg.png", "veredicto_bg.png"]
    )


# ─── Base ─────────────────────────────────────────────────────────────────────

def base_slide(template_nome: str | None = None) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """
    Fundo do slide. Prioridade:
      1. Template Canva (se existir em templates/carrossel/<template_nome>)
      2. Branco puro (design padrão)
    """
    if template_nome:
        tmpl = _carregar_template(template_nome)
        if tmpl:
            return tmpl, ImageDraw.Draw(tmpl)
    img  = Image.new("RGB", (LARGURA, ALTURA), BRANCO_PURO)
    draw = ImageDraw.Draw(img)
    return img, draw


# ─── Slides ───────────────────────────────────────────────────────────────────

def slide_intro(categoria: str, numero: int, total: int) -> Image.Image:
    img, draw = base_slide("intro_bg.png")
    cx = LARGURA // 2

    # Contador sutil
    fonte_num = encontrar_fonte(22, bold=False)
    draw.text((cx, 30), f"{numero}/{total}", font=fonte_num,
              fill=CINZA_MEDIO, anchor="mt")

    # Balança dourada — elemento decorativo sobre branco
    desenhar_balanca(draw, cx, 130, tamanho=52, cor=DOURADO)

    # "ME JULGA" — título principal
    fonte_marca = encontrar_fonte(90)
    draw.text((cx, 280), "ME JULGA", font=fonte_marca,
              fill=ROXO_PROFUNDO, anchor="mm")

    # Sublinhado dourado
    draw.rectangle([cx - 120, 324, cx + 120, 329], fill=DOURADO)

    # Texto intro (multilinha, Voice DNA)
    intro   = INTRO_TEXTOS.get(categoria, "A Dra. Julga\ntem um recado para você.")
    linhas  = intro.split("\n")
    fonte_t = encontrar_fonte(48, bold=False)
    y = 380
    for linha in linhas:
        draw.text((cx, y), linha, font=fonte_t, fill=ROXO_VIBRANTE, anchor="mm")
        bbox = draw.textbbox((0, 0), linha, font=fonte_t)
        y += (bbox[3] - bbox[1]) + 16

    # Badge "Deslize" — pill com borda, sem fill pesado
    fonte_badge = encontrar_fonte(28, bold=False)
    badge_txt   = "Deslize para o veredicto  >>>"
    draw.rounded_rectangle([180, 800, LARGURA - 180, 858],
                            radius=30, fill=None,
                            outline=ROXO_VIBRANTE, width=2)
    draw.text((cx, 829), badge_txt, font=fonte_badge,
              fill=ROXO_VIBRANTE, anchor="mm")

    # Rodapé sutil
    fonte_footer = encontrar_fonte(22, bold=False)
    draw.text((cx, ALTURA - 28), "@dra.julga  •  mejulga.com.br",
              font=fonte_footer, fill=CINZA_MEDIO, anchor="mm")

    return img


def slide_cena(texto: str, numero_cena: int, numero_slide: int, total: int) -> Image.Image:
    img, draw = base_slide("cena_bg.png")
    cx = LARGURA // 2

    # Contador sutil
    fonte_num = encontrar_fonte(22, bold=False)
    draw.text((cx, 28), f"{numero_slide}/{total}", font=fonte_num,
              fill=CINZA_MEDIO, anchor="mt")

    # Badge label — pill com borda roxa sobre branco
    label_tmpl = LABELS_EVIDENCIA[(numero_cena - 1) % len(LABELS_EVIDENCIA)]
    label      = label_tmpl.format(numero_cena)
    fonte_lbl  = encontrar_fonte(30, bold=True)
    lbl_bbox   = draw.textbbox((0, 0), label, font=fonte_lbl)
    lbl_w      = lbl_bbox[2] - lbl_bbox[0]
    lbl_h      = lbl_bbox[3] - lbl_bbox[1]
    pad_h, pad_v = 28, 12
    draw.rounded_rectangle(
        [cx - lbl_w // 2 - pad_h, 78 - lbl_h // 2 - pad_v,
         cx + lbl_w // 2 + pad_h, 78 + lbl_h // 2 + pad_v],
        radius=24, fill=CINZA_SUAVE, outline=ROXO_VIBRANTE, width=2
    )
    draw.text((cx, 78), label, font=fonte_lbl, fill=ROXO_VIBRANTE, anchor="mm")

    # Linha divisória sutil abaixo da label
    draw.rectangle([80, 122, LARGURA - 80, 124], fill=CINZA_SUAVE)

    # Texto da cena — centralizado com mais espaço disponível
    fonte_texto = encontrar_fonte(62)
    palavras    = texto.split()
    linhas      = []
    linha_atual = []

    for palavra in palavras:
        linha_atual.append(palavra)
        linha_teste = " ".join(linha_atual)
        bbox = draw.textbbox((0, 0), linha_teste, font=fonte_texto)
        if (bbox[2] - bbox[0]) > 900:
            if len(linha_atual) > 1:
                linhas.append(" ".join(linha_atual[:-1]))
                linha_atual = [palavra]
            else:
                linhas.append(linha_teste)
                linha_atual = []
    if linha_atual:
        linhas.append(" ".join(linha_atual))

    n          = len(linhas)
    line_h     = 88
    zona_top   = 140
    zona_bot   = ALTURA - 100
    altura_txt = n * line_h
    y = zona_top + (zona_bot - zona_top - altura_txt) // 2

    for linha in linhas:
        draw.text((cx, y), linha, font=fonte_texto,
                  fill=ROXO_PROFUNDO, anchor="mm")
        y += line_h

    # Dots de progresso
    _desenhar_dots(draw, numero_slide, total)

    # Rodapé sutil
    fonte_footer = encontrar_fonte(20, bold=False)
    draw.text((cx, ALTURA - 16), "@dra.julga",
              font=fonte_footer, fill=CINZA_MEDIO, anchor="mm")

    return img


def slide_veredicto(conclusao: str, numero: int, total: int) -> Image.Image:
    img, draw = base_slide("veredicto_bg.png")
    cx = LARGURA // 2

    # Contador sutil
    fonte_num = encontrar_fonte(22, bold=False)
    draw.text((cx, 28), f"{numero}/{total}", font=fonte_num,
              fill=CINZA_MEDIO, anchor="mt")

    # Martelo dourado
    desenhar_martelo(draw, cx, 80, tamanho=44, cor=DOURADO)

    # "VEREDICTO FINAL" — label com ornamentos
    fonte_lbl = encontrar_fonte(32, bold=True)
    label     = "VEREDICTO FINAL"
    lbl_bbox  = draw.textbbox((0, 0), label, font=fonte_lbl)
    lbl_w     = lbl_bbox[2] - lbl_bbox[0]
    draw.text((cx, 168), label, font=fonte_lbl, fill=ROXO_PROFUNDO, anchor="mm")
    # Linhas ornamentais laterais
    draw.rectangle([cx - lbl_w // 2 - 70, 168, cx - lbl_w // 2 - 12, 171], fill=DOURADO)
    draw.rectangle([cx + lbl_w // 2 + 12, 168, cx + lbl_w // 2 + 70, 171], fill=DOURADO)

    # Caixa do veredicto — fundo cinza suave sobre branco
    draw.rounded_rectangle([60, 205, LARGURA - 60, 610],
                           radius=20, fill=CINZA_SUAVE, outline=ROXO_BORDA, width=2)

    # Texto do veredicto
    fonte_v  = encontrar_fonte(66)
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
    line_h = 92
    y      = 205 + (405 - n * line_h) // 2
    for linha in linhas:
        draw.text((cx, y), linha, font=fonte_v,
                  fill=ROXO_PROFUNDO, anchor="mm")
        y += line_h

    # Carimbo CULPADO — desordem controlada
    _desenhar_carimbo(img)

    # Bloco CTA — único bloco escuro do slide (âncora visual)
    draw.rounded_rectangle([60, 638, LARGURA - 60, 870],
                           radius=20, fill=ROXO_PROFUNDO)
    fonte_l1 = encontrar_fonte(34, bold=False)
    fonte_l2 = encontrar_fonte(38, bold=True)
    fonte_l3 = encontrar_fonte(48, bold=True)
    draw.text((cx, 682), VEREDICTO_CTA_L1,
              font=fonte_l1, fill=BRANCO_PURO, anchor="mm")
    draw.text((cx, 729), VEREDICTO_CTA_L2,
              font=fonte_l2, fill=BRANCO_PURO, anchor="mm")
    draw.rectangle([cx - 90, 752, cx + 90, 755], fill=DOURADO)
    draw.text((cx, 815), VEREDICTO_CTA_L3,
              font=fonte_l3, fill=DOURADO, anchor="mm")

    # Dots de progresso
    _desenhar_dots(draw, numero, total)

    # Rodapé sutil
    fonte_footer = encontrar_fonte(20, bold=False)
    draw.text((cx, ALTURA - 16), "@dra.julga",
              font=fonte_footer, fill=CINZA_MEDIO, anchor="mm")

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

    pasta_saida = Path(__file__).parent / "generated" / "reels"
    pasta_saida.mkdir(parents=True, exist_ok=True)
    slides = []

    # ── Modo 1: templates completos (1.png–6.png) ─────────────────────────────
    # Carrega design Canva, substitui texto do conteúdo pelo da nova categoria
    if _templates_completos():
        print(f"Carrossel — {categoria} — {hoje} [template Canva]")
        roteiro_t  = carregar_roteiro(categoria, hoje)
        cenas_t    = roteiro_t.get("cenas", [])[:4]
        conclusao_t = roteiro_t.get("conclusao", "Sem defesa possível.")

        # Slide 1 — intro
        intro_txt = INTRO_TEXTOS.get(categoria, "A Dra. Julga\ntem um recado para você.")
        s1 = _processar_template(TEMPLATES_DIR / "1.png", "intro", intro_txt)
        p1 = pasta_saida / f"{hoje}_{categoria}_slide_01.png"
        s1.save(str(p1)); slides.append(p1)
        print("  Slide 1/6 — intro")

        # Slides 2–5 — cenas
        for i in range(4):
            n   = i + 2
            txt = cenas_t[i]["texto"] if i < len(cenas_t) else "..."
            s   = _processar_template(TEMPLATES_DIR / f"{n}.png", "cena", txt)
            p   = pasta_saida / f"{hoje}_{categoria}_slide_0{n}.png"
            s.save(str(p)); slides.append(p)
            print(f"  Slide {n}/6 — cena {i + 1}")

        # Slide 6 — veredicto
        s6 = _processar_template(TEMPLATES_DIR / "6.png", "veredicto", conclusao_t)
        p6 = pasta_saida / f"{hoje}_{categoria}_slide_06.png"
        s6.save(str(p6)); slides.append(p6)
        print("  Slide 6/6 — veredicto")

        print(f"\nSlides prontos em {pasta_saida}")
        return slides

    # ── Modo 2: geração PIL (design padrão ou background overlay) ─────────────
    modo = "background Canva" if _templates_ativos() else "design padrão"
    print(f"Gerando carrossel v3 — {categoria} — {hoje} [{modo}]")

    roteiro   = carregar_roteiro(categoria, hoje)
    cenas     = roteiro.get("cenas", [])[:4]
    conclusao = roteiro.get("conclusao", "Sem defesa possível.")
    if not conclusao and cenas:
        conclusao = cenas[-1]["texto"]

    total_slides = 6

    print("  Slide 1/6 — Intro")
    s1 = slide_intro(categoria, 1, total_slides)
    p1 = pasta_saida / f"{hoje}_{categoria}_slide_01.png"
    s1.save(str(p1))
    slides.append(p1)

    for i, cena in enumerate(cenas):
        n = i + 2
        print(f"  Slide {n}/6 — Cena {i + 1}")
        img = slide_cena(cena["texto"], i + 1, n, total_slides)
        p   = pasta_saida / f"{hoje}_{categoria}_slide_0{n}.png"
        img.save(str(p))
        slides.append(p)

    for i in range(len(cenas), 4):
        n   = i + 2
        img = slide_cena("...", i + 1, n, total_slides)
        p   = pasta_saida / f"{hoje}_{categoria}_slide_0{n}.png"
        img.save(str(p))
        slides.append(p)

    print("  Slide 6/6 — Veredicto")
    s6 = slide_veredicto(conclusao, 6, total_slides)
    p6 = pasta_saida / f"{hoje}_{categoria}_slide_06.png"
    s6.save(str(p6))
    slides.append(p6)

    print(f"\nSlides gerados em {pasta_saida}")
    for s in slides:
        print(f"   {s.name}")

    return slides


if __name__ == "__main__":
    main()
