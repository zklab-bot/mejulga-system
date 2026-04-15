# content-engine/tests/test_skills_criativas.py
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from skills.loader import load_skill


def test_estrutura_slides_existe_e_cobre_7_slides():
    content = load_skill("estrutura_slides")
    assert len(content) > 200
    for i in range(1, 8):
        assert f"Slide {i}" in content or f"slide {i}" in content, f"Slide {i} não definido"


def test_estrutura_slides_define_regra_capa():
    content = load_skill("estrutura_slides")
    assert "12 palavra" in content or "máx" in content.lower() or "swipe" in content.lower()


def test_visual_rules_existe():
    content = load_skill("visual_rules")
    assert len(content) > 200
    assert "fundo" in content.lower() or "background" in content.lower()


def test_visual_rules_define_limite_palavras():
    content = load_skill("visual_rules")
    assert "12" in content  # regra das 12 palavras por slide


def test_legenda_rules_existe():
    content = load_skill("legenda_rules")
    assert len(content) > 200
    assert "mejulga.com.br" in content
    assert "hashtag" in content.lower() or "#" in content


def test_filtro_sensibilidade_existe():
    content = load_skill("filtro_sensibilidade")
    assert len(content) > 200
    assert "saude_mental" in content.lower() or "saúde mental" in content.lower()
    assert "proib" in content.lower() or "bloqueado" in content.lower() or "never" in content.lower()
