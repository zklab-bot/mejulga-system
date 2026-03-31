"""
generate_video_v2.py
Versão 2 do gerador de vídeo com suporte a múltiplos estilos visuais.
Uso:
  python generate_video_v2.py --categoria dinheiro --estilo minimalista
  python generate_video_v2.py --categoria dinheiro --estilo tribunal
  python generate_video_v2.py --categoria dinheiro --estilo original
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
ALTURA  = 1920
FPS     = 30

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


# ─── ESTILO: MINIMALISTA ──────────────────────────────────────────────────────

def gerar_frame_minimalista(roteiro: dict) -> Image.Image:
    """Frame único branco + texto roxo."""
    from cena_minimalista import cena_minimalista
    return cena_minimalista(roteiro)


# ─── ESTILO: TRIBUNAL/PODCAST ─────────────────────────────────────────────────

def gerar_frame_tribunal(roteiro: dict) -> Image.Image:
    """Frame único tribunal/podcast."""
    from cena_tribunal_podcast import cena_tribunal_podcast
    return cena_tribunal_podcast(roteiro)


# ─── GERAR VÍDEO ─────────────────────────────────────────────────────────────

def gerar_video_estilo(roteiro: dict, arquivo_audio: Path, arquivo_saida: Path, estilo: str):
    from moviepy import AudioFileClip, ImageSequenceClip

    print(f"  🎨 Gerando frame(s) — estilo: {estilo}...")

    if estilo == "minimalista":
        frame = gerar_frame_minimalista(roteiro)
        frames_list = [frame]
        modo = "unico"
    elif estilo == "tribunal":
        frame = gerar_frame_tribunal(roteiro)
        frames_list = [frame]
        modo = "unico"
    else:
        raise ValueError(f"Estilo desconhecido: {estilo}. Use: minimalista, tribunal")

    # Salvar frame(s) como PNG temporário
    pasta_frames = arquivo_saida.parent / "frames_temp"
    pasta_frames.mkdir(exist_ok=True)
    caminhos_frames = []

    audio = AudioFileClip(str(arquivo_audio))
    dur_audio = audio.duration

    if modo == "unico":
        # Repete o frame único pela duração do áudio
        total_frames = int(dur_audio * FPS)
        print(f"  🖼️  1 frame estático × {total_frames} ({dur_audio:.1f}s de áudio)")
        for i in range(total_frames):
            caminho = pasta_frames / f"frame_{i:06d}.png"
            frames_list[0].save(str(caminho))
            caminhos_frames.append(str(caminho))

    print(f"  ✅ {len(caminhos_frames)} frames prontos")

    print("  🎬 Montando vídeo...")
    video = ImageSequenceClip(caminhos_frames, fps=FPS)

    print("  🎵 Adicionando áudio...")
    dur_v = video.duration
    if dur_audio > dur_v:
        audio = audio.subclipped(0, dur_v)
    elif dur_audio < dur_v:
        video = video.subclipped(0, dur_audio)

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

    import shutil
    shutil.rmtree(pasta_frames, ignore_errors=True)
    print("  🧹 Frames temporários removidos")


# ─── CARREGAR DADOS ───────────────────────────────────────────────────────────

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


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categoria", default="dinheiro", choices=list(CATEGORIAS_INFO.keys()))
    parser.add_argument("--data", default=None)
    parser.add_argument("--estilo", default="minimalista",
                        choices=["minimalista", "tribunal"],
                        help="Estilo visual do vídeo")
    args = parser.parse_args()

    hoje      = args.data or datetime.now().strftime("%Y-%m-%d")
    categoria = args.categoria
    estilo    = args.estilo

    print(f"\n🎬 Gerando vídeo — {categoria} — {hoje} — estilo: {estilo}")

    pasta_saida = Path(__file__).parent / "generated" / "reels"
    pasta_saida.mkdir(parents=True, exist_ok=True)
    arquivo_saida = pasta_saida / f"{hoje}_{categoria}_{estilo}_reels.mp4"

    print("📄 Carregando roteiro...")
    roteiro = carregar_roteiro(categoria, hoje)

    print("🎵 Carregando áudio...")
    arquivo_audio = carregar_audio(categoria, hoje)

    print(f"🎨 Renderizando — estilo {estilo}...")
    gerar_video_estilo(roteiro, arquivo_audio, arquivo_saida, estilo)

    print(f"\n✅ Vídeo gerado: {arquivo_saida}")
    print(f"📱 Pronto para publicar no @dra.julga!")


if __name__ == "__main__":
    main()
