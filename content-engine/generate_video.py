"""
generate_video.py
Gera vídeo de Reels com cenários visuais humorísticos por categoria.
Uso: python generate_video.py --categoria dinheiro
"""

import os
import json
import argparse
import math
import numpy as np
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

LARGURA = 1080
ALTURA = 1920
FPS = 30

# Cores base
ROXO_ESCURO = (15, 10, 30)
ROXO_MEDIO = (45, 16, 96)
ROXO_VIBRANTE = (124, 58, 237)
ROXO_CLARO = (168, 85, 247)
BRANCO = (255, 255, 255)
VERMELHO = (226, 75, 74)
CINZA_ESCURO = (30, 16, 64)
AMARELO = (250, 199, 117)

CATEGORIAS_INFO = {
    "dinheiro": "Dinheiro",
    "amor": "Amor",
    "trabalho": "Trabalho",
    "dopamina": "Dopamina",
    "vida_adulta": "Vida Adulta",
    "social": "Social",
    "saude_mental": "Saude Mental",
}

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
    linhas = []
    linha = []
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

def adicionar_texto_cena(draw: ImageDraw, texto: str, y_base: int = None):
    """Adiciona o texto da cena na parte inferior do frame."""
    if y_base is None:
        y_base = ALTURA - 380

    # Caixa de texto
    draw.rounded_rectangle([40, y_base, LARGURA-40, y_base+220], radius=20, fill=(20, 10, 50), outline=(80, 40, 160), width=2)

    # Label ME JULGA
    fonte_label = encontrar_fonte(28, bold=False)
    draw.text((LARGURA//2, y_base+28), "ME JULGA", font=fonte_label, fill=(80, 50, 140), anchor="mm")

    # Linha separadora
    draw.line([80, y_base+50, LARGURA-80, y_base+50], fill=(40, 25, 80), width=1)

    # Texto principal
    linhas = quebrar_texto(texto, max_chars=22)
    fonte_texto = encontrar_fonte(72 if len(texto) < 40 else 58)
    y_texto = y_base + 80
    for linha in linhas:
        draw.text((LARGURA//2, y_texto), linha, font=fonte_texto, fill=BRANCO, anchor="mm")
        y_texto += 85

    # Footer @dra.julga
    fonte_footer = encontrar_fonte(26, bold=False)
    draw.text((LARGURA//2, y_base+198), "@dra.julga", font=fonte_footer, fill=(60, 40, 100), anchor="mm")


# ─── CENÁRIOS POR CENA ────────────────────────────────────────────────────────

def cena_cartao_sofrencia(texto: str) -> Image.Image:
    """Cena 1 — Cartão suando frio."""
    img = Image.new("RGB", (LARGURA, ALTURA), ROXO_ESCURO)
    draw = ImageDraw.Draw(img)

    # Cartão de crédito gigante
    cx, cy = LARGURA//2, 620
    w, h = 700, 440

    draw.rounded_rectangle([cx-w//2, cy-h//2, cx+w//2, cy+h//2], radius=40, fill=(26, 10, 62), outline=ROXO_VIBRANTE, width=4)
    draw.rounded_rectangle([cx-w//2, cy-h//2, cx+w//2, cy-h//2+130], radius=40, fill=ROXO_MEDIO)

    fonte_cartao = encontrar_fonte(36, bold=False)
    fonte_numero = encontrar_fonte(52)
    fonte_small = encontrar_fonte(30, bold=False)

    draw.text((cx, cy-h//2+65), "◆ MASTERCARD SOFRÊNCIA", font=fonte_cartao, fill=(155, 127, 232), anchor="mm")
    draw.text((cx, cy+20), "**** **** **** 2024", font=fonte_numero, fill=(100, 80, 160), anchor="mm")
    draw.text((cx, cy+90), "LIMITE: R$500    USADO: R$498,73", font=fonte_small, fill=(80, 60, 130), anchor="mm")

    # Barra de limite QUASE CHEIA
    bx, by = cx-280, cy+130
    draw.rounded_rectangle([bx, by, bx+560, by+30], radius=15, fill=(30, 16, 64))
    draw.rounded_rectangle([bx, by, bx+555, by+30], radius=15, fill=VERMELHO)
    draw.text((cx, by+55), "⚠ LIMITE QUASE ESGOTADO ⚠", font=fonte_small, fill=VERMELHO, anchor="mm")

    # Gotinhas de suor
    for gx, gy, gr in [(cx+320, cy-140, 18), (cx+350, cy-80, 13), (cx+310, cy-30, 10)]:
        draw.ellipse([gx-gr//2, gy-gr, gx+gr//2, gy+gr], fill=(74, 158, 255, 180))

    adicionar_texto_cena(draw, texto)
    return img


def cena_nota_fiscal(texto: str) -> Image.Image:
    """Cena 2 — Nota fiscal absurda do café."""
    img = Image.new("RGB", (LARGURA, ALTURA), (13, 13, 13))
    draw = ImageDraw.Draw(img)

    # Xícara de café
    cx, cy = LARGURA//2, 380
    draw.ellipse([cx-180, cy-60, cx+180, cy], fill=(61, 31, 10))
    draw.rectangle([cx-180, cy-100, cx+180, cy], fill=(42, 21, 5))
    draw.ellipse([cx-180, cy-140, cx+180, cy-80], fill=(50, 25, 7))
    draw.arc([cx+150, cy-120, cx+230, cy-60], start=270, end=90, fill=(61, 31, 10), width=20)

    # Vapor
    for vx in [cx-80, cx, cx+80]:
        for i in range(5):
            vy = cy - 160 - i*30
            draw.arc([vx-15, vy-15, vx+15, vy+15], start=0, end=180, fill=(80, 80, 80), width=3)

    # Recibo
    rx, ry = cx-320, 580
    draw.rounded_rectangle([rx, ry, rx+640, ry+420], radius=10, fill=(245, 245, 245))
    fonte_titulo = encontrar_fonte(38)
    fonte_linha = encontrar_fonte(32, bold=False)
    fonte_obs = encontrar_fonte(26, bold=False)

    draw.text((cx, ry+40), "CAFÉ PARCELADO LTDA", font=fonte_titulo, fill=(50, 50, 50), anchor="mm")
    draw.line([rx+20, ry+70, rx+620, ry+70], fill=(200, 200, 200), width=2)

    itens = [
        ("1x café pequeno", "R$ 7,00", (80, 80, 80)),
        ("Parcelado 3x", "R$ 2,33/mês", (226, 75, 74)),
        ("Juros 3,9%/mês", "+R$ 0,27", (226, 75, 74)),
        ("─────────────", "─────", (180, 180, 180)),
        ("TOTAL REAL:", "R$ 7,81", (50, 50, 50)),
    ]
    y_item = ry + 100
    for label, valor, cor in itens:
        draw.text((rx+40, y_item), label, font=fonte_linha, fill=cor)
        draw.text((rx+600, y_item), valor, font=fonte_linha, fill=cor, anchor="ra")
        y_item += 55

    draw.text((cx, ry+395), "*café já esfriou na parcela 2", font=fonte_obs, fill=(150, 150, 150), anchor="mm")

    adicionar_texto_cena(draw, texto)
    return img


def cena_app_bancario(texto: str) -> Image.Image:
    """Cena 3 — App bancário com saldo negativo."""
    img = Image.new("RGB", (LARGURA, ALTURA), (15, 10, 30))
    draw = ImageDraw.Draw(img)

    # Celular
    px, py = LARGURA//2-220, 120
    pw, ph = 440, 760
    draw.rounded_rectangle([px, py, px+pw, py+ph], radius=50, fill=(26, 26, 46), outline=(60, 60, 80), width=4)
    draw.rounded_rectangle([px+10, py+30, px+pw-10, py+ph-30], radius=40, fill=(13, 13, 26))
    # Notch
    draw.rounded_rectangle([px+pw//2-70, py+8, px+pw//2+70, py+36], radius=15, fill=(20, 20, 35))

    fonte_app = encontrar_fonte(32, bold=False)
    fonte_saldo = encontrar_fonte(68)
    fonte_small = encontrar_fonte(26, bold=False)
    fonte_mini = encontrar_fonte(22, bold=False)

    draw.text((px+pw//2, py+90), "Banco do Sofrimento", font=fonte_app, fill=(100, 100, 120), anchor="mm")
    draw.text((px+pw//2, py+130), "Olá, Endividado!", font=fonte_small, fill=(80, 80, 100), anchor="mm")
    draw.text((px+pw//2, py+220), "-R$247,00", font=fonte_saldo, fill=VERMELHO, anchor="mm")
    draw.text((px+pw//2, py+280), "▼ saldo disponível", font=fonte_small, fill=VERMELHO, anchor="mm")

    # Gráfico despencando
    gx, gy = px+30, py+320
    gw, gh = pw-60, 180
    draw.rounded_rectangle([gx, gy, gx+gw, gy+gh], radius=10, fill=(17, 17, 30))
    pontos = [(gx+i*50, gy+gh - int((gh-20) * v)) for i, v in enumerate([0.9, 0.85, 0.75, 0.5, 0.6, 0.3, 0.1, 0.05])]
    for i in range(len(pontos)-1):
        draw.line([pontos[i], pontos[i+1]], fill=VERMELHO, width=4)

    # Notificações
    for i, msg in enumerate(["⚠ Débito: Parcela Air Fryer 2022", "⚠ Fatura vencida há 3 dias"]):
        ny = py + 530 + i*55
        draw.rounded_rectangle([px+20, ny, px+pw-20, ny+45], radius=8, fill=(30, 10, 10))
        draw.text((px+pw//2, ny+22), msg, font=fonte_mini, fill=VERMELHO, anchor="mm")

    adicionar_texto_cena(draw, texto)
    return img


def cena_tubarao_juros(texto: str) -> Image.Image:
    """Cena 4 — Tubarão de juros."""
    img = Image.new("RGB", (LARGURA, ALTURA), (10, 6, 24))
    draw = ImageDraw.Draw(img)

    # Oceano de dívidas
    for i in range(3):
        y = 550 + i*30
        pontos = []
        for x in range(0, LARGURA+50, 50):
            oy = int(20 * math.sin((x + i*40) * 0.03))
            pontos.append((x, y + oy))
        pontos += [(LARGURA, ALTURA), (0, ALTURA)]
        draw.polygon(pontos, fill=(10, 5, 30 + i*5))

    # Corpo do tubarão
    sx, sy = LARGURA//2, 400
    draw.ellipse([sx-250, sy-130, sx+250, sy+130], fill=(50, 50, 70))
    # Cauda
    draw.polygon([(sx+220, sy), (sx+320, sy-80), (sx+320, sy+80)], fill=(45, 45, 65))
    # Nadadeira dorsal
    draw.polygon([(sx-50, sy-130), (sx+50, sy-130), (sx, sy-260)], fill=(45, 45, 65))
    # Boca
    draw.arc([sx-220, sy+30, sx-80, sy+160], start=0, end=180, fill=(200, 50, 50), width=8)
    # Dentes
    for dx in range(-200, -70, 30):
        draw.polygon([(sx+dx, sy+100), (sx+dx+15, sy+140), (sx+dx+30, sy+100)], fill=BRANCO)
    # Olho
    draw.ellipse([sx-170, sy-50, sx-120, sy], fill=BRANCO)
    draw.ellipse([sx-158, sy-38, sx-132, sy-12], fill=(10, 10, 10))

    # Placa do tubarão
    bx, by = sx-300, sy+180
    draw.rounded_rectangle([bx, by, bx+600, by+220], radius=20, fill=(26, 10, 62), outline=ROXO_VIBRANTE, width=3)
    fonte_taxa = encontrar_fonte(40, bold=False)
    fonte_num = encontrar_fonte(110)
    fonte_sub = encontrar_fonte(32, bold=False)
    draw.text((sx, by+45), "TAXA ROTATIVO CARTÃO", font=fonte_taxa, fill=(155, 127, 232), anchor="mm")
    draw.text((sx, by+150), "12,9%", font=fonte_num, fill=VERMELHO, anchor="mm")
    draw.text((sx, by+200), "ao mês • seu novo melhor amigo", font=fonte_sub, fill=(109, 68, 184), anchor="mm")

    adicionar_texto_cena(draw, texto)
    return img


def cena_prontuario(texto: str) -> Image.Image:
    """Cena 5 — Prontuário da Dra. Julga com carimbo CULPADE."""
    img = Image.new("RGB", (LARGURA, ALTURA), (15, 10, 30))
    draw = ImageDraw.Draw(img)

    # Papel do prontuário
    px, py = 80, 100
    pw, ph = LARGURA-160, 820
    draw.rounded_rectangle([px, py, px+pw, py+ph], radius=15, fill=(248, 245, 255), outline=(212, 194, 255), width=3)

    # Cabeçalho roxo
    draw.rounded_rectangle([px, py, px+pw, py+120], radius=15, fill=ROXO_MEDIO)
    fonte_titulo = encontrar_fonte(48)
    fonte_sub = encontrar_fonte(30, bold=False)
    fonte_campo = encontrar_fonte(36, bold=False)
    fonte_diag = encontrar_fonte(72)
    fonte_small = encontrar_fonte(28, bold=False)

    draw.text((px+pw//2, py+45), "CLÍNICA DRA. JULGA", font=fonte_titulo, fill=(232, 217, 255), anchor="mm")
    draw.text((px+pw//2, py+90), "Especialista em Decisões Questionáveis", font=fonte_sub, fill=(155, 127, 232), anchor="mm")

    # Campos
    y = py + 160
    for label, valor in [
        ("Paciente:", "Anônimo (Endividado)"),
        ("Queixa:", '"Fatura alta, não sei pq"'),
        ("", ""),
    ]:
        if label:
            draw.text((px+40, y), label, font=fonte_campo, fill=(109, 68, 184))
            draw.text((px+220, y), valor, font=fonte_campo, fill=(45, 16, 96))
            y += 55

    draw.line([px+30, y+10, px+pw-30, y+10], fill=(212, 194, 255), width=2)
    y += 40

    draw.text((px+40, y), "DIAGNÓSTICO:", font=fonte_campo, fill=(45, 16, 96))
    y += 55
    draw.text((px+40, y), "Parcelite Crônica", font=fonte_diag, fill=ROXO_VIBRANTE)
    y += 90
    draw.text((px+40, y), "Estágio: AVANÇADO (terminal)", font=fonte_small, fill=(155, 127, 232))
    y += 45
    draw.text((px+40, y), "Prognóstico: Sem defesa possível", font=fonte_small, fill=(155, 127, 232))
    y += 60
    draw.text((px+pw-40, y), "Dra. Julga — CRP 00/00000", font=fonte_small, fill=(155, 127, 232), anchor="ra")

    # Carimbo CULPADE girado
    img2 = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    draw2 = ImageDraw.Draw(img2)
    fonte_carimbo = encontrar_fonte(120)
    draw2.rounded_rectangle([580, 480, 980, 640], radius=20, outline=(226, 75, 74), width=12, fill=(0, 0, 0, 0))
    draw2.text((780, 560), "CULPADE", font=fonte_carimbo, fill=(226, 75, 74), anchor="mm")
    img2_rot = img2.rotate(-20, expand=False)
    arr = np.array(img2_rot)
    mask = img2_rot.split()[3] if img2_rot.mode == 'RGBA' else None
    img.paste(Image.fromarray(arr[:, :, :3]), mask=mask)

    # Desenha carimbo diretamente
    cx_stamp, cy_stamp = 800, 560
    fonte_stamp = encontrar_fonte(100)
    draw.rounded_rectangle([580, 460, 990, 640], radius=20, outline=VERMELHO, width=10)
    draw.text((cx_stamp, cy_stamp), "CULPADE", font=fonte_stamp, fill=VERMELHO, anchor="mm")

    adicionar_texto_cena(draw, texto)
    return img


def cena_card_viral(texto: str) -> Image.Image:
    """Cena 6 — Card claro e viral para compartilhar."""
    img = Image.new("RGB", (LARGURA, ALTURA), (245, 240, 255))
    draw = ImageDraw.Draw(img)

    # Card branco central
    cx = LARGURA//2
    draw.rounded_rectangle([60, 150, LARGURA-60, 1100], radius=40, fill=BRANCO, outline=(212, 194, 255), width=3)

    fonte_marca = encontrar_fonte(60)
    fonte_label = encontrar_fonte(32, bold=False)
    fonte_usuario = encontrar_fonte(80)
    fonte_veredicto = encontrar_fonte(90)
    fonte_cta = encontrar_fonte(36, bold=False)

    draw.text((cx, 240), "ME JULGA", font=fonte_marca, fill=(45, 16, 96), anchor="mm")
    draw.line([120, 290, LARGURA-120, 290], fill=(226, 212, 255), width=2)

    draw.text((cx, 360), "A Dra. Julga analisou", font=fonte_label, fill=(184, 160, 232), anchor="mm")
    draw.text((cx, 470), "@você", font=fonte_usuario, fill=(45, 16, 96), anchor="mm")
    draw.line([120, 530, LARGURA-120, 530], fill=(226, 212, 255), width=2)

    draw.text((cx, 610), "e o veredicto é", font=fonte_label, fill=(184, 160, 232), anchor="mm")
    draw.text((cx, 730), "Sem defesa", font=fonte_veredicto, fill=(45, 16, 96), anchor="mm")
    draw.text((cx, 840), "possível.", font=fonte_veredicto, fill=(45, 16, 96), anchor="mm")

    draw.line([120, 920, LARGURA-120, 920], fill=(226, 212, 255), width=2)
    draw.text((160, 980), "E o seu? mejulga.com.br", font=fonte_cta, fill=(184, 160, 232))
    draw.text((LARGURA-160, 980), "@dra.julga", font=fonte_cta, fill=(196, 175, 245), anchor="ra")

    # Botão CTA roxo
    draw.rounded_rectangle([60, 1120, LARGURA-60, 1300], radius=30, fill=ROXO_VIBRANTE)
    fonte_btn = encontrar_fonte(58)
    draw.text((cx, 1195), "Descobre o seu em", font=fonte_btn, fill=BRANCO, anchor="mm")
    draw.text((cx, 1265), "mejulga.com.br", font=fonte_btn, fill=(232, 217, 255), anchor="mm")

    # Rodapé
    fonte_footer = encontrar_fonte(32, bold=False)
    draw.text((cx, 1400), "ME JULGA • @dra.julga", font=fonte_footer, fill=(184, 160, 232), anchor="mm")

    return img


# ─── Mapeamento de cenários por número de cena ────────────────────────────────

CENARIOS = {
    1: cena_cartao_sofrencia,
    2: cena_nota_fiscal,
    3: cena_app_bancario,
    4: cena_tubarao_juros,
    5: cena_prontuario,
    6: cena_card_viral,
}


# ─── Gerar frames da cena ────────────────────────────────────────────────────

def gerar_frames_cena(cena: dict, duracao_segundos: float) -> list:
    numero = cena["numero"]
    texto = cena["texto"]

    fn = CENARIOS.get(numero, cena_cartao_sofrencia)
    frame = fn(texto)

    total_frames = int(duracao_segundos * FPS)
    return [frame] * total_frames


# ─── Carregar dados ──────────────────────────────────────────────────────────

def carregar_roteiro(categoria: str, data: str = None) -> dict:
    if not data:
        data = datetime.now().strftime("%Y-%m-%d")
    pasta = Path(__file__).parent / "generated" / "reels"
    arquivo = pasta / f"{data}_{categoria}_reels.json"
    if not arquivo.exists():
        raise FileNotFoundError(f"Roteiro não encontrado: {arquivo}")
    with open(arquivo, "r", encoding="utf-8") as f:
        return json.load(f)


def carregar_audio(categoria: str, data: str = None) -> Path:
    if not data:
        data = datetime.now().strftime("%Y-%m-%d")
    pasta = Path(__file__).parent / "generated" / "reels"
    arquivo = pasta / f"{data}_{categoria}_audio.mp3"
    if not arquivo.exists():
        raise FileNotFoundError(f"Áudio não encontrado: {arquivo}")
    return arquivo


# ─── Gerar vídeo ─────────────────────────────────────────────────────────────

def gerar_video(roteiro: dict, arquivo_audio: Path, arquivo_saida: Path):
    from moviepy import AudioFileClip, ImageSequenceClip

    cenas = roteiro.get("cenas", [])
    pasta_frames = arquivo_saida.parent / "frames_temp"
    pasta_frames.mkdir(exist_ok=True)

    print("  🎨 Gerando frames...")
    caminhos_frames = []
    idx = 0

    for cena in cenas:
        duracao = float(cena.get("duracao_segundos", 4))
        numero = cena["numero"]
        print(f"  📽️  Cena {numero}: {cena['texto'][:40]}...")

        frames = gerar_frames_cena(cena, duracao)
        for frame in frames:
            caminho = pasta_frames / f"frame_{idx:06d}.png"
            frame.save(str(caminho))
            caminhos_frames.append(str(caminho))
            idx += 1

    print(f"  ✅ {len(caminhos_frames)} frames gerados")

    print("  🎬 Montando vídeo...")
    video = ImageSequenceClip(caminhos_frames, fps=FPS)

    print("  🎵 Adicionando áudio...")
    audio = AudioFileClip(str(arquivo_audio))

    dur_v = video.duration
    dur_a = audio.duration
    if dur_a > dur_v:
        audio = audio.subclipped(0, dur_v)
    elif dur_a < dur_v:
        video = video.subclipped(0, dur_a)

    video_final = video.with_audio(audio)

    print("  💾 Exportando MP4...")
    video_final.write_videofile(
        str(arquivo_saida),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp_audio.m4a",
        remove_temp=True,
        logger=None
    )

    video_final.close()
    audio.close()

    # Limpa frames temporários
    import shutil
    shutil.rmtree(pasta_frames, ignore_errors=True)
    print("  🧹 Frames temporários removidos")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categoria", default="dinheiro", choices=list(CATEGORIAS_INFO.keys()))
    parser.add_argument("--data", default=None)
    args = parser.parse_args()

    hoje = args.data or datetime.now().strftime("%Y-%m-%d")
    categoria = args.categoria

    print(f"🎬 Gerando vídeo Reels — {categoria} — {hoje}")

    pasta_saida = Path(__file__).parent / "generated" / "reels"
    pasta_saida.mkdir(parents=True, exist_ok=True)
    arquivo_saida = pasta_saida / f"{hoje}_{categoria}_reels.mp4"

    print("📄 Carregando roteiro...")
    roteiro = carregar_roteiro(categoria, hoje)

    print("🎵 Carregando áudio...")
    arquivo_audio = carregar_audio(categoria, hoje)

    print("🎨 Renderizando vídeo com cenários visuais...")
    gerar_video(roteiro, arquivo_audio, arquivo_saida)

    print(f"\n✅ Vídeo gerado: {arquivo_saida}")
    print(f"📱 Pronto para publicar no @dra.julga!")


if __name__ == "__main__":
    main()
