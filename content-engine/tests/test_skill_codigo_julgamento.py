# content-engine/tests/test_skill_codigo_julgamento.py
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from skills.loader import load_skill


def test_codigo_julgamento_existe():
    content = load_skill("codigo_julgamento")
    assert len(content) > 200


def test_codigo_julgamento_define_tipos_veredicto():
    content = load_skill("codigo_julgamento")
    assert "Culpado" in content
    assert "Reincidente" in content


def test_codigo_julgamento_define_formato_processo():
    content = load_skill("codigo_julgamento")
    assert "TRA" in content or "CAT" in content
    assert "/" in content


def test_codigo_julgamento_define_estrutura_obrigatoria():
    content = load_skill("codigo_julgamento")
    assert "Acusação" in content or "acusação" in content
    assert "Prova" in content or "prova" in content
    assert "Veredicto" in content or "veredicto" in content
