import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from pathlib import Path
import gerar_carrossel as gc


def _glossario_valido():
    return {
        "formato_post": "glossario",
        "categoria": "amor",
        "termo": "afetofobia seletiva",
        "pronuncia": "a·fe·to·fo·bi·a  se·le·ti·va",
        "classe_gramatical": "substantivo feminino",
        "definicao": "Incapacidade de demonstrar afeto — mas só com quem gosta de verdade.",
        "manifestacao": "Sumiços estratégicos. Mensagens frias logo depois de noites boas.",
        "nao_confundir": "Não confundir com timidez. Tímido não some. Tímido demora.",
        "frase_exemplo": "Ele só é assim comigo. Com os outros ele é super carinhoso.",
        "veredicto": "Culpado de fugir do que mais quer. Pena: ficar com quem não teme.",
        "legenda_instagram": "#draJulga #glossario",
        "sugestao_musica": "lo-fi",
    }


def test_gerar_slides_glossario_cria_6_arquivos(tmp_path):
    glossario = _glossario_valido()
    slides = gc.gerar_slides_glossario(glossario, tmp_path, "2026-04-08")
    assert len(slides) == 6
    for p in slides:
        assert p.exists(), f"Slide não criado: {p}"


def test_gerar_slides_glossario_nomenclatura_correta(tmp_path):
    glossario = _glossario_valido()
    slides = gc.gerar_slides_glossario(glossario, tmp_path, "2026-04-08")
    nomes = [p.name for p in slides]
    assert "2026-04-08_amor_glossario_slide_01.png" in nomes
    assert "2026-04-08_amor_glossario_slide_06.png" in nomes


def test_slide_glossario_capa_retorna_imagem(tmp_path):
    from PIL import Image
    glossario = _glossario_valido()
    img = gc.slide_glossario_capa(glossario, 1, 6)
    assert isinstance(img, Image.Image)
    assert img.size == (1080, 1080)


def test_slide_glossario_conteudo_retorna_imagem(tmp_path):
    from PIL import Image
    img = gc.slide_glossario_conteudo("DEFINIÇÃO", "Texto de teste aqui.", 2, 6)
    assert isinstance(img, Image.Image)
    assert img.size == (1080, 1080)
