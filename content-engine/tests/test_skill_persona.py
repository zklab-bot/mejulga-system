# content-engine/tests/test_skill_persona.py
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from skills.loader import load_skill


def test_persona_existe():
    content = load_skill("persona")
    assert len(content) > 200


def test_persona_contem_secoes_obrigatorias():
    content = load_skill("persona")
    assert "Tom" in content or "tom" in content
    assert "Vocabulário" in content or "vocabulário" in content
    assert "Frases" in content or "frases" in content


def test_persona_menciona_dra_julga():
    content = load_skill("persona")
    assert "Dra. Julga" in content


def test_persona_contem_vocabulario_permitido():
    content = load_skill("persona")
    for palavra in ["culpado", "veredicto", "processo", "réu"]:
        assert palavra in content.lower(), f"Palavra '{palavra}' não encontrada na persona"
